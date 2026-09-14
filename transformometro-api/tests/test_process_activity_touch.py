from __future__ import annotations

from unittest.mock import patch

from tm_app.application.services.process_activity_touch import (
    resolve_processo_id_for_revisao,
    touch_processo_for_revisao,
    touch_processo_updated_at,
)


def test_touch_processo_updated_at_delegates_to_repository():
    with patch(
        "tm_app.application.services.process_activity_touch.ProcessoRepository"
    ) as proc_cls:
        proc_cls.return_value.touch_updated_at.return_value = True
        assert touch_processo_updated_at("proc-1") is True
    proc_cls.return_value.touch_updated_at.assert_called_once_with("proc-1")


def test_touch_processo_updated_at_blank_is_noop():
    with patch(
        "tm_app.application.services.process_activity_touch.ProcessoRepository"
    ) as proc_cls:
        assert touch_processo_updated_at("  ") is False
    proc_cls.assert_not_called()


def test_touch_processo_updated_at_swallows_errors():
    with patch(
        "tm_app.application.services.process_activity_touch.ProcessoRepository"
    ) as proc_cls:
        proc_cls.return_value.touch_updated_at.side_effect = RuntimeError("db down")
        assert touch_processo_updated_at("proc-1") is False


def test_resolve_and_touch_for_revisao_uses_explicit_processo_id():
    with patch(
        "tm_app.application.services.process_activity_touch.ProcessoRepository"
    ) as proc_cls:
        proc_cls.return_value.touch_updated_at.return_value = True
        pid = touch_processo_for_revisao("rev-1", processo_id="proc-explicit")
    assert pid == "proc-explicit"
    proc_cls.return_value.touch_updated_at.assert_called_once_with("proc-explicit")


def test_resolve_processo_id_for_revisao_looks_up_when_omitted():
    with patch(
        "tm_app.application.services.process_activity_touch.RevisaoRepository"
    ) as rev_cls:
        rev_cls.return_value.get.return_value = {"processo_id": "proc-from-rev"}
        assert resolve_processo_id_for_revisao("rev-1") == "proc-from-rev"
