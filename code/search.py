"""search.py — load the index and rank documents.

DEFAULT = the required system: pure TF-IDF cosine, no title boost, no synonyms.

Rankers (model=):
  - "tfidf"  cosine similarity between log-tf.idf vectors   (REQUIRED core, default)
  - "bm25"   Okapi BM25 (k1=1.5, b=0.75)                     (bonus comparison)

Optional enhancements (off by default, switch on per call / in the UI):
  - title_boost: score *= (1 + title_boost * #query terms in the title)
  - synonyms:    query expansion from synonyms.py (weight 0.5) + Chinese keyword map
  - pivot:       (v6, tfidf only) pivoted length normalization (Singhal et al., 1996):
                 divide by (1-s)*avg_norm + s*|d| instead of |d|. s=0 is plain cosine.
                 Fixes cosine's bias toward very short pages.
  - fuzzy:       (v7) typo / IME tolerance. A query word not in the vocabulary is
                 corrected to the nearest term by edit distance (English typos) or
                 by pinyin (wrong Chinese character), added at weight 0.7, and the
                 correction is reported ("injetcion -> injection").
  - coverage:    (v7.1) coordination-level ranking: pages containing more of the
                 distinct query words come first; the TF-IDF cosine score orders
                 pages within each group (the score itself is unchanged).
Hub pages (menus / full listings, clean.is_hub) are never returned (SKIP_HUBS).
Every result also reports which query words it MATCHED and which are MISSING
(like Google's "Missing: ..."), so the ranking is explainable.
Always on:
  - phrase search: "exact phrase" -> verified contiguous word match
  - Boolean:       +term (must contain) and -term (must not contain)
  - timing:        elapsed_ms = from receiving the query string to the finished
                   ranked list with snippets (index loading NOT included)

The same collection IDF is reused (never refit). CLI:
    python search.py "wifi password cracking"            (TF-IDF cosine)
    python search.py --bm25 "sql injection tool"
    python search.py --pivot "port scanning techniques"   (TF-IDF + pivoted normalization)
    python search.py --bm25 --boost --syn "wifi password cracking"   (explicit comparison)
"""
import gzip
import json
import os
import re
import sys
import time
from collections import Counter
from functools import lru_cache

from preprocess import tokenize
from weighting import log_tf, vector, norm
import positions
import query_intent
import gtfo_append
import gtfo_functions
import write_effects
import ranking
from snippets import snippet
import synonyms
import fuzzy
import offsets

SKIP_HUBS = True     # v7.1: see clean.is_hub(); set False to reproduce v7 numbers

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_PATH = os.environ.get("IR_INDEX_PATH", os.path.join(DATA_DIR, "index-v8.1.json.gz"))

K1 = 1.5
B = 0.75
TITLE_BOOST = 0.5          # value used when title boost is switched on
PIVOT_SLOPE = 0.2          # v6: slope used when pivoted normalization is switched on
                           # (chosen up front as a common literature value, NOT tuned)

def load_index(path=None):
    return _read_index(os.path.abspath(path if path is not None else INDEX_PATH))


@lru_cache(maxsize=2)
def _read_index(path):
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        index = json.load(f)
    if (index.get("schema_version") != 4 or
            index.get("position_offset_encoding") != offsets.ENCODING):
        raise ValueError("Index schema mismatch; run python code/indexer.py")
    return index


def parse_query(raw):
    """Pull out "phrases", +must, -mustnot, leave the rest as free terms."""
    phrases = re.findall(r'"([^"]+)"', raw)
    rest = re.sub(r'"[^"]+"', " ", raw)
    must, mustnot, free, free_text = [], [], [], []
    for tok in rest.split():
        if tok.startswith("+") and len(tok) > 1:
            must.extend(tokenize(tok[1:]))
        elif tok.startswith("-") and len(tok) > 1:
            mustnot.extend(tokenize(tok[1:]))
        else:
            free.extend(tokenize(tok))
            free_text.append(tok)
    phrase_terms = [t for ph in phrases for t in tokenize(ph)]
    return {"phrases": phrases, "must": must, "mustnot": mustnot,
            "free": free, "all_terms": free + must + phrase_terms, "free_text": " ".join(free_text)}


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


