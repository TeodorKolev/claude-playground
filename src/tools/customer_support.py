CUSTOMERS = [
    {
        "customer_id": "cust_001",
        "name": "Alice Chen",
        "email": "alice@example.com",
        "verified": True,
    },
    {
        "customer_id": "cust_002",
        "name": "Bob Diaz",
        "email": "bob@example.com",
        "verified": False,
    },
]

ORDERS = {
    "ord_1001": {
        "order_id": "ord_1001",
        "customer_id": "cust_001",
        "item": "Wireless Headphones",
        "amount": 79.99,
        "status": "delivered",
    },
    "ord_1002": {
        "order_id": "ord_1002",
        "customer_id": "cust_002",
        "item": "Desk Lamp",
        "amount": 34.50,
        "status": "delivered",
    },
}


class SessionState:
    """Tracks which customer IDs get_customer has verified this session.

    One instance must be created per agent session (e.g. per `run()` call)
    and never reused across sessions: reuse would let verification from one
    conversation authorize a refund in another.
    """

    def __init__(self):
        self._verified_customer_ids: set[str] = set()

    def record_customer(self, customer: dict) -> None:
        if customer.get("verified") and customer.get("customer_id"):
            self._verified_customer_ids.add(customer["customer_id"])

    def is_verified(self, customer_id: str) -> bool:
        return customer_id in self._verified_customer_ids


def get_customer(query: str) -> dict:
    needle = query.strip().lower()
    for customer in CUSTOMERS:
        if needle in (customer["name"].lower(), customer["email"].lower()):
            return {
                "customer_id": customer["customer_id"],
                "name": customer["name"],
                "email": customer["email"],
                "verified": customer["verified"],
            }
    return {"error": f"No customer found matching {query!r}"}


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return {"error": f"No order found with ID {order_id!r}"}
    return dict(order)


def process_refund(customer_id: str, amount: float, session: SessionState) -> dict:
    # Prerequisite gate enforced here, in code, rather than by trusting the
    # model to have called get_customer first: prompt instructions alone
    # are not 100% reliable, and a refund is not the place for that gap.
    if not session.is_verified(customer_id):
        return {
            "error": (
                "BLOCKED: Cannot process refund. Customer identity not "
                "verified. Call get_customer first."
            )
        }
    return {
        "status": "refunded",
        "customer_id": customer_id,
        "amount": amount,
    }


_PLACEHOLDERS = {"n/a", "na", "tbd", "unknown", "none", "placeholder", "todo", "..."}
_MIN_NARRATIVE_LENGTH = 15


def _blank_or_placeholder(value: str) -> bool:
    normalized = value.strip().strip(".").lower()
    return not normalized or normalized in _PLACEHOLDERS


def escalate_to_human(
    customer_id: str,
    conversation_summary: str,
    root_cause_analysis: str,
    recommended_action: str,
    refund_amount: float | None = None,
) -> dict:
    # A human agent picking this up has no access to the conversation
    # transcript - this handoff is the only context they get. Enforced in
    # code rather than left to the model, same reasoning as the refund gate:
    # an empty or placeholder field here just forces the customer to repeat
    # themselves to a second agent.
    narrative_fields = {
        "conversation_summary": conversation_summary,
        "root_cause_analysis": root_cause_analysis,
        "recommended_action": recommended_action,
    }

    invalid = []
    if _blank_or_placeholder(customer_id):
        invalid.append("customer_id")
    for name, value in narrative_fields.items():
        if _blank_or_placeholder(value) or len(value.strip()) < _MIN_NARRATIVE_LENGTH:
            invalid.append(name)

    if invalid:
        return {
            "error": (
                "BLOCKED: Handoff rejected, incomplete or placeholder "
                f"field(s): {', '.join(invalid)}. A human agent will not "
                "see this conversation - every field must be fully "
                "populated before escalating."
            )
        }

    return {
        "status": "escalated",
        "handoff": {
            "customer_id": customer_id,
            "conversation_summary": conversation_summary,
            "root_cause_analysis": root_cause_analysis,
            "refund_amount": refund_amount,
            "recommended_action": recommended_action,
        },
    }
