# Response to Reviewers

**Paper:** *When to Trust an LLM Annotator: Self-Reported Confidence Ranks—but Overstates—Reliability in Political Stance and Ideology Labeling* (retitled; previously "…Self-Reported Confidence Predicts Reliability…")

We thank the panel for an unusually thorough review. The reviews converged on one decisive issue—the confidence→correctness analysis was pooled across context conditions—plus a set of major concerns about statistical inference, manuscript completeness, label-space consistency, positioning, and ethics reporting. We have rerun the analysis pipeline from the raw model outputs and human annotations, added the requested analyses, and rewritten the framing around the conditional claim the data support. Every number in the revised paper was recomputed from raw data for this revision (scripts `revision_analysis.py`, `revision_analysis2.py`, `revision_figures.py`, `seed_stability_check.py`, included in the release).

Below, **R** = reviewer comment, **A** = author response, **C** = change in the manuscript.

---

## 1. The decisive issue: within-condition confidence→correctness (EIC W7; R1-W1 CRITICAL; R3-W3; DA-1)

**R:** The confidence–accuracy bins pool across the four context conditions; since context raises both confidence and accuracy, the monotone curve could be entirely a between-condition artifact. No within-condition analysis exists. *(Unanimous; DA: "fatal for the triage claim as stated.")*

**A:** We agree this analysis was required, and we ran it. **The relationship survives conditioning on context.** Three independent tests:

1. **AUROC per model × condition × task** (no binning): confidence discriminates correct from incorrect predictions above chance in **62 of 64 cells** (exceptions: llama-3.1-8b and qwen3-4b, stance, T+B). Mean within-condition AUROC: 0.62–0.73 (ideology), 0.56–0.74 (stance).
2. **Logistic regression** of correctness on confidence with **condition and model fixed effects**, SEs clustered by post: OR = 1.73 per 10 confidence points for ideology (z = 12.0, p < .001, n = 7,990) and 1.40 for stance (z = 9.4, p < .001, n = 8,090). Per-model fits (confidence + condition FEs): coefficient positive in 16/16, significant in 15/16 (llama-3.1-8b stance p = .069).
3. **Within-condition reliability curves** (equal-mass bins, sizes shown): accuracy is monotone in confidence *inside* T alone and *inside* T+B+C+M alone, for both tasks.

Interesting structure the reviewers' question surfaced: discrimination is *weakest* at T+B—the condition where confidence inflates without accuracy gains—and strongest at the context extremes. This is now a finding, not a buried artifact.

**C:** New Section 5.4 ("Confidence Predicts Correctness *Within* Conditions") with Figure 2 (within-condition reliability curves), Appendix Figure 4 (per-model AUROC), Appendix Table 8 (mean AUROC by condition). The old pooled-bin table and figure (former Table 4/Figure 2, joint-correctness criterion, equal-width bins with cells resting on n = 1–36) are **removed**; abstract, intro, and conclusion now state the within-condition result as the central claim.

---

## 2. Gold labels constructed under full context (EIC W7; R1-W2 CRITICAL; R3-W4; DA-2)

**R:** Coders annotated the full-context variant, so low-context predictions are scored against labels defined with information they were denied; part of the context→accuracy gradient is built in. Also: how many posts lacked a majority, and what is the exact evaluation n?

**A:** Partially agree, and we now own this explicitly rather than implicitly. The gold standard is deliberately a *context-rich human reference interpretation*: the scientific question is whether a model can recover the contextually grounded reading from less information, which is precisely the deployment situation. A separate "text-only human truth" is not constructible for much of this data—our own coders report confidence of 16–40/100 when judging from text alone, which is evidence that text-only labels would largely be forced guesses (this was the original motivation for the confidence sub-study). We therefore (a) state the design choice and its two interpretive consequences in a dedicated paragraph, and (b) reframe low-context "accuracy" in the text as agreement-with-full-context-interpretation. Exact accounting, previously flagged `% VERIFY`, is now in the paper: majority exists for **289/295 (ideology)** and **291/295 (stance)**; 6 and 4 three-way splits are excluded; unanimity 196/289 and 203/291.

