
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# System deps (optional minimal)
RUN apt-get update && apt-get install -y --no-install-recommends     tini   && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Nicht-root (optional)
# RUN useradd -ms /bin/bash appuser && chown -R appuser:appuser /app
# USER appuser

EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["bash", "./entrypoint.sh"]
