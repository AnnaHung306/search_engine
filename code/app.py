"""Normal Flask product entry. TP §4; U3 p.37–38; U4 p.15–39."""
import json
from flask import Flask, request, render_template, abort, send_file

import search as se
from evaluation import ROOT, load_suite, displayed_score
from snippets import highlight

app = Flask(__name__)


def options_from_form(form):
    mode = form.get("mode", "baseline")
    if mode not in ("baseline", "experiment"):
        raise ValueError("Choose a valid search mode.")
    options = {"model": "tfidf", "title_boost": 0.0, "use_synonyms": False,
               "pivot": 0.0, "coverage": False, "use_fuzzy": False,
               "proximity_weight": 0.0, "field_weight": 0.0}
    if mode == "experiment":
        model = form.get("model", "tfidf")
        if model not in ("tfidf", "bm25"):
            raise ValueError("Choose TF-IDF or BM25.")
        options.update(model=model, title_boost=0.5 if form.get("boost") == "1" else 0.0,
            use_synonyms=form.get("syn") == "1", pivot=0.2 if form.get("pivot") == "1" else 0.0,
            coverage=form.get("cov") == "1", use_fuzzy=form.get("fuzzy") == "1",
            proximity_weight=0.3 if form.get("proximity") == "1" else 0.0,
            field_weight=2.0 if form.get("fields") == "1" else 0.0)
        if options["field_weight"] and (model == "bm25" or options["pivot"]):
            raise ValueError("Field cosine is a separate comparison: use TF-IDF with pivot off.")
        if model == "bm25" and options["pivot"]:
            raise ValueError("Pivot normalization applies to TF-IDF; turn it off for BM25.")
    return mode, options


@app.get("/")
def home():
    query = request.args.get("q", "").strip()
    error = None
    try:
        mode, options = options_from_form(request.args)
        if len(query) > 512:
            raise ValueError("Use a query of at most 512 characters.")
    except ValueError as invalid:
        error = str(invalid)
        mode, options = options_from_form({})
    result = se.search(query, explain=True, **options) if not error else {
        "status": "invalid", "num_indexed": se.load_index()["N"], "results": [], "terms": [], "elapsed_ms": None}
    terms = set(result.get("terms") or []) | set((result.get("corrections") or {}).values()) | set(result.get("expanded") or [])
    for hit in result["results"]:
        hit["snippet_html"] = highlight(hit["snippet"], terms)
    return render_template("search.html", q=query, mode=mode,
        mode_description=("log TF × collection IDF, cosine; no query correction or reranking" if mode == "baseline" else
                          "Enhancements are explicit comparisons; their general quality is not yet human-validated"),
        error=error, status=result["status"], num_indexed=result["num_indexed"],
        results=result["results"], terms=result.get("terms"), elapsed=result["elapsed_ms"],
        expanded=result.get("expanded"), corrections=result.get("corrections"),
        model=options["model"], boost=bool(options["title_boost"]), syn=options["use_synonyms"],
        pivot=bool(options["pivot"]), cov=options["coverage"], fuzzy=options["use_fuzzy"],
        proximity=bool(options["proximity_weight"]), fields=bool(options["field_weight"])), (400 if error else 200)


@app.get("/documents/<int:doc_id>")
def document(doc_id):
    index = se.load_index()
    if not 0 <= doc_id < index["N"]:
        abort(404)
    return render_template("document.html", doc=index["docs"][doc_id], doc_id=doc_id)


@app.get("/evaluation")
def evaluation():
    suites = []
    for name in ("course", "development", "holdout"):
        output = ROOT / "data/evaluation/v8" / name
        manifest_path = output / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
        except ValueError:
            manifest = None  # invalid records are shown as stale, never as a score
        try:
            suite, _ = load_suite(name)
            suite_error = False
        except ValueError:
            # Visible stale state, with no old score shown under changed queries.
            suite, suite_error = {"queries": [], "role": "Frozen query file changed; restore it or create a new experiment."}, True
        scores, score_state = displayed_score(output) if not suite_error else (None, "stale")
        suites.append({"name": name, "count": len(suite["queries"]), "role": suite["role"],
                       "pool": manifest["pool_size"] if manifest else None, "scores": scores,
                       "score_state": score_state})
    return render_template("evaluation.html", suites=suites)


@app.get("/evaluation/<suite>/<asset>")
def review_asset(suite, asset):
    if suite not in ("course", "development", "holdout") or asset not in (
            "review.html", "reviewer-a.csv", "reviewer-b.csv"):
        abort(404)
    path = ROOT / "data/evaluation/v8" / suite / asset
    if not path.exists():
        abort(404)
    return send_file(path, as_attachment=asset.endswith(".csv"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
