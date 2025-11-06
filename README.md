# LLM Context & Confidence Analysis Experiment

A comprehensive framework for testing how different contextual dimensions affect Large Language Model (LLM) confidence calibration and interpretation accuracy in social media stance detection.

## Overview

This experiment systematically evaluates how LLMs interpret social meaning under different context conditions:

- **Context Variants**: 8 ablation conditions (T, T+C, T+B, T+M, T+C+B, T+C+M, T+B+M, FULL)
- **Multiple LLMs**: GPT-4, GPT-3.5, Claude-3 Opus, Claude-3 Sonnet, Llama-2-70B, Gemma-2-27B
- **Metrics**: Accuracy, F1, Calibration (ECE, Brier), Overconfidence Rate, Context Sensitivity
- **Output**: Metrics analysis, calibration curves, heatmaps, case studies

## Project Structure

```
llm-context/
├── data/                          # Social media data (Parquet files)
│   ├── posts/
│   ├── users/
│   ├── interactions/
│   ├── post_edges/
│   ├── cascades_nodes/
│   └── tree_features/
├── experiment_config.yaml         # Main experiment configuration
├── data_loader.py                 # Data loading and exploration utilities
├── llm_inference.py               # LLM provider implementations and inference pipeline
├── evaluation_metrics.py           # Metrics computation (calibration, accuracy, etc.)
├── analysis_visualization.py      # Results analysis and visualization
├── run_experiment.py              # Main experiment runner script
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 2. Configure API Keys

Set up API keys for the LLM providers you plan to use:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# HuggingFace (for Replicate models)
export REPLICATE_API_TOKEN="..."

# HuggingFace Hub (for local models)
export HUGGINGFACE_API_KEY="hf_..."
```

### 3. Verify Data

The experiment expects data in the `data/` folder:

```bash
ls -lh data/posts/posts.parquet
ls -lh data/users/users.parquet
# ... etc
```

## Configuration

### Experiment Config (`experiment_config.yaml`)

The main configuration file controls:

1. **Models to Evaluate**
   - OpenAI (GPT-4, GPT-3.5)
   - Anthropic (Claude-3 Opus, Sonnet)
   - HuggingFace (Llama-2, Gemma-2)

2. **Context Variants**
   - `T`: Text only (baseline)
   - `T+C`: + Conversation history
   - `T+B`: + Background context
   - `T+M`: + User metadata
   - `T+C+B`: + Conversation + Background
   - `T+C+M`: + Conversation + Metadata
   - `T+B+M`: + Background + Metadata
   - `FULL`: All context (T+C+B+M)

3. **Tasks & Targets**
   - Stance detection toward political entities
   - Sentiment analysis
   - Customizable target entities and label sets

4. **Evaluation Metrics**
   - **Accuracy & F1**: Classification performance
   - **Expected Calibration Error (ECE)**: Confidence calibration
   - **Brier Score**: Probabilistic accuracy
   - **Overconfidence Rate**: % of incorrect predictions with >70% confidence
   - **Context Sensitivity**: Performance delta across variants

5. **Execution Parameters**
   - Batch size, retry logic, caching
   - Output directory configuration
   - Stratified sampling strategy

## Quick Start

### Option 1: Run Full Pipeline

```bash
python run_experiment.py --config experiment_config.yaml
```

### Option 2: Run Individual Steps

```bash
# Explore data
python run_experiment.py --steps explore

# Generate context variants
python run_experiment.py --steps explore variants

# Run inference
python run_experiment.py --steps explore variants inference

# Compute metrics and analysis
python run_experiment.py --steps metrics analysis report
```

### Option 3: Dry Run (Testing)

```bash
python run_experiment.py --dry-run
```

## Data Format

### Input Data

The framework expects Parquet files with the following structure:

**posts.parquet**
- `id`: Unique post identifier
- `text` (or `content`): Post text
- `author_id` (or `user_id`): Author user ID
- `created_at` (or `timestamp`): Post creation time

**users.parquet**
- `id`: Unique user identifier
- `bio` (or `description`): User biography
- `followers_count`: Number of followers
- `verified`: Verification status

**post_edges.parquet**
- `source_id` (or `source`): Source post ID
- `target_id` (or `target`): Target post ID
- Encodes conversation threads

### Output Files

```
results/
├── data_summary.json              # Data exploration summary
├── sample_variants.json           # Example context variant structure
├── inference_results.json         # Raw LLM inference outputs
├── metrics_by_model.json          # Computed metrics by model and variant
├── experiment_report.json         # Summary report and findings
└── figures/                       # Visualization plots
    ├── accuracy_by_context.png
    ├── calibration_curve.png
    ├── ece_by_context.png
    ├── overconfidence_by_context.png
    ├── context_sensitivity_heatmap.png
    └── marginal_improvements.png
```

## Core Modules

### 1. `data_loader.py`

Utilities for loading and exploring social media data:

