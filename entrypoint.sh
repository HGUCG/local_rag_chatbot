
#!/usr/bin/env bash
set -e

: "${BUILD_INDEX_ON_START:=false}"
: "${DATA_DIR:=data}"
: "${INDEX_PATH:=index.jsonl}"

if [ "$BUILD_INDEX_ON_START" = "true" ]; then
  echo "[entrypoint] Building index from $DATA_DIR -> $INDEX_PATH"
  python -m app.ingest --data-dir "$DATA_DIR" --index-path "$INDEX_PATH" --reset || true
fi

echo "[entrypoint] Starting server on 0.0.0.0:${PORT:-8000}"
exec gunicorn -w 2 -b 0.0.0.0:${PORT:-8000} app.main:app
