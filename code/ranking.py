"""Self-written rankers and the exact evidence used to explain them. U4 p.15–39."""
import math
from dataclasses import dataclass

from weighting import log_tf, norm


@dataclass(frozen=True)
class _Term:
    name: str
    query_weight: float
    idf: float
    postings: dict
    titles: dict
    descriptions: dict
    bm25_idf: float | None


def _prepare(index, query, model):
    return [_Term(term, weight, index['idf'][term], index['postings'][term],
                  index['title_postings'].get(term, {}),
                  index['description_postings'].get(term, {}),
                  math.log(1 + (index['N'] - index['df'][term] + 0.5) /
                           (index['df'][term] + 0.5)) if model == 'bm25' else None)
            for term, weight in query.items()]


def _contribution(index, term, doc_id, query_norm, pivot, field_weight):
    key = str(doc_id)
    count = term.postings.get(key, 0)
    if not count:
        return 0.0
    if term.bm25_idf is not None:
        denominator = count + 1.5 * (0.25 + 0.75 * index['doc_len'][doc_id] / index['avg_dl'])
        return term.query_weight * term.bm25_idf * count * 2.5 / denominator
    if field_weight:
        title_count = term.titles.get(key, 0)
        description_count = term.descriptions.get(key, 0)
        title_weight = log_tf(title_count) * term.idf
        body_weight = log_tf(count - title_count - description_count) * term.idf
        description_weight = log_tf(description_count) * term.idf
        title_denominator = query_norm * index['title_norms'][doc_id]
        body_denominator = query_norm * index['body_norms'][doc_id]
        description_denominator = query_norm * index['description_norms'][doc_id]
        return ((term.query_weight * body_weight / body_denominator if body_denominator else 0.0) +
                (term.query_weight * description_weight / description_denominator if description_denominator else 0.0) +
                field_weight * (term.query_weight * title_weight / title_denominator if title_denominator else 0.0)
                ) / (2 + field_weight)
    document_norm = index['norms'][doc_id]
    denominator = query_norm * ((1 - pivot) * index['avg_norm'] + pivot * document_norm
                                if pivot else document_norm)
    document_weight = log_tf(count) * term.idf
    return term.query_weight * document_weight / denominator if denominator else 0.0


def term_scores(index, query, doc_id, model='tfidf', pivot=0.0, field_weight=0.0):
    """Per-term contributions use the same arithmetic as ranking, without rounding."""
    key, query_norm = str(doc_id), norm(query)
    rows = []
    for term in _prepare(index, query, model):
        count = term.postings.get(key, 0)
        rows.append({'term': term.name, 'tf': count, 'title_tf': term.titles.get(key, 0),
                     'description_tf': term.descriptions.get(key, 0),
                     'df': index['df'][term.name],
                     'idf': term.bm25_idf if term.bm25_idf is not None else term.idf,
                     'query_weight': term.query_weight, 'document_weight': log_tf(count) * term.idf,
                     'contribution': _contribution(index, term, doc_id, query_norm, pivot, field_weight)})
    return rows


def score(index, query, candidates, *, model='tfidf', pivot=0.0, field_weight=0.0):
    if model not in ('tfidf', 'bm25'):
        raise ValueError('Unknown ranking model')
    if not 0 <= pivot <= 1 or field_weight < 0:
        raise ValueError('Invalid normalization or field weight')
    if field_weight and (model != 'tfidf' or pivot):
        raise ValueError('Field cosine is a separate experiment; it cannot also use BM25 or pivot')
    terms, query_norm = _prepare(index, query, model), norm(query)
    return {doc_id: sum(_contribution(index, term, doc_id, query_norm, pivot, field_weight)
                        for term in terms) for doc_id in candidates}
