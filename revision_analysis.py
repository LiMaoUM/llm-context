"""Revision analyses for the EACL R&R.

Reads results/20260115_215043 (the run behind the paper's numbers, per
intercoder_reliability.ipynb) and data/manual/, and computes every number the
revised manuscript needs. Outputs: revision_analysis_output.json + stdout report.

Run: uv run --with statsmodels --with scikit-learn --with openpyxl --with pyarrow revision_analysis.py
"""
import glob
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.metrics import f1_score, roc_auc_score, cohen_kappa_score

warnings.filterwarnings("ignore")
rng = np.random.default_rng(20260609)

RESULTS_DIR = "results/20260115_215043"
OUT = {}

# ---------------------------------------------------------------- model preds
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
    if model == "model":  # combined file
        continue
    df = pd.read_json(fp, lines=True)
    df["model"] = model
    frames.append(df)
preds = pd.concat(frames, ignore_index=True)
parsed = preds["response"].apply(parse_response)
preds["ideology_pred"] = parsed.str[0]
preds["stance_pred_raw"] = parsed.str[1]
# fold non-committal stance into center; ideology already 3-class
preds["stance_pred"] = preds["stance_pred_raw"].replace({"neutral": "center", "undecided": "center"})

OUT["run_dir"] = RESULTS_DIR
OUT["n_models"] = preds["model"].nunique()
OUT["n_unique_posts_inference"] = int(preds["sample_id"].nunique())
OUT["variants"] = sorted(preds["variant"].unique())

# parse / validity rates per model x variant
def validity(g):
    return pd.Series({
        "n": len(g),
        "ideology_parsed": g["ideology_pred"].notna().mean(),
        "stance_parsed": g["stance_pred_raw"].notna().mean(),
        "conf_present": g["ideology_confidence"].notna().mean(),
        "noncommittal_stance": g["stance_pred_raw"].isin(["neutral", "undecided"]).mean(),
        "api_success": g["success"].mean() if "success" in g else np.nan,
    })

val = preds.groupby(["model", "variant"]).apply(validity).round(4)
OUT["validity_by_model_variant"] = val.reset_index().to_dict("records")

# ------------------------------------------------------------------ gold set
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
for name, df, icol, scol in [
    ("qing", qing, "Ideology", "Stance"),
    ("xinyu", xinyu, "ideology", "stance"),
    ("shengteng", sheng, "ideology", "stance"),
]:
    d = df[df["variant"] == "T+B+C+M"][["sample_id", icol, scol]].copy()
    d.columns = ["sample_id", "ideology", "stance"]
    d["ideology"] = d["ideology"].apply(lambda v: norm_label(v, "ideology"))
    d["stance"] = d["stance"].apply(lambda v: norm_label(v, "stance"))
    coders[name] = d.set_index("sample_id")

gold_ids = coders["shengteng"].index
rows = []
for sid in gold_ids:
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

OUT["gold"] = {
    "n_validated_posts": len(gold),
    "ideology": {
        "n_with_majority": int(gold["gt_ideology"].notna().sum()),
        "n_unanimous": int((gold["ideology_agree"] == 3).sum()),
        "n_2of3": int((gold["ideology_agree"] == 2).sum()),
        "n_no_majority": int(gold["gt_ideology"].isna().sum()),
        "class_dist": gold["gt_ideology"].value_counts().to_dict(),
    },
    "stance": {
        "n_with_majority": int(gold["gt_stance"].notna().sum()),
        "n_unanimous": int((gold["stance_agree"] == 3).sum()),
        "n_2of3": int((gold["stance_agree"] == 2).sum()),
        "n_no_majority": int(gold["gt_stance"].isna().sum()),
        "class_dist": gold["gt_stance"].value_counts().to_dict(),
    },
    "platform_dist": gold["platform"].value_counts().to_dict(),
    "class_dist_by_platform": {
        t: gold.groupby("platform")[f"gt_{t}"].value_counts().unstack(fill_value=0).to_dict()
        for t in ("ideology", "stance")
    },
}

