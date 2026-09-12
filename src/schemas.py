from typing import Literal, TypedDict


class Finding(TypedDict):
    """A single research finding, with content separated from attribution
    metadata so any downstream step can produce a citation without the
    coordinator having to smuggle source details into the claim text."""

    claim: str
    source_url: str | None
    document_name: str | None
    page_number: int | None
    confidence: Literal["high", "medium", "low"]
    retrieved_by: str


class Section(TypedDict):
    topic: str
    findings: list[Finding]


class Coverage(TypedDict):
    covered: list[str]
    gaps: list[str]
    completeness: float


class ResearchReport(TypedDict):
    topic: str
    subtopics: list[str]
    sections: list[Section]
    coverage: Coverage
    iterations: int
    # Produced by the synthesis subagent from the complete, metadata-intact
    # findings of every other subagent — every claim here must cite a
    # source_url or a document_name/page_number pair.
    synthesized_report: str


FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "claim": {"type": "string"},
        "source_url": {"type": ["string", "null"]},
        "document_name": {"type": ["string", "null"]},
        "page_number": {"type": ["integer", "null"]},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
        "retrieved_by": {"type": "string"},
    },
    "required": list(Finding.__annotations__.keys()),
}
