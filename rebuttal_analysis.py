"""ARR rebuttal analyses (reviews in docs/reviews/2026-09-arr-submission2351-reviews.md).

Computes, from the paper run (results/20260115_215043) and existing seed-stability data:
  A. per-condition absolute calibration (gap, ECE, confidently-wrong) per model x condition x task
     [h3ni W1]
  B. risk-coverage curves and AURC for confidence triage vs the platform rule, plus
     confidence triage within each platform                                          [h3ni W3]
  C. sample agreement vs verbalized confidence as a reliability signal, on the existing
     3-seed re-decoding of gemma-3-27b-it and qwen3-4b (extended by sample_agreement_run.py)
                                                                          [8FDE W2, 24ts W2, W3]
  D. per-coder confidence agreement (model vs each coder separately)                 [8FDE W3]
  E. Bluesky stance majority baseline and per-platform per-condition numbers          [8FDE W1]

Outputs: rebuttal_analysis_output.json + stdout report.
Run: uv run --with statsmodels --with scikit-learn --with openpyxl --with pyarrow rebuttal_analysis.py
"""
import glob
import json
import os
import re
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import cohen_kappa_score, roc_auc_score

warnings.filterwarnings("ignore")

RESULTS_DIR = "results/20260115_215043"
VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = ["gemma-3-27b-it", "gpt-oss-120b", "llama-3.1-8b", "ministral-3-14b",
          "ministral-3-8b", "qwen3-30b-a3b", "qwen3-4b", "qwen3-80b-a3b"]
SEED_FILES = sorted(glob.glob("seed_stability_*.jsonl")) + sorted(glob.glob("sample_agreement/*.jsonl"))
OUT = {}


def parse_response(response):
    if pd.isna(response) or response == "---":
        return None, None
    s = str(response).lower()
    m = re.search(r"ideology:\s*\**\s*(left|center|right)", s)
    ideology = m.group(1) if m else None
    m = re.search(r"(?:trump stance|stance toward trump|stance towards trump|stance):\s*\**\s*(favor|against|neutral|undecided)", s)
    stance = m.group(1) if m else None
    return ideology, stance


def fold_stance(x):
    return {"neutral": "center", "undecided": "center"}.get(x, x)


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


# ------------------------------------------------------------------ gold set
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
        votes = [coders[c].loc[sid, task] for c in coders if sid in coders[c].index]
        votes = [v for v in votes if pd.notna(v)]
        vc = pd.Series(votes).value_counts()
        if len(vc) and vc.iloc[0] >= 2:
            rec[f"gt_{task}"] = vc.index[0]
            rec[f"{task}_agree"] = int(vc.iloc[0])
        else:
            rec[f"gt_{task}"] = np.nan
            rec[f"{task}_agree"] = 1 if len(vc) else 0
    rows.append(rec)
gold = pd.DataFrame(rows)
gold["platform"] = np.where(gold["sample_id"].astype(str).str.startswith("at://"), "bluesky", "truthsocial")

# ------------------------------------------------------------ model preds
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
preds["stance_pred"] = parsed.str[1].map(fold_stance)
for c in ("ideology_confidence", "stance_confidence"):
    preds[c] = pd.to_numeric(preds[c], errors="coerce")
m = preds.merge(gold, on="sample_id", how="inner").drop_duplicates(["model", "variant", "sample_id"])
m = m[m["model"].isin(MODELS)]
for task in ("ideology", "stance"):
    m[f"{task}_correct"] = (m[f"{task}_pred"] == m[f"gt_{task}"]).astype(float)
    m.loc[m[f"{task}_pred"].isna() | m[f"gt_{task}"].isna(), f"{task}_correct"] = np.nan


def ece(conf, correct, nbins=10):
    conf = np.asarray(conf, float) / 100.0
    correct = np.asarray(correct, float)
    order = np.argsort(conf, kind="stable")
    bins = np.array_split(order, nbins)
    e = 0.0
    for b in bins:
        if len(b) == 0:
            continue
        e += len(b) / len(conf) * abs(conf[b].mean() - correct[b].mean())
    return e


def calib_stats(d, task):
    d = d.dropna(subset=[f"{task}_confidence", f"{task}_correct"])
    if len(d) < 20:
        return None
    c, y = d[f"{task}_confidence"].values, d[f"{task}_correct"].values
    hi = c >= 70
    return {"n": int(len(d)), "mean_conf": round(c.mean(), 1), "acc": round(100 * y.mean(), 1),
            "gap": round(c.mean() - 100 * y.mean(), 1), "ece": round(ece(c, y), 3),
            "cw_pct": round(100 * (1 - y[hi].mean()), 1) if hi.sum() else None,
            "n_hi": int(hi.sum())}


