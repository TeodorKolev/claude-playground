import re
from datetime import datetime, timezone
from typing import Any

from claude_agent_sdk import HookContext, PostToolUseHookInput

# PostToolUse runs after the tool has executed but before the model sees the
# result, which makes it the right place to normalise cross-source formats -
# a PreToolUse hook fires before execution and has no result to rewrite yet.
_DDMMYYYY = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")

_STATUS_MAP = {
    "200": "active",
    "404": "not_found",
    "S": "shipped",
    "P": "pending",
}


def _normalise_created_at(value: Any) -> Any:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if isinstance(value, str):
        match = _DDMMYYYY.match(value)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month}-{day}T00:00:00Z"

    return value


def _normalise_status(value: Any) -> Any:
    return _STATUS_MAP.get(str(value), value)


async def normalise_tool_output(
    input_data: PostToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> dict:
    tool_response = input_data["tool_response"]
    if not isinstance(tool_response, dict):
        return {}

    normalised = dict(tool_response)
    if "created_at" in normalised:
        normalised["created_at"] = _normalise_created_at(normalised["created_at"])
    if "status" in normalised:
        normalised["status"] = _normalise_status(normalised["status"])

    if normalised == tool_response:
        return {}

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": normalised,
        }
    }
