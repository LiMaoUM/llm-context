"""
Test to verify no truncation is happening in metadata and posts.
"""

from data_loader import DataLoader, ContextVariantGenerator

# Load data
loader = DataLoader()
loader.load_all()
generator = ContextVariantGenerator(loader)

# Find a post with many parent conversations
import pandas as pd
parent_count = loader.post_edges.groupby('src_post_id').size().reset_index(name='parent_count')
top_posts = parent_count.nlargest(3, 'parent_count')

print("Testing posts with most parent conversations:")
print("=" * 80)

for idx, row in top_posts.iterrows():
    post_id = row['src_post_id']
    num_parents = row['parent_count']
    
    print(f"\nPost {idx + 1}: {num_parents} parents")
    print("-" * 80)
    
    # Get full sample
    sample = loader.get_post_with_all_context(post_id)
    
    if not sample:
        print("  Could not load sample")
        continue
    
    # Check post text length
    post_text = sample.get('post_text', '')
    print(f"  Target post length: {len(post_text)} chars")
    if len(post_text) > 0:
        print(f"  First 100 chars: {post_text[:100]}...")
        print(f"  Last 100 chars: ...{post_text[-100:]}")
    
    # Check metadata
    metadata = sample.get('user_metadata', {})
    recent_posts = sample.get('user_recent_posts', [])
    if recent_posts:
        print(f"\n  User recent posts: {len(recent_posts)}")
        for i, post in enumerate(recent_posts[:2], 1):
            text = post.get('text', '')
            print(f"    Post {i} length: {len(text)} chars")
            if '...' in text:
                print(f"    ⚠️  WARNING: Contains ellipsis, may be truncated!")
    
    # Check conversation
    conversation = sample.get('conversation', {})
    parents = conversation.get('parent_posts', [])
    children = conversation.get('child_posts', [])
    
    print(f"\n  Conversation:")
    print(f"    Parents: {len(parents)}")
    print(f"    Children: {len(children)}")
    
    # Check first few parents
    if parents:
        for i, parent in enumerate(parents[:3], 1):
            text = parent.get('text') or parent.get('content', '')
            print(f"    Parent {i} length: {len(text)} chars")
    
    # Generate T+B+C+M variant to check total length
    variants = generator.generate_variants(sample)
    
    print(f"\n  Variant lengths:")
    for variant_name in ['T', 'T+B', 'T+B+C', 'T+B+C+M']:
        variant_text = variants[variant_name]
        print(f"    {variant_name:8s}: {len(variant_text):6d} chars")
    
    # Check if T+B+C+M is unreasonably short given parent count
    full_variant = variants['T+B+C+M']
    expected_min_length = num_parents * 50  # Assume at least 50 chars per parent
    if len(full_variant) < expected_min_length:
        print(f"  ⚠️  WARNING: T+B+C+M variant ({len(full_variant)} chars) seems too short")
        print(f"       Expected at least {expected_min_length} chars for {num_parents} parents")
    
    # Note: Ellipsis (...) in variants is usually part of user content, not truncation
    # Real truncation would show as incomplete sentences or cut-off HTML tags
    
    print()

print("\n" + "=" * 80)
print("Truncation check complete!")
print("=" * 80)
