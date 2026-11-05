"""Frozen experiments, blind-review export and strict P@5. TP §6; U3 p.9,29–36."""
import csv
import hashlib
import html
import json
from collections import defaultdict
from pathlib import Path

import search

ROOT = Path(__file__).resolve().parent.parent
BENCHMARKS = ROOT / "data/benchmarks"
REVIEW_FIELDS = ["pair_id", "query_id", "query", "information_need", "relevance_rule",
                 "doc_id", "url", "title", "relevant", "reason", "reviewer", "review_origin"]
SYSTEMS = {
    "tfidf": {},
    "tfidf_cov": {"coverage": True},
    "tfidf_pivot": {"pivot": 0.2},
    "tfidf_pivot_cov": {"pivot": 0.2, "coverage": True},
    "bm25": {"model": "bm25"},
    "bm25_boost_syn": {"model": "bm25", "title_boost": 0.5, "use_synonyms": True},
    "tfidf_proximity": {"proximity_weight": 0.3},
    "tfidf_fields": {"field_weight": 2.0},
    "tfidf_fields_proximity": {"field_weight": 2.0, "proximity_weight": 0.3},
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fields)
        writer.writeheader()
        writer.writerows(rows)


def load_suite(name):
    freeze = json.loads((BENCHMARKS / "freeze.json").read_text())
    expected = freeze["suites"][name]
    path = BENCHMARKS / expected["file"]
    if digest(path) != expected["sha256"]:
        raise ValueError("Query suite differs from its frozen digest; do not silently change a test set")
    suite = json.loads(path.read_text())
    queries = suite["queries"]
    if (not queries or len(queries) != expected["count"] or
            len({q["query"] for q in queries}) != len(queries) or
            len({q["id"] for q in queries}) != len(queries)):
        raise ValueError("Invalid frozen query suite")
    return suite, expected["sha256"]


def load_manifest(output):
    """Validate the shared display/run metadata before any caller uses fields."""
    manifest = json.loads((Path(output) / "manifest.json").read_text())
    hashes = ("suite_sha256", "index_sha256", "collection_sha256", "systems_sha256",
              "runs_sha256", "review_html_sha256")
    if (not isinstance(manifest, dict) or type(manifest.get("pool_size")) is not int or
            manifest["pool_size"] < 0 or manifest.get("suite") not in ("course", "development", "holdout") or
            not isinstance(manifest.get("systems"), dict) or not manifest["systems"] or
            not all(isinstance(manifest.get(key), str) and len(manifest[key]) == 64 and
                    all(c in "0123456789abcdef" for c in manifest[key]) for key in hashes)):
        raise ValueError("Invalid frozen experiment manifest structure")
    return manifest


