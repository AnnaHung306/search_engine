"""Descriptive ranking diagnostics, never relevance judgments. TP §6; U3/U4.

Course/development only: the holdout is reserved for a final human evaluation.
This report cannot establish that a longer document or changed ranking is better.
"""
import argparse
import json
import statistics
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

import evaluation as ev
import search


def analyze(suite_name):
    if suite_name not in ("course", "development"):
        raise ValueError("Diagnostics are limited to course/development; holdout is reserved")
    suite, suite_hash = ev.load_suite(suite_name)
    index = search.load_index()
    records, summaries = [], {}
    for query in suite["queries"]:
        baseline = {h["url"] for h in search.search(query["query"], top_k=5)["results"]}
        for system, options in ev.SYSTEMS.items():
            response = search.search(query["query"], top_k=5, **options)
            hits = [{"rank": rank, "doc_id": h["doc_id"], "url": h["url"],
                     "title": h["title"], "score": h["score"],
                     "document_tokens": index["doc_len"][h["doc_id"]],
                     "matched": h["matched"], "missing": h["missing"]}
                    for rank, h in enumerate(response["results"], 1)]
            urls = {h["url"] for h in hits}
            records.append({"query_id": query["id"], "query": query["query"],
                "information_need": query["information_need"], "relevance_rule": query["relevance_rule"],
                "system": system, "baseline_overlap_count": len(urls & baseline),
                "baseline_jaccard": len(urls & baseline) / len(urls | baseline) if urls | baseline else None,
                "hits": hits})
    for system in ev.SYSTEMS:
        selected = [r for r in records if r["system"] == system]
        hits = [h for r in selected for h in r["hits"]]
        overlap = [r["baseline_jaccard"] for r in selected if r["baseline_jaccard"] is not None]
        summaries[system] = {"returned_positions": len(hits),
            "median_document_tokens": statistics.median(h["document_tokens"] for h in hits) if hits else None,
            "mean_baseline_jaccard": statistics.mean(overlap) if overlap else None,
            "host_counts": dict(Counter(urlsplit(h["url"]).netloc for h in hits))}
    return {"status": "descriptive diagnostics only; no new relevance labels or quality scores",
            "suite": suite_name, "suite_sha256": suite_hash,
            "collection_sha256": index["collection_sha256"], "index_sha256": ev.digest(search.INDEX_PATH),
            "systems": ev.SYSTEMS, "code_sha256": {p.name: ev.digest(p) for p in sorted((ev.ROOT / "code").glob("*.py"))},
            "summaries": summaries, "queries": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("course", "development"), default="development")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    destination = Path(args.output)
    if destination.exists():
        raise FileExistsError("Choose a new diagnostic output; previous evidence is preserved")
    result = analyze(args.suite)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summaries"], indent=2))
