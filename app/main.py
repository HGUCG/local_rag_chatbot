from flask import Flask, request, jsonify, render_template
import os

from app.config import HOST, PORT, DATA_DIR, INDEX_PATH
from .retriever import Retriever
from .chat import ChatEngine

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
    from .ingest import ingest
    # Env gesteuert
    from .config import CHUNK_SIZE, CHUNK_OVERLAP
    n = ingest(DATA_DIR, INDEX_PATH, CHUNK_SIZE, CHUNK_OVERLAP)
    retriever.reload()
    return jsonify({"indexed_chunks": n})


def main():
    app.run(host=HOST, port=PORT, debug=False)


if __name__ == '__main__':
    main()
