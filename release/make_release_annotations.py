"""Build the public validation-annotation file for the EACL 2027 camera-ready.

Reads the coder exports under data/manual/ (post text, kept out of git) and writes
release/validation_annotations.csv: one row per validated post, keyed to a salted
SHA-256 of the post identifier, with each coder's folded labels, the majority-vote
gold labels, the number of coders agreeing, and the two coders' text-only confidence
ratings. No post text, author handle or raw identifier is written.

The salt lives in release/.salt (gitignored) so the hash cannot be rebuilt from
public post identifiers. Coders are labelled A, B, C.

Run: uv run --with openpyxl python release/make_release_annotations.py
"""
import hashlib
import secrets
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
SALT_FILE = HERE / ".salt"
if not SALT_FILE.exists():
    SALT_FILE.write_text(secrets.token_hex(32))
    SALT_FILE.chmod(0o600)
SALT = SALT_FILE.read_text().strip()


def post_hash(sample_id):
    return hashlib.sha256((SALT + str(sample_id)).encode()).hexdigest()[:16]


def norm_label(x, task):
    """Same folding as revision_analysis.py; stance 'none' is the folded neutral/undecided class."""
    if pd.isna(x):
        return np.nan
    x = str(x).strip().lower()
    if task == "ideology":
        if x in ("left", "center", "right"):
            return x
        if x in ("undecided", "unclear", "unknown"):
            return "center"
    else:
        if x in ("favor", "favoue", "favour"):
            return "favor"
        if x == "against":
            return "against"
        if x in ("neutral", "undecided", "center", "unclear"):
            return "none"
    return np.nan


base = pd.read_excel("data/manual/manual_Shengteng.xlsx")
a = pd.read_csv("data/manual/manual_qing.csv")
b = pd.read_csv("data/manual/manual_Xinyu.csv")
a["sample_id"] = base["sample_id"]
b["sample_id"] = base["sample_id"]

out = None
for name, df, icol, scol in [("A", a, "Ideology", "Stance"), ("B", b, "ideology", "stance"), ("C", base, "ideology", "stance")]:
    d = df[df["variant"] == "T+B+C+M"][["sample_id", icol, scol]].copy()
    d.columns = ["sample_id", f"ideology_{name}", f"stance_{name}"]
    d[f"ideology_{name}"] = d[f"ideology_{name}"].apply(lambda v: norm_label(v, "ideology"))
    d[f"stance_{name}"] = d[f"stance_{name}"].apply(lambda v: norm_label(v, "stance"))
    out = d if out is None else out.merge(d, on="sample_id", how="left")

for task in ("ideology", "stance"):
    gold, agree = [], []
    for _, r in out.iterrows():
        votes = [r[f"{task}_{c}"] for c in "ABC" if pd.notna(r[f"{task}_{c}"])]
        vc = pd.Series(votes).value_counts()
        if len(vc) and vc.iloc[0] >= 2:
            gold.append(vc.index[0])
            agree.append(int(vc.iloc[0]))
        else:
            gold.append(np.nan)
            agree.append(1 if len(vc) else 0)
    out[f"gold_{task}"] = gold
    out[f"n_agree_{task}"] = agree

# text-only confidence sub-study (coders A and B)
ca = pd.read_excel("data/manual/conf_manual.xlsx")
cb = pd.read_csv("data/manual/conf_manual_Xinyu_1.14.csv")
ca.columns = [c.strip().lower().replace(" ", "_") for c in ca.columns]
cb.columns = [c.strip().lower() for c in cb.columns]
# the exports are row-aligned with the label export; take identifiers from it (as third_coder/recompute_table2.py does)
ca["sample_id"] = base["sample_id"].values
cb["sample_id"] = base["sample_id"].values
ca = ca[ca["variant"] == "T"][["sample_id", "ideology_confidence", "stance_confidence"]].rename(
    columns={"ideology_confidence": "text_only_conf_ideology_A", "stance_confidence": "text_only_conf_stance_A"})
cb = cb[cb["variant"] == "T"][["sample_id", "confidence", "confidence.1"]].rename(
    columns={"confidence": "text_only_conf_ideology_B", "confidence.1": "text_only_conf_stance_B"})
out = out.merge(ca, on="sample_id", how="left").merge(cb, on="sample_id", how="left")

out["platform"] = np.where(out["sample_id"].astype(str).str.startswith("at://"), "bluesky", "truthsocial")
out.insert(0, "post_hash", out["sample_id"].map(post_hash))
assert out["post_hash"].is_unique
out = out.drop(columns=["sample_id"]).sort_values("post_hash")
cols = ["post_hash", "platform"] + [c for c in out.columns if c not in ("post_hash", "platform")]
out[cols].to_csv(HERE / "validation_annotations.csv", index=False)

print("rows", len(out))
print("gold ideology", out["gold_ideology"].notna().sum(), "unanimous", (out["n_agree_ideology"] == 3).sum())
print("gold stance", out["gold_stance"].notna().sum(), "unanimous", (out["n_agree_stance"] == 3).sum())
print("text-only confidence rows", out["text_only_conf_ideology_A"].notna().sum(), out["text_only_conf_ideology_B"].notna().sum())
print(out.groupby("platform").size().to_dict())
