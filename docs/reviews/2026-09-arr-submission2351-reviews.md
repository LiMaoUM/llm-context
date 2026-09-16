# ARR reviews, Submission 2351 (received 2026-09, reviews modified 2026-09-15)

Paper: `latex/acl_latex.tex` ("Confidence Ranks, but Overstates, Reliability" LLM political-annotation paper).
Three official reviews, all Overall Assessment 3 (Findings). Verbatim text below; equation
symbols dropped by the OpenReview copy are marked `[symbol missing in copy]`.

| Reviewer | Confidence | Soundness | Excitement | Overall | Repro | Datasets | Software |
|---|---|---|---|---|---|---|---|
| 24ts | 4 | 4 | 4 | 3 (Findings) | 4 | 4 | 3 |
| 8FDE | 3 | 3 | 3.5 | 3 (Findings) | 3 | 1 | 1 |
| h3ni | 4 | 3.5 | 3.5 | 3 (Findings) | 4 | 4 | 4 |

Ethical concerns: none from any reviewer. Needs ethics review: no.

---

## Reviewer 24ts (07 Sept 2026, 17:28; modified 15 Sept 2026, 10:30)

### Paper Summary

This paper discusses in detail two important points when utilizing LLMs for annotation: how useful and reliable verbalized confidence is, and how important context is when carrying out post-level annotation. The authors conduct a plethora of experiments to draw interesting and relevant conclusions that illustrate the main considerations to keep in mind when using LLMs for this task. First, the importance of context in text-level tasks, especially in the field of social sciences. Second, the value of verbalized confidence only for the ranking of the outputs. They collect these insights into a usage protocol on how to build better LLM-based annotation pipelines.

### Summary Of Strengths

The paper is quite relevant and interesting. It is very well written, and the authors make a substantial effort to carry out the required experiments to draw relevant and, down the line, useful conclusions. To this end, they build an interesting dataset of conversation trees from threads queried from Bluesky and Truth Social, which they consider the information unit of interest for annotation tasks in the social sciences. These conversation trees, together with additional metadata, enable the creation of inputs with different context levels. Further, they carry out human annotation of a subset of posts, using several annotators, and not only label ideology and stance but also confidence in the response. This allows them to perform a range of experiments, among which I would highlight those revealing the following results: the relationship between context size and increased confidence (Section 5.3), the relationship between human and LLM confidence (Section 5.5), and the variation in accuracy when using confidence for prediction selection (Section 5.7).

### Summary Of Weaknesses

I believe the paper is well-rounded, and the most important conclusions, which are interesting and relevant, are well justified. Yet I consider there are two weaknesses which, even though are discussed in the limitations, if they had been addressed, the manuscript would have deserved a higher score. These are:

1. I appreciate that the authors present the platform as a baseline, as it is quite revealing and indeed says a lot about the generability of the results. In light of these results, I would have appreciated some additional data from another, less biased platform, which would have shown near-random performance in the baseline experiments. I believe this would have substantially strengthened the conclusions.
2. Information about the human annotation agreement could have been used more extensively, beyond the experiment in Section 5.6, for example, to try to predict challenging cases for humans using the probability of class-flip when prompting the model several times.
3. Finally, I cannot understand why the authors chose a temperature of 0.7, which introduces another stochastic component that could blur the conclusions of the experiments. I would appreciate a more detailed discussion of this decision.

I understand tackling some of these points is time-consuming and laborious, but I do honestly believe they would lead to a more impactful paper.

### Comments Suggestions And Typos

In 3.3, the acronyms for the different elements of the context are used before being defined. I would just remove them, leaving full context, or refer to the later section.

And also, the suggestions mentioned before.

### Scores

- Confidence: 4 = Quite sure. I tried to check the important points carefully. It's unlikely, though conceivable, that I missed something that should affect my ratings.
- Soundness: 4 = Strong: This study provides sufficient support for all of its claims. Some extra experiments could be nice, but not essential.
- Excitement: 4 = Exciting: I would mention this paper to others and/or make an effort to attend its presentation in a conference.
- Overall Assessment: 3 = Findings: I think this paper could be accepted to the Findings of the ACL.
- Ethical Concerns: There are no concerns with this submission. Needs Ethics Review: No.
- Reproducibility: 4 = They could mostly reproduce the results, but there may be some variation because of sample variance or minor variations in their interpretation of the protocol or method.
- Datasets: 4 = Useful: I would recommend the new datasets to other researchers or developers for their ongoing work.
- Software: 3 = Potentially useful: Someone might find the new software useful for their work.
- Knowledge Of Or Educated Guess At Author Identity: No. Knowledge Of Paper: N/A.
- Publication Ethics Policy Compliance: I used a privacy-preserving tool exclusively for the use case(s) approved by PEC policy, such as language edits.

