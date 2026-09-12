import re

from tools.record_sources import get_customer_record, get_order_record, get_shipment_record


def test_customer_record_uses_epoch_seconds_and_numeric_status():
    record = get_customer_record("C-001")

    assert isinstance(record["created_at"], int)
    assert isinstance(record["status"], int)


def test_order_record_uses_iso_8601_and_string_status():
    record = get_order_record("ORD-42")

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", record["created_at"])
    assert isinstance(record["status"], str) and len(record["status"]) > 1


def test_shipment_record_uses_ddmmyyyy_and_single_char_status():
    record = get_shipment_record("SHP-7")

    assert re.fullmatch(r"\d{2}/\d{2}/\d{4}", record["created_at"])
    assert isinstance(record["status"], str) and len(record["status"]) == 1


def test_all_three_tools_disagree_on_date_and_status_format():
    customer = get_customer_record("C-001")
    order = get_order_record("ORD-42")
    shipment = get_shipment_record("SHP-7")

    # Same underlying moment/state, three incompatible representations -
    # the "chaos" this agent exists to demonstrate.
    assert isinstance(customer["created_at"], int)
    assert isinstance(order["created_at"], str) and "T" in order["created_at"]
    assert isinstance(shipment["created_at"], str) and "/" in shipment["created_at"]

    assert isinstance(customer["status"], int)
    assert customer["status"] != order["status"] != shipment["status"]