# pairwise Cohen kappa on folded labels
kap = {}
pairs = [("qing", "xinyu"), ("qing", "shengteng"), ("xinyu", "shengteng")]
for task in ("ideology", "stance"):
    ks = {}
    for a, b in pairs:
        da, db = coders[a][task], coders[b][task]
        common = da.dropna().index.intersection(db.dropna().index)
        ks[f"{a}-{b}"] = round(cohen_kappa_score(da.loc[common], db.loc[common]), 3)
    kap[task] = ks
OUT["intercoder_kappa_folded"] = kap

# 295 vs 283: which gold posts lack a T row in the coder export, and in the run?
t_export_ids = set(sheng[sheng["variant"] == "T"]["sample_id"])
missing_T = [sid for sid in gold_ids if sid not in t_export_ids]
run_T_ids = set(preds[preds["variant"] == "T"]["sample_id"])
OUT["T_subset"] = {
    "n_missing_T_in_export": len(missing_T),
    "n_of_those_with_T_in_run": sum(sid in run_T_ids for sid in missing_T),
}

# ------------------------------------------------------- merge preds w/ gold
m = preds.merge(gold, on="sample_id", how="inner")
for task in ("ideology", "stance"):
    m[f"{task}_correct"] = (m[f"{task}_pred"] == m[f"gt_{task}"]).astype(float)
    m.loc[m[f"gt_{task}"].isna(), f"{task}_correct"] = np.nan
    # treat unparsed predictions as missing (primary analysis), sensitivity below
    m.loc[m[f"{task}_pred"].isna(), f"{task}_correct"] = np.nan
m["avg_confidence"] = (m["ideology_confidence"] + m["stance_confidence"]) / 2

VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = sorted(m["model"].unique())

# --------------------------------------------- Table 1 recompute w/ boot CIs
def pooled_metrics(d, task):
    sub = d.dropna(subset=[f"gt_{task}", f"{task}_pred"])
    if not len(sub):
        return np.nan, np.nan
    acc = (sub[f"{task}_pred"] == sub[f"gt_{task}"]).mean()
    f1 = f1_score(sub[f"gt_{task}"], sub[f"{task}_pred"], average="macro")
    return acc, f1


def boot_ci(d, task, metric, B=2000):
    ids = d["sample_id"].unique()
    groups = dict(tuple(d.groupby("sample_id")))
    vals = []
    for _ in range(B):
        take = rng.choice(ids, size=len(ids), replace=True)
        bd = pd.concat([groups[i] for i in take], ignore_index=True)
        a, f = pooled_metrics(bd, task)
        vals.append(a if metric == "acc" else f)
    return np.nanpercentile(vals, [2.5, 97.5])


table1 = []
for v in VARIANTS:
    row = {"variant": v}
    dv = m[m["variant"] == v]
    for task in ("ideology", "stance"):
        acc, f1 = pooled_metrics(dv, task)
        lo_a, hi_a = boot_ci(dv, task, "acc", B=500)
        lo_f, hi_f = boot_ci(dv, task, "f1", B=500)
        row[f"{task}_acc"] = round(acc * 100, 1)
        row[f"{task}_acc_ci"] = [round(lo_a * 100, 1), round(hi_a * 100, 1)]
        row[f"{task}_f1"] = round(f1 * 100, 1)
        row[f"{task}_f1_ci"] = [round(lo_f * 100, 1), round(hi_f * 100, 1)]
        # sensitivity: unparsed counted as center
        sub = dv.dropna(subset=[f"gt_{task}"]).copy()
        sub[f"{task}_pred"] = sub[f"{task}_pred"].fillna("center")
        row[f"{task}_acc_unparsed_as_center"] = round((sub[f"{task}_pred"] == sub[f"gt_{task}"]).mean() * 100, 1)
    table1.append(row)
OUT["table1"] = table1

# majority-class baseline
base = {}
for task in ("ideology", "stance"):
    g = gold[f"gt_{task}"].dropna()
    maj = g.value_counts().idxmax()
    acc = (g == maj).mean()
    f1 = f1_score(g, pd.Series([maj] * len(g)), average="macro")
    base[task] = {"majority_class": maj, "acc": round(acc * 100, 1), "macro_f1": round(f1 * 100, 1)}
OUT["majority_baseline"] = base

