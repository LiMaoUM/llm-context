# Background Context Integration Guide

## Overview

The background context module provides structured information about major events during the study period (May 30 - June 30, 2024) that are relevant to understanding social media discourse about political ideology and stance toward Biden and Trump.

## Study Period Events

### 1. Donald Trump Hush-Money Trial Verdict
- **Date**: May 30, 2024
- **Event**: A New York jury found Trump guilty on all 34 felony counts related to falsifying business records
- **Significance**: First criminal conviction of a former U.S. president
- **Impact on Discourse**: Central polarizing issue in the 2024 campaign

### 2. Hunter Biden Federal Gun Trial Verdict
- **Date**: June 11, 2024
- **Event**: Hunter Biden (son of President Biden) found guilty on three felony counts related to illegal firearm possession
- **Significance**: Parallel legal case to Trump conviction but involving Biden family
- **Impact on Discourse**: Became ammunition for partisan attacks and defensive rhetoric

### 3. First Biden-Trump Presidential Debate
- **Date**: June 27, 2024
- **Event**: First general election debate between Biden and Trump held in Atlanta (CNN)
- **Significance**: Major moment in election campaign
- **Impact on Discourse**: Shaped perceptions of candidate competence and policy positions

## Key Components

### BackgroundContextManager

The `BackgroundContextManager` class provides methods to access and manage background events:

```python
from background_context import BackgroundContextManager

manager = BackgroundContextManager()

# Get all events
events = manager.get_all_events()

# Get specific event
trump_trial = manager.get_event('trump_trial')

# Get formatted text for LLM prompts
context_text = manager.get_event_text('trump_trial')

# Get context for a specific date
context = manager.get_context_for_date(date(2024, 6, 15))

# Search events by keyword
biden_events = manager.search_events_by_keyword('Biden')
```

### Integration with Data Loader

The `DataLoader` now includes background context:

```python
from data_loader import DataLoader

loader = DataLoader("./data")
loader.load_all()

# Get background context for a sample
background = loader.get_background_context(post_date=date(2024, 6, 1))

# Get complete sample with all context including background
sample = loader.get_post_with_all_context("post_id_123")
# Returns: {
#     'post_id': '...',
#     'post_text': '...',
#     'post_date': date(...),
#     'user_metadata': {...},
#     'conversation': {...},
#     'background_context': '...',  # NEW: Background context text
#     'post_raw': {...}
# }
```

## Using Background Context in Prompts

### Example 1: Simple Background Insertion

```python
from llm_inference import ANALYSIS_PROMPT_TEMPLATE
from background_context import format_background_for_llm
from datetime import date

background = format_background_for_llm(post_date=date(2024, 5, 31))

prompt = ANALYSIS_PROMPT_TEMPLATE.format(
    background=background,
    conversation="[TARGET POST]\nUser's statement here",
    user_metadata="User bio and profile info",
    target_post="User's actual post"
)
```

### Example 2: Date-Specific Context

```python
# Get context for a post written before Trump trial
context_early = format_background_for_llm(post_date=date(2024, 5, 29))

# Get context for a post written after all events
context_late = format_background_for_llm(post_date=date(2024, 6, 30))
```

### Example 3: Context Variants with Background

The `ContextVariantGenerator` in `data_loader.py` now includes background in all variants:

```python
from data_loader import DataLoader, ContextVariantGenerator

loader = DataLoader("./data")
loader.load_all()

# Load a sample with all context including background
sample = loader.get_post_with_all_context("post_id_123")

# Generate context variants (now includes background)
generator = ContextVariantGenerator(loader)
variants = generator.generate_variants(sample)

# Variants now include:
# - 'T': Text only
# - 'T+C': Text + Conversation
# - 'T+B': Text + Background (now populated!)
# - 'T+M': Text + Metadata
# - 'T+C+B': Text + Conversation + Background
# - 'T+C+M': Text + Conversation + Metadata
# - 'T+B+M': Text + Background + Metadata
# - 'FULL': All contexts combined
```

## Event Details

### Trump Hush-Money Trial

**Key Figures**: 
- Donald Trump (defendant)
- Judge Juan Merchan
- Stormy Daniels (alleged victim)
- Michael Cohen (key witness)

**Related Keywords**:
- Trump conviction
- Felony charges
- Hush money
- Stormy Daniels
- Falsifying records
- Manhattan DA
- Jury verdict

**Impact on Social Media**:
- Supporters: Viewed as politically motivated, witch hunt
- Critics: Saw as appropriate accountability for criminal behavior
- Neutral observers: Discussed implications for democracy and justice system

### Hunter Biden Gun Trial

**Key Figures**:
- Hunter Biden (defendant)
- President Joe Biden (father)
- Delaware prosecutors
- Gun dealers

**Related Keywords**:
- Hunter Biden
- Gun trial
- Felony charges
- Drug use
- Federal charges
- Guilty verdict

**Impact on Social Media**:
- Republicans: Emphasized Biden family misconduct
- Democrats: Noted willingness to cooperate with justice
- General discourse: Questions about family privilege and accountability

### Biden-Trump Debate

**Key Figures**:
- Joe Biden (incumbent president)
- Donald Trump (former president)
- CNN moderators
- American voters

**Related Keywords**:
- Presidential debate
- Debate performance
- Policy positions
- Campaign
- Competence
- Stamina
- Rhetoric

**Impact on Social Media**:
- Shaped media narratives about candidate viability
- Influenced voter perceptions
- Generated extensive commentary and fact-checking
- Affected campaign momentum

## Design Considerations

### Why Background Context Matters

1. **Contextual Sensitivity**: Users' political ideology and stance may be influenced by current events
2. **Temporal Relevance**: A post written on May 30 has different context than one on June 30
3. **Event-Specific Reactions**: Users may be directly responding to specific events
4. **Model Understanding**: LLMs can better assess confidence when they have relevant background

### Ablation Study Benefits

By having structured background context, you can test:

- **T (Text only)**: Baseline - how well does LLM perform without context?
- **T+B**: Does background knowledge alone improve accuracy?
- **Full (T+C+B+M)**: How much does comprehensive context help?

This allows isolating the contribution of background knowledge from other context types.

## Extending the Framework

### Adding New Events

```python
from background_context import BackgroundEvent, EventType
from datetime import date

new_event = BackgroundEvent(
    event_id="event_new_2024",
    title="New Political Event",
    date=date(2024, 6, 15),
    event_type=EventType.POLITICAL,
    description="Description of the event",
    key_figures=["Figure 1", "Figure 2"],
    impact="Impact of the event",
    related_keywords=["keyword1", "keyword2"]
)

# Add to manager (would need to modify BackgroundContextManager)
```

### Customizing Background Format

The background context uses a structured text format by default. You can customize by:

1. Modifying `BackgroundEvent.to_text()` method
2. Creating custom formatting in `format_background_for_llm()`
3. Integrating with external data sources

## Performance Implications

- **Token Usage**: Background context adds ~500-1500 tokens per prompt
- **Cost**: Consider including background in batched evaluations
- **Latency**: Minimal impact on inference time

## Files

- `background_context.py`: Core background context module
- `data_loader.py`: Updated to include background context integration
- `llm_inference.py`: Prompt templates support background context
- `examples_background_context.py`: Examples and usage patterns
- `BACKGROUND_CONTEXT.md`: This documentation

## References

For more information about the events, see:
- General study period context in `STUDY_PERIOD_GENERAL_BACKGROUND`
- Individual event details in event objects
- Complete event text via `get_all_events_text()`
