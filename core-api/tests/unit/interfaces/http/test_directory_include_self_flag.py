from app.interfaces.http.me_controller import _truthy_query_flag


def test_truthy_query_flag_accepts_common_values() -> None:
    assert _truthy_query_flag("true") is True
    assert _truthy_query_flag("1") is True
    assert _truthy_query_flag("YES") is True
    assert _truthy_query_flag("on") is True


def test_truthy_query_flag_rejects_missing_or_false() -> None:
    assert _truthy_query_flag(None) is False
    assert _truthy_query_flag("") is False
    assert _truthy_query_flag("false") is False
    assert _truthy_query_flag("0") is False
