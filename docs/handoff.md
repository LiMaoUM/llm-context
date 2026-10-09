
## 2026-10-09 (llm-context-23, on the delegation menu P3; nothing needs Mao to proceed except the items marked DECIDE)

Done without you:

- P3.1 numbers. Every number quoted in `docs/reviews/2026-09-arr-response-final.md` and in the
  paper's new text (Sections 5.1, 5.5, 5.7, Limitations, Appendix tables and the agreement
  appendix) was recomputed from `rebuttal_analysis_output.json`, which in turn reads
  `sample_agreement/*.jsonl` (8 models x 10 seeds) and `results/20260115_215043`. All match. One
  wording was imprecise: "for seven of eight models" (posted in R1.3 and in Limitations) is exactly
  "14 of 16 model x task pairs"; the two pairs where agreement leads are llama-3.1-8b ideology
  (0.73 vs 0.62) and ministral-3-8b ideology (0.674 vs 0.661). The tex and the archived response
  now say 14 of 16; the posted comment cannot be edited and the difference does not change the
  claim. ACL format: compiles clean under `\usepackage[review]{acl}`, 16 pages, body ends on page
  8 with Limitations starting there, no placeholders left in the tex or in
  `latex/responsible_nlp_checklist.md`. Five overfull-hbox warnings come from the verbatim prompt
  in Appendix B (long lines in the prompt itself); harmless, fix with a smaller verbatim font if
  the camera-ready editor complains.
- P3.2 third-coder kit in `third_coder/`: `make_rating_sheet.py` wrote
  `data/third_coder/rating_sheet_T.xlsx` (283 posts, 207 Truth Social and 76 Bluesky, same row
  order as the other two coders, instructions on a second sheet; post text, so it stays out of
  git); `recompute_table2.py` recomputes Table 2 against three coders and reproduces the submitted
  Table 2 exactly in its two-coder fallback (gpt-oss-120b 46.9 / 0.82 / 0.57 and 45.6 / 0.77 /
  0.56). Send the sheet to the coder, drop the filled file at the same path, run the script.
- P3.3 curated commits exist on a local branch `curated-evidence` (worktree under the session
  scratchpad, not pushed, main untouched), four commits: gitignore for logs, results, LaTeX build
  output, root figures and notebooks; the pipeline source as it ran for the paper (plus removal of
  four stale planning notes); the R&R analysis scripts and outputs including the 3-seed stability
  files; the ACL style files and the four paper figures. Secret scan on everything staged: only
  environment-variable references, no keys.

DECIDE (the repo is public):

1. Merge `curated-evidence` into main or not. Flag inside it: the two `seed_stability_*.jsonl`
   files key model outputs to raw post ids (Bluesky at:// URIs and Truth Social numeric ids). The
   paper promises annotations keyed to hashed ids; either hash the ids before merging or drop the
   two files from the branch. Everything else on the branch is code, figures, or aggregate JSON.
   The branch lives in `.git` and survives if the scratchpad worktree is cleaned (`git worktree
   prune` then `git checkout curated-evidence`, or `git merge curated-evidence` from main).
2. What stays out for good: `results/` (8.4 GB of prompts and responses, with post text),
   `data/` (coder sheets with post text, already ignored), `intercoder_reliability.ipynb` (13 MB),
   `experiment*.log`, `nohup.out`, the eleven scratch markdown notes at the root (QUICK_*,
   VALIDATION_*, UPDATE_SUMMARY, PROJECT_FILES, VLLM_BATCH_INFERENCE, BUG_FIX_*), and the two
   4 MB exploratory figures. The branch's gitignore keeps them out; deleting the scratch notes is
   your call.
3. EACL commitment by 2026-10-11 or ARR October; saving the meta-review in the repo; the third
   coder.

Left as is: the posted ARR replies (three comments, under 2,000 characters each, no general
comment).
