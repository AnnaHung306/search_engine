"""Rebuild the 983-page append experiment from the recorded captures."""
import argparse
import hashlib
import json
from pathlib import Path

from build_gtfo_functions import derive
from gtfo_functions import APPEND_COLLECTION, APPEND_RELATIONS_SHA256
from indexer import DATA_DIR, PAGES_PATH, build_index, write_index

OUTPUT = DATA_DIR / "gtfo-v8.5"
ADDED = {"https://gtfobins.org/gtfobins/" + name + "/" for name in ("hashcat", "screen", "tee")}
CAPTURE_SHA256 = "c89a93842f4d473b36d8b7411ded2a7fc1223e7965cd45321d3c4c7a5bb39783"
ADDITIONS_SHA256 = "6ca118c08c32a5dbe8ea23ba7eb3a6fe97cdae57297e7cfecfb017087fc0b59c"


def build(output):
    paths = (output / "index.json.gz", output / "relations.json")
    if output.exists():
        raise FileExistsError("Choose a new output directory to preserve the frozen experiment")
    base = PAGES_PATH.read_bytes()
    capture_bytes = (OUTPUT / "capture.json").read_bytes()
    additions_bytes = (OUTPUT / "additions.json").read_bytes()
    if (hashlib.sha256(capture_bytes).hexdigest() != CAPTURE_SHA256 or
            hashlib.sha256(additions_bytes).hexdigest() != ADDITIONS_SHA256):
        raise ValueError("Captured additions or acquisition records changed")
    capture = json.loads(capture_bytes)
    if hashlib.sha256(base).hexdigest() != capture["base_pages_sha256"]:
        raise ValueError("Original pages differ from the recorded capture base")
    pages = json.loads(base)
    additions = json.loads(additions_bytes)
    if (len(additions) != len(ADDED) or {doc["url"] for doc in additions} != ADDED or
            {doc["url"] for doc in pages} & ADDED):
        raise ValueError("Unexpected append experiment additions")
    merged = pages + additions
    collection_sha = hashlib.sha256(json.dumps(merged, ensure_ascii=False).encode()).hexdigest()
    if collection_sha != APPEND_COLLECTION:
        raise ValueError("Unexpected merged collection digest")
    index = build_index(merged, collection_sha)
    relations = derive(index, include_append=True)
    appended = {url for url, entry in relations["documents"].items()
                if any(row["context"] == "sudo" and "append" in row for row in entry["relations"])}
    if appended != ADDED or relations["unverified"]:
        raise ValueError("Expected every added append source and all example anchors to be grounded")
    relation_bytes = (json.dumps(relations, ensure_ascii=False, indent=2) + "\n").encode()
    if hashlib.sha256(relation_bytes).hexdigest() != APPEND_RELATIONS_SHA256:
        raise ValueError("Derived relation bytes differ from the frozen artifact")
    output.mkdir(parents=True, exist_ok=False)
    with paths[1].open("xb") as stream:
        stream.write(relation_bytes)
    write_index(index, paths[0])
    print(f"Indexed {index['N']} pages, with {relations['counts']['append_relations']} grounded append relations")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