def export(name, output, systems=None):
    """One final run per output directory. Never overwrite labels or prior runs."""
    suite, suite_hash = load_suite(name)
    selected = list(SYSTEMS) if systems is None else list(systems)
    if not selected or len(set(selected)) != len(selected) or any(s not in SYSTEMS for s in selected):
        raise ValueError("Choose distinct known systems for this frozen review pool")
    selected_systems = {name: SYSTEMS[name] for name in selected}
    index = search.load_index()
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new output directory; existing runs and human work are preserved")
    output.mkdir(parents=True, exist_ok=True)
    runs, pool = [], {}
    for system, options in selected_systems.items():
        for query in suite["queries"]:
            hits = search.search(query["query"], top_k=5, **options)["results"]
            for rank in range(1, 6):
                hit = hits[rank - 1] if rank <= len(hits) else None
                runs.append({"system": system, "query_id": query["id"], "query": query["query"],
                             "rank": rank, "doc_id": hit["doc_id"] if hit else "",
                             "url": hit["url"] if hit else "", "score": hit["score"] if hit else ""})
                if hit:
                    identity = query["id"] + "\n" + hit["url"]
                    pair_id = hashlib.sha256(identity.encode()).hexdigest()[:20]
                    pool[pair_id] = {"pair_id": pair_id, "query_id": query["id"],
                        "query": query["query"], "information_need": query["information_need"],
                        "relevance_rule": query["relevance_rule"], "doc_id": hit["doc_id"],
                        "url": hit["url"], "title": hit["title"],
                        "relevant": "", "reason": "", "reviewer": "", "review_origin": ""}
    write_csv(output / "runs.csv", runs, list(runs[0]))
    # Pair-id ordering hides rank and producing system from both reviewers.
    rows = [pool[key] for key in sorted(pool)]
    for reviewer in ("a", "b"):
        write_csv(output / f"reviewer-{reviewer}.csv", rows, REVIEW_FIELDS)
    escape = html.escape
    parts = ["<!doctype html><meta charset='utf-8'><title>Blind relevance review</title>",
             "<h1>Blind relevance review</h1><p>Read the full text against the information need; "
             "fill your own CSV with 0/1, reason, your real reviewer name and review_origin=human. Model names and ranks "
             "are intentionally absent. Do not edit the other reviewer’s file.</p>"]
    for row in rows:
        doc = index["docs"][row["doc_id"]]
        parts.append(f"<details id='{row['pair_id']}'><summary>{escape(row['pair_id'])}: "
                     f"{escape(row['query'])} — {escape(row['title'])}</summary>"
                     f"<p>Need: {escape(row['information_need'])}</p>"
                     f"<p>Rule: {escape(row['relevance_rule'])}</p>"
                     f"<p>{escape(row['url'])}</p><pre style='white-space:pre-wrap'>"
                     f"{escape(doc['title'] + chr(10) + doc['description'] + chr(10) + doc['text'])}</pre></details>")
    (output / "review.html").write_text("\n".join(parts), encoding="utf-8")
    manifest = {"suite": name, "suite_sha256": suite_hash,
                "index_sha256": digest(search.INDEX_PATH), "collection_sha256": index["collection_sha256"],
                "systems": selected_systems, "systems_sha256": hashlib.sha256(json.dumps(
                    selected_systems, sort_keys=True).encode()).hexdigest(),
                "code_sha256": {p.name: digest(p) for p in sorted((ROOT / "code").glob("*.py"))},
                "runs_sha256": digest(output / "runs.csv"),
                "review_html_sha256": digest(output / "review.html"),
                "pool_size": len(rows), "human_review": "pending; no final P@5 available"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _labels(path):
    rows = read_csv(path)
    labels = {}
    invalid = []
    for row in rows:
        key = (row["query_id"], row["url"])
        row["relevant"] = row.get("relevant", "").strip()
        reviewer = row.get("reviewer", "").strip()
        if (key in labels or row["relevant"] not in ("0", "1") or not reviewer or
                not row.get("reason", "").strip() or row.get("review_origin", "").strip() != "human"):
            invalid.append(row.get("pair_id", str(key)))
        row["reviewer"], row["review_origin"] = reviewer, row.get("review_origin", "").strip()
        labels[key] = row
    if invalid:
        raise ValueError(f"{len(invalid)} incomplete/invalid judgments in {Path(path).name}; "
                         f"need 0/1, reason, human reviewer and review_origin=human. First IDs: {invalid[:5]}")
    return labels


def _verified_run(output):
    manifest = load_manifest(output)
    if digest(output / "runs.csv") != manifest["runs_sha256"]:
        raise ValueError("Run file changed after freezing")
    if digest(output / "review.html") != manifest["review_html_sha256"]:
        raise ValueError("The full-text review material changed after freezing")
    suite, suite_hash = load_suite(manifest["suite"])
    if suite_hash != manifest["suite_sha256"]:
        raise ValueError("Suite mismatch")
    if hashlib.sha256(json.dumps(manifest["systems"], sort_keys=True).encode()).hexdigest() != manifest["systems_sha256"]:
        raise ValueError("System settings changed after freezing")
    return manifest, suite, read_csv(output / "runs.csv")


def displayed_score(output, collection_sha256=None):
    """Explicit pending/current/stale states; never display an old score as current."""
    output = Path(output)
    try:
        manifest = load_manifest(output)
    except FileNotFoundError:
        return None, "pending"
    except ValueError:
        return None, "stale"
    if collection_sha256 is not None and manifest["collection_sha256"] != collection_sha256:
        return None, "different_collection"
    if not (output / "scores.json").exists():
        return None, "pending"
    try:
        _verified_run(output)
        summary = json.loads((output / "scores.json").read_text())
        if not all((output / name).exists() and digest(output / name) == expected
                   for name, expected in summary["evidence_sha256"].items()):
            return None, "stale"
    except (ValueError, KeyError, FileNotFoundError):
        return None, "stale"
    return summary["mean_precision_at_5"], "current"


def adjudicate(output, resolutions=None):
    output = Path(output)
    _, _, runs = _verified_run(output)
    expected_pairs = {(r["query_id"], r["url"]) for r in runs if r["url"]}
    a, b = (_labels(output / f"reviewer-{reviewer}.csv") for reviewer in ("a", "b"))
    if set(a) != expected_pairs or set(b) != expected_pairs:
        raise ValueError("Both reviewers must label exactly the frozen result pool")
    if {row["reviewer"].strip().casefold() for row in a.values()} & {row["reviewer"].strip().casefold() for row in b.values()}:
        raise ValueError("The two reviewers must be independent people")
    resolved = _labels(resolutions) if resolutions else {}
    disagreement_keys = {key for key in a if a[key]["relevant"] != b[key]["relevant"]}
    if set(resolved) - disagreement_keys:
        raise ValueError("Resolution file contains a pair without a reviewer disagreement")
    missing = disagreement_keys - set(resolved)
    if missing:
        raise ValueError(f"{len(missing)} disagreements need explicit adjudication: {sorted(missing)[:5]}")
    disagreements, final = [], []
    for key in a:
        if a[key]["relevant"] == b[key]["relevant"]:
            row = dict(a[key])
            row["reviewer"] = a[key]["reviewer"] + " + " + b[key]["reviewer"]
            row["reason"] = a[key]["reason"] + " | " + b[key]["reason"]
        elif key in resolved:
            row = resolved[key]
            disagreements.append(key)
        else:
            raise ValueError(f"Disagreement needs explicit adjudication: {key}")
        final.append(row)
    total = len(a)
    observed = sum(a[k]["relevant"] == b[k]["relevant"] for k in a) / total if total else None
    pa = sum(r["relevant"] == "1" for r in a.values()) / total if total else None
    pb = sum(r["relevant"] == "1" for r in b.values()) / total if total else None
    expected = pa * pb + (1 - pa) * (1 - pb) if total else None
    agreement = {"pairs": total, "agreement": observed, "expected_by_chance": expected,
                 "kappa": (observed - expected) / (1 - expected) if total and expected < 1 else None,
                 "kappa_note": "undefined for empty or constant-category judgments" if not total or expected == 1 else "",
                 "adjudicated_pairs": len(disagreements)}
    write_csv(output / "consensus.csv", final, REVIEW_FIELDS)
    (output / "agreement.json").write_text(json.dumps(agreement, indent=2))
    return agreement


def precision_at_five(runs, queries, systems, labels):
    """Shared arithmetic only; callers must validate judgment provenance first."""
    groups = defaultdict(list)
    for run in runs:
        groups[(run["system"], run["query_id"])].append(run)
    expected = {(system, query["id"]) for system in systems for query in queries}
    if not queries or not systems or len({q["id"] for q in queries}) != len(queries) or set(groups) != expected:
        raise ValueError("Run must contain exactly the declared query/system groups")
    results = []
    totals = defaultdict(int)
    for system in systems:
        for query in queries:
            rows = groups[(system, query["id"])]
            if sorted(int(row["rank"]) for row in rows) != [1, 2, 3, 4, 5]:
                raise ValueError("Each query/system must have five distinct rank positions")
            relevant = 0
            for row in rows:
                if row["url"]:
                    key = (query["id"], row["url"])
                    if key not in labels:
                        raise ValueError(f"Unjudged result; scoring stopped: {key}")
                    label = labels[key]
                    if type(label) is not int or label not in (0, 1):
                        raise ValueError("Relevance must be binary 0/1")
                    relevant += label
            results.append({"system": system, "query_id": query["id"],
                            "query": query["query"], "precision_at_5": relevant / 5})
            totals[system] += relevant
    means = {system: totals[system] / (5 * len(queries)) for system in systems}
    return results, means


def score(output):
    output = Path(output)
    manifest, suite, runs = _verified_run(output)
    # Consensus must be produced from both current independent reviewer files.
    adjudicate(output, output / "resolutions.csv" if (output / "resolutions.csv").exists() else None)
    labels = {key: int(row["relevant"]) for key, row in _labels(output / "consensus.csv").items()}
    results, means = precision_at_five(runs, suite["queries"], manifest["systems"], labels)
    write_csv(output / "scores.csv", results, list(results[0]))
    summary = {"mean_precision_at_5": means, "denominator": 5,
               "query_count": len(suite["queries"]),
               "evidence_sha256": {name: digest(output / name) for name in
                   ("consensus.csv", "reviewer-a.csv", "reviewer-b.csv", "runs.csv", "manifest.json")}}
    if (output / "resolutions.csv").exists():
        summary["evidence_sha256"]["resolutions.csv"] = digest(output / "resolutions.csv")
    (output / "scores.json").write_text(json.dumps(summary, indent=2))
    return summary
