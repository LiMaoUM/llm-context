# ARR Submission 2351: Revision Roadmap and Author Response

Source reviews: `2026-09-arr-submission2351-reviews.md`. Revised manuscript: `latex/acl_latex.tex`
at commit 72a08df and later. New numbers: `rebuttal_analysis_output.json` (script
`rebuttal_analysis.py`); new appendix tables: `latex/tab_rebuttal.tex` (script `rebuttal_tables.py`).

The eight-model, ten-seed re-decoding run (`sample_agreement_run.py`, vLLM 0.13.0, outputs in
`sample_agreement/`) is complete; every number below is in the manuscript.

## Part 1: Revision Roadmap

### Overview

- Decision context: three reviews, all Overall 3 (Findings). Soundness 4 / 3 / 3.5.
- Comments parsed: 13 (5 Major, 4 Minor, 1 Editorial, 3 Positive blocks).
- Cross-reviewer pattern: stochastic decoding at temperature 0.7 with one sample per cell is raised
  by all three reviewers (24ts W3 asks why; 8FDE W2 and 24ts W2 ask for cross-sample agreement as a
  rival signal or as a predictor of human difficulty). One experiment answers all three.

### P1: Must fix

| # | Comment | Reviewer | Type | Section | Action | Status |
|---|---|---|---|---|---|---|
| 1 | Absolute calibration is pooled over conditions, the move the paper argues against elsewhere; per-condition ECE and gap tables needed; protocol step 1 has not been shown to detect condition-level overconfidence | h3ni W1 | Major | 5.5, 6.3, App. | Per-condition gap/ECE table for 8 models x 4 conditions x 2 tasks (Table `tab:calibration_cond`); rewrite 5.5 around per-condition values; protocol step 1 now says to check in the deployed condition | Done |
| 2 | Table 8 caption and 5.4 say discrimination is weakest at T+B; true for stance, false for ideology (T+B+C is the minimum) | h3ni W2a | Major | 5.4, Table 8 | Task-specific wording; mechanism claim attached to T+B removed | Done |
| 3 | Table 7 caption says gpt-oss-120b least overconfident; on ideology gemma-3-27b-it is better on gap, ECE, and confidently-wrong rate; the "only gpt-oss passes" claim is task-aggregated | h3ni W2b | Major | 5.5, Table 7, abstract, 6.3, conclusion | Least-overconfident model stated per task; the "only gpt-oss-120b passes" claim now refers only to alignment with human confidence (Table 2), where it holds; abstract and conclusion qualified | Done |
| 4 | Triage advantage over the platform rule does not survive coverage matching; risk-coverage curve and AURC requested | h3ni W3 | Major | 5.7, App. | Matched-coverage comparison reported honestly (tie at 75 percent); AURC over the full frontier with post-level bootstrap CI (Table `tab:aurc`); within-platform triage numbers carry the argument | Done |
| 5 | Bluesky stance is at chance under every condition and highest at text-only; belongs in 5.1, not an appendix | 8FDE W1 | Major | 5.1, 5.2 | New paragraph in 5.1 with majority baselines, the T to full trajectory, and the predicted-label collapse toward the community prior; 5.2 shortened to avoid repetition | Done |
| 6 | No comparison of verbalized confidence against cross-sample agreement | 8FDE W2, 24ts W2 | Major | Limitations, new App. | Re-decode the gold subset k times for every model; AUROC, coverage-matched accuracy, and combination for the three signals (Table `tab:agreement`, Appendix `app:agreement`) | Done (k=10, eight models) |

### P2: Should fix

| # | Comment | Reviewer | Type | Section | Action | Status |
|---|---|---|---|---|---|---|
| 7 | Human confidence reference rests on two coders whose scale use differs by 2.5x; unweighted kappa 0.28 / 0.34 | 8FDE W3 | Minor | 3.3, 5.5, App. | Model-versus-coder agreement recomputed against each coder separately and against a scale-free rank consensus (Table `tab:conf_agree_coder`); ordering unchanged | Done |
| 8 | Why temperature 0.7; it adds a stochastic component | 24ts W3 | Minor | 4.2, Limitations | Rationale added (deployment setting; the confidence studied is the one practitioners see); three-seed stability bound retained; cross-sample comparison turns the concern into a measured quantity | Done |
| 9 | Use human agreement more, e.g. predict hard-for-humans cases from class-flip probability under repeated prompting | 24ts W2 | Minor | App. `app:agreement` | Flip rate on split versus unanimous posts, and AUROC of agreement and of verbalized confidence for coder unanimity | Done |
| 10 | Data from a less biased platform | 24ts W1 | Minor | Limitations | Out of scope for this cycle; acknowledged in the response and in Limitations (Scope) | Response only |

