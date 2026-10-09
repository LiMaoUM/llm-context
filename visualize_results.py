import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json
import os

def load_data(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                record = json.loads(line)
                if record.get('success'):
                    data.append(record)
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(data)

def visualize_confidence_trends(df, output_path='results/confidence_trends.png'):
    # Define variant order
    variant_order = ['T', 'T+B', 'T+B+C', 'T+B+C+M']
    
    # Filter for valid variants
    df = df[df['variant'].isin(variant_order)].copy()
    
    # Convert variant to categorical with specific order
    df['variant'] = pd.Categorical(df['variant'], categories=variant_order, ordered=True)
    
    # Set up the plotting style
    sns.set_theme(style="whitegrid")
    
    # Create a figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    
    # Metrics to plot
    metrics = [
        ('ideology_confidence', 'Ideology Confidence'),
        ('stance_confidence', 'Stance Confidence')
    ]
    
    for i, (metric, title) in enumerate(metrics):
        ax = axes[i]
        
        # Plot individual lines (spaghetti plot)
        # We group by sample_id to draw lines for the same sample across variants
        # We use a low alpha to make them faint background lines
        # Note: This requires that sample_id is present and consistent
        if 'sample_id' in df.columns:
            sns.lineplot(
                data=df, 
                x='variant', 
                y=metric, 
                units='sample_id', 
                estimator=None, 
                color='gray', 
                alpha=0.1, 
                linewidth=0.5,
                ax=ax,
                zorder=1
            )
        
        # Plot the mean trend line with error bands (95% CI by default in seaborn)
        sns.lineplot(
            data=df, 
            x='variant', 
            y=metric, 
            color='blue', 
            marker='o', 
            linewidth=2.5, 
            errorbar=('ci', 95),
            label='Mean Trend (95% CI)',
            ax=ax,
            zorder=2
        )
        
        ax.set_title(f'{title} Trend across Context Variants')
        ax.set_xlabel('Context Variant')
        ax.set_ylabel('Confidence Score (0-100)')
        ax.set_ylim(0, 105)
        ax.legend()

    plt.tight_layout()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    plt.savefig(output_path, dpi=300)
    print(f"Visualization saved to {output_path}")

if __name__ == "__main__":
    input_file = '/home/maolee/projects/llm-context/results/model_responses.jsonl'
    output_file = '/home/maolee/projects/llm-context/results/confidence_trends.png'
    
    if os.path.exists(input_file):
        print(f"Loading data from {input_file}...")
        df = load_data(input_file)
        
        if not df.empty:
            print(f"Loaded {len(df)} records.")
            visualize_confidence_trends(df, output_file)
        else:
            print("No valid data found in the input file.")
    else:
        print(f"Input file {input_file} not found.")
