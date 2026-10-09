# Third-coder kit (camera-ready promise, ARR 2351 reply R2.3)

The response to Reviewer 8FDE promises that the camera-ready adds a third coder's text-only
confidence ratings and recomputes Table 2 against three coders. Two scripts do that.

1. `make_rating_sheet.py` writes `data/third_coder/rating_sheet_T.xlsx`: the 283 validated posts
   that have a text-only rendering, in the same row order the other two coders used, with empty
   columns for ideology, ideology_confidence, stance, stance_confidence, and a note. The second
   sheet carries the instructions. The file holds post text, so it stays under `data/` (gitignored)
   and travels to the coder outside git.
2. `recompute_table2.py` reads the two existing confidence exports and the filled sheet, and
   prints Table 2 (mean confidence, Spearman rho, quadratic-weighted kappa_w per model) against the
   three-coder mean and the rank consensus, plus the three-coder ceiling, writing the full numbers
   to `third_coder/table2_three_coders.json`. With no third sheet it falls back to two coders and
   reproduces the submitted Table 2, which is how it was checked.

Run both with `uv run --with openpyxl --with scikit-learn python third_coder/<script>.py`.
