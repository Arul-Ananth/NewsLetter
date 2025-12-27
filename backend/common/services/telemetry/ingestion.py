from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def file_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if size <= 0:
        return []
    if overlap >= size:
        overlap = 0
    chunks: list[str] = []
    idx = 0
    while idx < len(text):
        chunk = text[idx : idx + size]
        if chunk.strip():
            chunks.append(chunk.strip())
        idx += max(size - overlap, 1)
    return chunks


def extract_text_from_file(path: Path) -> tuple[str | None, str | None]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore"), None
        if suffix == ".html":
            try:
                import trafilatura

                downloaded = path.read_text(encoding="utf-8", errors="ignore")
                extracted = trafilatura.extract(downloaded)
                return extracted or "", None
            except Exception as exc:  # pragma: no cover - optional dependency
                return None, f"HTML extraction failed: {exc}"
        if suffix == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(str(path))
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
                return text, None
            except Exception as exc:  # pragma: no cover - optional dependency
                return None, f"PDF extraction failed: {exc}"
        if suffix == ".docx":
            try:
                from docx import Document

                doc = Document(str(path))
                text = "\n".join(p.text for p in doc.paragraphs)
                return text, None
            except Exception as exc:  # pragma: no cover - optional dependency
                return None, f"DOCX extraction failed: {exc}"
        return None, f"Unsupported file type: {suffix}"
    except Exception as exc:
        logger.exception("File extraction failed for %s: %s", path, exc)
        return None, str(exc)
