import re

from schemas import Finding, ResearchReport

# Matches the exact citation forms the synthesis subagent is instructed to
# append after each claim (see agents/synthesis_agent.py): '[source_url]' or
# '[document_name, p. page_number]'. Anchoring on the bracket itself (rather
# than guessing sentence boundaries with '.'/'!'/'?') avoids false splits on
# periods that occur inside the citation, e.g. 'p. 99'.
CLAIM_RE = re.compile(
    r"(?P<body>.*?)\[(?P<reference>[^\[\],]+)(?:,\s*p\.\s*(?P<page>\d+))?\]",
    re.DOTALL,
)


def all_findings(report: ResearchReport) -> list[Finding]:
    return [
        finding
        for section in report["sections"]
        for finding in section["findings"]
    ]


def find_uncited_claims(report_text: str, findings: list[Finding]) -> list[str]:
    """Return every claim in `report_text` that either has no citation
    bracket, or whose citation doesn't match a source_url, or a
    document_name/page_number pair, present in `findings`.

    A returned claim does not by itself mean the synthesis prompt failed:
    check first whether the missing source_url / document_name / page_number
    was actually present in `findings`. If it wasn't, the failure is
    upstream — the coordinator didn't pass complete finding metadata to the
    synthesis subagent (see coordinator.py's delegation instructions) — not
    a synthesis-prompt problem.
    """
    known_urls = {f["source_url"] for f in findings if f["source_url"]}
    known_doc_pages = {
        (f["document_name"], f["page_number"])
        for f in findings
        if f["document_name"] and f["page_number"] is not None
    }

    uncited = []
    pos = 0
    for match in CLAIM_RE.finditer(report_text):
        body = match.group("body").strip()
        pos = match.end()
        if not body:
            continue

        reference, page = match.group("reference"), match.group("page")
        cited = (
            (reference, int(page)) in known_doc_pages
            if page is not None
            else reference in known_urls
        )
        if not cited:
            uncited.append(body)

    trailing = report_text[pos:].strip()
    if trailing:
        uncited.append(trailing)

    return uncited


def verify_synthesis_citations(report: ResearchReport) -> list[str]:
    return find_uncited_claims(report["synthesized_report"], all_findings(report))
