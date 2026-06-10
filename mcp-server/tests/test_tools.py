"""Tool tests — exercise the MCP tool implementations end-to-end."""

from __future__ import annotations

import pytest

from re_library_mcp.loader import load_all
from re_library_mcp.search import SearchIndex
from re_library_mcp.tools import ToolRegistry


@pytest.fixture(scope="module")
def registry() -> ToolRegistry:
    entries = load_all()
    return ToolRegistry(SearchIndex.build(entries))


def test_search_re_returns_top_hit_for_known_query(registry: ToolRegistry) -> None:
    hits = registry.search_re("APK structure", max_results=3)
    assert hits, "expected at least one hit for 'APK structure'"
    slugs = [h["slug"] for h in hits]
    assert "android/01-apk-structure" in slugs


def test_search_re_respects_category_filter(registry: ToolRegistry) -> None:
    hits = registry.search_re("packing", category="packers", max_results=3)
    assert hits
    for h in hits:
        assert h["category"] == "packers"


def test_search_re_unknown_category_raises(registry: ToolRegistry) -> None:
    with pytest.raises(ValueError):
        registry.search_re("anything", category="bogus-category")


def test_get_entry_returns_full_body(registry: ToolRegistry) -> None:
    e = registry.get_entry("android/01-apk-structure")
    assert e["title"] == "APK Structure"
    assert e["category"] == "android"
    assert "AndroidManifest" in e["body_markdown"]


def test_get_entry_unknown_raises(registry: ToolRegistry) -> None:
    with pytest.raises(KeyError):
        registry.get_entry("does/not-exist")


def test_list_categories_has_eight(registry: ToolRegistry) -> None:
    # v2.7.0 (2026-06-06) — three new categories. The canonical
    # count is now 12 (8 originals + 3 from v2.7.0 + 1 from v2.9.0 re-ai-mcp).
    cats = registry.list_categories()
    assert len(cats) == 12
    by_name = {c["name"]: c["count"] for c in cats}
    assert by_name["android"] >= 1
    assert by_name["drm"] >= 1
    assert by_name["sandbox-emulation"] >= 1
    assert by_name["uefi-firmware-re"] >= 1
    assert by_name["reference-awesome-lists"] >= 1


def test_list_entries_filters_by_category(registry: ToolRegistry) -> None:
    entries = registry.list_entries("tools")
    assert entries
    for e in entries:
        assert e["slug"].startswith("tools/")


def test_list_entries_unknown_category_raises(registry: ToolRegistry) -> None:
    with pytest.raises(ValueError):
        registry.list_entries("bogus-category")


def test_get_anti_analysis_techniques(registry: ToolRegistry) -> None:
    out = registry.get_anti_analysis_techniques()
    assert out
    for e in out:
        assert e["category"] == "anti-analysis"
        assert e["body_markdown"].strip()


def test_get_anti_analysis_techniques_platform_filter(registry: ToolRegistry) -> None:
    out = registry.get_anti_analysis_techniques(platform="linux")
    assert out
    for e in out:
        assert "linux" in e["platforms"]


def test_search_re_platform_filter(registry: ToolRegistry) -> None:
    hits = registry.search_re("debug", platform="android", max_results=3)
    # Every returned hit must have 'android' in the underlying entry's
    # platforms. The hit payload is the SearchHit dict, which doesn't
    # include platforms — we re-check via the index.
    for h in hits:
        e = registry.index.get(h["slug"])
        assert e is not None
        assert "android" in e.frontmatter.platforms