# ================================================================ A. per-condition calibration
A = {"per_model_condition": [], "pooled_by_condition": [], "pooled_over_conditions": []}
for task in ("ideology", "stance"):
    for mod in MODELS:
        for v in VARIANTS:
            s = calib_stats(m[(m["model"] == mod) & (m["variant"] == v)], task)
            if s:
                A["per_model_condition"].append({"task": task, "model": mod, "variant": v, **s})
        s = calib_stats(m[m["model"] == mod], task)
        A["pooled_over_conditions"].append({"task": task, "model": mod, **s})
    for v in VARIANTS:
        s = calib_stats(m[m["variant"] == v], task)
        A["pooled_by_condition"].append({"task": task, "variant": v, **s})

# does the pooled check detect condition-level overconfidence? compare pooled gap with min/max per-condition gap
pc = pd.DataFrame(A["per_model_condition"])
summ = []
for (task, mod), g in pc.groupby(["task", "model"]):
    pooled = next(r for r in A["pooled_over_conditions"] if r["task"] == task and r["model"] == mod)
    summ.append({"task": task, "model": mod, "pooled_gap": pooled["gap"], "pooled_ece": pooled["ece"],
                 "gap_T": float(g[g.variant == "T"]["gap"].iloc[0]),
                 "gap_full": float(g[g.variant == "T+B+C+M"]["gap"].iloc[0]),
                 "min_gap": float(g["gap"].min()), "max_gap": float(g["gap"].max()),
                 "ece_T": float(g[g.variant == "T"]["ece"].iloc[0]),
                 "ece_full": float(g[g.variant == "T+B+C+M"]["ece"].iloc[0]),
                 "max_ece": float(g["ece"].max())})
A["pooled_vs_condition_summary"] = summ
# ranking of least-overconfident model per task, pooled and per condition
A["least_overconfident"] = {}
for task in ("ideology", "stance"):
    r = {}
    p = [x for x in A["pooled_over_conditions"] if x["task"] == task]
    r["pooled_by_gap"] = sorted(p, key=lambda x: x["gap"])[0]["model"]
    r["pooled_by_ece"] = sorted(p, key=lambda x: x["ece"])[0]["model"]
    for v in VARIANTS:
        q = pc[(pc.task == task) & (pc.variant == v)]
        r[f"{v}_by_gap"] = q.sort_values("gap").iloc[0]["model"]
        r[f"{v}_by_ece"] = q.sort_values("ece").iloc[0]["model"]
    A["least_overconfident"][task] = r
OUT["A_calibration"] = A

# ================================================================ B. risk-coverage / AURC
def risk_coverage(score, correct, n_grid=None):
    """Sort by score desc; return coverage grid and selective risk; AURC = mean risk over coverage."""
    score = np.asarray(score, float)
    correct = np.asarray(correct, float)
    # random tie-break with fixed rng so ties at round confidence values do not favor either policy
    rng = np.random.default_rng(0)
    order = np.lexsort((rng.random(len(score)), -score))
    c = correct[order]
    cum_err = np.cumsum(1 - c) / np.arange(1, len(c) + 1)
    cov = np.arange(1, len(c) + 1) / len(c)
    return cov, cum_err


def acc_at_cov(cov, risk, x):
    i = np.searchsorted(cov, x)
    i = min(i, len(cov) - 1)
    return round(100 * (1 - risk[i]), 1)


