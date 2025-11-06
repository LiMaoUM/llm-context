# Architecture & Components Guide

## System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         LLM CONTEXT EXPERIMENT                     │
│                      Confidence & Calibration Study                │
└────────────────────────────────────────────────────────────────────┘

                              INPUT LAYER
                         ┌───────────────────┐
                         │   Parquet Files   │
                         │  (Social Media)   │
                         │                   │
                         │  - posts          │
                         │  - users          │
                         │  - interactions   │
                         │  - post_edges     │
                         │  - cascades       │
                         │  - tree_features  │
                         └────────┬──────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │    DATA LOADING LAYER     │
                    │  (data_loader.py)         │
                    │                           │
                    │  • DataLoader             │
                    │  • Data exploration       │
                    │  • Context retrieval      │
                    └─────────────┬──────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  CONTEXT GENERATION       │
                    │  (data_loader.py)         │
                    │                           │
                    │  • T                      │
                    │  • T+C, T+B, T+M          │
                    │  • T+C+B, T+C+M, T+B+M    │
                    │  • FULL                   │
                    │                           │
                    │  Context variants:        │
                    │  [8 conditions]           │
                    └─────────────┬──────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼─────┐        ┌────────▼────────┐        ┌────▼──────┐
    │  LANGUAGE │        │   LANGUAGE      │        │ LANGUAGE  │
    │   MODELS  │        │     MODELS      │        │  MODELS   │
    │           │        │                 │        │           │
    │ OpenAI    │        │  Anthropic      │        │HuggingFace│
    │ • GPT-4   │        │ • Claude-3      │        │ • Llama   │
    │ • GPT-3.5 │        │   Opus/Sonnet   │        │ • Gemma   │
    └─────┬─────┘        └────────┬────────┘        └────┬──────┘
          │                       │                      │
          │          ┌────────────┼──────────────┐       │
          │          │                           │       │
          └──────────► INFERENCE PIPELINE        ◄───────┘
                      │ (llm_inference.py)      │
                      │                         │
                      │ • LLMProvider           │
                      │ • InferencePipeline     │
                      │ • BatchEvaluator        │
                      │                         │
                      │ Queries: 6 models ×     │
                      │          8 contexts ×   │
                      │          N samples      │
                      └────────────┬────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │  METRICS COMPUTATION        │
                    │ (evaluation_metrics.py)     │
                    │                             │
                    │ • Classification Metrics   │
                    │   - Accuracy              │
                    │   - F1 Score              │
                    │                             │
                    │ • Calibration Metrics     │
                    │   - ECE                   │
                    │   - Brier Score           │
                    │   - Overconfidence Rate   │
                    │                             │
                    │ • Sensitivity Metrics     │
                    │   - Marginal Improvements │
                    │   - Context Sensitivity   │
                    │   - Diminishing Returns   │
                    └────────────┬────────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │ ANALYSIS & VISUALIZATION  │
                    │(analysis_visualization.py)│
                    │                           │
                    │ • ResultsAnalyzer         │
                    │ • ResultsVisualizer       │
                    │                           │
                    │ Outputs:                  │
                    │ • 6 key plots             │
                    │ • Statistical summaries   │
                    │ • Error analysis          │
                    └────────────┬────────────────┘
                                 │
                         RESULTS LAYER
                         ┌─────────────┐
                         │   JSON      │
                         │  Reports    │
                         │  & Figures  │
                         └─────────────┘
```

---

## Module Dependency Graph

```
        run_experiment.py (Main Orchestrator)
               │
        ┌──────┼──────────┬──────────┐
        │      │          │          │
        ▼      ▼          ▼          ▼
    data_      llm_      evaluation_  analysis_
    loader.py  inference metrics.py   visualization.py
       │          │         │             │
       │          │         │             │
    [Classes]  [Classes]  [Classes]   [Classes]
    --------   --------   --------    --------
    • DataL.  • OpenAI    • Calibr.  • Results
    • Context Prov.       Metrics    Analyzer
    Generator • Anthrop.  • Context  • Results
              Prov.       Sensitivity Visualizer
              • HF Prov.  Metrics
              • Pipeline
              • Evaluator

Configuration Layer:
experiment_config.yaml (All hyperparameters & settings)
```

---

## Data Flow: Step-by-Step

### Step 1: Data Exploration

```
Input:  Parquet files
        │
        ├─► DataLoader.load_all()
        │       └─► pandas.read_parquet()
        │
        ├─► DataLoader.get_data_summary()
        │       └─► Returns schema, counts, samples
        │
Output: data_summary.json
        {
          "posts": {"total_count": ..., "columns": [...], ...},
          "users": {...},
          "interactions": {...},
          ...
        }
