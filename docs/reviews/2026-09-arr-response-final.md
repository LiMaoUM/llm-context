# ARR Submission 2351: author response (paste-ready)

Post one general comment on the submission and one official comment under each review. Text only,
no links (ARR rule). Table numbers below are the submitted paper's numbers: Table 2 model-versus-
human confidence agreement, Table 3 coverage-accuracy, Table 6 per-platform accuracy, Table 7
absolute calibration, Table 8 within-condition AUROC, Table 9 per-model coverage. New material is
described by content and marked as added to the revision.

Decisions applied (Mao, 2026-09-19, DECISIONS.md): text-only response, no revised PDF; the
camera-ready adds the third coder's confidence ratings; the Datasets/Software scores are not
discussed; the release plan is restated once.

---

## General comment

We thank the three reviewers. Every factual objection in the reviews checked out against our own
tables, and each has been corrected in the revision. Reviewer h3ni's three points required
rewording two captions and Section 5.4, replacing the pooled calibration analysis with a
per-condition one, and replacing a misleading comparison in Section 5.7 with a coverage-matched
one. Reviewer 8FDE's Bluesky point moved from an appendix table into Section 5.1. All three
reviewers raised stochastic decoding at temperature 0.7 from different angles (why that setting;
whether cross-sample agreement is a better reliability signal; whether it predicts items that are
hard for humans). One add-on experiment answers all three: we re-decoded every validated cell
(295 posts x 4 conditions, identical prompts) ten times for each of the eight models and compared
verbalized confidence against cross-sample agreement within condition. Results are below and in a
new appendix section. The body of the revision still ends on page 8. The camera-ready will add
the third coder's text-only confidence ratings (see our reply to 8FDE) and will release the code,
configuration, and the validation annotations keyed to hashed post identifiers.

---

## Reply to Reviewer h3ni

Thank you for a review that checked the tables. All three points are correct.

**W1, pooled calibration.** Agreed. The revision assesses absolute calibration per condition: a
new appendix table gives the confidence-accuracy gap and ECE for all 8 models x 4 conditions x 2
tasks, and Section 5.5 is rewritten around it. Mean confidence exceeds accuracy in 62 of 64 cells;
the two exceptions are gemma-3-27b-it and gpt-oss-120b on ideology at full context, where
confidence is 1 to 2 points below accuracy. Pooled over models, the gap peaks at T+B (25 points
ideology, 39 stance) and is smallest at full context (6 and 23). The pooled figure hides exactly
what you describe: gemma-3-27b-it's pooled ideology gap of 4.9 averages 13.6 at T+B with minus
1.9 at full context. Protocol step 1 in Section 6.3 now says to check overconfidence under the
context condition that will be deployed, and why a pooled check can pass a model that is badly
overconfident in the condition actually used.

**W2, Table 8 and Table 7 captions.** Both corrected. Section 5.4 and the Table 8 caption now
state that the minimum is T+B for stance (0.56) and T+B+C for ideology (0.62, with T+B at 0.63),
and we no longer attach a mechanism to T+B specifically. The Table 7 caption and Section 5.5 now
name gemma-3-27b-it as least overconfident on ideology and gpt-oss-120b on stance. The statement
that only gpt-oss-120b "passes" is restricted, in the abstract, Section 5.5, Section 6.3, and the
conclusion, to the check it actually concerns: alignment of the confidence distribution with human
confidence (Table 2), where gpt-oss-120b is the only model within the coder-coder ceiling.

**W3, coverage matching.** Agreed, and the original sentence was misleading. At the platform
rule's own coverage (75 percent) confidence selection ties it: 89.8 vs 89.5 on ideology, 74.8 vs
74.9 on stance. Section 5.7 now says so and compares the policies on the full frontier as you
suggest. The area under the risk-coverage curve (mean error over all coverage levels, El-Yaniv and
Wiener 2010) is 9.0 for confidence against 11.5 for the platform rule on ideology, with a
post-level bootstrap 95 percent CI on the difference of [minus 4.7, minus 0.6], and 18.8 against
26.8 on stance ([minus 10.9, minus 4.7]). The two policies also compose: ranking by platform and
then by confidence within platform gives 8.1 and 18.2. The within-platform argument now carries
the comparison. Keeping the top 60 percent raises full-context ideology agreement from 89.5 to
93.2 on Truth Social and from 69.7 to 77.1 on Bluesky, and within-platform AUROC exceeds 0.5 for
every model on both platforms. These numbers are in a new appendix table.

---

## Reply to Reviewer 8FDE

Thank you. Your first and second points changed the paper.

