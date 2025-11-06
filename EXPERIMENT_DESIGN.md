# Detailed Experiment Design Document

## Executive Summary

This document provides a comprehensive design for testing LLM confidence and performance under different contextual conditions. The experiment systematically evaluates how different contextual layers (conversational, background, and metadata) affect LLM interpretation accuracy and confidence calibration in social media stance detection tasks.

---

## 1. Research Questions

### Primary RQs
1. **RQ1**: How do different contextual dimensions (conversational, background, metadata) affect LLM accuracy in stance detection?
2. **RQ2**: How does context richness affect model confidence calibration?
3. **RQ3**: Which context types are essential vs. marginal for robust interpretation?

### Secondary RQs
4. **RQ4**: Are confidence improvements aligned with accuracy improvements?
5. **RQ5**: Do different LLM architectures respond differently to context?
6. **RQ6**: Are there interaction effects between context dimensions?

---

## 2. Experimental Design

### 2.1 Factorial Structure

```
Context Ablation: T, T+C, T+B, T+M, T+C+B, T+C+M, T+B+M, FULL (8 conditions)
LLM Models: 6 models (GPT-4, GPT-3.5, Claude-3 Opus, Claude-3 Sonnet, Llama-2-70B, Gemma-2-27B)
Tasks: 2 tasks (Stance Detection, Sentiment Analysis)
Samples: ~10,000 annotated posts (target)
Replicates: 1 (per sample × context × model combination)
```

**Total Cells**: 8 context × 6 models × 2 tasks = **96 experimental conditions**

### 2.2 Context Definitions

| Variant | Code | Components | Rationale |
|---------|------|-----------|-----------|
| Text Only | T | Post text | Baseline (local semantic) |
| + Conversation | T+C | Post + parent/child replies | Tests conversational coherence |
| + Background | T+B | Post + event summaries | Tests world knowledge grounding |
| + Metadata | T+M | Post + user bio, followers, history | Tests social cue integration |
| + Conv + Background | T+C+B | All except metadata | Tests integration of discourse + knowledge |
| + Conv + Metadata | T+C+M | All except background | Tests integration of discourse + social cues |
| + Background + Metadata | T+B+M | All except conversation | Tests integration of knowledge + social cues |
| Full Context | FULL | All components | Upper bound on performance |

### 2.3 Data Preparation Pipeline

```
Raw Data (posts, users, edges)
    ↓
[1] Sample Selection & Filtering
    - Select posts from ~5 salient events
    - Ensure balanced stance distribution
    - Filter for sufficient context availability
    ↓
[2] Context Assembly
    - Extract parent/child posts (depth 2-3)
    - Fetch user metadata (bio, followers, verification)
    - Retrieve event background (prepared separately)
    ↓
[3] Context Variant Creation
    - Generate 8 variants per sample
    - Standardize formatting
    - Validate completeness
    ↓
[4] Annotation
    - Human annotators label stance
    - Inter-coder reliability (target: κ ≥ 0.75)
    - Adjudicate disagreements
    ↓
[5] Final Dataset
    - ~10,000 samples × 8 variants
    - ~80,000 total "items"
    - Stratified by event, stance, context completeness
```

### 2.4 Prompt Engineering

**Standardized Prompt Template**:

```
[OPTIONAL: BACKGROUND SECTION]
Event: {event_name}
Date: {event_date}
Key Information: {event_summary}

[OPTIONAL: CONVERSATION SECTION]
{parent_posts_formatted}
[TARGET POST]
{focal_post_text}
{child_posts_formatted}

[OPTIONAL: METADATA SECTION]
Author: {user_name}
Bio: {user_bio}
Followers: {follower_count}
Verification: {verified_status}

Question: What is the author's stance toward {target_entity}?

Response Format:
1. Stance Category: [one of: strongly support, support, neutral, oppose, strongly oppose]
2. Confidence: [0-100%]
3. Reasoning: [1-2 sentences]
```

**Prompt Variations**:
- Fixed instruction format across all models
- Temperature: 0.7 (balance between determinism and diversity)
- Max tokens: 256 (sufficient for reasoning + confidence)

---

## 3. Evaluation Metrics

### 3.1 Classification Metrics

| Metric | Formula | Interpretation | Target |
|--------|---------|-----------------|--------|
| **Accuracy** | # correct / # total | Overall correctness | Maximize |
| **Macro F1** | Mean F1 per class | Balance across categories | Maximize |
| **Weighted F1** | F1 weighted by support | Accounts for imbalance | Maximize |

