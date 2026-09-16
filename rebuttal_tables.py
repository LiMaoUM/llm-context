"""Render the rebuttal appendix tables from rebuttal_analysis_output.json into latex/tab_rebuttal.tex.

Tables: tab:calibration_cond (per-condition gap/ECE), tab:aurc (risk-coverage AURC and matched
coverage vs the platform rule, within-platform triage), tab:conf_agree_coder (per-coder confidence
agreement), tab:agreement (sample agreement vs verbalized confidence, one row per model x task).
Run: uv run rebuttal_tables.py
"""
import json

O = json.load(open("rebuttal_analysis_output.json"))
VARIANTS = ["T", "T+B", "T+B+C", "T+B+C+M"]
MODELS = ["gemma-3-27b-it", "gpt-oss-120b", "llama-3.1-8b", "ministral-3-14b",
          "ministral-3-8b", "qwen3-30b-a3b", "qwen3-4b", "qwen3-80b-a3b"]
out = []

# ---------------------------------------------------------------- per-condition calibration
pc = O["A_calibration"]["per_model_condition"]
pooled_cond = O["A_calibration"]["pooled_by_condition"]
out.append(r"""\begin{table*}[t]
\centering
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{l|cccc|cccc}
\toprule
 & \multicolumn{4}{c|}{Ideology: gap / ECE} & \multicolumn{4}{c}{Stance: gap / ECE} \\
Model & T & T+B & T+B+C & Full & T & T+B & T+B+C & Full \\
\midrule""")
for mod in MODELS:
    cells = []
    for task in ("ideology", "stance"):
        for v in VARIANTS:
            r = next(x for x in pc if x["task"] == task and x["model"] == mod and x["variant"] == v)
            cells.append(f"{r['gap']:.1f} / {r['ece']:.2f}")
    out.append(f"{mod} & " + " & ".join(cells) + r" \\")
out.append(r"\midrule")
cells = []
for task in ("ideology", "stance"):
    for v in VARIANTS:
        r = next(x for x in pooled_cond if x["task"] == task and x["variant"] == v)
        cells.append(f"{r['gap']:.1f} / {r['ece']:.2f}")
out.append("Pooled over models & " + " & ".join(cells) + r" \\")
out.append(r"""\bottomrule
\end{tabular}
\caption{Absolute calibration \emph{per context condition}: confidence--accuracy gap (points; negative means under-confident) and expected calibration error (10 equal-mass bins), per model and task. Mean confidence exceeds accuracy in 62 of 64 cells; the exceptions are gemma-3-27b-it and gpt-oss-120b on ideology at full context. The gap is largest at T+B for almost every model and smallest at full context, so a check pooled over conditions (Table~\ref{tab:calibration}) averages a model's worst and best cases.}
\label{tab:calibration_cond}
\end{table*}
""")

# ---------------------------------------------------------------- AURC
B = O["B_risk_coverage"]
out.append(r"""\begin{table}[h]
\centering
\small
\setlength{\tabcolsep}{4pt}
\begin{tabular}{lcc}
\toprule
Selection policy (full context) & Ideology & Stance \\
\midrule""")
rows = [("Random order", "aurc_random"), ("Platform rule (Truth Social first)", "aurc_platform_rule"),
        ("Verbalized confidence", "aurc_confidence"), ("Platform, then confidence within platform", "aurc_platform_then_confidence")]
for name, k in rows:
    out.append(f"{name} & {B['ideology'][k]:.1f} & {B['stance'][k]:.1f} " + r"\\")
ci_i, ci_s = B["ideology"]["aurc_diff_conf_minus_platform_ci95"], B["stance"]["aurc_diff_conf_minus_platform_ci95"]
out.append(r"\midrule")
out.append(r"\multicolumn{3}{l}{\emph{Accuracy (\%) at the platform rule's coverage}}\\")
ki = [k for k in B["ideology"] if k.startswith("acc_at_") and k not in ("acc_at_20", "acc_at_40", "acc_at_60", "acc_at_80", "acc_at_100")][0]
ks = [k for k in B["stance"] if k.startswith("acc_at_") and k not in ("acc_at_20", "acc_at_40", "acc_at_60", "acc_at_80", "acc_at_100")][0]
out.append(f"Platform rule & {B['ideology'][ki]['platform_rule']:.1f} & {B['stance'][ks]['platform_rule']:.1f} " + r"\\")
out.append(f"Verbalized confidence & {B['ideology'][ki]['confidence']:.1f} & {B['stance'][ks]['confidence']:.1f} " + r"\\")
out.append(r"\midrule")
out.append(r"\multicolumn{3}{l}{\emph{Confidence triage within platform: accuracy at 100 / 60 / 20\% coverage}}\\")
for plat, name in (("truthsocial", "Truth Social"), ("bluesky", "Bluesky")):
    wi, ws = B["ideology"]["within_platform"][plat], B["stance"]["within_platform"][plat]
    out.append(f"{name} & {wi['acc_at_100']:.1f} / {wi['acc_at_60']:.1f} / {wi['acc_at_20']:.1f} & {ws['acc_at_100']:.1f} / {ws['acc_at_60']:.1f} / {ws['acc_at_20']:.1f} " + r"\\")
