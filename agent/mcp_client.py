"""Async MCP client used by the agent loop."""

from __future__ import annotations

import json
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client


class MCPClient:
    """Connect to an SSE MCP server and expose a small testable interface."""

    def __init__(self, url: str):
        self.url = url
        self._stack = AsyncExitStack()
        self.session: ClientSession | None = None

    async def __aenter__(self) -> "MCPClient":
        streams = await self._stack.enter_async_context(sse_client(self.url))
        self.session = await self._stack.enter_async_context(ClientSession(*streams))
        await self.session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        await self._stack.aclose()
        self.session = None

    async def list_tools(self) -> list[Any]:
        if not self.session:
            raise RuntimeError("MCPClient must be used inside an async context manager.")
        result = await self.session.list_tools()
        return list(result.tools)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if not self.session:
            raise RuntimeError("MCPClient must be used inside an async context manager.")
        return await self.session.call_tool(name, arguments)


def extract_tool_result(result: Any) -> str:
    """Convert MCP content blocks into compact JSON/text for the LLM."""
    if result is None:
        return "{}"
    if isinstance(result, (dict, list, str, int, float, bool)):
        return json.dumps(result, ensure_ascii=False, default=str) if not isinstance(result, str) else result
    structured = getattr(result, "structuredContent", None) or getattr(result, "structured_content", None)
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False, default=str)
    content = getattr(result, "content", None)
    if content is not None:
        chunks = []
        for block in content:
            text = getattr(block, "text", None)
            if text is not None:
                chunks.append(text)
            else:
                chunks.append(str(block))
        return "\n".join(chunks)
    return json.dumps(result, ensure_ascii=False, default=str)
