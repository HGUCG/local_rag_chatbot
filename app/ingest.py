
import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict

from pdfminer.high_level import extract_text as pdf_extract_text
from docx import Document

# Einfache Satz- und Token-Funktionen ohne NLTK
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ0-9])')
_WORD_SPLIT = re.compile(r"[^a-zA-Z0-9äöüÄÖÜß]+")


def read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return p.read_text(encoding='latin-1', errors='ignore')


def read_pdf_file(p: Path) -> str:
    try:
        return pdf_extract_text(str(p))
    except Exception as e:
        return ""


def read_docx_file(p: Path) -> str:
    try:
        doc = Document(str(p))
        return "
".join([para.text for para in doc.paragraphs])
    except Exception:
        return ""


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    # Paragraphen-orientiert, fallback auf sliding window
    paragraphs = [t.strip() for t in re.split(r"
\s*
+", text) if t.strip()]
    chunks: List[str] = []
    for para in paragraphs:
        if len(para) <= chunk_size:
            chunks.append(para)
        else:
            start = 0
            while start < len(para):
                end = min(start + chunk_size, len(para))
                chunks.append(para[start:end])
                if end == len(para):
                    break
                start = max(end - overlap, 0)
    return chunks


def detect_pages_for_pdf(text: str) -> List[int]:
    # pdfminer liefert Fließtext; ohne Layout nehmen wir Seite unbekannt => -1
    return []


def ingest(data_dir: str, index_path: str, chunk_size: int = 800, overlap: int = 120) -> int:
    root = Path(data_dir)
    idx_path = Path(index_path)
    idx_path.parent.mkdir(parents=True, exist_ok=True)

    supported = {'.txt', '.md', '.pdf', '.docx'}
    count = 0
    with open(idx_path, 'w', encoding='utf-8') as out:
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext not in supported:
                continue

            if ext in {'.txt', '.md'}:
                text = read_text_file(p)
                page_info = None
            elif ext == '.pdf':
                text = read_pdf_file(p)
                page_info = None  # Unknown page mapping
            elif ext == '.docx':
                text = read_docx_file(p)
                page_info = None
            else:
                continue

            if not text or not text.strip():
                continue

            chunks = split_into_chunks(text, chunk_size, overlap)
            for i, ch in enumerate(chunks):
                rec = {
                    'id': f"{p.name}:{i}",
                    'text': ch,
                    'source_path': str(p),
                    'source_name': p.name,
                    'page': page_info if page_info is not None else None,
                    'chunk_idx': i,
                }
                out.write(json.dumps(rec, ensure_ascii=False) + "
")
                count += 1
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data-dir', default='data')
    ap.add_argument('--index-path', default='index.jsonl')
    ap.add_argument('--chunk-size', type=int, default=800)
    ap.add_argument('--overlap', type=int, default=120)
    ap.add_argument('--reset', action='store_true')
    args = ap.parse_args()

    if args.reset and os.path.exists(args.index_path):
        os.remove(args.index_path)

    n = ingest(args.data_dir, args.index_path, args.chunk_size, args.overlap)
    print(f"Index erstellt: {n} Chunks -> {args.index_path}")

if __name__ == '__main__':
    main()
