"""Self-written rankers and the exact evidence used to explain them. U4 p.15–39."""
import math

from weighting import log_tf, norm


def term_scores(index, query, doc_id, model="tfidf", pivot=0.0, field_weight=0.0):
    """Per-term contributions sum to the unboosted score; no rounded arithmetic."""
    key = str(doc_id)
    query_norm = norm(query)
    rows = []
    for term, query_weight in query.items():
        count = index["postings"][term].get(key, 0)
        title_count = index["title_postings"].get(term, {}).get(key, 0)
        description_count = index["description_postings"].get(term, {}).get(key, 0)
        document_weight = log_tf(count) * index["idf"][term]
        if model == "bm25":
            inverse = math.log(1 + (index["N"] - index["df"][term] + 0.5) /
                               (index["df"][term] + 0.5))
            # query holds external expansion/query-TF multipliers for BM25
            denominator = count + 1.5 * (0.25 + 0.75 * index["doc_len"][doc_id] / index["avg_dl"])
            contribution = query_weight * inverse * count * 2.5 / denominator if count else 0.0
        elif field_weight:
            title_weight = log_tf(title_count) * index["idf"][term]
            body_weight = log_tf(count - title_count - description_count) * index["idf"][term]
            description_weight = log_tf(description_count) * index["idf"][term]
            title_denominator = query_norm * index["title_norms"][doc_id]
            body_denominator = query_norm * index["body_norms"][doc_id]
            description_denominator = query_norm * index["description_norms"][doc_id]
            contribution = ((query_weight * body_weight / body_denominator if body_denominator else 0.0) +
                (query_weight * description_weight / description_denominator if description_denominator else 0.0) +
                field_weight * (query_weight * title_weight / title_denominator if title_denominator else 0.0)
                ) / (2 + field_weight)
        else:
            document_norm = index["norms"][doc_id]
            denominator = query_norm * ((1 - pivot) * index["avg_norm"] + pivot * document_norm
                                         if pivot else document_norm)
            contribution = query_weight * document_weight / denominator if denominator else 0.0
        rows.append({"term": term, "tf": count, "title_tf": title_count, "description_tf": description_count,
                     "df": index["df"][term], "idf": inverse if model == "bm25" else index["idf"][term],
                     "query_weight": query_weight, "document_weight": document_weight,
                     "contribution": contribution})
    return rows


def score(index, query, candidates, *, model="tfidf", pivot=0.0, field_weight=0.0):
    if model not in ("tfidf", "bm25"):
        raise ValueError("Unknown ranking model")
    if not 0 <= pivot <= 1 or field_weight < 0:
        raise ValueError("Invalid normalization or field weight")
    if field_weight and (model != "tfidf" or pivot):
        raise ValueError("Field cosine is a separate experiment; it cannot also use BM25 or pivot")
    return {doc_id: sum(row["contribution"] for row in term_scores(
                index, query, doc_id, model=model, pivot=pivot, field_weight=field_weight))
            for doc_id in candidates}
