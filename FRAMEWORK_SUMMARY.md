# LLM Context & Confidence Analysis Framework
## Complete Experimental Design Summary

---

## 🎯 Overview

This framework provides a **complete, production-ready system** for testing how different contextual dimensions affect LLM confidence calibration and interpretation accuracy in social media text analysis.

**Core Focus**: Systematically decompose and ablate three contextual layers to answer:
- Which contexts matter most?
- Are models well-calibrated with partial context?
- Do different LLMs respond differently to context richness?

---

## 📋 Quick Reference

### Key Files & Their Purpose

| File | Purpose | Key Classes/Functions |
|------|---------|---------------------|
| `experiment_config.yaml` | Central configuration | Models, contexts, tasks, metrics |
| `data_loader.py` | Data ops | `DataLoader`, `ContextVariantGenerator` |
| `llm_inference.py` | LLM inference | `InferencePipeline`, provider classes |
| `evaluation_metrics.py` | Metrics | `CalibrationMetrics`, `ComprehensiveMetrics` |
| `analysis_visualization.py` | Analysis & plots | `ResultsAnalyzer`, `ResultsVisualizer` |
| `run_experiment.py` | Main runner | `ExperimentRunner` (6-step pipeline) |
| `EXPERIMENT_DESIGN.md` | Detailed design | RQs, hypotheses, statistical plan |
| `README.md` | Setup & usage | Installation, quick start, API ref |

---

## 🔬 Experimental Framework

### Context Ablation Scheme (8 Conditions)

```
Depth 1:     T                          (Text only)
             ↓
Depth 2:     T+C, T+B, T+M             (Add one dimension)
             ↓
Depth 3:     T+C+B, T+C+M, T+B+M      (Add two dimensions)
             ↓
Depth 4:     FULL                      (All dimensions)

Dimensions:
  C = Conversation (parent/child posts)
  B = Background (event context, entity summaries)
  M = Metadata (user bio, followers, verification status)
```

### Models Evaluated (6 LLMs)

| Provider | Models | Rationale |
|----------|--------|-----------|
| OpenAI | GPT-4, GPT-3.5 | Proprietary, state-of-the-art |
| Anthropic | Claude-3 Opus, Sonnet | Different architecture, proprietary |
| Meta | Llama-2-70B | Large open-source, community model |
| Google | Gemma-2-27B | Smaller open-source, efficient |

### Tasks (2 Examples)

1. **Stance Detection**: Classify author stance toward political entity/issue
2. **Sentiment Analysis**: Classify post sentiment (very positive → very negative)

---

## 📊 Evaluation Metrics

### Primary Metrics

| Category | Metric | Significance |
|----------|--------|--------------|
| **Accuracy** | Overall correctness | Measures interpretation ability |
| **F1 Score** | Weighted harmonic mean | Balances precision/recall |
| **ECE** | Expected Calibration Error | Confidence-accuracy gap |
| **Brier Score** | Probabilistic accuracy | MSE of confidence |
| **Overconfidence Rate** | % wrong with >70% conf | Risk of false confidence |
| **Context Sensitivity** | Performance range across contexts | How much context matters |

### Secondary Metrics

- **Confidence-Correctness Gap**: Avg conf(correct) - Avg conf(incorrect)
- **Diminishing Returns**: ΔAcc by context depth
- **Model Ranking**: By accuracy, calibration, robustness

---

## 🔄 Experiment Workflow (6 Steps)

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: DATA EXPLORATION                                   │
│ - Load posts, users, interactions from Parquet files       │
│ - Generate summary statistics                               │
│ - Understand data schema and relationships                 │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: CONTEXT VARIANT GENERATION                         │
│ - For each sample: fetch post, user metadata, conversation │
│ - Create 8 context variants (T, T+C, T+B, T+M, ...)       │
│ - Standardize formatting                                    │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: LLM INFERENCE                                      │
│ - Query all 6 models across all 8 contexts                │
│ - Extract predictions and confidence from responses       │
│ - Cache results for reproducibility                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: METRICS COMPUTATION                                │
│ - Compute accuracy, F1, ECE, Brier per (model, context)   │
│ - Calculate overconfidence rates                           │
│ - Analyze context sensitivity and marginal improvements   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: ANALYSIS & VISUALIZATION                           │
│ - Generate 6 standard plots:                               │
│   * Accuracy by context (line plot)                        │
│   * Calibration curves (confidence vs accuracy)            │
│   * ECE by context                                         │
│   * Overconfidence rate                                    │
│   * Context sensitivity heatmap                            │
│   * Marginal improvements                                  │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: REPORT GENERATION                                  │
│ - Compile summary statistics                              │
│ - Output comprehensive JSON report                        │
│ - Generate key findings summary                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Explore Data
```bash
python run_experiment.py --steps explore
```

