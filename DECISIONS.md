# Decisions (llm-context)

## 2026-09-19: ARR 2351 rebuttal is a text-only response, promises the third coder's confidence ratings, and stays silent on supplementary scores

Send a text-only author response to ARR Submission 2351 without uploading a revised PDF, so every key number is stated in the response and table references keep the submitted numbering. Promise that the camera-ready adds the third coder's text-only confidence ratings and recomputes the human-alignment table (Table 2). Do not discuss the Datasets/Software scores (nothing was attached at submission); only restate the release plan. (Mao, via /decide)

Rationale: Mao's decisions on 2026-09-19 after three reviews at Findings 3; the third-coder promise is the one item most likely to move 8FDE's soundness score, and a self-contained text response keeps reviewers from needing the PDF.

## 2026-11-13: accepted at EACL 2027

The EACL 2027 ARR commitment decision is Accept (OpenReview, seen by Mao 2026-11-13; no email yet). The decision line does not say main conference or Findings; confirm before the camera-ready. Map, CV and website updated the same day. (Mao)

## 2026-11-13: EACL 2027 camera-ready (Main Conference, Submission 354): scope, authors, release, citations

Decision email 2026-11-13 confirms Main Conference; the decision note carries no SAC comment. Camera-ready due 2026-11-26 AoE; Mao submits. Mao's decisions, each through AskUserQuestion on 2026-11-13:

1. Scope: change only what was promised during ARR, plus de-anonymization and acknowledgments. From the meta-review's item 4 and Reviewer h3ni's follow-up, two small edits only: Section 5.5 is retitled "Absolute Calibration: All Models Overconfident", and protocol step 1 says none of the eight models passes the overconfidence check in every condition. No rewrite of abstract or conclusion and no mechanism for the AUROC dip (no analysis supports one).
2. Third coder (promise to Reviewer 8FDE): Mao gets the rating sheet `data/third_coder/rating_sheet_T.xlsx` filled before 2026-11-26; then `third_coder/recompute_table2.py` recomputes Table 2. Open until the sheet returns.
3. Authors: Mao Li, Xinyu Lin, Shengteng Yang (University of Michigan). The third label coder, Qing Ren, is thanked in Acknowledgments; the ethics statement says two of the authors and one research collaborator annotated.
4. Release: the paper links https://github.com/LiMaoUM/llm-context. `curated-evidence` is merged into main without the two `seed_stability_*.jsonl` files (raw post ids); `release/validation_annotations.csv` carries labels and confidence keyed to salted hashes. The simulated-review response letter, the checklist draft and the downloaded OpenReview notes (`review/arr`, `review/eacl`) stay local.
5. Citations: the Allaway and McKeown sentence is rewritten to what the paper reports (Krippendorff's alpha 0.43); Niu et al. is dropped from the Introduction sentence about annotator judgments shifting (kept in Related Work); El-Yaniv and Wiener is cited for the risk-coverage curve, with the area described in our words.

Rationale: Mao wants small changes; EACL desk-rejects papers with unverifiable or inaccurate references, so every cited entry went through two independent passes (`review/reference-check.csv`, agent room thread 2026-11-13-camera-ready-references), with Mao's own pass still to come.

## 2026-11-13: third reference pass and the minimal-change rule for citations

Mao changed the third pass (2026-11-13): Claude re-checks every high and medium entry against re-fetched records and settles what a source can settle; Mao answers only what no source settles. His minimal-change rule: a citing sentence keeps its claim; fixes are narrowing, dropping one citation, or deleting. Result, recorded per key in `review/reference-check.csv` (column `third_pass`):

- All bib fields match the re-fetched records. Bib-only fixes in this pass: Kadavath et al. now prints its arXiv number; El-Yaniv and Wiener's title keeps its capitals.
- Citing sentences, final state against the submitted version: (a) Allaway and McKeown: "and frequent fallback to neutral categories" removed, rest of the clause as submitted (this supersedes item 5 of the earlier entry, which rewrote the clause); (b) Niu et al. dropped from the Introduction sentence on annotator judgments; (c) "risk--coverage curve of" El-Yaniv and Wiener, in text and table caption; (d) "e.g., for stance," added inside the two citations of the three stance benchmarks; (e) Kadavath et al. dropped from the two citation groups about verbalized confidence, kept for self-evaluation with source material.
- Mao's answers (AskUserQuestion, 2026-11-13): keep Stalnaker (2002), confirmed by him as author since the text is paywalled; cite the Llama 3 and Qwen3 reports by their title-page group authors.
- Author names where the paper PDF and the ACL Anthology record differ by a middle initial (Manning, Candes) follow the Anthology .bib.
- Mao's read of the final reference list (`review/reference-list-rendered.txt`): pending; he asked to see the list in the conversation.
