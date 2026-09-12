import json


def read_json_record(tool_response) -> dict | None:
    """Extract the record dict a tool call actually produced.

    An MCP tool's tool_response is the "content" array itself (a list of
    content blocks with JSON text), not a dict - confirmed by driving a real
    SDK MCP tool call through query() and logging what a hook received. A
    tool exercised outside that wrapper may hand back the flat dict instead.
    """
    if isinstance(tool_response, list):
        for block in tool_response:
            if not isinstance(block, dict) or block.get("type") != "text":
                continue
            try:
                record = json.loads(block.get("text", ""))
            except (TypeError, ValueError):
                continue
            if isinstance(record, dict):
                return record
        return None

    if isinstance(tool_response, dict):
        return tool_response

    return None
