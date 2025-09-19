
# Lokaler RAG-Chatbot (Container-fähig)

Ein minimaler, komplett lokaler Chatbot, der **eigene Dateien** (TXT, MD, PDF, DOCX) einliest, eine einfache **BM25-Retrieval**-Suche verwendet und Antworten mit **Quellenzitaten** liefert. Optional kann ein **lokales LLM via Ollama** für die Antwort-Synthese angebunden werden. Ohne LLM läuft der Bot **rein lokal** und **offline** (extraktiv).

## Features
- Läuft lokal oder im Container (Dockerfile + docker-compose)
- Ingest von lokalen Dateien aus `./data` (rekursiv)
- Unterstützung: `.txt`, `.md`, `.pdf` (pdfminer), `.docx`
- Index als `index.jsonl` (einfach portabel)
- BM25-Retrieval (rank_bm25)
- API (Flask) + minimale Web-UI
- Zitate inkl. Dateiname und (bei PDFs) Seite
- Optional: **Ollama** (lokales LLM) zur Antwortformulierung (`OLLAMA_MODEL`)

## Schnellstart (ohne Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Index aufbauen (liest ./data)
python -m app.ingest --data-dir data --index-path index.jsonl --reset
# Server starten
python -m app.main
# Öffnen: http://localhost:8000
```

## Schnellstart (Docker)
```bash
# Build
docker build -t local-rag-chatbot:latest .
# Start (mit Mount des lokalen data-Ordners)
docker run --rm -p 8000:8000   -e BUILD_INDEX_ON_START=true   -v $(pwd)/data:/app/data   --name ragbot local-rag-chatbot:latest
# Öffnen: http://localhost:8000
```

### Docker Compose (mit optionaler Ollama-Integration)
```bash
docker compose up --build
```
- **Nur App**: Die App läuft sofort. Daten liegen in `./data`. Beim Start wird der Index gebaut, wenn `BUILD_INDEX_ON_START=true` gesetzt ist.
- **Optional Ollama**: In `docker-compose.yml` ist ein `ollama`-Service auskommentiert. Bei Internet- und Modelzugang kann man den aktivieren und z. B. `llama3.2:3b` ziehen. Die App nutzt dann `OLLAMA_MODEL` zur Antwortsynthese.

## Umgebungsvariablen
| Variable | Default | Beschreibung |
|---|---|---|
| `HOST` | `0.0.0.0` | Bind-Adresse der App |
| `PORT` | `8000` | Port der App |
| `DATA_DIR` | `data` | Ordner mit Quell-Dateien |
| `INDEX_PATH` | `index.jsonl` | Pfad für den Index |
| `CHUNK_SIZE` | `800` | Zeichen pro Chunk |
| `CHUNK_OVERLAP` | `120` | Überlappung in Zeichen |
| `TOP_K` | `5` | Anzahl der Chunks für die Antwort |
| `BUILD_INDEX_ON_START` | `false` | Index beim Start neu bauen |
| `OLLAMA_HOST` | `http://ollama:11434` | Ziel-Host für Ollama (oder `http://host.docker.internal:11434`) |
| `OLLAMA_MODEL` | *(leer)* | Wenn gesetzt, verwendet die App ein lokales LLM über Ollama |

## API
- `POST /api/chat` – Body: `{ "message": "...", "history": [ {"role":"user|assistant", "content":"..."}, ... ] }`
- `POST /api/reindex` – baut den Index neu

## Erweiterungen
- S3/MinIO: Man kann vor Ingest Dateien aus einem lokalen S3 (MinIO) syncen (z. B. via `boto3`). Aus Einfachheitsgründen nicht enthalten, aber leicht ergänzbar.

## Hinweis
- Ohne LLM generiert der Bot extraktive Antworten aus Top-Snippets + Quellenangaben. Für natürlichere Formulierungen ein lokales LLM via Ollama setzen.

