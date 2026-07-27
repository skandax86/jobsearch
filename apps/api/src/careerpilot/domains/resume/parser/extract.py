"""Extract plain text from resume source files."""

from __future__ import annotations

import io


class ExtractionError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def extract_text(*, data: bytes, mime_type: str) -> str:
    mime = (mime_type or "").split(";")[0].strip().lower()
    if mime == "application/pdf":
        return _extract_pdf(data)
    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return _extract_docx(data)
    if mime == "application/msword":
        raise ExtractionError(
            "Legacy .doc files are uploaded but not parsed yet. Please upload PDF or DOCX."
        )
    raise ExtractionError(f"Unsupported mime type for parsing: {mime}")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("Could not read PDF file.") from exc

    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    combined = "\n".join(parts).strip()
    if not combined:
        raise ExtractionError("No extractable text found in PDF (it may be image-only).")
    return combined


def _extract_docx(data: bytes) -> str:
    from docx import Document

    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("Could not read DOCX file.") from exc

    parts = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    combined = "\n".join(parts).strip()
    if not combined:
        raise ExtractionError("No extractable text found in DOCX.")
    return combined
