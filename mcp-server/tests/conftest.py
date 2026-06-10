"""Shared pytest fixtures for the MCP server tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


# Repo root: <repo>/mcp-server/tests/conftest.py → <repo>
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_DIR = REPO_ROOT / "content"


@pytest.fixture(scope="session", autouse=True)
def _point_at_local_content():
    """Force the loader to use the local content/ directory for the
    whole test session, so tests don't make network calls."""
    os.environ["RE_LIBRARY_CONTENT_DIR"] = str(CONTENT_DIR)
    yield
    # Don't unset — the test runner exits after the session anyway.
