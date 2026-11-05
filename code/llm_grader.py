"""Stateless structured model inference through the user's authenticated CLI.

No shell/apps/browser/plugins/subagent tools are enabled for the classifier.
Full source inputs, raw events and validated responses remain auditable.
"""
import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import evaluation as ev
import model_evaluation as me


def _save_attempt(output, batch_id, stdout, stderr):
    raw_path = output / "raw" / (batch_id + ".jsonl")
    stderr_path = output / "raw" / (batch_id + ".stderr.txt")
    for path in (raw_path, stderr_path):
        if path.exists():
            path.rename(path.with_name(path.stem + ".prior-" + str(time.time_ns()) + path.suffix))
    raw_path.write_bytes(stdout.encode("utf-8") if isinstance(stdout, str) else stdout or b"")
    stderr_path.write_bytes(stderr.encode("utf-8") if isinstance(stderr, str) else stderr or b"")
    return raw_path


def grade_one(output, batch_path):
    batch = json.loads(batch_path.read_text())
    result_path = output / "responses" / batch_path.name
    if result_path.exists():
        record = json.loads(result_path.read_text())
        if record["input_sha256"] != ev.digest(batch_path):
            raise ValueError("Completed model response belongs to different input")
        me.validate_decisions(batch, record["result"])
        return batch_path.stem, "verified existing response"
    prompt = (output / "prompt.txt").read_text() + "\nSOURCE DATA:\n" + batch_path.read_text()
    command = ["codex", "exec", "--ephemeral", "--ignore-user-config", "--skip-git-repo-check",
               "--sandbox", "read-only", "--cd", "/tmp", "--json", "--color", "never",
               "--output-schema", str((output / "schema.json").resolve())]
    for feature in ("shell_tool", "apps", "plugins", "multi_agent", "browser_use", "computer_use", "memories", "chronicle"):
        command.extend(("--disable", feature))
    command.append("-")
    started = time.time()
    try:
        process = subprocess.run(command, input=prompt, text=True, capture_output=True, timeout=480)
    except subprocess.TimeoutExpired as error:
        raw_path = _save_attempt(output, batch_path.stem, error.stdout, error.stderr)
        me.write_json(output / "raw" / (batch_path.stem + ".timeout-" + str(time.time_ns()) + ".json"),
                      {"status": "timeout", "started_at": started, "finished_at": time.time(),
                       "input_sha256": ev.digest(batch_path), "partial_stdout_sha256": ev.digest(raw_path)})
        raise
    raw_path = _save_attempt(output, batch_path.stem, process.stdout, process.stderr)
    if process.returncode:
        raise RuntimeError(f"Classifier batch {batch_path.stem} failed; see retained raw output")
    result = me.parse_trace(process.stdout)
    me.validate_decisions(batch, result)
    record = {"review_origin": "llm", "evaluator": "Codex CLI default model; exact identifier not exposed by JSON events",
        "input_sha256": ev.digest(batch_path), "policy_sha256": ev.digest(output / "policy.json"),
        "prompt_sha256": ev.digest(output / "prompt.txt"), "schema_sha256": ev.digest(output / "schema.json"),
        "raw_events_sha256": ev.digest(raw_path), "started_at": started, "finished_at": time.time(),
        "command": command, "result": result}
    me.write_json(result_path, record)
    return batch_path.stem, f"{len(result['decisions'])} model decisions validated"


def run(output=me.OUTPUT, limit=None, workers=2):
    output = Path(output).resolve()
    me.verify(output)
    if not 1 <= workers <= 2:
        raise ValueError("Use one or two structured classifier requests at once")
    for directory in ("responses", "raw"):
        (output / directory).mkdir(exist_ok=True)
    batches = sorted((output / "inputs").glob("*.json"))
    if limit is not None:
        batches = batches[:limit]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        pending = [pool.submit(grade_one, output, batch) for batch in batches]
        errors = []
        for future in as_completed(pending):
            try:
                batch, status = future.result()
                print(f"{batch}: {status}", flush=True)
            except (ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
                errors.append(str(error))
                print("REJECTED: " + str(error), flush=True)
        if errors:
            raise ValueError(f"{len(errors)} rejected batches; originals retained, resume unchanged inputs. {errors[:3]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(me.OUTPUT))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    run(args.output, args.limit, args.workers)
