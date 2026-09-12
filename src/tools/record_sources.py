# Three backend systems, three date conventions, three status conventions.
# Deliberately inconsistent: without a normalization step, an agent calling
# more than one of these in the same turn has to reconcile epoch seconds,
# ISO 8601 strings, and DD/MM/YYYY strings, plus numeric/English/single-char
# status codes, on its own.


def get_customer_record(customer_id: str) -> dict:
    return {"customer_id": customer_id or "C-001", "created_at": 1710489600, "status": 200}


def get_order_record(order_id: str) -> dict:
    return {
        "order_id": order_id or "ORD-42",
        "created_at": "2024-03-15T12:00:00Z",
        "status": "active",
    }


def get_shipment_record(shipment_id: str) -> dict:
    return {
        "shipment_id": shipment_id or "SHP-7",
        "created_at": "15/03/2024",
        "status": "S",
    }
