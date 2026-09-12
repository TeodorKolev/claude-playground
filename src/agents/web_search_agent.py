from claude_agent_sdk import AgentDefinition

from model_config import MODEL

web_search_agent = AgentDefinition(
    description=(
        "Searches the web for current information and returns results "
        "with source URLs and titles."
    ),
    prompt=(
        "Search for information on the given topic. Return each finding as "
        "JSON matching this Finding schema: claim (the content), "
        "source_url, document_name (null — you have no document), "
        "page_number (null — you have no document), confidence "
        "('high'|'medium'|'low'), retrieved_by ('web-search'). Keep the "
        "claim itself free of citation details — those belong in the "
        "metadata fields, not embedded in the claim text."
    ),
    tools=["WebSearch"],
    model=MODEL,
    maxTurns=6,
)
