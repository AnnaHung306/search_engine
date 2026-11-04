"""Field-separated positional retrieval. U1 p.43–48; TP §9.

Literal positions retain stopwords. Non-word separators other than whitespace,
hyphen, slash and underscore create a gap, preserving the old phrase policy.
Stemming aliases are used only by the optional proximity experiment.
"""
import heapq
import re
from collections import defaultdict

from preprocess import tokenize

_WORD = re.compile(r"[a-z0-9]+(?:[+.#][a-z0-9]+)*[+#]*", re.IGNORECASE | re.ASCII)
_JOINER = re.compile(r"[\s\-_/]+")


def word_matches(text):
    """One literal definition for phrases, offsets, aliases and snippets."""
    return _WORD.finditer(text)


def lexemes(text):
    position, last_end = -1, None
    for match in word_matches(text):
        word = match.group().lower()
        if not any(c.isalnum() for c in word):
            continue
        position += 1
        if last_end is not None and not _JOINER.fullmatch(text[last_end:match.start()]):
            position += 1
        yield word, position, match.start(), match.end()
        last_end = match.end()


def build(docs):
    postings = defaultdict(dict)
    aliases = defaultdict(set)
    offsets = {}
    for doc_id, doc in enumerate(docs):
        offsets[str(doc_id)] = {}
        for field, text in (("title", doc["title"]), ("description", doc["description"]), ("body", doc["text"])):
            field_offsets = []
            offsets[str(doc_id)][field] = field_offsets
            for term, position, start, end in lexemes(text):
                while len(field_offsets) < position:
                    field_offsets.append(None)
                field_offsets.append([start, end])
                postings[term].setdefault(str(doc_id), {}).setdefault(field, []).append(position)
                for normalized in tokenize(term):
                    aliases[normalized].add(term)
    return dict(postings), {term: sorted(forms) for term, forms in aliases.items()}, offsets


def phrase_documents(index, phrase):
    words = [word for word, _, _, _ in lexemes(phrase)]
    if not words:
        return set()
    postings = index["positions"]
    lists = [postings.get(word, {}) for word in words]
    candidates = set(min(lists, key=len))  # shortest postings first, U1 p.44
    for posting in lists:
        candidates.intersection_update(posting)
    matches = set()
    for doc_id in candidates:
        for field in ("title", "description", "body"):
            starts = set(lists[0][doc_id].get(field, []))
            for offset, posting in enumerate(lists[1:], 1):
                starts.intersection_update(pos - offset for pos in posting[doc_id].get(field, []))
                if not starts:
                    break
            if starts:
                matches.add(int(doc_id))
                break
    return matches


def _minimum_window(lists):
    merged = heapq.merge(*([(position, term) for position in positions]
                           for term, positions in lists.items()))
    events = list(merged)
    counts, left, best = defaultdict(int), 0, None
    for right, (position, term) in enumerate(events):
        counts[term] += 1
        while len(counts) == len(lists):
            span = position - events[left][0]
            if best is None or span < best[0]:
                best = (span, events[left][0], position)
            old_term = events[left][1]
            counts[old_term] -= 1
            if not counts[old_term]:
                del counts[old_term]
            left += 1
    return best


def proximity(index, doc_id, terms):
    """Return closeness in [0,1] and its evidence, independent of ranker scores."""
    terms = set(terms)
    best = {"closeness": 0.0, "field": None, "window": None, "terms": []}
    if len(terms) < 2:
        return best
    for field in ("title", "description", "body"):
        lists = {}
        for term in terms:
            occurrences = {p for form in index["position_aliases"].get(term, [])
                           for p in index["positions"].get(form, {}).get(str(doc_id), {}).get(field, [])}
            if occurrences:
                lists[term] = sorted(occurrences)
        if len(lists) < 2:
            continue
        span, start, end = _minimum_window(lists)
        closeness = len(lists) / len(terms) * min(1.0, (len(lists) - 1) / max(1, span))
        if closeness > best["closeness"]:
            best = {"closeness": closeness, "field": field, "window": span,
                    "terms": sorted(lists),
                    "character_span": [index["position_offsets"][str(doc_id)][field][start][0],
                                       index["position_offsets"][str(doc_id)][field][end][1]]}
    return best
