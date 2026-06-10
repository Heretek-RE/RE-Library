"""MCP tool implementations.

Each public function here corresponds to one MCP tool. The ``server``
module registers them with the SDK; the functions are pure
(input → output) so they can also be called directly from tests.
"""

from __future__ import annotations

from typing import Any

from re_library_mcp.loader import CATEGORIES
from re_library_mcp.schema import Entry
from re_library_mcp.search import SearchHit, SearchIndex

# Short description for each tool — surfaced to the LLM via the
# ``list_tools`` response. These are the strings that decide whether a
# model calls the tool, so they should be terse and unambiguous.
SEARCH_RE_DESCRIPTION = (
    "Search RE-Library entries by free-text query. Optional filters: "
    "category (one of android, ios, anti-analysis, drm, packers, tools, "
    "native, web-hybrid) and platform (one of android, ios, linux, "
    "windows, macos, web). Returns up to max_results hits with title, "
    "category, snippet, and a relevance score."
)
GET_ENTRY_DESCRIPTION = (
    "Fetch a single RE-Library entry by its ID. The ID is the "
    "<category>/<NN>-<slug> form, e.g. 'android/01-apk-structure'. "
    "Returns the full frontmatter and the raw markdown body."
)
LIST_CATEGORIES_DESCRIPTION = (
    "List all RE-Library categories with their entry counts."
)
LIST_ENTRIES_DESCRIPTION = (
    "List all entries in a single RE-Library category. Returns "
    "{slug, title, summary, difficulty} for each — use get_entry to "
    "fetch a full entry."
)
GET_ANTI_ANALYSIS_TECHNIQUES_DESCRIPTION = (
    "Convenience aggregator: return all anti-analysis entries, "
    "optionally filtered to a single platform. Returns full entries."
)


def _entry_to_dict(entry: Entry) -> dict[str, Any]:
    """Serialise an entry to a JSON-friendly dict."""
    return {
        "slug": entry.id,
        "title": entry.frontmatter.title,
        "category": entry.frontmatter.category,
        "platforms": list(entry.frontmatter.platforms),
        "difficulty": entry.frontmatter.difficulty,
        "tags": list(entry.frontmatter.tags),
        "summary": entry.frontmatter.summary,
        "updated": entry.frontmatter.updated.isoformat(),
        "related": list(entry.frontmatter.related),
        "body_markdown": entry.body,
    }


def _entry_summary(entry: Entry) -> dict[str, Any]:
    return {
        "slug": entry.id,
        "title": entry.frontmatter.title,
        "summary": entry.frontmatter.summary,
        "difficulty": entry.frontmatter.difficulty,
    }


class ToolRegistry:
    """Holds the ``SearchIndex`` and exposes the MCP tool functions."""

    def __init__(self, index: SearchIndex) -> None:
        self.index = index

    # --- tools ---------------------------------------------------------

    def search_re(
        self,
        query: str,
        category: str | None = None,
        platform: str | None = None,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """See ``SEARCH_RE_DESCRIPTION``."""
        if category is not None and category not in CATEGORIES:
            raise ValueError(
                f"unknown category {category!r}; expected one of {sorted(CATEGORIES)}"
            )
        # ``platform`` is a post-filter — the index doesn't track it, so
        # we narrow the result set after search.
        hits: list[SearchHit] = self.index.search(
            query, category=category, max_results=max(max_results * 4, 20)
        )
        if platform is not None:
            hits = [h for h in hits if self._entry_has_platform(h.entry_id, platform)]
        return [h.to_dict() for h in hits[:max_results]]

    def _entry_has_platform(self, entry_id: str, platform: str) -> bool:
        e = self.index.get(entry_id)
        return e is not None and platform in e.frontmatter.platforms

    def get_entry(self, slug: str) -> dict[str, Any]:
        """See ``GET_ENTRY_DESCRIPTION``."""
        e = self.index.get(slug)
        if e is None:
            raise KeyError(f"no entry with id {slug!r}")
        return _entry_to_dict(e)

    def list_categories(self) -> list[dict[str, Any]]:
        """See ``LIST_CATEGORIES_DESCRIPTION``."""
        counts: dict[str, int] = {c: 0 for c in CATEGORIES}
        for e in self.index.entries:
            counts[e.category] = counts.get(e.category, 0) + 1
        return [
            {"name": c, "count": counts[c]} for c in CATEGORIES
        ]

    def list_entries(self, category: str) -> list[dict[str, Any]]:
        """See ``LIST_ENTRIES_DESCRIPTION``."""
        if category not in CATEGORIES:
            raise ValueError(
                f"unknown category {category!r}; expected one of {sorted(CATEGORIES)}"
            )
        return [
            _entry_summary(e)
            for e in sorted(self.index.entries, key=lambda e: e.id)
            if e.category == category
        ]

    def get_anti_analysis_techniques(
        self, platform: str | None = None
    ) -> list[dict[str, Any]]:
        """See ``GET_ANTI_ANALYSIS_TECHNIQUES_DESCRIPTION``."""
        result: list[dict[str, Any]] = []
        for e in self.index.entries:
            if e.category != "anti-analysis":
                continue
            if platform is not None and platform not in e.frontmatter.platforms:
                continue
            result.append(_entry_to_dict(e))
        return result