---

## Reviewer 8FDE (07 Sept 2026, 09:38; modified 15 Sept 2026, 10:30)

### Paper Summary

Eight open-weight models label political ideology and stance under four nested context conditions, and the paper asks whether their unprompted verbalized confidence can be used to decide which labels to keep.

### Summary Of Strengths

The nested design does real work, and the T+B condition turns out to be an accidental placebo. Adding a background brief lengthens the prompt, raises confidence for every model, and moves accuracy not at all. That is a clean isolation of confidence inflation from information gain, and the paper recognises it as such.

Table 9 is the right check for the headline recommendation. Pooled coverage curves could easily be an artifact of ranking well-calibrated models above badly-calibrated ones; showing the same monotone pattern within each of the eight models, including the worst, closes that off.

The Limitations section is worth reading, which is unusual. Three-seed re-decoding with flip rates reported, a parse-failure sensitivity analysis, and a plain statement that the gold labels are a context-rich reference rather than a truth.

### Summary Of Weaknesses

1. On one platform the entire pipeline recovers nothing, and this is left in an appendix table. Appendix Table 6 gives Bluesky stance accuracy as 56.2 at text-only, 46.1 at T+B, 49.2 at T+B+C, and 50.8 at full context. Accuracy is highest with no context and falls once context is added. The same table's caption gives the Bluesky gold composition as 0 favor, 39 against, 38 none, so the majority class is [symbol missing in copy] and full-context accuracy matches it to within two-tenths of a point. On a quarter of the validation set, one of the two tasks, the context pipeline performs at chance and the gradient runs backwards. §5.2 mentions the platform asymmetry as a difference in level. It is more than that, and it belongs in §5.1.

2. The paper never compares verbalized confidence against a rival confidence signal. Decoding is stochastic at temperature 0.7 with one sample per cell. Sampling [symbol missing in copy] times and using agreement across samples is the obvious competitor, it costs nothing conceptually since the machinery is already stochastic, and it is what a practitioner would reach for first. As things stand the claim is that verbalized confidence beats no selection, which was not seriously in doubt. Whether it beats sample agreement is the question the paper's title promises to answer.

3. The human comparison is asked to carry more than two annotators can bear. The confidence sub-study uses two coders whose scale use differs by roughly a factor of 2.5 (ideology means 39 and 16), with unweighted [symbol missing in copy] of 0.28 and 0.34. Every model in Table 2 is scored against the mean of those two, and the human ceiling is the agreement between them. The paper's most novel claim, that one model's uncertainty resembles human uncertainty, therefore rests on a two-person reference that agrees poorly with itself on the raw scale. A third coder was already recruited for the label task.

### Comments Suggestions And Typos

Focus on weakness.

### Scores

- Confidence: 3 = Pretty sure, but there's a chance I missed something. Although I have a good feel for this area in general, I did not carefully check the paper's details, e.g., the math or experimental design.
- Soundness: 3 = Acceptable: This study provides sufficient support for its main claims. Some minor points may need extra support or details.
- Excitement: 3.5
- Overall Assessment: 3 = Findings: I think this paper could be accepted to the Findings of the ACL.
- Ethical Concerns: There are no concerns with this submission. Needs Ethics Review: No.
- Reproducibility: 3 = They could reproduce the results with some difficulty. The settings of parameters are underspecified or subjectively determined, and/or the training/evaluation data are not widely available.
- Datasets: 1 = No usable datasets submitted.
- Software: 1 = No usable software released.
- Knowledge Of Or Educated Guess At Author Identity: No. Knowledge Of Paper: N/A.
- Publication Ethics Policy Compliance: I did not use any generative AI tools for this review.

---

## Reviewer h3ni (05 Sept 2026, 14:01; modified 15 Sept 2026, 10:30)

### Paper Summary

The paper asks whether an LLM annotator's unprompted verbalized confidence can be used to decide which political ideology and stance labels to trust. Eight open-weight models label Truth Social and Bluesky posts under four nested context conditions, and the authors show that confidence discriminates correct from incorrect predictions within conditions while being badly overconfident in absolute terms, motivating a rank-based triage protocol.

### Summary Of Strengths

