"""
Example: Using Background Context in the LLM Context Experiment

This script demonstrates how to:
1. Load background context information
2. Integrate it with sample data
3. Generate context variants with background information
4. Use it in LLM inference prompts
"""

from background_context import (
    BackgroundContextManager,
    format_background_for_llm,
    TRUMP_HUSH_MONEY_TRIAL,
    HUNTER_BIDEN_GUN_TRIAL,
    BIDEN_TRUMP_DEBATE,
)
from data_loader import DataLoader, ContextVariantGenerator
from datetime import date
import json


def example_background_context():
    """Example 1: Load and explore background context."""
    print("=" * 80)
    print("EXAMPLE 1: Background Context Management")
    print("=" * 80)
    
    manager = BackgroundContextManager()
    
    # Get all events
    print("\nAvailable Events:")
    for event_key, event in manager.get_all_events().items():
        print(f"  - {event_key}: {event.title} ({event.date})")
    
    # Get specific event
    print("\nTrump Trial Event:")
    print(manager.get_event_text('trump_trial'))
    
    # Get events by keyword
    print("\n" + "=" * 80)
    print("Events mentioning 'Biden':")
    events = manager.search_events_by_keyword('Biden')
    for event in events:
        print(f"  - {event.title}")


def example_context_for_date():
    """Example 2: Get background context for a specific date."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Background Context for Specific Date")
    print("=" * 80)
    
    manager = BackgroundContextManager()
    
    # Context before Trump trial
    print("\nContext for June 1, 2024 (after Trump trial):")
    context = manager.get_context_for_date(date(2024, 6, 1))
    print(context[:500] + "...")
    
    # Context after all events
    print("\nContext for June 30, 2024 (after all events):")
    context = manager.get_context_for_date(date(2024, 6, 30))
    print("(Includes all three major events)")


def example_with_data_loader():
    """Example 3: Integrate background context with data loading."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Integration with Data Loader")
    print("=" * 80)
    
    loader = DataLoader("./data")
    
    # Get background context
    background = loader.get_background_context()
    print("Background context retrieved successfully.")
    print(f"Length: {len(background)} characters")
    print(f"First 300 characters:\n{background[:300]}...")


def example_context_variants_with_background():
    """Example 4: Generate context variants that include background."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Context Variants with Background")
    print("=" * 80)
    
    # Create sample with background context
    sample = {
        'post_id': 'post_123',
        'post_text': "Trump's conviction is a dark day for America. The trial was rigged from the start.",
        'conversation': {
            'parent_posts': [
                {'text': "I can't believe what happened with Trump's trial today."}
            ],
            'child_posts': [
                {'text': "I totally agree, this is a witch hunt."}
            ]
        },
        'user_metadata': {
            'name': 'Conservative Voice',
            'bio': 'Constitutional rights advocate',
            'follower_count': 5000,
            'verified': False
        },
        'background_context': format_background_for_llm(post_date=date(2024, 5, 31))
    }
    
    print("Sample created with background context.")
    print(f"\nPost: {sample['post_text']}")
    print(f"Background context length: {len(sample['background_context'])} chars")
    
    # Show first part of background
    print(f"\nBackground Context (first 400 chars):")
    print(sample['background_context'][:400] + "...")


def example_prompt_with_background():
    """Example 5: Create an LLM prompt with background context."""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: LLM Prompt with Background Context")
    print("=" * 80)
    
    from llm_inference import ANALYSIS_PROMPT_TEMPLATE
    
    # Create sample context
    background = format_background_for_llm(post_date=date(2024, 6, 1))
    conversation = """[PARENT REPLY]
I'm shocked by Trump's conviction. This is political persecution.

[TARGET POST]
The jury found Trump guilty on all 34 counts. This is a watershed moment in American politics.

[CHILD REPLY]
Whether you support Trump or not, we should all be concerned about the state of our justice system."""
    
    user_metadata = """Name: Political Observer
Bio: Independent news follower
Followers: 2,500
Verified: No"""
    
    target_post = "The jury found Trump guilty on all 34 counts. This is a watershed moment in American politics."
    
    # Create prompt
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(
        background=background,
        conversation=conversation,
        user_metadata=user_metadata,
        target_post=target_post
    )
    
    print("LLM Prompt created successfully!")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"\nFirst 800 characters of prompt:")
    print(prompt[:800] + "...")


def example_event_metadata():
    """Example 6: Get event metadata."""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Event Metadata")
    print("=" * 80)
    
    manager = BackgroundContextManager()
    
    # Get event as JSON-serializable dict
    print("\nTrump Trial Event (as JSON):")
    event_dict = manager.get_event_summary('trump_trial')
    print(json.dumps(event_dict, indent=2, default=str))
    
    # Get keywords for event
    print("\nKeywords for Hunter Biden Trial:")
    keywords = manager.get_keywords_for_event('hunter_biden_trial')
    print(json.dumps(keywords, indent=2))


def example_comparative_analysis():
    """Example 7: Compare how context affects interpretation."""
    print("\n" + "=" * 80)
    print("EXAMPLE 7: Impact of Background Context on Analysis")
    print("=" * 80)
    
    # Same post, different background contexts
    post_text = "I can't support either candidate at this point."
    
    print(f"Post: '{post_text}'")
    print("\nWithout background context:")
    print("  LLM might classify as: Neutral")
    print("  Confidence: Medium (ambiguous)")
    
    print("\nWith background context (May 30, 2024 - Trump trial):")
    context1 = format_background_for_llm(post_date=date(2024, 5, 30))
    print("  - Context: Trump just convicted, Biden debate not yet happened")
    print("  - LLM might infer: Stance influenced by Trump conviction")
    print("  - Possible interpretation: Could reflect disillusionment with both")
    
    print("\nWith background context (June 28, 2024 - After debate):")
    context2 = format_background_for_llm(post_date=date(2024, 6, 28))
    print("  - Context: All three major events have occurred")
    print("  - LLM might infer: Reaction to Biden debate performance")
    print("  - Possible interpretation: Could reflect concerns about Biden's viability")


if __name__ == "__main__":
    # Run all examples
    example_background_context()
    example_context_for_date()
    example_with_data_loader()
    example_context_variants_with_background()
    example_prompt_with_background()
    example_event_metadata()
    example_comparative_analysis()
    
    print("\n" + "=" * 80)
    print("EXAMPLES COMPLETED")
    print("=" * 80)
