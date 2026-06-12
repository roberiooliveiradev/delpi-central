from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.application.services.json_backup_service import (
    JsonBackupService,
    SCHEMA_VERSION,
    detect_import_format,
)
from tm_app.infrastructure.persistence.json_backup_repository import JsonBackupRepository


def _mock_service() -> JsonBackupService:
    return JsonBackupService(MagicMock())


def _sample_bundle() -> dict:
    pid = "11111111-1111-1111-1111-111111111111"
    rid = "22222222-2222-2222-2222-222222222222"
    rcid = "33333333-3333-3333-3333-333333333333"
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": "2026-01-01T00:00:00+00:00",
        "filiais": [],
        "setores": [
            {
                "setor_id": "eng",
                "nome_setor": "Engenharia",
                "status_setor": "ativo",
                "deletado": False,
            }
        ],
        "setor_filiais": [{"setor_id": "eng", "filial_id": "01"}],
        "processos": [
            {
                "processo_id": pid,
                "codigo_processo": "PROC-0001",
                "nome_processo": "Teste",
                "filial_id": "01",
                "setor_id": "eng",
                "status_processo": "ativo",
                "deletado": False,
            }
        ],
        "processo_instancias": [],
        "recursos_compartilhados": [],
        "revisoes": [
            {
                "revisao_id": rid,
                "processo_id": pid,
                "versao_revisao": "v1",
                "chave_unica_processo_revisao": f"{pid}|v1",
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2025-01-01",
                "revisao_ativa": False,
                "status_aprovacao": "aprovada",
                "deletado": False,
            }
        ],
        "medicoes": [],
        "investimentos": [],
        "recurso_custos": [],
        "revisao_recursos_compartilhados": [
            {
                "vinculo_id": "44444444-4444-4444-4444-444444444444",
                "revisao_id": rid,
                "recurso_compartilhado_id": rcid,
                "ativo": True,
                "deletado": False,
            }
        ],
    }


def _complete_legacy_bundle(bundle: dict) -> dict:
    bundle = dict(bundle)
    bundle["recursos_compartilhados"] = [
        {
            "recurso_compartilhado_id": "33333333-3333-3333-3333-333333333333",
            "codigo_recurso": "REC-01",
            "nome_recurso": "Servidor",
            "tipo_custo": "fixo",
            "recorrencia": "mensal",
            "valor_total_recorrente": 100,
            "criterio_rateio": "igualitario",
            "status_recurso": "ativo",
            "base_competencia": "mensal_cheio",
            "deletado": False,
        }
    ]
    JsonBackupService(MagicMock())._prepare_legacy_payload(bundle)
    return bundle


def test_detect_import_format_legacy():
    assert detect_import_format(_sample_bundle()) == "legacy"


def test_prepare_legacy_backfills_instancia_and_filiais():
    bundle = _complete_legacy_bundle(_sample_bundle())
    assert len(bundle["filiais"]) >= 1
    assert len(bundle["processo_instancias"]) == 1
    assert len(bundle["processo_instancia_setores"]) == 1
    assert bundle["revisoes"][0]["instancia_id"]


def test_validate_bundle_rejects_missing_fk():
    bundle = _sample_bundle()
    JsonBackupService(MagicMock())._prepare_legacy_payload(bundle)
    errors = _mock_service().validate_bundle(bundle)
    assert any("recursos_compartilhados" in err for err in errors)


def test_validate_bundle_accepts_consistent_fk():
    bundle = _complete_legacy_bundle(_sample_bundle())
    assert _mock_service().validate_bundle(bundle) == []


def test_validate_bundle_dedupes_repeated_fk_errors():
    bundle = _complete_legacy_bundle(_sample_bundle())
    bundle["recursos_compartilhados"] = []
    bundle["revisoes"].append(
        {
            "revisao_id": "55555555-5555-5555-5555-555555555555",
            "processo_id": "99999999-9999-9999-9999-999999999999",
            "instancia_id": bundle["processo_instancias"][0]["instancia_id"],
            "versao_revisao": "v2",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2025-02-01",
            "deletado": False,
        }
    )
    errors = _mock_service().validate_bundle(bundle)
    fk_errors = [e for e in errors if "processo_id" in e]
    assert len(fk_errors) == 1


def test_validate_bundle_rejects_setor_filiais_without_setor():
    bundle = _complete_legacy_bundle(_sample_bundle())
    bundle["setor_filiais"] = [{"setor_id": "inexistente", "filial_id": "01"}]
    errors = _mock_service().validate_bundle(bundle)
    assert any("setor_filiais" in err and "setores" in err for err in errors)


def test_ensure_bundle_includes_referenced_deleted_processo():
    pid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    rid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    repo = MagicMock()
    repo.fetch_rows_by_ids.return_value = [
        {
            "processo_id": pid,
            "codigo_processo": "PROC-DEL",
            "nome_processo": "Só referenciado",
            "filial_id": "01",
            "setor_id": "eng",
            "status_processo": "ativo",
            "deletado": True,
        }
    ]
    data = {
        "setores": [],
        "processos": [],
        "revisoes": [{"revisao_id": rid, "processo_id": pid, "versao_revisao": "v1"}],
        "medicoes": [],
        "investimentos": [],
        "recursos_compartilhados": [],
        "recurso_custos": [],
        "revisao_recursos_compartilhados": [],
    }
    enriched = JsonBackupRepository.ensure_bundle_parent_rows(repo, data)
    assert len(enriched["processos"]) == 1
    assert enriched["processos"][0]["processo_id"] == pid
    processo_calls = [
        call
        for call in repo.fetch_rows_by_ids.call_args_list
        if call.args[0].bundle_key == "processos"
    ]
    assert len(processo_calls) == 1


def test_preview_merge_counts_insert_and_update():
    bundle = _sample_bundle()
    bundle["recursos_compartilhados"] = [
        {
            "recurso_compartilhado_id": "33333333-3333-3333-3333-333333333333",
            "codigo_recurso": "REC-01",
            "nome_recurso": "Servidor",
            "tipo_custo": "fixo",
            "recorrencia": "mensal",
            "valor_total_recorrente": 100,
            "criterio_rateio": "igualitario",
            "status_recurso": "ativo",
            "base_competencia": "mensal_cheio",
            "deletado": False,
        }
    ]

    repo = MagicMock()
    repo.fetch_existing_ids.side_effect = lambda spec: (
        {"11111111-1111-1111-1111-111111111111"} if spec.bundle_key == "processos" else set()
    )
    repo.fetch_filiais.return_value = []
    repo.fetch_setor_filiais.return_value = [{"setor_id": "eng", "filial_id": "01"}]
    repo.load_export_bundle.return_value = MagicMock(
        processos=[{}],
        processo_instancias=[],
        revisoes=[],
        medicoes=[],
        investimentos=[],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )

    preview = JsonBackupService(repo).preview(bundle, "merge", "legacy")
    assert preview["valid"] is True
    assert preview["resolved_format"] == "legacy"
    assert preview["legacy_transformed"] is True
    assert preview["entities"]["processos"]["update"] == 1
    assert preview["entities"]["processos"]["insert"] == 0
    assert preview["entities"]["revisoes"]["insert"] == 1
    assert preview["entities"]["setor_filiais"]["total"] == 1
