"""Recompute Table 2 (model confidence vs human confidence, text-only condition) with three coders.

Inputs (row-aligned exports, 283 text-only rows each, matched by sample_id):
  data/manual/conf_manual.xlsx              coder 1 (columns 'ideology confidence ', 'stance confidence')
  data/manual/conf_manual_Xinyu_1.14.csv    coder 2 (columns 'confidence', 'confidence.1')
  data/third_coder/rating_sheet_T.xlsx      coder 3 (columns 'ideology_confidence', 'stance_confidence'),
                                            the sheet from make_rating_sheet.py once filled in
Model confidence comes from results/20260115_215043/<model>_responses.jsonl (variant T).

Outputs: third_coder/table2_three_coders.json and a LaTeX table body on stdout with, per model,
mean confidence, Spearman rho and quadratic-weighted kappa_w against the three-coder mean and
against the rank consensus, plus the three-coder ceiling (mean pairwise rho and kappa_w).
Falls back to two coders, with a warning, if the third sheet is absent or unfilled.

Run: uv run --with openpyxl --with scikit-learn python third_coder/recompute_table2.py
"""
import glob
import json
import os
import sys
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import cohen_kappa_score

RESULTS_DIR = "results/20260115_215043"
MODELS = ["gemma-3-27b-it", "gpt-oss-120b", "llama-3.1-8b", "ministral-3-14b",
          "ministral-3-8b", "qwen3-30b-a3b", "qwen3-4b", "qwen3-80b-a3b"]
THIRD = "data/third_coder/rating_sheet_T.xlsx"


def bucket(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 33, 0, np.where(c <= 66, 1, 2))


def kw(a, b):
    return cohen_kappa_score(bucket(a), bucket(b), weights="quadratic")


def load_coders():
    base = pd.read_excel("data/manual/manual_Shengteng.xlsx")
    c1 = pd.read_excel("data/manual/conf_manual.xlsx")
    c1.columns = [c.strip().lower().replace(" ", "_") for c in c1.columns]
    c1["sample_id"] = base["sample_id"].values
    c1 = c1[c1["variant"] == "T"][["sample_id", "ideology_confidence", "stance_confidence"]]
    c1.columns = ["sample_id", "c1_ideo", "c1_stance"]

    c2 = pd.read_csv("data/manual/conf_manual_Xinyu_1.14.csv")
    c2.columns = [c.strip().lower() for c in c2.columns]
    c2["sample_id"] = base["sample_id"].values
    c2 = c2[c2["variant"] == "T"][["sample_id", "confidence", "confidence.1"]]
    c2.columns = ["sample_id", "c2_ideo", "c2_stance"]

    h = c1.merge(c2, on="sample_id")
    coders = ["c1", "c2"]
    if os.path.exists(THIRD):
        c3 = pd.read_excel(THIRD, sheet_name="ratings")
        c3 = c3[["sample_id", "ideology_confidence", "stance_confidence"]]
        c3.columns = ["sample_id", "c3_ideo", "c3_stance"]
        c3["c3_ideo"] = pd.to_numeric(c3["c3_ideo"], errors="coerce")
        c3["c3_stance"] = pd.to_numeric(c3["c3_stance"], errors="coerce")
        if c3["c3_ideo"].notna().sum() >= 50:
            h = h.merge(c3, on="sample_id")
            coders.append("c3")
        else:
            print("WARNING: third-coder sheet found but fewer than 50 ideology ratings filled; using two coders", file=sys.stderr)
    else:
        print("WARNING: no third-coder sheet at", THIRD, "; using two coders", file=sys.stderr)
    for t in ("ideo", "stance"):
        cols = [f"{c}_{t}" for c in coders]
        h = h.dropna(subset=cols)
        h[f"h_{t}"] = h[cols].mean(axis=1)
        h[f"hr_{t}"] = sum(h[c].rank(pct=True) for c in cols) / len(cols)
    return h, coders


