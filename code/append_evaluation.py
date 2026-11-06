"""Evaluate append ranking on the frozen 983-page collection."""
import argparse
import json
from pathlib import Path

import evaluation as ev
import gtfo_evaluation
import gtfo_functions
import intent_evaluation as comparison
import model_evaluation as judge
import search

OUTPUT = ev.ROOT / "data/evaluation/v8.5-append"
PLAN = ev.BENCHMARKS / "append-v8.5-plan.json"
QUERIES = ev.BENCHMARKS / "append-v8.5.json"
GROUPS = ("regression", "append", "context", "control")


def prepare(output):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a fresh comparison directory")
    plan = json.loads(PLAN.read_text())
    hashes = {"new_queries_sha256": ev.digest(QUERIES), "index_sha256": ev.digest(search.INDEX_PATH),
              "relations_sha256": ev.digest(gtfo_functions.APPEND_RELATIONS)}
    if any(plan[key] != value for key, value in hashes.items()):
        raise ValueError("Use the frozen v8.5 index, queries and append evidence")
    judge.verify(gtfo_evaluation.OUTPUT)
    previous = json.loads((gtfo_evaluation.OUTPUT / "queries.json").read_text())
    known = next(q for q in previous["write"]["queries"] if q["id"] == "gtfo-08")
    new = json.loads(QUERIES.read_text())["queries"]
    suites = {"regression": {"queries": [known], "role": "Known failure"}}
    for group in GROUPS[1:]:
        suites[group] = {"queries": [q for q in new if q["group"] == group],
                         "role": "Predeclared new questions"}
    if sum(len(s["queries"]) for s in suites.values()) != 1 + len(new):
        raise ValueError("Expected declared query groups")
    hashes["previous_queries_sha256"] = ev.digest(gtfo_evaluation.OUTPUT / "queries.json")
    hashes["plan_sha256"] = ev.digest(PLAN)
    policy = {"origin": "llm", "rules_fixed_before_labels": True, "comparison": plan["comparison"],
        "global_rule": "Require actual append semantics and the requested context in one example. "
                       "A documented append option attached to the same example qualifies.",
        "references": ["TP p.3 §6", "U3 p.9,29–38", "https://gtfobins.org/contributing/"]}
    return comparison.freeze_comparison(output, PLAN, plan, suites, policy, hashes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "score"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--adjudications", type=Path)
    args = parser.parse_args()
    if args.adjudications and args.action != "score":
        parser.error("--adjudications applies only to score")
    result = (prepare(args.output) if args.action == "prepare" else
              comparison.score(args.output, args.adjudications, experiment="append-v8.5", groups=GROUPS))
    print(json.dumps({k: v for k, v in result.items() if k not in ("frozen_artifacts", "evidence_sha256")}, indent=2))
