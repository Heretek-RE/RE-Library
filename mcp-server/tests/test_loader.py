"""Loader tests — verify the loader can find and parse every entry."""

from __future__ import annotations

from pathlib import Path

import pytest

from re_library_mcp.loader import (
    CATEGORIES,
    ContentSource,
    iter_entries,
    load_all,
    split_frontmatter,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_categories_contains_all_eight() -> None:
    # v2.7.0 (2026-06-06) — three new categories. The canonical
    # count is now 12 (8 originals + 3 from v2.7.0 + 1 from v2.9.0 re-ai-mcp).
    assert len(CATEGORIES) == 12
    assert "drm" in CATEGORIES
    assert "android" in CATEGORIES
    assert "sandbox-emulation" in CATEGORIES
    assert "uefi-firmware-re" in CATEGORIES
    assert "reference-awesome-lists" in CATEGORIES


def test_split_frontmatter_basic() -> None:
    raw = (
        "---\n"
        "title: \"Hello\"\n"
        "category: android\n"
        "platforms: [android]\n"
        "difficulty: beginner\n"
        "tags: [a, b]\n"
        "summary: \"hi\"\n"
        "updated: \"2026-06-04\"\n"
        "related: []\n"
        "---\n"
        "# body\n"
        "content here\n"
    )
    fm, body = split_frontmatter(raw)
    assert fm["title"] == "Hello"
    assert body.startswith("# body")
    assert "content here" in body


def test_split_frontmatter_missing_raises() -> None:
    with pytest.raises(ValueError):
        split_frontmatter("no frontmatter at all\n")


def test_load_all_returns_entries() -> None:
    entries = load_all()
    assert len(entries) >= 1
    for e in entries:
        assert e.id
        assert e.frontmatter.title
        assert e.category in CATEGORIES
        assert e.body.strip()


def test_every_entry_id_matches_category() -> None:
    """An entry's id (e.g. 'android/01-apk-structure') must start with
    its category. The Astro catch-all route relies on this."""
    entries = load_all()
    for e in entries:
        prefix = e.id.split("/")[0]
        assert prefix == e.category, (
            f"entry {e.id!r} has category {e.category!r} but id "
            f"prefix is {prefix!r}"
        )


def test_content_dir_has_all_eight_category_dirs() -> None:
    # v2.7.0 (2026-06-06) — three new categories. The canonical
    # count is now 11.
    content = REPO_ROOT / "content"
    assert content.is_dir()
    for cat in CATEGORIES:
        assert (content / cat).is_dir(), f"missing category dir: {cat}"