**W1, Bluesky stance at chance.** Agreed, and it now has its own paragraph in Section 5.1. On
Truth Social, accuracy rises with context on both tasks (57.8 to 89.6 ideology, 40.0 to 75.4
stance). On Bluesky it does not: stance is highest with no context (56.2), falls when the brief
is added (46.1), and ends at 50.8 against a 50.6 majority class; ideology at full context (69.6)
is also below its majority class (74.3). The paragraph reports the mechanism. As context
accumulates, the share of Bluesky stance predictions reading "against" climbs from 52 to 82
percent while the gold set is split almost evenly between "against" (39) and "none" (38). Context
pulls models toward the community prior, which is right on Truth Social and half right on
Bluesky. Section 5.2 now builds on this paragraph instead of describing the platform difference
as a difference in level.

**W2, verbalized confidence versus cross-sample agreement.** We ran the comparison. Every
validated cell (295 posts x 4 conditions, the same prompts as the paper) was re-decoded ten
times for each of the eight models at temperature 0.7. Within each condition we compare three
signals for the first sample's correctness: its verbalized confidence, the share of the other nine
samples that agree with its label, and their rank average.

Verbalized confidence is at least as discriminative as agreement in 44 of 64 model x condition x
task cells and in 14 of 16 model x task pairs pooled over conditions. The exception is
llama-3.1-8b on ideology, where agreement reaches AUROC 0.80 against 0.59 for verbalized
confidence at full context. The pattern has a simple explanation: agreement carries information
only when the model flips, and the share of cells where all ten samples agree runs from 48
percent (llama-3.1-8b) to 95 percent (gemma-3-27b-it); the gap between the two signals tracks
that share (Spearman 0.58 over the 16 pairs). The signals are complementary: their rank average
matches or exceeds verbalized confidence in 56 of 64 cells and adds 0.05 or more AUROC in 21,
up to 0.22 for llama-3.1-8b. At the operating point of Section 5.7 (top 60 percent of
full-context cells), verbalized confidence beats agreement for 13 of 16 pairs and the
combination is best or tied in 15; majority voting over the ten samples moves accuracy by at
most 3 points. So verbalized confidence does beat the rival a practitioner would reach for
first, for every model except the least stable one, and the new appendix section gives a
criterion (the flip rate on a small validated sample) for when extra samples are worth paying
for. The full per-model, per-condition table is in the appendix, and the Limitations paragraph on
decoding now states the result.

**W3, the two-coder confidence reference.** We agree it is thin, and we will strengthen it. For
the camera-ready, the third coder (already recruited for the label task, as you note) will rate
text-only confidence on the same 283 posts, and Table 2 will be recomputed against the
three-coder reference with a three-coder ceiling. For this revision we show what the two-coder
reference can and cannot carry: a new appendix table repeats the comparison against each coder
separately and against a scale-free consensus (the mean of within-coder percentile ranks). The
model ordering is identical under every reference. gpt-oss-120b leads against both coders on both
tasks (Spearman 0.82 and 0.66 for ideology; quadratic-weighted kappa 0.71 and 0.43), and the
rank-based consensus reproduces Table 2's correlations to two decimals. The scale difference
between the coders affects the level of agreement, and the ranking of models survives it.

---

## Reply to Reviewer 24ts

Thank you for the careful reading and for the acronym catch.

**W1, a less polarized platform.** We agree this would strengthen the conclusions and it is
beyond what we can add within the cycle. The revision makes the Bluesky result, our closest
approximation to a mixed platform, a headline finding in Section 5.1 (stance stays at the
majority-class level under every condition; see our reply to 8FDE), and the Limitations section
states that headline numbers on mixed platforms should be expected to sit near the Bluesky column.

**W2, using human agreement more; class-flip probability under repeated prompting.** Done, as
part of a ten-sample re-decoding of every validated cell for all eight models (details in our
reply to 8FDE). The cross-seed flip rate is higher on posts where the three coders split 2 to 1
than on unanimous posts for 15 of 16 model x task pairs, typically by a factor of two to six
(llama-3.1-8b ideology 44 vs 13 percent; qwen3-4b 29 vs 5 percent), so flip probability does
flag items that are hard for humans. Verbalized confidence flags the same items more sharply
(higher AUROC for coder unanimity in 15 of 16 pairs), which agrees with Section 5.6.

**W3, temperature 0.7.** The Limitations section now gives the rationale. Temperature 0.7 with
top-p 0.9 is the setting under which these models are typically deployed for annotation, and the
paper's question is whether the confidence a practitioner actually sees is usable, so we kept the
deployment setting and measured the noise it introduces. The three-seed check bounds that noise
(label flips in 2.5 to 15.1 percent of cells, confidence SD of 2 to 3 points), and the
ten-sample experiment above turns the same stochasticity into a measured rival signal: for seven
of eight models a single verbalized confidence score is at least as informative as agreement
across ten samples.

**Acronyms in Section 3.3.** Fixed. The section now says "the full-context rendering" and "the
text-only rendering" with a forward reference to Section 4.1.
