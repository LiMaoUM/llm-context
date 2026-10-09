"""
Test vLLM batch inference functionality.
"""

import time
from llm_inference import HuggingFaceProvider

def test_single_query():
    """Test single query."""
    print("="*60)
    print("Testing single query")
    print("="*60)
    
    provider = HuggingFaceProvider(
        model_id="google/gemma-2-27b-it",
        gpu_device=6,
        temperature=0.7,
        max_tokens=256
    )
    
    prompt = """You are a political discourse analyst.

[TARGET POST]
I'm hoping it get more people out to vote. That will hurt Trump the most.

ANALYSIS QUESTIONS:
1. POLITICAL IDEOLOGY: Left/Center/Right
2. STANCE TOWARD TRUMP: favor/against/neutral/undecided

RESPONSE FORMAT:
Ideology: [answer]
Ideology Confidence: [0-100]%
Trump Stance: [answer]
Stance Confidence: [0-100]%"""
    
    start = time.time()
    text, confidence, error = provider.query(prompt)
    elapsed = time.time() - start
    
    print(f"\nQuery time: {elapsed:.2f}s")
    print(f"Success: {error is None}")
    print(f"Response length: {len(text)} chars")
    print(f"Confidence: {confidence}")
    print(f"\nResponse:\n{text}")
    print()


def test_batch_query():
    """Test batch query."""
    print("="*60)
    print("Testing batch query")
    print("="*60)
    
    provider = HuggingFaceProvider(
        model_id="google/gemma-2-27b-it",
        gpu_device=6,
        temperature=0.7,
        max_tokens=256
    )
    
    prompts = [
        """You are a political discourse analyst.

[TARGET POST]
I'm hoping it get more people out to vote. That will hurt Trump the most.

ANALYSIS QUESTIONS:
1. POLITICAL IDEOLOGY: Left/Center/Right
2. STANCE TOWARD TRUMP: favor/against/neutral/undecided

RESPONSE FORMAT:
Ideology: [answer]
Ideology Confidence: [0-100]%
Trump Stance: [answer]
Stance Confidence: [0-100]%""",
        """You are a political discourse analyst.

[TARGET POST]
MAGA has the best policies for ALL Americans! Trump 2024!

ANALYSIS QUESTIONS:
1. POLITICAL IDEOLOGY: Left/Center/Right
2. STANCE TOWARD TRUMP: favor/against/neutral/undecided

RESPONSE FORMAT:
Ideology: [answer]
Ideology Confidence: [0-100]%
Trump Stance: [answer]
Stance Confidence: [0-100]%""",
        """You are a political discourse analyst.

[TARGET POST]
We need bipartisan solutions to move the country forward.

ANALYSIS QUESTIONS:
1. POLITICAL IDEOLOGY: Left/Center/Right
2. STANCE TOWARD TRUMP: favor/against/neutral/undecided

RESPONSE FORMAT:
Ideology: [answer]
Ideology Confidence: [0-100]%
Trump Stance: [answer]
Stance Confidence: [0-100]%""",
    ]
    
    print(f"\nProcessing {len(prompts)} prompts in batch...")
    start = time.time()
    results = provider.batch_query(prompts)
    elapsed = time.time() - start
    
    print(f"\nBatch query time: {elapsed:.2f}s")
    print(f"Average time per prompt: {elapsed/len(prompts):.2f}s")
    print(f"Throughput: {len(prompts)/elapsed:.2f} prompts/sec")
    
    for i, (text, confidence, error) in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Success: {error is None}")
        print(f"Response length: {len(text)} chars")
        print(f"Confidence: {confidence}")
        print(f"Response: {text[:200]}...")
    print()


def test_speedup():
    """Compare sequential vs batch inference."""
    print("="*60)
    print("Comparing sequential vs batch inference")
    print("="*60)
    
    provider = HuggingFaceProvider(
        model_id="google/gemma-2-27b-it",
        gpu_device=6,
        temperature=0.7,
        max_tokens=256
    )
    
    # Create 10 test prompts
    prompts = []
    test_posts = [
        "I'm hoping it get more people out to vote. That will hurt Trump the most.",
        "MAGA has the best policies for ALL Americans! Trump 2024!",
        "We need bipartisan solutions to move the country forward.",
        "Biden's policies are destroying this country.",
        "Democrats and Republicans need to work together.",
        "Trump is a threat to democracy.",
        "The economy was better under Trump.",
        "Healthcare should be a human right.",
        "Lower taxes and less government regulation!",
        "Climate change is our generation's greatest challenge.",
    ]
    
    for post in test_posts:
        prompts.append(f"""You are a political discourse analyst.

[TARGET POST]
{post}

ANALYSIS QUESTIONS:
1. POLITICAL IDEOLOGY: Left/Center/Right
2. STANCE TOWARD TRUMP: favor/against/neutral/undecided

RESPONSE FORMAT:
Ideology: [answer]
Ideology Confidence: [0-100]%
Trump Stance: [answer]
Stance Confidence: [0-100]%""")
    
    # Sequential
    print(f"\nSequential processing of {len(prompts)} prompts...")
    start = time.time()
    for prompt in prompts:
        provider.query(prompt)
    seq_time = time.time() - start
    print(f"Sequential time: {seq_time:.2f}s")
    print(f"Average: {seq_time/len(prompts):.2f}s per prompt")
    
    # Batch
    print(f"\nBatch processing of {len(prompts)} prompts...")
    start = time.time()
    provider.batch_query(prompts)
    batch_time = time.time() - start
    print(f"Batch time: {batch_time:.2f}s")
    print(f"Average: {batch_time/len(prompts):.2f}s per prompt")
    
    speedup = seq_time / batch_time
    print(f"\n🚀 Speedup: {speedup:.2f}x faster with batch inference!")
    print()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    print("vLLM Batch Inference Test")
    print("="*60 + "\n")
    
    # Run tests
    test_single_query()
    test_batch_query()
    test_speedup()
    
    print("="*60)
    print("All tests completed!")
    print("="*60)
