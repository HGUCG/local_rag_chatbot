
import os

HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '8000'))
DATA_DIR = os.getenv('DATA_DIR', 'data')
INDEX_PATH = os.getenv('INDEX_PATH', 'index.jsonl')
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '800'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '120'))
TOP_K = int(os.getenv('TOP_K', '5'))
OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')  # None => kein LLM
