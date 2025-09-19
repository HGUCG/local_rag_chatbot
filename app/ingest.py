import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from docx import Document
from pdfminer.high_level import extract_pages, extract_text as pdf_extract_text
from pdfminer.layout import LTTextContainer


PARAGRAPH_SPLIT_RE = re.compile(r"\n\s*\n+")
SINGLE_NEWLINE_RE = re.compile(r"(?<!\n)\n(?!\n)")
WHITESPACE_RE = re.compile(r"[ \t\f\v]+")


def normalize_text(text: str) -> str:
    """Collapse whitespace, remove soft hyphenation and join short lines."""

    if not text:
        return ""

    text = text.replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00ad", "")  # soft hyphen
    text = re.sub(r"-\s*\n", "", text)  # unwrap hyphenated line breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = WHITESPACE_RE.sub(" ", text)
    text = SINGLE_NEWLINE_RE.sub(" ", text)
    paragraphs = [p.strip() for p in PARAGRAPH_SPLIT_RE.split(text) if p.strip()]
    if not paragraphs:
        return text.strip()
    return "\n\n".join(paragraphs)


def read_text_file(path: Path) -> str:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw = path.read_text(encoding="latin-1", errors="ignore")
    return normalize_text(raw)


def read_docx_file(path: Path) -> str:
    try:
        document = Document(str(path))
    except Exception:
        return ""
    text = "\n".join(para.text for para in document.paragraphs)
    return normalize_text(text)


def read_pdf_file(path: Path) -> List[Tuple[Optional[int], str]]:
    pages: List[Tuple[Optional[int], str]] = []
    try:
        for page_number, layout in enumerate(extract_pages(str(path)), start=1):
            segments: List[str] = []
            for element in layout:
                if isinstance(element, LTTextContainer):
                    segments.append(element.get_text())
            page_text = normalize_text("\n".join(segments))
            if page_text:
                pages.append((page_number, page_text))
    except Exception:
        pages = []

    if pages:
        return pages

    # Fallback: best-effort plain text extraction if layout parsing fails
    try:
        fallback_text = normalize_text(pdf_extract_text(str(path)))
    except Exception:
        fallback_text = ""
    return [(None, fallback_text)] if fallback_text else []


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    if not text:
        return []

    text = text.strip()
    if not text:
        return []

    chunks: List[str] = []
    total_length = len(text)
    start = 0
    previous_start = -1

    while start < total_length and start != previous_start:
        previous_start = start
        end = min(start + chunk_size, total_length)

        if end < total_length:
            split = _find_split_position(text, start, end)
            if split is not None and split > start:
                end = split

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= total_length:
            break

        if overlap >= chunk_size:
            next_start = end
        else:
            next_start = max(end - overlap, 0)

        while next_start > start and next_start > 0 and not text[next_start - 1].isspace():
            next_start -= 1
        while next_start < total_length and text[next_start].isspace():
            next_start += 1

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks


def _find_split_position(text: str, start: int, end: int) -> Optional[int]:
    window = text[start:end]
    patterns: Iterable[Tuple[str, int]] = [
        ("\n\n", 0),
        (". ", 1),
        ("? ", 1),
        ("! ", 1),
        ("\n", 0),
        (" ", 0),
    ]

    for pattern, offset in patterns:
        idx = window.rfind(pattern)
        if idx > 0:
            return start + idx + offset
    return None


def split_into_chunks(text: str, chunk_size: int, overlap: int) -> List[str]:
    normalized = normalize_text(text)
    return chunk_text(normalized, chunk_size, overlap)


def load_sections(path: Path) -> List[Tuple[Optional[int], str]]:
    extension = path.suffix.lower()
    if extension in {".txt", ".md"}:
        text = read_text_file(path)
        return [(None, text)] if text else []
    if extension == ".docx":
        text = read_docx_file(path)
        return [(None, text)] if text else []
    if extension == ".pdf":
        return read_pdf_file(path)
    return []


def ingest(data_dir: str, index_path: str, chunk_size: int = 800, overlap: int = 120) -> int:
    data_root = Path(data_dir)
    index_file = Path(index_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = (
        index_file.with_suffix(index_file.suffix + ".tmp")
        if index_file.suffix
        else index_file.with_name(index_file.name + ".tmp")
    )
    if tmp_path.exists():
        tmp_path.unlink()

    chunk_count = 0

    with tmp_path.open("w", encoding="utf-8") as handle:
        for path in sorted(data_root.rglob("*")):
            if not path.is_file():
                continue

            sections = load_sections(path)
            if not sections:
                continue

            chunk_idx = 0
            for page_info, section_text in sections:
                for chunk in split_into_chunks(section_text, chunk_size, overlap):
                    record = {
                        "id": f"{path.name}:{chunk_idx}",
                        "text": chunk,
                        "source_path": str(path),
                        "source_name": path.name,
                        "page": page_info,
                        "chunk_idx": chunk_idx,
                    }
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    chunk_count += 1
                    chunk_idx += 1

    tmp_path.replace(index_file)
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
