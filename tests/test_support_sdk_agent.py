import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock, query

from agents.support_sdk_agent import support_agent_options


def _tool_names(messages) -> list[str]:
    return [
        block.name
        for message in messages
        if isinstance(message, AssistantMessage)
        for block in message.content
        if isinstance(block, ToolUseBlock)
    ]


@pytest.mark.asyncio
async def test_refund_over_threshold_is_denied_before_execution_and_escalated():
    prompt = "Refund customer cust_001 $750 for a defective product."

    messages = [message async for message in query(prompt=prompt, options=support_agent_options)]

    result = next(m for m in messages if isinstance(m, ResultMessage))
    denials = [d["tool_name"] for d in result.permission_denials]
    assert "mcp__payments__process_refund" in denials, result.permission_denials

    # The model gets steered to the escalation path instead of retrying.
    assert any("escalate_to_human" in name for name in _tool_names(messages))
    assert '"status": "refunded"' not in (result.result or "")


@pytest.mark.asyncio
async def test_refund_under_threshold_is_allowed_through():
    prompt = "Refund customer cust_001 $50 for a shipping delay."

    messages = [message async for message in query(prompt=prompt, options=support_agent_options)]

    result = next(m for m in messages if isinstance(m, ResultMessage))
    assert result.permission_denials == []
    assert "process_refund" in " ".join(_tool_names(messages))
