"""Opt-in write-effect and explicit source constraints over pinned evidence."""
import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlsplit

import gtfo_append
import gtfo_functions
import query_intent

DATA = gtfo_functions.EFFECTS_RELATIONS.parent / "effects.json"
SHA256 = "8b2f9a051baa18272032eacc317710213c5bbd0957fb60edbb54ea4f3a27f14b"
_EXTERNAL = re.compile(
    r"\b(?:gtfobins\s+alternatives|alternatives\s+to\s+gtfobins|"
    r"(?:non[- ]|outside\s+|exclud(?:e|ing)\s+|without\s+|other\s+than\s+)gtfobins)\b"
    r"(?:\.org\b)?"
)
_GTFO = re.compile(r"\bgtfobins\b")
_NEGATED_EXCLUSION = re.compile(r"\b(?:not|never|don['’]t|without)\s+" + _EXTERNAL.pattern)
_OVERWRITE = re.compile(r"\b(?:overwrit(?:e|es|ing)|replac(?:e|ing)\s+(?:the\s+)?(?:existing|old|prior))\b")
_DELETE = re.compile(r"\bdelet(?:e|es|ing)\b")
_CONFLICT = re.compile(r"\b(?:append\w*|truncat\w*)\b")
_FILE = re.compile(r"\b(?:files?|logs?|paths?)\b")


@dataclass(frozen=True)
class Request:
    effect: str
    context: str | None


def source_constraint(free_text):
    """Return whether an exclusion was requested or both sources were mentioned."""
    wording = _NEGATED_EXCLUSION.sub(" gtfobins ", free_text.lower())
    if not _EXTERNAL.search(wording):
        return False, False
    mixed = bool(_GTFO.search(_EXTERNAL.sub(" ", wording)))
    return not mixed, mixed


def request(free_text, *, outside):
    text = free_text.lower()
    wording = _EXTERNAL.sub(" gtfobins ", text) if outside else text
    if not _FILE.search(wording) or not query_intent.detect(wording, "source").source_host:
        return None
    contexts = gtfo_functions.contexts(wording)
    if len(contexts) > 1:
        return None
    context = next(iter(contexts), None)
    if outside and gtfo_functions.request(wording, "gtfobins.org", "append") == ("file-append", context):
        return Request("append", context)
    overwrite, delete = bool(_OVERWRITE.search(wording)), bool(_DELETE.search(wording))
    if (overwrite != delete and not _CONFLICT.search(wording) and not gtfo_append.requested(wording)
            and gtfo_functions.functions(wording) <= {"file-write"}):
        return Request("overwrite" if overwrite else "delete", context)
    return None


def from_gtfobins(url):
    hostname = (urlsplit(url).hostname or "").rstrip(".")
    return hostname == "gtfobins.org" or hostname.endswith(".gtfobins.org")


@lru_cache(maxsize=1)
def load():
    data = DATA.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA256:
        raise ValueError("Write-effect evidence differs from the frozen artifact")
    payload = json.loads(data)
    if payload["collection_sha256"] != gtfo_functions.EFFECTS_COLLECTION:
        raise ValueError("Write-effect evidence has the wrong collection")
    return payload["documents"]


def evidence(index, ranked, requested):
    documents = load()
    matched = {}
    for _, doc_id in ranked:
        doc = index["docs"][doc_id]
        entry = documents.get(doc["url"])
        if not entry:
            continue
        rows = [r for r in entry["examples"] if r["effect"] == requested.effect and
                (requested.context is None or r["context"] == requested.context)]
        if rows:
            if hashlib.sha256(doc["text"].encode()).hexdigest() != entry["body_sha256"]:
                raise ValueError("Write-effect evidence differs from the indexed body")
            matched[doc_id] = [dict(r) for r in rows]
    return matched
