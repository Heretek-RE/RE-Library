"""Pydantic models for RE-Library entries.

This module mirrors the Zod schema in ``src/content.config.ts`` (Astro).
The two should stay in lockstep; the schema-drift test in
``tests/test_schema_sync.py`` parses a sample of entries under both
runtimes and asserts the parsed shapes match.

The Python side is the *loader* side — it reads raw markdown with YAML
frontmatter from either a local directory (``RE_LIBRARY_CONTENT_DIR``)
or from the public GitHub repository, parses it, and exposes it to
the rest of the server.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Category = Literal[
    "android",
    "ios",
    "anti-analysis",
    "drm",
    "packers",
    "tools",
    "native",
    "web-hybrid",
    # v2.7.0 (2026-06-06) — three new categories. The Zod
    # schema in src/content.config.ts must mirror this
    # list; the schema-drift test asserts both sets match.
    "sandbox-emulation",
    "uefi-firmware-re",
    "reference-awesome-lists",
    # v2.9.0 (2026-06-07) — `re-ai-mcp` (12th category) added.
    # Mirrors the Zod schema's category literal.
    "re-ai-mcp",
]

Platform = Literal[
    "android",
    "ios",
    "linux",
    "windows",
    "macos",
    "web",
]

Difficulty = Literal["beginner", "intermediate", "advanced"]


class EntryFrontmatter(BaseModel):
    """The YAML frontmatter of a single entry.

    Mirrors the Zod schema in ``src/content.config.ts``.
    """

    title: str
    category: Category
    platforms: list[Platform] = Field(default_factory=list)
    difficulty: Difficulty = "intermediate"
    tags: list[str] = Field(default_factory=list)
    summary: str
    updated: date
    related: list[str] = Field(default_factory=list)

    # ``slug`` is optional on both sides; the Zod schema declares it but the
    # Pydantic side does not require it (it's currently unused as an ID —
    # the file path is the ID).
    slug: str | None = None

    @field_validator("updated", mode="before")
    @classmethod
    def _coerce_updated(cls, v: object) -> object:
        # YAML may parse "2026-06-04" as a date already; if it's a string,
        # leave it for Pydantic to coerce.
        return v


class Entry(BaseModel):
    """A complete entry: parsed frontmatter + raw markdown body."""

    # The entry's stable ID, e.g. "android/01-apk-structure".
    # This is the file path under content/ with the .md stripped, *and*
    # the value to pass to ``get_entry`` to retrieve this entry.
    id: str

    # Relative URL path, e.g. "android/01-apk-structure" (same as id today,
    # but kept separate in case the routing changes).
    slug: str

    frontmatter: EntryFrontmatter
    body: str  # the markdown body, frontmatter stripped

    @property
    def title(self) -> str:
        return self.frontmatter.title

    @property
    def category(self) -> Category:
        return self.frontmatter.category
