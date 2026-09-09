import pytest

from coordinator import coordinator


@pytest.mark.asyncio
async def test_renewable_energy_coverage():
    report = await coordinator.research("renewable energy technologies")

    required = [
        "solar",
        "wind",
        "geothermal",
        "tidal",
        "biomass",
        "fusion",
    ]

    missing = [
        category
        for category in required
        if not any(
            category in section["topic"].lower()
            for section in report["sections"]
        )
    ]

    assert not missing, f"Missing: {', '.join(missing)}"