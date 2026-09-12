import json

from claude import client
from tools.record_sources import get_customer_record, get_order_record, get_shipment_record

MODEL = "claude-haiku-4-5"
MAX_TOOL_ROUNDS = 4
# output_config.effort is only supported on Sonnet/Opus-tier models, and is
# moot on Haiku anyway (Haiku doesn't run adaptive thinking by default).
REQUEST_KWARGS = {} if MODEL == "claude-haiku-4-5" else {"output_config": {"effort": "low"}}


class RecordsAgent:
    # No normalization guidance given on purpose: each backend's tool
    # returns dates and statuses in its own format, and this agent is the
    # baseline for observing how inconsistently a model reconciles them
    # without an explicit normalization contract.
    system_prompt = (
        "You are a records lookup agent. Use get_customer_record, "
        "get_order_record, and get_shipment_record to retrieve records as "
        "needed, then report back each record's created_at date and status."
    )

    tools = [
        {
            "name": "get_customer_record",
            "description": "Look up a customer record by customer ID.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "string",
                        "description": "The customer ID to look up.",
                    }
                },
                "required": ["customer_id"],
            },
        },
        {
            "name": "get_order_record",
            "description": "Look up an order record by order ID.",
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
            "name": "get_shipment_record",
            "description": "Look up a shipment record by shipment ID.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "shipment_id": {
                        "type": "string",
                        "description": "The shipment ID to look up.",
                    }
                },
                "required": ["shipment_id"],
            },
        },
    ]

    async def run(self, request: str) -> dict:
        messages = [{"role": "user", "content": request}]

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
                result = self._execute_tool(tool_use.name, tool_use.input)
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

    def _execute_tool(self, name: str, tool_input: dict) -> dict:
        if name == "get_customer_record":
            return get_customer_record(tool_input["customer_id"])

        if name == "get_order_record":
            return get_order_record(tool_input["order_id"])

        if name == "get_shipment_record":
            return get_shipment_record(tool_input["shipment_id"])

        raise ValueError(f"unknown tool {name!r}")


records_agent = RecordsAgent()
