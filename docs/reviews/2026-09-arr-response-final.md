# ARR Submission 2351: author response (paste-ready)

One general comment on the submission, one official comment under each review. Text only, no
links. The manuscript cannot change within this cycle, so the response accepts, gives the
corrected numbers, and says what the revised version will do. Table numbers are the submitted
paper's (Table 2 human confidence agreement, Table 7 calibration, Table 8 AUROC).

Decisions applied (Mao, 2026-09-19, DECISIONS.md): text-only response; the camera-ready adds the
third coder's confidence ratings; the Datasets/Software scores are not discussed; the release plan
is restated once.

---

## General comment

Thanks so much to all three reviewers for reading the paper this closely. The factual points you
raised are all correct, and we are glad to have them caught now. Because the paper cannot be
edited within this cycle, we give the corrected numbers here and say what the revised version will
do.

All three of you asked, in different ways, about decoding at temperature 0.7. We answered with one
small experiment: every validated cell (295 posts, four conditions, the original prompts) was
re-decoded ten times for each of the eight models, so we could compare verbalized confidence with
agreement across samples. Details are in the individual replies.

The revised version will keep the body at eight pages and put the new material in the appendix.
The camera-ready will also add the third coder's confidence ratings and release the code, the
configuration, and the validation annotations keyed to hashed post ids.

---

## Reply to Reviewer h3ni

Thanks so much for checking the tables this carefully. All three points are correct.

Pooled calibration. We will report calibration per condition (gap and ECE for every model,
condition, and task) and rewrite Section 5.5 around that table. Per condition, confidence exceeds
accuracy in 62 of 64 cells, with the largest gaps at T+B (pooled gap 25 points on ideology, 39 on
stance) and the smallest at full context (6 and 23). Your gemma example is exactly what pooling
hides: its pooled ideology gap of 4.9 is the average of 13.6 at T+B and minus 1.9 at full context.
Step 1 of the protocol will ask for the check under the condition actually deployed, for this
reason.

Tables 8 and 7. Both captions will be corrected. Discrimination is lowest at T+B for stance
(0.56) and at T+B+C for ideology (0.62), so the text will describe a dip in the middle conditions
without tying it to T+B. Gemma-3-27b-it is the least overconfident model on ideology and
gpt-oss-120b on stance, and the paper will say so. The "only gpt-oss-120b passes" wording will be
limited to the human-alignment check in Table 2, where it holds.

Coverage matching. You are right that the two coverages in Section 5.7 were not comparable. At
the platform rule's own coverage of 75 percent the two policies tie (89.8 vs 89.5 on ideology,
74.8 vs 74.9 on stance). Over the whole curve, the area under the risk-coverage curve is 9.0 for
confidence and 11.5 for the platform rule on ideology (bootstrap 95 percent CI on the difference
[minus 4.7, minus 0.6]), and 18.8 vs 26.8 on stance. We will replace the current comparison with
this and lead with the within-platform result: the top 60 percent by confidence is more accurate
than the full set on both platforms (89.5 to 93.2 on Truth Social, 69.7 to 77.1 on Bluesky).

---

## Reply to Reviewer 8FDE

Thanks so much for this review. The first two points change how the paper reads.

Bluesky. Agreed, this belongs in Section 5.1 and will get its own paragraph there. On Bluesky,
stance accuracy is highest with no context (56.2) and ends at 50.8 against a 50.6 majority class,
and ideology at full context (69.6) is below its majority class (74.3) too. What happens is that
added context pulls predictions toward the community prior: the share of Bluesky stance labels
reading "against" rises from 52 to 82 percent while the gold set is split almost evenly between
"against" and "none". That is the right prior on Truth Social and half right on Bluesky.

Verbalized confidence versus agreement across samples. We ran this. Each validated cell was
re-decoded ten times per model at temperature 0.7, and within each condition we compared three
signals for the first sample's correctness: its verbalized confidence, the share of the other nine
samples that agree with its label, and the rank average of the two.

Verbalized confidence is at least as discriminative as agreement in 44 of 64 cells and in 14 of 16
model by task pairs. The exception is llama-3.1-8b on ideology, where agreement reaches AUROC 0.80
against 0.59. That model is also the least stable one: all ten samples agree in 48 percent of its
cells, against 95 percent for gemma, and the gap between the two signals tracks that stability
(Spearman 0.58 over the 16 pairs). Combining the two helps where the model is unstable, by up to
0.22 AUROC for llama, and does no harm elsewhere. At the top 60 percent of full-context cells,
verbalized confidence is more accurate than agreement for 13 of 16 pairs. So verbalized
confidence does beat the rival a practitioner would try first, and the flip rate on a small
validated sample tells you when extra samples are worth it. We will report the full table in the
appendix and state the result in Limitations.

Two coders. Agreed that this is a thin reference. For the camera-ready the third coder will rate
text-only confidence on the same 283 posts and Table 2 will be recomputed against three coders.
For now, comparing against each coder separately and against a rank-based consensus gives the
same model ordering, with gpt-oss-120b first against both coders (Spearman 0.82 and 0.66 on
ideology), so the scale difference affects the level of agreement and leaves the ranking alone.

---

## Reply to Reviewer 24ts

Thanks so much for the kind words and for catching the acronyms.

A less polarized platform. Agreed, and it is more than we can add this cycle. What we will do is
make the Bluesky result a headline finding in Section 5.1 (stance stays at the majority-class
level under every condition there; numbers in our reply to Reviewer 8FDE) and say in Limitations
that mixed platforms should be expected to look like the Bluesky column.

Class-flip probability and human disagreement. We tested this in the ten-sample re-decoding
described in the reply to Reviewer 8FDE. Labels flip across samples more often on posts where the
coders split 2 to 1 than on unanimous posts, for 15 of 16 model by task pairs, typically two to
six times as often (llama-3.1-8b on ideology: 44 vs 13 percent). So flip probability does pick out
the posts humans find hard. Verbalized confidence picks them out somewhat better (higher AUROC in
15 of 16 pairs). Both will go in the appendix.

Temperature 0.7. It is the setting these models are usually run with for annotation, and we
wanted the confidence a practitioner would actually see. The three-seed check bounds the noise it
adds (label flips in 2.5 to 15 percent of cells, confidence SD of 2 to 3 points), and the
ten-sample experiment shows that for seven of eight models a single verbalized score carries at
least as much information as agreement across ten samples. The revised Limitations will say this.

Acronyms in Section 3.3. We will remove them and refer forward to Section 4.1.