### P3: Editorial

| # | Comment | Reviewer | Section | Action | Status |
|---|---|---|---|---|---|
| 11 | Acronyms T, T+B+C+M used in 3.3 before definition | 24ts | 3.3 | Acronyms removed; forward reference to 4.1 | Done |

### Positive comments to acknowledge

| Reviewer | Point |
|---|---|
| 24ts | Well written; dataset of conversation trees; human annotation with confidence; highlights 5.3, 5.5, 5.7 |
| 8FDE | T+B as an accidental placebo isolating confidence inflation from information gain; Table 9 per-model coverage check; specific Limitations section |
| h3ni | Within-condition conditioning as the correct and non-obvious control, backed by three converging analyses; paper reports what works against it; coder-unanimity link to human label variation |

### Open item for the authors

8FDE scored Datasets 1 and Software 1; 24ts and h3ni scored both 3 to 4. Check what the submission package contained. If code and annotations were attached, say so in the response; if not, state the release plan.

### Revision order (all applied; commits 72a08df through the current HEAD)

1. h3ni factual corrections (items 2, 3) and the per-condition calibration table (item 1).
2. AURC comparison and within-platform triage (item 4).
3. Bluesky paragraph in 5.1 (item 5).
4. Per-coder agreement (item 7), temperature rationale (item 8), acronyms (item 11).
5. Sample-agreement appendix from the eight-model, ten-seed run (items 6, 9).
6. Trim introduction, related work, and discussion so the body ends on page 8.

## Part 2: Author Response (ARR format)

### General response

We thank the three reviewers for careful readings. Every factual claim in the reviews checked out
against our tables, and we have corrected each one. The revised manuscript adds four appendix
tables and one appendix section, all computed from the same run that produced the submitted
results, and one new experiment (re-decoding every gold cell ten times for every model) that
answers the question raised by all three reviewers about stochastic decoding. The body still ends
on page 8; the additions live in the appendix, and the introduction and related work were
tightened to make room for the new paragraph in Section 5.1.

### Reviewer h3ni

**W1 (pooled calibration).** Agreed. Absolute calibration is now assessed per condition
(Appendix Table `tab:calibration_cond`: gap and ECE for 8 models x 4 conditions x 2 tasks), and
Section 5.5 is rewritten around those values. Mean confidence exceeds accuracy in 62 of 64 cells;
the two exceptions are gemma-3-27b-it and gpt-oss-120b on ideology at full context (1 to 2 points
under-confident). The pooled gap does understate the problem exactly as you describe:
gemma-3-27b-it's pooled ideology gap of 4.9 averages 13.6 at T+B with minus 1.9 at full context.
Protocol step 1 (Section 6.3) now instructs practitioners to check overconfidence in the context
condition they will deploy, and says why a pooled check is insufficient.

**W2 (Table 8 and Table 7 captions).** Both corrected. Section 5.4 and the Table 8 caption now
state that the minimum is T+B for stance (0.56) and T+B+C for ideology (0.62, with T+B at 0.63),
and we no longer attach a mechanism to T+B specifically. The Table 7 caption and Section 5.5 now
name gemma-3-27b-it as least overconfident on ideology and gpt-oss-120b on stance. The claim that
only gpt-oss-120b "passes" is restricted, in the abstract, Section 5.5, Section 6.3, and the
conclusion, to the check it actually concerns: alignment of the confidence distribution with human
confidence (Table 2), where gpt-oss-120b is the only model within the coder-coder ceiling.

**W3 (coverage matching).** Agreed, and the original sentence was misleading. At the platform
rule's own coverage (75 percent) confidence selection ties it (89.8 vs 89.5 ideology; 74.8 vs 74.9
stance). Section 5.7 now reports this, and compares the two policies on the full frontier as you
suggest: AURC (mean error over all coverage levels, El-Yaniv and Wiener 2010) is 9.0 for
confidence against 11.5 for the platform rule on ideology (post-level bootstrap 95 percent CI on
the difference [minus 4.7, minus 0.6]) and 18.8 against 26.8 on stance ([minus 10.9, minus 4.7]);
ranking by platform and then by confidence within platform gives 8.1 and 18.2 (Appendix Table
`tab:aurc`). The within-platform argument now carries the comparison: keeping the top 60 percent
raises full-context ideology agreement from 89.5 to 93.2 on Truth Social and from 69.7 to 77.1 on
Bluesky, and within-platform AUROC exceeds 0.5 for every model on both platforms.

### Reviewer 8FDE

