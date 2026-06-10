"""Loader: reads RE-Library entries from either a local directory or GitHub.

The loader is the only place that knows how to *find* entries. The rest of
the server consumes the list of ``Entry`` objects and doesn't care where
they came from.

Resolution order for the content source:

1. ``RE_LIBRARY_CONTENT_DIR`` — if set, walk that directory.
2. Otherwise, fetch from GitHub: ``https://raw.githubusercontent.com/
   {RE_LIBRARY_REPO}/{RE_LIBRARY_BRANCH}/content/{category}/{file}.md``.

Defaults: ``RE_LIBRARY_REPO = Heretek-AI/RE-Library``,
``RE_LIBRARY_BRANCH = main``.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import httpx
import yaml

from re_library_mcp.schema import Entry, EntryFrontmatter

log = logging.getLogger(__name__)

CATEGORIES: tuple[str, ...] = (
    "android", "ios", "anti-analysis", "drm", "packers", "tools", "native", "web-hybrid",
    # v2.7.0 (2026-06-06) — three new categories. The Zod + Pydantic
    # schemas are kept in lockstep; the schema-drift test asserts
    # the literal sets match.
    "sandbox-emulation", "uefi-firmware-re", "reference-awesome-lists",
    # v2.9.0 (2026-06-07) — `re-ai-mcp` (12th category) added.
    # Houses the per-server entries for the RE-AI plugin's 31
    # MCP servers + 28 skills (the umbrella entry lists all 28
    # skills inline; the per-server entries cover the 6 most-used
    # servers).
    "re-ai-mcp",
)

DEFAULT_REPO = "Heretek-AI/RE-Library"
DEFAULT_BRANCH = "main"

# Split a markdown file into frontmatter + body. The frontmatter is
# delimited by lines that are exactly "---"; the body is everything after
# the closing delimiter.
_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)",
    re.DOTALL,
)


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Parse a markdown file into ``(frontmatter_dict, body)``.

    Raises ``ValueError`` if no frontmatter block is present.
    """
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("no frontmatter block found (expected '---' delimiters)")
    fm = yaml.safe_load(m.group("fm")) or {}
    body = m.group("body")
    if not isinstance(fm, dict):
        raise ValueError("frontmatter is not a YAML mapping")
    return fm, body


@dataclass(frozen=True)
class ContentSource:
    """A content source — either a local directory or a remote GitHub repo."""

    # Local directory (mutually exclusive with ``repo``)
    local_dir: Path | None = None
    # GitHub owner/name (mutually exclusive with ``local_dir``)
    repo: str = DEFAULT_REPO
    branch: str = DEFAULT_BRANCH

    @classmethod
    def from_env(cls) -> "ContentSource":
        local = os.environ.get("RE_LIBRARY_CONTENT_DIR")
        if local:
            return cls(local_dir=Path(local).expanduser().resolve())
        return cls(
            repo=os.environ.get("RE_LIBRARY_REPO", DEFAULT_REPO),
            branch=os.environ.get("RE_LIBRARY_BRANCH", DEFAULT_BRANCH),
        )

    def describe(self) -> str:
        if self.local_dir:
            return f"local: {self.local_dir}"
        return f"github: {self.repo}@{self.branch}"


def _entry_id(rel_path: Path) -> str:
    """Build the entry ID from a file path. ``android/01-apk-structure.md``
    → ``android/01-apk-structure``."""
    s = str(rel_path)
    if s.endswith(".md"):
        s = s[:-3]
    # Normalise to forward slashes regardless of OS.
    return s.replace("\\", "/")


def _iter_local(source: ContentSource) -> Iterable[tuple[str, str]]:
    """Yield ``(entry_id, raw_markdown)`` from a local directory."""
    assert source.local_dir is not None
    base = source.local_dir
    if not base.exists():
        raise FileNotFoundError(f"RE_LIBRARY_CONTENT_DIR does not exist: {base}")
    for cat in CATEGORIES:
        cat_dir = base / cat
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("*.md")):
            rel = path.relative_to(base)
            yield _entry_id(rel), path.read_text(encoding="utf-8")


def _iter_remote(source: ContentSource) -> Iterable[tuple[str, str]]:
    """Yield ``(entry_id, raw_markdown)`` from the public GitHub repo.

    We list the tree via the GitHub REST API (``/repos/{owner}/{repo}/git/
    trees/{branch}?recursive=1``) — this is unauthenticated, rate-limited
    to 60 req/hr per IP, but a single call returns the whole tree.
    """
    assert source.local_dir is None
    api_url = (
        f"https://api.github.com/repos/{source.repo}/git/trees/{source.branch}"
        f"?recursive=1"
    )
    raw_base = (
        f"https://raw.githubusercontent.com/{source.repo}/{source.branch}"
    )
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        resp = client.get(
            api_url,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        tree = resp.json().get("tree", [])
        md_paths: list[str] = []
        for item in tree:
            p = item.get("path", "")
            if not p.startswith("content/"):
                continue
            if not p.endswith(".md"):
                continue
            # Path looks like "content/android/01-apk-structure.md"
            parts = p.split("/")
            if len(parts) == 3 and parts[1] in CATEGORIES:
                md_paths.append(p)
        md_paths.sort()
        for p in md_paths:
            entry_id = _entry_id(Path(p).relative_to("content"))
            raw_url = f"{raw_base}/{p}"
            r = client.get(raw_url)
            r.raise_for_status()
            yield entry_id, r.text


def iter_entries(source: ContentSource) -> Iterable[Entry]:
    """Yield ``Entry`` objects from a ``ContentSource``.

    Parsing errors are logged and skipped — a single broken entry
    shouldn't take down the whole server.
    """
    if source.local_dir is not None:
        raw_iter = _iter_local(source)
    else:
        raw_iter = _iter_remote(source)

    for entry_id, raw in raw_iter:
        try:
            fm, body = split_frontmatter(raw)
            front = EntryFrontmatter.model_validate(fm)
        except Exception as e:
            log.warning("skipping %s: %s", entry_id, e)
            continue
        yield Entry(
            id=entry_id,
            slug=entry_id,
            frontmatter=front,
            body=body,
        )


def load_all(source: ContentSource | None = None) -> list[Entry]:
    """Convenience: load every entry into a list."""
    if source is None:
        source = ContentSource.from_env()
    return list(iter_entries(source))
