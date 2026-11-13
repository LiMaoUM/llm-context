# Released validation annotations

`validation_annotations.csv` holds the human annotations behind the paper "When to Trust an LLM
Annotator: Self-Reported Confidence Ranks (but Overstates) Reliability in Political Stance and
Ideology Labeling" (EACL 2027). One row per validated post (295 rows: 218 Truth Social, 77 Bluesky).

| Column | Meaning |
|---|---|
| `post_hash` | salted SHA-256 of the post identifier, first 16 hex characters |
| `platform` | `truthsocial` or `bluesky` |
| `ideology_A`, `ideology_B`, `ideology_C` | each coder's label from the full-context rendering: left, center, right |
| `stance_A`, `stance_B`, `stance_C` | each coder's stance toward Donald Trump: favor, against, none (neutral and undecided folded) |
| `gold_ideology`, `gold_stance` | majority vote of the three coders; empty for three-way splits (6 ideology, 4 stance) |
| `n_agree_ideology`, `n_agree_stance` | number of coders who chose the gold label (3 means unanimous) |
| `text_only_conf_ideology_A`, `text_only_conf_stance_A`, `text_only_conf_ideology_B`, `text_only_conf_stance_B` | coders A and B's own confidence (0 to 100) in judging from the post text alone; 283 posts have a text-only rendering |

The file carries no post text, author handle or platform identifier. `make_release_annotations.py`
builds it from the coder exports, which stay outside the repository.
