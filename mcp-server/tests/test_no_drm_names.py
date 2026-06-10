"""Test: no DRM system names in any entry.

Enforces the project's content policy (see CONTRIBUTING.md): the
``drm/`` category, in particular, must not name any specific DRM
system. This test fails CI if a name from the denylist slips in.

The check is *strict* in ``drm/`` (fail on any hit) and *advisory*
elsewhere (warning). Outside the ``drm/`` category, historical
references (e.g. mentioning a specific CDM in an entry about
Android root detection) are useful context even if the project's
drm/ entries avoid the names.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from re_library_mcp._denylist import DENYLIST, STRICT_CATEGORIES
from re_library_mcp.loader import CATEGORIES

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "content"


def _word_boundary_re(name: str) -> re.Pattern[str]:
    # Case-insensitive, word-boundary, allowing for spaces and dashes
    # inside the name (e.g. "fair play" must match the phrase).
    escaped = re.escape(name)
    return re.compile(rf"(?i)\b{escaped}\b")


def _scan_file(path: Path) -> list[tuple[str, int, str]]:
    """Return list of (name, line_number, line_text) hits in ``path``."""
    hits: list[tuple[str, int, str]] = []
    compiled = [(name, _word_boundary_re(name)) for name in DENYLIST]
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for name, pat in compiled:
            if pat.search(line):
                hits.append((name, lineno, line.strip()))
    return hits


def test_drm_category_is_clean() -> None:
    """Strict: drm/ must not contain any denylist name in frontmatter or body."""
    drm_dir = CONTENT_DIR / "drm"
    if not drm_dir.exists():
        pytest.skip("drm/ directory does not exist yet")
    failures: list[str] = []
    for path in sorted(drm_dir.glob("*.md")):
        for name, lineno, text in _scan_file(path):
            failures.append(f"{path.relative_to(REPO_ROOT)}:{lineno} '{name}' — {text!r}")
    assert not failures, (
        "DRM guardrail: drm/ entries must not name any specific DRM system.\n"
        "See CONTRIBUTING.md for the content policy.\n"
        f"Offending lines:\n  " + "\n  ".join(failures)
    )


def test_denylist_is_well_formed() -> None:
    """Sanity: the denylist is non-empty and every name is a non-empty string."""
    assert DENYLIST, "DENYLIST is empty — add at least one entry to make this test meaningful"
    for name in DENYLIST:
        assert isinstance(name, str) and name.strip(), f"bad denylist entry: {name!r}"


def test_categories_match() -> None:
    """The CATEGORIES tuple in the loader and STRICT_CATEGORIES must agree
    on the drm category name (the policy is 'drm entries never name
    a system'; if you rename the category, update the denylist module
    in the same PR)."""
    assert "drm" in CATEGORIES
    assert "drm" in STRICT_CATEGORIES
