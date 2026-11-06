"""app.py — Flask search interface for the pentest-tool search engine.

Run locally:  python app.py   ->  http://127.0.0.1:5000/
Shows title, URL, snippet, score, number of indexed pages, and query time.
A radio toggle switches between the required TF-IDF cosine ranker and the
bonus BM25 ranker, a checkbox toggles synonym expansion (also maps common
Chinese keywords to English). Supports "phrases", +must and -must-not terms.
"""
from flask import Flask, request, render_template_string

import search as se

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Pentest Tool Search</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 780px; margin: 36px auto; padding: 0 16px; }
    h1 { font-size: 1.4rem; margin-bottom: 4px; }
    .tag { color:#777; font-size:.85rem; margin-bottom:16px; }
    input[type=text]{ width:72%; padding:10px; font-size:1rem; }
    button{ padding:10px 16px; font-size:1rem; cursor:pointer; }
    .models{ margin:8px 0; font-size:.85rem; color:#555; }
    .meta{ color:#666; font-size:.85rem; margin:8px 0 18px; }
    .hit{ margin-bottom:20px; }
    .hit a{ font-size:1.05rem; color:#1a0dab; text-decoration:none; }
    .hit a:hover{ text-decoration:underline; }
    .url{ color:#0a7d2c; font-size:.8rem; word-break:break-all; }
    .score{ color:#999; font-size:.78rem; }
    .snippet{ color:#333; font-size:.92rem; margin-top:2px; }
    .note{ background:#fff6e0; padding:12px; border-radius:6px; }
    .ex{ font-size:.8rem; color:#888; }
    .ex a{ color:#1a0dab; text-decoration:none; margin-right:10px; }
  </style>
</head>
<body>
  <h1>🛡️ Pentest Tool Search</h1>
  <div class="tag">A mini search engine over Kali / Nmap / Metasploit docs — type a security problem in English.</div>
  <form method="get" action="/">
    <input type="text" name="q" value="{{ q|e }}" autofocus placeholder="e.g. wifi password cracking / 破解 wifi 密碼">
    <button type="submit">Search</button>
    <div class="models">
      Ranking:
      <label><input type="radio" name="model" value="tfidf" {{ 'checked' if model=='tfidf' }}> TF-IDF cosine (required)</label>
      <label><input type="radio" name="model" value="bm25" {{ 'checked' if model=='bm25' }}> BM25 (bonus)</label>
      &nbsp;·&nbsp;<label><input type="checkbox" name="boost" value="1" {{ 'checked' if boost }}> title boost</label>
      <label><input type="checkbox" name="syn" value="1" {{ 'checked' if syn }}> synonym expansion</label>
      <input type="hidden" name="sent" value="1">
    </div>
  </form>
  <div class="ex">Try:
    <a href="/?q=sql+injection+tool">sql injection tool</a>
    <a href="/?q=network+packet+sniffer">network packet sniffer</a>
    <a href='/?q="port+scan"+-metasploit'>"port scan" -metasploit</a>
  </div>
  <div class="meta">Indexed pages: {{ num_indexed }}{% if elapsed is not none %} · search time {{ '%.1f'|format(elapsed) }} ms (excl. index load){% endif %}{% if terms %} · terms: {{ terms }}{% endif %}{% if expanded %} · + synonyms: {{ expanded }}{% endif %}</div>

  {% if status == 'empty' %}
    <p class="note">Type something to search.</p>
  {% elif status == 'oov' %}
    <p class="note">None of your words are in the index. Try English tool/technique keywords
      such as <i>port scan</i>, <i>sql injection</i>, or <i>password cracking</i>.</p>
  {% elif status == 'no_match' %}
    <p class="note">No matching pages found.</p>
  {% elif status == 'ok' %}
    <p class="meta">Showing {{ results|length }} result(s) with positive score.</p>
    {% for h in results %}
      <div class="hit">
        {% if h.url.lower().startswith('http://') or h.url.lower().startswith('https://') %}<a href="{{ h.url }}" target="_blank" rel="noopener noreferrer">{{ h.title or h.url }}</a>{% else %}{{ h.title }}{% endif %}
        <div class="url">{{ h.url }}</div>
        <div class="score">score {{ '%.4f'|format(h.score) }} · rank {{ loop.index }}</div>
        <div class="snippet">{{ h.snippet }}</div>
      </div>
    {% endfor %}
  {% endif %}
</body>
</html>
"""


@app.route("/")
def home():
    q = request.args.get("q", "").strip()
    # default = required system: TF-IDF cosine, no boost, no synonyms
    model = request.args.get("model", "tfidf")
    if model not in ("bm25", "tfidf"):
        model = "tfidf"
    syn = request.args.get("syn") == "1"
    boost = request.args.get("boost") == "1"
    if not q:
        idx = se.load_index()
        return render_template_string(PAGE, q="", status="empty", model=model,
                                      num_indexed=idx["N"], results=[], terms=None,
                                      elapsed=None, syn=syn, boost=boost, expanded=None)
    r = se.search(q, top_k=10, model=model,
                  title_boost=se.TITLE_BOOST if boost else 0.0, use_synonyms=syn)
    return render_template_string(PAGE, q=q, status=r["status"], model=model,
                                  num_indexed=r["num_indexed"], results=r["results"],
                                  terms=r.get("terms"), elapsed=r["elapsed_ms"],
                                  syn=syn, boost=boost, expanded=r.get("expanded"))


if __name__ == "__main__":
    app.run(debug=False, port=5000)
