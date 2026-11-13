"""Revision analyses, part 2: human-confidence table (fixed alignment),
per-model performance tables, coverage-accuracy triage curves, new figures.

Run: uv run --with statsmodels --with scikit-learn --with openpyxl --with matplotlib revision_analysis2.py
"""
import glob
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import f1_score, cohen_kappa_score

warnings.filterwarnings("ignore")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RESULTS_DIR = "results/20260115_215043"
OUT = {}

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
preds["stance_pred"] = parsed.str[1].replace({"neutral": "center", "undecided": "center"})

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
            return "center"
    return np.nan

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
for task in ("ideology", "stance"):
    m[f"{task}_correct"] = (m[f"{task}_pred"] == m[f"gt_{task}"]).astype(float)
    m.loc[m[f"gt_{task}"].isna() | m[f"{task}_pred"].isna(), f"{task}_correct"] = np.nan

VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = sorted(m["model"].unique())

# ------------------------------------------------ per-model acc/F1 by variant
per_model = []
for mod in MODELS:
    for v in VARIANTS:
        d = m[(m["model"] == mod) & (m["variant"] == v)]
        row = {"model": mod, "variant": v}
        for task in ("ideology", "stance"):
            sub = d.dropna(subset=[f"gt_{task}", f"{task}_pred"])
            row[f"{task}_acc"] = round((sub[f"{task}_pred"] == sub[f"gt_{task}"]).mean() * 100, 1)
            row[f"{task}_f1"] = round(f1_score(sub[f"gt_{task}"], sub[f"{task}_pred"], average="macro") * 100, 1)
            row[f"{task}_n"] = len(sub)
        per_model.append(row)
OUT["per_model_performance"] = per_model

# --------------------------------------- human confidence (row-order aligned)
cq = pd.read_excel("data/manual/conf_manual.xlsx")
cx = pd.read_csv("data/manual/conf_manual_Xinyu_1.14.csv")
cq.columns = [c.strip().lower().replace(" ", "_") for c in cq.columns]
cx.columns = [c.strip().lower() for c in cx.columns]
cq["sample_id"] = sheng["sample_id"].values
cx["sample_id"] = sheng["sample_id"].values
cq = cq[cq["variant"] == "T"][["sample_id", "ideology_confidence", "stance_confidence"]].rename(
    columns={"ideology_confidence": "q_ideo", "stance_confidence": "q_stance"})
cx = cx[cx["variant"] == "T"][["sample_id", "confidence", "confidence.1"]].rename(
    columns={"confidence": "x_ideo", "confidence.1": "x_stance"})
hc = cq.merge(cx, on="sample_id")
hc["h_ideo"] = hc[["q_ideo", "x_ideo"]].mean(axis=1)
hc["h_stance"] = hc[["q_stance", "x_stance"]].mean(axis=1)

def bucket(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 33, 0, np.where(c <= 66, 1, 2))

hh = hc.dropna(subset=["q_ideo", "x_ideo", "q_stance", "x_stance"])
OUT["human_confidence_substudy"] = {
    "n": len(hh),
    "qing_means": [round(hh["q_ideo"].mean(), 1), round(hh["q_stance"].mean(), 1)],
    "xinyu_means": [round(hh["x_ideo"].mean(), 1), round(hh["x_stance"].mean(), 1)],
    "coder_spearman": [round(sps.spearmanr(hh["q_ideo"], hh["x_ideo"]).statistic, 2),
                       round(sps.spearmanr(hh["q_stance"], hh["x_stance"]).statistic, 2)],
    "coder_kw_quadratic": [round(cohen_kappa_score(bucket(hh["q_ideo"]), bucket(hh["x_ideo"]), weights="quadratic"), 2),
                           round(cohen_kappa_score(bucket(hh["q_stance"]), bucket(hh["x_stance"]), weights="quadratic"), 2)],
    "coder_kappa_unweighted": [round(cohen_kappa_score(bucket(hh["q_ideo"]), bucket(hh["x_ideo"])), 2),
                               round(cohen_kappa_score(bucket(hh["q_stance"]), bucket(hh["x_stance"])), 2)],
}

