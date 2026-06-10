"""MCP server entry point.

Wires the loader, the search index, and the tool registry to the
official ``mcp`` Python SDK over stdio.

Run via ``python -m re_library_mcp`` or the ``re-library-mcp`` console
script installed by ``pip install re-library-mcp``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from re_library_mcp.loader import ContentSource, load_all
from re_library_mcp.search import SearchIndex
from re_library_mcp.tools import (
    GET_ANTI_ANALYSIS_TECHNIQUES_DESCRIPTION,
    GET_ENTRY_DESCRIPTION,
    LIST_CATEGORIES_DESCRIPTION,
    LIST_ENTRIES_DESCRIPTION,
    SEARCH_RE_DESCRIPTION,
    ToolRegistry,
)

log = logging.getLogger(__name__)

SERVER_NAME = "re-library-mcp"
SERVER_VERSION = "0.1.0"


def _build_server(registry: ToolRegistry) -> Server:
    """Construct the MCP ``Server`` and register the tool handlers."""
    server: Server = Server(SERVER_NAME)

    @server.list_tools()
    async def _list_tools() -> list[Tool]:
        return [
            Tool(
                name="search_re",
                description=SEARCH_RE_DESCRIPTION,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Free-text search query.",
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "android",
                                "ios",
                                "anti-analysis",
                                "drm",
                                "packers",
                                "tools",
                                "native",
                                "web-hybrid",
                            ],
                            "description": "Optional category filter.",
                        },
                        "platform": {
                            "type": "string",
                            "enum": [
                                "android",
                                "ios",
                                "linux",
                                "windows",
                                "macos",
                                "web",
                            ],
                            "description": "Optional platform filter.",
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 50,
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="get_entry",
                description=GET_ENTRY_DESCRIPTION,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "slug": {
                            "type": "string",
                            "description": (
                                "Entry ID, e.g. 'android/01-apk-structure'."
                            ),
                        }
                    },
                    "required": ["slug"],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="list_categories",
                description=LIST_CATEGORIES_DESCRIPTION,
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="list_entries",
                description=LIST_ENTRIES_DESCRIPTION,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "android",
                                "ios",
                                "anti-analysis",
                                "drm",
                                "packers",
                                "tools",
                                "native",
                                "web-hybrid",
                            ],
                        }
                    },
                    "required": ["category"],
                    "additionalProperties": False,
                },
            ),
            Tool(
                name="get_anti_analysis_techniques",
                description=GET_ANTI_ANALYSIS_TECHNIQUES_DESCRIPTION,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "platform": {
                            "type": "string",
                            "enum": [
                                "android",
                                "ios",
                                "linux",
                                "windows",
                                "macos",
                                "web",
                            ],
                        }
                    },
                    "additionalProperties": False,
                },
            ),
        ]

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        try:
            if name == "search_re":
                result = registry.search_re(
                    query=arguments["query"],
                    category=arguments.get("category"),
                    platform=arguments.get("platform"),
                    max_results=int(arguments.get("max_results", 5)),
                )
            elif name == "get_entry":
                result = registry.get_entry(arguments["slug"])
            elif name == "list_categories":
                result = registry.list_categories()
            elif name == "list_entries":
                result = registry.list_entries(arguments["category"])
            elif name == "get_anti_analysis_techniques":
                result = registry.get_anti_analysis_techniques(
                    arguments.get("platform")
                )
            else:
                raise ValueError(f"unknown tool: {name!r}")
        except (KeyError, ValueError) as e:
            # Tool-internal validation errors become JSON-RPC "invalid
            # params" errors. The MCP SDK maps these to the appropriate
            # JSON-RPC error code; we just need to raise.
            raise ValueError(str(e)) from e

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    return server


async def _run(source: ContentSource | None = None) -> None:
    """Async entry: load the index and serve over stdio forever."""
    if source is None:
        source = ContentSource.from_env()
    log.info("loading content from %s", source.describe())
    entries = load_all(source)
    log.info("loaded %d entries", len(entries))
    index = SearchIndex.build(entries)
    registry = ToolRegistry(index)
    server = _build_server(registry)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main(argv: list[str] | None = None) -> None:
    """Console-script entry point. ``re-library-mcp`` and ``python -m
    re_library_mcp`` both call this."""
    parser = argparse.ArgumentParser(
        prog="re-library-mcp",
        description=(
            "MCP server for the RE-Library knowledge base. Speaks "
            "JSON-RPC over stdio; designed to be launched by an MCP "
            "client (Claude Desktop, Cursor, etc.)."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "Load the index, print a one-line summary to stdout, and "
            "exit. Useful for verifying the install and content "
            "resolution without starting a JSON-RPC session."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the log level (default: INFO).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,  # never write logs to stdout — that's the RPC channel
    )

    if args.check:
        source = ContentSource.from_env()
        entries = load_all(source)
        cats: dict[str, int] = {}
        for e in entries:
            cats[e.category] = cats.get(e.category, 0) + 1
        print(
            json.dumps(
                {
                    "source": source.describe(),
                    "entries": len(entries),
                    "by_category": cats,
                },
                indent=2,
            )
        )
        return

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
