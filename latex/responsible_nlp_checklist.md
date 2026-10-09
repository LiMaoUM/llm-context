# Responsible NLP Research Checklist — draft answers
(For ARR/EACL OpenReview submission. `[VERIFY]` = you must confirm/fill before submitting.)

## A. General
- **A1. Limitations discussed?** Yes — unnumbered **Limitations** section (nested-only design; researcher-authored background; verbalized vs. probabilistic confidence; temperature 0.7 stochasticity; two platforms / English / one-month window; human-confidence sub-study is text-only and two coders).
- **A2. Potential risks discussed?** Yes — **Ethical Considerations**: dual-use of inferring political ideology/stance of identifiable accounts; mitigations (public data only, no private accounts, IDs only for thread reconstruction, aggregate-only reporting, no release of identity-linked labels).
- **A3. Abstract/intro state claims accurately?** Yes.
- **A4. Did you use AI assistants?** **Yes — disclose.** AI assistant (Claude) used for data-analysis scripting, LaTeX editing, and prose tightening; all results were author-verified against the data. (Put this in an AI-disclosure note if the venue requires one.)

## B. Scientific artifacts
- **B1. Cite creators of artifacts you use?** Models: Gemma-3, Llama-3.1, Qwen3, GPT-OSS, Ministral — **[VERIFY: add citations/model cards for each in the bib]**. Serving: vLLM. Data: collected by the authors from Truth Social & Bluesky public APIs.
- **B2. License / terms of use?** **[VERIFY]** State each model's license (open-weight; e.g., Gemma/Llama community licenses, Apache-2.0 for Qwen/Mistral where applicable) and that data collection complied with each platform's Terms of Service / API terms. State the license you release code/data under.
- **B3. Intended use consistent with terms?** Yes — research use; consistent with open-weight model licenses and public-API access.
- **B4. PII / offensive content?** Data are public political posts and may contain offensive content; we infer sensitive attributes (political ideology/stance). We do **not** release identity-linked labels; identifiers used only to reconstruct reply structure and de-duplicate (Appendix A). **[VERIFY: confirm no usernames/handles or raw PII appear in any released artifact.]**
- **B5. Documentation (domains, languages, demographics)?** English-language US political discourse, two platforms, May 30–Jun 30 2024 window; documented in §3 and Appendix A.
- **B6. Relevant statistics?** 7,408 posts in ~100 conversation trees (inference corpus; 364 posts have no text-only rendering); 295 validated posts from 285 authors (majority gold: 289 ideology / 291 stance); 8 models × 4 conditions × 2 tasks. In §3 / Appendix.

## C. Computational experiments
- **C1. Model size & compute?** Models 4B–120B parameters (Table, Appendix); served locally with vLLM (FP8 for largest). **[VERIFY: report GPU type/count and total GPU-hours.]**
- **C2. Experimental setup / hyperparameters?** Temperature 0.7, top-p 0.9, max 1024 generated tokens, plain-text structured output parsed by regex (no JSON constraint, no confidence rubric), identical prompt across conditions (§4.2, Appendix B = verbatim run-time template).
- **C3. Descriptive stats / variance / significance?** Yes (rev.): 95% post-cluster bootstrap CIs on all pooled metrics; logistic regression with condition/model fixed effects and post-clustered SEs; AUROC per cell; equal-mass bins with per-bin n; ECE/Brier per model; 3-seed decoding-stability check on the validation subset for two models (Limitations).
- **C4. Packages used?** vLLM, HuggingFace Transformers, scikit-learn, SciPy, pandas, matplotlib. **[VERIFY: versions.]**

## D. Human annotation
- **D1. Full instructions / coding guidelines?** **[VERIFY: include the codebook / annotation instructions in an appendix or supplementary.]**
- **D2. Recruitment & compensation?** **[VERIFY — REQUIRED: how were the 3 label coders + 2 confidence coders recruited; were they students/colleagues; paid or volunteer; hourly rate if paid.]**
- **D3. Consent for data use?** Public posts; annotators are research collaborators who consented to participate. **[VERIFY.]**
- **D4. IRB / ethics board?** **[VERIFY — REQUIRED: state IRB approval/exemption number, or that an ethics board deemed it exempt. Many *ACL desk-checks look for this for human-subjects + political profiling.]**
- **D5. Annotator background?** 3 coders with political-content-analysis experience for labels; 2 coders for the text-only confidence sub-study. Inter-coder κ reported (§3.3). **[VERIFY: native language / expertise details.]**

## E. AI assistants (if separate item)
Disclose AI assistance for code, analysis, and writing, with author verification of all outputs (see A4).

---
### Highest-priority gaps to resolve before submission
1. **D2 (recruitment/payment) and D4 (IRB)** — required human-subjects info; currently unknown.
2. **B1/B2** — add model citations + license statements; state release license.
3. **C1/C4** — GPU hours + package versions.
4. Anonymize the **code/data link** in the paper (the `% VERIFY` in §4) before the anonymous submission.
