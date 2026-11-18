# Change map: camera-ready against the reviewed ARR submission

Reviewed version: `review/arr-submitted/llm-context-arr.pdf` (ARR August 2026, Submission 2351, PDF
created 2026-08-03; kept out of git). No LaTeX source of that version survives (the first commit of
`latex/acl_latex.tex`, 2026-09-16, already carried the rebuttal-period revision), so the comparison
runs on text extracted from the two PDFs with `review/measure_change.py`.

Rule (Mao, 2026-11-15): a main-text change stays only if it answers a specific reviewer or
meta-review comment or corrects a factual error; everything else returns to the reviewed text.
Appendix changes are accepted as they are. Classes: (a) reviewer or meta-review comment, (b) factual
or numerical correction, (c) de-anonymization, acknowledgments, format, (d) none.

## Change share (main text = abstract through Limitations)

| Version | Main-text words | New or changed | Share |
|---|---|---|---|
| Camera-ready of 2026-11-13 (commit 17d9ae4) | 5,393 | 1,284 | 23.8% |
| After this pass, as measured | 5,290 | 472 | 8.9% |
| With the third coder's ratings (2026-11-15), as measured | 5,290 | 556 | 10.5% |
| With the third coder's ratings, hand count | 5,290 | about 380 | about 7% |
| After this pass, hand count of the changes listed below | 5,290 | about 300 | about 5.6% |

The measured figure counts every camera-ready sentence against its closest reviewed sentence. It
includes extraction noise from section headings, figure labels and table cells that pdftotext places
differently in the two PDFs (the review PDF has margin line numbers and different float positions);
the hand count sums the words of the changes in the table below. The third coder's ratings replace the numbers in one paragraph of 3.3, one of 5.5 and the 48 cells of Table 2, which is where the last step's increase comes from. Whole paper: the appendix grew by
four tables and one section (all class a), so a whole-paper share is dominated by the appendix and
is not the headline.

## What was reverted, class (d)

The rebuttal-period revision of 2026-09-16 tightened prose across the paper to make room for new
material under the eight-page limit. None of that answers a comment, and the camera-ready has a
ninth page, so the reviewed wording is restored in: Introduction (all five paragraphs and the four
contributions); Related Work 2.1 to 2.4, including the separate subsection heading "Selective
Prediction and Confidence-Aware Workflows"; Sections 3.1 to 3.3; 4.1, 4.2 and 4.4; the abstention
paragraph of 5.1; 5.2 (per-platform sentences, "We flag this openly", the metadata-masked ablation
as future work); 5.3; the lead paragraph, Regression and Reliability paragraphs of 5.4; 5.6; the
frame of 5.7; 6.1, 6.2, the frame of 6.3; Conclusion; the Design, Evaluation-target and Scope
sentences of Limitations. About 60 sentences return to their reviewed form.

Also reverted from the 2026-11-13 camera-ready step: the longer versions of the Bluesky paragraph,
of the per-condition calibration paragraph and of the coverage-matched comparison (trimmed, detail
left in appendix tables), and the sentence listing the full-context gaps in 6.1.

## Main-text changes kept

