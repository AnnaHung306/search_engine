"""Self-written TF-IDF index, field norms and literal positions. TP §3; U1/U4.

Builds schema-4 index-v8.1.json.gz; historical indexes remain unchanged.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

from preprocess import tokenize
from clean import clean_text, is_hub
from weighting import log_tf
import positions
import offsets as offset_codec

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PAGES_PATH = DATA_DIR / "pages.json"
INDEX_PATH = DATA_DIR / "index-v8.1.json.gz"
SCHEMA_VERSION = 4


def build_index(pages, collection_hash):
    docs, postings, title_postings, description_postings = [], {}, {}, {}
    lengths, title_lengths = [], []
    for doc_id, page in enumerate(pages):
        body = clean_text(page["text"])
        docs.append({"url": page["url"], "title": page["title"], "text": body,
                     "description": page.get("description", ""), "fetch_time": page["fetch_time"], "hub": is_hub(page["url"], page["text"])})
        title_tokens = tokenize(page["title"])
        body_tokens = tokenize(body)
        description_tokens = tokenize(page.get("description", ""))
        for term, count in Counter(description_tokens).items():
            description_postings.setdefault(term, {})[str(doc_id)] = count
        for term, count in Counter(title_tokens).items():
            title_postings.setdefault(term, {})[str(doc_id)] = count
        for term, count in Counter(title_tokens + description_tokens + body_tokens).items():
            postings.setdefault(term, {})[str(doc_id)] = count
        lengths.append(len(title_tokens) + len(description_tokens) + len(body_tokens))
        title_lengths.append(len(title_tokens))
    total = len(docs)
    if not total:
        raise ValueError("The collection has no documents")
    df = {term: len(posting) for term, posting in postings.items()}
    idf = {term: math.log10(total / frequency) for term, frequency in df.items()}
    norms, title_norms, body_norms, description_norms = ([0.0] * total for _ in range(4))
    for term, posting in postings.items():
        titles = title_postings.get(term, {})
        for doc_id, count in posting.items():
            doc = int(doc_id)
            title_count = titles.get(doc_id, 0)
            description_count = description_postings.get(term, {}).get(doc_id, 0)
            norms[doc] += (log_tf(count) * idf[term]) ** 2
            title_norms[doc] += (log_tf(title_count) * idf[term]) ** 2
            body_norms[doc] += (log_tf(count - title_count - description_count) * idf[term]) ** 2
            description_norms[doc] += (log_tf(description_count) * idf[term]) ** 2
    norms, title_norms, body_norms, description_norms = ([math.sqrt(x) for x in values]
                                    for values in (norms, title_norms, body_norms, description_norms))
    literal_positions, aliases, offsets = positions.build(docs)
    return {"schema_version": SCHEMA_VERSION, "collection_sha256": collection_hash,
        "N": total, "docs": docs, "postings": postings, "title_postings": title_postings,
        "description_postings": description_postings, "description_norms": description_norms,
        "df": df, "idf": idf, "norms": norms, "doc_len": lengths,
        "title_len": title_lengths, "avg_dl": sum(lengths) / total,
        "avg_norm": sum(norms) / total, "title_norms": title_norms, "body_norms": body_norms,
        "positions": literal_positions, "position_aliases": aliases, "position_offsets": offsets,
        "position_offset_encoding": offset_codec.ENCODING}


def write_index(index, output):
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp")
    with temporary.open("wb") as raw:
        if output.suffix == ".gz":
            with gzip.GzipFile(filename="", fileobj=raw, mode="wb", compresslevel=6, mtime=0) as compressed:
                with io.TextIOWrapper(compressed, encoding="utf-8") as text:
                    json.dump(index, text, ensure_ascii=False, separators=(",", ":"))
        else:
            raw.write(json.dumps(index, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    temporary.replace(output)


def build(pages_path=PAGES_PATH, output=INDEX_PATH):
    raw = Path(pages_path).read_bytes()
    index = build_index(json.loads(raw), hashlib.sha256(raw).hexdigest())
    output = Path(output)
    write_index(index, output)
    print(f"Indexed {index['N']} docs, {len(index['postings'])} terms; {output.stat().st_size:,} bytes -> {output}")
    return index


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", default=str(PAGES_PATH))
    parser.add_argument("--output", default=str(INDEX_PATH))
    args = parser.parse_args()
    build(args.pages, args.output)
