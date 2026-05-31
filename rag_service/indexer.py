import os
import json
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
META_PATH = DATA_DIR / "metadata.json"
PDF_PATH = os.getenv("RAG_PDF_PATH", str(Path.cwd() / "2025学生手册.pdf"))

CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))


def _read_pdf_text(pdf_path: str) -> list[dict]:
    reader = PdfReader(pdf_path)
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": idx, "text": text})
    return pages


def _chunk_text(text: str, chunk_size: int, overlap: int) -> Iterable[str]:
    clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if not clean:
        return []
    step = max(chunk_size - overlap, 1)
    chunks = []
    for start in range(0, len(clean), step):
        chunk = clean[start : start + chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks


def build_index(pdf_path: str) -> None:
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    pages = _read_pdf_text(pdf_path)
    if not pages:
        raise ValueError("No readable text found in PDF.")

    metadata = []

    for page in pages:
        for chunk in _chunk_text(page["text"], CHUNK_SIZE, CHUNK_OVERLAP):
            metadata.append({
                "text": chunk,
                "page": page["page"],
                "source": Path(pdf_path).name,
            })

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with META_PATH.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Indexed {len(metadata)} chunks from {pdf_path}")


if __name__ == "__main__":
    build_index(PDF_PATH)
