import pytest
from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, HookMatcher, TextBlock, query

from agents.records_sdk_agent import MODEL, RECORDS_MCP_TOOL_NAMES, records_mcp_server
from hooks.normalize_tool_output import make_normalising_hook

PROMPT = "Look up customer C-001, find their order ORD-42, and check shipment SHP-7 status."


@pytest.mark.asyncio
async def test_model_receives_normalised_data_from_all_three_tools():
    # seen is populated inside the hook itself (see make_normalising_hook's
    # docstring) - a sibling observer hook would only get the raw, pre-hook
    # tool_response and couldn't tell us what the model actually received.
    seen: list[dict] = []

    options = ClaudeAgentOptions(
        model=MODEL,
        tools=[],
        mcp_servers={"records": records_mcp_server},
        allowed_tools=RECORDS_MCP_TOOL_NAMES,
        permission_mode="bypassPermissions",
        max_turns=6,
        hooks={"PostToolUse": [HookMatcher(matcher="mcp__records__.*", hooks=[make_normalising_hook(seen)])]},
    )

    replies: list[str] = []
    async for message in query(prompt=PROMPT, options=options):
        if isinstance(message, AssistantMessage):
            replies.extend(block.text for block in message.content if isinstance(block, TextBlock))

    assert len(seen) == 3, f"expected all three record tools to be called, hook saw: {seen}"

    by_source = {}
    for record in seen:
        if "customer_id" in record:
            by_source["customer"] = record
        elif "order_id" in record:
            by_source["order"] = record
        elif "shipment_id" in record:
            by_source["shipment"] = record
    assert set(by_source) == {"customer", "order", "shipment"}, seen

    # Tool A: epoch seconds -> ISO 8601, not the raw 1710489600.
    assert by_source["customer"]["created_at"] == "2024-03-15T08:00:00Z"
    assert by_source["customer"]["status"] == "active"

    # Tool B: already ISO 8601 / English - untouched.
    assert by_source["order"]["created_at"] == "2024-03-15T12:00:00Z"
    assert by_source["order"]["status"] == "active"

    # Tool C: DD/MM/YYYY -> ISO 8601, single-char status -> English.
    assert by_source["shipment"]["created_at"] == "2024-03-15T00:00:00Z"
    assert by_source["shipment"]["status"] == "shipped"

    reply_text = " ".join(replies)
    # The raw, unnormalised representations should never reach the model.
    assert "1710489600" not in reply_text
    assert "15/03/2024" not in reply_text