**W1 (Bluesky stance at chance).** Agreed, and it is now in Section 5.1 under its own heading.
On Bluesky, stance accuracy is highest with no context (56.2), falls when the brief is added
(46.1), and ends at 50.8 against a 50.6 majority class; ideology at full context (69.6) is also
below its majority class (74.3). The paragraph reports the mechanism: as context accumulates, the
share of Bluesky stance predictions reading "against" climbs from 52 to 82 percent while the gold
set is split almost evenly between "against" and "none", so context pulls models toward the
community prior, which is right on Truth Social and half right on Bluesky. Section 5.2 now
builds on this paragraph instead of restating the platform difference as a difference in level.

**W2 (rival signal: cross-sample agreement).** This was the most useful comment we received, and
we ran the experiment. We re-decoded every gold cell (295 posts x 4 conditions, identical prompts)
ten times for every model at temperature 0.7 and compared, within condition, three signals for
the first sample's correctness: its verbalized confidence, the share of the other nine samples
agreeing with its label, and their rank average (Appendix `app:agreement`, Table `tab:agreement`).
Verbalized confidence is at least as discriminative as agreement in 44 of 64 model x condition x
task cells and in 14 of 16 model x task pairs pooled over conditions. The exception is
llama-3.1-8b on ideology, where agreement reaches AUROC 0.80 against 0.59 for verbalized
confidence at full context. The pattern has a simple explanation: agreement carries information
only when the model flips, and the share of cells where all ten samples agree runs from 48 percent
(llama-3.1-8b) to 95 percent (gemma-3-27b-it); the gap between the two signals tracks that share
(Spearman 0.58 over the 16 pairs). The two signals are complementary: their rank average matches
or exceeds verbalized confidence in 56 of 64 cells and adds 0.05 or more AUROC in 21, up to 0.22
for llama-3.1-8b. At the deployment operating point (top 60 percent of full-context cells),
verbalized confidence beats agreement for 13 of 16 pairs and the combination is best or tied in 15;
majority voting over ten samples moves accuracy by at most 3 points. So verbalized confidence
does beat the rival a practitioner would reach for first, for every model but the least stable
one, and the appendix gives the practitioner a criterion (flip rate on a small validated sample)
for when extra samples are worth paying for.

**W3 (two-coder confidence reference).** We agree the reference is thin and now show what it
can and cannot carry. Appendix Table `tab:conf_agree_coder` repeats the model-versus-human
comparison against each coder separately and against a scale-free consensus (mean of within-coder
percentile ranks). The model ordering is identical under every reference; gpt-oss-120b leads
against both coders on both tasks (Spearman 0.82 and 0.66 for ideology; quadratic-weighted kappa
0.71 and 0.43), and the rank-based consensus reproduces Table 2's correlations to two decimals.
The third coder did not rate confidence; the Limitations section already states that the
confidence comparison speaks to two coders and the text-only condition only. [AUTHORS: decide
whether to state a plan to collect the third coder's confidence ratings for the camera-ready.]

### Reviewer 24ts

**W1 (a less biased platform).** We agree this would strengthen the conclusions and it is outside
what we can add in this cycle. The revised Section 5.1 now makes the Bluesky result, our closest
approximation to a mixed platform, a headline finding rather than an appendix entry, and the
Limitations (Scope) paragraph states that headline numbers on mixed platforms should be expected
to sit near the Bluesky column.

**W2 (use human agreement more; predict hard cases from class-flip probability).** Done as part of
the re-decoding experiment (Appendix `app:agreement`). Across ten samples per cell, the flip rate
is higher on posts where coders split 2 to 1 than on unanimous posts for 15 of 16 model x task
pairs, typically by a factor of two to six (llama-3.1-8b ideology 44 vs 13 percent; qwen3-4b
29 vs 5 percent), so flip probability does flag hard-for-humans items. Verbalized confidence
flags the same items more sharply (higher AUROC for coder unanimity in 15 of 16 pairs), which is
consistent with Section 5.6.

**W3 (temperature 0.7).** The Limitations section now gives the rationale: temperature 0.7 with
top-p 0.9 is the setting under which these models are typically deployed for annotation, and the
paper's question is whether the confidence a practitioner actually sees is usable, so we kept the
deployment setting and measured the noise it introduces rather than removing it. The three-seed
check bounds that noise (label flips in 2.5 to 15.1 percent of cells, confidence SD 2 to 3 points),
and the new cross-sample experiment uses the same stochasticity as a rival signal.

**Editorial (acronyms in 3.3).** Fixed; Section 3.3 now says "the full-context rendering" and
"the text-only rendering" with a forward reference to Section 4.1.

### Note on Datasets and Software scores

[AUTHORS: 8FDE scored Datasets 1 / Software 1; the other two reviewers scored 3 to 4. Confirm
what the submission package contained and state it here in one sentence.]
