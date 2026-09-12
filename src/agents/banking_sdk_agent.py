import json

from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, create_sdk_mcp_server, tool

from hooks.require_aml_check import AmlState, make_aml_hooks
from tools.banking import aml_check, transfer_funds

MODEL = "claude-haiku-4-5"
BANKING_MCP_TOOL_NAMES = [
    "mcp__banking__aml_check",
    "mcp__banking__transfer_funds",
]


@tool("aml_check", "Run an anti-money-laundering check on an account.", {"account_id": str})
async def _aml_check(args: dict) -> dict:
    result = aml_check(args["account_id"])
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


@tool(
    "transfer_funds",
    "Transfer funds from an account to a destination account.",
    {"account_id": str, "destination": str, "amount": float},
)
async def _transfer_funds(args: dict) -> dict:
    result = transfer_funds(args["account_id"], args["destination"], args["amount"])
    return {"content": [{"type": "text", "text": json.dumps(result)}]}


banking_mcp_server = create_sdk_mcp_server(
    "banking",
    tools=[_aml_check, _transfer_funds],
)


def build_banking_agent_options() -> ClaudeAgentOptions:
    """Build fresh ClaudeAgentOptions with their own AmlState.

    A new AmlState (and the two hooks closed over it) is built per call: the
    same state must be shared between the PreToolUse and PostToolUse hooks
    within one session, but never across sessions - see AmlState's docstring.
    """
    require_aml_check, record_aml_result = make_aml_hooks(AmlState())

    return ClaudeAgentOptions(
        model=MODEL,
        tools=[],  # no built-in tools (Bash, Read, ...) - only the MCP banking tools below
        mcp_servers={"banking": banking_mcp_server},
        allowed_tools=BANKING_MCP_TOOL_NAMES,
        permission_mode="bypassPermissions",
        system_prompt=(
            "Use aml_check to verify an account, then transfer_funds to move "
            "money. transfer_funds is blocked until aml_check has passed "
            "for this account in this session."
        ),
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="mcp__banking__transfer_funds", hooks=[require_aml_check])
            ],
            "PostToolUse": [
                HookMatcher(matcher="mcp__banking__aml_check", hooks=[record_aml_result])
            ],
        },
    )
