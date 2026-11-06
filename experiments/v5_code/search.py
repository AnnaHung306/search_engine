"""search.py — load the index and rank documents.

DEFAULT = the required system: pure TF-IDF cosine, no title boost, no synonyms.

Rankers (model=):
  - "tfidf"  cosine similarity between log-tf.idf vectors   (REQUIRED core, default)
  - "bm25"   Okapi BM25 (k1=1.5, b=0.75)                     (bonus comparison)

Optional enhancements (off by default, switch on per call / in the UI):
  - title_boost: score *= (1 + title_boost * #query terms in the title)
  - synonyms:    query expansion from synonyms.py (weight 0.5) + Chinese keyword map
Always on:
  - phrase search: "exact phrase" -> verified contiguous word match
  - Boolean:       +term (must contain) and -term (must not contain)
  - timing:        elapsed_ms = from receiving the query string to the finished
                   ranked list with snippets (index loading NOT included)

The same collection IDF is reused (never refit). CLI:
    python search.py "wifi password cracking"            (TF-IDF cosine)
    python search.py --bm25 "sql injection tool"
    python search.py --bm25 --boost --syn "wifi password cracking"   (best variant)
"""
import json
import math
import os
import re
import sys
import time

from preprocess import tokenize
import synonyms

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")

K1 = 1.5
B = 0.75
TITLE_BOOST = 0.5          # value used when title boost is switched on

_INDEX = None
_BM_IDF = None


def load_index():
    global _INDEX, _BM_IDF
    if _INDEX is None:
        with open(INDEX_PATH, encoding="utf-8") as f:
            _INDEX = json.load(f)
        N = _INDEX["N"]
        _BM_IDF = {t: math.log(1 + (N - df + 0.5) / (df + 0.5))
                   for t, df in _INDEX["df"].items()}
    return _INDEX


def snippet(text, query_terms, max_words=80):
    words = text.split()
    low = [w.lower() for w in words]
    qset = set(query_terms)
    pos = 0
    for i, w in enumerate(low):
        if any(q in w for q in qset):
            pos = max(0, i - 15)
            break
    chunk = words[pos:pos + max_words]
    s = " ".join(chunk)
    if pos > 0:
        s = "… " + s
    if pos + max_words < len(words):
        s += " …"
    return s


def parse_query(raw):
    """Pull out "phrases", +must, -mustnot, leave the rest as free terms."""
    phrases = re.findall(r'"([^"]+)"', raw)
    rest = re.sub(r'"[^"]+"', " ", raw)
    must, mustnot, free = [], [], []
    for tok in rest.split():
        if tok.startswith("+") and len(tok) > 1:
            must.extend(tokenize(tok[1:]))
        elif tok.startswith("-") and len(tok) > 1:
            mustnot.extend(tokenize(tok[1:]))
        else:
            free.extend(tokenize(tok))
    phrase_terms = [t for ph in phrases for t in tokenize(ph)]
    return {"phrases": phrases, "must": must, "mustnot": mustnot,
            "free": free, "all_terms": free + must + phrase_terms}


def _title_hits(idx, doc_id, terms):
    tp = idx["title_postings"]
    return sum(1 for t in terms if t in tp and str(doc_id) in tp[t])


def phrase_regex(ph):
    """Contiguous-word match: 'port scan' matches 'port scan' / 'Port-scan',
    but NOT 'port scanning' or 'export scan' (word boundaries on both ends)."""
    words = re.findall(r"[a-z0-9+#.]+", ph.lower())
    if not words:
        return None
    body = r"[\s\-_/]+".join(re.escape(w) for w in words)
    return re.compile(r"(?<![a-z0-9])" + body + r"(?![a-z0-9])")


