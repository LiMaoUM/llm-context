"""Multi-sample re-decoding of the gold-subset prompts for all eight paper models.

Purpose (ARR rebuttal, reviewers 8FDE W2 / 24ts W2-W3): compare verbalized confidence against
cross-sample agreement as a reliability signal. Prompts are taken verbatim from the paper run's
JSONL (results/20260115_215043), so every cell is the same prompt the paper scored. Decoding
mirrors llm_inference.py: raw-prompt generate(), temperature 0.7, top-p 0.9, max_tokens 1024,
tensor_parallel_size 2, max_model_len 20000.

Outputs one JSONL per model in sample_agreement/<model>.jsonl with fields
  sample_id, variant, seed, ideology, stance, ideo_conf, stance_conf
(same schema as seed_stability_*.jsonl, so rebuttal_analysis.py merges both).

Run (GPUs are set via CUDA_VISIBLE_DEVICES before any CUDA import):
  CUDA_VISIBLE_DEVICES=2,7 uv run sample_agreement_run.py --models all
  CUDA_VISIBLE_DEVICES=2,7 uv run sample_agreement_run.py --models qwen3-4b --smoke
"""
import argparse
import multiprocessing as mp
import os

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

import json
import re
import time

import pandas as pd

RESULTS_DIR = "results/20260115_215043"
OUT_DIR = "sample_agreement"
MODELS = {
    "qwen3-4b": "Qwen/Qwen3-4B-Instruct-2507",
    "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
    "ministral-3-8b": "mistralai/Ministral-3-8B-Instruct-2512",
    "ministral-3-14b": "mistralai/Ministral-3-14B-Instruct-2512",
    "gemma-3-27b-it": "google/gemma-3-27b-it",
    "qwen3-30b-a3b": "Qwen/Qwen3-30B-A3B-Instruct-2507-FP8",
    "qwen3-80b-a3b": "Qwen/Qwen3-Next-80B-A3B-Instruct-FP8",
    "gpt-oss-120b": "openai/gpt-oss-120b",
}
SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1010]


def parse_response(text):
    if not text:
        return None, None, None, None
    s = str(text).lower()
    m = re.search(r"ideology:\s*\**\s*(left|center|right)", s)
    ideology = m.group(1) if m else None
    m = re.search(r"(?:trump stance|stance toward trump|stance towards trump|stance):\s*\**\s*(favor|against|neutral|undecided)", s)
    stance = m.group(1) if m else None
    m = re.search(r"ideology confidence:\s*\**\s*(\d+)", s)
    ic = int(m.group(1)) if m else None
    m = re.search(r"stance confidence:\s*\**\s*(\d+)", s)
    sc = int(m.group(1)) if m else None
    return ideology, stance, ic, sc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=["all"])
    ap.add_argument("--seeds", nargs="+", type=int, default=SEEDS)
    ap.add_argument("--smoke", action="store_true", help="20 prompts, 2 seeds, write to *_smoke.jsonl")
    ap.add_argument("--tp", type=int, default=2)
    args = ap.parse_args()
    models = list(MODELS) if args.models == ["all"] else args.models
    seeds = args.seeds[:2] if args.smoke else args.seeds
    os.makedirs(OUT_DIR, exist_ok=True)

    sheng = pd.read_excel("data/manual/manual_Shengteng.xlsx")
    gold_ids = set(sheng[sheng["variant"] == "T+B+C+M"]["sample_id"])

    from vllm import LLM, SamplingParams

    for model_name in models:
        out_path = os.path.join(OUT_DIR, f"{model_name}{'_smoke' if args.smoke else ''}.jsonl")
        if os.path.exists(out_path) and not args.smoke:
            print(f"[skip] {out_path} exists", flush=True)
            continue
        df = pd.read_json(os.path.join(RESULTS_DIR, f"{model_name}_responses.jsonl"), lines=True)
        df = df[df["sample_id"].isin(gold_ids)].drop_duplicates(["sample_id", "variant"])
        if args.smoke:
            df = df.head(20)
        prompts = df["prompt"].tolist()
        keys = list(zip(df["sample_id"], df["variant"]))
        print(f"[{model_name}] {len(prompts)} prompts x {len(seeds)} seeds", flush=True)

        t0 = time.time()
        llm = LLM(model=MODELS[model_name], tensor_parallel_size=args.tp, gpu_memory_utilization=0.9,
                  max_model_len=20000, dtype="auto")
        print(f"[{model_name}] loaded in {time.time()-t0:.0f}s", flush=True)
        recs = []
        n_parsed = 0
        for seed in seeds:
            t1 = time.time()
            sp = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=1024, seed=seed)
            outs = llm.generate(prompts, sp, use_tqdm=False)
            for (sid, var), o in zip(keys, outs):
                ideo, st, ic, sc = parse_response(o.outputs[0].text)
                n_parsed += ideo is not None
                recs.append({"sample_id": sid, "variant": var, "seed": seed,
                             "ideology": ideo, "stance": st, "ideo_conf": ic, "stance_conf": sc})
            print(f"[{model_name}] seed {seed} done in {time.time()-t1:.0f}s", flush=True)
        with open(out_path, "w") as f:
            for r in recs:
                f.write(json.dumps(r) + "\n")
        print(f"[{model_name}] wrote {len(recs)} rows to {out_path}; ideology parse rate "
              f"{n_parsed/len(recs):.3f}; total {time.time()-t0:.0f}s", flush=True)

        del llm
        import gc
        import torch
        gc.collect()
        torch.cuda.empty_cache()
        try:
            import ray
            ray.shutdown()
        except Exception:
            pass
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
