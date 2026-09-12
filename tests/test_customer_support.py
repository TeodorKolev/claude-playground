from tools.customer_support import SessionState, get_customer, process_refund


def test_refund_blocked_without_any_verification():
    session = SessionState()

    result = process_refund("cust_001", 79.99, session)

    assert "error" in result
    assert "BLOCKED" in result["error"]


def test_refund_blocked_for_unverified_customer():
    session = SessionState()
    session.record_customer(get_customer("bob@example.com"))  # verified=False

    result = process_refund("cust_002", 34.50, session)

    assert "error" in result


def test_refund_allowed_after_verification():
    session = SessionState()
    session.record_customer(get_customer("alice@example.com"))  # verified=True

    result = process_refund("cust_001", 79.99, session)

    assert result == {"status": "refunded", "customer_id": "cust_001", "amount": 79.99}


def test_verifying_one_customer_does_not_unlock_another():
    session = SessionState()
    session.record_customer(get_customer("alice@example.com"))  # verifies cust_001

    result = process_refund("cust_002", 34.50, session)

    assert "error" in result


def test_verification_does_not_leak_across_sessions():
    session_a = SessionState()
    session_a.record_customer(get_customer("alice@example.com"))

    session_b = SessionState()

    result = process_refund("cust_001", 79.99, session_b)

    assert "error" in result