def search(query, top_k=10, model="tfidf", title_boost=0.0, use_synonyms=False,
           pivot=0.0, use_fuzzy=False, coverage=False,
           proximity_weight=0.0, field_weight=0.0, explain=False, intent=None, gtfo_mode=None,
           *, index_path=None):
    """title_boost=0.0, use_synonyms=False, pivot=0.0, use_fuzzy=False give the
    required pure TF-IDF cosine."""
    use_syn = use_synonyms
    boost = title_boost
    idx = load_index(index_path)  # cached by snapshot; not counted in query time
    t0 = time.perf_counter()
    zh_fixes = {}
    if use_fuzzy:
        query, zh_fixes = _fix_chinese(query)   # v7: wrong character -> right one (same pinyin)
    if use_syn or use_fuzzy:
        query = synonyms.translate_zh(query)   # 中文關鍵字 -> English
    parsed = parse_query(query)
    free_text = parsed["free_text"]
    if gtfo_mode in ("append", "effects"):
        free_text = gtfo_append.intent_text(free_text)
    signals = query_intent.detect(free_text, intent) if intent is not None else None
    if gtfo_mode is not None and (gtfo_mode not in gtfo_functions.MODES or intent not in ("source", "both")):
        raise ValueError("GTFOBins mode requires a known function mode and source intent")
    if gtfo_mode == "append" and idx["collection_sha256"] not in (gtfo_functions.APPEND_COLLECTION, gtfo_functions.EFFECTS_COLLECTION):
        raise ValueError("GTFOBins append mode requires IR_INDEX_PATH=data/gtfo-v8.5/index.json.gz")
    if gtfo_mode == "effects" and idx["collection_sha256"] != gtfo_functions.EFFECTS_COLLECTION:
        raise ValueError("Write effects mode requires IR_INDEX_PATH=data/gtfo-v8.6/index.json.gz")
    exclude_gtfobins, mixed_sources = (write_effects.source_constraint(free_text)
                                       if gtfo_mode == "effects" else (False, False))
    effect_request = (write_effects.request(free_text, outside=exclude_gtfobins)
                      if gtfo_mode == "effects" and not mixed_sources else None)
    if exclude_gtfobins or mixed_sources:
        signals = query_intent.Intent(api_term=signals.api_term)
    function_mode = "append" if gtfo_mode == "effects" else gtfo_mode
    requested_function = (gtfo_functions.request(free_text, signals.source_host, function_mode)
                          if gtfo_mode is not None and effect_request is None else None)
    # remember the words the user typed, to label each result matched / missing
    shown_words = []
    for w in parsed["free"] + parsed["must"] + [x for ph in parsed["phrases"] for x in tokenize(ph)]:
        if w not in shown_words:
            shown_words.append(w)
    terms = parsed["all_terms"]

    if not query.strip():
        return _wrap("empty", idx, [], None, t0, model)
    if not terms:                      # e.g. untranslatable Chinese / only symbols
        return _wrap("oov", idx, [], [query.strip()], t0, model)

    idf = idx["idf"]
    postings = idx["postings"]

    # v7: typo / IME correction for query words not in the vocabulary
    corrections = {}
    if use_fuzzy:
        vocab = idf
        for t in parsed["free"] + parsed["must"]:
            if t not in vocab and t not in corrections:
                c = fuzzy.correct(t, vocab, idx["df"], list(synonyms.ZH))
                if c:
                    c_tok = tokenize(c)
                    corrections[t] = c_tok[0] if c_tok else c
        for src, fixed in corrections.items():
            if fixed in idf and fixed not in parsed["free"]:
                parsed["free"].append(fixed)
    parsed["must"] = [corrections.get(t, t) for t in parsed["must"]]
    corrections.update(zh_fixes)

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
    for fixed in corrections.values():         # v7: corrected terms weigh less
        if fixed in weights:
            weights[fixed] = min(weights[fixed], fuzzy.FUZZY_WEIGHT)
    api_term = signals.api_term if signals else None
    if api_term in idf:
        weights.setdefault(api_term, query_intent.API_WEIGHT)
    weights = {t: w for t, w in weights.items() if t in idf}
    if not weights:
        return _wrap("oov", idx, [], terms, t0, model)
    scoring_terms = list(weights)

    # candidate docs = union of postings of scoring terms
    cand = set()
    for t in scoring_terms:
        cand.update(int(d) for d in postings[t])

    # v7.1: navigation hub pages (menus / full listings) are never results
    docs_all = idx["docs"]
    if exclude_gtfobins:
        cand = {d for d in cand if not write_effects.from_gtfobins(docs_all[d]["url"])}
    if SKIP_HUBS:
        cand = {d for d in cand if not docs_all[d].get("hub")}

    # Boolean filters
    must_sets = []
    for t in parsed["must"]:
        must_sets.append({int(d) for d in postings.get(t, {})})
    for s in must_sets:
        cand &= s
    for t in parsed["mustnot"]:
        cand -= {int(d) for d in postings.get(t, {})}

    # Literal phrase positions keep stopwords and never cross title/body.
    for phrase in parsed["phrases"]:
        cand.intersection_update(positions.phrase_documents(idx, phrase))

    if not cand:
        return _wrap("no_match", idx, [], terms, t0, model)

    counted_terms = [corrections.get(term, term) for term in parsed["all_terms"]]
    query_counts = Counter(counted_terms)
    query_vector = vector([term for term in counted_terms if term in weights], idf, weights)
    # Expansion/correction terms absent from the literal query get one weighted occurrence.
    for term, multiplier in weights.items():
        if term not in query_vector:
            query_vector[term] = multiplier * idf[term]
    rank_query = ({term: log_tf(max(1, query_counts[term])) * multiplier
                   for term, multiplier in weights.items()} if model == "bm25" else query_vector)
    scores = ranking.score(idx, rank_query, cand, model=model, pivot=pivot, field_weight=field_weight)
    base_scores = dict(scores)
    proximity_evidence = {}
    if proximity_weight:
        if proximity_weight < 0:
            raise ValueError("Proximity weight must be nonnegative")
        for doc_id in scores:
            evidence = positions.proximity(idx, doc_id, scoring_terms, include_offsets=False)
            proximity_evidence[doc_id] = evidence
            scores[doc_id] *= 1 + proximity_weight * evidence["closeness"]

    # title boost (both models): a query term in the TITLE multiplies the score,
    # so it works regardless of the ranker's score scale (cosine ~0-1 vs BM25 ~10-20)
    if boost:
        uniq = {t for t, w in weights.items() if w >= 1.0}
        for d in scores:
            th = _title_hits(idx, d, uniq)
            if th:
                scores[d] *= (1 + boost * th)

    if coverage:
        # v7.1 coordination-level ranking: pages containing MORE of the distinct
        # query words come first, and the
        # unchanged TF-IDF cosine score orders pages inside each group.
        orig = [t for t in scoring_terms if weights[t] >= 1.0] or scoring_terms
        cov = {d: sum(1 for t in orig if str(d) in postings[t] or d in postings[t]) for d in scores}
        ranked = sorted(((cov[d], s, d) for d, s in scores.items() if s > 0), reverse=True)
        ranked = [(s, d) for _, s, d in ranked]
    else:
        ranked = sorted(((s, d) for d, s in scores.items() if s > 0), reverse=True)
    if signals and (signals.source_host or api_term in postings):
        api_postings = postings.get(api_term, {})
        # Stable ordering: evidence first, existing ranking inside each tier.
        ranked.sort(key=lambda pair: signals.precedence(docs_all[pair[1]]["url"], str(pair[1]), api_postings),
                    reverse=True)
    function_evidence = {}
    if requested_function:
        function_evidence = gtfo_functions.evidence(idx, ranked, requested_function, function_mode)
        ranked.sort(key=lambda pair: pair[1] in function_evidence, reverse=True)
    effect_evidence = {}
    if effect_request:
        effect_evidence = write_effects.evidence(idx, ranked, effect_request)
        ranked.sort(key=lambda pair: pair[1] in effect_evidence, reverse=True)
    surface_forms = {}
    for term in scoring_terms:
        for form in idx["position_aliases"].get(term, []):
            surface_forms.setdefault(form, set()).add(term)
    out = []
    for s, d in ranked:
        if len(out) >= top_k:
            break
        doc = idx["docs"][d]
        if not doc["url"].lower().startswith(("http://", "https://")):
            continue                     # only HTTP/HTTPS result links
        matched, missing = [], []
        for w in shown_words:
            key = corrections.get(w, w)              # a typo counts by its correction
            if str(d) in postings.get(key, {}) or str(d) in postings.get(w, {}):
                matched.append(key)
            else:
                missing.append(w)
        out.append({"doc_id": d, "url": doc["url"], "title": doc["title"],
                    "score": s,
                    "snippet": snippet(doc["text"], surface_forms),
                    "matched": matched, "missing": missing})
    if explain:
        for hit in out:
            doc_id = hit["doc_id"]
            if proximity_weight:
                proximity_evidence[doc_id] = positions.proximity(idx, doc_id, scoring_terms)
            hit["explanation"] = {"model": model, "pivot": pivot, "field_weight": field_weight,
                "query_norm": norm(query_vector), "document_norm": idx["norms"][doc_id],
                "title_norm": idx["title_norms"][doc_id],
                "document_length": idx["doc_len"][doc_id], "average_document_length": idx["avg_dl"],
                "body_norm": idx["body_norms"][doc_id],
                "description_norm": idx["description_norms"][doc_id],
                "average_document_norm": idx["avg_norm"],
                "effective_document_norm": ((1 - pivot) * idx["avg_norm"] + pivot * idx["norms"][doc_id]
                                             if pivot else idx["norms"][doc_id]),
                "query_term_counts": {term: max(1, query_counts[term]) for term in rank_query},
                "query_multipliers": weights,
                "base_score": base_scores[doc_id], "final_score": hit["score"],
                "title_boost": boost, "coverage_first": coverage,
                "title_multiplier": 1 + boost * _title_hits(idx, doc_id,
                    {term for term, weight in weights.items() if weight >= 1.0}),
                "proximity_weight": proximity_weight, "proximity": proximity_evidence.get(doc_id),
                "terms": ranking.term_scores(idx, rank_query, doc_id, model=model,
                                             pivot=pivot, field_weight=field_weight)}
            if signals and (signals.source_host or api_term in postings):
                hit["explanation"]["intent_evidence"] = signals.precedence(
                    hit["url"], str(doc_id), postings.get(api_term, {}))
            if requested_function:
                hit["explanation"]["gtfo_evidence"] = function_evidence.get(doc_id)
            if effect_request:
                hit["explanation"]["write_effect_evidence"] = effect_evidence.get(doc_id)
    status = "ok" if out else "no_match"
    r = _wrap(status, idx, out, terms, t0, model)
    r["expanded"] = sorted(t for t, w in weights.items()
                           if w < 1.0 and t not in corrections.values())
    r["corrections"] = corrections
    if signals and (signals.source_host or api_term in postings):
        r["intent"] = {"source_host": signals.source_host, "expanded_api": api_term if api_term in postings else None}
    if requested_function:
        r["gtfo"] = {"function": requested_function[0], "context": requested_function[1],
                     "mode": function_mode, "matched_documents": len(function_evidence)}
    if effect_request or exclude_gtfobins:
        r["write_effect"] = {"effect": effect_request.effect if effect_request else None,
                             "context": effect_request.context if effect_request else None,
                             "exclude_gtfobins": exclude_gtfobins,
                             "matched_documents": len(effect_evidence)}
    return r


