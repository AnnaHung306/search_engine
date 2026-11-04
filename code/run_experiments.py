"""run_experiments.py — run the 10 frozen queries under each ranking variant
and save top-5 per variant to experiments/<name>.json for before/after comparison."""
import json, os
import search as se
import evaluate as ev

OUT = os.path.join(os.path.dirname(__file__), "..", "experiments")
os.makedirs(OUT, exist_ok=True)

VARIANTS = {
    "v0b_tfidf_rerun":       ("tfidf", 0.0),
    "v2_bm25":               ("bm25", 0.0),
    "v3_bm25_title":         ("bm25", 0.5),   # multiplicative title boost
}
# v4 (= v3 + synonyms) is the default in search.py; run_experiments turns
# synonyms OFF for v0b-v3 so those stay comparable. See v4_bm25_title_synonyms.json
# (v1 additive title boost was a failed experiment; its results are kept in
#  experiments/v1_tfidf_title_additive.json)

def run(name, model, boost):
    res, times = {}, []
    for q, _, _ in ev.QUERIES:
        r = se.search(q, top_k=5, model=model, title_boost=boost, use_synonyms=False)
        times.append(r["elapsed_ms"])
        res[q] = [(h["url"].replace("https://", ""), h["score"]) for h in r["results"]]
    json.dump({"model": model, "title_boost": boost, "avg_ms": sum(times)/len(times),
               "results": res}, open(os.path.join(OUT, name + ".json"), "w"), indent=1)
    return res, sum(times)/len(times)

if __name__ == "__main__":
    for name, (model, boost) in VARIANTS.items():
        res, ms = run(name, model, boost)
        print(f"===== {name} (model={model}, title_boost={boost}) avg {ms:.1f} ms")
        for q, v in res.items():
            print("##", q)
            for i, (u, s) in enumerate(v, 1):
                print(f"   {i}. {s:.3f} {u}")