```python
from data_loader import DataLoader, ContextVariantGenerator

# Load data
loader = DataLoader("./data")
summary = loader.get_data_summary()

# Get context for a post
context = loader.get_post_with_all_context(post_id)

# Generate variants
generator = ContextVariantGenerator(loader)
variants = generator.generate_variants(context)
# Returns: {'T': ..., 'T+C': ..., 'T+B': ..., ...}
```

### 2. `llm_inference.py`

LLM provider implementations and inference pipeline:

```python
from llm_inference import InferencePipeline, BatchEvaluator

# Initialize pipeline
pipeline = InferencePipeline(config)

# Query single model
result = pipeline.query_model('gpt-4', prompt)

# Evaluate batch
evaluator = BatchEvaluator(pipeline)
results = evaluator.evaluate_batch(samples, target_entity, stance_options)
```

### 3. `evaluation_metrics.py`

Metrics computation for calibration and classification:

```python
from evaluation_metrics import ComprehensiveMetrics, ContextSensitivityMetrics

# Compute all metrics
metrics = ComprehensiveMetrics.compute_all_metrics(
    y_true, y_pred, confidence
)

# Analyze context sensitivity
sensitivity = ContextSensitivityMetrics.context_sensitivity_analysis(
    results_by_variant
)
```

### 4. `analysis_visualization.py`

Results analysis and visualization:

```python
from analysis_visualization import ResultsAnalyzer, ResultsVisualizer

# Analyze results
analyzer = ResultsAnalyzer()
metrics = analyzer.compute_all_models_metrics(results, models, stance_options)

# Generate visualizations
visualizer = ResultsVisualizer()
visualizer.generate_all_plots(metrics)
```

## Expected Results

The experiment should reveal:

1. **Context Effects**: Which context layers most improve accuracy and calibration
2. **Model Differences**: How different models respond to contextual richness
3. **Confidence Patterns**: Whether models are better calibrated with full context
4. **Overconfidence**: Which models tend to be overconfident in low-context settings
5. **Diminishing Returns**: Whether additional context layers show marginal gains

## Key Metrics Explained

### Expected Calibration Error (ECE)
- Measures gap between predicted confidence and actual accuracy
- Lower is better (perfectly calibrated = 0)
- Formula: ECE = Σ |accuracy_bin - confidence_bin| × (n_bin / N)

### Overconfidence Rate
- Fraction of incorrect predictions where confidence > 70%
- Lower is better
- Indicates tendency to be confidently wrong

### Context Sensitivity
- Performance improvement from adding each context layer
- Reveals which context types are essential
- Diminishing returns analysis shows optimal context depth

## Customization

### Add New Models

Edit `experiment_config.yaml`:

```yaml
models:
  - name: "your-model"
    provider: "openai"  # or "anthropic", "huggingface"
    config:
      model_id: "model-identifier"
      temperature: 0.7
      max_tokens: 256
```

### Add New Tasks

```yaml
tasks:
  - task_id: "custom_task"
    task_name: "Your Task"
    description: "Your task description"
    target_entities: ["entity1", "entity2"]
    stance_options: ["option1", "option2", "option3"]
```

### Modify Context Variants

Edit the `ContextVariantGenerator` class in `data_loader.py` to customize how context is formatted.

### Add New Evaluation Metrics

Extend `ComprehensiveMetrics` in `evaluation_metrics.py`:

```python
@staticmethod
def your_metric(y_true, y_pred, confidence):
    """Your metric implementation."""
    # Your code here
    return metric_value
```

## Troubleshooting

### API Rate Limits

If you encounter rate limits:
- Increase `retry_delay` in `experiment_config.yaml`
- Reduce `batch_size`
- Implement request queuing

### Memory Issues

For large batches:
- Reduce `batch_size` in execution config
- Process in smaller chunks using `save_interval`
- Use streaming for inference results

### Missing Data

If context is incomplete:
- Check data format in `data_summary.json`
- Verify post_edges relationships
- Review `data_loader.py` context retrieval logic

## Performance Tips

1. **Caching**: Enable `cache_responses: true` to avoid re-querying
2. **Batching**: Optimize `batch_size` for your API rate limits
3. **Stratification**: Use stratified sampling for balanced evaluation
4. **Parallel Processing**: Can be added to `BatchEvaluator` for local models

## References

### Related Work
- LongBench, SoCkET for long-context reasoning
- O'Connor et al. (2022) on conversation trees
- Kadavath et al. (2022) on LLM calibration
- Lin et al. (2024) on uncertainty in LLMs

### Paper Sections
This framework directly supports:
- **Section 3**: Dataset construction with context decomposition
- **Section 4**: Experimental design with ablation scheme
- **Section 5**: Results with accuracy/calibration/interaction analysis
- **Section 6**: Discussion with sensitivity and error analysis



## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## Support

For issues or questions:
- Check the troubleshooting section above
- Review the paper outline for methodological context
- Examine example outputs in `results/` directory

---

**Last Updated**: November 5, 2025
**Version**: 1.0
