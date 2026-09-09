import json

from claude import client

MODEL = "claude-haiku-4-5"
MAX_TOOL_ROUNDS = 2
# output_config.effort is only supported on Sonnet/Opus-tier models, and is
# moot on Haiku anyway (Haiku doesn't run adaptive thinking by default).
REQUEST_KWARGS = {} if MODEL == "claude-haiku-4-5" else {"output_config": {"effort": "low"}}


def search_documents(query: str) -> dict:
    return {
        "query": query,
        "documents": [
            {
                "title": "Internal Report 1",
                "source": "docs://internal/report-1",
                "excerpt": f"Mock document excerpt relevant to: {query}",
            },
            {
                "title": "Internal Report 2",
                "source": "docs://internal/report-2",
                "excerpt": f"Another mock document excerpt relevant to: {query}",
            },
        ],
    }


class DocAnalysisAgent:
    system_prompt = (
        "You are a document analysis specialist. Given a subtopic and its "
        "broader research goal, use the search_documents tool to find "
        "relevant internal documentation, then report structured findings, "
        "one per line, each with a source reference and a confidence level."
    )

    tools = [
        {
            "name": "search_documents",
            "description": "Search internal documentation and return matching excerpts.",
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
                    "Use the search_documents tool as needed, then return "
                    "structured findings with source references and confidence levels."
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

            if response.stop_reason == "end_turn":
                findings.extend(
                    block.text
                    for block in response.content
                    if block.type == "text" and block.text.strip()
                )
                break

            if response.stop_reason != "tool_use":
                raise RuntimeError(
                    f"unexpected stop_reason {response.stop_reason!r} "
                    f"researching {subtopic!r}"
                )

            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_use in (b for b in response.content if b.type == "tool_use"):
                result = search_documents(tool_use.input["query"])
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    }
                )

            messages.append({"role": "user", "content": tool_results})

        return {"topic": subtopic, "findings": findings}


doc_analysis_agent = DocAnalysisAgent()
