"""Decoding-stability check for the R&R: re-decode the gold-subset prompts
(295 posts x 4 variants) with 3 seeds at temperature 0.7 for two models,
and measure label flip rates and confidence dispersion across seeds.

Prompts are taken verbatim from the original run's JSONL so the comparison is
exact. One model at a time; CUDA_VISIBLE_DEVICES set before any CUDA import.

Run: CUDA_VISIBLE_DEVICES=2 uv run seed_stability_check.py
"""
import multiprocessing as mp
import os

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

import json
import re

import pandas as pd

RESULTS_DIR = "results/20260115_215043"
MODELS = {
    "qwen3-4b": "Qwen/Qwen3-4B-Instruct-2507",
    "gemma-3-27b-it": "google/gemma-3-27b-it",
}
SEEDS = [101, 202, 303]


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
    # gold sample ids = the 295 posts in the coder export
    sheng = pd.read_excel("data/manual/manual_Shengteng.xlsx")
    gold_ids = set(sheng[sheng["variant"] == "T+B+C+M"]["sample_id"])

    from vllm import LLM, SamplingParams

    all_out = {}
    for model_name, model_id in MODELS.items():
        df = pd.read_json(os.path.join(RESULTS_DIR, f"{model_name}_responses.jsonl"), lines=True)
        df = df[df["sample_id"].isin(gold_ids)].drop_duplicates(["sample_id", "variant"])
        prompts = df["prompt"].tolist()
        keys = list(zip(df["sample_id"], df["variant"]))
        print(f"{model_name}: {len(prompts)} prompts")

        # mirror llm_inference.py: raw-prompt generate(), temp 0.7, top_p 0.9
        llm = LLM(model=model_id, tensor_parallel_size=1, gpu_memory_utilization=0.9,
                  max_model_len=20000, dtype="auto")
        recs = []
        for seed in SEEDS:
            sp = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=1024, seed=seed)
            outs = llm.generate(prompts, sp)
            for (sid, var), o in zip(keys, outs):
                ideo, st, ic, sc = parse_response(o.outputs[0].text)
                recs.append({"sample_id": sid, "variant": var, "seed": seed,
                             "ideology": ideo, "stance": st, "ideo_conf": ic, "stance_conf": sc})
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()

        r = pd.DataFrame(recs)
        r.to_json(f"seed_stability_{model_name}.jsonl", orient="records", lines=True)

        # flip rates: fraction of (post, variant) cells where the 3 seeds disagree
        out = {}
        for task in ("ideology", "stance"):
            g = r.dropna(subset=[task]).groupby(["sample_id", "variant"])[task].nunique()
            g = g[r.groupby(["sample_id", "variant"])[task].count() == 3]
            out[f"{task}_flip_rate"] = round(float((g > 1).mean()), 4)
            out[f"{task}_n_cells"] = int(len(g))
        for c in ("ideo_conf", "stance_conf"):
            sd = r.dropna(subset=[c]).groupby(["sample_id", "variant"])[c].std()
            out[f"{c}_median_sd"] = round(float(sd.median()), 1)
            out[f"{c}_mean_sd"] = round(float(sd.mean()), 1)
        all_out[model_name] = out
        print(model_name, out)

    with open("seed_stability_summary.json", "w") as f:
        json.dump(all_out, f, indent=2)
    print(json.dumps(all_out, indent=2))


if __name__ == "__main__":
    main()
