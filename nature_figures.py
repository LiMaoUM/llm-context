"""Nature-style regeneration of the four EACL paper figures.

Applies the nature-figure contract: editable-text vector output (PDF + 600 dpi
PNG), one colourblind-safe model->colour map across every panel, direct labels
in place of legends, restrained palette, hero treatment for the within-condition
calibration figure. All numbers come from the same verified pipeline as
revision_figures.py / revision_analysis2.py (run results/20260115_215043 + the
three human coder files).

Run: uv run --with scikit-learn --with openpyxl --with matplotlib nature_figures.py
"""
import glob
import os
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

warnings.filterwarnings("ignore")
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ----------------------------------------------------------------- Nature style
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "Liberation Sans"],
    "svg.fonttype": "none",     # editable text in SVG
    "pdf.fonttype": 42,         # editable TrueType text in PDF
    "font.size": 7,
    "axes.titlesize": 8,
    "axes.labelsize": 7.5,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.7,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.major.size": 2.6,
    "ytick.major.size": 2.6,
    "legend.frameon": False,
    "lines.linewidth": 1.2,
    "lines.markersize": 3.2,
    "figure.dpi": 200,
})

OUT = "latex"
# Paul Tol muted (colourblind-safe). Fixed model->colour map reused everywhere.
MODEL_COLORS = {
    "gpt-oss-120b":    "#332288",  # indigo  (best-calibrated; salient/dark)
    "gemma-3-27b-it":  "#117733",  # green
    "qwen3-80b-a3b":   "#44AA99",  # teal
    "qwen3-30b-a3b":   "#CC6677",  # rose
    "qwen3-4b":        "#AA4499",  # purple
    "llama-3.1-8b":    "#88CCEE",  # cyan
    "ministral-3-14b": "#999933",  # olive
    "ministral-3-8b":  "#882255",  # wine
}
GREY = "#767676"
GREY_LIGHT = "#BDBDBD"
BLUE = "#0F4D92"

def panel_label(ax, s, x=-0.12, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=9, fontweight="bold",
            ha="left", va="bottom")

def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"),
                    dpi=600 if ext == "png" else None, bbox_inches="tight")
    plt.close(fig)

def declutter(ys, min_gap):
    """Greedy 1-D label de-overlap: nudge sorted y-positions apart by min_gap."""
    order = np.argsort(ys)
    out = np.array(ys, dtype=float)
    for k in range(1, len(order)):
        i, j = order[k - 1], order[k]
        if out[j] - out[i] < min_gap:
            out[j] = out[i] + min_gap
    return out

def model_legend(fig):
    """One shared colourblind-safe model legend beneath both panels."""
    handles = [Line2D([0], [0], color=c, marker="o", mfc=c, mec="white",
                      mew=0.4, lw=1.2, ms=3.2, label=mod)
               for mod, c in MODEL_COLORS.items()]
    fig.legend(handles=handles, loc="lower center", ncol=4, fontsize=6.0,
               handletextpad=0.5, columnspacing=1.4, borderaxespad=0.0,
               bbox_to_anchor=(0.5, -0.10))

# ------------------------------------------------------------------- data load
def parse_response(r):
    if pd.isna(r) or r == "---":
        return None, None
    s = str(r).lower()
    m = re.search(r"ideology:\s*\**\s*(left|center|right)", s)
    ideo = m.group(1) if m else None
    m = re.search(r"(?:trump stance|stance toward trump|stance towards trump|stance):\s*\**\s*(favor|against|neutral|undecided)", s)
    return ideo, (m.group(1) if m else None)

def norm(x, task):
    if pd.isna(x):
        return np.nan
    x = str(x).strip().lower()
    if task == "ideology":
        return x if x in ("left", "center", "right") else ("center" if x in ("undecided", "unclear", "unknown") else np.nan)
    if x in ("favor", "favoue", "favour"):
        return "favor"
    if x == "against":
        return "against"
    if x in ("neutral", "undecided", "center", "unclear"):
        return "none"
    return np.nan

RES = "results/20260115_215043"
frames = []
for fp in sorted(glob.glob(os.path.join(RES, "*_responses.jsonl"))):
    mod = os.path.basename(fp).replace("_responses.jsonl", "")
    if mod == "model":
        continue
    df = pd.read_json(fp, lines=True)
    df["model"] = mod
    frames.append(df)
