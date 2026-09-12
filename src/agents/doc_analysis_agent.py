from claude_agent_sdk import AgentDefinition

from model_config import MODEL

doc_analysis_agent = AgentDefinition(
    description="Analyses documents and returns findings with page references.",
    prompt=(
        "Analyse the provided documents. Return each finding as JSON "
        "matching this Finding schema: claim (the content), source_url "
        "(null — you have no URL), document_name, page_number, confidence "
        "('high'|'medium'|'low'), retrieved_by ('doc-analysis'). Keep the "
        "claim itself free of citation details — those belong in the "
        "metadata fields, not embedded in the claim text."
    ),
    tools=["Read", "Grep"],
    model=MODEL,
    maxTurns=6,
)
