"""Storage MCP server — object store put/get via domain storage adapter."""

from __future__ import annotations

import base64
from typing import Any

from careerpilot import storage as object_storage
from careerpilot.mcp.base import McpServer, McpToolResult

storage_mcp = McpServer("storage")


@storage_mcp.tool("put_object", "Store bytes at an object key (base64 payload).")
async def put_object(
    *,
    object_key: str,
    data_b64: str,
    content_type: str = "application/octet-stream",
) -> McpToolResult:
    try:
        data = base64.b64decode(data_b64)
        await object_storage.put_object(
            object_key=object_key,
            data=data,
            content_type=content_type,
        )
    except Exception as exc:  # noqa: BLE001
        return McpToolResult(
            status="ERROR",
            error={"code": "storage_put_failed", "message": str(exc) or "put failed"},
        )
    return McpToolResult(
        status="SUCCESS",
        result={"object_key": object_key, "bytes": len(data)},
        metadata={"tool": "put_object"},
    )


@storage_mcp.tool("get_object", "Read object bytes by key (returns base64).")
async def get_object(*, object_key: str) -> McpToolResult:
    try:
        data = await object_storage.get_object(object_key)
    except Exception as exc:  # noqa: BLE001
        return McpToolResult(
            status="ERROR",
            error={"code": "storage_get_failed", "message": str(exc) or "get failed"},
        )
    return McpToolResult(
        status="SUCCESS",
        result={
            "object_key": object_key,
            "data_b64": base64.b64encode(data).decode("ascii"),
            "bytes": len(data),
        },
        metadata={"tool": "get_object"},
    )


async def call_storage_tool(tool_name: str, **kwargs: Any) -> McpToolResult:
    return await storage_mcp.call(tool_name, **kwargs)
