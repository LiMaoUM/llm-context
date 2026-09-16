# Experiment Card: sample agreement vs verbalized confidence

- **Study / version / date**: sample-agreement v1, 2026-09-16 (ARR rebuttal, Submission 2351).
- **Hypothesis**: Cross-sample label agreement (k stochastic decodes of the same prompt) is a
  weaker within-condition reliability signal than single-sample verbalized confidence, measured
  as AUROC for correctness against the gold labels; the two combined do not exceed verbalized
  confidence alone by more than 0.02 AUROC. Reviewers 8FDE (W2) and 24ts (W2, W3) asked for this
  comparison. Pilot evidence from the 3-seed re-decoding of gemma-3-27b-it and qwen3-4b:
  agreement AUROC 0.49 to 0.64 per cell against 0.48 to 0.85 for verbalized confidence, with
  agreement near-constant because 85 to 98 percent of cells fully agree at k=3.
- **Sample / cohort definition (FROZEN)**: the 295 gold posts (sample ids of the T+B+C+M rows
  in `data/manual/manual_Shengteng.xlsx`) x 4 context variants, prompts taken verbatim from
  `results/20260115_215043/<model>_responses.jsonl` (drop duplicates on sample_id x variant).
  Expected N per model: about 1,168 prompts (some posts lack a T rendering).
- **Conditions and metrics**: eight paper models, k=10 seeds (101, 202, ..., 1010), temperature
  0.7, top-p 0.9, max_tokens 1024, tensor_parallel_size 2, max_model_len 20000, vLLM 0.11.0.
  Per model x task x condition: AUROC of (a) first-seed verbalized confidence, (b) share of the
  other nine samples agreeing with the first-seed label, (c) rank-average of a and b, (d) mean
  confidence over seeds, for first-seed correctness. Coverage-matched accuracy at 80/60/40
  percent and AURC per signal. Also: AUROC of each signal for coder unanimity (24ts W2).
  Variance: post-level bootstrap on AURC differences in `rebuttal_analysis.py`.
- **Compute plan**: GPUs 2 and 7 (free at launch, 15 MiB used each). Largest weights:
  gpt-oss-120b MXFP4 about 65 GB, qwen3-80b FP8 about 80 GB, split over two H100 80 GB with
  0.9 utilization; KV cache for 20k context fits after weights on both. Smoke test on qwen3-4b
  measured load and per-seed throughput; see status log.
- **Smoke test**: `--models qwen3-4b --smoke` (20 prompts, 2 seeds) writes
  `sample_agreement/qwen3-4b_smoke.jsonl`; pass = 40 rows, ideology parse rate at or above 0.9.
- **Stopping rule**: one pass over the eight models. If a model fails to load twice, skip it and
  report the comparison on the remaining models. If agreement AUROC exceeds verbalized AUROC on
  a majority of cells, the hypothesis is rejected and the paper's protocol text changes; no
  larger k without an explicit override.
- **Artifacts**: `sample_agreement/<model>.jsonl` (one row per prompt x seed),
  `sample_agreement/run.log`, results merged by `rebuttal_analysis.py` into
  `rebuttal_analysis_output.json` (section C).
- **Monitor contract**: notify on model completion lines ("wrote ... rows"), Traceback/Error/OOM,
  and ALL DONE. Monitor expiry 30 min, re-armed on expiry until ALL DONE.
- **Status log**:
  - 2026-09-16 smoke v1 (qwen3-4b, 20 x 2) launched under vLLM 0.11.0 overlay after the venv's
    vLLM 0.1.2 failed on `max_model_len`.
  - 2026-09-16 smoke v1 passed: 40 rows, ideology parse rate 0.975, load 111 s, 20 prompts per
    seed in 7 s on GPUs 2 and 7 (TP=2).
  - 2026-09-16 full v1 launched: eight models, ten seeds, GPUs 2 and 7, log sample_agreement/run.log.
  - 2026-09-16 full v1 died at ministral-3-8b: vLLM 0.11.0 overlay ships transformers 4.57, which
    lacks the ministral3 config. qwen3-4b and llama-3.1-8b outputs (0.11.0) moved to
    sample_agreement/vllm0.11/. The paper run used vLLM 0.13.0; v2 reruns all eight models under
    0.13.0 so every model shares one engine version.
  - 2026-09-16 smoke v2 (ministral-3-8b, 20 x 2, vLLM 0.13.0) launched.
  - 2026-09-16 smoke v2 passed: 40 rows, ideology parse rate 0.80 (Ministral extraction rates are
    70 to 93 percent in the paper), load 90 s.
  - 2026-09-16 full v2 launched: eight models, ten seeds, vLLM 0.13.0, GPUs 2 and 7, log
    sample_agreement/run.log.
