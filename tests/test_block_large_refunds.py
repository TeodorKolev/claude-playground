import pytest

from hooks.block_large_refunds import block_large_refunds


def _hook_input(tool_input: dict) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__payments__process_refund",
        "tool_input": tool_input,
        "tool_use_id": "toolu_1",
        "session_id": "s1",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp",
    }


@pytest.mark.asyncio
async def test_denies_refund_over_the_threshold():
    output = await block_large_refunds(
        _hook_input({"customer_id": "cust_001", "amount": 750}), None, {"signal": None}
    )

    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "deny"
    assert "500" in specific["permissionDecisionReason"]
    assert "escalate_to_human" in specific["permissionDecisionReason"]


@pytest.mark.asyncio
async def test_allows_refund_at_or_under_the_threshold():
    for amount in (500, 499.99, 1):
        output = await block_large_refunds(
            _hook_input({"customer_id": "cust_001", "amount": amount}), None, {"signal": None}
        )
        assert output == {}, f"amount {amount} should not have been denied"


@pytest.mark.asyncio
async def test_ignores_missing_or_non_numeric_amount():
    output = await block_large_refunds(_hook_input({"customer_id": "cust_001"}), None, {"signal": None})
    assert output == {}

    output = await block_large_refunds(
        _hook_input({"customer_id": "cust_001", "amount": "lots"}), None, {"signal": None}
    )
    assert output == {}
