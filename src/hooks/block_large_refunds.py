from claude_agent_sdk import HookContext, PreToolUseHookInput

# PreToolUse runs before the tool executes, so a "deny" here stops the
# refund from ever happening - unlike PostToolUse, which only sees results
# after the action already occurred and is too late to enforce a policy.
REFUND_LIMIT = 500


async def block_large_refunds(
    input_data: PreToolUseHookInput,
    tool_use_id: str | None,
    context: HookContext,
) -> dict:
    amount = input_data["tool_input"].get("amount")

    if isinstance(amount, (int, float)) and not isinstance(amount, bool) and amount > REFUND_LIMIT:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Refund of ${amount:.2f} exceeds the ${REFUND_LIMIT} threshold and "
                    "cannot be processed automatically. Use escalate_to_human to hand this "
                    "off to a human agent instead of retrying process_refund."
                ),
            }
        }

    return {}
