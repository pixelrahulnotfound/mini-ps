import json
from types import SimpleNamespace

import pytest

from agent.agent import MiniPSAgent
from agent.config import Settings


class FakeMCP:
    async def list_tools(self):
        return [
            SimpleNamespace(
                name="get_destination_overview",
                description="Look up a destination",
                inputSchema={
                    "type": "object",
                    "properties": {"destination": {"type": "string"}},
                    "required": ["destination"],
                },
            )
        ]

    async def call_tool(self, name, arguments):
        return {"ok": True, "name": name, "arguments": arguments}


class FakeCompletions:
    def __init__(self):
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            tool_call = SimpleNamespace(
                id="call-1",
                function=SimpleNamespace(
                    name="get_destination_overview",
                    arguments=json.dumps({"destination": "Goa"}),
                ),
            )
            message = SimpleNamespace(content=None, tool_calls=[tool_call])
        else:
            message = SimpleNamespace(
                content="## Goa\n\nA short plan based on the tool result.",
                tool_calls=[],
            )
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class FakeLLM:
    def __init__(self):
        self.chat = SimpleNamespace(completions=FakeCompletions())


@pytest.mark.asyncio
async def test_agent_discovers_tools_and_loops_until_final():
    events = []
    agent = MiniPSAgent(
        FakeMCP(),
        settings=Settings(max_steps=3),
        llm_client=FakeLLM(),
        trace=events.append,
    )
    answer = await agent.run("Plan Goa.")
    assert "short plan" in answer
    assert any(event["type"] == "tool_start" for event in events)
    assert any(event["type"] == "final" for event in events)
