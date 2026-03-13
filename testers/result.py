def make_result(resource: str, identifier: str) -> dict:
    return {
        "resource": resource,
        "identifier": identifier,
        "status": "FAIL",
        "details": None,
        "error": None,
    }