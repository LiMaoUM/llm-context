# Implementation Checklist & Quick Reference

---

## 📁 Complete File Structure

```
llm-context/
├── README.md                      # Getting started & API reference
├── EXPERIMENT_DESIGN.md           # Detailed experimental design
├── FRAMEWORK_SUMMARY.md           # Complete framework overview
├── ARCHITECTURE.md                # System architecture & design
├── IMPLEMENTATION_CHECKLIST.md    # This file
│
├── experiment_config.yaml         # Main configuration (8 contexts, 6 models, 2 tasks)
│
├── data_loader.py                 # Data loading & context generation
│   ├─ DataLoader (load, explore, retrieve context)
│   └─ ContextVariantGenerator (create 8 context variants)
│
├── llm_inference.py               # LLM inference system
│   ├─ LLMProvider (abstract base)
│   ├─ OpenAIProvider (GPT-4, GPT-3.5)
│   ├─ AnthropicProvider (Claude-3)
│   ├─ HuggingFaceProvider (Llama, Gemma)
│   ├─ InferencePipeline
│   └─ BatchEvaluator
│
├── evaluation_metrics.py          # All metrics computation
│   ├─ CalibrationMetrics (ECE, Brier, overconfidence)
│   ├─ ContextSensitivityMetrics (marginal improvements, diminishing returns)
│   └─ ComprehensiveMetrics (all metrics combined)
│
├── analysis_visualization.py      # Analysis & visualization
│   ├─ ResultsAnalyzer
│   └─ ResultsVisualizer (6 standard plots)
│
├── run_experiment.py              # Main orchestrator (6-step pipeline)
│   └─ ExperimentRunner
│
├── requirements.txt               # Production dependencies
├── requirements-dev.txt           # Development dependencies
│
└── data/                          # Input data folder
    ├── posts/posts.parquet
    ├── users/users.parquet
    ├── interactions/interactions.parquet
    ├── post_edges/post_edges.parquet
    ├── cascades_nodes/cascades_nodes.parquet
    └── tree_features/tree_features.parquet
```

---

## ✅ Pre-Implementation Checklist

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment created
- [ ] Dependencies installed from `requirements.txt`
- [ ] API keys set for OpenAI, Anthropic (if using)

### Data Preparation
- [ ] Data files verified in `data/` folder
- [ ] Data summary generated (`python run_experiment.py --steps explore`)
- [ ] Annotation guidelines prepared
- [ ] ~10k samples identified and labeled

### Configuration
- [ ] `experiment_config.yaml` reviewed
- [ ] Models to use confirmed
- [ ] Context variants understood
- [ ] Target tasks and entities specified

---

## 🚀 Step-by-Step Implementation

### Phase 1: Data Exploration & Preparation (Week 1)

#### Day 1: Data Loading
```bash
# Activate environment
source venv/bin/activate

# Run data exploration
python run_experiment.py --config experiment_config.yaml --steps explore

# Check output
cat results/data_summary.json | jq .
```
- [ ] Data loads successfully
- [ ] Schema understood
- [ ] Sample counts verified

#### Day 2: Context Generation
```bash
# Generate and test context variants on small sample
python run_experiment.py --config experiment_config.yaml --steps explore variants
```
- [ ] 8 context variants generated correctly
- [ ] Format validated
- [ ] Sample structure saved

#### Day 3-5: Annotation Setup
- [ ] Annotation protocol finalized
- [ ] Annotators recruited (1-2 primary, 1 adjudicator)
- [ ] Inter-rater agreement pilot (100 posts)
- [ ] Iterate on protocol based on pilot
- [ ] Full annotation begins

### Phase 2: LLM Inference (Week 2-3)