conf_agree = []
for mod in MODELS:
    d = m[(m["model"] == mod) & (m["variant"] == "T")][
        ["sample_id", "ideology_confidence", "stance_confidence"]]
    dd = d.merge(hc, on="sample_id")
    di = dd.dropna(subset=["ideology_confidence", "h_ideo"])
    ds = dd.dropna(subset=["stance_confidence", "h_stance"])
    conf_agree.append({
        "model": mod, "n_ideo": len(di), "n_stance": len(ds),
        "mean_conf_ideo": round(di["ideology_confidence"].mean(), 1),
        "rho_ideo": round(sps.spearmanr(di["ideology_confidence"], di["h_ideo"]).statistic, 2),
        "kw_ideo": round(cohen_kappa_score(bucket(di["ideology_confidence"]), bucket(di["h_ideo"]), weights="quadratic"), 2),
        "mean_conf_stance": round(ds["stance_confidence"].mean(), 1),
        "rho_stance": round(sps.spearmanr(ds["stance_confidence"], ds["h_stance"]).statistic, 2),
        "kw_stance": round(cohen_kappa_score(bucket(ds["stance_confidence"]), bucket(ds["h_stance"]), weights="quadratic"), 2),
    })
OUT["table_conf_agree"] = conf_agree

# -------------------------------------------- coverage-accuracy triage curves
coverages = [1.0, 0.8, 0.6, 0.4, 0.2]
triage = []
for task in ("ideology", "stance"):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for v in ("T", "T+B+C+M"):
        for mod in MODELS + ["POOLED"]:
            d = m[m["variant"] == v]
            if mod != "POOLED":
                d = d[d["model"] == mod]
            d = d.dropna(subset=[cc, conf_c]).sort_values(conf_c, ascending=False)
            if not len(d):
                continue
            row = {"task": task, "variant": v, "model": mod}
            for cov in coverages:
                k = max(1, int(len(d) * cov))
                row[f"acc@{int(cov*100)}"] = round(d.iloc[:k][cc].mean() * 100, 1)
            triage.append(row)
OUT["coverage_accuracy"] = triage

# ----------------------------------------------------------------- figures
# Fig A: within-condition reliability (equal-mass quintiles, pooled models)
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
colors = {"T": "#888888", "T+B+C+M": "#1f77b4"}
for ax, task in zip(axes, ("ideology", "stance")):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for v in ("T", "T+B+C+M"):
        d = m[m["variant"] == v].dropna(subset=[cc, conf_c]).copy()
        d["bin"] = pd.qcut(d[conf_c], 5, duplicates="drop")
        gb = d.groupby("bin", observed=True).agg(n=(cc, "size"), conf=(conf_c, "mean"), acc=(cc, "mean"))
        ax.plot(gb["conf"], gb["acc"] * 100, "o-", color=colors[v], label=v,
                markersize=0, lw=1.8)
        ax.scatter(gb["conf"], gb["acc"] * 100, s=gb["n"] / 6, color=colors[v], zorder=3, alpha=0.85)
    ax.plot([0, 100], [0, 100], "--", color="#bbbbbb", lw=1)
    ax.set_title(task.capitalize())
    ax.set_xlabel("Mean confidence in bin")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.legend(title="Condition", loc="upper left", fontsize=9)
axes[0].set_ylabel("Accuracy (%)")
fig.suptitle("Within-condition confidence vs. accuracy (equal-mass bins, pooled over models)", y=1.02, fontsize=11)
fig.tight_layout()
fig.savefig("latex/fig_within_condition.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# Fig B: per-model AUROC by condition (both tasks)
from sklearn.metrics import roc_auc_score
fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
cmap = plt.get_cmap("tab10")
for ax, task in zip(axes, ("ideology", "stance")):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for i, mod in enumerate(MODELS):
        ys = []
        for v in VARIANTS:
            d = m[(m["variant"] == v) & (m["model"] == mod)].dropna(subset=[cc, conf_c])
            ys.append(roc_auc_score(d[cc], d[conf_c]) if d[cc].nunique() == 2 else np.nan)
        ax.plot(VARIANTS, ys, "o-", color=cmap(i % 10), label=mod, lw=1.4, ms=4)
    ax.axhline(0.5, ls="--", color="#bbbbbb", lw=1)
    ax.set_title(task.capitalize())
    ax.set_ylim(0.4, 0.9)
    ax.tick_params(axis="x", rotation=20)
axes[0].set_ylabel("AUROC (confidence discriminates correct vs. incorrect)")
axes[1].legend(fontsize=7, ncol=1, loc="lower right")
fig.suptitle("Within-condition discrimination by model", y=1.02, fontsize=11)
fig.tight_layout()
fig.savefig("latex/fig_auroc_within.png", dpi=200, bbox_inches="tight")
plt.close(fig)

with open("revision_analysis_output2.json", "w") as f:
    json.dump(OUT, f, indent=2, default=str)
print(json.dumps({k: OUT[k] for k in ("human_confidence_substudy", "table_conf_agree")}, indent=2))
print("\ncoverage (POOLED rows):")
for r in OUT["coverage_accuracy"]:
    if r["model"] == "POOLED":
        print(r)
print("\nfigures written: latex/fig_within_condition.png, latex/fig_auroc_within.png")
