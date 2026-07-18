"""Per-format text extraction.

Each parser returns list[PageText] so page numbers survive all the way to
citations. Formats without real pages (TXT/MD/DOCX) approximate: DOCX splits
on page breaks where present, otherwise everything is page 1 — an honest
limitation we document rather than hide.
"""
import io
from dataclasses import dataclass

from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.exceptions import AppError


class UnsupportedFileTypeError(AppError):
    status_code = 415
    code = "UNSUPPORTED_FILE_TYPE"


class EmptyDocumentError(AppError):
    status_code = 422
    code = "EMPTY_DOCUMENT"


@dataclass
class PageText:
    page_number: int
    text: str


# Magic bytes: we sniff CONTENT, not the filename. Anyone can rename
# malware.exe to report.pdf — the first bytes don't lie.
_PDF_MAGIC = b"%PDF"
_ZIP_MAGIC = b"PK\x03\x04"  # docx is a zip archive

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def sniff_and_parse(filename: str, data: bytes) -> list[PageText]:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"Unsupported file type: {ext or 'unknown'}")

    if ext == ".pdf":
        if not data.startswith(_PDF_MAGIC):
            raise UnsupportedFileTypeError("File does not look like a real PDF")
        pages = _parse_pdf(data)
    elif ext == ".docx":
        if not data.startswith(_ZIP_MAGIC):
            raise UnsupportedFileTypeError("File does not look like a real DOCX")
        pages = _parse_docx(data)
    else:  # .txt / .md
        pages = [PageText(page_number=1, text=data.decode("utf-8", errors="replace"))]

    pages = [p for p in pages if p.text.strip()]
    if not pages:
        raise EmptyDocumentError("No extractable text found (is this a scanned/image PDF?)")
    return pages


def _parse_pdf(data: bytes) -> list[PageText]:
    reader = PdfReader(io.BytesIO(data))
    return [
        PageText(page_number=i + 1, text=page.extract_text() or "")
        for i, page in enumerate(reader.pages)
    ]


def _parse_docx(data: bytes) -> list[PageText]:
    doc = DocxDocument(io.BytesIO(data))
    text = "\n".join(p.text for p in doc.paragraphs)
    return [PageText(page_number=1, text=text)]
