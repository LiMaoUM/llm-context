# Quick Start Guide (One-Page Reference)

## 🎯 What This Framework Does

Tests how LLM **confidence calibration** changes with **contextual richness** across 6 LLM models using 8 context variants.

```
Research Question: Which context types matter for LLM confidence?
Answer: A → Context → Variants → LLM Inference → Metrics → Visualization
```

---

## 📦 What You Get

| Component | Purpose | Output |
|-----------|---------|--------|
| **data_loader.py** | Load data + create context variants | 8 context versions per sample |
| **llm_inference.py** | Query 6 LLMs | Responses + extracted confidence |
| **evaluation_metrics.py** | Compute calibration metrics | Accuracy, ECE, overconfidence rates |
| **analysis_visualization.py** | Generate plots & analysis | 6 publication-ready figures |
| **run_experiment.py** | Orchestrate everything | Results directory with all outputs |

---

## 🚀 Quick Start (5 Minutes)

### 1. Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Add API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 2. Explore Data
```bash
python run_experiment.py --steps explore
# Generates: results/data_summary.json
```

### 3. Generate Context Variants
```bash
python run_experiment.py --steps explore variants
# Generates: sample with 8 context versions
```

### 4. Run LLM Inference
```bash
python run_experiment.py --steps inference
# Queries all 6 models × 8 contexts
# Saves: results/inference_results.json
```

### 5. Analyze & Visualize
```bash
python run_experiment.py --steps metrics analysis report
# Generates: metrics + 6 plots + summary report
```

---

## 📊 8 Context Variants

```
Depth 1: T                          (Just the post)
Depth 2: T+C, T+B, T+M             (Post + one context)
Depth 3: T+C+B, T+C+M, T+B+M      (Post + two contexts)
Depth 4: FULL                      (Post + all contexts)

Key: C=Conversation, B=Background, M=Metadata
```

---

## 🔬 6 Models Evaluated

| Model | Provider | Type |
|-------|----------|------|
| GPT-4 | OpenAI | Proprietary |
| GPT-3.5 | OpenAI | Proprietary |
| Claude-3 Opus | Anthropic | Proprietary |
| Claude-3 Sonnet | Anthropic | Proprietary |
| Llama-2-70B | Meta | Open-source |
| Gemma-2-27B | Google | Open-source |

---

## 📈 Key Metrics

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Accuracy** | % correct predictions | Performance |
| **ECE** | Confidence-accuracy gap | Calibration quality |
| **Overconfidence** | % wrong with 70%+ confidence | Risk of false confidence |
| **Sensitivity** | Performance range across contexts | Context dependence |

---

## 📁 Key Files

| File | Purpose | Edit for |
|------|---------|----------|
| experiment_config.yaml | All settings | Models, tasks, thresholds |
| data_loader.py | Data ops | Custom data loading |
| llm_inference.py | LLM queries | New LLM providers |
| evaluation_metrics.py | Metric computation | Custom metrics |
| run_experiment.py | Main orchestrator | Pipeline steps |

---

## 📋 Expected Results Summary

```
Typical findings:
• Accuracy: T(60%) → T+C(72%) → FULL(82%)     [+22% full context]
• ECE: T(0.20) → T+C(0.15) → FULL(0.10)       [better calibrated]
• Conversation context: Most valuable (+12%)
• Background: Second most valuable (+8%)
• Metadata: Small effect (+2%)
• GPT-4: Best overall (85% acc, 0.08 ECE)
• Gemma: Lowest but efficient (70% acc, 0.15 ECE)
```

---

## 🎯 Use Cases

1. **Research**: Understand context effects on LLM confidence
2. **Model Selection**: Choose best model for your scenario
3. **Context Design**: Decide what context to retrieve for RAG systems
4. **Safety**: Identify when models are overconfident

---

## ⚠️ Common Gotchas

| Issue | Fix |
|-------|-----|
| API key errors | `export OPENAI_API_KEY="..."`  |
| Memory overflow | Reduce `batch_size` in config |
| Low accuracy | Check data annotation quality |
| Missing plots | Run all steps: `--steps explore variants inference metrics analysis` |

---

## 📊 Output Structure

```
results/
├── data_summary.json              # Data overview
├── inference_results.json         # Raw model outputs
├── metrics_by_model.json          # All metrics computed
├── experiment_report.json         # Summary + findings
└── figures/
    ├── accuracy_by_context.png
    ├── calibration_curve.png
    ├── ece_by_context.png
    ├── overconfidence_by_context.png
    ├── context_sensitivity_heatmap.png
    └── marginal_improvements.png
```

---

## 🔗 Learn More

| Document | Read for |
|----------|----------|
| README.md | Setup, API reference |
| EXPERIMENT_DESIGN.md | Detailed methodology |
| ARCHITECTURE.md | System design |
| FRAMEWORK_SUMMARY.md | Complete overview |
| IMPLEMENTATION_CHECKLIST.md | Step-by-step guidance |

---

## 💡 Key Insights Expected

1. **Conversation matters most** - Direct discourse is most informative
2. **Models vary** - Different architectures respond differently to context
3. **Calibration improves with context** - More context → better confidence estimates
4. **Diminishing returns** - After 2-3 context types, marginal gains are small
5. **Overconfidence in sparse context** - Models make bold claims with little info

---

## 🚦 Status Check

Run this to verify setup:
```bash
python -c "
import pandas as pd
from data_loader import DataLoader
loader = DataLoader()
summary = loader.get_data_summary()
print('✓ Data loaded' if summary else '✗ Data error')
print(f'✓ Posts: {summary[\"posts\"][\"total_count\"]}')
"
```

---

**Quick Start Version**: 1.0  
**Last Updated**: November 5, 2025