# platform-prior baseline: bluesky->left/against, truthsocial->right/favor
pp = {}
rule = {"ideology": {"bluesky": "left", "truthsocial": "right"},
        "stance": {"bluesky": "against", "truthsocial": "favor"}}
for task in ("ideology", "stance"):
    g = gold.dropna(subset=[f"gt_{task}"])
    pred = g["platform"].map(rule[task])
    pp[task] = {"acc": round((pred == g[f"gt_{task}"]).mean() * 100, 1),
                "macro_f1": round(f1_score(g[f"gt_{task}"], pred, average="macro") * 100, 1)}
OUT["platform_prior_baseline"] = pp

# per-platform pooled model accuracy by variant
plat_acc = []
for v in VARIANTS:
    for p in ("bluesky", "truthsocial"):
        d = m[(m["variant"] == v) & (m["platform"] == p)]
        row = {"variant": v, "platform": p}
        for task in ("ideology", "stance"):
            a, f1v = pooled_metrics(d, task)
            row[f"{task}_acc"] = round(a * 100, 1) if a == a else None
        plat_acc.append(row)
OUT["platform_accuracy"] = plat_acc

# ------------------------------------- WITHIN-CONDITION confidence->accuracy
def within_condition_auroc():
    out = []
    for task in ("ideology", "stance"):
        cc, conf_c = f"{task}_correct", f"{task}_confidence"
        for v in VARIANTS:
            per_model = {}
            for mod in MODELS:
                d = m[(m["variant"] == v) & (m["model"] == mod)].dropna(subset=[cc, conf_c])
                if d[cc].nunique() == 2 and len(d) > 20:
                    per_model[mod] = round(roc_auc_score(d[cc], d[conf_c]), 3)
                else:
                    per_model[mod] = None
            vals = [x for x in per_model.values() if x is not None]
            out.append({"task": task, "variant": v, "auroc_by_model": per_model,
                        "mean_auroc": round(float(np.mean(vals)), 3) if vals else None,
                        "n_models_above_0.5": sum(x > 0.5 for x in vals)})
    return out

OUT["within_condition_auroc"] = within_condition_auroc()

# pooled-condition AUROC for comparison (what the old analysis implicitly did)
pooled_auroc = []
for task in ("ideology", "stance"):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    per_model = {}
    for mod in MODELS:
        d = m[m["model"] == mod].dropna(subset=[cc, conf_c])
        per_model[mod] = round(roc_auc_score(d[cc], d[conf_c]), 3)
    pooled_auroc.append({"task": task, "auroc_by_model": per_model,
                         "mean_auroc": round(float(np.mean(list(per_model.values()))), 3)})
OUT["pooled_auroc"] = pooled_auroc

# within-condition reliability bins (equal-mass quintiles, pooled across models)
rel = []
for task in ("ideology", "stance"):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for v in ("T", "T+B+C+M"):
        d = m[m["variant"] == v].dropna(subset=[cc, conf_c]).copy()
        try:
            d["bin"] = pd.qcut(d[conf_c], 5, duplicates="drop")
        except ValueError:
            continue
        gb = d.groupby("bin", observed=True).agg(
            n=(cc, "size"), conf=(conf_c, "mean"), acc=(cc, "mean")).reset_index()
        rel.append({"task": task, "variant": v,
                    "bins": [{"n": int(r.n), "conf": round(r.conf, 1), "acc": round(r.acc * 100, 1)}
                             for r in gb.itertuples()]})
OUT["within_condition_reliability"] = rel

# logistic regression: correct ~ conf + C(variant) + C(model), cluster by post
import statsmodels.formula.api as smf

