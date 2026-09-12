import json

from claude import client
from tools.customer_support import (
    SessionState,
    escalate_to_human,
    get_customer,
    lookup_order,
    process_refund,
)

MODEL = "claude-haiku-4-5"
MAX_TOOL_ROUNDS = 5
# output_config.effort is only supported on Sonnet/Opus-tier models, and is
# moot on Haiku anyway (Haiku doesn't run adaptive thinking by default).
REQUEST_KWARGS = {} if MODEL == "claude-haiku-4-5" else {"output_config": {"effort": "low"}}


class SupportAgent:
    system_prompt = (
        "You are a customer support agent. Use get_customer to look up "
        "and verify a customer before taking any action on their behalf. "
        "Use lookup_order to find order details. Use process_refund to "
        "refund a verified customer. Never call process_refund for a "
        "customer you have not first looked up with get_customer. "
        "If you cannot resolve the issue yourself, call escalate_to_human. "
        "The human agent who picks it up will NOT see this conversation, "
        "so the handoff must be fully self-contained: a concrete summary "
        "of what happened, your root cause analysis, and a specific "
        "recommended action - no placeholders like 'TBD' or 'unknown'."
    )

    tools = [
        {
            "name": "get_customer",
            "description": "Look up and verify a customer by name or email.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Customer name or email.",
                    }
                },
                "required": ["query"],
            },
        },
        {
            "name": "lookup_order",
            "description": "Look up order details by order ID.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up.",
                    }
                },
                "required": ["order_id"],
            },
        },
        {
            "name": "process_refund",
            "description": "Process a refund for a verified customer.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The verified customer's ID, from get_customer.",
                    },
                    "amount": {
                        "type": "number",
                        "description": "The refund amount.",
                    },
                },
                "required": ["customer_id", "amount"],
            },
        },
        {
            "name": "escalate_to_human",
            "description": (
                "Escalate to a human agent with a self-contained structured "
                "summary. The human agent cannot see this conversation."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer's ID.",
                    },
                    "conversation_summary": {
                        "type": "string",
                        "description": "What happened in the conversation so far.",
                    },
                    "root_cause_analysis": {
                        "type": "string",
                        "description": "Your analysis of why this needs a human.",
                    },
                    "refund_amount": {
                        "type": "number",
                        "description": "Refund amount in question, if applicable.",
                    },
                    "recommended_action": {
                        "type": "string",
                        "description": "What the human agent should do next.",
                    },
                },
                "required": [
                    "customer_id",
                    "conversation_summary",
                    "root_cause_analysis",
                    "recommended_action",
                ],
            },
        },
    ]

    async def run(self, request: str) -> dict:
        messages = [{"role": "user", "content": request}]

        # Fresh per call: verification must not leak across sessions.
        session = SessionState()
        replies: list[str] = []
        tool_calls: list[dict] = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=self.system_prompt,
                tools=self.tools,
                **REQUEST_KWARGS,
                messages=messages,
            )

            if response.stop_reason == "end_turn":
                replies.extend(
                    block.text
                    for block in response.content
                    if block.type == "text" and block.text.strip()
                )
                break

            if response.stop_reason != "tool_use":
                raise RuntimeError(f"unexpected stop_reason {response.stop_reason!r}")

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in (b for b in response.content if b.type == "tool_use"):
                result = self._execute_tool(tool_use.name, tool_use.input, session)
                tool_calls.append(
                    {"name": tool_use.name, "input": tool_use.input, "result": result}
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        return {"request": request, "replies": replies, "tool_calls": tool_calls}

    def _execute_tool(
        self,
        name: str,
        tool_input: dict,
        session: SessionState,
    ) -> dict:
        if name == "get_customer":
            result = get_customer(tool_input["query"])
            session.record_customer(result)
            return result

        if name == "lookup_order":
            return lookup_order(tool_input["order_id"])

        if name == "process_refund":
            return process_refund(
                tool_input["customer_id"],
                tool_input["amount"],
                session,
            )

        if name == "escalate_to_human":
            return escalate_to_human(
                tool_input["customer_id"],
                tool_input["conversation_summary"],
                tool_input["root_cause_analysis"],
                tool_input["recommended_action"],
                tool_input.get("refund_amount"),
            )

        raise ValueError(f"unknown tool {name!r}")


support_agent = SupportAgent()