def _fix_chinese(query):
    """Replace a Chinese substring whose pinyin equals a known keyword's pinyin
    but whose characters differ (選字錯誤, e.g. 掃瞄 -> 掃描, 無缐 -> 無線)."""
    if not fuzzy._HAVE_PINYIN or not any('\u4e00' <= c <= '\u9fff' for c in query):
        return query, {}
    fixes = {}
    keys = sorted(synonyms.ZH, key=len, reverse=True)
    pin = {k: fuzzy._pinyin(k) for k in keys}
    for k in keys:
        L = len(k)
        i = 0
        while i + L <= len(query):
            sub = query[i:i + L]
            if sub != k and all('\u4e00' <= c <= '\u9fff' for c in sub) \
                    and sub not in synonyms.ZH and fuzzy._pinyin(sub) == pin[k]:
                fixes[sub] = k
                query = query[:i] + k + query[i + L:]
            i += 1
    return query, fixes


def _wrap(status, idx, results, terms, t0, model="tfidf"):
    return {"status": status, "num_indexed": idx["N"], "results": results,
            "terms": terms, "model": model,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    model = "bm25" if "--bm25" in args else "tfidf"
    boost = TITLE_BOOST if "--boost" in args else 0.0
    syn = "--syn" in args
    pv = PIVOT_SLOPE if "--pivot" in args else 0.0
    fz = "--fuzzy" in args
    cv = "--cov" in args
    gtfo_mode = next((mode for flag, mode in (
        ("--write-effects", "effects"), ("--gtfo-append", "append"), ("--gtfo-functions", "verified"))
        if flag in args), None)
    intent = "both" if "--intent" in args or gtfo_mode else None
    args = [a for a in args if a not in ("--bm25", "--tfidf", "--boost", "--syn", "--pivot", "--fuzzy",
                                         "--cov", "--intent", "--gtfo-functions", "--gtfo-append", "--write-effects")]
    q = " ".join(args)
    r = search(q, model=model, title_boost=boost, use_synonyms=syn, pivot=pv, use_fuzzy=fz, coverage=cv,
               intent=intent, gtfo_mode=gtfo_mode)
    if r.get("corrections"):
        print("did you mean:", r["corrections"])
    if r.get("intent"):
        print("intent evidence:", r["intent"])
    if r.get("gtfo"):
        print("GTFOBins function evidence:", r["gtfo"])
    if r.get("write_effect"):
        print("Write-effect evidence:", r["write_effect"])
    print(f"[{r['status']}] model={r['model']} indexed={r['num_indexed']} "
          f"terms={r.get('terms')} {r['elapsed_ms']}ms")
    for i, h in enumerate(r["results"], 1):
        print(f"{i:2}. {h['score']:.4f}  {h['title']}")
        print(f"     {h['url']}")
        print(f"     matched={h['matched']} missing={h['missing']}")
