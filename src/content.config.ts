// Astro 6 content layer config — single source of truth for the entry schema.
// The Python Pydantic model in mcp-server/src/re_library_mcp/loader.py mirrors
// this shape; the schema-drift test (mcp-server/tests/test_schema_sync.py)
// parses a sample of entries under both and asserts they match.

import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

// v2.7.0 (2026-06-06) — three new categories. The Zod + Pydantic
// schemas are kept in lockstep; the schema-drift test asserts
// the literal sets match by raw-text parsing, so the list
// below must be a single comma-separated run with no
// multi-line comments inside the brackets.
// v2.9.0 (2026-06-07) — added `re-ai-mcp` (12th category).
// Houses the per-server entries for the RE-AI plugin's 31
// MCP servers. The 28 skills live inline in the umbrella
// entry (01-re-ai-plugin.md) and in cross-references from
// the per-server entries. See `Output/v2.9.0-stress-test/
// stress-summary.md` for the v2.9.0 cycle context.
const CATEGORIES = [
  'android', 'ios', 'anti-analysis', 'drm', 'packers', 'tools', 'native', 'web-hybrid',
  'sandbox-emulation', 'uefi-firmware-re', 'reference-awesome-lists', 're-ai-mcp',
] as const;

const PLATFORMS = [
  'android',
  'ios',
  'linux',
  'windows',
  'macos',
  'web',
] as const;

const DIFFICULTY = ['beginner', 'intermediate', 'advanced'] as const;

const entries = defineCollection({
  // Load from ./content at the repo root (not src/content/) so the GitHub raw
  // URLs the MCP server uses stay clean: /content/<category>/<slug>.md.
  loader: glob({ pattern: '**/*.md', base: './content' }),
  schema: z.object({
    title: z.string(),
    slug: z.string().optional(),
    category: z.enum(CATEGORIES),
    platforms: z.array(z.enum(PLATFORMS)).default([]),
    difficulty: z.enum(DIFFICULTY).default('intermediate'),
    tags: z.array(z.string()).default([]),
    summary: z.string(),
    updated: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, {
      message: 'updated must be an ISO date YYYY-MM-DD',
    }),
    related: z.array(z.string()).default([]),
  }),
});

export const collections = { entries };

// Re-export the literal sets so other modules (the category list page,
// the sitemap, future tests) can import the source of truth.
export { CATEGORIES, PLATFORMS, DIFFICULTY };
