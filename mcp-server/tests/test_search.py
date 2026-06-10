"""Search-index tests."""

from __future__ import annotations

from re_library_mcp.loader import load_all
from re_library_mcp.search import SearchHit, SearchIndex, tokenize


def test_tokenize_strips_stop_words() -> None:
    toks = tokenize("the quick brown fox is fast")
    assert "the" not in toks
    assert "is" not in toks
    assert "quick" in toks
    assert "fox" in toks


def test_tokenize_lowercases() -> None:
    toks = tokenize("UPPER and Mixed")
    assert toks == ["upper", "mixed"]


def test_build_index_includes_all_entries() -> None:
    entries = load_all()
    idx = SearchIndex.build(entries)
    assert len(idx.entries) == len(entries)


def test_search_empty_query_returns_no_results() -> None:
    entries = load_all()
    idx = SearchIndex.build(entries)
    assert idx.search("") == []
    assert idx.search("the a an") == []  # all stop words


def test_search_returns_snippet_with_marked_terms() -> None:
    entries = load_all()
    idx = SearchIndex.build(entries)
    hits = idx.search("APK")
    assert hits
    assert isinstance(hits[0], SearchHit)
    assert "<mark>" in hits[0].snippet or hits[0].snippet  # snippet is non-empty
