import json
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


def _normalise_record(record: dict) -> dict:
    normalised = dict(record)
    if "created_at" in normalised:
        normalised["created_at"] = _normalise_created_at(normalised["created_at"])
    if "status" in normalised:
        normalised["status"] = _normalise_status(normalised["status"])
    return normalised


def make_normalising_hook(seen: list[dict] | None = None):
    """Build the PostToolUse hook, optionally recording each normalised
    record into `seen` as it's produced.

    A separate observer hook registered alongside this one would only ever
    receive the original tool_response - PostToolUse hooks don't see each
    other's rewrites - so capturing what the model actually gets has to
    happen here, at the point the rewrite is made.
    """

    async def normalise_tool_output(
        input_data: PostToolUseHookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> dict:
        tool_response = input_data["tool_response"]

        # For an MCP tool call, tool_response is the "content" array itself
        # (a list of content blocks) - not a dict - since that's the only
        # part of the CallToolResult the model actually reads. Find the
        # first text block whose text is a JSON object with our fields.
        if isinstance(tool_response, list):
            for index, block in enumerate(tool_response):
                if not isinstance(block, dict) or block.get("type") != "text":
                    continue
                try:
                    record = json.loads(block.get("text", ""))
                except (TypeError, ValueError):
                    continue
                if not isinstance(record, dict):
                    continue

                normalised = _normalise_record(record)
                if seen is not None:
                    seen.append(normalised)
                if normalised == record:
                    return {}

                updated_blocks = [dict(b) for b in tool_response]
                updated_blocks[index]["text"] = json.dumps(normalised)
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "updatedToolOutput": updated_blocks,
                    }
                }
            return {}

        # Fallback for a tool_response that is already the flat record dict
        # (e.g. a tool exercised directly, outside the MCP content wrapper).
        if isinstance(tool_response, dict):
            normalised = _normalise_record(tool_response)
            if seen is not None:
                seen.append(normalised)
            if normalised == tool_response:
                return {}

            return {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "updatedToolOutput": normalised,
                }
            }

        return {}

    return normalise_tool_output


normalise_tool_output = make_normalising_hook()
