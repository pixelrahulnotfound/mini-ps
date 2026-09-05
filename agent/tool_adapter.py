"""Convert MCP tool metadata into OpenAI-compatible function schemas."""

from __future__ import annotations

from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_none=True)
    return dict(value)


def mcp_tool_to_openai(tool: Any) -> dict[str, Any]:
    name = getattr(tool, "name", None) or _as_dict(tool).get("name")
    description = getattr(tool, "description", None) or _as_dict(tool).get("description", "")
    schema = getattr(tool, "inputSchema", None)
    if schema is None:
        schema = getattr(tool, "input_schema", None)
    if schema is None:
        schema = _as_dict(tool).get("inputSchema", {})
    schema = _as_dict(schema)
    schema.setdefault("type", "object")
    schema.setdefault("properties", {})
    schema.setdefault("required", [])
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": schema,
        },
    }


def mcp_tools_to_openai(tools: list[Any]) -> list[dict[str, Any]]:
    return [mcp_tool_to_openai(tool) for tool in tools]