logit_out = {}
for task in ("ideology", "stance"):
    d = m.dropna(subset=[f"{task}_correct", f"{task}_confidence"]).copy()
    d["correct"] = d[f"{task}_correct"]
    d["conf10"] = d[f"{task}_confidence"] / 10.0  # per-10-point OR
    mod = smf.logit("correct ~ conf10 + C(variant) + C(model)", data=d).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": d["sample_id"]})
    logit_out[task] = {
        "n": int(mod.nobs),
        "conf_coef_per10pts": round(mod.params["conf10"], 4),
        "odds_ratio_per10pts": round(float(np.exp(mod.params["conf10"])), 3),
        "z": round(mod.tvalues["conf10"], 2),
        "p": float(mod.pvalues["conf10"]),
    }
    # per-model: count models with significant positive conf coef (within-condition)
    sig = {}
    for mo in MODELS:
        dm = d[d["model"] == mo]
        try:
            mm = smf.logit("correct ~ conf10 + C(variant)", data=dm).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": dm["sample_id"]})
            sig[mo] = {"or_per10": round(float(np.exp(mm.params["conf10"])), 3),
                       "p": float(mm.pvalues["conf10"])}
        except Exception as e:
            sig[mo] = {"error": str(e)[:60]}
    logit_out[task + "_per_model"] = sig
OUT["logit"] = logit_out

# ------------------------------------------------- old pooled-bin disclosure
old_bins = {}
for task in ("ideology", "stance"):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    rowsb = {}
    for mod in MODELS:
        d = m[m["model"] == mod].dropna(subset=[cc, conf_c]).copy()
        d["bin"] = pd.cut(d[conf_c], bins=np.arange(0, 101, 10), include_lowest=True)
        gb = d.groupby("bin", observed=True)[cc].agg(["size", "mean"])
        nz = gb[gb["size"] > 0]
        rowsb[mod] = {"lowest_bin_n": int(nz.iloc[0]["size"]), "lowest_bin_acc": round(nz.iloc[0]["mean"] * 100, 1),
                      "highest_bin_n": int(nz.iloc[-1]["size"]), "highest_bin_acc": round(nz.iloc[-1]["mean"] * 100, 1)}
    old_bins[task] = rowsb
OUT["old_pooled_equalwidth_bins"] = old_bins

# ------------------------------------------------------- ECE / Brier / gaps
cal = []
for task in ("ideology", "stance"):
    cc, conf_c = f"{task}_correct", f"{task}_confidence"
    for mod in MODELS:
        d = m[m["model"] == mod].dropna(subset=[cc, conf_c]).copy()
        p = d[conf_c] / 100.0
        y = d[cc]
        try:
            d["bin"] = pd.qcut(p, 10, duplicates="drop")
            gb = d.assign(p=p).groupby("bin", observed=True).agg(n=("p", "size"), conf=("p", "mean"), acc=(cc, "mean"))
            ece = float((gb["n"] / gb["n"].sum() * (gb["conf"] - gb["acc"]).abs()).sum())
        except ValueError:
            ece = np.nan
        cal.append({"task": task, "model": mod,
                    "mean_conf": round(float(d[conf_c].mean()), 1),
                    "acc": round(float(y.mean()) * 100, 1),
                    "gap": round(float(d[conf_c].mean() - y.mean() * 100), 1),
                    "ece": round(ece, 3),
                    "brier": round(float(((p - y) ** 2).mean()), 3),
                    "confidently_wrong_pct": round(float((1 - y[d[conf_c] >= 70].mean()) * 100), 1)
                    if (d[conf_c] >= 70).sum() > 0 else None})
OUT["calibration_by_model"] = cal

# ------------------------------------ coder unanimity vs model confidence
unan = {}
for task in ("ideology", "stance"):
    conf_c = f"{task}_confidence"
    d = m[m["variant"] == "T+B+C+M"].dropna(subset=[conf_c]).merge(
        gold[["sample_id", f"{task}_agree"]], on="sample_id", suffixes=("", "_g"))
    d = d[d[f"{task}_agree{'' if f'{task}_agree' in d else '_g'}"].notna()] if False else d
    agree_col = f"{task}_agree" if f"{task}_agree" in d.columns else f"{task}_agree_g"
    g3 = d[d[agree_col] == 3][conf_c]
    g2 = d[d[agree_col] == 2][conf_c]
    u = sps.mannwhitneyu(g3, g2, alternative="greater")
    # also correctness by unanimity
    accs = d.groupby(agree_col)[f"{task}_correct"].mean()
    unan[task] = {"mean_conf_unanimous": round(float(g3.mean()), 1),
                  "mean_conf_2of3": round(float(g2.mean()), 1),
                  "n_unanimous_rows": int(len(g3)), "n_2of3_rows": int(len(g2)),
                  "mannwhitney_p_greater": float(u.pvalue),
                  "acc_by_agreement": {str(k): round(float(v) * 100, 1) for k, v in accs.items()}}
    # per-condition deltas
    per_v = {}
    for v in VARIANTS:
        dv = m[m["variant"] == v].dropna(subset=[conf_c]).merge(
            gold[["sample_id", f"{task}_agree"]], on="sample_id", suffixes=("", "_g"))
        ac = f"{task}_agree" if f"{task}_agree" in dv.columns else f"{task}_agree_g"
        per_v[v] = round(float(dv[dv[ac] == 3][conf_c].mean() - dv[dv[ac] == 2][conf_c].mean()), 1)
    unan[task]["conf_delta_unan_minus_2of3_by_variant"] = per_v
