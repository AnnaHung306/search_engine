"""Frozen evaluation of GTFOBins executable function-context retrieval."""
import argparse
import json
from pathlib import Path

import evaluation as ev
import gtfo_functions
import intent_evaluation as comparison
import model_evaluation as judge
import search

OUTPUT = ev.ROOT / "data/evaluation/v8.4-gtfo"
PLAN = ev.BENCHMARKS / "gtfo-v8.4-plan.json"
QUERIES = ev.BENCHMARKS / "gtfo-v8.4.json"
GROUPS = ("regression", "reverse", "write", "binding", "control")


def prepare(output):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a fresh comparison directory")
    plan = json.loads(PLAN.read_text())
    inputs = {"new_queries_sha256": ev.digest(QUERIES),
              "relations_sha256": ev.digest(gtfo_functions.RELATIONS)}
    if any(plan[key] != sha for key, sha in inputs.items()):
        raise ValueError("Frozen queries or relation evidence changed")
    previous = judge.verify(comparison.OUTPUT)
    if previous["index_sha256"] != ev.digest(search.INDEX_PATH):
        raise ValueError("Use the original frozen v8.3 index")
    historical = json.loads((comparison.OUTPUT / "queries.json").read_text())
    known = {q["id"]: q for suite in historical.values() for q in suite["queries"]}
    old = [known[qid] for qid in plan["regression_ids"]]
    new = json.loads(QUERIES.read_text())["queries"]
    suites = {"regression": {"queries": old, "role": "Known v8.3 failures"}}
    for name in GROUPS[1:]:
        suites[name] = {"queries": [q for q in new if q["group"] == name],
                        "role": "Predeclared new queries"}
    all_queries = [q for suite in suites.values() for q in suite["queries"]]
    if (len(all_queries) != len(old) + len(new) or
            len({q["id"] for q in all_queries}) != len(all_queries) or
            len({q["query"] for q in all_queries}) != len(all_queries)):
        raise ValueError("Expected distinct questions in the declared groups")
    policy = {"origin": "llm", "rules_fixed_before_labels": True,
              "comparison": plan["comparison"],
              "global_rule": "A function must actually satisfy the need in the requested context. "
                             "Do not infer an operation from a heading or unrelated context.",
              "references": ["TP p.3 §6", "U3 p.9,29–38", "https://gtfobins.org/contributing/"]}
    inputs["v8.3_queries_sha256"] = ev.digest(comparison.OUTPUT / "queries.json")
    inputs["plan_sha256"] = ev.digest(PLAN)
    return comparison.freeze_comparison(output, PLAN, plan, suites, policy, inputs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "score"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--adjudications", type=Path)
    args = parser.parse_args()
    if args.adjudications and args.action != "score":
        parser.error("--adjudications applies only to score")
    result = (prepare(args.output) if args.action == "prepare" else
              comparison.score(args.output, args.adjudications, experiment="gtfo-v8.4", groups=GROUPS))
    print(json.dumps({k: v for k, v in result.items() if k not in ("frozen_artifacts", "evidence_sha256")}, indent=2))