#### Day 1: API Setup & Testing
```bash
# Verify API credentials
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Test with single model on small batch
python -c "
from llm_inference import InferencePipeline
import yaml

with open('experiment_config.yaml') as f:
    config = yaml.safe_load(f)

config['models'] = [config['models'][0]]  # Just first model
pipeline = InferencePipeline(config)

prompt = 'What is the sentiment of this post? I love this policy!'
result = pipeline.query_model('gpt-4-turbo', prompt)
print(result)
"
```
- [ ] OpenAI API works
- [ ] Anthropic API works (if using)
- [ ] Confidence extraction works

#### Day 2-5: Full Inference
```bash
# Run inference on prepared samples
python run_experiment.py --config experiment_config.yaml --steps inference

# Check intermediate results
tail -20 results/inference_results.json
```
- [ ] All models queried successfully
- [ ] Confidence extracted from responses
- [ ] Cache mechanism working
- [ ] Results saved with timestamps
- [ ] No rate limiting issues
- [ ] Error recovery working

### Phase 3: Metrics & Analysis (Week 3-4)

#### Day 1-2: Metrics Computation
```bash
# Compute all metrics
python run_experiment.py --config experiment_config.yaml --steps metrics
```
- [ ] Accuracy computed
- [ ] F1 scores calculated
- [ ] ECE computed correctly
- [ ] Overconfidence rates calculated
- [ ] Context sensitivity analyzed

#### Day 3-5: Visualization & Analysis
```bash
# Generate plots and report
python run_experiment.py --config experiment_config.yaml --steps analysis report
```
- [ ] All 6 plots generated
- [ ] Calibration curves look reasonable
- [ ] Heatmaps readable
- [ ] Summary statistics computed
- [ ] Key findings identified

---

## 🔧 Configuration Quick Reference

### experiment_config.yaml

```yaml
# Models - Add/remove as needed
models:
  - name: "gpt-4-turbo"
    provider: "openai"
    config:
      model_id: "gpt-4-turbo-preview"
      temperature: 0.7
      max_tokens: 256

# Context variants - All 8 included
context_variants:
  - variant_name: "T"      # Text only
  - variant_name: "T+C"    # + Conversation
  - variant_name: "T+B"    # + Background
  - variant_name: "T+M"    # + Metadata
  # ... etc

# Prompt template - Standardized format
prompt_template: |
  [BACKGROUND]...
  [CONVERSATION]...
  [METADATA]...
  [TARGET POST]
  Question: ...

# Tasks - Can add more
tasks:
  - task_id: "stance_detection"
    target_entities: ["Biden", "Trump", ...]
    stance_options: ["strongly support", "support", "neutral", "oppose", "strongly oppose"]

# Metrics - All included
evaluation_metrics:
  accuracy: ...
  f1_score: ...
  ece: ...
  # ... etc

# Execution - Tune as needed
execution:
  batch_size: 32
  max_retries: 3
  retry_delay: 2
  cache_responses: true
  save_interval: 100
  output_dir: "./results"
```

---

## 📊 Output Validation

### Expected Outputs by Step

#### Step 1: Exploration
```json
results/data_summary.json
{
  "posts": {
    "total_count": 1000,
    "columns": ["id", "text", "author_id", ...],
    "sample": {...}
  },
  "users": {...},
  ...
}
```
- ✓ Contains all dataset descriptions
- ✓ Sample records visible
- ✓ Column names match expected schema

#### Step 2: Variants
```json
results/sample_variants.json
{
  "sample_id": "...",
  "context_variants": {
    "T": "Post text only",
    "T+C": "Post + conversation...",
    "T+B": "Post + background...",
    ...
    "FULL": "All contexts..."
  }
}
```
- ✓ All 8 variants present
- ✓ Format consistent
- ✓ Text content looks reasonable

#### Step 3: Inference
```json
results/inference_results.json
[
  {
    "sample_id": "...",
    "variants": {
      "T": {
        "model_results": {
          "gpt-4": {
            "success": true,
            "response_text": "...",
            "confidence": 85.0
          },
          ...
        }
      },
      ...
    }
  }
]
```
- ✓ All samples processed
- ✓ All contexts included
- ✓ All models queried
- ✓ Confidence values in 0-100 range
- ✓ Some failures acceptable (<5%)

