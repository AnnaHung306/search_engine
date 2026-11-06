"""Reproducible evaluation CLI. TP §6/9; U3 p.9,29–36. See docs/evaluation.md."""
import argparse
import json
import math
import statistics
import time
from pathlib import Path

import search as se
import evaluation as ev

SYSTEMS = ev.SYSTEMS
QUERIES = [(q["query"], q["information_need"], q["relevance_rule"])
           for q in ev.load_suite("course")[0]["queries"]]


def legacy_score():
    labels = {(row["query"], row["url"]): int(row["relevant"])
              for row in ev.read_csv(ev.ROOT / "data/eval_judgments.csv")}
    original_runs = ev.read_csv(ev.ROOT / "data/eval_runs.csv")
    means, differences = {}, []
    for system in list(SYSTEMS)[:6]:
        relevant = 0
        for query, _, _ in QUERIES:
            hits = se.search(query, top_k=5, **SYSTEMS[system])["results"]
            old = [row["url"] for row in original_runs if row["system"] == system and row["query"] == query]
            if old != [hit["url"] for hit in hits]:
                differences.append({"system": system, "query": query})
            for hit in hits:
                key = (query, hit["url"])
                if key not in labels:
                    raise ValueError(f"A changed result is unjudged: {key}")
                relevant += labels[key]
        means[system] = relevant / (5 * len(QUERIES))
    return {"status": "legacy assistant judgments; not independent human validation",
            "mean_precision_at_5": means, "rank_differences_from_v7_1": differences}


def timing(suite, output, repeats):
    if repeats < 1:
        raise ValueError("repeats must be positive")
    queries, suite_hash = ev.load_suite(suite)
    se.load_index()
    summary = {"suite_sha256": suite_hash, "index_sha256": ev.digest(se.INDEX_PATH),
        "boundary": "whole search() call with top-10 plain snippets; excludes initial index load, explanation table, Flask rendering and network; each query warmed once",
        "repeats_per_query": repeats, "systems": {}}
    for system, options in SYSTEMS.items():
        elapsed, per_query = [], {}
        for query in queries["queries"]:
            se.search(query["query"], top_k=10, **options)
            values = []
            for _ in range(repeats):
                started = time.perf_counter()
                se.search(query["query"], top_k=10, **options)
                values.append((time.perf_counter() - started) * 1000)
            elapsed.extend(values)
            per_query[query["id"]] = statistics.median(values)
        ordered = sorted(elapsed)
        summary["systems"][system] = {"mean_ms": statistics.mean(elapsed),
            "median_ms": statistics.median(elapsed), "p95_ms": ordered[math.ceil(len(ordered) * .95) - 1],
            "max_ms": max(elapsed), "median_per_query_ms": per_query}
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "timing.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    for action in ("dump", "score", "timing", "adjudicate", "legacy-score"):
        actions.add_argument("--" + action, action="store_true")
    parser.add_argument("--suite", choices=("course", "development", "holdout"), default="course")
    parser.add_argument("--output", help="separate run directory; export never overwrites a previous run")
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--resolutions", help="explicit adjudication CSV for disagreeing pairs")
    parser.add_argument("--systems", nargs="+", choices=tuple(SYSTEMS),
                        help="explicit system subset for --dump; default is all nine")
    args = parser.parse_args()
    if args.systems is not None and not args.dump:
        parser.error("--systems is used only with --dump")
    output = args.output or ev.ROOT / "data/evaluation/v8" / args.suite
    if args.legacy_score:
        result = legacy_score()
    elif args.dump:
        result = ev.export(args.suite, output, args.systems)
    elif args.timing:
        result = timing(args.suite, output, args.repeats)
    elif args.adjudicate:
        result = ev.adjudicate(output, args.resolutions)
    else:
        result = ev.score(output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
