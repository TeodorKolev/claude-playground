from claude_agent_sdk import AgentDefinition

from model_config import MODEL

synthesis_agent = AgentDefinition(
    description=(
        "Synthesises structured findings from the other research subagents "
        "into a coherent, fully-cited report. Takes no actions of its own — "
        "it only reasons over the findings it is given."
    ),
    prompt=(
        "Synthesise the research findings you are given into a coherent "
        "report. Your instructions will embed the complete findings arrays "
        "verbatim, as JSON, from the other subagents — every finding "
        "carries claim, source_url, document_name, page_number, "
        "confidence, and retrieved_by. Never assume you were given only "
        "claim text; if metadata for a finding is missing from what you "
        "were given, treat that finding as uncited rather than inventing "
        "a source.\n\n"
        "Every factual claim in your report MUST cite its source, and each "
        "claim must be its own sentence so citations stay unambiguous. "
        "Append the citation to the end of the sentence, in exactly one of "
        "these forms:\n"
        "  - '[source_url]' verbatim, when the finding has a source_url.\n"
        "  - '[document_name, p. page_number]' verbatim, when the finding "
        "has a document_name and page_number.\n"
        "Do not state a claim without its citation attached, do not "
        "paraphrase or truncate the source_url/document_name, and do not "
        "merge multiple findings' citations into one sentence."
    ),
    tools=[],
    model=MODEL,
    maxTurns=3,
)
