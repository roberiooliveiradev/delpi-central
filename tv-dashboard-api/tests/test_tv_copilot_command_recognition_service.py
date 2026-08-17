"""Reconhecimento de comando do editor — tolerância a acento e digitação."""

from __future__ import annotations

from tv_app.application.services.data.tv_copilot_command_planner_service import (
    TvCopilotCommandPlannerService,
)
from tv_app.application.services.data.tv_copilot_command_recognition_service import (
    TvCopilotCommandRecognitionService as Recognition,
)
from tv_app.application.services.data.tv_copilot_content_service import (
    clear_tv_copilot_content_cache,
)


def setup_function() -> None:
    clear_tv_copilot_content_cache()


def test_marker_hit_exato_e_sem_acento():
    assert Recognition.marker_hit("crie um slide", "crie um slide agora")
    assert Recognition.marker_hit("crie uma programação", "crie uma programacao nova")


def test_marker_hit_tolera_erro_de_digitacao():
    assert Recognition.marker_hit("crie um slide", "crie um sldie")
    assert Recognition.marker_hit("apagar slide", "apagar sldie")


def test_marker_hit_nao_casa_objeto_diferente():
    assert not Recognition.marker_hit("crie um slide", "crie um gráfico de OEE")
    assert not Recognition.marker_hit("apagar slide", "qual o oee de hoje")


def test_token_curto_exige_igualdade():
    # «um» não pode casar com «em» só por proximidade.
    assert not Recognition.marker_hit("crie um slide", "crie em slide")


def test_is_editor_command_separa_comando_de_pergunta():
    assert Recognition.is_editor_command("crie um slide")
    assert Recognition.is_editor_command("crie um sldie")
    assert Recognition.is_editor_command("adicione um KPI de OEE")
    assert not Recognition.is_editor_command("quem é você")
    assert not Recognition.is_editor_command("qual o OEE de ontem")


def test_planner_com_typo_produz_plano_pronto():
    plan = TvCopilotCommandPlannerService.plan(
        message="crie um sldie",
        host_context={"playlistId": "pl-1"},
    )
    assert plan["status"] == "ready"
    assert plan["ops"]
    assert plan["confirmationPolicy"] == "direct"


def test_planner_marca_pergunta_como_not_command():
    plan = TvCopilotCommandPlannerService.plan(
        message="quem é você",
        host_context={"playlistId": "pl-1"},
    )
    assert plan["status"] == "not_command"
    assert plan["ops"] == []
    assert plan["reason"] == ""


def test_planner_marca_comando_sem_capability_como_unsupported():
    plan = TvCopilotCommandPlannerService.plan(
        message="exporte o slide para powerpoint",
        host_context={"playlistId": "pl-1"},
    )
    assert plan["status"] == "unsupported"
    assert plan["reason"]
