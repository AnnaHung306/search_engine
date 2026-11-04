"""Query-dependent plain-text summaries and safe highlighting. TP §4; U3 p.37–38."""
import re
from collections import Counter
from bisect import bisect_right

from markupsafe import Markup, escape
from preprocess import tokenize
from positions import word_matches

_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9+#.\-]*")


def snippet(text, surface_forms, max_words=80):
    matches = list(re.finditer(r"\S+", text))
    words = [match.group() for match in matches]
    if len(words) <= max_words:
        return " ".join(words)
    starts = [match.start() for match in matches]
    hits = [set() for _ in words]
    for match in word_matches(text):
        terms = surface_forms.get(match.group().lower())
        if terms:
            hits[bisect_right(starts, match.start()) - 1].update(terms)
    counts = Counter(term for terms in hits[:max_words] for term in terms)
    best_start, best_value = 0, (len(counts), sum(counts.values()))
    for start in range(1, len(words) - max_words + 1):
        for term in hits[start - 1]:
            counts[term] -= 1
            if not counts[term]:
                del counts[term]
        counts.update(hits[start + max_words - 1])
        value = (len(counts), sum(counts.values()))
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
