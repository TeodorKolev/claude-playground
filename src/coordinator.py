# coordinator.py

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agents.synthesis_agent import synthesis_agent
from agents.web_search_agent import web_search_agent
from model_config import MODEL
from schemas import FINDING_SCHEMA, ResearchReport
from verification import all_findings, verify_synthesis_citations

RESEARCH_REPORT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "topic": {"type": "string"},
            "subtopics": {"type": "array", "items": {"type": "string"}},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "findings": {
                            "type": "array",
                            "items": FINDING_SCHEMA,
                        },
                    },
                    "required": ["topic", "findings"],
                },
            },
            "coverage": {
                "type": "object",
                "properties": {
                    "covered": {"type": "array", "items": {"type": "string"}},
                    "gaps": {"type": "array", "items": {"type": "string"}},
                    "completeness": {"type": "number"},
                },
                "required": ["covered", "gaps", "completeness"],
            },
            "iterations": {"type": "integer"},
            "synthesized_report": {"type": "string"},
        },
        "required": [
            "topic",
            "subtopics",
            "sections",
            "coverage",
            "iterations",
            "synthesized_report",
        ],
    },
}


class Coordinator:
    system_prompt = (
        "You are a research coordinator running in quick mode: favor speed "
        "over exhaustive coverage. You have a WebSearch tool available, "
        "but it exists only so the web-search subagent can use it — you "
        "must never call WebSearch yourself. Always delegate research to "
        "the web-search subagent via the Agent tool; if you call WebSearch "
        "directly, findings skip the subagent's structured-JSON output "
        "entirely and break attribution for the whole pipeline. "
        "Decompose the topic into exactly 4-5 "
        "subtopics — pick the most important ones, do not aim for "
        "exhaustive breadth. For all subtopics, delegate to the web-search "
        "subagent using the Agent tool, invoking every subtopic's call in "
        "parallel: emit all of that round's Agent tool calls together in "
        "a single response rather than waiting for one to finish before "
        "starting the next. Aggregate the findings into sections. "
        "Do a single pass only — no refinement iterations, no follow-up "
        "research on gaps. Report iterations as 1, and coverage as "
        "whatever the single pass actually produced (do not delegate "
        "further research to improve completeness). "
        "The web-search subagent returns findings as structured JSON (claim plus "
        "attribution metadata: source_url, document_name, page_number, "
        "confidence, retrieved_by). Preserve every finding's metadata "
        "fields exactly as returned — never collapse a finding into a "
        "prose sentence or drop its source_url/document_name/page_number/"
        "confidence/retrieved_by, since that is what makes the final "
        "report citable.\n\n"
        "Once the single research pass is done, delegate to the synthesis "
        "subagent exactly once to produce synthesized_report. When you "
        "invoke it via the Agent tool, embed the complete findings arrays "
        "from every section, verbatim, as JSON, in its prompt — every "
        "finding's full object (claim, source_url, document_name, "
        "page_number, confidence, retrieved_by), not just the claim "
        "strings and not a summary. Passing only claim text to the "
        "synthesis subagent is the single most common failure here: it "
        "leaves the synthesis subagent unable to cite anything, so do not "
        "do it."
    )

    agents = {
        "web-search": web_search_agent,
        "synthesis": synthesis_agent,
    }

    async def research(self, topic: str) -> ResearchReport:
        options = ClaudeAgentOptions(
            system_prompt=self.system_prompt,
            # `tools` sets the base toolset for the whole session, including
            # subagents — a subagent's own `tools` can only select from
            # within this base, not add capabilities beyond it. WebSearch
            # must be listed here for the web-search subagent's own
            # tools=["WebSearch"] to actually grant anything.
            tools=["Agent", "WebSearch"],
            allowed_tools=["Agent"],
            agents=self.agents,
            output_format=RESEARCH_REPORT_SCHEMA,
            permission_mode="bypassPermissions",
            model=MODEL,
            max_turns=15,
            max_budget_usd=0.5,
        )

        result: ResultMessage | None = None
        async for message in query(
            prompt=(
                f"Research this topic quickly: {topic}. Pick 4-5 subtopics, "
                "invoke the web-search subagent for all of them in "
                "parallel — emit all of that round's Agent tool calls in a "
                "single response — then pass their complete structured "
                "findings to the synthesis subagent. Single pass only, no "
                "refinement."
            ),
            options=options,
        ):
            if isinstance(message, ResultMessage):
                result = message

        if result is None:
            raise RuntimeError(f"no result returned researching {topic!r}")
        if result.is_error:
            raise RuntimeError(f"research failed for {topic!r}: {result.result}")

        report: ResearchReport = result.structured_output

        uncited = verify_synthesis_citations(report)
        if uncited:
            findings_have_metadata = any(
                f["source_url"] or f["document_name"] for f in all_findings(report)
            )
            cause = (
                "synthesis subagent didn't cite them correctly"
                if findings_have_metadata
                else "findings had no source_url/document_name to cite — "
                "trace back to whether the coordinator passed complete "
                "finding metadata to the synthesis subagent"
            )
            print(
                f"WARNING: {len(uncited)} uncited claim(s) in synthesized_report "
                f"for {topic!r} ({cause}):"
            )
            for claim in uncited:
                print(f"  - {claim}")

        return report


coordinator = Coordinator()
