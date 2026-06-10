"""DRM name denylist.

The content policy (see ``CONTRIBUTING.md``) is that the ``drm/``
category and the project as a whole must not name any specific DRM
system. The tests in ``tests/test_no_drm_names.py`` and the build-time
lint in CI grep for these names and fail if any appear.

This is a *defensive* guard, not the *primary* policy — the policy is
explained in CONTRIBUTING.md and the contributor is expected to follow
it. The denylist catches accidents, not malice.

If a new DRM system needs to be added to the denylist, edit this file
and update CONTRIBUTING.md in the same PR.
"""

from __future__ import annotations

# Lowercased, word-boundary matched. Order doesn't matter; case doesn't
# matter (we lowercase the input). Add new entries as the need arises.
DENYLIST: tuple[str, ...] = (
    # Major commercial CDMs. We do not name these in the drm/ category.
    "widevine",
    "fairplay",
    "playready",
    # Common variants and misspellings that drift in via copy-paste.
    "wide-vine",
    "wide vine",
    "fair play",
    "play ready",
    "play-ready",
)

# Categories where the denylist *must* be clean. Outside these
# categories we apply a *softer* check (we only warn, not fail), because
# historical references in RE tutorials (e.g. "Widevine L1" in an
# Android entry about root detection) are useful context even if the
# project policy is to avoid the names.
STRICT_CATEGORIES: frozenset[str] = frozenset({"drm"})
