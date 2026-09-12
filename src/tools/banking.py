def aml_check(account_id: str) -> dict:
    return {"account_id": account_id, "status": "pass"}


def transfer_funds(account_id: str, destination: str, amount: float) -> dict:
    return {
        "status": "transferred",
        "account_id": account_id,
        "destination": destination,
        "amount": amount,
    }