def search(query, top_k=10, model="tfidf", title_boost=0.0, use_synonyms=False):
    """title_boost=0.0 and use_synonyms=False give the required pure TF-IDF cosine."""
    use_syn = use_synonyms
    boost = title_boost
    idx = load_index()            # loaded once; not counted in query time
    t0 = time.perf_counter()
    N = idx["N"]
    if use_syn:
        query = synonyms.translate_zh(query)   # 中文關鍵字 -> English
    parsed = parse_query(query)
    terms = parsed["all_terms"]

    if not query.strip():
        return _wrap("empty", idx, [], None, t0)
    if not terms:                      # e.g. untranslatable Chinese / only symbols
        return _wrap("oov", idx, [], [query.strip()], t0)

    idf = idx["idf"]
    postings = idx["postings"]
    scoring_terms = [t for t in (parsed["free"] + parsed["must"]) if t in idf]
    # phrase terms also contribute to ranking if in vocab
    for ph in parsed["phrases"]:
        scoring_terms += [t for t in tokenize(ph) if t in idf]
    # query expansion: originals weight 1.0, synonyms 0.5 (also rescues an OOV original
    # word whose synonym IS in the vocabulary)
    if use_syn:
        orig = parsed["free"] + parsed["must"] + [t for ph in parsed["phrases"] for t in tokenize(ph)]
        weights = synonyms.expand(orig)
    else:
        weights = {t: 1.0 for t in scoring_terms}
    weights = {t: w for t, w in weights.items() if t in idf}
    if not weights:
        return _wrap("oov", idx, [], terms, t0)
    scoring_terms = list(weights)

    # candidate docs = union of postings of scoring terms
    cand = set()
    for t in scoring_terms:
        cand.update(int(d) for d in postings[t])

    # Boolean filters
    must_sets = []
    for t in parsed["must"]:
        must_sets.append({int(d) for d in postings.get(t, {})})
    for s in must_sets:
        cand &= s
    for t in parsed["mustnot"]:
        cand -= {int(d) for d in postings.get(t, {})}

    # phrase filter: verified contiguous word match in title+text
    if parsed["phrases"]:
        docs = idx["docs"]
        pats = [p for p in (phrase_regex(ph) for ph in parsed["phrases"]) if p]
        keep = set()
        for d in cand:
            txt = (docs[d]["title"] + " " + docs[d]["text"]).lower()
            if all(p.search(txt) for p in pats):
                keep.add(d)
        cand = keep

    if not cand:
        return _wrap("no_match", idx, [], terms, t0)

    scores = {}
    if model == "bm25":
        doc_len = idx["doc_len"]
        avg_dl = idx["avg_dl"]
        for t in scoring_terms:
            widf = _BM_IDF[t]
            for d_str, c in postings[t].items():
                d = int(d_str)
                if d not in cand:
                    continue
                dl = doc_len[d]
                denom = c + K1 * (1 - B + B * dl / avg_dl)
                scores[d] = scores.get(d, 0.0) + weights[t] * widf * (c * (K1 + 1)) / denom
    else:  # tfidf cosine
        norms = idx["norms"]
        q_w = {t: weights[t] * idf[t] for t in scoring_terms}
        q_norm = math.sqrt(sum(w * w for w in q_w.values())) or 1.0
        for t, qw in q_w.items():
            for d_str, c in postings[t].items():
                d = int(d_str)
                if d not in cand:
                    continue
                dw = (1 + math.log10(c)) * idf[t]
                scores[d] = scores.get(d, 0.0) + qw * dw
        for d in scores:
            scores[d] /= (q_norm * (norms[d] or 1.0))

    # title boost (both models): a query term in the TITLE multiplies the score,
    # so it works regardless of the ranker's score scale (cosine ~0-1 vs BM25 ~10-20)
    if boost:
        uniq = {t for t, w in weights.items() if w >= 1.0}
        for d in scores:
            th = _title_hits(idx, d, uniq)
            if th:
                scores[d] *= (1 + boost * th)

    ranked = sorted(((s, d) for d, s in scores.items() if s > 0), reverse=True)
    out = []
    for s, d in ranked:
        if len(out) >= top_k:
            break
        doc = idx["docs"][d]
        if not doc["url"].lower().startswith(("http://", "https://")):
            continue                     # only HTTP/HTTPS result links
        out.append({"doc_id": d, "url": doc["url"], "title": doc["title"],
                    "score": round(s, 4),
                    "snippet": snippet(doc["text"], scoring_terms)})
    status = "ok" if out else "no_match"
    r = _wrap(status, idx, out, terms, t0, model)
    r["expanded"] = sorted(t for t, w in weights.items() if w < 1.0)
    return r


def _wrap(status, idx, results, terms, t0, model="tfidf"):
    return {"status": status, "num_indexed": idx["N"], "results": results,
            "terms": terms, "model": model,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    model = "bm25" if "--bm25" in args else "tfidf"
    boost = TITLE_BOOST if "--boost" in args else 0.0
    syn = "--syn" in args
    args = [a for a in args if a not in ("--bm25", "--tfidf", "--boost", "--syn")]
    q = " ".join(args)
    r = search(q, model=model, title_boost=boost, use_synonyms=syn)
    print(f"[{r['status']}] model={r['model']} indexed={r['num_indexed']} "
          f"terms={r.get('terms')} {r['elapsed_ms']}ms")
    for i, h in enumerate(r["results"], 1):
        print(f"{i:2}. {h['score']:.4f}  {h['title']}")
        print(f"     {h['url']}")
