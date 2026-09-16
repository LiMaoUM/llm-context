# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A research framework that measures how supplying different **contextual dimensions** to an LLM
changes its **classification accuracy** and **confidence calibration** on a social-media
political-analysis task (inferring a post author's political ideology and stance toward Trump).

The core experimental design is a **context ablation**: each post is rendered into several
context variants and every model sees every variant, so the effect of each context block can be
isolated. Variants in the current config (`experiment_config.yaml`):

- `T` — focal post text only (baseline)
- `T+B` — text + background event context
- `T+B+C` — text + background + conversation history (parent/child posts)
- `T+B+C+M` — everything + user/post metadata

The model is explicitly instructed (in the prompt template) that **confidence means contextual
sufficiency**, not how strongly the author feels — this is central to the calibration analysis,
not an incidental wording choice.

## Running things

Use `uv` for everything — never call `python`/`python3` directly. Heavy local inference runs on
GPUs via vLLM, so commands assume the Linux machine with CUDA.

```bash
# Full pipeline (explore → variants → inference → metrics → analysis → report)
uv run run_experiment.py --gpus 1,2

# Quick smoke test on a few samples
uv run run_experiment.py --num-samples 5 --gpus 1,2

# Run only some stages
uv run run_experiment.py --steps inference metrics --gpus 1,2

# Only collect confidence (skip full prediction bookkeeping)
uv run run_experiment.py --confidence-only

# Standalone tests / utilities
uv run test_vllm_batch.py
uv run test_truncation.py
uv run split_model_results.py
uv run visualize_results.py
```

`--gpus` sets `CUDA_VISIBLE_DEVICES` globally before any model loads. Per-model `gpu_device` and
`tensor_parallel_size` in `experiment_config.yaml` are interpreted relative to that visible set.

There is no test runner / linter configured; the `test_*.py` files are standalone scripts, not a
pytest suite.

## Pipeline architecture

`run_experiment.py` (`ExperimentRunner`) orchestrates six steps; each can be run independently via
`--steps`. Everything is driven by `experiment_config.yaml` — models, context variants, the prompt
template, task definition, metrics, and execution settings all live there, not in code.

1. **explore** — `DataLoader` (`data_loader.py`) loads the parquet datasets and writes a summary.
2. **variants** — `ContextVariantGenerator` (`data_loader.py`) pulls each post's full context
   (conversation tree, author metadata, background) and renders the variant set per sample.
3. **inference** — `InferencePipeline` + `BatchEvaluator` (`llm_inference.py`). **Models are loaded
   and run one at a time**, then explicitly torn down (delete refs, `gc.collect()`,
   `torch.cuda.empty_cache()`, `ray.shutdown()`) to free GPU memory before the next model. A
   failure on one model is logged and skipped, not fatal.
4. **metrics** — `ResultsAnalyzer` (`analysis_visualization.py`) + `ComprehensiveMetrics`
   (`evaluation_metrics.py`) compute per-model, per-variant accuracy, F1, ECE, Brier,
   overconfidence rate, and context-sensitivity deltas.
5. **analysis** — `ResultsVisualizer` (`analysis_visualization.py`) generates calibration curves,
   heatmaps, bar/line plots.
6. **report** — aggregates summary statistics into `experiment_report.json`.

`background_context.py` builds the background-event text blocks used by the `T+B*` variants.

### Things that will bite you

- **`multiprocessing.set_start_method('spawn', force=True)` must run before any CUDA import.** It's
  done at the top of `run_experiment.py` under `if __name__ == '__main__'`. vLLM tensor parallelism
  depends on it. Don't import torch/vllm at module top level in new entry points.
- **`max_tokens` is 1024 deliberately.** It was raised from 512 because models truncated mid-JSON.
  The task requires JSON-only output; truncation produces unparseable responses. See
  `test_truncation.py`.
- **Outputs are timestamped.** Each run writes to `results/<YYYYMMDD_HHMMSS>/` with per-model
  `*_responses.jsonl` and `*_inference_results.json`, a combined `inference_results.json`,
  `model_responses.jsonl`, `results_manifest.json`, `metrics_by_model.json`, and `figures/`.
- **`data/` is a symlink** to `/home/maolee/projects/simulate-conversation/data/processed`
  (parquet: posts, users, interactions, post_edges, cascades_nodes, tree_features). It is not
  part of this repo.
- **Ground-truth labels are not yet wired in** — `step_2` sets `ground_truth: None` (see the TODO).
  Accuracy/F1 depend on labels being supplied; check this before trusting classification metrics.

## Config is the source of truth

To change models, context variants, the prompt, or metrics, edit `experiment_config.yaml` — most
behavior is data-driven from it. The current model roster is all local HuggingFace/vLLM checkpoints
(Qwen3, Llama-3.x, gpt-oss, Gemma-3, Ministral) sized for 1–2 GPUs. The README also documents
hosted-API providers (OpenAI/Anthropic/Replicate); treat the README provider section as historical
unless the config actually lists them.

## Repo hygiene note

The working tree contains many uncommitted scratch artifacts — multiple overlapping `*.md` notes
(QUICK_*, VALIDATION_*, UPDATE_SUMMARY, etc.), large `*.png` figures, multi-MB `*.log` files,
`nohup.out`, and notebooks. The canonical, committed sources are the `.py` modules and
`experiment_config.yaml`. Don't treat the loose markdown files as authoritative.

## Running vLLM in this repo (recorded 2026-09-16)

The project venv pins `vllm>=0.1.2` and uv resolved it to the 2023 release 0.1.2, whose `LLM()`
has no `max_model_len`. The paper run (results/20260115_215043, January 2026) ran under vLLM
0.13.0 (experiment_new.log: "Initializing a V1 LLM engine (v0.13.0)"); the December 2025 pilot
used 0.11.0, whose transformers 4.57 cannot load Ministral-3 (`KeyError: 'ministral3'`). Launch
any inference script with the 0.13.0 overlay:

```bash
CUDA_VISIBLE_DEVICES=2,7 uv run --with vllm==0.13.0 sample_agreement_run.py --models all
```

Do not `uv add vllm==0.11.0`: it would force torch 2.8 into the lockfile and the analysis
scripts were validated on the current venv.