out.append(r"""\bottomrule
\end{tabular}
\caption{Selective-prediction comparison at full context, pooled over models. Top: area under the risk--coverage curve (mean error rate over all coverage levels, lower is better; \citealp{elyaniv_foundations_2010}). Post-level bootstrap 95\% CI on the confidence-minus-platform difference: """ + f"$[{ci_i[0]:.1f}, {ci_i[1]:.1f}]$ ideology, $[{ci_s[0]:.1f}, {ci_s[1]:.1f}]$ stance" + r""". Middle: accuracy at the platform rule's coverage (""" + f"{B['ideology']['truthsocial_share']:.0f}\\%" + r"""). Bottom: confidence triage inside each platform.}
\label{tab:aurc}
\end{table}
""")

# ---------------------------------------------------------------- per-coder confidence agreement
D = O["D_per_coder_confidence"]
out.append(r"""\begin{table}[h]
\centering
\small
\setlength{\tabcolsep}{3pt}
\begin{tabular}{lcccc|cccc}
\toprule
 & \multicolumn{4}{c|}{Ideology $\rho$} & \multicolumn{4}{c}{Stance $\rho$} \\
Model & C1 & C2 & Mean & Rank & C1 & C2 & Mean & Rank \\
\midrule""")
for r in sorted(D["per_model"], key=lambda x: -x["rho_ideo_h"]):
    out.append(f"{r['model']} & {r['rho_ideo_q']:.2f} & {r['rho_ideo_x']:.2f} & {r['rho_ideo_h']:.2f} & {r['rho_ideo_rankmean']:.2f} & "
               f"{r['rho_stance_q']:.2f} & {r['rho_stance_x']:.2f} & {r['rho_stance_h']:.2f} & {r['rho_stance_rankmean']:.2f} " + r"\\")
out.append(r"""\bottomrule
\end{tabular}
\caption{Spearman correlation between each model's text-only confidence and human confidence under four references: coder 1 alone (mean """ + f"{D['coder_means']['qing'][0]:.0f}/{D['coder_means']['qing'][1]:.0f}" + r"""), coder 2 alone (mean """ + f"{D['coder_means']['xinyu'][0]:.0f}/{D['coder_means']['xinyu'][1]:.0f}" + r"""), their raw mean (as in Table~\ref{tab:conf_agree}), and the mean of within-coder percentile ranks, which removes the scale difference. Quadratic-weighted $\kappa_w$ against coder 1 / coder 2 for gpt-oss-120b: """ + f"{next(x for x in D['per_model'] if x['model']=='gpt-oss-120b')['kw_ideo_q']:.2f} / {next(x for x in D['per_model'] if x['model']=='gpt-oss-120b')['kw_ideo_x']:.2f}" + r""" (ideology). $n{=}""" + str(D["n"]) + r"""$ posts.}
\label{tab:conf_agree_coder}
\end{table}
""")

# ---------------------------------------------------------------- sample agreement
C = O["C_sample_agreement"]
if C:
    out.append(r"""\begin{table*}[t]
\centering
\small
\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{llc|cccc|cccc|cc}
\toprule
 & & & \multicolumn{4}{c|}{AUROC, verbalized / agreement} & \multicolumn{4}{c|}{AUROC, combined} & \multicolumn{2}{c}{Acc.\ at 60\% cov., full} \\
Model & Task & $k$ & T & T+B & T+B+C & Full & T & T+B & T+B+C & Full & Verb. & Agree. \\
\midrule""")
    for mod in MODELS:
        if mod not in C:
            continue
        r = C[mod]
        for task in ("ideology", "stance"):
            t = r[task]
            va = " & ".join(f"{t['auroc_by_condition'][v].get('verbalized', float('nan')):.2f} / {t['auroc_by_condition'][v].get('agreement', float('nan')):.2f}" for v in VARIANTS)
            cb = " & ".join(f"{t['auroc_by_condition'][v].get('combined', float('nan')):.2f}" for v in VARIANTS)
            cm = t["coverage_matched"]["T+B+C+M"]
            out.append(f"{mod if task=='ideology' else ''} & {task} & {r['k']} & {va} & {cb} & {cm['verbalized']['acc_at_60']:.1f} & {cm['agreement']['acc_at_60']:.1f} " + r"\\")
    out.append(r"""\bottomrule
\end{tabular}
\caption{Verbalized confidence vs.\ cross-sample agreement as reliability signals, on the gold subset re-decoded $k$ times (temperature 0.7). Signals: the first sample's verbalized confidence; the share of the other $k{-}1$ samples whose label agrees with the first sample's; and their rank average. AUROC is for the first sample's correctness, within condition. Right: accuracy among the 60\% of full-context cells ranked highest by each signal.}
\label{tab:agreement}
\end{table*}
""")

open("latex/tab_rebuttal.tex", "w").write("\n".join(out))
print("wrote latex/tab_rebuttal.tex;", len(C), "models in agreement table")
