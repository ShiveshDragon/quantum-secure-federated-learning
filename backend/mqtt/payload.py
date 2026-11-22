import json


def serialize_message(message: dict) -> str:
    return json.dumps(message, sort_keys=True, separators=(",", ":"))


def deserialize_message(payload: str) -> dict:
    return json.loads(payload)


def update_topic(client_id: str) -> str:
    return f"iot/fl/{client_id}/update"


def global_model_topic() -> str:
    return "iot/fl/global_model"


def key_status_topic(client_id: str) -> str:
    return f"iot/qkd/{client_id}/key_status"
