"""Unit tests for citation parsing + confidence heuristic — pure functions."""
from app.ai.vectorstore.base import VectorHit
from app.services.rag_service import _confidence, _extract_cited_hits


def hit(i: int, score: float = 0.9) -> VectorHit:
    return VectorHit(id=f"c{i}", score=score, text=f"chunk {i}", metadata={})


def test_citation_extraction_ordered_and_deduped():
    hits = [hit(1), hit(2), hit(3)]
    answer = "Fact one [2]. Fact two [1][2]. Fact three [3]."
    cited = _extract_cited_hits(answer, hits)
    assert [c.id for c in cited] == ["c2", "c1", "c3"]  # first-mention order, no dupes


def test_out_of_range_citations_dropped():
    hits = [hit(1)]
    cited = _extract_cited_hits("Real [1] but fake [7] and [99].", hits)
    assert [c.id for c in cited] == ["c1"]  # model cannot invent sources


def test_confidence_zero_when_nothing_cited():
    assert _confidence("An answer with no citations.", []) == 0.0


def test_confidence_rises_with_coverage():
    low = _confidence("Cited [1]. Uncited. Uncited. Uncited.", [hit(1)])
    high = _confidence("Cited [1]. Also cited [1]. And this [1].", [hit(1)])
    assert 0 < low < high <= 1.0
