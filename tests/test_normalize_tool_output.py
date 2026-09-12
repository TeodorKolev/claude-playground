import pytest

from hooks.normalize_tool_output import normalise_tool_output


def _hook_input(tool_response: dict) -> dict:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__records__get_customer_record",
        "tool_input": {},
        "tool_response": tool_response,
        "tool_use_id": "toolu_1",
        "session_id": "s1",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp",
    }


@pytest.mark.asyncio
async def test_normalises_epoch_seconds_and_numeric_status():
    output = await normalise_tool_output(
        _hook_input({"customer_id": "C-001", "created_at": 1710489600, "status": 200}),
        None,
        {"signal": None},
    )

    updated = output["hookSpecificOutput"]["updatedToolOutput"]
    assert output["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert updated["created_at"] == "2024-03-15T08:00:00Z"
    assert updated["status"] == "active"


@pytest.mark.asyncio
async def test_normalises_ddmmyyyy_and_single_char_status():
    output = await normalise_tool_output(
        _hook_input({"shipment_id": "SHP-7", "created_at": "15/03/2024", "status": "S"}),
        None,
        {"signal": None},
    )

    updated = output["hookSpecificOutput"]["updatedToolOutput"]
    assert updated["created_at"] == "2024-03-15T00:00:00Z"
    assert updated["status"] == "shipped"


@pytest.mark.asyncio
async def test_leaves_already_normalised_fields_alone():
    record = {"order_id": "ORD-42", "created_at": "2024-03-15T12:00:00Z", "status": "active"}

    output = await normalise_tool_output(_hook_input(record), None, {"signal": None})

    assert output == {}


@pytest.mark.asyncio
async def test_ignores_unknown_status_codes():
    output = await normalise_tool_output(
        _hook_input({"created_at": "2024-03-15T12:00:00Z", "status": "weird"}),
        None,
        {"signal": None},
    )

    assert output == {}


@pytest.mark.asyncio
async def test_non_dict_tool_response_is_left_alone():
    output = await normalise_tool_output(_hook_input(None), None, {"signal": None})

    assert output == {}
