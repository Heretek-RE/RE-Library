# RE-Library

A context7-style knowledge base for Reverse Engineering. Curated markdown
entries on techniques, anti-analysis bypass, mobile internals, packers, and
the tools that pull them apart. Read it on the web, or wire it into Claude /
Cursor / any MCP client.

The site is live at <https://heretek-ai.github.io/RE-Library/>.

## What's in it

Eight categories, ~50 entries (growing):

| Category | What it covers |
|---|---|
| `android` | APK structure, smali, native libs, Frida on Android, repackaging, SSL pinning, root detection |
| `ios` | IPA structure, ObjC runtime, Swift demangling, jailbreak detection, Frida on iOS, Objection |
| `anti-analysis` | Anti-debug, anti-VM, anti-sandbox, anti-Frida, anti-dumper, code integrity, detection patterns |
| `drm` | CDM architecture, security levels, key ladders, proxy/relay, attestation *(no system names)* |
| `packers` | UPX, Themida, VMProtect, OLLVM, custom packers |
| `tools` | Ghidra, IDA, Binary Ninja, Frida, Xposed, Magisk, Hopper, radare2 |
| `native` | PE, ELF, Mach-O, dynamic analysis, syscalls, hooking |
| `web-hybrid` | Electron, WebAssembly, browser extensions, hybrid frameworks, Cordova |

The `drm/` category intentionally doesn't name any specific DRM system. The
content describes architectures, security models, and protocol shapes; readers
who know the space will recognise which system is being described. See
[`CONTRIBUTING.md`](CONTRIBUTING.md) for the full content policy.

## Use it from an MCP client

The MCP server is a Python package (`re-library-mcp`) that exposes the same
content over the Model Context Protocol. Install and configure:

```bash
pip install re-library-mcp
```

Add to your MCP client config (e.g. `claude_desktop_config.json`):

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

Then ask your assistant things like:

- *"What are the main ways to bypass SSL pinning on Android?"*
- *"Show me anti-debug techniques for native code on Linux."*
- *"List the categories and how many entries each has."*

The server fetches the latest content from this repo on startup and returns
search results, full entry text, and category summaries.

## Run the site locally

```bash
npm install
npm run dev
# → http://localhost:4321/RE-Library/
```

Build the static site + Pagefind index:

```bash
npm run build
# → dist/  (deploy dist/ to any static host)
```

## Repository layout

```
content/        single source of truth — every entry is a .md file
src/            Astro site (content collections, pages, styles)
public/         static assets (favicon, etc.)
mcp-server/     Python MCP server (publishable to PyPI as `re-library-mcp`)
.github/        CI + GitHub Pages deploy
```

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the entry template, schema
reference, DRM guardrail, and how to run the test suite.

## License

[MIT](LICENSE). Entry content is provided for educational and research
purposes; no warranty of fitness for any particular use.
