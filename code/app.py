"""Normal Flask product entry. TP §4; U3 p.37–38; U4 p.15–39."""
from flask import Flask, request, render_template, abort, send_file, url_for

import search as se
from evaluation import ROOT, load_suite, load_manifest, displayed_score
from snippets import highlight
import model_evaluation

app = Flask(__name__)
EFFECTS_INDEX = ROOT / "data/gtfo-v8.6/index.json.gz"
EFFECTS_EXAMPLES = (
    ("站外附加", "outside GTFOBins append to a local file with sudo"),
    ("sudo 覆寫", "GTFOBins sudo overwrite a local file"),
)
COURSE_EXAMPLES = (
    ("SQL injection", "sql injection tool"),
    ("封包分析", "network packet sniffer"),
    ("片語與排除", '"port scan" -metasploit'),
)


def options_from_form(form):
    mode = form.get("mode", "baseline")
    if mode not in ("baseline", "experiment", "effects"):
        raise ValueError("Choose a valid search mode.")
    options = {"model": "tfidf", "title_boost": 0.0, "use_synonyms": False,
               "pivot": 0.0, "coverage": False, "use_fuzzy": False,
               "proximity_weight": 0.0, "field_weight": 0.0}
    if mode == "effects":
        variant = form.get("variant", "effects")
        if variant not in ("append", "effects"):
            raise ValueError("請選擇有效的比較版本。")
        options.update(model="bm25", intent="both", gtfo_mode=variant, index_path=EFFECTS_INDEX)
        return mode, options
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
        if mode == "effects":
            evidence = hit["explanation"].get("write_effect_evidence") or ()
            if evidence:
                body = se.load_index(EFFECTS_INDEX)["docs"][hit["doc_id"]]["text"]
                hit["example_text"] = [
                    body[row["example_start"]:row["example_start"] + row["example_length"]]
                    for row in evidence
                ]
        hit["document_href"] = url_for("document", doc_id=hit["doc_id"],
                                       **({"collection": "effects"} if mode == "effects" else {}))
    return render_template("search.html", q=query, mode=mode,
        variant=options.get("gtfo_mode", "effects"),
        examples=EFFECTS_EXAMPLES if mode == "effects" else COURSE_EXAMPLES,
        write_effect=result.get("write_effect"),
        error=error, status=result["status"], num_indexed=result["num_indexed"],
        results=result["results"], terms=result.get("terms"), elapsed=result["elapsed_ms"],
        expanded=result.get("expanded"), corrections=result.get("corrections"),
        model=options["model"], boost=bool(options["title_boost"]), syn=options["use_synonyms"],
        pivot=bool(options["pivot"]), cov=options["coverage"], fuzzy=options["use_fuzzy"],
        proximity=bool(options["proximity_weight"]), fields=bool(options["field_weight"])), (400 if error else 200)


@app.get("/documents/<int:doc_id>")
def document(doc_id):
    collection = request.args.get("collection", "course")
    if collection not in ("course", "effects"):
        abort(404)
    index = se.load_index(EFFECTS_INDEX if collection == "effects" else None)
    if not 0 <= doc_id < index["N"]:
        abort(404)
    return render_template("document.html", doc=index["docs"][doc_id], doc_id=doc_id,
                           collection=collection, num_indexed=index["N"])


@app.get("/evaluation")
def evaluation():
    suites = []
    active_collection = se.load_index()["collection_sha256"]
    for name in ("course", "development", "holdout"):
        output = ROOT / "data/evaluation/v8" / name
        manifest_error = False
        try:
            manifest = load_manifest(output)
        except FileNotFoundError:
            manifest = None
        except ValueError:
            manifest = None  # invalid records are shown as stale, never as a score
            manifest_error = True
        try:
            suite, _ = load_suite(name)
            suite_error = False
        except ValueError:
            # Visible stale state, with no old score shown under changed queries.
            suite, suite_error = {"queries": [], "role": "Frozen query file changed; restore it or create a new experiment."}, True
        scores, score_state = displayed_score(output, active_collection) if not (suite_error or manifest_error) else (None, "stale")
        suites.append({"name": name, "count": len(suite["queries"]), "role": suite["role"],
                       "pool": manifest["pool_size"] if manifest else None, "scores": scores,
                       "score_state": score_state})
    model_summary, model_score_state = model_evaluation.displayed_score(collection_sha256=active_collection)
    return render_template("evaluation.html", suites=suites,
                           model_summary=model_summary, model_score_state=model_score_state)


@app.get("/evaluation/model/<asset>")
def model_asset(asset):
    assets = {name: name for name in ("llm_judgments.csv", "raw_llm_judgments.csv", "adjudications.json", "policy.json", "scores.json")}
    assets.update({name + "-scores.csv": name + "/scores.csv" for name in ("course", "development", "holdout")})
    if asset not in assets:
        abort(404)
    path = model_evaluation.OUTPUT / assets[asset]
    if not path.is_file():
        abort(404)
    return send_file(path, as_attachment=True)


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
