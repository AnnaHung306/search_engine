"""Input formatting and ranking from the Gemini Embedding 2 experiment."""

import hashlib
import math
import time

MODEL = "models/gemini-embedding-2"
DIMENSIONS = 768
MAX_BYTES = 6000
OVERLAP_BYTES = 500
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/{MODEL}:batchEmbedContents"


def input_digest(text):
    return hashlib.sha256(f"{MODEL}/{DIMENSIONS}/{text}".encode()).hexdigest()


def utf8_windows(text):
    body = text.encode()
    start = 0
    while True:
        end = min(start + MAX_BYTES, len(body))
        while end < len(body) and body[end] & 0xC0 == 0x80:
            end -= 1
        yield start, body[start:end].decode()
        if end == len(body):
            break
        start = end - OVERLAP_BYTES
        while body[start] & 0xC0 == 0x80:
            start += 1


def model_inputs(index, suites):
    documents = []
    for doc_id, doc in enumerate(index["docs"]):
        for offset, body in utf8_windows(doc["text"]):
            title = doc["title"].strip() or "none"
            documents.append((doc_id, offset, f"title: {title} | text: {body}"))
    queries = sorted({q["query"] for groups in suites.values() for suite in groups.values() for q in suite["queries"]})
    query_inputs = {q: f"task: search result | query: {q}" for q in queries}
    return documents, query_inputs


def fetch_embeddings(session, texts):
    payload = {"requests": [{"model": MODEL, "content": {"parts": [{"text": text}]},
                             "outputDimensionality": DIMENSIONS} for text in texts]}
    for attempt in range(5):
        response = session.post(ENDPOINT, json=payload, timeout=(10, 100))
        if response.ok:
            break
        if response.status_code not in (429, 500, 502, 503, 504) or attempt == 4:
            status = response.json().get("error", {}).get("status", "") if "json" in response.headers.get("Content-Type", "") else ""
            raise SystemExit(f"Gemini API failed: HTTP {response.status_code} {status}")
        wait = response.headers.get("Retry-After", "")
        delay = max(float(wait) if wait.isnumeric() else 0, (12 if response.status_code == 429 else 2) * (attempt + 1))
        print(f"HTTP {response.status_code}. Retry in {delay:g}s.", flush=True)
        time.sleep(delay)
    embeddings = response.json().get("embeddings", [])
    if len(embeddings) != len(texts):
        raise ValueError("API returned the wrong number of embeddings")
    normalized = []
    for row in embeddings:
        vector = row["values"]
        norm = math.hypot(*vector)
        if len(vector) != DIMENSIONS or not math.isfinite(norm) or norm == 0:
            raise ValueError("API returned an invalid embedding")
        normalized.append([value / norm for value in vector])
    return normalized


def dense_rankings(index, docs, queries, vectors):
    document_vectors = vectors[:len(docs)]
    query_vectors = vectors[len(docs):]
    results = {}
    for query, vector in zip(queries, query_vectors, strict=True):
        best = {}
        for (doc_id, offset, _), document_vector in zip(docs, document_vectors, strict=True):
            doc = index["docs"][doc_id]
            if doc["hub"] or not doc["url"].startswith(("http://", "https://")):
                continue
            score = math.sumprod(vector, document_vector)
            if doc_id not in best or score > best[doc_id][0]:
                best[doc_id] = (score, offset)
        results[query] = [{"doc_id": i, "score": score, "chunk_start_byte": offset,
                           "url": index["docs"][i]["url"], "title": index["docs"][i]["title"]}
                          for i, (score, offset) in sorted(best.items(), key=lambda pair: (-pair[1][0], pair[0]))]
    return results
