"""Query-dependent plain-text summaries and safe highlighting. TP §4; U3 p.37–38."""
import re
from collections import defaultdict
from bisect import bisect_right
from functools import lru_cache
from itertools import groupby
from operator import itemgetter

from markupsafe import Markup, escape
from preprocess import tokenize
from positions import word_matches

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#.\-]*")


@lru_cache(maxsize=128)
def _layout(text):
    """Whitespace layout only; do not build an unused full-document vocabulary."""
    matches = list(re.finditer(r"\S+", text))
    words = tuple(match.group() for match in matches)
    return words, tuple(match.start() for match in matches)


@lru_cache(maxsize=128)
def _matching_locations(text, forms):
    """Cache literal locations for requested forms, never results or scores."""
    _, starts = _layout(text)
    wanted = set(forms)
    if not wanted:
        return ()
    locations = defaultdict(set)
    for match in word_matches(text):
        term = match.group().lower()
        if term in wanted:
            locations[term].add(bisect_right(starts, match.start()) - 1)
    return tuple((term, tuple(sorted(indices))) for term, indices in locations.items())


def snippet(text, surface_forms, max_words=80):
    if max_words < 1:
        raise ValueError("max_words must be positive")
    words, _ = _layout(text)
    if len(words) <= max_words:
        return " ".join(words)
    hits = defaultdict(set)
    for form, word_indices in _matching_locations(text, tuple(sorted(surface_forms))):
        for word_index in word_indices:
            hits[word_index].update(surface_forms[form])
    # A window's value changes only when a hit enters or leaves it. Evaluate
    # these starts in order, retaining the same earliest-window tie policy.
    events = []
    last_start = len(words) - max_words
    for word_index, terms in hits.items():
        enter = max(0, word_index - max_words + 1)
        leave = word_index + 1
        if enter <= last_start:
            events.extend((enter, term, 1) for term in terms)
        if leave <= last_start:
            events.extend((leave, term, -1) for term in terms)
    counts, total_hits = {}, 0
    best_start, best_value = 0, (0, 0)
    for start, changes in groupby(sorted(events, key=itemgetter(0)), key=itemgetter(0)):
        for _, term, change in changes:
            count = counts.get(term, 0) + change
            if count:
                counts[term] = count
            else:
                counts.pop(term, None)
            total_hits += change
        value = (len(counts), total_hits)
        if value > best_value:
            best_start, best_value = start, value
    summary = " ".join(words[best_start:best_start + max_words])
    return ("… " if best_start else "") + summary + (" …" if best_start + max_words < len(words) else "")


def highlight(text, terms):
    terms = set(terms)
    output, last = [], 0
    for match in _WORD.finditer(text):
        output.append(escape(text[last:match.start()]))
        word = match.group()
        output.append(Markup("<b>%s</b>") % word if set(tokenize(word)) & terms else escape(word))
        last = match.end()
    output.append(escape(text[last:]))
    return Markup("").join(output)