**C:** New paragraph "What the gold standard means" (§3.3); exact ns throughout; Limitations paragraph "Evaluation target."

---

## 3. The prompt and the "rubric-echoing / tautology" concern (EIC W2; R3-W2; DA-3)

**R:** The prompt instructs models that confidence = contextual sufficiency with numeric bands; "confidence rises with context" is then close to instructed behavior. Run a neutral-prompt ablation or reframe.

**A:** Here we must report an error that the review process uncovered, and we are grateful for it. In re-verifying the pipeline against the raw inference logs, we found that **the prompt shown in the original Appendix B was never the prompt used in the reported runs.** The appendix had been updated to a *planned* protocol revision (JSON output, confidence-as-sufficiency rubric) that was not the protocol behind the reported results. The actual prompt—now reproduced verbatim in Appendix B from the logged requests—requests confidence with **no definition, rubric, or bands whatsoever** ("Ideology Confidence: [0–100]%").

Consequences:
- The tautology concern is resolved *empirically*, not rhetorically: the context→confidence rise is **unprompted, emergent behavior**, which makes it more interesting, not less. The requested "neutral confidence prompt" ablation is, in effect, what was actually run.
- All text claiming confidence was "framed as contextual sufficiency" in the prompt was wrong and has been removed; "contextual sufficiency" now appears only as our *interpretation* of the observed behavior (Discussion), clearly separated from the elicitation protocol.
- We have re-verified every reported number against the raw logs in the course of this correction (all reproduce within rounding; the handful of corrected values are noted below).

We apologize for the discrepancy; it originated in maintaining the appendix from a config file that had moved ahead of the experiments.

**C:** §4.2 (Prompting Protocol) rewritten to describe the actual protocol and to state explicitly that no confidence rubric was given; Appendix B replaced with the verbatim template; abstract/intro/discussion language adjusted ("unprompted, self-reported confidence").

---

## 4. No statistical inference; tiny bins; pooling (EIC W6; R1-W3, W5, W8; DA-6)

**R:** No CIs or tests anywhere; lowest equal-width bins may hold a handful of items; pooling eight heterogeneous models invites Simpson-style distortion; promised majority-class baseline missing; binning scheme uncommitted.

**A:** All addressed:
- **Cluster bootstrap CIs** (2,000 replicates, resampling posts—the repeated unit) on every pooled accuracy and macro-F1 (Table 1 + appendix). The T→T+B ideology delta (53.6→56.7) indeed lies within overlapping CIs and is no longer described as a gain.
- **Equal-mass bins everywhere, with per-bin n printed**; the equal-width hedge is gone. The old low bins did rest on as few as n = 1–36 per model—those tables are removed.
- **AUROC** (binning-free) is now the primary discrimination statistic; ECE (10 equal-mass bins) and Brier per model in Appendix Table 7.
- **Majority-class baseline added** (ideology 65.4 acc / 26.4 F1; stance 58.8 / 24.7)—and it is informative: at T, pooled model accuracy (53.6) is *below* majority-class for ideology, which we now state plainly.
- **Per-model results** shown alongside every pooled claim (Figure 1; regression per model; AUROC per model). Pooled rows are summaries over visible heterogeneity, not substitutes for it.

**C:** §4.4 (Evaluation) rewritten; Table 1 with CIs and two baselines; Appendix Tables 7–8.

---

## 5. Decoding stochasticity (R1-W4; EIC Q6)

**R:** Single stochastic sample at temperature 0.7; a fixed seed makes the draw repeatable, not representative. Decode greedily or report cross-seed variance.

**A:** We re-decoded the full validation subset (295 posts × 4 conditions) with **three fresh seeds** at the original sampling settings for two models spanning our scale range (qwen3-4b; gemma-3-27b-it). At least one label flip across seeds occurs in 15.1%/14.1% (qwen3-4b, ideology/stance) and 2.5%/10.9% (gemma-3-27b-it) of post×condition cells; within-cell confidence SD is 2–3 points on average (median 0–2.6). This is meaningful but bounded noise: our headline effects (30-point accuracy ranges across conditions; ORs of 1.4–1.7 per 10 confidence points with |z| ≥ 9) are far larger than the jitter, and pooled estimates average over it. We report the flip rates in Limitations rather than re-running the full 8-model grid at multiple seeds (≈ 940k generations), which we hope the panel agrees is a reasonable cost–evidence trade-off.