#### Step 4: Metrics
```json
results/metrics_by_model.json
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
  ...
}
```
- ✓ All metrics present
- ✓ Values in expected ranges
- ✓ All model-variant combinations
- ✓ Metrics reasonable (not all 0 or 1)

#### Step 5: Visualizations
```
results/figures/
├─ accuracy_by_context.png        ✓ Clear trend lines
├─ calibration_curve.png          ✓ Scores visible with sizes
├─ ece_by_context.png             ✓ ECE values plotted
├─ overconfidence_by_context.png  ✓ Rates shown
├─ context_sensitivity_heatmap.png ✓ Readable color map
└─ marginal_improvements.png      ✓ Grouped bars visible
```
- ✓ All plots generated
- ✓ Axes labeled clearly
- ✓ Legends present
- ✓ File sizes reasonable (>50KB)

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "API key not found" | Missing env vars | `export OPENAI_API_KEY="sk-..."` |
| "No module named 'openai'" | Package not installed | `pip install -r requirements.txt` |
| "Connection timeout" | Rate limit / network | ↑ `retry_delay`, ↓ `batch_size` |
| "Memory error" | Too many samples | ↓ `batch_size`, process in chunks |
| "Empty results" | Data path wrong | Verify `data/` folder exists |
| "Very low accuracy" | Task too hard | Check annotation quality first |
| "Plots not generated" | Matplotlib issue | `pip install --upgrade matplotlib` |

---

## 📈 Expected Performance Metrics

### Baseline Expectations

```
Task: Stance Detection

Accuracy:
  • T (baseline):           60-70%
  • T+C (+ conversation):   70-75% (+5-10%)
  • T+B (+ background):     72-78% (+8-15%)
  • T+M (+ metadata):       62-72% (+2-8%)
  • FULL:                   78-85% (+15-25% from baseline)

ECE (Expected Calibration Error):
  • Well-calibrated model:  0.05-0.15
  • Poorly-calibrated:      0.20-0.40
  • Overconfident:          0.30+

Overconfidence Rate (% wrong with >70% conf):
  • Well-calibrated:        10-20%
  • Overconfident:          30-50%

Model Ranking (typical):
  1. GPT-4 (highest accuracy, good calibration)
  2. Claude-3 Opus (similar to GPT-4)
  3. Claude-3 Sonnet (slightly lower)
  4. Llama-2-70B (comparable to Claude)
  5. Gemma-2-27B (lower accuracy but efficient)
  6. GPT-3.5 (fastest but lower quality)
```

---

## 🔬 Analysis Commands

### Quick Checks

```bash
# Check data is loaded
python -c "
from data_loader import DataLoader
loader = DataLoader()
summary = loader.get_data_summary()
print(f\"Posts: {summary['posts']['total_count']}\")
"

# Test context generation
python -c "
from data_loader import DataLoader, ContextVariantGenerator
loader = DataLoader()
loader.load_all()
gen = ContextVariantGenerator(loader)
sample = loader.get_post_with_all_context(loader.posts.iloc[0]['id'])
variants = gen.generate_variants(sample)
print(f\"Generated {len(variants)} variants\")
"

# Test metrics
python -c "
from evaluation_metrics import ComprehensiveMetrics
import numpy as np
y_true = np.array([0,1,1,0,1])
y_pred = np.array([0,1,1,0,1])
conf = np.array([95,88,92,90,85])
metrics = ComprehensiveMetrics.compute_all_metrics(y_true, y_pred, conf)
print(f\"Accuracy: {metrics['accuracy']:.2f}\")
print(f\"ECE: {metrics['ece']:.3f}\")
"

# Check results
python -c "
import json
with open('results/metrics_by_model.json') as f:
    metrics = json.load(f)
    for model in metrics:
        acc = metrics[model]['T']['accuracy']
        print(f\"{model}: {acc:.3f}\")
"
```

