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
- No stemming, to keep the demo explainable (documented as a limitation).
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


def tokenize(text):
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
    return out


if __name__ == "__main__":
    for s in ["Machine-learning with C++ and 802.11 wifi-cracking!",
              "Nmap's -sS SYN scan on example.com"]:
        print(s, "->", tokenize(s))
