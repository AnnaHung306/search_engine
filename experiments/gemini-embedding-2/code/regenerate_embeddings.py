"""Optionally request fresh Gemini vectors using the original index snapshot."""

import argparse
from getpass import getpass
import json
import os
from pathlib import Path
import sqlite3

from embedding_core import fetch_embeddings, input_digest
from reproduce import ROOT, read_inputs, snapshot_inputs


BATCH_SIZE = 8


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True, help="Original index-v8.1.json.gz")
    parser.add_argument("--output", type=Path, required=True, help="New or resumable SQLite cache outside this folder")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("Choose a separate cache outside the delivered folder.")
    manifest, mapping = read_inputs()
    documents, queries = snapshot_inputs(args.index, manifest, mapping)
    texts = [text for _, _, text in documents] + list(queries.values())
    inputs = {input_digest(text): text for text in texts}

    import requests

    with sqlite3.connect(output) as db:
        db.execute("CREATE TABLE IF NOT EXISTS vectors (digest TEXT PRIMARY KEY, vector TEXT NOT NULL)")
        saved = {row[0] for row in db.execute("SELECT digest FROM vectors")}
        if saved - inputs.keys():
            raise ValueError("The output cache contains vectors outside this experiment.")
        missing = [(key, value) for key, value in inputs.items() if key not in saved]
        if not missing:
            print(f"Cache already contains {len(saved)} vectors.")
            return

        key = os.environ.get("GEMINI_API_KEY") or getpass("Gemini API key: ")
        if not key:
            parser.error("A Gemini API key is required to request vectors.")
        with requests.Session() as session:
            session.headers["x-goog-api-key"] = key
            for offset in range(0, len(missing), BATCH_SIZE):
                batch = missing[offset:offset + BATCH_SIZE]
                vectors = fetch_embeddings(session, [text for _, text in batch])
                db.executemany(
                    "INSERT INTO vectors VALUES (?, ?)",
                    [(digest, json.dumps(vector, separators=(",", ":"))) for (digest, _), vector in zip(batch, vectors, strict=True)],
                )
                db.commit()
                print(f"{len(saved) + offset + len(batch)}/{len(inputs)} vectors saved.", flush=True)


if __name__ == "__main__":
    main()
