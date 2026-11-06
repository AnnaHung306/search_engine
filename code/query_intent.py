"""Opt-in evidence for source names and documented native-module terminology."""
import re
from dataclasses import dataclass
from urllib.parse import urlsplit


_SOURCE_ALIASES = {"gtfobins": "gtfobins.org"}
_MIXED_SOURCE = {"alternative", "alternatives", "compare", "comparison", "vs", "versus"}
_EXCLUSION = re.compile(r"\b(?:not|never|without|except|cannot|exclud(?:e|ed|es|ing)|ignor(?:e|ed|es|ing))\b|"
                        r"\b(?:other\s+than|rather\s+than|instead\s+of|no\s+longer)\b|\b[a-z]+n['’]t\b")
_LIST = {"list", "show", "enumerate", "enumerating", "inspect", "view", "which", "what"}
_NATIVE = {"native", "shared", "process"}
_OTHER_TASK = {"kernel", "python", "java", "export", "exports", "exported", "symbol", "symbols", "inject", "injection"}
_NONCURRENT = re.compile(r"\b(?:before|pending|unloaded|unmapped|will|formerly|previously)\b|\bto\s+be\s+loaded\b")
_MODULES = {"library", "libraries", "module", "modules"}
_MODULE_API = "process.enumeratemodules"
API_WEIGHT = 0.5


@dataclass(frozen=True)
class Intent:
    source_host: str | None = None
    api_term: str | None = None

    def precedence(self, url, doc_key, api_postings):
        return (bool(self.source_host and urlsplit(url).hostname == self.source_host),
                bool(self.api_term and doc_key in api_postings))


def detect(free_text, mode):
    """Read unsigned, unquoted wording only; never reinterpret Boolean filters."""
    if mode not in ("source", "native", "both"):
        raise ValueError("Intent must be source, native, or both")
    wording = free_text.lower()
    if _EXCLUSION.search(wording):
        return Intent()
    words = set(re.findall(r"[a-z0-9]+", wording))
    hosts = {_SOURCE_ALIASES[w] for w in words & _SOURCE_ALIASES.keys()}
    source = next(iter(hosts)) if mode != "native" and len(hosts) == 1 and not words & _MIXED_SOURCE else None
    native = (mode != "source" and "loaded" in words and words & _LIST and words & _MODULES and
              words & _NATIVE and not words & _OTHER_TASK and not _NONCURRENT.search(wording))
    return Intent(source, _MODULE_API if native else None)
