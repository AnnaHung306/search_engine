"""Build a separate snapshot with official external append evidence."""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import build_gtfo_append as prior
import gtfo_functions
import write_effects
from indexer import DATA_DIR, PAGES_PATH, build_index, write_compressed_index

DATA = DATA_DIR / "gtfo-v8.6"
EXTERNAL_SHA = "a49bf1deb507f1fcb7894e34a95a520883ad4978ce7cd0734d799d68fa3b4814"
CAPTURE_SHA = "1671279e35cceeea51789bb525e02ad669976148ee66c876862b2f3877b9483c"
INDEX_SHA = "a27a84ba001c1068ce62572f93c9ce81ff9d2979a206e61af2b028200b265678"
BASH = "https://www.gnu.org/s/bash/manual/html_node/Redirections.html"
POSIX = "https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html#tag_19_07_02"
CSH = "https://man.freebsd.org/cgi/man.cgi?query=csh&sektion=1"
TEE = "https://www.gnu.org/s/coreutils/manual/html_node/tee-invocation.html"
CP = "https://www.gnu.org/software/coreutils/manual/html_node/cp-invocation.html"
ARIA = "https://aria2.github.io/manual/en/html/aria2c.html#cmdoption-allow-overwrite"


def read_pinned(path, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Unexpected source bytes: {path}")
    return json.loads(data)


def effects(index, relations, examples):
    docs = {d["url"]: d for d in index["docs"]}
    evidence = {}
    for url, entry in relations["documents"].items():
        body = docs[url]["text"]
        if hashlib.sha256(body.encode()).hexdigest() != entry["body_sha256"]:
            raise ValueError("GTFOBins body differs from its grounded examples")
        rows = []
        for row in entry["relations"]:
            start = row["example_start"]
            snippet = body[start:start + row["example_length"]]
            source = url
            note = None
            if row["effect"] == "delete-only":
                effect = "delete"
                note = row["warning_start"]
            elif re.fullmatch(r"(?:bash|ash|csh)(?: -p)? -c 'echo DATA >/path/to/output-file'(?: -b)?", snippet):
                effect = "overwrite"
                source = CSH if snippet.startswith("csh ") else POSIX if snippet.startswith("ash ") else BASH
            elif snippet == "echo DATA | tee /path/to/output-file":
                effect, source = "overwrite", TEE
            elif snippet == "echo DATA | cp /dev/stdin /path/to/output-file":
                effect, source = "overwrite", CP
            elif row["function"] == "download" and entry["canonical"] == "aria2c":
                note = body.find("Use --allow-overwrite if needed.", row["function_start"], row["context_start"])
                if note == -1:
                    continue
                effect, source = "overwrite", ARIA
            else:
                continue
            record = {"effect": effect, "context": row["context"], "example_start": start,
                      "example_length": row["example_length"], "source": source}
            if note is not None:
                record["note_start"] = note
            rows.append(record)
        if rows:
            evidence[url] = {"body_sha256": entry["body_sha256"], "examples": rows}
    for url, command in examples.items():
        body = docs[url]["text"]
        if (not re.fullmatch(r'echo [^|]+\|\s*sudo tee (?:-a|--append) (?:/[^\s]+|"[^"\n]+")', command)
                or command not in body):
            raise ValueError("External append example lost its preformatted anchor")
        evidence[url] = {"body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "examples": [{"effect": "append", "context": "sudo", "example_start": body.index(command),
                          "example_length": len(command), "source": url}]}
    return {"collection_sha256": index["collection_sha256"], "documents": evidence}


def assemble():
    capture = read_pinned(DATA / "capture.json", CAPTURE_SHA)
    new = read_pinned(DATA / "additions.json", EXTERNAL_SHA)
    base_capture = read_pinned(prior.OUTPUT / "capture.json", prior.CAPTURE_SHA256)
    base = read_pinned(PAGES_PATH, base_capture["base_pages_sha256"])
    added = read_pinned(prior.OUTPUT / "additions.json", prior.ADDITIONS_SHA256)
    relations = read_pinned(gtfo_functions.APPEND_RELATIONS, gtfo_functions.APPEND_RELATIONS_SHA256)
    examples = capture["preformatted_append_examples"]
    pages = base + added + new
    if (len(new) != 3 or {d["url"] for d in new} != set(examples) or
            len({d["url"] for d in pages}) != len(pages)):
        raise ValueError("Unexpected supplement URLs")
    collection = hashlib.sha256(json.dumps(pages, ensure_ascii=False).encode()).hexdigest()
    if collection != gtfo_functions.EFFECTS_COLLECTION:
        raise ValueError("Unexpected merged collection digest")
    index = build_index(pages, collection)
    relations["collection_sha256"] = collection
    return index, relations, effects(index, relations, examples)


def publish(output, index, relations, evidence):
    raw = io.BytesIO()
    write_compressed_index(index, raw)
    artifacts = {"index.json.gz": raw.getvalue()}
    if hashlib.sha256(artifacts["index.json.gz"]).hexdigest() != INDEX_SHA:
        raise ValueError("Rebuilt index differs from the frozen bytes")
    for name, data, expected in (
        ("relations.json", relations, gtfo_functions.EFFECTS_RELATIONS_SHA256),
        ("effects.json", evidence, write_effects.SHA256),
    ):
        payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError(f"Derived artifact differs from the frozen bytes: {name}")
        artifacts[name] = payload
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in artifacts.items():
        with (output / name).open("xb") as stream:
            stream.write(payload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output
    if output.exists():
        raise FileExistsError("Choose a new destination")
    index, relations, evidence = assemble()
    publish(output, index, relations, evidence)
