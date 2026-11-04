"""fuzzy.py — typo / IME tolerance for query terms (v7).

When a query word is NOT in the index vocabulary, it is probably a typo
("injetcion"), an English spelling slip, or a wrong Chinese character / wrong
pinyin pick from an input method. We try, in order:

  1. exact          the word is already a known term -> keep it.
  2. edit distance   find vocabulary terms within a small Damerau-Levenshtein
                     distance (handles insert/delete/replace/adjacent-swap):
                     "injetcion"->"injection", "scaner"->"scanner".
  3. pinyin          for a Chinese word with no mapping, match other Chinese
                     keywords in synonyms.ZH that share the same pinyin, so a
                     wrong character (破解 vs 破繲, 掃描 vs 掃瞄) still resolves.

A fuzzy correction enters the query as its OWN term at a reduced weight
(FUZZY_WEIGHT) and is reported so the UI can say 'injetcion → injection'.
Documents are never changed; only the query is repaired.
"""
FUZZY_WEIGHT = 0.7
MAX_EDITS = 2            # at most 2 edits, and never more than len(word)//3 + 1

from pypinyin import lazy_pinyin

_HAVE_PINYIN = True  # required dependency; loading errors must remain visible


def _dl_distance(a, b, cap):
    """Damerau-Levenshtein with early exit once the row minimum exceeds cap."""
    la, lb = len(a), len(b)
    if abs(la - lb) > cap:
        return cap + 1
    prev2 = None
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        rowmin = cur[0]
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            v = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if (prev2 is not None and i > 1 and j > 1
                    and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]):
                v = min(v, prev2[j - 2] + 1)      # transposition
            cur[j] = v
            if v < rowmin:
                rowmin = v
        if rowmin > cap:
            return cap + 1
        prev2, prev = prev, cur
    return prev[lb]


def _is_subseq(a, b):
    it = iter(b)
    return all(ch in it for ch in a)


def _pinyin(s):
    if not _HAVE_PINYIN:
        return None
    return "".join(lazy_pinyin(s)) if any('\u4e00' <= c <= '\u9fff' for c in s) else None


_BUCKETS = {}      # id(vocab) -> {length: [terms]} built once (speed: ~60k terms)


def _buckets(vocab, vocab_df):
    key = id(vocab)
    if key not in _BUCKETS:
        b = {}
        for t in vocab:
            # only plain words seen in >= 2 pages: skips hashes, IDs, one-off junk
            if t.isascii() and t.isalpha() and (vocab_df or {}).get(t, 2) >= 2:
                b.setdefault(len(t), []).append(t)
        _BUCKETS.clear()
        _BUCKETS[key] = b
    return _BUCKETS[key]


def correct(term, vocab, vocab_df=None, zh_keys=None):
    """term not in vocab -> best replacement, or None.
    vocab: set/dict of known index terms. vocab_df: term->doc-frequency for
    tie-breaking (prefer the more common, i.e. more 'central', correction).
    zh_keys: iterable of Chinese keywords (synonyms.ZH) for pinyin matching."""
    if term in vocab:
        return None
    # Chinese: match by pinyin against the known Chinese keyword list
    pin = _pinyin(term)
    if pin and zh_keys:
        for k in zh_keys:
            if k != term and _pinyin(k) == pin:
                return k
    if not term.isascii() or len(term) < 4:
        return None
    cap = min(MAX_EDITS, len(term) // 3 + 1)
    best, best_d, best_df = None, cap + 1, (False, -1)
    buckets = _buckets(vocab, vocab_df)
    tset = set(term)
    cands = [c for L in range(len(term) - cap - 1, len(term) + cap + 1) for c in buckets.get(L, ())]
    for cand in cands:
        if len(tset ^ set(cand)) > 2 * cap + 2:
            continue            # cheap prefilter: too many different letters
        # index terms are STEMS ("https" is stored as "http"), so also compare
        # against the plural surface form the stemmer removed
        d = min(_dl_distance(term, cand, cap), _dl_distance(term, cand + "s", cap))
        # tie-break: a dropped letter is the most common typo ("htps" -> "https",
        # not "hops"), so prefer a candidate that contains the typed word as a
        # subsequence; then prefer the more common term (higher df).
        rank = (_is_subseq(term, cand) or _is_subseq(term, cand + "s"), (vocab_df or {}).get(cand, 0))
        if d < best_d or (d == best_d and rank > best_df):
            best, best_d, best_df = cand, d, rank
    return best if best_d <= cap else None
