import json

import pytest

from hooks.require_aml_check import AmlState, make_aml_hooks


def _pre_input(tool_input: dict) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__banking__transfer_funds",
        "tool_input": tool_input,
        "tool_use_id": "toolu_1",
        "session_id": "s1",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp",
    }


def _post_input(tool_response) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__banking__aml_check",
        "tool_input": {},
        "tool_response": tool_response,
        "tool_use_id": "toolu_2",
        "session_id": "s1",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp",
    }


@pytest.mark.asyncio
async def test_transfer_denied_before_any_aml_check():
    require_aml_check, _ = make_aml_hooks()

    output = await require_aml_check(_pre_input({"account_id": "acc_1"}), None, {"signal": None})

    specific = output["hookSpecificOutput"]
    assert specific["permissionDecision"] == "deny"
    assert "aml_check" in specific["permissionDecisionReason"]


@pytest.mark.asyncio
async def test_transfer_allowed_after_a_passing_aml_check():
    require_aml_check, record_aml_result = make_aml_hooks()

    content_blocks = [{"type": "text", "text": json.dumps({"account_id": "acc_1", "status": "pass"})}]
    assert await record_aml_result(_post_input(content_blocks), None, {"signal": None}) == {}

    assert await require_aml_check(_pre_input({"account_id": "acc_1"}), None, {"signal": None}) == {}


@pytest.mark.asyncio
async def test_a_failing_aml_check_does_not_unlock_transfer():
    require_aml_check, record_aml_result = make_aml_hooks()

    content_blocks = [{"type": "text", "text": json.dumps({"account_id": "acc_1", "status": "fail"})}]
    await record_aml_result(_post_input(content_blocks), None, {"signal": None})

    output = await require_aml_check(_pre_input({"account_id": "acc_1"}), None, {"signal": None})
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.asyncio
async def test_passing_one_session_does_not_unlock_a_different_session():
    require_aml_check_a, record_aml_result_a = make_aml_hooks(AmlState())
    require_aml_check_b, _ = make_aml_hooks(AmlState())

    content_blocks = [{"type": "text", "text": json.dumps({"account_id": "acc_1", "status": "pass"})}]
    await record_aml_result_a(_post_input(content_blocks), None, {"signal": None})

    output = await require_aml_check_b(_pre_input({"account_id": "acc_1"}), None, {"signal": None})
    assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
