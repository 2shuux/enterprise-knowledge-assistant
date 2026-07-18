"""Split cleaned pages into overlapping chunks.

Why chunk at all? Embeddings represent ONE idea well; a 50-page document
averaged into a single vector matches nothing precisely. ~800 tokens per
chunk keeps each vector focused; the ~120-token overlap ensures a sentence
straddling a boundary is fully present in at least one chunk.

The splitter is hierarchical: try paragraph breaks first, then lines, then
sentences, then words — so chunks break at natural seams, not mid-sentence.
"""
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.ai.ingestion.parsers import PageText


@dataclass
class Chunk:
    chunk_index: int
    page_number: int
    content: str
    token_estimate: int  # chars/4 heuristic — fine for budgeting, not billing


def chunk_pages(
    pages: list[PageText], chunk_size_chars: int = 3200, overlap_chars: int = 480
) -> list[Chunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_chars,
        chunk_overlap=overlap_chars,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[Chunk] = []
    index = 0
    for page in pages:  # split per page so every chunk keeps its page number
        for piece in splitter.split_text(page.text):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append(
                Chunk(
                    chunk_index=index,
                    page_number=page.page_number,
                    content=piece,
                    token_estimate=max(1, len(piece) // 4),
                )
            )
            index += 1
    return chunks
