"""preprocess.py — the ONE tokenizer shared by indexer and search.

The spec requires documents and queries to be preprocessed identically, so both
sides import tokenize() from here.

Choices (documented in README):
- Lowercase everything.
- Tokens are runs of letters/digits, but '+', '-', '.', '#' are kept *inside* a
  token so that c++, nmap-scan, 802.11, and .onion survive. Leading/trailing
  punctuation is stripped. This avoids merging "machine-learning" into
  "machinelearning" (it becomes the single hyphenated token "machine-learning",
  AND we also emit its parts; see below).
- A hyphenated/slashed token is ALSO split into parts, so a search for either
  "wifi" or "cracking" still hits "wifi-cracking". The compound token is kept too.
- Stopwords: a small English list (articles, prepositions, auxiliaries). Pentest
  jargon is never stopped.
- v6: a small, explainable suffix-stripping stemmer (stem() below), so that
  scanning/scans/scanned -> scan, techniques -> technique, cracking -> crack.
  It is applied to documents AND queries (same function), and only to plain
  alphabetic words longer than 4 letters, so tool names like aircrack-ng, c++,
  802.11 are never changed. Switch off with STEM = False (then re-run indexer).
"""
import re

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to",
    "in", "on", "at", "by", "for", "with", "from", "as", "is", "are", "was",
    "were", "be", "been", "being", "this", "that", "these", "those", "it",
    "its", "you", "your", "we", "our", "they", "their", "he", "she", "him",
    "her", "can", "will", "would", "should", "could", "may", "might", "do",
    "does", "did", "has", "have", "had", "not", "no", "so", "than", "too",
    "very", "just", "about", "into", "over", "after", "before", "up", "down",
    "out", "off", "all", "any", "each", "more", "most", "some", "such", "only",
    "own", "same", "s", "t", "i", "me", "my",
}

# a token: starts & ends with an alphanumeric, may contain + - . # / inside
_TOKEN = re.compile(r"[a-z0-9]+(?:[+\-./#][a-z0-9]+)*\+*#*")
_SPLIT = re.compile(r"[\-/.]")

STEM = True
_VOWEL = re.compile(r"[aeiouy]")


def stem(w):
    """Light English suffix stripping (a tiny subset of Porter's step 1).
       ies -> y     (vulnerabilities -> vulnerability)
       sses -> ss   (passes -> pass)
       ing / ed     (scanning -> scan, cracked -> crack; only if a vowel stays)
       s            (tools -> tool; not ss/us/is: pass, status, analysis)"""
    if len(w) <= 4 or not w.isalpha():
        return w
    if w.endswith("ies") and len(w) > 5:
        return w[:-3] + "y"
    if w.endswith("sses"):
        return w[:-2]
    for suf in ("ing", "ed"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            b = w[:-len(suf)]
            if not _VOWEL.search(b):          # 'thing', 'red' style words stay
                return w
            if b[-1] == b[-2] and b[-1] not in "lsz":   # scann -> scan
                b = b[:-1]
            return b
    if w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def tokenize(text, use_stem=None):
    if use_stem is None:
        use_stem = STEM
    text = text.lower()
    out = []
    for m in _TOKEN.finditer(text):
        tok = m.group(0)
        if tok in STOPWORDS:
            continue
        out.append(tok)
        # also emit sub-parts of a compound (machine-learning -> machine, learning)
        if any(c in tok for c in "-/."):
            for part in _SPLIT.split(tok):
                if len(part) > 1 and part not in STOPWORDS:
                    out.append(part)
    if use_stem:
        out = [stem(t) for t in out]
    return out


if __name__ == "__main__":
    for s in ["Machine-learning with C++ and 802.11 wifi-cracking!",
              "Nmap's -sS SYN scan on example.com",
              "Port scanning techniques for cracking vulnerabilities"]:
        print(s, "->", tokenize(s))
