import json

from claude import client
from tools.web_search import web_search

MODEL = "claude-haiku-4-5"
MAX_TOOL_ROUNDS = 2
# output_config.effort is only supported on Sonnet/Opus-tier models, and is
# moot on Haiku anyway (Haiku doesn't run adaptive thinking by default).
REQUEST_KWARGS = {} if MODEL == "claude-haiku-4-5" else {"output_config": {"effort": "low"}}


class WebSearchAgent:
    system_prompt = (
        "You are a web research specialist. Given a subtopic and its "
        "broader research goal, use the web_search tool to gather "
        "relevant, credible information. Report structured findings, "
        "one per line, each with a source URL and a confidence level."
    )

    tools = [
        {
            "name": "web_search",
            "description": "Search the web and return results with titles, URLs, and snippets.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    }
                },
                "required": ["query"],
            },
        }
    ]

    async def run(self, subtopic: str, context: str) -> dict:
        messages = [
            {
                "role": "user",
                "content": (
                    f"Research subtopic: {subtopic}\n"
                    f"Broader goal: {context}\n"
                    "Use the web_search tool as needed, then return "
                    "structured findings with source URLs and confidence levels."
                ),
            }
        ]

        findings: list[str] = []

        for _ in range(MAX_TOOL_ROUNDS):
            response = await client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=self.system_prompt,
                tools=self.tools,
                **REQUEST_KWARGS,
                messages=messages,
            )

            tool_uses = [block for block in response.content if block.type == "tool_use"]

            if not tool_uses:
                findings.extend(
                    block.text
                    for block in response.content
                    if block.type == "text" and block.text.strip()
                )
                break

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in tool_uses:
                result = web_search(tool_use.input["query"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        return {"topic": subtopic, "findings": findings}


web_search_agent = WebSearchAgent()