B = {}
for task in ("ideology", "stance"):
    d = m[(m["variant"] == "T+B+C+M")].dropna(subset=[f"{task}_confidence", f"{task}_correct"]).copy()
    y = d[f"{task}_correct"].values
    ts_share = (d["platform"] == "truthsocial").mean()
    # policy 1: verbalized confidence
    cov1, r1 = risk_coverage(d[f"{task}_confidence"].values, y)
    # policy 2: platform rule (keep Truth Social first, then Bluesky; within each, random order)
    cov2, r2 = risk_coverage((d["platform"] == "truthsocial").astype(float).values, y)
    # policy 3: platform then confidence within platform
    cov3, r3 = risk_coverage(((d["platform"] == "truthsocial").astype(float) * 1000 + d[f"{task}_confidence"]).values, y)
    # policy 4: random (baseline)
    cov4, r4 = risk_coverage(np.zeros(len(d)), y)
    res = {"n": int(len(d)), "truthsocial_share": round(100 * ts_share, 1),
           "aurc_confidence": round(100 * r1.mean(), 2), "aurc_platform_rule": round(100 * r2.mean(), 2),
           "aurc_platform_then_confidence": round(100 * r3.mean(), 2), "aurc_random": round(100 * r4.mean(), 2)}
    for x in (0.2, 0.4, 0.6, ts_share, 0.8, 1.0):
        k = f"acc_at_{round(100*x)}"
        res[k] = {"confidence": acc_at_cov(cov1, r1, x), "platform_rule": acc_at_cov(cov2, r2, x),
                  "platform_then_confidence": acc_at_cov(cov3, r3, x)}
    # bootstrap CI on AURC difference (confidence vs platform rule), resampling posts
    rng = np.random.default_rng(1)
    posts = d["sample_id"].unique()
    diffs = []
    for _ in range(500):
        samp = rng.choice(posts, len(posts), replace=True)
        dd = pd.concat([d[d["sample_id"] == s] for s in samp])
        yy = dd[f"{task}_correct"].values
        _, a = risk_coverage(dd[f"{task}_confidence"].values, yy)
        _, b = risk_coverage((dd["platform"] == "truthsocial").astype(float).values, yy)
        diffs.append(100 * (a.mean() - b.mean()))
    res["aurc_diff_conf_minus_platform_ci95"] = [round(np.percentile(diffs, 2.5), 2), round(np.percentile(diffs, 97.5), 2)]
    # within-platform triage: accuracy at 100/80/60/40/20 coverage inside each platform
    wp = {}
    for plat in ("truthsocial", "bluesky"):
        dp = d[d["platform"] == plat]
        cov, r = risk_coverage(dp[f"{task}_confidence"].values, dp[f"{task}_correct"].values)
        wp[plat] = {"n": int(len(dp)), **{f"acc_at_{x}": acc_at_cov(cov, r, x / 100) for x in (100, 80, 60, 40, 20)},
                    "aurc": round(100 * r.mean(), 2)}
        # per model AUROC within platform at full context
        aucs = []
        for mod in MODELS:
            dm = dp[dp["model"] == mod]
            if dm[f"{task}_correct"].nunique() == 2:
                aucs.append(roc_auc_score(dm[f"{task}_correct"], dm[f"{task}_confidence"]))
        wp[plat]["auroc_mean_over_models"] = round(float(np.mean(aucs)), 3)
        wp[plat]["auroc_min_over_models"] = round(float(np.min(aucs)), 3)
    res["within_platform"] = wp
    # curves for plotting (100-point grid)
    grid = np.linspace(0.05, 1.0, 96)
    res["curves"] = {"coverage": [round(g, 3) for g in grid],
                     "confidence": [acc_at_cov(cov1, r1, g) for g in grid],
                     "platform_rule": [acc_at_cov(cov2, r2, g) for g in grid],
                     "platform_then_confidence": [acc_at_cov(cov3, r3, g) for g in grid]}
    B[task] = res
OUT["B_risk_coverage"] = B

# ================================================================ C. sample agreement vs verbalized
C = {}
seed_frames = []
for fp in SEED_FILES:
    df = pd.read_json(fp, lines=True)
    mod = re.sub(r"^.*?(seed_stability_|sample_agreement/)", "", fp).replace(".jsonl", "")
    df["model"] = mod
    seed_frames.append(df)
