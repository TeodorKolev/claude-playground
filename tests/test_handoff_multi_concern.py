import pytest

from agents.support_agent import support_agent

REQUEST = (
    "I'm Alice Chen (alice@example.com). I need to return order ord_1001, "
    "dispute a charge of $45.00 on my last bill, and update my shipping "
    "address to 123 New Street. Please handle all of this."
)

# None of the four tools (get_customer, lookup_order, process_refund,
# escalate_to_human) can resolve a billing dispute or an address change, so
# this compound request should end in a single handoff that covers all
# three concerns - not just the return, which is the item the agent has
# the most direct tooling for and the easiest one to silently privilege.
CONCERN_KEYWORDS = {
    "return": ["return", "ord_1001"],
    "billing dispute": ["dispute", "45.00", "45"],
    "address update": ["address", "123 new street", "shipping"],
}


def _covers_concern(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


@pytest.mark.asyncio
async def test_handoff_covers_all_three_concerns_in_compound_request():
    result = await support_agent.run(REQUEST)

    escalations = [
        c
        for c in result["tool_calls"]
        if c["name"] == "escalate_to_human" and c["result"].get("status") == "escalated"
    ]

    assert escalations, (
        "agent never produced a successful handoff for this multi-concern "
        f"request: {result['tool_calls']}"
    )

    handoff = escalations[-1]["result"]["handoff"]

    # Self-contained per the handoff contract: identity and at least one
    # concrete concern-specific detail must be present, not just the
    # customer's own restatement of the request.
    assert handoff["customer_id"] == "cust_001"

    combined_text = " ".join(
        [handoff["conversation_summary"], handoff["recommended_action"]]
    )

    missing = [
        concern
        for concern, keywords in CONCERN_KEYWORDS.items()
        if not _covers_concern(combined_text, keywords)
    ]

    print(handoff)

    assert not missing, (
        f"handoff omitted concern(s): {', '.join(missing)}\n"
        f"conversation_summary: {handoff['conversation_summary']}\n"
        f"recommended_action: {handoff['recommended_action']}"
    )
