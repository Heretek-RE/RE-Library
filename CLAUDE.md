# RE-Library

A context7-style knowledge base for Reverse Engineering. Astro site (GitHub Pages) + pip-installable MCP server.

## Structure

```
content/                 # Markdown entries organized by category
  android/               # APK structure, smali, Frida on Android
  anti-analysis/         # Anti-debug, anti-VM, anti-sandbox, IL2CPP triage
  engines/               # Per-engine RE notes (Blackspace, Glacier 2, Unity IL2CPP, UE5)
  storefronts/           # Per-storefront RE notes (Steam, EOS, EA App/Origin)
  protection/            # Per-protection pattern docs (encrypted VM, anti-debug, hardware fingerprinting, telemetry leaks)
  drm/                   # CDM architecture, telemetry relay (vendor-neutral, no system names)
  ios/                   # IPA structure, ObjC runtime
  native/                # PE, ELF format docs
  packers/               # UPX, Themida, VMProtect
  re-ai-mcp/             # RE-AI MCP server documentation
  reference-awesome-lists/
  sandbox-emulation/
  tools/                 # Ghidra, IDA, Binary Ninja, Frida
  web-hybrid/            # Electron, WebAssembly
src/                     # Astro components, layouts, pages
mcp-server/              # Python MCP server (re-library-mcp package)
  pyproject.toml         # Hatchling build, mcp + httpx + pydantic + pyyaml deps
  src/re_library_mcp/    # MCP server source
```

## Build commands

### Astro site
```bash
npm ci
npm run build          # build + pagefind index
npm run dev            # dev server at localhost:4321
npm run check          # astro check (type checking)
```

### MCP server
```bash
cd mcp-server
pip install -e ".[dev]"
pytest                 # run tests
re-library-mcp         # start MCP server on stdio
```

## Adding content

New entries go in `content/<category>/` as numbered markdown files (e.g., `01-new-topic.md`). The content config at `src/content.config.ts` controls frontmatter validation. See `CONTRIBUTING.md` for the full content policy.

**Content rules:**
- DRM category: describe architectures and protocol shapes only. Do not name specific DRM systems.
- Per-engine and per-protection content: use vendor-neutral phrasing. No specific game titles, publisher names, or engagement identifiers.
- All entries must include sensory detail and code examples where applicable.

## Deployment

GitHub Pages via `.github/workflows/deploy-pages.yml`. Deploys on push to `main`. Site URL: `https://heretek-re.github.io/RE-Library/`.

## License

MIT. See `LICENSE`.

## Key files

- `astro.config.mjs` — Astro config (site URL, base path, Shiki theme)
- `src/content.config.ts` — Content schema definitions
- `CONTRIBUTING.md` — Content policy and contribution guide
- `mcp-server/pyproject.toml` — MCP server build config
