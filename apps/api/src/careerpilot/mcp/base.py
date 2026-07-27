"""In-process MCP tool protocol (modular monolith adapter)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class McpToolResult:
    status: str  # SUCCESS | ERROR | UNSUPPORTED
    result: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: dict[str, str] | None = None


ToolHandler = Callable[..., Awaitable[McpToolResult]]


@dataclass
class McpTool:
    name: str
    description: str
    handler: ToolHandler


class McpServer:
    def __init__(self, name: str) -> None:
        self.name = name
        self._tools: dict[str, McpTool] = {}

    def tool(self, name: str, description: str) -> Callable[[ToolHandler], ToolHandler]:
        def decorator(fn: ToolHandler) -> ToolHandler:
            self._tools[name] = McpTool(name=name, description=description, handler=fn)
            return fn

        return decorator

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": t.name, "description": t.description, "server": self.name}
            for t in self._tools.values()
        ]

    async def call(self, tool_name: str, **kwargs: Any) -> McpToolResult:
        tool = self._tools.get(tool_name)
        if tool is None:
            return McpToolResult(
                status="ERROR",
                error={"code": "unknown_tool", "message": f"Unknown tool: {tool_name}"},
            )
        return await tool.handler(**kwargs)