if seed_frames:
    sd = pd.concat(seed_frames, ignore_index=True)
    sd["stance"] = sd["stance"].map(fold_stance)
    sd = sd.drop_duplicates(["model", "sample_id", "variant", "seed"])
    sd = sd.merge(gold, on="sample_id", how="inner")
    for mod, gm in sd.groupby("model"):
        seeds = sorted(gm["seed"].unique())
        res = {"seeds": [int(s) for s in seeds], "k": len(seeds)}
        for task in ("ideology", "stance"):
            conf_col = "ideo_conf" if task == "ideology" else "stance_conf"
            cells = []
            for (sid, var), g in gm.groupby(["sample_id", "variant"]):
                g = g.dropna(subset=[task])
                if len(g) < 2 or pd.isna(g[f"gt_{task}"].iloc[0]):
                    continue
                gt = g[f"gt_{task}"].iloc[0]
                labels = g[task].tolist()
                vc = pd.Series(labels).value_counts()
                modal, modal_n = vc.index[0], int(vc.iloc[0])
                # policy view: the "deployed" prediction is the first seed's; extra samples give agreement
                first = g.sort_values("seed").iloc[0]
                others = g.sort_values("seed").iloc[1:]
                agree_first = (others[task] == first[task]).mean()  # share of extra samples agreeing with deployed label
                cells.append({"sample_id": sid, "variant": var, "platform": g["platform"].iloc[0],
                              "gt": gt, "n_seeds": len(g),
                              "first_label": first[task], "first_conf": first[conf_col],
                              "first_correct": float(first[task] == gt),
                              "agree_first": agree_first,
                              "modal_label": modal, "modal_share": modal_n / len(g),
                              "modal_correct": float(modal == gt),
                              "mean_conf": g[conf_col].mean(),
                              "unanimous_coders": float(g[f"{task}_agree"].iloc[0] == 3)})
            cdf = pd.DataFrame(cells)
            r = {"n_cells": int(len(cdf)),
                 "acc_first_seed": round(100 * cdf["first_correct"].mean(), 1),
                 "acc_majority_vote": round(100 * cdf["modal_correct"].mean(), 1),
                 "share_cells_full_agreement": round(100 * (cdf["modal_share"] == 1).mean(), 1),
                 "spearman_conf_vs_agreement": round(sps.spearmanr(cdf["first_conf"].fillna(cdf["first_conf"].median()), cdf["agree_first"]).statistic, 3)}
            # AUROC for first-seed correctness: verbalized conf vs agreement vs combination, pooled and within condition
            def aucs(sub):
                out = {}
                y = sub["first_correct"]
                if y.nunique() < 2:
                    return out
                fc = sub["first_conf"].fillna(sub["first_conf"].median())
                out["verbalized"] = round(roc_auc_score(y, fc), 3)
                out["agreement"] = round(roc_auc_score(y, sub["agree_first"]), 3)
                # combination: rank-average
                comb = fc.rank(pct=True) + sub["agree_first"].rank(pct=True)
                out["combined"] = round(roc_auc_score(y, comb), 3)
                out["mean_conf_over_seeds"] = round(roc_auc_score(y, sub["mean_conf"].fillna(sub["mean_conf"].median())), 3)
                out["n"] = int(len(sub))
                return out
            r["auroc_pooled"] = aucs(cdf)
            r["auroc_by_condition"] = {v: aucs(cdf[cdf.variant == v]) for v in VARIANTS}
            # coverage-matched accuracy at full context and text-only: keep top 60% by each signal
            cm = {}
            for v in ("T", "T+B+C+M"):
                sub = cdf[cdf.variant == v]
                y = sub["first_correct"].values
                row = {}
                for name, sc in [("verbalized", sub["first_conf"].fillna(0).values), ("agreement", sub["agree_first"].values),
                                 ("combined", (sub["first_conf"].fillna(0).rank(pct=True) + sub["agree_first"].rank(pct=True)).values)]:
                    cov, risk = risk_coverage(sc, y)
                    row[name] = {f"acc_at_{x}": acc_at_cov(cov, risk, x / 100) for x in (100, 80, 60, 40)}
                    row[name]["aurc"] = round(100 * risk.mean(), 2)
                cm[v] = row
            r["coverage_matched"] = cm
            # predicting human disagreement (24ts W2): AUROC for "coders unanimous" from agreement / confidence, full context
            hd = {}
            for v in ("T", "T+B+C+M"):
                sub = cdf[cdf.variant == v]
                yu = sub["unanimous_coders"]
                if yu.nunique() == 2:
                    hd[v] = {"auroc_agreement": round(roc_auc_score(yu, sub["agree_first"]), 3),
                             "auroc_verbalized": round(roc_auc_score(yu, sub["first_conf"].fillna(0)), 3),
                             "n_unanimous": int(yu.sum()), "n_split": int((yu == 0).sum()),
                             "flip_rate_unanimous": round(100 * (sub[yu == 1]["modal_share"] < 1).mean(), 1),
                             "flip_rate_split": round(100 * (sub[yu == 0]["modal_share"] < 1).mean(), 1)}
            r["predict_human_disagreement"] = hd
            res[task] = r
        C[mod] = res
OUT["C_sample_agreement"] = C

