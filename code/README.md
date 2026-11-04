# v7.1 歷史安裝說明

> 本檔原文保留作 v7.1 歷程。v8 的正式安裝、正常入口、schema-2 索引及九組評估以 [根目錄 README](../README.md) 為準；下方舊指令與「四組」描述不適用於新版，不應直接照跑。

# Pentest Tool Search — Term Project I: Web Search Engine

A small topic-focused search engine over penetration-testing tool documentation
(Kali, Nmap, Metasploit, Wireshark, mitmproxy, Frida, GTFOBins).
A user types a security problem in English (e.g. `wifi password cracking`) and
gets the pages of the tools that solve it (e.g. aircrack-ng), ranked by our own
TF-IDF + cosine similarity.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install requests==2.34.2 beautifulsoup4==4.15.0 flask==3.1.3 pypinyin==0.55.0
```
Python 3.10+.

## Run (in order)

```bash
cd code
python crawler.py      # ~20-30 min; writes data/pages.json, crawl_log.jsonl, crawl_summary.json
python indexer.py      # writes data/index.json
python search.py "wifi password cracking"            # CLI, required TF-IDF cosine
python search.py --bm25 "wifi password cracking"     # bonus BM25
python search.py --bm25 --boost --syn "wifi password cracking"  # + title boost + synonyms
python app.py          # open http://127.0.0.1:5000/  (default = TF-IDF cosine)
python toy_example.py  # step-by-step TF-IDF + cosine on 3 tiny docs (for the oral check)
```

Reproduce the evaluation (fixed snapshot = the shipped data/index.json):

```bash
python evaluate.py --dump     # runs 4 systems (tfidf, tfidf_pivot, bm25, bm25_boost_syn), writes data/eval_runs.csv and adds new
                              # (query, page) pairs to data/eval_judgments.csv
# label data/eval_judgments.csv: relevant 1/0 + reason (+ reviewer)
python evaluate.py --score    # P@5 per query per system + mean -> data/eval_results.csv
python evaluate.py --timing   # query-time summary -> data/timing_summary.json
```
Skip `crawler.py`/`indexer.py` to evaluate the shipped snapshot; re-crawling changes the pages.

## Files

| File | Role |
|---|---|
| `config.py` | seeds, host allowlist, per-host path rules and caps, UA, limits |
| `crawler.py` | robots-aware focused crawler |
| `preprocess.py` | shared tokenizer for documents AND queries |
| `indexer.py` | inverted index, df, idf, document norms |
| `search.py` | candidate retrieval + cosine ranking + snippets |
| `app.py` | Flask search UI |
| `synonyms.py` | domain synonym table + Chinese→English keyword map |
| `fuzzy.py` | v7 typo / IME tolerance: edit distance + pinyin correction of OOV query words |
| `clean.py` | strips site boilerplate (ads, prev/next nav, GitHub buttons) at index time |
| `fix_encoding.py` | one-off repair of mis-decoded UTF-8 in the v7 crawl |
| `evaluate.py` | 10 frozen queries, 4 systems, pooled judgments, P@5, timing |
| `toy_example.py` | hand-checkable TF-IDF/cosine example |
| `run_experiments.py` | development variants v0b–v3 → `experiments/` |
| `data/pages.json` | collection `{url, title, text, fetch_time}` |
| `data/index.json` | saved index |
| `data/crawl_log.jsonl` | every attempt: fetched / skipped (reason) / failed (code) |
| `data/crawl_summary.json` | attempts, valid pages, per-host counts, failures, avg text size |
| `data/eval_runs.csv` | system, query, rank, doc_id, url, score (top 5) |
| `data/eval_judgments.csv` | pooled judgments: query, doc_id, url, relevant, reason, reviewer |
| `data/eval_results.csv` | joined: system, query, rank, doc_id, url, relevant, reason |
| `data/timing_summary.json` | query-time mean/median/max per system |

## Crawl scope

Seed URLs (8, v7):
- https://www.kali.org/tools/
- https://www.kali.org/docs/
- https://nmap.org/book/toc.html
- https://docs.metasploit.com/
- https://www.wireshark.org/docs/wsug_html_chunked/
- https://docs.mitmproxy.org/stable/
- https://frida.re/docs/home/
- https://gtfobins.org/

Allowed hosts (no other subdomains): `www.kali.org`, `nmap.org`, `docs.metasploit.com`,
`www.wireshark.org`, `docs.mitmproxy.org`, `frida.re`, `gtfobins.org`.

Path rules: kali.org only `/tools/` and `/docs/` (excluding `/docs/nethunter/`, `/docs/arm/`,
`/docs/installation/`, `/docs/virtualization/`, `/docs/usb/`, `/docs/cloud/`); nmap.org only `/book/`;
docs.metasploit.com excluding `/api/`; wireshark only `/docs/wsug_html_chunked/`; mitmproxy only
`/stable/` excluding `/stable/api/`; frida only `/docs/`.
Per-host caps: kali 430, nmap 150, metasploit 150, wireshark 80, mitmproxy 50, frida 40, gtfobins 100
(total ≤ 1,000). Result: 980 valid pages, 1,016 requests, 0 failures.

Politeness: robots.txt fetched per host with our UA and obeyed; ≥ 2 s between requests
to the same host (longer if robots `Crawl-delay` asks); timeout 10 s; max 2,500 attempts
including failures; on HTTP 429 we wait `Retry-After` (≤ 60 s) and do not retry the URL.
UA: `NUK-IR-SearchEngine/1.0 (course project; contact: …)`.

URL handling: relative links resolved with `urljoin`; `#fragment` removed; scheme/host
lowercased and default ports dropped; **query strings kept**. Scope re-checked after redirects.
Non-HTML responses, thin pages (< 200 chars of main text), exact-duplicate texts and
duplicate post-redirect URLs are skipped and logged.

