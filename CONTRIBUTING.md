# Contributing to RE-Library

Thanks for considering an entry. The bar is *"would this help the next person
doing this work?"*, not *"is this novel research"* — short, useful entries
beat long, speculative ones.

## TL;DR

1. Pick a category. Drop a new `.md` file under `content/<category>/`.
2. Copy the frontmatter from any existing entry.
3. Write the body following the [entry template](#entry-template).
4. Run `npm run check` and `npm run build` to make sure the site still
   builds, and `pytest` (in `mcp-server/`) for the schema/DRM lints.
5. Open a PR.

## The DRM guardrail

Entries in `content/drm/` (and DRM-related content anywhere else in the
repo) **must not name any specific DRM system**. The package is called
`re-library-mcp`, not `widevine-bypass-mcp` (or any of the other avoided
names), and the repo never types those names.

Why: the goal of the library is to teach the **architecture** — security
levels, key-ladder theory, attestation, proxy/relay patterns, OEMCrypto
boundaries. Readers who work in the space will recognise which system is
being described; readers who don't will still learn the model.

A `drm` lint test in `mcp-server/tests/test_no_drm_names.py` greps the
content tree for the denylist and fails CI if a name slips in. Treat the
denylist as a starting point; if a new system needs to be added to the
denylist, open a PR against that test file rather than just adding the
content.

In prose, prefer phrases like:

- "the most widely deployed CENC-based CDM"
- "the proprietary streaming DRM on iOS / macOS"
- "the Microsoft-originated CDM"
- "a hardware-rooted security level"
- "a software-only / clear-key level"
- "an OEM-issued attestation leaf signed by a vendor root"

…over naming the system directly.

## Entry template

Every entry follows the same internal structure so the site renders
predictably *and* the MCP `get_entry` payload is consistent enough for an
LLM to follow without re-orienting.

```markdown
---
title: "<Human-readable title>"
slug: "<optional-stable-id-for-cross-links>"
category: "<android|ios|anti-analysis|drm|packers|tools|native|web-hybrid>"
platforms: ["<android|ios|linux|windows|macos|web>"]   # can be empty
difficulty: "<beginner|intermediate|advanced>"
tags: ["<free-form>"]
summary: "<One-sentence pitch. ≤ 240 chars ideally.>"
updated: "YYYY-MM-DD"
related: ["<slug-of-another-entry>", ...]
---

## Summary

One or two sentences restating the pitch in different words.

## Why this matters

A paragraph of context: who hits this, when, and what the cost of not
understanding it is.

## Mechanics

How the technique / protection actually works. Code snippets, hex dumps,
register layouts, syscall tables — whatever fits the topic. This is the
load-bearing section.

## Approach

The high-level strategy for the analyst. Steps, in order.

## Common pitfalls

Detection signals, false-positive traps, things that bite people the first
time.

## Tooling pointers

Links to other entries in `tools/` (and elsewhere) that the reader should
have open alongside this one.

## References

External links. Cite the canonical source when one exists.
```

## Frontmatter reference

| Field | Required | Notes |
|---|---|---|
| `title` | yes | The human-readable title. |
| `slug` | optional | A stable id for cross-references. Defaults to the filename. |
| `category` | yes | One of the eight canonical categories. |
| `platforms` | no | Subset of `android`, `ios`, `linux`, `windows`, `macos`, `web`. |
| `difficulty` | no | `beginner` / `intermediate` / `advanced`. Defaults to `intermediate`. |
| `tags` | no | Free-form. Used for filtering and search. |
| `summary` | yes | One-sentence pitch. |
| `updated` | yes | ISO date, `YYYY-MM-DD`. Bump on meaningful edits. |
| `related` | no | List of slugs (or `<category>/<slug>`) for cross-links. |

The schema lives in [`src/content.config.ts`](src/content.config.ts) and is
mirrored as a Pydantic model in
[`mcp-server/src/re_library_mcp/loader.py`](mcp-server/src/re_library_mcp/loader.py).
A sync test in `mcp-server/tests/test_schema_sync.py` parses a sample under
both runtimes and asserts they match — if you change one, change the other.

## File naming

`<NN>-<kebab-case-slug>.md` where `NN` is a zero-padded number giving the
stable order within a category (used in the sidebar). Example:
`content/android/04-frida-android.md`.

## Running the tests

```bash
# Site
npm install
npm run check    # type-check Astro components and content schema
npm run build    # builds dist/ + Pagefind index

# MCP server
cd mcp-server
pip install -e ".[dev]"
pytest -q
```

The DRM-naming lint lives at
`mcp-server/tests/test_no_drm_names.py`. Run it in isolation to see the
denylist:

```bash
cd mcp-server
pytest tests/test_no_drm_names.py -v
```

## Style notes

- US English. Second person ("you") is fine.
- Code blocks use triple-backtick with a language hint.
- Prefer concrete examples over abstract descriptions.
- If a claim is uncertain, say so. Mark speculation as speculation.
- Don't link to piracy, warez, or "download X APK here" sites.
- Don't include screenshots of proprietary UIs unless they're necessary
  and you have the right to share them.

## Filing issues (without writing a PR)

You don't have to send a PR to contribute. The issue tracker has
templates for the common cases:

| Template | When to use it |
|---|---|
| 📚 **New entry** | You have an idea for an entry but want to vet the topic (or find a collaborator) before writing it. |
| 🔄 **Update entry** | An existing entry is stale, incomplete, or has broken cross-links. |
| 🐞 **Correction / erratum** | A specific claim is wrong or misleading. Smaller than a full update. |
| 🐛 **Site or MCP bug** | The GitHub Pages site, the MCP server, or the build pipeline is broken. |
| ❓ **Question / discussion** | "Is this in scope?" or "is there an entry for X?" — anything that doesn't fit the other templates. |

The new-entry template includes a DRM-policy acknowledgement checkbox;
please tick it before submitting. Issues that violate the content
policy (see [The DRM guardrail](#the-drm-guardrail)) will be closed
without merge, regardless of the rest of the submission.

## License

By contributing, you agree your contributions are MIT-licensed (see
[`LICENSE`](LICENSE)).