**C:** Limitations ("Measurement"); §4.3 notes stochastic decoding and points to the stability check; `seed_stability_check.py` released.

---

## 6. Label space: "center" vs "neutral", folding, parse failures (EIC W5; R1-W6; R2-W1; DA observation)

**R:** Prompt elicits favor/against/neutral/undecided; evaluation uses favor/against/center. "Center" is an ideology word; the folded class mixes neutral stance, no stance, and abstention—and abstention is exactly the behavior the paper advocates. Parse failures (ministral-3-14b n≈160) unquantified; folding rule may manufacture effects (missing confidence imputed as 0 lands unparseable items in the lowest bin).

**A:** All correct. Changes:
- The stance class is renamed **none** throughout (favor/against/none), defined as covering neutral stance, no expressed stance, and non-commitment; "center" is reserved for ideology. The four-way elicitation and folding rule are stated in §3.2.
- **Non-committal response rates are now data, not noise**: Appendix Table 5 reports neutral/undecided usage per model × condition. It falls from up to 47% at T (gpt-oss-120b) to <4% at full context—we discuss this as a response-format component of the context effect (§5.1), exactly the abstention behavior the reviewer noted.
- **Extraction success rates per model × condition** are in the same table (ministral-3-14b is the outlier at 70–90%). Unparseable responses are **excluded, never imputed**—in particular, the prior pipeline's imputation of confidence 0 for unparseable responses (which seeded the old table's near-empty bottom bins) is gone. A sensitivity analysis (unparseable → none/center) appears in the appendix: it shifts pooled accuracy 2–4 points and changes no conclusion.

**C:** §3.2, §5.1, Appendix Table 5 + sensitivity paragraph.

---

## 7. Platform confound (R2-W3; DA alternative explanations)

**R:** Truth Social and Bluesky are near-homogeneous; the metadata gain may be platform-identity recovery; report per-platform distributions and accuracy, run a platform-masked ablation, report the promised baseline.

**A:** We computed everything computable from the existing runs, and the reviewer's hypothesis is substantially right—so we now feature it rather than bury it. A trivial **platform-prior rule** (Bluesky→left/against; Truth Social→right/favor) achieves 83.7%/72.2% accuracy—statistically indistinguishable from pooled full-context model accuracy (84.5%/68.9%)—though models beat it on macro-F1 (65.0 vs 57.0; 52.8 vs 49.6), i.e., on the minority classes the rule cannot get right. Per-platform accuracy at full context: 89.6% (TS) vs 69.6% (BS) for ideology. New §5.2 ("Platform Identity Is a Strong Confound") reports all of this and draws the deployment implication (expect Bluesky-column numbers on mixed platforms). Gold-set class × platform composition is in Appendix Table 6. A masked-metadata ablation requires re-running the full inference grid; we agree it is the right next experiment and say so, but note that platform identity is not hidden from the *human* coders either—the confound is partly constitutive of the task in segregated political spaces.

**C:** New §5.2; Table 1 baseline row; Appendix Table 6; Limitations ("Scope").

---

## 8. Title/abstract overclaim; 7/8 models overconfident (EIC W8; R3-W1; DA-4)

**R:** Title says "Confidence Predicts Reliability" while the paper's own tables show 7/8 models globally overconfident, high-confidence predictions wrong 27–75% of the time, llama's top bin at 34%; hedges live only in the Discussion.

**A:** Agreed. The title is now "…Self-Reported Confidence **Ranks—but Overstates—**Reliability…", and the abstract carries the limits in full ("wrong in 18–68% of cases"—the range recomputed per-task with the corrected pipeline; the old 27–75% came from the joint-correctness criterion we removed). The conditional claim (ranking signal after a per-model overconfidence check; calibrated-in-distribution for one model only) is the headline everywhere, and §6.3 turns the caveats into an explicit two-precondition usage protocol. The "monotonically related" abstract sentence is gone; the quantified within-condition statement (62/64 cells) replaces it.

**C:** Title, abstract, intro contribution 4, §5.5, §6.1, §6.3, Conclusion.

