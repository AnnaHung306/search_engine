"""Optional GTFOBins ranking based on grounded function/context examples."""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from copy import deepcopy

from gtfo_append import requested as append_requested

RELATIONS = Path(__file__).resolve().parent.parent / "data/gtfo-v8.4/relations.json"
RELATIONS_SHA256 = "fbd9c89699c105dc082f9e4548fafa4de34eb48a0944b451e1bf521b635eeb2d"
APPEND_RELATIONS = RELATIONS.parent.parent / "gtfo-v8.5/relations.json"
APPEND_COLLECTION = "cf69d35aeb9d4838cf9a1d7538bf805318124bb118906a98b8af361792a89ef9"
APPEND_RELATIONS_SHA256 = "5ea2c15eef1df3689fa380648735bc75fd8622d9ec09d44ebae1be41ec26d55a"
MODES = {"function", "paired", "verified", "append"}
_FUNCTIONS = {
    "reverse-shell": r"\b(?:reverse|outbound|connect[- ]back)[-\s]+shells?\b",
    "bind-shell": r"\bbind[-\s]+shells?\b",
    "file-write": r"\b(?:file[-\s]+writ(?:e|ing)|writ(?:e|ing)(?:\s+[a-z]+){0,5}\s+(?:files?|paths?))\b",
    "file-read": r"\b(?:file[-\s]+read(?:ing)?|read(?:ing)?(?:\s+[a-z]+){0,5}\s+files?)\b",
    "command": r"\b(?:noninteractive\s+commands?|command\s+execution)\b",
    "shell": r"\b(?:interactive|local)\s+shells?\b",
}
_CONTEXTS = {"sudo": r"\bsudo\b", "suid": r"\b(?:suid|setuid|set-user-id)\b",
             "unprivileged": r"\bunprivileged\b", "capabilities": r"\blinux\s+capabilities\b"}


def request(free_text, source_host, mode="verified"):
    if source_host != "gtfobins.org":
        return None
    text = free_text.lower()
    contexts = {name for name, pattern in _CONTEXTS.items() if re.search(pattern, text)}
    functions = {name for name, pattern in _FUNCTIONS.items() if re.search(pattern, text)}
    if mode == "append" and append_requested(text):
        if len(contexts) <= 1 and functions <= {"file-write"}:
            return "file-append", next(iter(contexts), None)
        return None
    # Append is a distinct operation; this relation index does not infer it.
    if re.search(r"\b(?:append|appending|truncate|truncating|delete|deleting)\b", text):
        return None
    if len(functions) != 1 or len(contexts) > 1:
        return None
    return next(iter(functions)), next(iter(contexts), None)


@lru_cache(maxsize=2)
def _load(collection_sha):
    path, expected = (APPEND_RELATIONS, APPEND_RELATIONS_SHA256) if collection_sha == APPEND_COLLECTION else (RELATIONS, RELATIONS_SHA256)
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("GTFOBins relations differ from the pinned artifact")
    payload = json.loads(data)
    if payload.get("schema") != 1 or payload.get("collection_sha256") != collection_sha:
        raise ValueError("GTFOBins relations are not for this index collection")
    return payload["documents"]


def evidence(index, ranked, requested, mode):
    """Return verified examples for eligible candidates; no new candidates or query rewriting."""
    function, context = requested
    append = function == "file-append"
    if append:
        function = "file-write"
    documents = _load(index["collection_sha256"])
    matched = {}
    for _, doc_id in ranked:
        doc = index["docs"][doc_id]
        entry = documents.get(doc["url"])
        if not entry:
            continue
        rows = [r for r in entry["relations"] if r["function"] == function and
                (mode == "function" or context is None or r["context"] == context) and
                (mode not in {"verified", "append"} or r["effect"] != "delete-only") and
                (not append or "append" in r)]
        if not rows:
            continue
        if hashlib.sha256(doc["text"].encode()).hexdigest() != entry["body_sha256"]:
            raise ValueError("GTFOBins evidence body differs from the active index")
        matched[doc_id] = {"canonical": entry["canonical"], "relations": deepcopy(rows)}
    return matched
