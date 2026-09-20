# ARR Submission 2351: author response (paste-ready)

Post one general comment on the submission and one official comment under each review. Text only,
no links (ARR rule). The manuscript cannot change within this cycle, so the response accepts,
states the corrected claims with their numbers, and says what the revised version will do; it never describes edits as made.
Table numbers are the submitted paper's: Table 2 model-versus-human confidence agreement, Table 3
coverage-accuracy, Table 6 per-platform accuracy, Table 7 absolute calibration, Table 8
within-condition AUROC, Table 9 per-model coverage.

Decisions applied (Mao, 2026-09-19, DECISIONS.md): text-only response; the camera-ready adds the
third coder's confidence ratings; the Datasets/Software scores are not discussed; the release plan
is restated once.

---

## General comment

Thanks so much to all three reviewers for reading the paper this carefully. Every factual point
raised checked out against our own tables, and we are glad to have them caught now. Since the
manuscript cannot change within this cycle, this response says what we accept, what the corrected
claims are, and what the revised version will do, with the numbers so that nothing has to
be taken on trust.

Three of the questions concern stochastic decoding at temperature 0.7: why that setting, whether
agreement across repeated samples is a better reliability signal than verbalized confidence, and
whether it predicts the items that are hard for humans. One add-on experiment answers all three.
We re-decoded every validated cell (295 posts x 4 conditions, identical prompts) ten times for
each of the eight models and compared verbalized confidence against cross-sample agreement within
condition. The results are in the replies below.

In the revised version the body will stay at eight pages and the new material will go into the
appendix; the camera-ready will add the third coder's text-only confidence ratings; and we will
release the code, the configuration, and the validation annotations keyed to
hashed post identifiers.

---

## Reply to Reviewer h3ni

Thanks so much for a review that checked the tables. All three points are right, and we accept
each of them.

On the pooled calibration analysis. You are right that Table 7 pools over the very conditions the
paper insists on separating everywhere else. We will assess absolute calibration per condition,
with a gap and ECE table for all 8 models x 4 conditions x 2 tasks, and rewrite Section 5.5
around it. The per-condition picture is this. Mean confidence exceeds accuracy in 62
of 64 cells; the two exceptions are gemma-3-27b-it and gpt-oss-120b on ideology at full context,
where confidence sits 1 to 2 points below accuracy. Pooled over models, the gap peaks at T+B (25
points on ideology, 39 on stance) and is smallest at full context (6 and 23). The pooled figure
hides exactly what you suspected: gemma-3-27b-it's pooled ideology gap of 4.9 averages 13.6 at T+B
with minus 1.9 at full context. Protocol step 1 in Section 6.3 will therefore become a check under the
context condition that will be deployed, with the reason stated, since a pooled check can pass a
model that is badly overconfident in the condition actually used.

On Table 8 and Table 7. Both captions are wrong as written, and we will correct them.
Discrimination is weakest at T+B for stance (0.56) and at T+B+C for ideology (0.62, with T+B at
0.63), so the paper will describe a mid-spectrum dip and attach no mechanism to T+B
specifically. The least overconfident model is task-specific: gemma-3-27b-it on ideology and
gpt-oss-120b on stance. The statement that only gpt-oss-120b "passes" will be confined, in the
abstract, Section 5.5, Section 6.3, and the conclusion, to the check it concerns, alignment of the
confidence distribution with human confidence (Table 2), where gpt-oss-120b is the only model
within the coder-coder ceiling.

On coverage matching. You are right, and the sentence in Section 5.7 was misleading as written.
At the platform rule's own coverage (75 percent) confidence selection ties it: 89.8 vs 89.5 on
ideology and 74.8 vs 74.9 on stance. Comparing the two policies on the full frontier, as you
suggest, the area under the risk-coverage curve (the mean error rate over all coverage levels,
El-Yaniv and Wiener 2010) is 9.0 for confidence against 11.5 for the platform rule on ideology,
with a post-level bootstrap 95 percent CI on the difference of [minus 4.7, minus 0.6], and 18.8
against 26.8 on stance ([minus 10.9, minus 4.7]). The two policies also compose: ranking by
platform and then by confidence within platform gives 8.1 and 18.2. We will report these in
place of the current comparison and let the within-platform argument carry the point.
Keeping the top 60 percent raises full-context ideology agreement from 89.5 to 93.2 on Truth
Social and from 69.7 to 77.1 on Bluesky, and within-platform AUROC exceeds 0.5 for every model on
both platforms.

---

## Reply to Reviewer 8FDE

Thanks so much for this review. Your first two points change how the paper reads, and we are
grateful for both.

