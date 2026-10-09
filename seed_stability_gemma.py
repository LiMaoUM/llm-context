import multiprocessing as mp, os
if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
import json, re
import pandas as pd
from seed_stability_check import parse_response, RESULTS_DIR, SEEDS

def main():
    sheng = pd.read_excel("data/manual/manual_Shengteng.xlsx")
    gold_ids = set(sheng[sheng["variant"] == "T+B+C+M"]["sample_id"])
    from vllm import LLM, SamplingParams
    model_name, model_id = "gemma-3-27b-it", "google/gemma-3-27b-it"
    df = pd.read_json(os.path.join(RESULTS_DIR, f"{model_name}_responses.jsonl"), lines=True)
    df = df[df["sample_id"].isin(gold_ids)].drop_duplicates(["sample_id", "variant"])
    prompts = df["prompt"].tolist(); keys = list(zip(df["sample_id"], df["variant"]))
    print(f"{model_name}: {len(prompts)} prompts")
    llm = LLM(model=model_id, tensor_parallel_size=2, gpu_memory_utilization=0.85,
              max_model_len=20000, dtype="auto")
    recs = []
    for seed in SEEDS:
        sp = SamplingParams(temperature=0.7, top_p=0.9, max_tokens=1024, seed=seed)
        outs = llm.generate(prompts, sp)
        for (sid, var), o in zip(keys, outs):
            ideo, st, ic, sc = parse_response(o.outputs[0].text)
            recs.append({"sample_id": sid, "variant": var, "seed": seed,
                         "ideology": ideo, "stance": st, "ideo_conf": ic, "stance_conf": sc})
    pd.DataFrame(recs).to_json(f"seed_stability_{model_name}.jsonl", orient="records", lines=True)
    print("done")

if __name__ == "__main__":
    main()
