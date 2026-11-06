"""indexer.py — self-implemented inverted index + TF-IDF model (+ BM25 stats).

Reads data/pages.json, assigns integer doc IDs, builds:
  - inverted index: term -> {doc_id: term_frequency}   (title+body)
  - title index:    term -> {doc_id: tf_in_title}       (title boost applied at query time)
  - document frequency + idf per term
  - TF-IDF document-vector L2 norm per doc (so cosine is cheap at query time)
  - document length (token count) and average length (for BM25)

Writes data/index.json. No TfidfVectorizer is used.

Definitions (also in README / DEVLOG):
  tf(t,d)  = 1 + log10(raw_count)        (log tf, 0 when count 0)
  idf(t)   = log10(N / df(t))            (N = number of docs)
  weight   = tf * idf
  doc norm = sqrt(sum_t weight(t,d)^2)
BM25 (k1=1.5, b=0.75) uses idf_bm = ln(1 + (N-df+0.5)/(df+0.5)).
Query uses the SAME collection idf values, never refit per query.
"""
import json
import math
import os

from preprocess import tokenize

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PAGES_PATH = os.path.join(DATA_DIR, "pages.json")
INDEX_PATH = os.path.join(DATA_DIR, "index.json")



def build():
    with open(PAGES_PATH, encoding="utf-8") as f:
        pages = json.load(f)

    docs = []
    postings = {}          # term -> {doc_id: tf in title+body (title counted once)}
    title_post = {}        # term -> {doc_id: tf in title only} -> title boost at query time
    doc_len = []           # token count per doc (title+body)
    title_len = []         # token count of the title

    for doc_id, p in enumerate(pages):
        docs.append({"url": p["url"], "title": p["title"], "text": p["text"]})
        title_toks = tokenize(p["title"])
        body_toks = tokenize(p["text"])

        tcounts = {}
        for tok in title_toks:
            tcounts[tok] = tcounts.get(tok, 0) + 1
        for term, c in tcounts.items():
            title_post.setdefault(term, {})[doc_id] = c

        counts = {}
        for tok in title_toks + body_toks:
            counts[tok] = counts.get(tok, 0) + 1
        for term, c in counts.items():
            postings.setdefault(term, {})[doc_id] = c
        doc_len.append(len(title_toks) + len(body_toks))
        title_len.append(len(title_toks))

    N = len(docs)
    df = {term: len(pl) for term, pl in postings.items()}
    idf = {term: math.log10(N / df[term]) for term in df}

    norms = [0.0] * N
    for term, pl in postings.items():
        w_idf = idf[term]
        for doc_id, c in pl.items():
            w = (1 + math.log10(c)) * w_idf
            norms[doc_id] += w * w
    norms = [math.sqrt(x) for x in norms]

    index = {
        "N": N,
        "docs": docs,
        "postings": postings,
        "title_postings": title_post,
        "df": df,
        "idf": idf,
        "norms": norms,
        "doc_len": doc_len,
        "title_len": title_len,
        "avg_dl": sum(doc_len) / N if N else 0,
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    print(f"Indexed {N} docs, {len(postings)} unique terms, "
          f"avg_dl={index['avg_dl']:.1f} -> {INDEX_PATH}")


if __name__ == "__main__":
    build()
