"""Unit tests for the ingestion building blocks — no app, no HTTP."""
import pytest

from app.ai.ingestion.chunker import chunk_pages
from app.ai.ingestion.cleaner import clean_text
from app.ai.ingestion.parsers import (
    PageText,
    UnsupportedFileTypeError,
    sniff_and_parse,
)


def test_cleaner_dehyphenates_and_collapses():
    dirty = "The manage-\nment policy   applies\nto all employees.\n\n\n\nNext para."
    cleaned = clean_text(dirty)
    assert "management" in cleaned
    assert "   " not in cleaned
    assert "\n\n\n" not in cleaned
    # single newline inside a paragraph became a space
    assert "applies to all employees" in cleaned


def test_txt_parsing():
    pages = sniff_and_parse("notes.txt", b"hello world")
    assert pages == [PageText(page_number=1, text="hello world")]


def test_extension_spoofing_rejected():
    # An .exe renamed to .pdf: extension says pdf, magic bytes say otherwise
    with pytest.raises(UnsupportedFileTypeError):
        sniff_and_parse("report.pdf", b"MZ\x90\x00 not a pdf at all")


def test_unsupported_extension_rejected():
    with pytest.raises(UnsupportedFileTypeError):
        sniff_and_parse("archive.zip", b"PK\x03\x04")


def test_chunker_respects_size_and_pages():
    long_text = ("Lorem ipsum dolor sit amet. " * 300).strip()  # ~8400 chars
    pages = [PageText(1, long_text), PageText(2, "Short second page.")]
    chunks = chunk_pages(pages, chunk_size_chars=3200, overlap_chars=480)

    assert len(chunks) >= 3  # page 1 split into multiple
    assert all(len(c.content) <= 3200 for c in chunks)
    assert chunks[-1].page_number == 2  # page metadata preserved
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_chunker_overlap_exists():
    text = ("word " * 2000).strip()
    chunks = chunk_pages([PageText(1, text)], chunk_size_chars=1000, overlap_chars=200)
    # consecutive chunks share content (the overlap window)
    tail = chunks[0].content[-100:]
    assert tail in chunks[1].content
