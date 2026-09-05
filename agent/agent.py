"""Travel planning agent with MCP tool integration."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from openai import AsyncOpenAI

from agent.config import Settings, get_settings
from agent.mcp_client import MCPClient, extract_tool_result
from agent.tool_adapter import mcp_tools_to_openai

TraceCallback = Callable[[dict[str, Any]], Awaitable[None] | None]

SYSTEM_PROMPT = """You are a travel planning assistant.

Your task is to generate a practical trip plan based on the user's destination, origin,
travel month, duration, group size, budget, interests, and preferred pace. Use the
available MCP tools to fetch facts and build the plan.

Planning steps:
1. Look up the destination overview.
2. Check travel logistics and transport costs from the origin.
3. Check seasonal suitability and any weather/crowd warnings for the requested month.
4. Match activities to user interests.
5. Create a daily itinerary.
6. Calculate budget breakdown using transport and activity estimates.
7. Look for accommodation options.

If the calculated budget exceeds the user's budget, suggest adjustments or call
the budget tool with lower-cost options. If a tool returns an error, continue
with available information.

Provide a clear final plan covering travel logistics, timing, budget breakdown,
day-by-day itinerary, stay suggestions, and practical tips. Use INR when budget is in INR.
"""


class MiniPSAgent:
    def __init__(
        self,
        mcp_client: MCPClient,
        *,
        settings: Settings | None = None,
        llm_client: Any | None = None,
        trace: TraceCallback | None = None,
    ):
        self.mcp_client = mcp_client
        self.settings = settings or get_settings()
        self.llm = llm_client or AsyncOpenAI(
            base_url=self.settings.llm_base_url,
            api_key=self.settings.llm_api_key,
            timeout=self.settings.request_timeout,
        )
        self.trace = trace
        self.tools: list[dict[str, Any]] = []

    async def _emit(self, event: dict[str, Any]) -> None:
        if self.trace:
            result = self.trace(event)
            if hasattr(result, "__await__"):
                await result

    async def prepare(self) -> None:
        discovered = await self.mcp_client.list_tools()
        self.tools = mcp_tools_to_openai(discovered)
        await self._emit({"type": "tools_discovered", "count": len(self.tools)})

    async def run(self, user_query: str) -> str:
        if not self.tools:
            await self.prepare()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query},
        ]
        for step in range(1, self.settings.max_steps + 1):
            await self._emit({"type": "model_step", "step": step})
            response = await self.llm.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                tools=self.tools or None,
                tool_choice="auto" if self.tools else None,
            )
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            text = getattr(message, "content", None)
            if not tool_calls:
                final = text or "I could not produce a plan from the available information."
                await self._emit({"type": "final", "content": final})
                return final

            assistant_message: dict[str, Any] = {
                "role": "assistant",
                "content": text,
                "tool_calls": [],
            }
            for call in tool_calls:
                function = call.function
                raw_arguments = function.arguments or "{}"
                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    arguments = {}
                assistant_message["tool_calls"].append({
                    "id": call.id,
                    "type": "function",
                    "function": {"name": function.name, "arguments": raw_arguments},
                })
            messages.append(assistant_message)
            for call in tool_calls:
                function = call.function
                raw_arguments = function.arguments or "{}"
                try:
                    arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    arguments = {}
                await self._emit({
                    "type": "tool_start",
                    "step": step,
                    "name": function.name,
                    "arguments": arguments,
                })
                try:
                    result = await self.mcp_client.call_tool(function.name, arguments)
                    result_text = extract_tool_result(result)
                except Exception as exc:
                    result_text = json.dumps({
                        "ok": False,
                        "error": f"Tool {function.name} failed: {exc}",
                        "source": "MCP client",
                    })
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": function.name,
                    "content": result_text,
                })
                await self._emit({
                    "type": "tool_end",
                    "step": step,
                    "name": function.name,
                    "result": result_text[:700],
                })

        final = "Step limit reached before completing the plan. Please refine your request."
        await self._emit({"type": "limit", "content": final})
        return final
