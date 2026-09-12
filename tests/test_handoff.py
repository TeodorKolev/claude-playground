from tools.customer_support import escalate_to_human

VALID_KWARGS = dict(
    customer_id="cust_002",
    conversation_summary=(
        "Customer says order ord_1002 (Desk Lamp) arrived broken and wants a refund."
    ),
    root_cause_analysis=(
        "Customer could not be verified via get_customer, so process_refund "
        "was blocked by the verification gate."
    ),
    recommended_action=(
        "Verify the customer's identity manually, then refund $34.50 for ord_1002."
    ),
)


def test_handoff_succeeds_with_all_fields_populated():
    result = escalate_to_human(**VALID_KWARGS, refund_amount=34.50)

    assert result["status"] == "escalated"
    handoff = result["handoff"]
    for field in (
        "customer_id",
        "conversation_summary",
        "root_cause_analysis",
        "refund_amount",
        "recommended_action",
    ):
        assert field in handoff
    assert handoff["refund_amount"] == 34.50


def test_handoff_allows_refund_amount_to_be_omitted_when_not_applicable():
    result = escalate_to_human(**VALID_KWARGS)

    assert result["status"] == "escalated"
    assert result["handoff"]["refund_amount"] is None


def test_handoff_rejects_empty_field():
    kwargs = dict(VALID_KWARGS)
    kwargs["conversation_summary"] = ""

    result = escalate_to_human(**kwargs)

    assert "error" in result
    assert "conversation_summary" in result["error"]


def test_handoff_rejects_placeholder_text():
    kwargs = dict(VALID_KWARGS)
    kwargs["root_cause_analysis"] = "TBD"

    result = escalate_to_human(**kwargs)

    assert "error" in result
    assert "root_cause_analysis" in result["error"]


def test_handoff_rejects_too_short_narrative_field():
    kwargs = dict(VALID_KWARGS)
    kwargs["recommended_action"] = "Refund"

    result = escalate_to_human(**kwargs)

    assert "error" in result
    assert "recommended_action" in result["error"]


def test_handoff_rejects_missing_customer_id():
    kwargs = dict(VALID_KWARGS)
    kwargs["customer_id"] = "   "

    result = escalate_to_human(**kwargs)

    assert "error" in result
    assert "customer_id" in result["error"]


def test_handoff_reports_every_invalid_field_at_once():
    result = escalate_to_human(
        customer_id="",
        conversation_summary="n/a",
        root_cause_analysis="short",
        recommended_action="Refund $34.50 for order ord_1002 after manual verification.",
    )

    assert "error" in result
    assert "customer_id" in result["error"]
    assert "conversation_summary" in result["error"]
    assert "root_cause_analysis" in result["error"]
    assert "recommended_action" not in result["error"]
