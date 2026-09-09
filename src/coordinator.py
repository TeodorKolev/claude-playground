# coordinator.py

import asyncio

from claude import client
from agents.web_search_agent import web_search_agent
from agents.doc_analysis_agent import doc_analysis_agent

MODEL = "claude-haiku-4-5"
# output_config.effort is only supported on Sonnet/Opus-tier models, and is
# moot on Haiku anyway (Haiku doesn't run adaptive thinking by default).
REQUEST_KWARGS = {} if MODEL == "claude-haiku-4-5" else {"output_config": {"effort": "low"}}


class Coordinator:
    system_prompt = (
        "You are a research coordinator. "
        "Decompose topics into comprehensive subtopics, "
        "delegate to specialist subagents, aggregate results, "
        "and identify coverage gaps. "
        "A decomposition is only comprehensive if it covers the full "
        "breadth of the topic: mainstream approaches as well as "
        "lesser-known, emerging, or experimental ones. Never limit "
        "yourself to the handful of approaches that come to mind first "
        "or the ones that are most commonly discussed."
    )

    subagents = [
        web_search_agent,
        doc_analysis_agent,
    ]

    async def evaluate_coverage(
        self,
        subtopics: list[str],
        results: list[dict],
    ) -> dict:
        covered = [
            subtopic
            for subtopic in subtopics
            if any(
                result["topic"] == subtopic
                and len(result["findings"]) > 0
                for result in results
            )
        ]

        gaps = [
            subtopic
            for subtopic in subtopics
            if subtopic not in covered
        ]

        completeness = (
            len(covered) / len(subtopics)
            if subtopics
            else 1.0
        )

        return {
            "covered": covered,
            "gaps": gaps,
            "completeness": completeness,
        }

    async def research(self, topic: str):
        subtopics = await self.decompose(topic)

        all_results = []

        # Initial research
        for subtopic in subtopics:
            result = await self.delegate_to_subagents(subtopic, topic)
            all_results.append(result)

        # Evaluate initial coverage
        coverage = await self.evaluate_coverage(
            subtopics,
            all_results,
        )

        # Iterative refinement
        iterations = 0
        max_iterations = 3
        coverage_threshold = 0.9

        while (
            coverage["completeness"] < coverage_threshold
            and iterations < max_iterations
        ):
            print(
                f"Coverage: {coverage['completeness']:.0%}. "
                f"Gaps: {coverage['gaps']}"
            )

            # Only research the missing subtopics
            for gap in coverage["gaps"]:
                new_result = await self.delegate_to_subagents(gap, topic)
                all_results.append(new_result)

            # Re-evaluate after targeted research
            coverage = await self.evaluate_coverage(
                subtopics,
                all_results,
            )

            iterations += 1

        return {
            "topic": topic,
            "subtopics": subtopics,
            "sections": all_results,
            "coverage": coverage,
            "iterations": iterations,
        }

    async def decompose(self, topic: str) -> list[str]:
        response = await client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=self.system_prompt,
            **REQUEST_KWARGS,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Decompose this research topic into subtopics, "
                        "covering the full breadth of the field: both "
                        "established, widely-deployed approaches and "
                        "emerging or experimental ones that are still "
                        "maturing. Return one subtopic per line, with no "
                        f"numbering or extra commentary:\n\n{topic}"
                    ),
                }
            ],
        )

        text = "".join(
            block.text for block in response.content if block.type == "text"
        )

        return [line.strip("-* \t") for line in text.splitlines() if line.strip()]

    async def delegate_to_subagents(
        self,
        subtopic: str,
        context: str,
    ) -> dict:
        results = await asyncio.gather(
            *(agent.run(subtopic, context) for agent in self.subagents),
            return_exceptions=True,
        )

        findings = []
        for agent, result in zip(self.subagents, results):
            if isinstance(result, Exception):
                print(f"{type(agent).__name__} failed on {subtopic!r}: {result}")
                continue
            findings.extend(result["findings"])

        return {"topic": subtopic, "findings": findings}


coordinator = Coordinator()
