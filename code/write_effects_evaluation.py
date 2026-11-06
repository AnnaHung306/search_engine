"""Frozen evaluation for document write effects and excluded sources."""
import argparse
import json
from pathlib import Path

import append_evaluation as previous
import evaluation as ev
import gtfo_functions
import intent_evaluation as comparison
import model_evaluation as judge
import search
import write_effects

OUTPUT = ev.ROOT / "data/evaluation/v8.6-effects"
PLAN = ev.BENCHMARKS / "write-effects-v8.6-plan.json"
QUERIES = ev.BENCHMARKS / "write-effects-v8.6.json"
GROUPS = ("regression", "overwrite", "external", "control")


def prepare(output):
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a fresh comparison directory")
    plan = json.loads(PLAN.read_text())
    hashes = {"new_queries_sha256": ev.digest(QUERIES), "index_sha256": ev.digest(search.INDEX_PATH),
              "effects_sha256": ev.digest(write_effects.DATA),
              "relations_sha256": ev.digest(gtfo_functions.EFFECTS_RELATIONS)}
    if any(plan[key] != sha for key, sha in hashes.items()):
        raise ValueError("Expected frozen v8.6 queries, collection and evidence")
    judge.verify(previous.OUTPUT)
    historical = json.loads((previous.OUTPUT / "queries.json").read_text())["control"]["queries"]
    known = {q["id"]: q for q in historical}
    new = json.loads(QUERIES.read_text())["queries"]
    suites = {"regression": {"queries": [known["app-10"], known["app-11"]], "role": "Known failures"}}
    for name in GROUPS[1:]:
        suites[name] = {"queries": [q for q in new if q["group"] == name],
                        "role": "Predeclared new questions"}
    if sum(len(s["queries"]) for s in suites.values()) != len(new) + 2:
        raise ValueError("Expected declared query groups")
    policy = {"origin": "llm", "rules_fixed_before_labels": True, "comparison": plan["comparison"],
        "global_rule": "Verify the specified source, effect and context on the same actual example. "
                       "For the default semantics of a documented writing command use the GNU Bash "
                       "and coreutils manuals. A documented option on the same example can qualify.",
        "references": ["TP p.3 §6", "U3 p.9,29–38", "https://www.gnu.org/s/coreutils/manual/html_node/tee-invocation.html"]}
    hashes["previous_queries_sha256"] = ev.digest(previous.OUTPUT / "queries.json")
    hashes["plan_sha256"] = ev.digest(PLAN)
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
              comparison.score(args.output, args.adjudications, experiment="write-effects-v8.6", groups=GROUPS))
    print(json.dumps({k: v for k, v in result.items() if k not in ("frozen_artifacts", "evidence_sha256")}, indent=2))