OUT["unanimity_vs_confidence"] = unan

# --------------------------------- human confidence agreement spot-check
cq = pd.read_excel("data/manual/conf_manual.xlsx")
cx = pd.read_csv("data/manual/conf_manual_Xinyu_1.14.csv")
cq.columns = [c.strip().lower().replace(" ", "_") for c in cq.columns]
cx.columns = [c.strip().lower() for c in cx.columns]
cq = cq[cq["variant"] == "T"][["sample_id", "ideology_confidence", "stance_confidence"]].rename(
    columns={"ideology_confidence": "q_ideo", "stance_confidence": "q_stance"})
cx = cx[cx["variant"] == "T"][["sample_id", "confidence", "confidence.1"]].rename(
    columns={"confidence": "x_ideo", "confidence.1": "x_stance"})
hc = cq.merge(cx, on="sample_id")
hc["h_ideo"] = hc[["q_ideo", "x_ideo"]].mean(axis=1)
hc["h_stance"] = hc[["q_stance", "x_stance"]].mean(axis=1)

def bucket(c):
    return np.where(c <= 33, 0, np.where(c <= 66, 1, 2))

hum = {"n": len(hc),
       "qing_means": [round(hc["q_ideo"].mean(), 1), round(hc["q_stance"].mean(), 1)],
       "xinyu_means": [round(hc["x_ideo"].mean(), 1), round(hc["x_stance"].mean(), 1)],
       "coder_spearman": [round(sps.spearmanr(hc["q_ideo"], hc["x_ideo"], nan_policy="omit").statistic, 2),
                          round(sps.spearmanr(hc["q_stance"], hc["x_stance"], nan_policy="omit").statistic, 2)],
       "coder_kw": [round(cohen_kappa_score(bucket(hc["q_ideo"].dropna()), bucket(hc["x_ideo"].dropna()), weights="quadratic"), 2)
                    if hc["q_ideo"].notna().all() else None, None]}
# model vs human (verify gpt-oss + one overconfident model)
mv = {}
for mod in ("gpt-oss-120b", "qwen3-30b-a3b"):
    d = m[(m["model"] == mod) & (m["variant"] == "T")][["sample_id", "ideology_confidence", "stance_confidence"]]
    dd = d.merge(hc, on="sample_id").dropna(subset=["ideology_confidence", "h_ideo"])
    mv[mod] = {"n": len(dd),
               "mean_conf": [round(dd["ideology_confidence"].mean(), 1), round(dd["stance_confidence"].mean(), 1)],
               "spearman_ideo": round(sps.spearmanr(dd["ideology_confidence"], dd["h_ideo"]).statistic, 2),
               "kw_ideo": round(cohen_kappa_score(bucket(dd["ideology_confidence"]), bucket(dd["h_ideo"]), weights="quadratic"), 2),
               "spearman_stance": round(sps.spearmanr(dd["stance_confidence"].dropna(), dd.loc[dd["stance_confidence"].notna(), "h_stance"]).statistic, 2)}
hum["model_vs_human_spotcheck"] = mv
OUT["human_confidence"] = hum

# ------------------------------------------------------------------- output
with open("revision_analysis_output.json", "w") as f:
    json.dump(OUT, f, indent=2, default=str)

print(json.dumps(OUT, indent=2, default=str)[:12000])
print("\n... full output in revision_analysis_output.json")
