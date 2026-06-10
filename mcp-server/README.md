# re-library-mcp

A [Model Context Protocol](https://modelcontextprotocol.io/) server that
exposes the [RE-Library](https://heretek-ai.github.io/RE-Library/)
knowledge base as a set of tools for any MCP-compatible client
(Claude Desktop, Cursor, Continue, …).

The server reads the same `content/**/*.md` files that the GitHub
Pages site reads, parses them, and serves them over JSON-RPC via
stdio. No hosted backend; runs on the analyst's box.

## Install

```bash
pip install re-library-mcp
```

For development, install from the repo in editable mode:

```bash
git clone https://github.com/Heretek-AI/RE-Library
cd RE-Library/mcp-server
pip install -e ".[dev]"
```

## Use

### From Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "re-library": {
      "command": "python",
      "args": ["-m", "re_library_mcp"]
    }
  }
}
```

Restart Claude Desktop. You'll see `re-library` listed with five tools
available. Try asking:

> *"What are the main ways to bypass SSL pinning on Android?"*

### From Cursor / Continue / any MCP client

Same pattern — point the client at `python -m re_library_mcp` over
stdio. See your client's docs for the exact config key.

## Tools

| Tool | Purpose |
|---|---|
| `search_re(query, category?, platform?, max_results?)` | Free-text search; returns up to 5 hits with title, category, snippet, and score. |
| `get_entry(slug)` | Full text of one entry. The slug is `<category>/<NN>-<slug>`, e.g. `android/01-apk-structure`. |
| `list_categories()` | All eight categories with their entry counts. |
| `list_entries(category)` | Lightweight summary of every entry in one category. |
| `get_anti_analysis_techniques(platform?)` | Convenience aggregator for the `anti-analysis` category. |

## Configuration

| Env var | Default | Notes |
|---|---|---|
| `RE_LIBRARY_CONTENT_DIR` | (unset) | Path to a local copy of `content/`. If set, the loader reads from disk — useful for development and air-gapped use. |
| `RE_LIBRARY_REPO` | `Heretek-AI/RE-Library` | GitHub `owner/name` to fetch from when no local content is set. |
| `RE_LIBRARY_BRANCH` | `main` | Branch to fetch from. |
| `RE_LIBRARY_OFFLINE` | (unset) | If truthy, never make network requests; fail if local content is missing. |

## Smoke test

Verify the install and content resolution without starting a JSON-RPC
session:

```bash
re-library-mcp --check
# or
python -m re_library_mcp --check
```

This prints a one-line summary of the loaded corpus (entry count by
category) and exits.

## Run the tests

```bash
cd mcp-server
pip install -e ".[dev]"
pytest -q
```

The tests cover:

- `test_loader.py` — the loader can find and parse every entry.
- `test_no_drm_names.py` — the DRM-name denylist is clean (the
  project's content policy guard).
- `test_schema_sync.py` — the Python Pydantic schema and the Astro
  Zod schema agree on field names and the category/platform/
  difficulty enums.
- `test_search.py` — the in-memory search index.
- `test_tools.py` — every MCP tool returns what its description
  promises.

## Publishing a new release

The repo ships a `python-publish.yml` workflow (`.github/workflows/`)
that builds the sdist + wheel and publishes to PyPI on every GitHub
release, using **PyPI trusted publishing** (OIDC). No API tokens are
stored in GitHub secrets.

One-time PyPI setup (do this once before the first release):

1. Log in to <https://pypi.org/> and create the `re-library-mcp`
   project if it doesn't already exist. PyPI project URLs are reserved
   on first upload; you don't need to "create" the project in advance.
2. Go to <https://pypi.org/manage/account/publishing/> and add a new
   *pending publisher* with:
   - **PyPI Project Name:** `re-library-mcp`
   - **Owner:** `Heretek-AI`
   - **Repository name:** `RE-Library`
   - **Workflow filename:** `python-publish.yml`
   - **Environment name:** `pypi` (must match the environment in the
     workflow file — create it under GitHub Settings → Environments)
3. (Optional) Repeat the same steps on
   <https://test.pypi.org/> if you want a dry-run target.

To cut a release:

```bash
# 1. Bump version in pyproject.toml (and any version references)
# 2. Commit
# 3. Tag and push
git tag v0.1.0
git push --tags

# 4. Open the release on GitHub
gh release create v0.1.0 --generate-notes

# The release event triggers the publish workflow, which builds and
# uploads to PyPI. Watch progress under the Actions tab.
```

You can also trigger the workflow manually from the Actions tab
(`workflow_dispatch`) — useful for a TestPyPI dry-run.

## Development

The server is small and self-contained. Three modules do almost
all the work:

- `loader.py` — finds and parses entries (local dir or GitHub).
- `search.py` — builds an in-memory inverted index.
- `tools.py` — the five MCP tool implementations.

`server.py` is the thin glue that registers them with the `mcp`
Python SDK over stdio.

The full content corpus is at
[`../content/`](../content/) — add an entry there, restart the
server, and it's available.

## License

MIT. See [`../LICENSE`](../LICENSE).
