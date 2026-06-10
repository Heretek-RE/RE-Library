"""RE-Library MCP server.

A Model Context Protocol server that exposes the RE-Library knowledge base
(``content/**/*.md``) as a set of tools for any MCP-compatible client
(Claude Desktop, Cursor, Continue, …).

Install::

    pip install re-library-mcp

Run via stdio (the standard MCP transport)::

    python -m re_library_mcp

Or use the console script::

    re-library-mcp

Configuration via environment variables:

- ``RE_LIBRARY_CONTENT_DIR`` — path to a local copy of the ``content/`` tree.
  If set, the server reads markdown files from disk instead of fetching
  them from GitHub. Useful for development and for air-gapped environments.
- ``RE_LIBRARY_REPO`` — GitHub ``owner/name`` to fetch from
  (default: ``Heretek-AI/RE-Library``).
- ``RE_LIBRARY_BRANCH`` — branch to fetch from (default: ``main``).
- ``RE_LIBRARY_OFFLINE`` — if set to a truthy value, the server will not
  make any network requests and will fail if content cannot be read
  locally.
"""

from __future__ import annotations

__version__ = "0.1.0"