### 3.2 Calibration Metrics

#### Expected Calibration Error (ECE)

Measures gap between predicted confidence and actual accuracy:

$$\text{ECE} = \sum_{i=1}^{M} \frac{|B_i|}{n} | \text{acc}(B_i) - \text{conf}(B_i) |$$

Where:
- $M$ = number of bins (typically 10)
- $B_i$ = samples in bin $i$
- $\text{acc}(B_i)$ = accuracy of samples in bin
- $\text{conf}(B_i)$ = average confidence in bin

**Interpretation**: 
- ECE = 0: Perfect calibration
- ECE > 0.15: Poor calibration
- Models with lower ECE are more reliable

#### Brier Score

Mean squared error between confidence and correctness:

$$\text{Brier} = \frac{1}{n} \sum_{i=1}^{n} (\hat{p}_i - y_i)^2$$

Where:
- $\hat{p}_i$ = predicted probability for sample $i$
- $y_i$ = 1 if correct, 0 if incorrect

**Interpretation**: Lower is better (range 0–1)

### 3.3 Confidence Analysis Metrics

#### Overconfidence Rate

Fraction of incorrect predictions with confidence > 70%:

$$\text{Overconf}_{70} = \frac{|\{\text{samples where } \text{confidence} > 70 \text{ AND incorrect}\}|}{|\{\text{all incorrect samples}\}|}$$

**Interpretation**: Higher = more problematic

#### Confidence-Correctness Gap

$$\Delta = \text{avg\_confidence}(\text{correct}) - \text{avg\_confidence}(\text{incorrect})$$

**Interpretation**: 
- Δ > 20%: Model differentiates well
- Δ < 10%: Model poorly calibrated

### 3.4 Context Sensitivity Metrics

#### Marginal Improvement

Accuracy gain from adding a context layer:

$$\text{MI}_{X \to Y} = \text{Acc}_Y - \text{Acc}_X$$

Example: $\text{MI}_{T \to T+C}$ = Accuracy gain from adding conversation

#### Context Sensitivity Index

Overall model sensitivity to context variations:

$$\text{CSI} = \frac{\max(\text{Acc}_{\text{all variants}}) - \min(\text{Acc}_{\text{all variants}})}{\max(\text{Acc}_{\text{all variants}})}$$

**Interpretation**: 
- CSI > 0.15: High context sensitivity
- CSI < 0.05: Low context sensitivity

#### Diminishing Returns Curve

Average accuracy by context depth:

```
Depth 1 (T):              Acc₁
Depth 2 (T+X):           Acc₂ = Acc₁ + ΔAcc₁₂
Depth 3 (T+X+Y):         Acc₃ = Acc₂ + ΔAcc₂₃
Depth 4 (FULL):          Acc₄ = Acc₃ + ΔAcc₃₄

Diminishing Returns: ΔAcc₁₂ > ΔAcc₂₃ > ΔAcc₃₄
```

---

## 4. Statistical Analysis Plan

### 4.1 Main Analysis

**For each model and task**:

1. **One-way ANOVA** across context conditions
   - H₀: All context conditions have equal accuracy
   - If significant, proceed to pairwise comparisons

2. **Post-hoc Tests** (if ANOVA significant)
   - Bonferroni-corrected t-tests
   - Contrast analyses for planned comparisons (T vs. FULL)

3. **Effect Sizes**
   - Cohen's d for pairwise comparisons
   - η² for ANOVA effect size

### 4.2 Cross-Model Comparison

1. **Two-way ANOVA**: Model × Context
   - Main effects and interaction
   - Interaction indicates model-specific context effects

2. **Model Ranking**
   - By overall accuracy
   - By calibration (ECE)
   - By context robustness (CSI)

### 4.3 Calibration Analysis

1. **Calibration Plots**
   - X-axis: Predicted confidence bins (0-10%, 10-20%, ..., 90-100%)
   - Y-axis: Actual accuracy in each bin
   - Perfect calibration: 45° line

2. **Calibration Tests**
   - Hosmer-Lemeshow test for calibration goodness-of-fit
   - ECE comparison across models

---

## 5. Experimental Workflow

### Phase 1: Preparation (Week 1-2)
- [ ] Data loading and exploration
- [ ] Context variant generation
- [ ] Annotation protocol development
- [ ] Prompt testing with smaller sample

### Phase 2: Annotation (Week 3-4)
- [ ] Recruit human annotators
- [ ] Annotate ~10,000 samples
- [ ] Calculate inter-rater reliability
- [ ] Adjudicate disagreements