def load_models():
    frames = []
    for fp in sorted(glob.glob(os.path.join(RESULTS_DIR, "*_responses.jsonl"))):
        model = os.path.basename(fp).replace("_responses.jsonl", "")
        if model not in MODELS:
            continue
        df = pd.read_json(fp, lines=True)
        df = df[df["variant"] == "T"][["sample_id", "ideology_confidence", "stance_confidence"]].copy()
        df["model"] = model
        frames.append(df)
    m = pd.concat(frames, ignore_index=True).drop_duplicates(["model", "sample_id"])
    for c in ("ideology_confidence", "stance_confidence"):
        m[c] = pd.to_numeric(m[c], errors="coerce")
    return m


def main():
    h, coders = load_coders()
    m = load_models()
    out = {"n_posts": int(len(h)), "coders": coders, "coder_means": {}, "ceiling": {}, "per_model": []}
    for c in coders:
        out["coder_means"][c] = [round(h[f"{c}_ideo"].mean(), 1), round(h[f"{c}_stance"].mean(), 1)]
    for t in ("ideo", "stance"):
        pairs = list(combinations(coders, 2))
        out["ceiling"][t] = {
            "pairwise_rho": [round(sps.spearmanr(h[f"{a}_{t}"], h[f"{b}_{t}"]).statistic, 2) for a, b in pairs],
            "pairwise_kw": [round(kw(h[f"{a}_{t}"], h[f"{b}_{t}"]), 2) for a, b in pairs],
            # leave-one-out: each coder against the mean of the others, the ceiling a model is held to
            "coder_vs_rest_rho": [round(sps.spearmanr(h[f"{c}_{t}"], h[[f"{d}_{t}" for d in coders if d != c]].mean(axis=1)).statistic, 2) for c in coders],
            "coder_vs_rest_kw": [round(kw(h[f"{c}_{t}"], h[[f"{d}_{t}" for d in coders if d != c]].mean(axis=1)), 2) for c in coders],
        }
    for mod in MODELS:
        d = m[m["model"] == mod].merge(h, on="sample_id").dropna(subset=["ideology_confidence", "stance_confidence"])
        row = {"model": mod, "n": int(len(d))}
        for t, mc in (("ideo", "ideology_confidence"), ("stance", "stance_confidence")):
            row[f"mean_{t}"] = round(d[mc].mean(), 1)
            row[f"rho_{t}"] = round(sps.spearmanr(d[mc], d[f"h_{t}"]).statistic, 2)
            row[f"kw_{t}"] = round(kw(d[mc], d[f"h_{t}"]), 2)
            row[f"rho_rank_{t}"] = round(sps.spearmanr(d[mc], d[f"hr_{t}"]).statistic, 2)
            for c in coders:
                row[f"rho_{t}_{c}"] = round(sps.spearmanr(d[mc], d[f"{c}_{t}"]).statistic, 2)
                row[f"kw_{t}_{c}"] = round(kw(d[mc], d[f"{c}_{t}"]), 2)
        out["per_model"].append(row)
    out["per_model"].sort(key=lambda r: -r["kw_ideo"])

    os.makedirs("third_coder", exist_ok=True)
    with open("third_coder/table2_three_coders.json", "w") as f:
        json.dump(out, f, indent=1)

    print(f"% Table 2 recomputed with {len(coders)} coders, n={out['n_posts']} posts")
    print("% coder means:", out["coder_means"])
    print("% ceiling (coder vs mean of the others), ideology kw:", out["ceiling"]["ideo"]["coder_vs_rest_kw"],
          "stance kw:", out["ceiling"]["stance"]["coder_vs_rest_kw"])
    print("Model & mean & rho & kw & mean & rho & kw \\\\")
    for r in out["per_model"]:
        print(f"{r['model']} & {r['mean_ideo']} & {r['rho_ideo']:.2f} & {r['kw_ideo']:.2f} & "
              f"{r['mean_stance']} & {r['rho_stance']:.2f} & {r['kw_stance']:.2f} \\\\")


if __name__ == "__main__":
    main()
