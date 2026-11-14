# Citing sentences (camera-ready, extracted from latex/acl_latex.tex and latex/tab_rebuttal.tex)

Regenerated after the third pass on 2026-11-13; Codex read the first extraction (git history).

1. keys: bransford_contextual_1972, clark_using_2005, grosz_centering_1995, stalnaker_common_2002

   Human readers interpret a text by combining its literal content with background knowledge, discourse history, speaker identity, and situational cues \cite{clark_using_2005, grosz_centering_1995, stalnaker_common_2002, bransford_contextual_1972}.

2. keys: aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022

   On social media, where posts are indirect, referential, or written for a particular audience, the information needed to resolve meaning often lies outside the captured text, and disagreement between annotators is often signal about the item rather than noise \cite{aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022}.

3. keys: allaway_zero-shot_2020, joseph_constance_2017, li_p-stance_2021, mohammad_semeval-2016_2016

   Stance detection, ideology inference, and sentiment analysis are nonetheless defined and evaluated on individual posts \cite[e.g., for stance,][]{mohammad_semeval-2016_2016, li_p-stance_2021, allaway_zero-shot_2020}, and the problem is sharpest in political discourse, where annotators' judgments demonstrably shift when conversational or situational context is added or removed \cite{joseph_constance_2017}.

4. keys: gilardi_chatgpt_2023, pangakis_automated_2023, tornberg_large_2025, ziems_can_2024

   LLM-based annotation pipelines increasingly replace or supplement human annotators in this setting \cite{gilardi_chatgpt_2023, tornberg_large_2025}, their reliability requires validation \cite{pangakis_automated_2023, ziems_can_2024}, and they typically operate on isolated posts, delegating the isolationist assumption to the model.

5. keys: gligoric_can_2025, tian_just_2023, xiong_can_2024

   Calibration research shows verbalized confidence carries information about correctness while being systematically inflated \cite{tian_just_2023, xiong_can_2024}, and confidence-driven routing between LLMs and humans has been proposed as a workflow \cite{gligoric_can_2025}.

6. keys: allaway_zero-shot_2020, joseph_constance_2017, li_p-stance_2021, mohammad_semeval-2016_2016

   Benchmarks for stance, ideology, and sentiment annotate each post independently with a single label \cite[e.g., for stance,][]{mohammad_semeval-2016_2016, li_p-stance_2021, allaway_zero-shot_2020}, although annotators struggle on isolated posts, with low agreement \cite{allaway_zero-shot_2020}, and the context shown to them changes the labels they produce \cite{joseph_constance_2017}.

7. keys: aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022

   The human-label-variation literature treats such disagreement as informative \cite{aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022}; we adopt that view by analyzing coder unanimity as an item-level ambiguity measure (Section~\ref{sec:results_unanimity}).

8. keys: deverna_large_2025, niu_challenge_2024, pujari_we_2024, sucu_exploiting_2025

   Conversational structure \cite{niu_challenge_2024}, user profile summaries and post histories \cite{sucu_exploiting_2025}, socially grounded entity and event context \cite{pujari_we_2024}, and curated external context \cite{deverna_large_2025} have each been shown to help political text classification.

9. keys: davenia_quantifying_2025

   Such context is typically concatenated without distinguishing its kinds and evaluated only on accuracy, and irrelevant context can distort LLM political judgments \cite{davenia_quantifying_2025}.

10. keys: kadavath_language_2022, tian_just_2023, xiong_can_2024

   LLMs can express uncertainty in words, sometimes more informatively than token probabilities \cite{tian_just_2023}, but verbalized confidence is systematically overconfident and clusters in the 80--100 range \cite{xiong_can_2024}, and self-evaluation improves when relevant source material is present in context \cite{kadavath_language_2022}.

11. keys: geifman_selective_2017, gligoric_can_2025, kamath_selective_2020

   Using a score to decide which predictions to keep is selective prediction \cite{geifman_selective_2017, kamath_selective_2020}; routing the remainder to humans is the basis of confidence-driven annotation pipelines \cite{gligoric_can_2025}.

12. keys: kwon2023vllm

   All models are served locally on NVIDIA H100 GPUs with vLLM \cite{kwon2023vllm} and decoded with temperature $0.7$, top-$p$ $0.9$, and a maximum of $1024$ generated tokens (raised from 512 after observing mid-output truncation); qwen3-80b-a3b is served in FP8 and gpt-oss-120b in its native MXFP4 quantization.

13. keys: plank_problem_2022

   LLM confidence thus encodes part of the ambiguity humans perceive, supporting the label-variation view that disagreement is signal \cite{plank_problem_2022}, which majority-vote evaluation alone would hide.

14. keys: elyaniv_foundations_2010

   Over the whole coverage range it is better: the area under the risk--coverage curve of \citet{elyaniv_foundations_2010}, the mean error rate across all coverage levels, is $9.0$ for confidence against $11.5$ for the platform rule on ideology (post-bootstrap 95\% CI on the difference $[-4.7, -0.6]$) and $18.8$ against $26.8$ on stance ($[-10.9, -4.7]$), and ranking by platform and then by confidence within platform gives $8.1$ and $18.2$ (Appendix Table~\ref{tab:aurc}).

15. keys: gligoric_can_2025, kamath_selective_2020

   Our results support confidence-aware pipelines \cite{gligoric_can_2025, kamath_selective_2020}, with two non-optional preconditions:

16. keys: xiong_can_2024

   \textbf{Measurement.} We elicit verbalized confidence rather than token-likelihood-based confidence, and the two need not coincide \cite{xiong_can_2024}.

17. keys: gemma3_2025, gptoss_2025, llama3_2024, mistral3_2025, qwen3_2025

   \caption{Large language models evaluated in this study: Gemma-3 \cite{gemma3_2025}, Llama-3.1 \cite{llama3_2024}, Qwen3 \cite{qwen3_2025}, gpt-oss \cite{gptoss_2025}, and Ministral-3 \cite{mistral3_2025}.}

18. keys: elyaniv_foundations_2010

   Top: area under the risk--coverage curve of \citet{elyaniv_foundations_2010} (mean error rate over all coverage levels, lower is better); the platform rule keeps Truth Social posts first and orders posts at random within platform.

