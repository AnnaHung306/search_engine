"""Three historical ranking variants, written to a NEW directory. TP §6.

For the frozen nine-system human evaluation use evaluate.py. This helper never
replaces historical experiment files and makes no new relevance claims.
"""
import argparse
import json
from pathlib import Path

import evaluation as ev
import search as se

VARIANTS = {
    'v0b_tfidf_rerun': ('tfidf', 0.0),
    'v2_bm25': ('bm25', 0.0),
    'v3_bm25_title': ('bm25', 0.5),
}


def run(output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Choose a new experiment directory; historical outputs are preserved')
    suite, suite_hash = ev.load_suite('course')
    index = se.load_index()
    output.mkdir(parents=True, exist_ok=True)
    for name, (model, boost) in VARIANTS.items():
        results, times = {}, []
        for query in suite['queries']:
            response = se.search(query['query'], top_k=5, model=model, title_boost=boost, use_synonyms=False)
            times.append(response['elapsed_ms'])
            results[query['query']] = [(h['url'], h['score']) for h in response['results']]
        record = {'model': model, 'title_boost': boost, 'avg_ms': sum(times) / len(times),
                  'results': results, 'quality_status': 'unjudged; not a new P@5 result',
                  'suite_sha256': suite_hash, 'index_sha256': ev.digest(se.INDEX_PATH),
                  'collection_sha256': index['collection_sha256']}
        with (output / (name + '.json')).open('x', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2)
    return {'output': str(output), 'variants': list(VARIANTS), 'queries': len(suite['queries'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=str(ev.ROOT / 'experiments/v8.1-legacy-variants'))
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))