# ================================================================ D. per-coder confidence agreement
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
hc = cq.merge(cx, on="sample_id").dropna()
hc["h_ideo"] = hc[["q_ideo", "x_ideo"]].mean(axis=1)
hc["h_stance"] = hc[["q_stance", "x_stance"]].mean(axis=1)
# scale-free consensus: average of within-coder percentile ranks
for t in ("ideo", "stance"):
    hc[f"hr_{t}"] = (hc[f"q_{t}"].rank(pct=True) + hc[f"x_{t}"].rank(pct=True)) / 2


def bucket(c):
    c = np.asarray(c, dtype=float)
    return np.where(c <= 33, 0, np.where(c <= 66, 1, 2))


D = {"n": int(len(hc)),
     "coder_means": {"qing": [round(hc.q_ideo.mean(), 1), round(hc.q_stance.mean(), 1)],
                     "xinyu": [round(hc.x_ideo.mean(), 1), round(hc.x_stance.mean(), 1)]},
     "coder_spearman": [round(sps.spearmanr(hc.q_ideo, hc.x_ideo).statistic, 2), round(sps.spearmanr(hc.q_stance, hc.x_stance).statistic, 2)],
     "coder_kw": [round(cohen_kappa_score(bucket(hc.q_ideo), bucket(hc.x_ideo), weights="quadratic"), 2),
                  round(cohen_kappa_score(bucket(hc.q_stance), bucket(hc.x_stance), weights="quadratic"), 2)],
     "per_model": []}
for mod in MODELS:
    d = m[(m["model"] == mod) & (m["variant"] == "T")][["sample_id", "ideology_confidence", "stance_confidence"]]
    dd = d.merge(hc, on="sample_id").dropna(subset=["ideology_confidence", "stance_confidence"])
    row = {"model": mod, "n": int(len(dd))}
    for t, mc in (("ideo", "ideology_confidence"), ("stance", "stance_confidence")):
        row[f"mean_conf_{t}"] = round(dd[mc].mean(), 1)
        for coder in ("q", "x", "h"):
            row[f"rho_{t}_{coder}"] = round(sps.spearmanr(dd[mc], dd[f"{coder}_{t}"]).statistic, 2)
            row[f"kw_{t}_{coder}"] = round(cohen_kappa_score(bucket(dd[mc]), bucket(dd[f"{coder}_{t}"]), weights="quadratic"), 2)
        row[f"rho_{t}_rankmean"] = round(sps.spearmanr(dd[mc], dd[f"hr_{t}"]).statistic, 2)
    D["per_model"].append(row)
OUT["D_per_coder_confidence"] = D

# ================================================================ E. Bluesky stance
E = {}
for task in ("ideology", "stance"):
    for plat in ("bluesky", "truthsocial"):
        gp = gold[gold.platform == plat].dropna(subset=[f"gt_{task}"])
        maj = gp[f"gt_{task}"].value_counts()
        rec = {"n_gold": int(len(gp)), "majority_class": maj.index[0], "majority_baseline_acc": round(100 * maj.iloc[0] / len(gp), 1),
               "class_dist": maj.to_dict()}
        for v in VARIANTS:
            d = m[(m.variant == v) & (m.platform == plat)].dropna(subset=[f"{task}_correct"])
            rec[f"acc_{v}"] = round(100 * d[f"{task}_correct"].mean(), 1)
            # 95% CI via post-level bootstrap
            per_post = d.groupby("sample_id")[f"{task}_correct"].mean()
            rng = np.random.default_rng(2)
            bs = [rng.choice(per_post.values, len(per_post), replace=True).mean() for _ in range(1000)]
            rec[f"acc_{v}_ci"] = [round(100 * np.percentile(bs, 2.5), 1), round(100 * np.percentile(bs, 97.5), 1)]
            rec[f"macro_f1_{v}"] = round(100 * __import__("sklearn.metrics", fromlist=["f1_score"]).f1_score(
                d[f"gt_{task}"], d[f"{task}_pred"], average="macro"), 1)
            rec[f"pred_dist_{v}"] = d[f"{task}_pred"].value_counts(normalize=True).round(3).to_dict()
        E[f"{task}_{plat}"] = rec
OUT["E_platform"] = E

with open("rebuttal_analysis_output.json", "w") as f:
    json.dump(OUT, f, indent=1, default=float)