### Phase 3: Inference (Week 5-6)
- [ ] Set up API credentials
- [ ] Run inference on GPT models
- [ ] Run inference on Claude models
- [ ] Run inference on open-source models
- [ ] Cache and validate outputs

### Phase 4: Analysis (Week 7)
- [ ] Compute metrics
- [ ] Generate visualizations
- [ ] Statistical testing
- [ ] Error analysis & case studies

### Phase 5: Writing (Week 8-9)
- [ ] Draft results section
- [ ] Create figures and tables
- [ ] Draft discussion
- [ ] Revision and proofs

---

## 6. Expected Findings & Hypotheses

### H1: Context Hierarchy
**Prediction**: Conversation > Background > Metadata in importance

**Rationale**: Local discourse provides immediate disambiguation; world knowledge is secondary; social signals are marginal

### H2: Diminishing Returns
**Prediction**: ΔAcc(T→T+C) > ΔAcc(T+C→FULL)

**Rationale**: Most informative context is conversational; additional layers have diminishing returns

### H3: Calibration-Accuracy Decoupling
**Prediction**: Accuracy and confidence don't always improve together

**Rationale**: Models may gain accuracy but remain poorly calibrated, or vice versa

### H4: Model-Specific Patterns
**Prediction**: Larger models (GPT-4, Claude-Opus) show better context integration

**Rationale**: Model capacity affects context processing

### H5: Overconfidence in Low-Context
**Prediction**: Overconfidence rate highest in T condition

**Rationale**: Ambiguity without context encourages false confidence

---

## 7. Data Collection Details

### 7.1 Event Selection

**Criteria for events**:
- High social media volume
- Clear stance polarity
- Multiple source posts
- Temporal locality (reduces background knowledge requirement)

**Target events** (suggestions):
1. 2024 U.S. Presidential Election
2. Dobbs v. Wade decision (abortion)
3. Cryptocurrency regulation debate
4. AI/ChatGPT policy discussions
5. Climate policy initiatives

### 7.2 Sampling Strategy

```
Total Posts: 10,000
Distribution by Event: 2,000 per event
Distribution by Stance: ~20% strong support, 20% support, 20% neutral, 20% oppose, 20% strong oppose

Filters:
- Post length: 50-280 characters (Twitter-like)
- Conversation depth: ≥1 parent or child
- User metadata: Complete bios available
- Language: English only

Stratification:
- Ensure balanced stance across all conditions
- Balance by event
- Balance by user engagement level (followers)
```

### 7.3 Annotation Guidelines

```
Task: Classify stance of post author toward {target_entity}

Definitions:
- Strongly Support: Author explicitly advocates for, celebrates, or demands this
- Support: Author favors, agrees with, or expresses positive view
- Neutral: Author provides information without clear position
- Oppose: Author disfavors, disagrees with, or expresses negative view
- Strongly Oppose: Author explicitly condemns, attacks, or vehemently rejects

Guidelines:
1. Use post text as primary signal
2. Use conversation context to disambiguate (e.g., if replying to criticism)
3. Use user metadata as tiebreaker (e.g., activist profile consistent with stance)
4. Mark as "Unclear" if annotation is impossible (target: <5%)
5. DO NOT project your own views

Quality Checks:
- 10% overlap between coders
- Target inter-rater agreement: κ ≥ 0.75
- Adjudicate disagreements via third-party review
```

---

## 8. Validation & Quality Control

### 8.1 Internal Validity

**Confounds to minimize**:
1. **Prompt bias**: Fixed templates across models
2. **Order effects**: Randomize context presentation? (Decision: No—realistic scenario)
3. **Model differences**: Control via standardized prompts
4. **Sampling bias**: Stratified sampling with balanced distribution

**Controls**:
- Cache API responses (no drift due to retries)
- Use consistent random seed for reproducibility
- Version control for all code and configs

### 8.2 External Validity

**Generalizability considerations**:
- **Dataset scope**: Limited to English, social media, political topics
- **Model coverage**: Includes proprietary (OpenAI, Anthropic) and open-source (Meta, Google)
- **Time horizon**: Single snapshot (not longitudinal)

**Limitations to note**:
- Results may not generalize to other domains (scientific, legal, medical)
- Inference API behavior may change
- Fine-tuned models may behave differently

### 8.3 Reproducibility

**Artifacts for sharing**:
- Config file with all hyperparameters
- Annotated dataset (if shareable)
- Inference prompts (exact templates)
- Results (JSON with all outputs)
- Analysis code (all metrics and visualizations)
- Seed and version numbers

