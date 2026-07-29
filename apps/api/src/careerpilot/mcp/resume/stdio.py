"""Debug CLI for resume MCP tools (in-process). Full Cursor MCP uses the API ACP path."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from careerpilot.mcp.resume.server import call_resume_tool, resume_mcp


async def _main() -> int:
    parser = argparse.ArgumentParser(description="CareerPilot resume MCP CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List resume MCP tools")

    call_p = sub.add_parser("call", help="Call a resume MCP tool")
    call_p.add_argument("tool")
    call_p.add_argument("--json", dest="payload", default="{}", help="JSON kwargs")

    args = parser.parse_args()
    if args.cmd == "list":
        print(json.dumps(resume_mcp.list_tools(), indent=2))
        return 0

    payload = json.loads(args.payload)
    result = await call_resume_tool(args.tool, **payload)
    print(
        json.dumps(
            {
                "status": result.status,
                "result": result.result,
                "metadata": result.metadata,
                "error": result.error,
            },
            indent=2,
            default=str,
        )
    )
    return 0 if result.status == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
