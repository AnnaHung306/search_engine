"""Build snapshot-grounded GTFOBins function/context postings from official YAML."""
import argparse
import hashlib
import io
import json
import re
import tarfile
import urllib.request
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

import search
from gtfo_append import note_evidence
import yaml

REVISION = "acd524623f9c406acedd2754ebd9c2431f3675ad"
ARCHIVE = "https://codeload.github.com/GTFOBins/GTFOBins.github.io/tar.gz/" + REVISION
ARCHIVE_SHA256 = "afe286956f27472819d18a5ad63938b6c66be911fbd1abb003dbd366f4c3b3b6"
OUTPUT = Path(__file__).resolve().parent.parent / "data/gtfo-v8.4/relations.json"
DELETE_NOTE = "This actually deletes the file."


def digest(data):
    return hashlib.sha256(data).hexdigest()


def normalize(text):
    return " ".join(text.split())


def headers(definitions):
    return {key: normalize(row["label"] + " " + re.sub(r"[`*]", "", row["description"]))
            for key, row in definitions.items()}


def sections(text, markers):
    """Exact rendered headings and descriptions delimit local evidence."""
    lookup = {v: k for k, v in markers.items()}
    pattern = "|".join(re.escape(marker) for marker in lookup)
    hits = list(re.finditer(pattern, text))
    for i, hit in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        yield lookup[hit.group()], hit.start(), text[hit.start():end]


def source_records():
    with urllib.request.urlopen(ARCHIVE, timeout=30) as response:
        blob = response.read(1_000_000)
    if digest(blob) != ARCHIVE_SHA256:
        raise ValueError("Official source archive differs from the pinned checksum")
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
        root = f"GTFOBins.github.io-{REVISION}"
        def read(path):
            with archive.extractfile(root + "/" + path) as stream:
                return yaml.safe_load(stream)
        entries = {m.name.rsplit("/", 1)[1]: read(m.name.removeprefix(root + "/"))
                   for m in archive.getmembers() if m.isfile() and
                   m.name.startswith(root + "/_gtfobins/")}
        return entries, headers(read("_data/functions.yml")), headers(read("_data/contexts.yml"))


def resolve_alias(entries, name):
    seen = set()
    while name not in seen and name in entries:
        seen.add(name)
        entry = entries[name]
        if "alias" not in entry:
            return name, entry
        name = entry["alias"]
    raise ValueError("Missing or cyclic official alias: " + name)


def derive(index, *, include_append=False):
    entries, functions, contexts = source_records()
    documents, missing, counts = {}, [], Counter()
    for doc in index["docs"]:
        url = urlsplit(doc["url"])
        slug = re.fullmatch(r"/gtfobins/([^/]+)/", url.path)
        if url.hostname != "gtfobins.org" or not slug:
            continue
        name = unquote(slug[1])
        canonical, entry = resolve_alias(entries, name)
        text = doc["text"]
        local = {}
        for function, start, section in sections(text, functions):
            local[function] = (start, section)
        relations = []
        for function, examples in sorted(entry["functions"].items()):
            # A possible inherited capability is not a direct function.
            if function == "inherit":
                counts["inherit_variants_excluded"] += len(examples)
                continue
            start, section = local.get(function, (0, ""))
            context_sections = list(sections(section, contexts))
            for variant, example in enumerate(examples):
                for context, override in sorted(example["contexts"].items()):
                    override = override or {}
                    code = normalize(override.get("code", example.get("code", "")))
                    delete_only = function == "file-write" and DELETE_NOTE in (
                        example.get("comment", "") + " " + override.get("comment", ""))
                    match = next(((offset, block.index(code)) for role, offset, block in context_sections
                                  if role == context and code and code in block), None)
                    if match is None or (delete_only and DELETE_NOTE not in section):
                        missing.append({"url": doc["url"], "function": function, "context": context, "variant": variant})
                        continue
                    offset, pos = match
                    row = {"function": function, "context": context, "variant": variant,
                           "effect": "delete-only" if delete_only else "documented",
                           "function_start": start, "context_start": start + offset,
                           "example_start": start + offset + pos, "example_length": len(code)}
                    if delete_only:
                        row["warning_start"] = start + section.index(DELETE_NOTE)
                    if include_append and function == "file-write" and not delete_only:
                        for note in (override.get("comment", ""), example.get("comment", "")):
                            append_note = note_evidence(normalize(note))
                            if append_note:
                                kind, rendered = append_note
                                note_at = section.rfind(rendered, 0, offset + pos)
                                if note_at < 0:
                                    raise ValueError("Append note could not be grounded: " + doc["url"])
                                row["append"] = {"kind": kind, "note_start": start + note_at,
                                                 "note_length": len(rendered)}
                                counts["append_relations"] += 1
                                break
                    relations.append(row)
                    counts["grounded_relations"] += 1
                    counts["delete_only_relations"] += delete_only
        documents[doc["url"]] = {"canonical": canonical, "body_sha256": digest(text.encode()),
                                "relations": relations}
    return {"schema": 1, "collection_sha256": index["collection_sha256"],
            "source": {"archive": ARCHIVE, "revision": REVISION, "archive_sha256": ARCHIVE_SHA256},
            "documents": documents, "unverified": missing, "counts": dict(counts)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Preserve prior evidence; choose a new output path")
    result = derive(search.load_index())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print({"documents": len(result["documents"]), "unverified": len(result["unverified"]), **result["counts"]})