# ------------------------------------------------------------------ report
print("=== A. per-condition calibration (gap / ECE / CW%) ===")
for task in ("ideology", "stance"):
    print(f"\n[{task}]  model            " + "  ".join(f"{v:>16}" for v in VARIANTS) + "   pooled")
    for mod in MODELS:
        cells = []
        for v in VARIANTS:
            r = next((x for x in A["per_model_condition"] if x["task"] == task and x["model"] == mod and x["variant"] == v), None)
            cells.append(f"{r['gap']:5.1f}/{r['ece']:.2f}/{r['cw_pct'] if r['cw_pct'] is not None else float('nan'):4.1f}" if r else " " * 16)
        p = next(x for x in A["pooled_over_conditions"] if x["task"] == task and x["model"] == mod)
        print(f"  {mod:16s} " + "  ".join(f"{c:>16}" for c in cells) + f"   {p['gap']:5.1f}/{p['ece']:.2f}/{p['cw_pct']:4.1f}")
    print("  pooled over models: " + "  ".join(f"{x['variant']}:{x['gap']}/{x['ece']}" for x in A["pooled_by_condition"] if x["task"] == task))
    print("  least overconfident:", A["least_overconfident"][task])

print("\n=== B. risk-coverage, full context ===")
for task, r in B.items():
    print(f"[{task}] n={r['n']} TS share={r['truthsocial_share']}%  AURC conf={r['aurc_confidence']} platform={r['aurc_platform_rule']} "
          f"platform+conf={r['aurc_platform_then_confidence']} random={r['aurc_random']}  diff CI={r['aurc_diff_conf_minus_platform_ci95']}")
    for k, v in r.items():
        if k.startswith("acc_at_"):
            print(f"   {k}: {v}")
    for plat, w in r["within_platform"].items():
        print(f"   within {plat}: {w}")

print("\n=== C. sample agreement vs verbalized confidence ===")
for mod, r in C.items():
    print(f"[{mod}] seeds={r['seeds']}")
    for task in ("ideology", "stance"):
        t = r[task]
        print(f"  {task}: n={t['n_cells']} acc first={t['acc_first_seed']} majority={t['acc_majority_vote']} "
              f"full-agree cells={t['share_cells_full_agreement']}% rho(conf,agree)={t['spearman_conf_vs_agreement']}")
        print(f"    AUROC pooled: {t['auroc_pooled']}")
        for v, a in t["auroc_by_condition"].items():
            print(f"    AUROC {v:8s}: {a}")
        for v, cm in t["coverage_matched"].items():
            print(f"    coverage {v}: " + " | ".join(f"{k}: {vv}" for k, vv in cm.items()))
        print(f"    human-disagreement prediction: {t['predict_human_disagreement']}")

print("\n=== D. per-coder confidence agreement (text-only) ===")
print(f"n={D['n']} coder means={D['coder_means']} rho={D['coder_spearman']} kw={D['coder_kw']}")
print("  model            mean   rho_q  rho_x  rho_h  rho_rk | kw_q  kw_x  kw_h   (ideology)   || (stance) mean rho_q rho_x rho_h rho_rk | kw_q kw_x kw_h")
for r in D["per_model"]:
    print(f"  {r['model']:16s} {r['mean_conf_ideo']:5.1f}  {r['rho_ideo_q']:5.2f} {r['rho_ideo_x']:5.2f} {r['rho_ideo_h']:5.2f} {r['rho_ideo_rankmean']:5.2f} | "
          f"{r['kw_ideo_q']:5.2f} {r['kw_ideo_x']:5.2f} {r['kw_ideo_h']:5.2f}   || {r['mean_conf_stance']:5.1f} {r['rho_stance_q']:5.2f} {r['rho_stance_x']:5.2f} "
          f"{r['rho_stance_h']:5.2f} {r['rho_stance_rankmean']:5.2f} | {r['kw_stance_q']:5.2f} {r['kw_stance_x']:5.2f} {r['kw_stance_h']:5.2f}")

print("\n=== E. per-platform ===")
for k, r in E.items():
    print(f"[{k}] n={r['n_gold']} majority={r['majority_class']} ({r['majority_baseline_acc']}%)  " +
          "  ".join(f"{v}: {r[f'acc_{v}']} {r[f'acc_{v}_ci']} F1={r[f'macro_f1_{v}']}" for v in VARIANTS))
    for v in VARIANTS:
        print(f"    pred dist {v}: {r[f'pred_dist_{v}']}")