```

### Step 2: Context Variant Generation

```
Input:  Posts + Users + Edges from DataLoader
        │
        ├─► For each sample:
        │
        ├─► DataLoader.get_post_with_all_context()
        │   ├─► Get post text
        │   ├─► Get user metadata
        │   └─► Get conversation thread
        │
        ├─► ContextVariantGenerator.generate_variants()
        │   ├─► _format_text_only()          → T
        │   ├─► _format_text_conversation()  → T+C
        │   ├─► _format_text_background()    → T+B
        │   ├─► _format_text_metadata()      → T+M
        │   ├─► _format_text_conversation_background() → T+C+B
        │   ├─► _format_text_conversation_metadata()   → T+C+M
        │   ├─► _format_text_background_metadata()     → T+B+M
        │   └─► _format_full_context()                 → FULL
        │
Output: Sample with 8 context variants
        {
          "sample_id": "...",
          "context_variants": {
            "T": "Post text only",
            "T+C": "Post + conversation",
            "T+B": "Post + background",
            ...
            "FULL": "All contexts"
          }
        }
```

### Step 3: LLM Inference

```
Input:  Samples with context variants
        │
        ├─► InferencePipeline.__init__(config)
        │   └─► Instantiate provider for each model
        │       • OpenAIProvider
        │       • AnthropicProvider
        │       • HuggingFaceProvider
        │
        ├─► BatchEvaluator.evaluate_batch()
        │   For each sample:
        │     For each variant:
        │       For each model:
        │         ├─► Create prompt from context
        │         ├─► Call InferencePipeline.query_model()
        │         │   └─► provider.query(prompt)
        │         │       ├─► API call (with retry logic)
        │         │       ├─► Extract confidence from response
        │         │       └─► Return response + confidence
        │         └─► Store result
        │
Output: inference_results.json
        {
          "sample_id": "...",
          "variants": {
            "T": {
              "prompt": "...",
              "model_results": {
                "gpt-4": {
                  "response_text": "...",
                  "confidence": 85.0,
                  "success": true
                },
                "claude-3-opus": {...},
                ...
              }
            },
            "T+C": {...},
            ...
          }
        }
```

### Step 4: Metrics Computation

```
Input:  Inference results + ground truth labels
        │
        ├─► For each (model, variant) pair:
        │
        ├─► Extract (y_true, y_pred, confidence)
        │
        ├─► ComprehensiveMetrics.compute_all_metrics()
        │   ├─► Classification:
        │   │   ├─► accuracy_score()
        │   │   └─► f1_score()
        │   │
        │   ├─► Calibration:
        │   │   ├─► CalibrationMetrics.expected_calibration_error()
        │   │   │   └─► Bin-wise accuracy vs confidence analysis
        │   │   └─► CalibrationMetrics.overconfidence_rate()
        │   │       └─► % incorrect with high confidence
        │   │
        │   └─► Confidence:
        │       └─► CalibrationMetrics.confidence_by_correctness()
        │           └─► Compare conf for correct vs incorrect
        │
Output: metrics_by_model.json
        {
          "gpt-4-turbo": {
            "T": {
              "accuracy": 0.85,
              "f1_weighted": 0.83,
              "ece": 0.12,
              "overconfidence_rate": 0.15,
              ...
            },
            "T+C": {...},
            ...
          },
          "claude-3-opus": {...},
          ...
        }
```

### Step 5: Analysis & Visualization

```
Input:  Metrics by model
        │
        ├─► ResultsAnalyzer
        │   ├─► compute_model_metrics_by_variant()
        │   └─► extract_calibration_data()
        │
        ├─► ResultsVisualizer.generate_all_plots()
        │   ├─► plot_accuracy_by_context()
        │   │   └─► Line plot: accuracy vs context (by model)
        │   │
        │   ├─► plot_calibration_curve()
        │   │   └─► Scatter: confidence vs actual accuracy
        │   │
        │   ├─► plot_ece_by_context()
        │   │   └─► Line plot: ECE vs context
        │   │
        │   ├─► plot_overconfidence_rate()
        │   │   └─► Bar plot: overconfidence vs context
        │   │
        │   ├─► plot_context_sensitivity_heatmap()
        │   │   └─► Heatmap: models × contexts
        │   │
        │   └─► plot_marginal_improvements()
        │       └─► Bar plot: improvement from each context addition
        │
Output: results/figures/
        ├─► accuracy_by_context.png
        ├─► calibration_curve.png
        ├─► ece_by_context.png
        ├─► overconfidence_by_context.png
        ├─► context_sensitivity_heatmap.png
        └─► marginal_improvements.png
```

### Step 6: Report Generation

```
Input:  All metrics and statistics
        │
        ├─► Aggregate statistics by model
        ├─► Identify key findings
        ├─► Compile summary tables
        │
Output: experiment_report.json
        {
          "experiment_config": {...},
          "summary_statistics": {
            "gpt-4-turbo": {
              "variants": 8,
              "avg_accuracy": 0.86,
              "avg_ece": 0.11,
              ...
            },
            ...
          },
          "key_findings": [...]
        }
