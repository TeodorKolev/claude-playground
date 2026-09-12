import json

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, create_sdk_mcp_server, tool

from hooks.block_large_refunds import block_large_refunds
from tools.customer_support import SessionState, escalate_to_human, process_refund

MODEL = "claude-haiku-4-5"
PAYMENTS_MCP_TOOL_NAMES = [
    "mcp__payments__process_refund",
    "mcp__payments__escalate_to_human",
]


@tool("process_refund", "Process a refund for a verified customer.", {"customer_id": str, "amount": float})
async def _process_refund(args: dict) -> dict:
    # Identity verification is a separate concern, already covered by
    # tools/customer_support.py's own gate and tests - every call here is
    # treated as pre-verified so this tool can focus on the PreToolUse
    # amount gate below.
    session = SessionState()
    session.record_customer({"customer_id": args["customer_id"], "verified": True})
    result = process_refund(args["customer_id"], args["amount"], session)
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


@tool(
    "escalate_to_human",
    "Escalate to a human agent with a self-contained structured summary.",
    {
        "customer_id": str,
        "conversation_summary": str,
        "root_cause_analysis": str,
        "recommended_action": str,
    },
)
async def _escalate_to_human(args: dict) -> dict:
    result = escalate_to_human(
        args["customer_id"],
        args["conversation_summary"],
        args["root_cause_analysis"],
        args["recommended_action"],
    )
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


payments_mcp_server = create_sdk_mcp_server(
    "payments",
    tools=[_process_refund, _escalate_to_human],
)

# Matched to the refund tool specifically, so the callback never has to
# check tool_name itself - escalate_to_human is left untouched.
support_agent_options = ClaudeAgentOptions(
    model=MODEL,
    tools=[],  # no built-in tools (Bash, Read, ...) - only the MCP payments tools below
    mcp_servers={"payments": payments_mcp_server},
    allowed_tools=PAYMENTS_MCP_TOOL_NAMES,
    permission_mode="bypassPermissions",
    system_prompt=(
        "Use process_refund to refund a customer. If a refund is denied or "
        "cannot be processed, use escalate_to_human to hand it off, with a "
        "concrete summary, root cause, and recommended action."
    ),
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="mcp__payments__process_refund", hooks=[block_large_refunds])
        ]
    },
)