| # | Location | Reviewed text | Camera-ready text | Class and justification |
|---|---|---|---|---|
| 1 | Title block | Anonymous ACL submission | Mao Li and Xinyu Lin (University of Michigan), Shengteng Yang (The University of Texas Health Science Center at Houston), emails | (c) de-anonymization; Yang's affiliation follows her OpenReview profile and the EACL submission record (Mao, 2026-11-15) |
| 2 | Abstract | "overconfident in absolute terms---high-confidence predictions" | "overconfident in absolute terms in nearly every context condition---high-confidence predictions" | (a) h3ni W1: "Per-condition ECE and gap tables are needed"; meta-review 4: "rewrite the abstract ... to reflect that no model passes a per-condition overconfidence check" |
| 3 | 1, first paragraph | (Clark, 2005; ...) | (Clark, 1996; ...) | (b) Crossref gives 1996 for the book; bib only |
| 4 | 1, second paragraph; 2.1 | "(Mohammad et al., 2016; Li et al., 2021; Allaway and McKeown, 2020)" | "(e.g., for stance, Mohammad et al., 2016; ...)" | (b) the three works are stance benchmarks; the sentence also names ideology and sentiment |
| 5 | 1, second paragraph | "(Joseph et al., 2017; Allaway and McKeown, 2020; Niu et al., 2024)" | "(Joseph et al., 2017)" | (b) only Joseph et al. compare annotator labels with and without context (Mao approved dropping Niu et al. on 2026-11-13; Allaway and McKeown do not make that comparison either) |
| 6 | 1, fourth paragraph; 2.3 | "(Kadavath et al., 2022; Tian et al., 2023; Xiong et al., 2024)" and "(Kadavath et al., 2022; Tian et al., 2023)" | Kadavath et al. dropped from both groups; kept in "Kadavath et al. (2022) further showed ..." | (b) Kadavath et al. study P(True) and P(IK), not verbalized confidence |
| 7 | 2.1 | "with low agreement and frequent fallback to neutral categories (Allaway and McKeown, 2020)" | "with low agreement (Allaway and McKeown, 2020)" | (b) the paper reports alpha 0.427 and only 350 crowdsourced neutral labels |
| 8 | 2.2 | (DeVerna et al., 2025) | (DeVerna et al., 2026) | (b) now published in Findings of ACL 2026; bib only |
| 9 | 2.4, last sentences | "must be checked for global overconfidence per model. We provide both tests; one widely available model passes the second, seven do not." | "must be checked for overconfidence per model and condition." | (a) h3ni W2: the "only gpt-oss-120b passes" claim "is task-aggregated but the underlying evidence is task-specific"; h3ni follow-up: "no model passes a global overconfidence check at any condition" |
| 10 | 3.3 | "using the full-context (T+B+C+M) rendering"; "text-only (T) rendering" | "using the full-context rendering (Section 4.1)"; "text-only rendering" | (a) 24ts: "In 3.3, the acronyms ... are used before being defined. I would just remove them ... or refer to the later section." |
| 11 | 4.3 | "annotations with the camera-ready version." | "annotations at https://github.com/LiMaoUM/llm-context." | (c) the camera-ready is this version; 8FDE scored Datasets and Software 1 for nothing released |
| 12 | 4.4 | "gap per model." | "gap per model and condition." | (a) h3ni W1 |
| 13 | 5.1, new last sentence | none | "The gain is confined to one platform (Appendix Table 6): on Bluesky, stance accuracy is highest with no context (56.2%) and ends at 50.8% against a 50.6% majority class, and ideology at full context (69.6%) stays below its majority class (74.3%), as added context pulls predictions toward the community prior." | (a) 8FDE W1: "It is more than that, and it belongs in §5.1"; meta-review 2: "move the inverted Bluesky stance accuracy result from the appendix into Section 5.1" |
| 14 | 5.4, Discrimination | "Confidence is most discriminative at the extremes of the context spectrum (T and full context) and weakest just after the background brief is added---the condition where confidence inflates without accuracy gains." | "Confidence is most discriminative at full context and weakest in the middle conditions: at T+B for stance (0.56) and at T+B+C for ideology (0.62)." | (a) and (b) h3ni W2: "For ideology it does not: T+B+C is ... below T+B"; meta-review 4 |
| 15 | 5.5, heading | "Absolute Calibration: All Models Overconfident, One Exception Usable" | "Absolute Calibration: All Models Overconfident" | (a) meta-review 4; h3ni follow-up ("a uniform negative"); Mao's decision of 2026-11-13 |
| 16 | 5.5, first paragraph | "Pooled over conditions, mean confidence exceeds accuracy for every model on both tasks: the gap ranges from 4.9 points (gemma-3-27b-it, ideology) to 55.7 (llama-3.1-8b, stance), with ECE between 0.06 and 0.56 (Appendix Table 7)." | "Per condition (Appendix Table 10), mean confidence exceeds accuracy in 62 of 64 model x condition x task cells, with the largest gaps at T+B (25 points for ideology and 39 for stance, pooled over models) and the smallest at full context (6 and 23); pooling over conditions hides this (gemma-3-27b-it's pooled ideology gap of 4.9 spans 13.6 at T+B to -1.9 at full context; Appendix Table 7)." The two following sentences are as reviewed. | (a) h3ni W1: "The absolute-calibration analysis pools over conditions, which is the exact move the paper argues against"; meta-review 2 |
| 17 | Contribution (2); 3.3 sub-study; 5.5 human comparison; Table 2; 6.2; Limitations | two coders: means 39 and 16 (ideology), 40 and 15 (stance); Spearman 0.68 / 0.66; kappa_w 0.54 / 0.55; unweighted kappa 0.28 / 0.34. Table 2 against the mean of two; gpt-oss-120b kappa_w 0.57 / 0.56, rho 0.82 / 0.77; other models kappa_w at most 0.30; human mean near 28; "coder confidence means of 16-40"; "covers two coders and the text-only condition" | three coders: means 39, 16 and 20; 40, 15 and 13; pairwise Spearman 0.68-0.80 / 0.66-0.78; kappa_w 0.54-0.72 / 0.40-0.70; unweighted kappa 0.28-0.49 / 0.23-0.45. Table 2 against the mean of three (n=158-281); gpt-oss-120b kappa_w 0.60 / 0.47, rho 0.85 / 0.77; other models at most 0.26; human mean near 25; "13-40"; "covers the text-only condition"; one added sentence: "It also leads against each coder separately (Appendix Table 12)." | (a) 8FDE W3: "A third coder was already recruited for the label task"; meta-review 3: "Expand the human confidence comparison to include the third coder"; promised in our reply and final response. Ratings received 2026-11-15 (`data/manual/conf_manual_qing.csv`), recomputed with `third_coder/recompute_table2.py` |
| 18 | 5.7 | "Confidence-based selection also compares favorably with the crude rival policy of keeping only Truth Social labels (89.6% ideology agreement at 74% coverage, vs. 91.3% at 60%)---and unlike that policy it works within each platform." | "Against the crude rival policy of keeping only Truth Social labels, confidence-based selection ties at matched coverage (89.8% vs. 89.5% ideology agreement at 75%) and has the lower area under the risk-coverage curve of El-Yaniv and Wiener (2010) (9.0 vs. 11.5; Appendix Table 11)---and unlike that policy it works within each platform." | (a) and (b) h3ni W3: "Those are different coverage levels ... A risk-coverage curve with area under it (El-Yaniv and Wiener, 2010) would let both policies be compared on one frontier" |
| 19 | 6.1 | "overstates accuracy for every model, often grossly (§5.5)" | "overstates accuracy for every model (§5.5)" | (a) h3ni follow-up: "A 6-point ideology gap at full context is not 'often grossly'" |
| 20 | 6.3, step 1 | "check global overconfidence first---compare mean confidence to accuracy on a small validated sample (and, where possible, distributional alignment as in Table 2); in our pool only gpt-oss-120b passes" | "check overconfidence first, under the context condition to be deployed---compare ... (and, where possible, distributional alignment as in Table 2); none of our eight models passes the first check in every condition, and only gpt-oss-120b passes the second" | (a) h3ni W1: "the paper has not shown that a pooled check detects condition-level overconfidence"; h3ni W2; meta-review 4 |
| 21 | 7 | "after a per-model overconfidence check" | "after a per-model, per-condition overconfidence check" | (a) meta-review 4 |
| 22 | Limitations, Measurement | "Decoding is stochastic (temperature 0.7, single sample per cell); a three-seed ..." | "... single sample per cell), the setting under which these models are typically deployed for annotation; a three-seed ..." | (a) 24ts W3: "I cannot understand why the authors chose a temperature of 0.7 ... I would appreciate a more detailed discussion" |
| 23 | Limitations, Measurement | none | "Agreement across repeated samples is a rival signal: over ten re-decodings, a single verbalized score discriminates at least as well in 14 of 16 model x task pairs (Appendix D)." | (a) 8FDE W2: "The paper never compares verbalized confidence against a rival confidence signal"; 24ts W2 |
| 24 | Limitations, Scope | none | "on a less polarized platform, accuracy should be expected to resemble our Bluesky column;" | (a) 24ts W1; promised for Limitations in our reply; arguable, see below |
| 25 | Limitations, Scope | "The one well-calibrated model (gpt-oss-120b) ... cannot attribute its calibration" | "The one model whose confidence aligns with human uncertainty (gpt-oss-120b) ... cannot attribute that alignment" | (a) h3ni W2: on ideology gemma-3-27b-it is better calibrated |
| 26 | Ethical Considerations | "performed by three of the authors, who have experience in political content analysis, as part of their regular research duties" | "performed by two of the authors and one research collaborator, all with experience in political content analysis" | (b) and (c) the third label coder is not an author |
| 27 | Acknowledgments | none | "We thank Qing Ren for annotating the validation set." | (c) |
| 28 | References | see `review/reference-check.csv` | bib corrections only | (b) |
| 29 | Figures 1 and 2 | width 0.46 of the page width (as in the reviewed PDF) | width 0.9 of the page width; images and captions unchanged | (c) format; Mao's decision of 2026-11-17, the legends were too small to read. Body now ends on page 9 of 9 |

Counts: class (a) 17, class (b) 8 (two shared with a), class (c) 4, class (d) 0 remaining.

## Appendix (accepted as is)

Per-condition calibration table (h3ni W1), AURC table (h3ni W3; the 8.9 for confidence on ideology
is corrected to 9.0, the value is 8.95), per-coder agreement table (8FDE W3), Appendix D with the
cross-sample agreement table (8FDE W2, 24ts W2), corrected captions of Tables 7 and 8 (h3ni W2).

## Arguable links, for Mao

- #17: resolved on 2026-11-15, the third coder's ratings are in. The earlier Table 2 numbers came
  from `revision_analysis.py`, which matched coders on identifiers that lose precision in the CSV
  exports; `third_coder/recompute_table2.py` aligns the exports by row, so a few two-coder values
  would also have moved by 0.01 to 0.02.
- #24: Section 5.2, restored to its reviewed form, already says mixed platforms should expect
  numbers "closer to our Bluesky column"; the Limitations clause repeats it because our reply to
  24ts promised it there.
- #9: the fix deletes a reviewed sentence instead of rewording it.
- #20: the longest protocol change; a shorter form would drop "none of our eight models passes the
  first check in every condition".
