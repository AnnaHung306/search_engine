"""Frozen v8.3 comparison; known failures and new queries stay separate."""
import argparse
import json
from pathlib import Path

import evaluation as ev
import model_evaluation as judge
import search


OUTPUT = ev.ROOT / "data/evaluation/v8.3-intent"
PLAN = ev.BENCHMARKS / "intent-v8.3-plan.json"
NEW_QUERIES = ev.BENCHMARKS / "intent-v8.3.json"


def prepare(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a fresh directory for a new comparison")
    previous = judge.verify(judge.OUTPUT)
    if previous["index_sha256"] != ev.digest(search.INDEX_PATH):
        raise ValueError("Use the exact v8.2 index snapshot for this comparison")
    plan = json.loads(PLAN.read_text())
    if ev.digest(NEW_QUERIES) != plan["new_queries_sha256"]:
        raise ValueError("Frozen v8.3 queries changed")
    new = json.loads(NEW_QUERIES.read_text())["queries"]
    old = json.loads((judge.OUTPUT / "queries.json").read_text())["holdout"]["queries"]
    by_id = {q["id"]: q for q in old}
    suites = {"regression": {"queries": [by_id[q] for q in plan["regression_ids"]],
                             "role": "Known failures used for diagnosis, not held out"}}
    for group in ("source", "native", "control"):
        suites[group] = {"queries": [q for q in new if q["group"] == group],
                         "role": "New, predeclared targeted or control queries"}
    all_queries = [q for suite in suites.values() for q in suite["queries"]]
    if (len(all_queries) != len(new) + len(plan["regression_ids"]) or
            len({q["id"] for q in all_queries}) != len(all_queries) or
            len({q["query"] for q in all_queries}) != len(all_queries)):
        raise ValueError("Query groups must cover distinct frozen questions")
    output.mkdir(parents=True, exist_ok=True)
    (output / "plan.json").write_bytes(PLAN.read_bytes())
    judge.write_json(output / "implementation.json", {
        p.name: ev.digest(p) for p in sorted((ev.ROOT / "code").glob("*.py"))})
    for name, suite in suites.items():
        (output / name).mkdir()
        rows = ev.retrieval_runs(suite["queries"], plan["systems"])
        ev.write_csv(output / name / "runs.csv", rows, list(rows[0]))
    policy = {"origin": "llm", "rules_fixed_before_labels": True,
        "comparison": plan["comparison"], "model_settings_frozen_in": "plan.json",
        "aggregation": "Any positive segment establishes relevance; all segments required; missing labels fail.",
        "global_rule": "Judge the stated information need using substantive text, not mere term co-occurrence.",
        "references": ["TP p.3 §6", "Unit 3 p.9,29–38", "https://arxiv.org/abs/2309.10621"]}
    return judge.freeze_inputs(output, suites, plan["systems"], policy,
        {"v8.2_queries_sha256": ev.digest(judge.OUTPUT / "queries.json"),
         "new_queries_sha256": ev.digest(NEW_QUERIES), "plan_sha256": ev.digest(PLAN)})


def score(output, adjudications=None):
    output = Path(output)
    frozen = judge.verify(output)
    if not {"plan.json", "implementation.json"} <= set(frozen["frozen_artifacts"]):
        raise ValueError("Score requires a frozen intent experiment; no files were written")
    suites = json.loads((output / "queries.json").read_text())
    plan = json.loads((output / "plan.json").read_text())
    if (set(suites) != {"regression", "source", "native", "control"} or
            any(not isinstance(plan.get(k), str) or plan[k] not in frozen["systems"]
                for k in ("baseline", "candidate")) or
            plan["baseline"] == plan["candidate"]):
        raise ValueError("Intent plan, systems or suite groups do not match")
    if adjudications is None and (output / "adjudications.json").is_file():
        raise ValueError("Pass --adjudications explicitly to preserve the reviewed result")
    manifest, raw, evidence = judge.collect(output)
    final, corrections = raw, 0
    if adjudications:
        path = Path(adjudications).resolve()
        if not path.is_relative_to(output.resolve()):
            raise ValueError("Keep explicit self-review inside this experiment")
        # A self-review is tied to a previously scored, unchanged first pass.
        if ev.read_csv(output / "raw_llm_judgments.csv") != [{k: str(v) for k, v in row.items()} for row in raw]:
            raise ValueError("Saved raw judgments do not match the original model responses")
        final, corrections = judge._adjudicate(output, raw, path)
        evidence[str(path.relative_to(output.resolve()))] = ev.digest(path)
    labels = {(row["query_id"], row["url"]): row["relevant"] for row in final}
    means, outcomes, tables, new_rows = {}, {}, {}, []
    for name, suite in suites.items():
        runs = ev.read_csv(output / name / "runs.csv")
        rows, means[name] = ev.precision_at_five(runs, suite["queries"], manifest["systems"], labels)
        tables[name] = rows
        per_query = {(r["system"], r["query_id"]): r["precision_at_5"] for r in rows}
        delta = [per_query[plan["candidate"], q["id"]] - per_query[plan["baseline"], q["id"]]
                 for q in suite["queries"]]
        outcomes[name] = {"wins": sum(v > 0 for v in delta), "ties": sum(v == 0 for v in delta),
                          "losses": sum(v < 0 for v in delta)}
        if name != "regression":
            new_rows.extend(rows)
    ev.write_csv(output / "raw_llm_judgments.csv", raw, list(raw[0]))
    ev.write_csv(output / "llm_judgments.csv", final, list(final[0]))
    for name, rows in tables.items():
        path = output / name / "scores.csv"
        ev.write_csv(path, rows, list(rows[0]))
        evidence[name + "/scores.csv"] = ev.digest(path)
    evidence.update(manifest["frozen_artifacts"])
    for name in ("manifest.json", "raw_llm_judgments.csv", "llm_judgments.csv"):
        evidence[name] = ev.digest(output / name)
    new_count = sum(len(s["queries"]) for k, s in suites.items() if k != "regression")
    summary = {"origin": "llm", "collection_sha256": manifest["collection_sha256"], "denominator": 5,
        "pair_count": len(final), "document_count": manifest["document_count"], "self_review_corrections": corrections,
        "mean_precision_at_5": means, "candidate_vs_baseline": outcomes,
        "new_query_count": new_count,
        "new_mean_precision_at_5": {s: sum(round(r["precision_at_5"] * 5) for r in new_rows if r["system"] == s)
                                   / (5 * new_count) for s in manifest["systems"]},
        "comparison": plan["comparison"], "evidence_sha256": evidence}
    judge.write_json(output / "scores.json", summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "score"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--adjudications", type=Path)
    args = parser.parse_args()
    if args.adjudications and args.action != "score":
        parser.error("--adjudications applies only to score")
    result = prepare(args.output) if args.action == "prepare" else score(args.output, args.adjudications)
    print(json.dumps({k: v for k, v in result.items() if k not in ("frozen_artifacts", "evidence_sha256")}, indent=2))