---

## 📚 Documentation Map

| Document | Purpose | When to Use |
|----------|---------|------------|
| README.md | Setup & usage | Starting out, basic questions |
| EXPERIMENT_DESIGN.md | Detailed design | Understanding methodology |
| FRAMEWORK_SUMMARY.md | Complete overview | High-level understanding |
| ARCHITECTURE.md | System design | Deep technical understanding |
| This file | Implementation guide | Running the experiment |

---

## 🎓 Key Concepts to Understand

### Context Dimensions
- **C (Conversation)**: Local discourse context (parent/child posts)
- **B (Background)**: World knowledge, event context
- **M (Metadata)**: Social signals (user profile, followers, verification)

### Metrics Explained
- **Accuracy**: % correct predictions
- **ECE**: Average |confidence - accuracy| per confidence bin (lower = better calibrated)
- **Overconfidence Rate**: % of wrong predictions made with >70% confidence
- **Context Sensitivity**: How much accuracy varies across context conditions

### Expected Findings
- Conversation helps most (highest marginal improvement)
- Background helps significantly
- Metadata has small marginal effect
- Larger models better calibrated
- Diminishing returns after context depth 3

---

## 🚦 Go/No-Go Criteria

### Before Starting Inference
- [ ] Data summary generated without errors
- [ ] Context variants generate correctly
- [ ] Sample variant structure looks good
- [ ] Ground truth labels prepared (or weak labels)
- [ ] API keys tested and working
- [ ] Can query at least one model successfully

### Before Running Full Experiment
- [ ] Test batch (100 samples) runs end-to-end
- [ ] Results saved correctly
- [ ] Metrics computed without errors
- [ ] Plots generate successfully
- [ ] ~5% error rate acceptable on inference

### Before Analysis
- [ ] All 6 models × 8 contexts queried
- [ ] >90% success rate on inference
- [ ] Ground truth labels validated
- [ ] Metrics computed for all conditions
- [ ] No obvious outliers or errors in data

---

## 📞 Support Resources

### If you're stuck:
1. Check README.md "Troubleshooting"
2. Review EXPERIMENT_DESIGN.md for methodology
3. Check log output for specific errors
4. Verify data in results/ directory
5. Run smaller test batches first

### Key files for debugging:
- `results/data_summary.json` - Data schema issues
- `results/inference_results.json` - Inference problems
- `results/metrics_by_model.json` - Metrics computation issues
- `results/figures/` - Visualization issues

---

## 📅 Typical Timeline

```
Week 1:  Data exploration & context preparation (1-2 days)
         Annotation setup & pilot (3-4 days)

Week 2:  Annotation (ongoing)
         API setup & inference (1-2 days)
         Run inference on full dataset (3-5 days)

Week 3:  Continue inference if needed
         Compute metrics (1 day)
         Generate analysis & visualizations (1-2 days)

Week 4:  Error analysis & case studies (1-2 days)
         Statistical testing (1-2 days)
         Write up results (2-3 days)
```

---

## ✨ After Running Experiment

### Suggested Next Steps
1. **Validate Results**
   - [ ] Check results against expectations
   - [ ] Identify outliers or anomalies
   - [ ] Verify with manual spot-checks

2. **Deeper Analysis**
   - [ ] Statistical significance testing
   - [ ] Subgroup analysis (by event, stance, etc.)
   - [ ] Error categorization
   - [ ] Case study selection

3. **Paper Writing**
   - [ ] Draft results section
   - [ ] Create publication-quality figures
   - [ ] Write discussion
   - [ ] Add to methods section

4. **Reproducibility**
   - [ ] Archive all code and config
   - [ ] Document any manual decisions
   - [ ] Create data/code repository
   - [ ] Write reproducibility statement

---

**Implementation Guide Version**: 1.0  
**Last Updated**: November 5, 2025  
**Status**: Ready for Production