1. The central methodological move is correct and not obvious. Context raises confidence and accuracy together, so a pooled confidence-accuracy association is uninformative. Conditioning on context and testing the relationship within each condition is exactly the right control, and §5.4 backs it with three converging analyses (AUROC, fixed-effects logistic regression, binned reliability curves) rather than one.
2. The paper reports what works against it. Models fall below the majority-class baseline at text-only, the crude platform-prior rule nearly matches full-context accuracy, the background brief does not help, the abstention-rate shift is surfaced as a response-format effect rather than folded away, and §5.2 openly states that some of the metadata gain is community-prior recovery. The Limitations section is specific and includes a three-seed decoding-stability check and a parse-failure sensitivity analysis.
3. Tying model confidence to coder unanimity (§5.6) is a good idea, and it connects the calibration literature to the human-label-variation literature in a way that is more than decorative. The accuracy split it produces (94.9% versus 62.5% for ideology) is a striking demonstration that majority-vote evaluation hides item difficulty.

### Summary Of Weaknesses

1. The absolute-calibration analysis pools over conditions, which is the exact move the paper argues against everywhere else. §5.4 establishes that pooling across conditions confounds context with confidence, and the paper conditions on context for every discrimination result. Yet Table 7 is explicitly "pooled over conditions," and §5.5 opens with "Pooled over conditions, mean confidence exceeds accuracy for every model." Since confidence and accuracy both rise across conditions, a pooled gap can be near zero while every individual condition is badly miscalibrated in the same direction, or while conditions miscalibrate in opposite directions. Gemma-3-27b-it illustrates the risk: its pooled ideology gap is 4.9 points with ECE 0.06, yet Table 2 shows its text-only mean confidence at 64.5 against a human mean near 28. This matters directly for the deliverable, because the §6.3 protocol instructs practitioners to "check global overconfidence first," and the paper has not shown that a pooled check detects condition-level overconfidence. Per-condition ECE and gap tables are needed.

2. Table 8 contradicts the sentence it supports, and one headline claim is wrong for one of the two tasks. §5.4 and the Table 8 caption both state that discrimination is "weakest just after the background brief is added." For stance this holds (T+B [value missing in copy] is the minimum). For ideology it does not: T+B+C is [value missing in copy], below T+B at [value missing in copy]. The claim is presented as a general pattern with a mechanistic explanation attached ("the condition where confidence inflates without accuracy gains"), and half the evidence points the other way. Relatedly, Table 7's caption says gpt-oss-120b is least overconfident, but on ideology gemma-3-27b-it beats it on gap (4.9 versus 7.1), ECE (.06 versus .08), and confidently-wrong rate (17.8 versus 20.3). The "only gpt-oss-120b passes" claim in the abstract, §5.5, §6.3, and the Conclusion is task-aggregated but the underlying evidence is task-specific.

3. The triage protocol's advantage over the crude alternative does not survive coverage matching, and the paper's own comparison is stated in a way that obscures this. §5.7 writes that confidence-based selection "compares favorably with the crude rival policy of keeping only Truth Social labels (89.6% ideology agreement at 74% coverage, vs. 91.3% at 60%)." Those are different coverage levels. Interpolating Table 3's full-context ideology row between 80% coverage (88.3) and 60% (91.3) gives roughly 89.2% at 74% coverage, which is slightly below the platform rule's 89.6%. On the accuracy axis at matched coverage, the free heuristic is at least as good. The defense offered in the same sentence, that confidence works within each platform while the platform rule does not, is the real argument and should carry the comparison on its own. A risk-coverage curve with area under it (El-Yaniv and Wiener, 2010) would let both policies be compared on one frontier instead of at hand-picked points.

### Comments Suggestions And Typos

Please refer to the Weaknesses section.

### Scores

- Confidence: 4 = Quite sure. I tried to check the important points carefully. It's unlikely, though conceivable, that I missed something that should affect my ratings.
- Soundness: 3.5
- Excitement: 3.5
- Overall Assessment: 3 = Findings: I think this paper could be accepted to the Findings of the ACL.
- Ethical Concerns: There are no concerns with this submission. Needs Ethics Review: No.
- Reproducibility: 4 = They could mostly reproduce the results, but there may be some variation because of sample variance or minor variations in their interpretation of the protocol or method.
- Datasets: 4 = Useful: I would recommend the new datasets to other researchers or developers for their ongoing work.
- Software: 4 = Useful: I would recommend the new software to other researchers or developers for their ongoing work.
- Knowledge Of Or Educated Guess At Author Identity: No. Knowledge Of Paper: N/A.
- Publication Ethics Policy Compliance: I used a privacy-preserving tool exclusively for the use case(s) approved by PEC policy, such as language edits.
