from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, create_sdk_mcp_server, tool

from hooks.normalize_tool_output import normalise_tool_output
from tools.record_sources import get_customer_record, get_order_record, get_shipment_record


@tool("get_customer_record", "Look up a customer record by customer ID.", {"customer_id": str})
async def _get_customer_record(args: dict) -> dict:
    record = get_customer_record(args["customer_id"])
    return {"content": [{"type": "text", "text": str(record)}], "structuredContent": record}


@tool("get_order_record", "Look up an order record by order ID.", {"order_id": str})
async def _get_order_record(args: dict) -> dict:
    record = get_order_record(args["order_id"])
    return {"content": [{"type": "text", "text": str(record)}], "structuredContent": record}


@tool("get_shipment_record", "Look up a shipment record by shipment ID.", {"shipment_id": str})
async def _get_shipment_record(args: dict) -> dict:
    record = get_shipment_record(args["shipment_id"])
    return {"content": [{"type": "text", "text": str(record)}], "structuredContent": record}


records_mcp_server = create_sdk_mcp_server(
    "records",
    tools=[_get_customer_record, _get_order_record, _get_shipment_record],
)

# The matcher covers every tool this server exposes (mcp__records__*), so
# every date/status format the three backends use gets normalised the same
# way regardless of which tool the model calls.
records_agent_options = ClaudeAgentOptions(
    mcp_servers={"records": records_mcp_server},
    allowed_tools=[
        "mcp__records__get_customer_record",
        "mcp__records__get_order_record",
        "mcp__records__get_shipment_record",
    ],
    hooks={"PostToolUse": [HookMatcher(matcher="mcp__records__.*", hooks=[normalise_tool_output])]},
)
