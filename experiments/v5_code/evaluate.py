"""evaluate.py — Precision@5 over 10 frozen queries, for several systems
judged with ONE shared set of relevance judgments.

Systems (same queries, same judgments):
  tfidf           required core: pure TF-IDF cosine            <- main result
  bm25            bonus: BM25 comparison
  bm25_boost_syn  extra: BM25 + title boost + synonym expansion

Files:
  data/eval_runs.csv        system, query, rank, doc_id, url, title, score
  data/eval_judgments.csv   query, doc_id, url, title, relevant, reason, reviewer
                            (POOLED: each (query, page) judged once, reused by every system)
  data/eval_results.csv     joined: system, query, rank, doc_id, url, relevant, reason
  data/timing_summary.json  query-time summary

Workflow:
  1. python evaluate.py --dump    run all systems, write eval_runs.csv, add any
                                  NEW (query, page) pairs to eval_judgments.csv
                                  (existing labels are kept)
  2. group members fill relevant (1/0) + reason in eval_judgments.csv, judging
     the page CONTENT against the query's relevance rule; a second member
     reviews ambiguous ones (reviewer column)
  3. python evaluate.py --score   P@5 per query per system + mean, writes
                                  eval_results.csv
  4. python evaluate.py --timing  timing summary

Denominator is ALWAYS 5 (missing positions count as nonrelevant).
"""
import csv
import json
import os
import statistics
import sys
import time

import search as se

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
RUNS = os.path.join(DATA_DIR, "eval_runs.csv")
JUDG = os.path.join(DATA_DIR, "eval_judgments.csv")
RESULTS = os.path.join(DATA_DIR, "eval_results.csv")
TIMING = os.path.join(DATA_DIR, "timing_summary.json")

SYSTEMS = {
    "tfidf":          dict(model="tfidf", title_boost=0.0, use_synonyms=False),
    "bm25":           dict(model="bm25",  title_boost=0.0, use_synonyms=False),
    "bm25_boost_syn": dict(model="bm25",  title_boost=0.5, use_synonyms=True),
}

# 10 frozen queries, each with an information need + a relevance rule.
QUERIES = [
    ("wifi password cracking",
     "User wants a tool to recover/crack Wi-Fi (WEP/WPA) passwords.",
     "Relevant if the page is about a tool that cracks or captures Wi-Fi keys/handshakes."),
    ("sql injection tool",
     "User wants a tool to find/exploit SQL injection.",
     "Relevant if the page documents a tool that detects or exploits SQLi."),
    ("port scanning techniques",
     "User wants to learn how to scan ports / a port scanner.",
     "Relevant if the page explains port scanning or documents a port scanner."),
    ("password hash cracking",
     "User wants to crack password hashes.",
     "Relevant if the page is about cracking hashed passwords (e.g. john, hashcat)."),
    ("web application vulnerability scanner",
     "User wants a scanner for web app vulnerabilities.",
     "Relevant if the page documents a web vulnerability scanner."),
    ("network packet sniffer",
     "User wants to capture/analyze network traffic.",
     "Relevant if the page is about packet capture/sniffing."),
    ("exploit metasploit module",
     "User wants to use/run a Metasploit exploit module.",
     "Relevant if the page explains Metasploit modules/exploitation."),
    ("brute force login",
     "User wants to brute-force a login service.",
     "Relevant if the page documents an online brute-force/login attack tool."),
    ("directory enumeration web server",
     "User wants to enumerate directories/files on a web server.",
     "Relevant if the page is about web content/directory discovery."),
    ("wireless deauthentication attack",
     "User wants to perform a wireless deauth attack.",
     "Relevant if the page covers deauth / wireless attacks."),
]




