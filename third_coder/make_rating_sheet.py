"""Build the text-only confidence rating sheet for the third coder.

Reads the text-only (T) rendering of each validated post from the existing coder export
(data/manual/conf_manual.xlsx, column `prompt`), extracts the post text, and writes
data/third_coder/rating_sheet_T.xlsx with the same 283 rows and row order the two other coders
used, so the three files align by row and by sample_id.

Columns the coder fills: ideology, ideology_confidence (0-100), stance, stance_confidence (0-100),
note. The post text is shown without background, conversation, or metadata, exactly as in the T
condition. Output lives under data/, which is gitignored (it carries post text).

Run: uv run --with openpyxl python third_coder/make_rating_sheet.py
"""
import os
import re

import pandas as pd

SRC = "data/manual/conf_manual.xlsx"
OUT_DIR = "data/third_coder"
OUT = os.path.join(OUT_DIR, "rating_sheet_T.xlsx")


def post_text(prompt: str) -> str:
    """The T prompt is: header line, blank, post text, blank, 'ANALYSIS QUESTIONS:' ..."""
    head = "based on ONLY the information provided."
    i = prompt.find(head)
    j = prompt.find("ANALYSIS QUESTIONS")
    if i < 0 or j < 0:
        return prompt
    body = prompt[i + len(head):j].strip()
    body = re.sub(r"</?p>", "", body).strip()
    return body


def main():
    df = pd.read_excel(SRC)
    t = df[df["variant"] == "T"].copy()
    t["post_text"] = t["prompt"].astype(str).map(post_text)
    t["platform"] = t["sample_id"].astype(str).map(lambda s: "bluesky" if s.startswith("at://") else "truthsocial")
    sheet = pd.DataFrame({
        "row": range(1, len(t) + 1),
        "sample_id": t["sample_id"].values,
        "platform": t["platform"].values,
        "post_text": t["post_text"].values,
        "ideology": "",
        "ideology_confidence": "",
        "stance": "",
        "stance_confidence": "",
        "note": "",
    })
    os.makedirs(OUT_DIR, exist_ok=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        sheet.to_excel(xw, index=False, sheet_name="ratings")
        pd.DataFrame({
            "instruction": [
                "Rate each post from its text alone. No background, conversation, or author information is shown, and none should be looked up.",
                "ideology: Left, Center, or Right. If you cannot tell, pick the closest and give a low confidence.",
                "stance (toward Donald Trump): favor, against, neutral, or undecided.",
                "ideology_confidence and stance_confidence: 0 to 100, how confident you are that the label is right given only this text.",
                "Use the whole 0 to 100 range; 0 means a coin flip, 100 means certain.",
                "note: optional, for anything you want to flag.",
                "Work in row order and do not reorder or delete rows; the file is matched to the other coders by row.",
            ]
        }).to_excel(xw, index=False, sheet_name="instructions")
    print(f"wrote {OUT}: {len(sheet)} rows; platforms {sheet['platform'].value_counts().to_dict()}")
    print("empty post_text rows:", int((sheet["post_text"].str.len() == 0).sum()))


if __name__ == "__main__":
    main()