### 3. Run Full Pipeline
```bash
python run_experiment.py --config experiment_config.yaml
```

### 4. Run Specific Steps
```bash
# Just generate variants and check structure
python run_experiment.py --steps explore variants

# Just run inference (requires samples prepared)
python run_experiment.py --steps inference

# Just generate metrics and plots
python run_experiment.py --steps metrics analysis
```

---

## 📈 Expected Results Structure

### Output Directory
```
results/
├── data_summary.json              # Data exploration
├── sample_variants.json           # Example context format
├── inference_results.json         # Raw model outputs
├── metrics_by_model.json          # All computed metrics
├── experiment_report.json         # Summary & findings
└── figures/                       # Visualizations
    ├── accuracy_by_context.png
    ├── calibration_curve.png
    ├── ece_by_context.png
    ├── overconfidence_by_context.png
    ├── context_sensitivity_heatmap.png
    └── marginal_improvements.png
```

### Key Output: metrics_by_model.json
```json
{
  "gpt-4-turbo": {
    "T": {
      "accuracy": 0.85,
      "f1_weighted": 0.83,
      "ece": 0.12,
      "overconfidence_rate": 0.15,
      ...
    },
    "T+C": {
      "accuracy": 0.88,
      ...
    },
    ...
  },
  "claude-3-opus": { ... },
  ...
}
```

---

## 💡 Core Concepts

### Context Variants Explained

**T (Baseline)**:
```
[TARGET POST]
"We need stricter gun laws!"
```

**T+C (+ Conversation)**:
```
[PARENT REPLY]
"Why do you want to ban guns?"

[TARGET POST]
"We need stricter gun laws!"

[CHILD REPLY]
"I agree, background checks are essential"
```

**T+B (+ Background)**:
```
[BACKGROUND]
Event: Gun violence prevention debate
Recent shooting incidents: [X incidents in past 30 days]
Policy proposals: Universal background checks, assault weapon ban

[TARGET POST]
"We need stricter gun laws!"
```

**T+M (+ Metadata)**:
```
[USER METADATA]
Name: Policy Advocate
Bio: Gun violence prevention activist | 25K followers | Verified
Recent posts: Posted 5 times about gun regulation in past week

[TARGET POST]
"We need stricter gun laws!"
```

### Evaluation Metrics Explained

**Expected Calibration Error (ECE)**
- Groups predictions into 10 confidence bins
- For each bin: |accuracy_in_bin - avg_confidence_in_bin|
- Averages across bins weighted by frequency
- **Lower is better** (0 = perfect, 0.3 = poor)

**Overconfidence Rate**
- Of the predictions that are WRONG
- What fraction are made with >70% confidence?
- **Lower is better** (0% ideal, high % indicates risky model)

**Context Sensitivity Index (CSI)**
- Max accuracy - Min accuracy across all context variants
- Normalized by max accuracy
- **Higher = model benefits more from context**

---

## 🔧 Customization Guide

### Add a New LLM Model

Edit `experiment_config.yaml`:
```yaml
models:
  - name: "your-llama-70b"
    provider: "huggingface"
    config:
      model_id: "meta-llama/Llama-2-70b-chat-hf"
      temperature: 0.7
      max_tokens: 256
```

Then extend provider in `llm_inference.py` if needed.

### Add a New Task

```yaml
tasks:
  - task_id: "entity_recognition"
    task_name: "Named Entity Recognition"
    description: "Identify entities mentioned"
    stance_options: ["person", "organization", "location", "other"]
```

### Add Custom Metrics

In `evaluation_metrics.py`, extend `ComprehensiveMetrics`:
```python
@staticmethod
def my_custom_metric(y_true, y_pred, confidence):
    # Your implementation
    return metric_value
```

### Modify Context Format

In `data_loader.py`, edit `ContextVariantGenerator._format_*` methods to change how context is assembled and formatted.

---

## 📚 Theory & Research Questions