---

## 9. Novelty and missing literature (EIC W3; R2-W4, W5; DA-5)

**R:** Plank/Pavlick-&-Kwiatkowski/Aroyo-&-Welty (label variation), Joseph et al. 2017 ConStance, Xiong et al. (verbalized overconfidence), selective prediction (Kamath et al., Geifman & El-Yaniv), LLM-annotation validation (Ziems, Pangakis) missing; differentiate from Gligorić et al. and Kadavath.

**A:** All added and load-bearing, not decorative: §2.1 now grounds the ambiguity argument in the label-variation literature *and* we act on it—new §5.6 analyzes coder unanimity as an item-level ambiguity signal (see point 10). §2.3 credits Xiong et al. for the overconfidence-with-clustering finding our Table 2 independently replicates, and credits Kadavath et al. for confidence responding to in-context source material, stating precisely what we add (decomposed naturalistic context; human-confidence benchmark). New §2.4 frames the workflow as selective prediction, explicitly disclaims novelty for routing per se, and states our contribution as the two evidence conditions (survives conditioning on context; per-model overconfidence check) that make the workflow safe in this setting.

**C:** §2.1, §2.3, §2.4 (new); 9 references added.

---

## 10. The analysis sitting in our data (R2-Q4)

**R:** Does model confidence drop on items where the three coders split? This is the most direct test of your thesis available in your data.

**A:** Thank you—this is now Section 5.6. At full context, mean model confidence is 92.1 on unanimous vs 85.9 on 2–1 ideology posts (Mann–Whitney p < .001; stance 92.3 vs 89.5, p < .001), the gap holding in every condition; model accuracy on contested posts drops from 94.9% to 62.5% (ideology) and 77.7% to 47.9% (stance). LLM confidence encodes part of the same ambiguity humans perceive.

**C:** New §5.6 ("Confidence Tracks Human Disagreement").

---

## 11. Triage workflow asserted, never simulated (R3-W1)

**R:** Show a coverage–accuracy curve: keeping top-X% by confidence yields Y% agreement at Z% review cost.

**A:** Done—Table 3: within full context, top-60% coverage gives 91.3% (ideology) and 77.8% (stance) agreement vs 84.5%/68.5% at full coverage; within text-only, top-60% gives 66.8% ideology. It also shows the signal's ceiling honestly: no amount of selectivity lifts text-only stance much above 64%—under-determined input needs context, not selectivity.

**C:** New §5.7 + Table 3.

---

## 12. Manuscript completeness: VERIFY flags, ns, terminology (EIC W1, W4, W9; R2-W8; R3-W6)

**R:** `% VERIFY` comments on evaluation-set size, seed/FP8/code link, and IRB/annotator reporting; 295 vs 283 unexplained; "evaluation set" means two things; stray title space; missing figures-in-appendix bookkeeping.

**A:**
- **Evaluation set size:** resolved (289/291; see point 2). "Evaluation set" now refers only to the validated subset; the 7,408-post corpus is the "inference corpus" (§3.1, Appendix A).
- **295 vs 283:** explained—12 of the 295 gold posts have no text-only rendering (364 of 7,408 posts are media-only/empty after cleaning); the confidence sub-study covers the remaining 283 (§3.3).
- **Implementation details:** §4.3 now states decoding parameters (temp 0.7, top-p 0.9, 1024 max tokens), serving precision per model (FP8 for qwen3-80b-a3b; native MXFP4 for gpt-oss-120b), and extraction procedure; code/config/anonymized annotations released with camera-ready.
- **Annotators:** the Ethics section now describes the three coders (trained research-team members, no crowdworkers, regular research duties, support for exposure to hostile content). **The IRB/ethics-board determination is the one item we cannot truthfully complete without the authors' institutional records; it is marked as a pre-submission author action in the source and must be inserted before submission.** We agree with the panel that the paper should not be submitted without it.
- Stray space in §3.2 title fixed; every table/figure referenced in text now exists in main text or appendix; intercoder κ reported as exact ranges (0.49–0.69 ideology, 0.62–0.67 stance) instead of the previous rounded claim.

---

## 13. Points of respectful disagreement / acknowledged limitations

