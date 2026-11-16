"""EVA guided line-balancing — capability-level eval matrix (EV-S##).

Doc 125 §3: cada cenário executa a sequência de tool calls que o método
guiado (`knowledge(routing.guided_analysis)`) prescreve, validando o que
o BACKEND garante — dedup, estágios, honestidade de estado, rótulos e
eco de parâmetros para comparação de cenários.

A condução multi-turn (escolha de perguntas, prosa) pertence ao
consumidor ChatGPT e é avaliada pelo owner — Doc 125 §7 (OWNER_RUN).
Nenhum resultado aqui simula uma conversa real.
"""

import asyncio
from types import SimpleNamespace

import pytest

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from engineering_app.interface.mcp import tool_bridge as bridge
from engineering_app.interface.mcp import semantic_bridge as sem


def _human_user(permissions=("engineering.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    yield
    clear_current_user()
    clear_request_authorization()


def _op(product, level, code, desc, ct, res, minutes, setup=0.0, comp=None):
    return {
        "branch": "02",
        "route_code": "01",
        "product_code": product,
        "operation_code": code,
        "operation_description": desc,
        "resource_code": res,
        "work_center": ct,
        "setup_hours": setup,
        "standard_time_hour_mil": minutes * 60,
        "standard_time_hours_piece": minutes / 60,
        "standard_time_minutes_piece": minutes,
        "operation_type": "1",
        "mandatory_operation": "S",
        "mandatory_sequence": "S",
        "mandatory_report": "N",
        "component_code": comp,
        "component_description": f"COMP {comp}" if comp else None,
        "component_sequence": "010" if comp else None,
        "bom_level": level,
    }


def _eval_guide():
    """Payload real-like: 6 linhas → 3 operações únicas em 3 estágios.

    Espelha o produto 90264302 (Doc 122): raiz nível 0 e dois
    componentes nível 1 — cada operação repetida por linha de
    componente do payload.
    """
    items = [
        _op("P9000", 0, "01", "INSPECIONAR", "CT-99", "CT-99", 1.2, comp="A5001"),
        _op("P9000", 0, "01", "INSPECIONAR", "CT-99", "CT-99", 1.2, comp="B5002"),
        _op("A5001", 1, "01", "CORTAR", "CT-01", "LASER", 0.5, comp="M100"),
        _op("A5001", 1, "01", "CORTAR", "CT-01", "LASER", 0.5, comp="M200"),
        _op("B5002", 1, "01", "CORTAR", "CT-01", "LASER", 0.5, comp="M100"),
        _op("B5002", 1, "01", "CORTAR", "CT-01", "LASER", 0.5, comp="M300"),
    ]
    return {"status": "available", "data": {"items": items, "total": 6}}


class _GuideAux:
    def __init__(self, result=None):
        self.result = result if result is not None else _eval_guide()
        self.calls = []

    async def fetch_product_guide(self, ctx, **kw):
        self.calls.append(kw)
        return self.result


def _patch_aux(monkeypatch, aux):
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: aux
    )


def _analyze(**params):
    return asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance", parameters=params
        )
    )


# --- EV-S01/S02: roteiro oficial + análise calculada ------------------------


def test_ev_s01_routing_steps_official_data(monkeypatch):
    """Solicitação genérica: o roteiro vem da fonte oficial — nada é
    perguntado ao usuário que o read já responde."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="P9000")
    )
    assert not result.is_error
    items = result.structured_content["data"]["data"]["items"]
    assert len(items) == 6  # linhas oficiais brutas, sem fabricação


def test_ev_s02_valid_routing_calculated(monkeypatch):
    """Roteiro válido + parâmetros completos → CALCULATED com takt."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(
        product_code="P9000", demand=500, available_minutes=420
    )
    assert not r.is_error
    data = r.structured_content["data"]
    assert data["data_class"] == "CALCULATED"
    stage0 = next(
        s for s in data["stages"] if s["product_code"] == "P9000"
    )
    assert stage0["takt_minutes"] == 0.84  # 420/500
    assert stage0["work_content_minutes"] == 1.2  # dedup: 1 op, não 2


# --- EV-S03/S04: ausência e incompletude honestas ---------------------------


def test_ev_s03_product_without_routing_honest_empty(monkeypatch):
    """Produto sem roteiro → PARTIAL/empty explícito, nunca fabricado."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux({"status": "available", "data": {"items": [], "total": 0}}))
    r = _analyze(product_code="EMPTY1", demand=500, available_minutes=420)
    assert not r.is_error
    data = r.structured_content["data"]
    assert data["stages"] == []
    assert any("vazio" in l.lower() for l in data["limitations"])


def test_ev_s04_incomplete_data_partial(monkeypatch):
    """Dados incompletos → PARTIAL + missing_parameters explícitos."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(product_code="P9000")
    assert not r.is_error
    data = r.structured_content["data"]
    assert data["data_class"] == "PARTIAL"
    assert set(data["missing_parameters"]) >= {
        "demand",
        "available_minutes",
    }
    # Eco de parâmetros rotulado — UNKNOWN para ausentes.
    assert data["parameters"]["demand"]["data_class"] == "UNKNOWN"


# --- EV-S05/S06/S13: takt, mudança de parâmetro e comparação ----------------


