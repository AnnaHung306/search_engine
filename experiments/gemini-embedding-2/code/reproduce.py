"""Re-rank the 980 pages and recalculate the three systems' Precision@5."""

import argparse
from collections import defaultdict
import csv
import gzip
from hashlib import file_digest
import json
import math
from pathlib import Path
import sqlite3
from statistics import mean
import sys

from embedding_core import DIMENSIONS, dense_rankings, input_digest, model_inputs


ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ("tfidf", "bm25", "gemini")
K = 5


def sha256(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def read_csv(name):
    with (ROOT / "tables" / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_inputs():
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    for relative, expected in manifest["sha256"].items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"File hash mismatch: {relative}")
    with gzip.open(ROOT / "data" / "embedding-map.json.gz", "rt", encoding="utf-8") as stream:
        return manifest, json.load(stream)


def snapshot_inputs(path, manifest, mapping):
    if sha256(path) != manifest["index_sha256"]:
        raise ValueError("The supplied index is not the original snapshot.")
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        index = json.load(stream)
    if index["collection_sha256"] != manifest["collection_sha256"]:
        raise ValueError("The collection identifier does not match.")
    documents, queries = model_inputs(index, mapping["suites"])
    doc_rows = [[doc_id, offset, input_digest(value)] for doc_id, offset, value in documents]
    query_rows = [[query, input_digest(value)] for query, value in queries.items()]
    if doc_rows != mapping["document_windows"] or query_rows != mapping["queries"]:
        raise ValueError("Inputs reconstructed from the original index differ from the delivered map.")
    return documents, queries


def load_vectors(mapping, path):
    keys = [row[2] for row in mapping["document_windows"]]
    keys.extend(row[1] for row in mapping["queries"])
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro&immutable=1", uri=True) as db:
        raw = dict(db.execute("SELECT digest, vector FROM vectors"))
    if set(raw) != set(keys):
        raise ValueError("Vector keys do not match the document and query inputs.")
    vectors = {key: json.loads(value) for key, value in raw.items()}
    for vector in vectors.values():
        if len(vector) != DIMENSIONS or not math.isclose(math.hypot(*vector), 1, abs_tol=1e-12):
            raise ValueError("A vector has invalid dimensions or is not normalized.")
    return [vectors[key] for key in keys]


def verify_baselines(course_repo, index_path, settings):
    sys.path.insert(0, str(course_repo.resolve() / "code"))
    from search import search

    results = {}
    for row in read_csv("top-five.csv"):
        system = row["system"]
        if system not in settings:
            continue
        key = system, row["query"]
        if key not in results:
            results[key] = search(row["query"], top_k=K, index_path=index_path, **settings[system])["results"]
        actual = results[key][int(row["rank"]) - 1]
        if (int(row["doc_id"]), row["url"]) != (actual["doc_id"], actual["url"]):
            raise ValueError(f"Baseline rank differs: {key}, position {row['rank']}")
    print("TF-IDF and BM25 rankings verified against the original course search code.")


def verify_scores(rankings):
    by_case = defaultdict(list)
    for row in read_csv("top-five.csv"):
        by_case[row["benchmark"], row["group"], row["query_id"], row["system"]].append(row)

    label_index = {}
    judgment_keys = set()
    for row in read_csv("judgments.csv"):
        key = row["benchmark"], row["query_id"], row["url"]
        if key in label_index:
            raise ValueError(f"Duplicate judgment: {key}")
        label_index[key] = row

    cases = read_csv("per-case.csv")
    used = set()
    for case in cases:
        identity = case["benchmark"], case["group"], case["query_id"]
        by_system = {}
        for system in SYSTEMS:
            key = (*identity, system)
            if key in used:
                raise ValueError(f"Duplicate case: {key}")
            used.add(key)
            rows = sorted(by_case[key], key=lambda row: int(row["rank"]))
            if [int(row["rank"]) for row in rows] != list(range(1, K + 1)):
                raise ValueError(f"Expected five ranked results: {key}")
            if len({row["doc_id"] for row in rows}) != K:
                raise ValueError(f"Repeated document: {key}")
            if system == "gemini":
                for saved, actual in zip(rows, rankings[case["query"]][:K], strict=True):
                    if (int(saved["doc_id"]), saved["url"]) != (actual["doc_id"], actual["url"]):
                        raise ValueError(f"Gemini rank differs: {key}")
                    if not math.isclose(float(saved["retrieval_score"]), actual["score"], abs_tol=1e-12):
                        raise ValueError(f"Gemini score differs: {key}")
            values = []
            for row in rows:
                judgment_key = row["benchmark"], row["query_id"], row["url"]
                judgment = label_index[judgment_key]
                judgment_keys.add(judgment_key)
                if row["relevant"] not in ("0", "1") or row["relevant"] != judgment["relevant"]:
                    raise ValueError(f"Judgment differs: {key}")
                if row["label_source"] != judgment["label_source"] or row["doc_id"] != judgment["doc_id"]:
                    raise ValueError(f"Judgment provenance differs: {key}")
                values.append(int(judgment["relevant"]))
            relevant = sum(values)
            if relevant != int(case[f"{system}_relevant"]) or relevant / K != float(case[f"{system}_p_at_5"]):
                raise ValueError(f"Case score differs: {key}")
            by_system[system] = relevant
        yield case, by_system
    if used != by_case.keys() or judgment_keys != label_index.keys():
        raise ValueError("Ranked results or judgments include unexpected rows.")


def verify_summary(scored_cases):
    by_scope = defaultdict(list)
    for case, scores in scored_cases:
        by_scope["all", "all"].append(scores)
        by_scope["benchmark", case["benchmark"]].append(scores)
        by_scope["group", f'{case["benchmark"]}/{case["group"]}'].append(scores)

    summary = read_csv("summary.csv")
    if {(row["scope"], row["name"]) for row in summary} != by_scope.keys():
        raise ValueError("Summary scopes differ from the cases.")
    for row in summary:
        scores = by_scope[row["scope"], row["name"]]
        if len(scores) != int(row["cases"]) or len(scores) * K != int(row["slots_per_system"]):
            raise ValueError(f"Summary size differs: {row['name']}")
        for system in SYSTEMS:
            relevant = sum(case[system] for case in scores)
            if relevant != int(row[f"{system}_relevant"]):
                raise ValueError(f"Summary total differs: {row['name']} {system}")
            if not math.isclose(relevant / (K * len(scores)), float(row[f"{system}_p_at_5"]), abs_tol=1e-8):
                raise ValueError(f"Summary Precision@5 differs: {row['name']} {system}")
        for baseline in ("tfidf", "bm25"):
            differences = [case["gemini"] - case[baseline] for case in scores]
            counts = [sum(diff > 0 for diff in differences), differences.count(0), sum(diff < 0 for diff in differences)]
            expected = [int(row[f"gemini_vs_{baseline}_{name}"]) for name in ("wins", "ties", "losses")]
            if counts != expected:
                raise ValueError(f"Summary outcomes differ: {row['name']} {baseline}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    original = parser.add_mutually_exclusive_group()
    original.add_argument("--index", type=Path, help="Also verify inputs against the original index-v8.1.json.gz.")
    original.add_argument("--course-repo", type=Path, help="Also re-run TF-IDF and BM25 using the original course repository.")
    args = parser.parse_args()
    manifest, mapping = read_inputs()
    index_path = args.course_repo / "data" / "index-v8.1.json.gz" if args.course_repo else args.index
    if index_path:
        snapshot_inputs(index_path, manifest, mapping)
        print("Original snapshot and all input hashes verified.")
    if args.course_repo:
        verify_baselines(args.course_repo, index_path, manifest["baseline_settings"])
    index = {"docs": mapping["documents"]}
    vectors = load_vectors(mapping, ROOT / "data" / "vectors.sqlite")
    rankings = dense_rankings(index, mapping["document_windows"], [row[0] for row in mapping["queries"]], vectors)
    scored_cases = list(verify_scores(rankings))
    verify_summary(scored_cases)
    slots = len(scored_cases) * K
    if len(scored_cases) != manifest["cases"] or len(rankings) != manifest["unique_queries"]:
        raise ValueError("Unexpected number of cases or unique queries.")
    per_query = defaultdict(list)
    for case, scores in scored_cases:
        per_query[case["query"]].append(scores)
    for system in SYSTEMS:
        relevant = sum(scores[system] for _, scores in scored_cases)
        weighted = mean(mean(scores[system] / K for scores in cases) for cases in per_query.values())
        if not math.isclose(weighted, manifest["unique_query_p_at_5"][system], abs_tol=1e-12):
            raise ValueError(f"Unique-query mean differs: {system}")
        print(f"{system}: {relevant}/{slots} = {relevant / slots:.6f}; per unique query = {weighted:.6f}")
    print(f"Verified {len(scored_cases)} cases, {len(rankings)} unique queries, and {slots * len(SYSTEMS)} ranked results.")


if __name__ == "__main__":
    main()
