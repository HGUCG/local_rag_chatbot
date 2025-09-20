from pathlib import Path
import sys

# Allow running this module directly (e.g. ``python app/main.py``) by ensuring
# the repository root is on ``sys.path`` so ``import app`` works even when
# Python sets ``__package__`` to ``None``.
if __package__ is None or __package__ == "":  # pragma: no cover - runtime setup
    package_dir = Path(__file__).resolve().parent
    project_root = package_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from flask import Flask, request, jsonify, render_template

from app.config import HOST, PORT, DATA_DIR, INDEX_PATH
from app.retriever import Retriever
from app.chat import ChatEngine

app = Flask(__name__, template_folder='templates', static_folder='static')

retriever = Retriever(INDEX_PATH)
engine = ChatEngine(retriever)


@app.route('/')
def index():
    return render_template('index.html')


@app.post('/api/chat')
def api_chat():
    data = request.get_json(force=True)
    message = data.get('message', '')
    history = data.get('history', [])
    res = engine.answer(message, history)
    return jsonify(res)


@app.post('/api/reindex')
def api_reindex():
    # Lazy import to avoid cost at import time
    from app.ingest import ingest
    # Env gesteuert
    from app.config import CHUNK_SIZE, CHUNK_OVERLAP
    n = ingest(DATA_DIR, INDEX_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
    retriever.reload()
    return jsonify({"indexed_chunks": n})


def main():
    app.run(host=HOST, port=PORT, debug=False)


if __name__ == '__main__':
    main()