def _read(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(path, fields, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def dump():
    runs = []
    for sysname, kw in SYSTEMS.items():
        for q, _, _ in QUERIES:
            hits = se.search(q, top_k=5, **kw)["results"]
            for rank in range(1, 6):
                h = hits[rank - 1] if rank <= len(hits) else None
                runs.append({"system": sysname, "query": q, "rank": rank,
                             "doc_id": h["doc_id"] if h else "",
                             "url": h["url"] if h else "",
                             "title": h["title"] if h else "(no result)",
                             "score": h["score"] if h else ""})
    _write(RUNS, ["system", "query", "rank", "doc_id", "url", "title", "score"], runs)

    old = {(r["query"], r["url"]): r for r in _read(JUDG)}
    info = {q: (need, rule) for q, need, rule in QUERIES}
    judg = list(old.values())
    for r in runs:
        key = (r["query"], r["url"])
        if r["url"] and key not in old:
            need, rule = info[r["query"]]
            row = {"query": r["query"], "doc_id": r["doc_id"], "url": r["url"],
                   "title": r["title"], "relevant": "", "reason": "", "reviewer": "",
                   "information_need": need, "relevance_rule": rule}
            old[key] = row
            judg.append(row)
    judg.sort(key=lambda r: ([q for q, _, _ in QUERIES].index(r["query"]), r["url"]))
    _write(JUDG, ["query", "doc_id", "url", "title", "relevant", "reason", "reviewer",
                  "information_need", "relevance_rule"], judg)
    todo = sum(1 for r in judg if str(r["relevant"]).strip() not in ("0", "1"))
    print(f"Wrote {RUNS} ({len(runs)} rows) and {JUDG} ({len(judg)} pooled pairs, "
          f"{todo} still unlabeled).")


def score():
    judg = {(r["query"], r["url"]): r for r in _read(JUDG)}
    runs = _read(RUNS)
    missing = [r for r in runs if r["url"] and
               str(judg.get((r["query"], r["url"]), {}).get("relevant", "")).strip() not in ("0", "1")]
    if missing:
        print(f"WARNING: {len(missing)} run rows have no 0/1 label yet; they count as 0.")
    out, table = [], {}
    for r in runs:
        j = judg.get((r["query"], r["url"]), {})
        rel = 1 if str(j.get("relevant", "")).strip() == "1" else 0
        out.append({"system": r["system"], "query": r["query"], "rank": r["rank"],
                    "doc_id": r["doc_id"], "url": r["url"], "relevant": rel,
                    "reason": j.get("reason", "fewer than 5 results" if not r["url"] else "")})
        table.setdefault(r["system"], {}).setdefault(r["query"], 0)
        table[r["system"]][r["query"]] += rel
    _write(RESULTS, ["system", "query", "rank", "doc_id", "url", "relevant", "reason"], out)
    systems = list(table)
    print(f"{'query':40}" + "".join(f"{s:>16}" for s in systems))
    for q, _, _ in QUERIES:
        print(f"{q:40}" + "".join(f"{table[s][q] / 5:16.2f}" for s in systems))
    print("-" * (40 + 16 * len(systems)))
    print(f"{'MEAN P@5':40}" + "".join(
        f"{sum(table[s].values()) / 5 / len(QUERIES):16.3f}" for s in systems))


def timing(repeats=20):
    """Boundary: inside search(), from receiving the query string to the finished
    top-10 list with snippets. Index loading (once at start-up), Flask and the
    browser are NOT included. One warm-up call first, then `repeats` runs each."""
    se.load_index()
    summary = {"boundary": ("inside search(): from receiving the query string to the finished "
                             "top-10 list with snippets; index loading, Flask rendering and "
                             "network are excluded; 1 warm-up call, then repeats per query"),
               "repeats_per_query": repeats, "systems": {}}
    for sysname, kw in SYSTEMS.items():
        se.search(QUERIES[0][0], **kw)          # warm-up
        per_q = {}
        allt = []
        for q, _, _ in QUERIES:
            ts = [se.search(q, top_k=10, **kw)["elapsed_ms"] for _ in range(repeats)]
            per_q[q] = round(statistics.median(ts), 3)
            allt += ts
        summary["systems"][sysname] = {
            "mean_ms": round(statistics.mean(allt), 3),
            "median_ms": round(statistics.median(allt), 3),
            "min_ms": round(min(allt), 3), "max_ms": round(max(allt), 3),
            "median_per_query_ms": per_q}
        print(f"{sysname:16} mean {statistics.mean(allt):.2f} ms  median "
              f"{statistics.median(allt):.2f} ms  max {max(allt):.2f} ms")
    with open(TIMING, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    if "--score" in sys.argv:
        score()
    elif "--timing" in sys.argv:
        timing()
    else:
        dump()
