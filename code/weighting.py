"""Shared, self-written TF-IDF arithmetic. References: U4 p.15–39; TP §3–5."""
import math
from collections import Counter


def log_tf(count):
    return 1.0 + math.log10(count) if count > 0 else 0.0


def vector(tokens, idf, multipliers=None):
    """Count repeated tokens; reuse collection IDF; apply expansion weights last."""
    multipliers = multipliers or {}
    return {term: log_tf(count) * idf[term] * multipliers.get(term, 1.0)
            for term, count in Counter(tokens).items() if term in idf}


def norm(weights):
    return math.sqrt(sum(value * value for value in weights.values()))


def cosine(query, document):
    denominator = norm(query) * norm(document)
    return (sum(value * document.get(term, 0.0) for term, value in query.items())
            / denominator) if denominator else 0.0
