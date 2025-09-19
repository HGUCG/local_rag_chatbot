import os
from typing import List, Dict, Any
import requests

from app.retriever import Retriever
from app.config import TOP_K, OLLAMA_HOST, OLLAMA_MODEL


SYSTEM_PROMPT = (
    "Du bist ein hilfreicher, präziser Assistent. Verwende ausschließlich die bereitgestellten Kontexte, "
    "um die Frage zu beantworten. Zitiere Quellen (Dateiname, evtl. Seite). Wenn die Antwort in den Kontexten "
    "nicht enthalten ist, sage knapp, dass die Information nicht vorliegt. Antworte auf Deutsch."
)


def _synthesize_with_ollama(question: str, contexts: List[Dict[str, Any]]) -> str:
    prompt = SYSTEM_PROMPT + ""
    prompt += "Kontexte:\n"
    for i, c in enumerate(contexts, 1):
        meta = f"{c.get('source_name')}"
        prompt += f"[{i}] ({meta})\n{c['text']}\n\n"
    prompt += f"Frage: {question}\n\nAntwort (mit Quellen in eckigen Klammern, z. B. [1], [2]):"

    try:
        resp = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "")
    except Exception as e:
        return "(Hinweis: LLM nicht erreichbar)\n\n" + _synthesize_extractive(question, contexts)


def _synthesize_extractive(question: str, contexts: List[Dict[str, Any]]) -> str:
    # Einfache extraktive Antwort: Liste der Top-Snippets mit Zitaten
    lines = [
        "Ich habe folgende relevanten Stellen in deinen lokalen Quellen gefunden:",
        "",
    ]
    for i, c in enumerate(contexts, 1):
        cite = c.get('source_name', 'Quelle')
        if c.get('page') is not None:
            cite += f", Seite {c['page']}"
        lines.append(f"[{i}] {cite}:")
        snippet = c['text'].strip().replace('\n', ' ')
        if len(snippet) > 500:
            snippet = snippet[:500] + '…'
        lines.append(f"    {snippet}")
        lines.append("")
    lines.append("Tipp: Aktiviere ein lokales LLM via Ollama (Umgebungsvariable OLLAMA_MODEL), um eine zusammenhängende Antwort zu erhalten.")
    return "\n".join(lines)


class ChatEngine:
    def __init__(self, retriever: Retriever):
        self.retriever = retriever

    def answer(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        results = self.retriever.search(message, k=TOP_K)
        if not results:
            return {
                'answer': "Ich habe in deinen lokalen Quellen keine passenden Stellen gefunden. Prüfe bitte den Datenordner und den Index.",
                'citations': [],
            }

        if OLLAMA_MODEL:
            answer = _synthesize_with_ollama(message, results)
        else:
            answer = _synthesize_extractive(message, results)

        citations = [
            {
                'source_name': r['source_name'],
                'source_path': r['source_path'],
                'page': r.get('page'),
                'score': r['score'],
                'chunk_idx': r.get('chunk_idx'),
            }
            for r in results
        ]

        return {
            'answer': answer,
            'citations': citations,
        }