preds = pd.concat(frames, ignore_index=True)
p = preds["response"].apply(parse_response)
preds["ideology_pred"] = p.str[0]
preds["stance_pred"] = p.str[1].replace({"neutral": "none", "undecided": "none"})

sheng = pd.read_excel("data/manual/manual_Shengteng.xlsx")
qing = pd.read_csv("data/manual/manual_qing.csv")
xin = pd.read_csv("data/manual/manual_Xinyu.csv")
qing["sample_id"] = sheng["sample_id"]
xin["sample_id"] = sheng["sample_id"]
coders = {}
for n, df, ic, sc in [("q", qing, "Ideology", "Stance"), ("x", xin, "ideology", "stance"), ("s", sheng, "ideology", "stance")]:
    d = df[df["variant"] == "T+B+C+M"][["sample_id", ic, sc]].copy()
    d.columns = ["sample_id", "ideology", "stance"]
    d["ideology"] = d["ideology"].apply(lambda v: norm(v, "ideology"))
    d["stance"] = d["stance"].apply(lambda v: norm(v, "stance"))
    coders[n] = d.set_index("sample_id")
rows = []
for sid in coders["s"].index:
    rec = {"sample_id": sid}
    for t in ("ideology", "stance"):
        votes = [v for v in (coders[c].loc[sid, t] for c in coders) if pd.notna(v)]
        vc = pd.Series(votes).value_counts()
        rec[f"gt_{t}"] = vc.index[0] if len(vc) and vc.iloc[0] >= 2 else np.nan
    rows.append(rec)
gold = pd.DataFrame(rows)
m = preds.merge(gold, on="sample_id", how="inner")
for t in ("ideology", "stance"):
    m[f"{t}_correct"] = (m[f"{t}_pred"] == m[f"gt_{t}"]).astype(float)
    m.loc[m[f"gt_{t}"].isna() | m[f"{t}_pred"].isna(), f"{t}_correct"] = np.nan

VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
XLAB = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = list(MODEL_COLORS.keys())  # fixed legend/colour order
X = np.arange(len(VARIANTS))

