"""toy_example.py — show TF-IDF + cosine scoring step by step on 3 tiny documents.

For the demo / oral check ("demonstrate the scoring of a small example").
Uses the SAME tokenizer and the SAME formulas as indexer.py / search.py:
  tf(t,d) = 1 + log10(count)      idf(t) = log10(N / df(t))
  w = tf * idf                    cosine = q.d / (|q| |d|)
Run:  python toy_example.py  ["optional query"]
"""
import math
import sys

from preprocess import tokenize
from weighting import log_tf, vector

DOCS = {
    0: "sqlmap is an sql injection tool",
    1: "nmap is a port scanning tool",
    2: "sql injection and sql injection payloads",
}
QUERY = sys.argv[1] if len(sys.argv) > 1 else "sql injection tool"


def main():
    N = len(DOCS)
    toks = {d: tokenize(t) for d, t in DOCS.items()}
    print("1) Tokens (stopwords removed, lowercase)")
    for d, t in toks.items():
        print(f"   d{d}: {t}")

    # inverted index: term -> {doc: count}
    index = {}
    for d, ts in toks.items():
        for t in ts:
            index.setdefault(t, {}).setdefault(d, 0)
            index[t][d] += 1
    print("\n2) Inverted index  term -> {doc: tf}")
    for t in sorted(index):
        print(f"   {t:10} {index[t]}")

    idf = {t: math.log10(N / len(p)) for t, p in index.items()}
    print(f"\n3) IDF = log10(N/df), N={N}")
    for t in sorted(idf):
        print(f"   {t:10} df={len(index[t])}  idf={idf[t]:.4f}")

    w = {d: {} for d in DOCS}
    for t, p in index.items():
        for d, c in p.items():
            w[d][t] = log_tf(c) * idf[t]
    norm = {d: math.sqrt(sum(x * x for x in w[d].values())) for d in DOCS}
    print("\n4) Document weights w = (1+log10 tf) * idf, and norms |d|")
    for d in DOCS:
        nz = {t: round(x, 4) for t, x in w[d].items() if x}
        print(f"   d{d}: {nz}   |d|={norm[d]:.4f}")

    qt = [t for t in tokenize(QUERY)]
    qc = {}
    for t in qt:
        qc[t] = qc.get(t, 0) + 1
    oov = [t for t in qc if t not in idf]
    qw = vector(qt, idf)
    qn = math.sqrt(sum(x * x for x in qw.values()))
    print(f"\n5) Query '{QUERY}' -> tokens {qt}; OOV ignored: {oov}")
    print(f"   query weights {({t: round(x, 4) for t, x in qw.items()})}  |q|={qn:.4f}")
    print("   (query uses the SAME collection idf; no refitting)")

    print("\n6) Candidates = docs in the postings of the query terms; cosine:")
    cand = sorted({d for t in qw for d in index[t]})
    res = []
    for d in cand:
        dot = sum(qw[t] * w[d].get(t, 0) for t in qw)
        parts = " + ".join(f"{qw[t]:.3f}*{w[d].get(t, 0):.3f}" for t in qw)
        cos = dot / (qn * norm[d]) if qn and norm[d] else 0
        res.append((cos, d))
        print(f"   d{d}: ({parts}) / ({qn:.3f}*{norm[d]:.3f}) = {cos:.4f}")
    print("\n7) Ranking (score > 0):")
    for r, (cos, d) in enumerate(sorted(res, reverse=True), 1):
        if cos > 0:
            print(f"   {r}. d{d}  {cos:.4f}  \"{DOCS[d]}\"")
    print("\nNote: 'tool' is in d0 and d1 -> lower idf than 'sqlmap'/'payloads';"
          " a term in every doc would get idf = 0 and not help ranking.")


if __name__ == "__main__":
    main()
