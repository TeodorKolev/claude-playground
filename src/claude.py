import os

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

load_dotenv()

client = AsyncAnthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

tools = [
    {
        "name": "calculator",
        "description": "Calculate a mathematical expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to calculate.",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "web_search",
        "description": "Search the web and return mock search results.",
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
    },
]