---

## 9. Contingency Plans

### Issue: Annotation Cost Too High
**Plan A**: Use smaller sample (e.g., 3,000 posts) with same design
**Plan B**: Use weak labels (agreement on Twitter posts if available)

### Issue: API Rate Limits
**Plan A**: Extend timeline for inference phase
**Plan B**: Use local models for some LLMs (Llama, Gemma already open-source)

### Issue: Model Performance Ceiling (All Accuracies ~100%)
**Plan A**: Use harder task (ambiguous stance)
**Plan B**: Increase label granularity (more than 5 options)

### Issue: Missing Context Data
**Plan A**: Filter to posts with complete context
**Plan B**: Synthesize missing context with LLM

---

## 10. Analysis Plan by Research Question

### RQ1: Context Effects on Accuracy

**Visualizations**:
- Line plot: Accuracy vs. Context Variant (by model)
- Bar plot: Marginal improvements (T→T+C, T+C→FULL, etc.)
- Heatmap: Model × Context variant

**Statistics**:
- One-way ANOVA per model
- Pairwise t-tests with Bonferroni correction
- Effect sizes (Cohen's d)

### RQ2: Context Effects on Calibration

**Visualizations**:
- Calibration curves (confidence vs. accuracy)
- Line plot: ECE vs. Context variant
- Scatter plot: Accuracy vs. ECE (each point = model+context combo)

**Statistics**:
- Pearson correlation between context depth and ECE
- Hosmer-Lemeshow calibration tests

### RQ3: Essential vs. Marginal Context

**Analysis**:
- Compare marginal improvements: MI(T→T+C) vs. MI(T→T+B) vs. MI(T→T+M)
- Identify "elbow point" where diminishing returns begin
- Model-specific comparison

### RQ4: Confidence-Accuracy Alignment

**Analysis**:
- Scatter plot: Accuracy change vs. Confidence change (T to FULL)
- Correlation analysis
- Cases where accuracy ↑ but confidence ↓ (and vice versa)

### RQ5: Model-Specific Patterns

**Analysis**:
- Rank models by: accuracy, calibration, context sensitivity
- Cluster analysis on metric profiles
- Interaction effects (Model × Context)

### RQ6: Context Dimension Interactions

**Analysis**:
- Compare pairs: T+C+B vs. (T+C) + (T+B)
- Additive vs. synergistic improvements
- Interaction terms in linear models

---

## 11. Report Outline

### Main Results Section

1. **Descriptive Statistics**
   - Dataset composition
   - Annotation agreement (κ values)
   - Model inference success rates

2. **RQ1: Accuracy Results**
   - Table: Accuracy by model and context
   - Heatmap visualization
   - Statistical tests and effect sizes

3. **RQ2: Calibration Results**
   - Table: ECE, Brier scores by model and context
   - Calibration curves
   - Overconfidence analysis

4. **RQ3: Essential Context**
   - Marginal improvements analysis
   - Diminishing returns curves
   - Context importance ranking

5. **RQ4–6: Additional Analyses**
   - Confidence-accuracy alignment
   - Model comparison ranking
   - Interaction effects

6. **Error Analysis**
   - 20–30 qualitative cases
   - Patterns of errors
   - Examples where context helps/hurts

### Discussion

1. **Key Findings** (aligned with hypotheses)
2. **Theoretical Implications** for LLM "understanding"
3. **Practical Implications** for applications
4. **Limitations** and future work

---

## 12. Deliverables

1. ✅ **Framework Code** (this repository)
   - Data loading, context generation
   - LLM inference pipeline
   - Metrics computation
   - Visualization

2. **Annotated Dataset** (~10k posts)
   - Posts with stance labels
   - Inter-rater agreement stats

3. **Inference Results** (JSON)
   - LLM responses
   - Extracted confidence
   - Raw outputs

4. **Analysis Report** (PDF)
   - Results tables and figures
   - Statistical tests
   - Qualitative analysis

5. **Python Package** (optional)
   - Installable `llm_context` module
   - Extensible for future work

---

## References

Key papers to review during implementation:

- Kadavath et al. (2022): LLM Calibration
- Lin et al. (2024): Uncertainty in LLMs
- O'Connor et al. (2022): Conversation trees
- SoCkET, LongBench: Context benchmarks

---

**Document Version**: 1.0
**Last Updated**: November 5, 2025
**Status**: Ready for implementation
