import pytest

from coordinator import coordinator
from verification import verify_synthesis_citations


@pytest.mark.asyncio
async def test_quick_research_produces_a_cited_report():
    report = await coordinator.research("renewable energy technologies")

    # Quick mode: 4-5 subtopics, single pass, no refinement.
    assert 1 <= len(report["subtopics"]) <= 5
    assert report["iterations"] == 1
    assert report["sections"], "expected at least one section of findings"

    candidate_categories = [
        "solar",
        "wind",
        "geothermal",
        "tidal",
        "biomass",
        "fusion",
        "hydro",
        "nuclear",
    ]
    covered = [
        category
        for category in candidate_categories
        if any(
            category in section["topic"].lower() for section in report["sections"]
        )
    ]
    assert covered, "expected at least one recognizable renewable-energy category"

    assert report["synthesized_report"].strip()

    uncited = verify_synthesis_citations(report)
    assert not uncited, f"uncited claims in synthesized_report: {uncited}"
