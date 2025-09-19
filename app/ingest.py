import argparse
import json
import os
import re
from pathlib import Path
from typing import List

from docx import Document
from pdfminer.high_level import extract_text as pdf_extract_text


PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1", errors="ignore")


def read_pdf_file(path: Path) -> str:
    try:
        return pdf_extract_text(str(path))
    except Exception:
        return ""


def read_docx_file(path: Path) -> str:
    try:
        document = Document(str(path))
        return "\n".join(para.text for para in document.paragraphs)
    except Exception:
        return ""


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT_RE.split(text) if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()]

    chunks: List[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
            continue

        start = 0
        text_length = len(paragraph)
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(paragraph[start:end])
            if end == text_length:
                break
            if overlap >= chunk_size:
                start = end
            else:
                start = max(end - overlap, 0)
    return chunks


def ingest(data_dir: str, index_path: str, chunk_size: int = 800, overlap: int = 120) -> int:
    data_root = Path(data_dir)
    index_file = Path(index_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".txt", ".md", ".pdf", ".docx"}
    chunk_count = 0

    with index_file.open("w", encoding="utf-8") as handle:
        for path in data_root.rglob("*"):
            if not path.is_file():
                continue

            extension = path.suffix.lower()
            if extension not in supported_extensions:
                continue

            if extension in {".txt", ".md"}:
                text = read_text_file(path)
                page_info = None
            elif extension == ".pdf":
                text = read_pdf_file(path)
                page_info = None
            elif extension == ".docx":
                text = read_docx_file(path)
                page_info = None
            else:
                continue

            if not text or not text.strip():
                continue

            for idx, chunk in enumerate(split_into_chunks(text, chunk_size, overlap)):
                record = {
                    "id": f"{path.name}:{idx}",
                    "text": chunk,
                    "source_path": str(path),
                    "source_name": path.name,
                    "page": page_info,
                    "chunk_idx": idx,
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                chunk_count += 1

    return chunk_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--index-path", default="index.jsonl")
    parser.add_argument("--chunk-size", type=int, default=800)
    parser.add_argument("--overlap", type=int, default=120)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if args.reset and os.path.exists(args.index_path):
        os.remove(args.index_path)

    total = ingest(args.data_dir, args.index_path, args.chunk_size, args.overlap)
    print(f"Index erstellt: {total} Chunks -> {args.index_path}")


if __name__ == "__main__":
    main()