```

---

## Configuration Flow

```
experiment_config.yaml
    ├─► Models Configuration
    │   └─► Each model: provider + API params
    │
    ├─► Context Variants
    │   ├─► 8 variant definitions
    │   └─► Component specifications
    │
    ├─► Prompt Template
    │   └─► Standardized format for all models
    │
    ├─► Tasks
    │   ├─► Task ID & name
    │   ├─► Target entities
    │   └─► Stance/label options
    │
    ├─► Metrics
    │   ├─► Accuracy, F1
    │   ├─► ECE, Brier
    │   └─► Overconfidence, sensitivity
    │
    ├─► Analysis Sections
    │   ├─► Accuracy analysis
    │   ├─► Calibration analysis
    │   ├─► Interaction effects
    │   └─► Error analysis
    │
    └─► Execution Parameters
        ├─► Batch size, retries
        ├─► Output directory
        └─► Sampling strategy
```

---

## Error Handling & Validation

```
Data Quality Checks:
├─► DataLoader.get_data_summary()
│   └─► Validates schema, counts, types
│
├─► Context completeness checks
│   ├─► Missing posts?
│   ├─► Missing users?
│   └─► Missing edges?
│
├─► LLM inference error handling
│   ├─► API failures → Retry with exponential backoff
│   ├─► Rate limits → Adjust delays
│   ├─► Malformed responses → Log and skip
│   └─► Failed extractions → Mark confidence as None
│
└─► Metrics validation
    ├─► NaN/Inf checks
    ├─► Range validation (0-1 for probabilities)
    └─► Count mismatches
```

---

## Key Classes & Methods

### DataLoader
```python
DataLoader("./data")
├─ load_all()                      → Dict[str, DataFrame]
├─ get_data_summary()              → Dict
├─ get_user_metadata(user_id)      → Dict
├─ get_conversation_context(post_id) → Dict
└─ get_post_with_all_context(post_id) → Dict
```

### ContextVariantGenerator
```python
ContextVariantGenerator(loader)
├─ generate_variants(sample)       → Dict[str, str]
├─ _format_text_only()             → str
├─ _format_text_conversation()     → str
├─ _format_text_background()       → str
├─ _format_text_metadata()         → str
└─ ... (other format methods)
```

### LLMProvider (Abstract Base)
```python
LLMProvider(model_id)
├─ query(prompt)                   → (response, confidence, error)
└─ extract_confidence(response)    → float
```

### InferencePipeline
```python
InferencePipeline(config)
├─ __init__(config)
├─ query_model(model_name, prompt) → Dict
├─ query_all_models(prompt)        → Dict[str, Dict]
└─ evaluate_sample(...)            → Dict
```

### ComprehensiveMetrics
```python
ComprehensiveMetrics
├─ compute_all_metrics(y_true, y_pred, confidence) → Dict
└─ ... (calibration, confidence, etc.)
```

### ResultsVisualizer
```python
ResultsVisualizer(output_dir)
├─ plot_accuracy_by_context()
├─ plot_calibration_curve()
├─ plot_ece_by_context()
├─ plot_overconfidence_rate()
├─ plot_context_sensitivity_heatmap()
├─ plot_marginal_improvements()
└─ generate_all_plots()
```

---

## Extensibility Points

### Add a New LLM Provider

```python
# In llm_inference.py
class MyProvider(LLMProvider):
    def __init__(self, model_id, api_key=None, **kwargs):
        super().__init__(model_id, **kwargs)
        # Initialize client
    
    def query(self, prompt):
        # Call API
        # Extract confidence
        return response_text, confidence, error
```

### Add a New Metric

```python
# In evaluation_metrics.py
@staticmethod
def my_metric(y_true, y_pred, confidence):
    # Compute metric
    return metric_value

# In ComprehensiveMetrics.compute_all_metrics()
metrics['my_metric'] = MyMetrics.my_metric(...)
```

### Add a New Visualization

```python
# In analysis_visualization.py
def plot_my_visualization(self, data, save_name="my_plot.png"):
    fig, ax = plt.subplots()
    # Create plot
    plt.savefig(self.output_dir / save_name)
    plt.close()

# In ResultsVisualizer.generate_all_plots()
self.plot_my_visualization(metrics_by_model)
```

---

## Performance Considerations

### Optimization Strategies

1. **Caching**
   - Cache API responses (avoid re-querying)
   - Save intermediate results
   - Resume from checkpoints

2. **Batching**
   - Batch inference queries where possible
   - Parallel processing for local models
   - Async requests for API calls

3. **Memory Management**
   - Stream processing for large datasets
   - Discard intermediate objects
   - Use generators for large arrays

### Scalability

```
10k samples × 8 contexts × 6 models = 480,000 API calls

Estimated time:
- Rate limit: 100 req/min per model × $
- 6 models → ~6-12 hours (with retries, backoffs)
- Cache hits reduce this significantly

Memory usage:
- Results JSON: ~500MB
- Metrics: ~50MB
- Visualizations: ~20MB
- Total: ~600MB (manageable)
```

---

## Reproducibility Checklist

- ✅ Random seed fixed
- ✅ Config file version controlled
- ✅ API response caching
- ✅ Model versions pinned
- ✅ Data version in summary
- ✅ Results timestamped
- ✅ Code version tracked
- ✅ Dependencies specified (requirements.txt)

---

**Document Version**: 1.0  
**Last Updated**: November 5, 2025
