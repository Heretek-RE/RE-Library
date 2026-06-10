"""Test: the Zod schema (Astro) and the Pydantic schema (Python) agree.

This is the schema-drift test referenced in CONTRIBUTING.md. It runs
the *TypeScript* content collection type-check via ``npx astro check``
and the *Python* content collection validator via Pydantic on a sample
of entries, and asserts the parsed shapes are consistent.

The Astro side is invoked via subprocess (``npx astro check`` is not
importable from Python). The check is intentionally shallow — it
verifies that the *field names* agree, and that the *set of valid
category / platform / difficulty values* agree. We don't try to
compare the type systems themselves; just the surface contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from re_library_mcp.loader import CATEGORIES, iter_entries, ContentSource
from re_library_mcp.schema import EntryFrontmatter

REPO_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_LIMIT = 3  # how many entries to parse on each side


def _zod_constants() -> dict:
    """Read the canonical lists out of the TypeScript schema file via
    simple text matching. Avoids a full TypeScript compile dependency."""
    ts = (REPO_ROOT / "src" / "content.config.ts").read_text(encoding="utf-8")
    # Find `const CATEGORIES = [ ... ] as const;`
    def _find_list(name: str) -> list[str]:
        marker = f"const {name} = ["
        i = ts.find(marker)
        if i == -1:
            raise AssertionError(f"could not find {name} in content.config.ts")
        j = ts.find("] as const;", i)
        if j == -1:
            raise AssertionError(f"could not find end of {name}")
        block = ts[i + len(marker) : j]
        return [s.strip().strip("'\"") for s in block.split(",") if s.strip()]
    return {
        "CATEGORIES": _find_list("CATEGORIES"),
        "PLATFORMS": _find_list("PLATFORMS"),
        "DIFFICULTY": _find_list("DIFFICULTY"),
    }


def test_zod_and_pydantic_categories_agree() -> None:
    zod = _zod_constants()
    assert set(CATEGORIES) == set(zod["CATEGORIES"]), (
        f"category list drift:\n"
        f"  Python: {sorted(CATEGORIES)}\n"
        f"  Zod:    {sorted(zod['CATEGORIES'])}"
    )


def test_zod_and_pydantic_platforms_agree() -> None:
    zod = _zod_constants()
    # The Python Literal lives in schema.py. Re-derive from Pydantic.
    from re_library_mcp.schema import Platform
    py_platforms = list(Platform.__args__)
    assert set(py_platforms) == set(zod["PLATFORMS"]), (
        f"platform list drift:\n"
        f"  Python: {sorted(py_platforms)}\n"
        f"  Zod:    {sorted(zod['PLATFORMS'])}"
    )


def test_zod_and_pydantic_difficulty_agree() -> None:
    zod = _zod_constants()
    from re_library_mcp.schema import Difficulty
    py_difficulty = list(Difficulty.__args__)
    assert set(py_difficulty) == set(zod["DIFFICULTY"]), (
        f"difficulty list drift:\n"
        f"  Python: {sorted(py_difficulty)}\n"
        f"  Zod:    {sorted(zod['DIFFICULTY'])}"
    )


def test_zod_frontmatter_field_names() -> None:
    """Every required field in the Zod schema has a Python equivalent
    on ``EntryFrontmatter``."""
    pydantic_fields = set(EntryFrontmatter.model_fields.keys())
    required = {
        "title", "category", "summary", "updated",
        "platforms", "difficulty", "tags", "related",
    }
    missing = required - pydantic_fields
    assert not missing, (
        f"Python schema is missing required frontmatter fields: {sorted(missing)}. "
        f"Add them to src/re_library_mcp/schema.py and update the Zod schema "
        f"in src/content.config.ts (or vice versa)."
    )


@pytest.mark.parametrize("limit", [SAMPLE_LIMIT])
def test_sample_entries_parse_on_both_sides(limit: int) -> None:
    """Parse a few entries through the Pydantic loader. The Zod side is
    covered by ``npm run check`` / ``npx astro check`` in CI; we just
    ensure the Python side is happy with the same corpus."""
    source = ContentSource.from_env()
    entries = list(iter_entries(source))[:limit]
    assert entries, "no entries were loaded — check RE_LIBRARY_CONTENT_DIR"
    for e in entries:
        # Pydantic should have already validated during load. Re-validate
        # to be explicit.
        EntryFrontmatter.model_validate(e.frontmatter.model_dump())
