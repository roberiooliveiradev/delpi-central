from app.domain.services.llm_tool_argument_parser import parse_llm_tool_arguments


def test_parse_json_string_arguments():
    assert parse_llm_tool_arguments('{"query":"pedidos"}') == {"query": "pedidos"}


def test_parse_dict_arguments():
    assert parse_llm_tool_arguments({"limit": 3}) == {"limit": 3}
