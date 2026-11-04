"""Focused crawler. TP §2; U2 p.14–31; see docs/changes/001-correctness.md.

The v7.1 snapshot is preserved. New crawls write a separate directory by default.
Every actual HTTP request, including robots and redirect hops, shares one gate.
"""
import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

import config
from crawl_http import CrawlHTTP, FetchRejected, AttemptLimitReached
from crawl_urls import normalize, in_scope

MAIN_SELECTORS = ["main", "article", "[role=main]", "#main-content",
                  ".main-content", "#content", ".content", "#main"]


def extract(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    metadata = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    description = metadata.get("content", "").strip() if metadata else ""
    # v7: collect links from the WHOLE page before stripping <nav>/<aside>.
    # Some doc sites (mitmproxy, Metasploit) only link their chapters from the
    # sidebar; taking links from <main> alone found 3 mitmproxy pages.
    # The scope allowlist still decides which links are followed.
    links = [a["href"] for a in soup.find_all("a", href=True)]
    # remove non-content tags
    for tag in soup(["script", "style", "noscript", "nav", "header",
                     "footer", "form", "aside"]):
        tag.decompose()
    node = None
    for sel in MAIN_SELECTORS:
        node = soup.select_one(sel)
        if node:
            break
    if node is None:
        node = soup.body or soup
    text = node.get_text(" ", strip=True)
    text = " ".join(text.split())
    return title, text, links, description



def crawl(output=None, resume=False):
    output = Path(output) if output else Path(__file__).resolve().parent.parent / "data/crawls/v8"
    output.mkdir(parents=True, exist_ok=True)
    state_path = output / "crawl_state.json"
    if not resume and any(output.iterdir()):
        raise ValueError("Crawl output is not empty; choose a new directory or use --resume")
    if resume and not state_path.exists():
        raise ValueError("--resume requires a checkpoint in the selected output directory")
    state = json.loads(state_path.read_text()) if resume else {}
    if state and state.get("schema_version") != 2:
        raise ValueError("Checkpoint schema mismatch; use a new output directory")
    frontiers = defaultdict(deque, {h: deque(q) for h, q in state.get("frontiers", {}).items()})
    seen, stored, hashes = (set(state.get(k, [])) for k in ("seen", "stored", "hashes"))
    pages = state.get("pages", [])
    per_host = Counter(state.get("per_host_valid", {}))
    stats = Counter(state.get("stats", {}))
    if not resume:
        for seed in config.SEED_URLS:
            url = normalize(seed)
            if not in_scope(url):
                raise ValueError(f"Seed outside declared scope: {url}")
            if url not in seen:
                seen.add(url)
                frontiers[urlsplit(url).netloc].append(url)
    with (output / "crawl_log.jsonl").open("a" if resume else "w", encoding="utf-8") as logfile:
        def log(record):
            logfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            logfile.flush()

        client = CrawlHTTP(config, log, state=state.get("http"))

        def checkpoint():
            checkpoint_data = {"schema_version": 2,
                "frontiers": {h: list(q) for h, q in frontiers.items()},
                "seen": sorted(seen), "stored": sorted(stored), "hashes": sorted(hashes),
                "pages": pages, "per_host_valid": dict(per_host),
                "stats": dict(stats), "http": client.state()}
            temporary = state_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(checkpoint_data, ensure_ascii=False), encoding="utf-8")
            temporary.replace(state_path)

        active = None
        try:
            while any(frontiers.values()) and len(pages) < config.MAX_VALID_PAGES:
                hosts = [h for h, queue in frontiers.items() if queue]
                host = min(hosts, key=lambda h: client.last.get(h, 0) +
                           max(config.DELAY_PER_HOST, client.delays.get(h, 0)))
                url = frontiers[host].popleft()
                active = (host, url)
                if url in stored:
                    active = None
                    continue
                if per_host[host] >= config.MAX_PAGES_PER_HOST.get(host, config.MAX_VALID_PAGES):
                    stats["skipped_host_cap"] += 1
                    log({"url": url, "status": "skipped", "reason": "host_cap"})
                    active = None
                    continue
                stats["content_urls_considered"] += 1
                try:
                    response = client.fetch(url)
                except FetchRejected as error:
                    stats[error.reason] += 1
                    log({"url": url, "status": "skipped", "reason": error.reason,
                         "destination": error.url})
                    active = None
                    continue
                try:
                    if response.status_code != 200:
                        stats["failed_status"] += 1
                        log({"url": url, "status": "failed", "code": response.status_code})
                        active = None
                        continue
                    content_type = response.headers.get("Content-Type", "")
                    if "html" not in content_type.lower():
                        stats["skipped_nonhtml"] += 1
                        log({"url": url, "status": "skipped", "reason": "nonhtml"})
                        active = None
                        continue
                    final = normalize(response.url)
                    final_host = urlsplit(final).netloc
                    if not in_scope(final):
                        raise RuntimeError("Request gate returned an out-of-scope response")
                    if "charset" not in content_type.lower():
                        detected = response.apparent_encoding
                        if not detected:
                            stats["skipped_encoding_unknown"] += 1
                            log({"url": final, "status": "skipped", "reason": "encoding_unknown"})
                            active = None
                            continue
                        response.encoding = detected
                    title, text, links, description = extract(response.text)
                finally:
                    response.close()
                for href in links:
                    try:
                        target = normalize(href, final)
                    except (ValueError, TypeError):
                        continue
                    if target not in seen and in_scope(target):
                        seen.add(target)
                        frontiers[urlsplit(target).netloc].append(target)
                digest = hashlib.sha256(text.encode()).hexdigest()
                reason = ("duplicate_url" if final in stored else
                          "duplicate_text" if digest in hashes else
                          "thin_text" if len(text) < config.MIN_TEXT_CHARS else
                          "host_cap" if per_host[final_host] >= config.MAX_PAGES_PER_HOST.get(
                              final_host, config.MAX_VALID_PAGES) else None)
                if reason:
                    stats["skipped_" + reason] += 1
                    log({"url": final, "status": "skipped", "reason": reason})
                    active = None
                    continue
                pages.append({"url": final, "title": title, "text": text, "description": description,
                              "fetch_time": datetime.now(timezone.utc).isoformat()})
                stored.add(final)
                hashes.add(digest)
                per_host[final_host] += 1
                stats["valid"] += 1
                log({"url": final, "status": "fetched", "chars": len(text), "title": title})
                active = None
                if len(pages) % 25 == 0:
                    checkpoint()
                    print(f"{len(pages)} valid; {client.attempts} actual HTTP requests", flush=True)
        except AttemptLimitReached:
            stats["stopped_attempt_limit"] += 1
            log({"status": "stopped", "reason": "attempt_limit"})
        finally:
            if active is not None:
                pending_host, pending_url = active
                frontiers[pending_host].appendleft(pending_url)
            checkpoint()  # interruptions preserve unfinished work as well as durable pages
    (output / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {"schema_version": 2, "attempts": client.attempts,
        "attempt_definition": "all HTTP requests: content, robots, redirect hops, network failures",
        "http_requests": dict(client.counts), "valid_pages": len(pages), "hosts": dict(per_host),
        "failed": client.counts["network_failures"] + client.counts["http_failures"],
        "paused_hosts": client.blocked, "skipped_and_failed": dict(stats),
        "avg_text_chars": round(sum(len(p["text"]) for p in pages) / len(pages), 1) if pages else 0,
        "frontier_left": sum(map(len, frontiers.values()))}
    (output / "crawl_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", help="new crawl directory; v7.1 data is never overwritten by default")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    crawl(args.output, args.resume)