def test_ev_s06_parameter_change_preserves_and_recomputes(monkeypatch):
    """'Agora considere 700 peças': duas análises independentes, eco de
    parâmetros distinto — o consumidor atribui cada resultado ao seu
    cenário sem confusão."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r500 = _analyze(
        product_code="P9000", demand=500, available_minutes=420
    )
    r700 = _analyze(
        product_code="P9000", demand=700, available_minutes=420
    )
    d500 = r500.structured_content["data"]
    d700 = r700.structured_content["data"]
    assert d500["parameters"]["demand"]["value"] == 500
    assert d700["parameters"]["demand"]["value"] == 700
    for d in (d500, d700):
        assert d["parameters"]["available_minutes"]["value"] == 420
        assert d["parameters"]["demand"]["data_class"] == "PROVIDED"
    s500 = d500["stages"][0]["takt_minutes"]
    s700 = d700["stages"][0]["takt_minutes"]
    assert s500 == 0.84 and s700 == 0.6  # 420/500 vs 420/700
    assert s500 != s700  # cenários distinguíveis


def test_ev_s07_branch_change_filter_echo(monkeypatch):
    """Alteração de filial: filtro propagado à fonte e ecoado."""
    _set_context(_human_user())
    aux = _GuideAux()
    _patch_aux(monkeypatch, aux)
    _analyze(
        product_code="P9000",
        demand=500,
        available_minutes=420,
        branch="01",
    )
    assert aux.calls[-1]["branch"] == "01"


# --- EV-S08/S09: dedup e estágios BOM ----------------------------------------


def test_ev_s08_s09_stages_and_component_dedup(monkeypatch):
    """Níveis de BOM separados + linhas duplicadas por componente não
    somam: 6 linhas → 3 ops únicas em 3 estágios."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(product_code="P9000", demand=500, available_minutes=420)
    data = r.structured_content["data"]
    assert data["official_rows"] == 6
    assert data["unique_operations"] == 3
    assert len(data["stages"]) == 3
    keys = {(s["product_code"], s["bom_level"]) for s in data["stages"]}
    assert keys == {("P9000", 0), ("A5001", 1), ("B5002", 1)}
    # Estágio por componente: conteúdo = 0.5 (não 1.0 por 2 linhas).
    a = next(s for s in data["stages"] if s["product_code"] == "A5001")
    assert a["work_content_minutes"] == 0.5


# --- EV-S10/S11: gargalo e num_stations --------------------------------------


def test_ev_s10_bottleneck_above_takt(monkeypatch):
    """Demanda apertada → operação acima do takt identificada."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(product_code="P9000", demand=500, available_minutes=420)
    s0 = next(
        s
        for s in r.structured_content["data"]["stages"]
        if s["product_code"] == "P9000"
    )
    # takt 0.84 < op 1.2 min → acima do takt, gargalo candidato.
    assert s0["bottleneck_candidate"]["operation_code"] == "01"
    assert s0["over_takt_operations"][0]["minutes_piece"] == 1.2
    assert s0["theoretical_min_stations"] == 2  # ceil(1.2/0.84)


def test_ev_s11_station_feasibility_check(monkeypatch):
    """Redução de postos: num_stations informado → check de viabilidade,
    nunca garantia sem evidência."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(
        product_code="P9000",
        demand=500,
        available_minutes=420,
        num_stations=2,
    )
    s0 = next(
        s
        for s in r.structured_content["data"]["stages"]
        if s["product_code"] == "P9000"
    )
    check = s0["station_check"]
    assert check["num_stations"] == 2
    assert check["required_cycle_minutes"] == 0.6
    assert check["feasible"] is True


# --- EV-S12/S14: limitações e deflexão de escrita ----------------------------


def test_ev_s12_equipment_restriction_outside_vocabulary(monkeypatch):
    """Restrição de equipamento não é campo do contrato — rejeitado com
    allowed_fields (a condução conversacional registra como limitação,
    não como parâmetro inventado)."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux())
    r = _analyze(
        product_code="P9000",
        demand=500,
        available_minutes=420,
        locked_work_center="CT-99",
    )
    assert r.is_error
    assert r.structured_content["error_code"] == "validation"
    assert "allowed_fields" in r.structured_content["data"]


def test_ev_s14_routing_write_rejected():
    """'Atualize o roteiro' → não existe capability de escrita routing.*
    — vocabulário fechado rejeita, proposta vai à Engenharia."""
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_execute(
            entity="routing",
            action="update",
            target_ref="P9000",
            payload={"operations": []},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] in {
        "not_implemented",
        "validation",
        "not_found",
    }


# --- EV-S15/S16: autorização e upstream ---------------------------------------


def test_ev_s15_service_principal_rejected():
    """Sem principal humano → fail-closed, independente do conteúdo."""
    _set_context(
        _human_user(principal_type="service", permissions=("engineering.access",))
    )
    r = _analyze(product_code="P9000", demand=500, available_minutes=420)
    assert r.is_error
    assert r.structured_content["status_code"] in {401, 403}


def test_ev_s16_upstream_unavailable_honest(monkeypatch):
    """Fonte indisponível → 502/unavailable, nunca 'sem roteiro'."""
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux({"status": "unavailable"}))
    r = _analyze(product_code="P9000", demand=500, available_minutes=420)
    assert r.is_error
    assert r.structured_content["status_code"] == 502


def test_ev_s16b_forbidden_maps_403(monkeypatch):
    _set_context(_human_user())
    _patch_aux(monkeypatch, _GuideAux({"status": "forbidden"}))
    r = _analyze(product_code="P9000", demand=500, available_minutes=420)
    assert r.is_error
    assert r.structured_content["status_code"] == 403