Text extraction: remove `script, style, noscript, nav, header, footer, form, aside`;
take the first of `main`, `article`, `[role=main]`, `#main-content`, … else `body`.
Links are collected from the whole page BEFORE stripping (some sites link chapters only from the sidebar).
When a response has no charset, the detected encoding is used.

## Preprocessing (same for docs and queries — `preprocess.py`)

- Lowercase.
- Token = alphanumeric run that may contain `+ - . / #` *inside* it, so `c++`, `802.11`,
  `wifi-cracking`, `example.com` stay whole. Leading/trailing punctuation dropped.
- Compound tokens are **also** split into parts: `machine-learning` → `machine-learning`,
  `machine`, `learning`. So we never merge it into `machinelearning`, and searching either part works.
- `C++` → `c++` (the trailing `+` is kept), so it does not collapse into `c`.
- Small English stopword list (articles, prepositions, auxiliaries).
- v6: light self-written suffix stemmer (`preprocess.stem`, plain words > 4 letters only; tool names untouched).
- v6: site boilerplate (Kali OffSec ad, prev/next nav, YARD footer) is stripped by `clean.py` before indexing; `pages.json` is unchanged.
- v6: optional pivoted length normalization for TF-IDF (`search(..., pivot=0.2)`, CLI `--pivot`, UI checkbox). Default stays pure cosine.
- Title is indexed together with body text.

## Scoring

- tf(t,d) = 1 + log10(count(t,d)), 0 if absent
- idf(t) = log10(N / df(t)), N = number of indexed pages (no smoothing; query terms not
  in the vocabulary are OOV and ignored)
- w(t,d) = tf · idf; the query vector uses the same formula with the **collection** idf
- cosine(q,d) = Σ w(t,q)·w(t,d) / (‖q‖·‖d‖); ‖d‖ precomputed at index time
- Candidates = union of postings of the query terms; return top 10 with score > 0.

Empty query → "Type something"; all-OOV query → clear message; no positive score → "No matching pages".

## Bonus features

The **required system (default everywhere)** is pure TF-IDF cosine: no title boost, no synonyms.
Everything below is optional and switched on explicitly (UI checkboxes / CLI flags).

- **BM25 comparison** (k1 = 1.5, b = 0.75, idf = ln(1 + (N − df + 0.5)/(df + 0.5))), evaluated on the
  **same 10 queries and the same pooled judgments** as TF-IDF.
- **Phrase & Boolean**: `"exact phrase"` = verified contiguous word match with word boundaries
  (`"port scan"` matches "port scan"/"port-scan", not "port scanning" or "export scan"); `+must`, `-mustnot`.
- **Query timing**: boundary = inside `search()`, from receiving the query string to the finished top-10
  list with snippets; index loading, Flask rendering and network excluded. Summary (mean/median/max over
  10 queries × 20 runs after a warm-up) in `data/timing_summary.json`.
- Extra (not a listed bonus): **title boost** score × (1 + 0.5 × #query terms in title); **synonym
  expansion** (`synonyms.py`, query side only, weight 0.5) incl. a small Chinese→English keyword map.
  The collection is English, so no Chinese segmentation is used; Chinese words not in the map are OOV.
- **Typo / IME tolerance** (v7, `fuzzy.py`, `--fuzzy`, UI checkbox on by default): an OOV query word is
  corrected by Damerau-Levenshtein distance (≤ 2 edits) against the vocabulary, or, for Chinese, by
  matching pinyin against the Chinese keyword map (`掃瞄→掃描`). The correction is added at weight 0.7
  and shown as "did you mean". Not used in P@5 (all frozen queries are spelled correctly).
- **Coverage-first TF-IDF** (v7.1, `coverage=True`, `--cov`, UI "more query words first"): pages with more
  distinct query words rank first; TF-IDF cosine orders pages within each group (score unchanged).
- **Hub pages** (v7.1, `clean.is_hub`): 12 menu/listing pages stay in the collection but are never returned.
- **Matched / missing keywords** (v7): every result lists which query terms it contains and which are
  missing, and query terms are bolded in the snippet.
See `../DEVLOG.md` for the development story and before/after results.

## Evaluation

`evaluate.py` holds 10 frozen queries with an information need and a relevance rule each.
Judgments are **pooled**: each (query, page) pair is judged once in `eval_judgments.csv` and reused by
every system, so TF-IDF and BM25 are compared on the same judgments. Label from page content, write a
reason, and have a second member review rows marked ambiguous.
P@5 = relevant in top 5 / 5 (denominator always 5, missing positions = 0), averaged over the 10 queries.