- **User-level ideology re-design (R2-W2, R3-W7):** We agree single-post user-ideology inference has construct-validity limits, now discussed (Limitations; §5.2 community-prior framing) along with the author-recurrence count the reviewer requested (285 unique authors / 295 posts; 8 authors with 2–3 posts). Redefining the task at user level with multi-post evidence is a different study; we scope-limit rather than retrofit.
- **Full factorial / reordered conditions (R1, EIC):** Acknowledged as designed-in; nested marginal effects in a fixed order are what we claim, no more (Limitations).
- **Human confidence at all conditions (R3-W5):** Human confidence was collected only at T; collecting it at full context is flagged as the natural next data collection. The two-coder base and their 2.4× scale-use difference are now stated where the sub-study is used, and the cross-condition claims are scoped to minimal context only.
- **gpt-oss-120b as n = 1 (DA):** Now explicit in Limitations: we cannot attribute its calibration to scale, architecture, or reasoning post-training.
- **Ideology–stance correlation (DA):** The joint-correctness metric is removed; the two tasks are analyzed strictly separately. Their correlation in this corpus is acknowledged in §5.2 (both partly recover the same community prior).

---

## Summary of major manuscript changes

| # | Change |
|---|--------|
| 1 | Retitled; abstract/intro/conclusion rebuilt around the conditional, within-condition claim |
| 2 | New §5.4: AUROC + fixed-effects regression + within-condition reliability curves (the decisive analysis) |
| 3 | New §5.2 (platform confound), §5.6 (coder disagreement), §5.7 (coverage–accuracy triage) |
| 4 | §2 repositioned (label variation; ConStance; Xiong; selective prediction; Gligorić delta) |
| 5 | Appendix B replaced with the verbatim run-time prompt; §4.2 corrected (no confidence rubric was given) |
| 6 | Cluster-bootstrap CIs, majority-class + platform-prior baselines, equal-mass bins with ns, ECE/Brier |
| 7 | Stance class renamed *none*; folding + extraction rates reported; no imputation of failures |
| 8 | All `% VERIFY` items resolved except IRB determination (explicit author action before submission) |
| 9 | Old pooled equal-width-bin tables/figures removed; figures regenerated from the verified pipeline |

---

## Addendum: second-round (verification re-review) fixes

The verification panel returned **Minor Revision / conditional accept** with a punch list; all items are now in the manuscript:

1. **Table 1 vs Table 3 denominators** — Table 3 caption now states it is computed over predictions with parsed labels *and* confidence scores (full-coverage values differ ≤0.4 pts from Table 1).
2. **llama-3.3-70b provenance** (found by the Devil's Advocate in old logs) — §4.3 now states: an earlier pilot run with a previous pipeline version included Llama-3.3-70B; it was not re-run under the final protocol and is excluded; reported results cover exactly the eight models run in full under the final pipeline.
3. **Platform control on the confidence signal** — §5.4: adding a platform fixed effect leaves the ORs essentially unchanged (1.71 / 1.39), and within-platform AUROC at full context exceeds 0.5 for all 8 models on both platforms and tasks (means 0.69–0.74). §5.2 cross-references this.
4. **Per-model triage curves** — new Appendix Table (per-model coverage–accuracy at full context); §5.7 notes the pooled curve is not a model-ranking artifact, and benchmarks triage against the "keep Truth Social" rival policy.
5. **Brier score** — added to the calibration table (was promised in §4.4 but missing).
6. **Tree-level dependence** — acknowledged in §4.4 with the headroom argument (|z| ≥ 9).
7. **OR confidence intervals** — added (ideology [1.58, 1.89]; stance [1.30, 1.50]).
8. **Masked-metadata ablation** — now committed to in the manuscript (§5.2), not only in this letter.
9. **"Under 4%" abstention claim** — corrected to "6% or less for every model"; equal-mass bin tie-heaping noted in the Figure 2 caption; Table 1 caption notes the T-row n=283 base; abstract "within every condition" softened to the quantified statement.
10. **IRB determination** — remains the single outstanding item; it requires the authors' institutional records and is marked as a mandatory pre-submission action in the source. The paper must not be submitted without it.
