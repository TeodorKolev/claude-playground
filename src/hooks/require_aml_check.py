from claude_agent_sdk import HookContext, PostToolUseHookInput, PreToolUseHookInput

from hooks._mcp_content import read_json_record


class AmlState:
    """Tracks whether aml_check has passed in this session.

    One instance must be created per agent session and never reused across
    sessions: a bare module-level flag would let an AML pass recorded for
    one customer's transfer silently clear the check for every other
    customer's session for the lifetime of the process - exactly the kind
    of gap this hook exists to close.
    """

    def __init__(self):
        self.passed = False


def make_aml_hooks(state: AmlState | None = None):
    """Build the (PreToolUse, PostToolUse) hook pair sharing one AmlState.

    require_aml_check denies transfer_funds until record_aml_result has
    seen a passing aml_check in the same state - two callbacks, one flag,
    same session.
    """
    state = state if state is not None else AmlState()

    async def require_aml_check(
        input_data: PreToolUseHookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> dict:
        if state.passed:
            return {}

        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "COMPLIANCE BLOCK: transfer_funds requires a passing "
                    "aml_check in this session. Run aml_check first."
                ),
            }
        }

    async def record_aml_result(
        input_data: PostToolUseHookInput,
        tool_use_id: str | None,
        context: HookContext,
    ) -> dict:
        record = read_json_record(input_data["tool_response"])
        if isinstance(record, dict) and record.get("status") == "pass":
            state.passed = True

        return {}

    return require_aml_check, record_aml_result
