"""Text normalization before chunking.

Garbage in → garbage embeddings → garbage retrieval. Most RAG demos skip
this and silently pay for it in answer quality.
"""
import re
import unicodedata


def clean_text(text: str) -> str:
    # Normalize unicode (ﬁ → fi, fancy quotes → plain, etc.)
    text = unicodedata.normalize("NFKC", text)
    # Re-join words hyphenated across line breaks: "manage-\nment" → "management"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Single newlines inside paragraphs → spaces (PDF extraction artifact)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Collapse runs of spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines to paragraph breaks
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