# ============================================================ Figure 1: macro-F1
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8), sharey=True)
for ax, task, lab in zip(axes, ("ideology", "stance"), ("a", "b")):
    for mod in MODELS:
        ys = []
        for v in VARIANTS:
            d = m[(m["model"] == mod) & (m["variant"] == v)].dropna(subset=[f"gt_{task}", f"{task}_pred"])
            ys.append(f1_score(d[f"gt_{task}"], d[f"{task}_pred"], average="macro") * 100)
        ax.plot(X, ys, "-o", color=MODEL_COLORS[mod], mfc=MODEL_COLORS[mod],
                mec="white", mew=0.4, alpha=0.95)
    ax.set_xticks(X)
    ax.set_xticklabels(XLAB, rotation=18, ha="right")
    ax.set_title(f"{task.capitalize()}", fontweight="bold")
    ax.grid(axis="y", color="#E8E8E8", lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(12, 72)
    panel_label(ax, lab)
axes[0].set_ylabel("Macro-F$_1$ (%)")
model_legend(fig)
fig.subplots_adjust(wspace=0.12)
save(fig, "fig_f1_rev")

# ===================================== Figure 2 (HERO): within-condition reliability
fig, axes = plt.subplots(1, 2, figsize=(5.4, 2.7), sharey=True)
cond_style = {"T": (GREY, "Text only (T)"), "T+B+C+M": (BLUE, "Full context")}
for ax, task, lab in zip(axes, ("ideology", "stance"), ("a", "b")):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    ax.plot([0, 100], [0, 100], ls=(0, (4, 3)), color=GREY_LIGHT, lw=0.8, zorder=1)
    for v in ("T", "T+B+C+M"):
        col, name = cond_style[v]
        d = m[m["variant"] == v].dropna(subset=[cc, conf_c]).copy()
        d["bin"] = pd.qcut(d[conf_c], 5, duplicates="drop")
        gb = d.groupby("bin", observed=True).agg(n=(cc, "size"), conf=(conf_c, "mean"), acc=(cc, "mean"))
        ax.plot(gb["conf"], gb["acc"] * 100, "-", color=col, lw=1.3, zorder=3)
        ax.scatter(gb["conf"], gb["acc"] * 100, s=gb["n"] / 7.0, color=col,
                   edgecolor="white", linewidth=0.4, zorder=4)
    # direct condition labels near each curve (colour disambiguates)
    ax.text(8, 90, "Full context", color=BLUE, fontsize=6.2, ha="left",
            va="center", fontweight="bold")
    tonly_y = 41 if task == "ideology" else 22   # clear of the size legend in panel a
    ax.text(70, tonly_y, "Text only (T)", color=GREY, fontsize=6.2, ha="left",
            va="center", fontweight="bold")
    ax.text(50, 58, "perfect calibration", color=GREY, fontsize=5.2,
            rotation=45, ha="center", va="center", style="italic")
    ax.set_xlim(0, 102)
    ax.set_ylim(0, 102)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_aspect("equal")
    ax.set_xlabel("Mean confidence in bin")
    ax.set_title(f"{task.capitalize()}", fontweight="bold")
    panel_label(ax, lab)
axes[0].set_ylabel("Accuracy (%)")
# one shared size legend (bin n), in the ideology panel's empty lower-right
for nval in (200, 600, 1200):
    axes[0].scatter([], [], s=nval / 7.0, color=GREY, edgecolor="white",
                    linewidth=0.4, label=f"{nval}")
axes[0].legend(title="bin $n$", loc="lower right", labelspacing=0.9,
               borderpad=0.5, handletextpad=0.7, fontsize=5.4,
               title_fontsize=5.8, bbox_to_anchor=(1.0, 0.02))
fig.subplots_adjust(wspace=0.08)
save(fig, "fig_within_condition")

# ============================================ Figure 3: mean confidence by condition
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8), sharey=True)
for ax, conf_c, title, lab in zip(axes, ("ideology_confidence", "stance_confidence"),
                                  ("Ideology", "Stance"), ("a", "b")):
    for mod in MODELS:
        d = preds[preds["model"] == mod]
        ys = [d[d["variant"] == v][conf_c].mean() for v in VARIANTS]
        ax.plot(X, ys, "-o", color=MODEL_COLORS[mod], mfc=MODEL_COLORS[mod],
                mec="white", mew=0.4, alpha=0.95)
    ax.set_xticks(X)
    ax.set_xticklabels(XLAB, rotation=18, ha="right")
    ax.set_title(title, fontweight="bold")
    ax.grid(axis="y", color="#E8E8E8", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(35, 100)
    panel_label(ax, lab)
axes[0].set_ylabel("Mean self-reported confidence")
model_legend(fig)
fig.subplots_adjust(wspace=0.12)
save(fig, "fig_conf_rev")

# ============================================ Figure 4: within-condition AUROC
fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.8), sharey=True)
for ax, task, lab in zip(axes, ("ideology", "stance"), ("a", "b")):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for mod in MODELS:
        ys = []
        for v in VARIANTS:
            d = m[(m["variant"] == v) & (m["model"] == mod)].dropna(subset=[cc, conf_c])
            ys.append(roc_auc_score(d[cc], d[conf_c]) if d[cc].nunique() == 2 else np.nan)
        ax.plot(X, ys, "-o", color=MODEL_COLORS[mod], mfc=MODEL_COLORS[mod],
                mec="white", mew=0.4, alpha=0.95)
    ax.axhline(0.5, ls=(0, (4, 3)), color=GREY_LIGHT, lw=0.8)
    ax.text(0.02, 0.508, "chance", color=GREY, fontsize=5.6, va="bottom")
    ax.set_xticks(X)
    ax.set_xticklabels(XLAB, rotation=18, ha="right")
    ax.set_title(f"{task.capitalize()}", fontweight="bold")
    ax.grid(axis="y", color="#E8E8E8", lw=0.6)
    ax.set_axisbelow(True)
    ax.set_ylim(0.40, 0.90)
    panel_label(ax, lab)
axes[0].set_ylabel("AUROC (confidence vs. correctness)")
model_legend(fig)
fig.subplots_adjust(wspace=0.12)
save(fig, "fig_auroc_within")

print("wrote: fig_f1_rev, fig_within_condition, fig_conf_rev, fig_auroc_within (.pdf + .png) in latex/")
