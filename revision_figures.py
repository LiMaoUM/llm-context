"""Regenerate main-text figures for the revised paper.

Run: uv run --with scikit-learn --with openpyxl --with matplotlib revision_figures.py
"""
import glob
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = "results/20260115_215043"

def parse_response(response):
    if pd.isna(response) or response == "---":
        return None, None
    s = str(response).lower()
    m = re.search(r"ideology:\s*\**\s*(left|center|right)", s)
    ideology = m.group(1) if m else None
    stance = None
    m = re.search(r"(?:trump stance|stance toward trump|stance towards trump|stance):\s*\**\s*(favor|against|neutral|undecided)", s)
    if m:
        stance = m.group(1)
    return ideology, stance

def norm_label(x, task):
    if pd.isna(x):
        return np.nan
    x = str(x).strip().lower()
    if task == "ideology":
        if x in ("left", "center", "right"):
            return x
        if x in ("undecided", "unclear", "unknown"):
            return "center"
    else:
        if x in ("favor", "favoue", "favour"):
            return "favor"
        if x == "against":
            return "against"
        if x in ("neutral", "undecided", "center", "unclear"):
            return "none"
    return np.nan

frames = []
for fp in sorted(glob.glob(os.path.join(RESULTS_DIR, "*_responses.jsonl"))):
    model = os.path.basename(fp).replace("_responses.jsonl", "")
    if model == "model":
        continue
    df = pd.read_json(fp, lines=True)
    df["model"] = model
    frames.append(df)
preds = pd.concat(frames, ignore_index=True)
parsed = preds["response"].apply(parse_response)
preds["ideology_pred"] = parsed.str[0]
preds["stance_pred"] = parsed.str[1].replace({"neutral": "none", "undecided": "none"})

sheng = pd.read_excel("data/manual/manual_Shengteng.xlsx")
qing = pd.read_csv("data/manual/manual_qing.csv")
xinyu = pd.read_csv("data/manual/manual_Xinyu.csv")
qing["sample_id"] = sheng["sample_id"]
xinyu["sample_id"] = sheng["sample_id"]
coders = {}
for name, df, icol, scol in [("qing", qing, "Ideology", "Stance"),
                              ("xinyu", xinyu, "ideology", "stance"),
                              ("shengteng", sheng, "ideology", "stance")]:
    d = df[df["variant"] == "T+B+C+M"][["sample_id", icol, scol]].copy()
    d.columns = ["sample_id", "ideology", "stance"]
    d["ideology"] = d["ideology"].apply(lambda v: norm_label(v, "ideology"))
    d["stance"] = d["stance"].apply(lambda v: norm_label(v, "stance"))
    coders[name] = d.set_index("sample_id")
rows = []
for sid in coders["shengteng"].index:
    rec = {"sample_id": sid}
    for task in ("ideology", "stance"):
        votes = [coders[c].loc[sid, task] for c in coders]
        votes = [v for v in votes if pd.notna(v)]
        vc = pd.Series(votes).value_counts()
        rec[f"gt_{task}"] = vc.index[0] if len(vc) and vc.iloc[0] >= 2 else np.nan
    rows.append(rec)
gold = pd.DataFrame(rows)
m = preds.merge(gold, on="sample_id", how="inner")

VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = sorted(m["model"].unique())
cmap = plt.get_cmap("tab10")

# Fig 1: macro-F1 by condition per model (gold subset)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), sharey=True)
for ax, task in zip(axes, ("ideology", "stance")):
    for i, mod in enumerate(MODELS):
        ys = []
        for v in VARIANTS:
            d = m[(m["model"] == mod) & (m["variant"] == v)].dropna(subset=[f"gt_{task}", f"{task}_pred"])
            ys.append(f1_score(d[f"gt_{task}"], d[f"{task}_pred"], average="macro") * 100)
        ax.plot(VARIANTS, ys, "o-", color=cmap(i % 10), label=mod, lw=1.4, ms=4)
    ax.set_title(f"{task.capitalize()} (macro-F$_1$)")
    ax.tick_params(axis="x", rotation=20)
    ax.grid(alpha=0.25)
axes[0].set_ylabel("Macro-F$_1$ (%)")
axes[1].legend(fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig("latex/fig_f1_rev.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Fig 2: mean self-reported confidence by condition per model (full corpus)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.0), sharey=True)
for ax, conf_c, title in zip(axes, ("ideology_confidence", "stance_confidence"),
                             ("Ideology confidence", "Stance confidence")):
    for i, mod in enumerate(MODELS):
        d = preds[preds["model"] == mod]
        ys = [d[d["variant"] == v][conf_c].mean() for v in VARIANTS]
        ax.plot(VARIANTS, ys, "o-", color=cmap(i % 10), label=mod, lw=1.4, ms=4)
    ax.set_title(title)
    ax.tick_params(axis="x", rotation=20)
    ax.grid(alpha=0.25)
axes[0].set_ylabel("Mean self-reported confidence")
axes[1].legend(fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig("latex/fig_conf_rev.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("written: latex/fig_f1_rev.png, latex/fig_conf_rev.png")