On Bluesky. You are right that a result of this size belongs in Section 5.1, and we will give
it a paragraph of its own there. On Truth Social, accuracy rises with context on both
tasks (57.8 to 89.6 on ideology, 40.0 to 75.4 on stance). On Bluesky it does not. Stance is
highest with no context (56.2), falls when the brief is added (46.1), and ends at 50.8 against a
50.6 majority class; ideology at full context (69.6) is also below its majority class (74.3). The
predicted labels show why. As context accumulates, the share of Bluesky stance predictions
reading "against" climbs from 52 to 82 percent while the gold set is split almost evenly between
"against" (39) and "none" (38). Context pulls models toward the community prior, which is right
on Truth Social and half right on Bluesky. Section 5.2 will then build on that paragraph, and the
platform asymmetry will be presented as a difference in what context does on each platform.

On verbalized confidence versus cross-sample agreement. We ran the comparison you asked for.
Every validated cell (295 posts x 4 conditions, the same prompts as the paper) was re-decoded ten
times for each of the eight models at temperature 0.7. Within each condition we compare three
signals for the first sample's correctness: its verbalized confidence, the share of the other nine
samples that agree with its label, and their rank average.

Verbalized confidence is at least as discriminative as agreement in 44 of 64 model x condition x
task cells and in 14 of 16 model x task pairs pooled over conditions. The exception is
llama-3.1-8b on ideology, where agreement reaches AUROC 0.80 against 0.59 for verbalized
confidence at full context. The pattern has a simple explanation. Agreement carries information
only when the model flips, and the share of cells where all ten samples agree runs from 48
percent (llama-3.1-8b) to 95 percent (gemma-3-27b-it); the gap between the two signals tracks
that share (Spearman 0.58 over the 16 pairs). The two signals are complementary. Their rank
average matches or exceeds verbalized confidence in 56 of 64 cells and adds 0.05 or more AUROC in
21, up to 0.22 for llama-3.1-8b. At the operating point of Section 5.7 (the top 60 percent of
full-context cells), verbalized confidence beats agreement for 13 of 16 pairs and the
combination is best or tied in 15; majority voting over the ten samples moves accuracy by at most
3 points. So verbalized confidence does beat the rival a practitioner would reach for first, for
every model except the least stable one, and the flip rate on a small validated sample tells a
practitioner whether extra samples are worth paying for. We will report the full per-model,
per-condition table in the appendix and state the result in the Limitations paragraph on
decoding.

On the two-coder reference. You are right that two coders who use the scale this differently are
a thin reference for the paper's most novel claim, and we will strengthen it in two steps. For
the camera-ready, the third coder, who was recruited for the label task as you note, will rate
text-only confidence on the same 283 posts, and Table 2 will be recomputed against a three-coder
reference with a three-coder ceiling. In the meantime we can say what the two-coder reference
does carry. Repeating the comparison against each coder separately and against a scale-free
consensus (the mean of within-coder percentile ranks) leaves the model ordering unchanged:
gpt-oss-120b leads against both coders on both tasks (Spearman 0.82 and 0.66 for ideology;
quadratic-weighted kappa 0.71 and 0.43), and the rank consensus reproduces the Table 2
correlations to two decimals. The scale difference between the coders moves the level of
agreement and leaves the ranking of models where it is.

---

## Reply to Reviewer 24ts

Thanks so much for the kind words and for the careful reading, including the acronym catch.

On a less polarized platform. We agree it would strengthen the conclusions, and it is more than
we can add within this cycle. What we will do is make the Bluesky result, our closest
approximation to a mixed platform, a headline finding in Section 5.1 (stance stays at the
majority-class level under every condition; the numbers are in our reply to Reviewer 8FDE), with
the Limitations section stating that headline numbers on mixed platforms should be expected to
sit near the Bluesky column.

On using human agreement more, and class-flip probability under repeated prompting. This was a
good idea and we tested it, as part of a ten-sample re-decoding of every validated cell for all
eight models (details in our reply to Reviewer 8FDE). The cross-seed flip rate is higher on posts
where the three coders split 2 to 1 than on unanimous posts for 15 of 16 model x task pairs,
typically by a factor of two to six (llama-3.1-8b ideology 44 vs 13 percent; qwen3-4b 29 vs 5
percent), so flip probability does flag items that are hard for humans. Verbalized confidence
flags the same items more sharply (higher AUROC for coder unanimity in 15 of 16 pairs), which
agrees with Section 5.6. We will report both in the appendix.

On temperature 0.7. The reason is that temperature 0.7 with top-p 0.9 is the setting under which
these models are typically deployed for annotation, and the paper's question is whether the
confidence a practitioner actually sees is usable, so we kept the deployment setting and
measured the noise it introduces. The three-seed check bounds that noise (label flips in 2.5 to
15.1 percent of cells, confidence SD of 2 to 3 points), and the ten-sample experiment above turns
the same stochasticity into a measured rival signal: for seven of eight models a single
verbalized confidence score is at least as informative as agreement across ten samples. We
will state this rationale in the Limitations section.

On the acronyms in Section 3.3. Thank you, and we will remove them; the section will say
"the full-context rendering" and "the text-only rendering" with a forward reference to Section
4.1.
