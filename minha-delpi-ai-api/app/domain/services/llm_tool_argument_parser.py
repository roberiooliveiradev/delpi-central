import json


def parse_llm_tool_arguments(raw) -> dict:
    if isinstance(raw, dict):
        return raw

    if not raw:
        return {}

    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}
