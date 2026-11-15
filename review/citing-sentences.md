# Citing sentences (camera-ready, extracted from latex/acl_latex.tex and latex/tab_rebuttal.tex)

Regenerated 2026-11-15 after the main text was restored to the reviewed wording; Codex read the first extraction (git history).

1. keys: bransford_contextual_1972, clark_using_2005, grosz_centering_1995, stalnaker_common_2002

   Language understanding is inherently contextual: human readers interpret a text by combining its literal content with background knowledge, discourse history, speaker identity, and situational cues---a point long central to discourse analysis, pragmatics, and dialogue research \cite{clark_using_2005, grosz_centering_1995, stalnaker_common_2002, bransford_contextual_1972}.

2. keys: aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022

   The human-label-variation literature makes the same point from the annotation side: disagreement between annotators is often signal about the item, not noise to be averaged away \cite{aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022}.

3. keys: allaway_zero-shot_2020, li_p-stance_2021, mohammad_semeval-2016_2016

   This tension is built into common computational social science workflows: stance detection, ideology inference, and sentiment analysis are typically defined and evaluated on individual posts, even when those posts are replies or fragments within longer threads \cite[e.g., for stance,][]{mohammad_semeval-2016_2016, li_p-stance_2021, allaway_zero-shot_2020}.

4. keys: joseph_constance_2017

   The problem is sharpest in political discourse, where posts depend on shared events, implicit targets, sarcasm, and community-specific cues; annotators' judgments demonstrably shift when conversational or situational context is added or removed \cite{joseph_constance_2017}.

5. keys: gilardi_chatgpt_2023, pangakis_automated_2023, tornberg_large_2025, ziems_can_2024

   LLM-based annotation pipelines increasingly replace or supplement human annotators in this setting \cite{gilardi_chatgpt_2023, tornberg_large_2025}, though their reliability requires validation rather than assumption \cite{pangakis_automated_2023, ziems_can_2024}, and they typically operate on isolated posts, delegating the isolationist assumption to the model.

6. keys: gligoric_can_2025, tian_just_2023, xiong_can_2024

   Calibration research shows verbalized confidence carries information about correctness while being systematically inflated \cite{tian_just_2023, xiong_can_2024}, and confidence-driven routing between LLMs and humans has been proposed as a workflow \cite{gligoric_can_2025}.

7. keys: allaway_zero-shot_2020, joseph_constance_2017, li_p-stance_2021, mohammad_semeval-2016_2016

   Most social-media NLP treats individual posts as self-contained units of meaning: benchmarks for stance, ideology, and sentiment annotate each post independently with a single label \cite[e.g., for stance,][]{mohammad_semeval-2016_2016, li_p-stance_2021, allaway_zero-shot_2020}, even though human annotators struggle on isolated posts, with low agreement \cite{allaway_zero-shot_2020}, and the context shown to annotators demonstrably changes the labels they produce \cite{joseph_constance_2017}.

8. keys: aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022

   The human-label-variation literature argues that such disagreement is informative rather than erroneous \cite{aroyo_truth_2015, pavlick_inherent_2019, plank_problem_2022}; we adopt that view operationally by analyzing coder unanimity as an item-level ambiguity measure rather than discarding it (Section~\ref{sec:results_unanimity}).

9. keys: deverna_large_2025, niu_challenge_2024, pujari_we_2024, sucu_exploiting_2025

   A growing body of work adds context to social-media models: conversational structure improves stance classification \cite{niu_challenge_2024}, user profile summaries and post histories improve political stance detection \cite{sucu_exploiting_2025}, and socially grounded entity and event context helps resolve ambiguous political texts \cite{pujari_we_2024}; curated external context has similarly been studied for political fact-checking \cite{deverna_large_2025}.

10. keys: davenia_quantifying_2025

   Such context is typically a performance add-on, concatenated without distinguishing its kinds and evaluated only on accuracy, and irrelevant context can even distort LLM political judgments \cite{davenia_quantifying_2025}.

11. keys: tian_just_2023, xiong_can_2024

   LLMs can express uncertainty in words, sometimes more informatively than token probabilities \cite{tian_just_2023}, but verbalized confidence is systematically overconfident and clusters in the 80--100 range \cite{xiong_can_2024}.

12. keys: kadavath_language_2022

   \citet{kadavath_language_2022} further showed that self-evaluation improves when relevant source material is present in context.

13. keys: geifman_selective_2017, gligoric_can_2025, kamath_selective_2020

   Using a score to decide which predictions to keep is selective prediction \cite{geifman_selective_2017, kamath_selective_2020}; routing the remainder to humans is the basis of confidence-driven annotation pipelines \cite{gligoric_can_2025}.

14. keys: kwon2023vllm

   All models are served locally on NVIDIA H100 GPUs with vLLM \cite{kwon2023vllm} and decoded with temperature $0.7$, top-$p$ $0.9$, and a maximum of $1024$ generated tokens (raised from 512 after observing mid-output truncation); qwen3-80b-a3b is served in FP8 and gpt-oss-120b in its native MXFP4 quantization.

15. keys: plank_problem_2022

   LLM confidence thus encodes part of the same ambiguity humans perceive---supporting the label-variation view that disagreement is signal \cite{plank_problem_2022}---which majority-vote evaluation alone would hide.

16. keys: elyaniv_foundations_2010

   Against the crude rival policy of keeping only Truth Social labels, confidence-based selection ties at matched coverage ($89.8\%$ vs.\ $89.5\%$ ideology agreement at $75\%$) and has the lower area under the risk--coverage curve of \citet{elyaniv_foundations_2010} ($9.0$ vs.\ $11.5$; Appendix Table~\ref{tab:aurc})---and unlike that policy it works within each platform.

17. keys: gligoric_can_2025, kamath_selective_2020

   Our results support confidence-aware pipelines \cite{gligoric_can_2025, kamath_selective_2020}, with two non-optional preconditions:

18. keys: xiong_can_2024

   \textbf{Measurement.} We elicit verbalized confidence rather than token-likelihood-based confidence, and the two need not coincide \cite{xiong_can_2024}.

19. keys: gemma3_2025, gptoss_2025, llama3_2024, mistral3_2025, qwen3_2025

   \caption{Large language models evaluated in this study: Gemma-3 \cite{gemma3_2025}, Llama-3.1 \cite{llama3_2024}, Qwen3 \cite{qwen3_2025}, gpt-oss \cite{gptoss_2025}, and Ministral-3 \cite{mistral3_2025}.}

20. keys: elyaniv_foundations_2010

   Top: area under the risk--coverage curve of \citet{elyaniv_foundations_2010} (mean error rate over all coverage levels, lower is better); the platform rule keeps Truth Social posts first and orders posts at random within platform.

