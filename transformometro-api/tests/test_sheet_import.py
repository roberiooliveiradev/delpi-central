from tm_app.application.services.sheet_import_service import SheetImportService
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.persistence.import_persistence import normalize_raw_rows


def _minimal_raw() -> TransformometroRawData:
    return TransformometroRawData(
        processos=[
            {
                "processo_id": "11111111-1111-1111-1111-111111111111",
                "codigo_processo": "PROC-0001",
                "nome_processo": "Processo teste",
                "filial_id": "01",
                "setor_id": "engenharia",
                "status_processo": "ativo",
            }
        ],
        revisoes=[
            {
                "revisao_id": "22222222-2222-2222-2222-222222222222",
                "processo_id": "11111111-1111-1111-1111-111111111111",
                "versao_revisao": "1.0.0",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": "TRUE",
            }
        ],
        medicoes=[
            {
                "revisao_id": "22222222-2222-2222-2222-222222222222",
                "volume_mensal": "100",
                "tempo_medio_execucao_min": "30",
                "custo_hora_mao_obra": "50",
            }
        ],
        investimentos=[],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
    )


def test_normalize_raw_assigns_uuids_and_dates():
    raw = normalize_raw_rows(_minimal_raw())
    assert raw.processos[0]["filial_id"] == "01"
    assert raw.revisoes[0]["data_inicio_vigencia"] == "2025-01-01"
    assert raw.revisoes[0]["revisao_ativa"] is True
    assert raw.medicoes[0]["volume_mensal"] == 100.0


def test_validate_ok_for_minimal_fixture():
    raw = normalize_raw_rows(_minimal_raw())
    validation = SheetImportService().validate(raw)
    assert validation.ok is True
    assert validation.sheet_counts["processos"] == 1


def test_validate_fails_on_orphan_revisao():
    raw = normalize_raw_rows(_minimal_raw())
    raw.revisoes[0]["processo_id"] = "99999999-9999-9999-9999-999999999999"
    validation = SheetImportService().validate(raw)
    assert validation.ok is False
    assert any("processo_id" in err for err in validation.errors)