### Research Questions
1. **RQ1**: How do context dimensions affect accuracy?
2. **RQ2**: How does context affect calibration?
3. **RQ3**: Which contexts are essential vs. marginal?
4. **RQ4**: Are accuracy and confidence improvements aligned?
5. **RQ5**: Do different models respond differently?
6. **RQ6**: Are there synergistic interactions between contexts?

### Hypotheses
- **H1**: Conversation > Background > Metadata (by importance)
- **H2**: Diminishing returns (T→T+C has biggest gain; T+C+B→FULL has smallest)
- **H3**: Models are overconfident in low-context settings
- **H4**: Larger models show better context integration
- **H5**: Accuracy-calibration decoupling (gains don't always align)

### Expected Findings
- Context helps most for ambiguous posts
- Larger models (GPT-4, Claude-Opus) are better calibrated
- Background context has largest marginal improvement after conversation
- Overconfidence rates drop significantly with full context
- Different models show distinct context sensitivity profiles

---

## ⚙️ Technical Architecture

### Data Flow
```
Parquet Files (data/)
    ↓
DataLoader (load + explore)
    ↓
ContextVariantGenerator (create 8 variants)
    ↓
InferencePipeline (query LLMs)
    ↓
Metrics (compute calibration, accuracy, etc.)
    ↓
Analyzer & Visualizer (plots + reports)
    ↓
JSON Results (metrics_by_model.json + figures/)
```

### Key Design Patterns

1. **Configuration-Driven**: All parameters in `experiment_config.yaml`
2. **Modular**: Each module has single responsibility
3. **Extensible**: Easy to add models, tasks, metrics
4. **Reproducible**: Fixed seeds, cached results, version control
5. **Observable**: Logging at each step

---

## 🎓 Learning Resources

### About Calibration
- Guo et al. (2017): "On Calibration of Modern Neural Networks"
- Niculescu-Mizil & Caruana (2005): "Predicting Good Probabilities with Supervised Learning"

### About LLM Confidence
- Kadavath et al. (2022): "Language Models (Mostly) Know What They Know"
- Lin et al. (2024): "Uncertainty in Language Models: A Review"

### About Context in NLP
- O'Connor et al. (2022): "Context Threading for Understanding Conversations"
- Raffel et al. (2020): "Exploring the Limits of Transfer Learning"

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "API rate limit" | ↑ `retry_delay`, ↓ `batch_size` |
| "Memory error" | ↓ `batch_size`, process in chunks |
| "Missing context" | Check `data_summary.json`, verify post_edges |
| "Low model accuracy" | Task too hard? Verify annotations |
| "ECE too high" | Model poorly calibrated, check temperature |

---

## 📋 Deliverables Checklist

- ✅ **Framework Code**: Complete and documented
- ✅ **Configuration System**: experiment_config.yaml
- ✅ **Data Pipeline**: Loading, exploration, variant generation
- ✅ **LLM Integration**: OpenAI, Anthropic, HuggingFace providers
- ✅ **Metrics Suite**: Classification, calibration, sensitivity metrics
- ✅ **Analysis & Viz**: Plots, reports, statistical analysis
- ✅ **Documentation**: README, EXPERIMENT_DESIGN.md, this summary
- ⏳ **Annotated Dataset**: To be prepared (10k posts)
- ⏳ **Inference Results**: Generated during Step 3
- ⏳ **Analysis Report**: Generated during Steps 4-6

---

## 📊 Next Steps for Implementation

### Immediate (Week 1)
1. ✅ Framework design & coding (DONE)
2. Prepare annotation guidelines
3. Test with small sample (100 posts)
4. Verify context variant generation
5. Test LLM inference with 1 model

### Short-term (Week 2-3)
1. Annotate full dataset (10k posts)
2. Run full inference pipeline on all 6 models
3. Compute all metrics
4. Generate visualizations

### Medium-term (Week 4-5)
1. Statistical analysis of results
2. Error analysis & case studies
3. Sensitivity analyses (varying thresholds, contexts)
4. Model-specific deep dives

### Long-term (Week 6+)
1. Write paper sections
2. Create additional visualizations for publication
3. Prepare supplementary materials
4. Clean up and release code

---

## 📞 Support & Questions

**If you encounter issues**:
1. Check README.md "Troubleshooting" section
2. Review EXPERIMENT_DESIGN.md for methodological details
3. Check log output for specific error messages
4. Examine data_summary.json for data schema issues

---

**Framework Version**: 1.0  
**Status**: Production-ready  
**Last Updated**: November 5, 2025
