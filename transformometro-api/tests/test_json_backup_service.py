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


def test_detect_import_format_modern_when_instancias_present():
    bundle = _sample_bundle()
    bundle["processo_instancias"] = [
        {
            "instancia_id": "66666666-6666-6666-6666-666666666666",
            "processo_id": "11111111-1111-1111-1111-111111111111",
            "filial_id": "01",
            "todas_filiais_ativas": False,
            "deletado": False,
        }
    ]
    assert detect_import_format(bundle) == "modern"


def test_validate_modern_ignores_orphan_revisoes_on_deleted_process():
    pid = "fa809c58-5ca8-4765-870c-6b9610172a46"
    active_pid = "88888888-8888-8888-8888-888888888888"
    iid = "77777777-7777-7777-7777-777777777777"
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "filiais": [{"filial_id": "f1", "codigo_filial": "01", "nome_filial": "Matriz", "deletado": False}],
        "setores": [{"setor_id": "s1", "codigo_setor": "qualidade", "nome_setor": "Qualidade", "deletado": False}],
        "setor_filiais": [],
        "processos": [
            {
                "processo_id": pid,
                "codigo_processo": "PROC-0049",
                "nome_processo": "Deletado",
                "status_processo": "ativo",
                "deletado": True,
            },
            {
                "processo_id": active_pid,
                "codigo_processo": "PROC-0001",
                "nome_processo": "Ativo",
                "status_processo": "ativo",
                "deletado": False,
            },
        ],
        "processo_instancias": [
            {
                "instancia_id": iid,
                "processo_id": active_pid,
                "filial_id": "f1",
                "todas_filiais_ativas": False,
                "deletado": False,
            }
        ],
        "processo_instancia_setores": [],
        "recursos_compartilhados": [],
        "revisoes": [
            {
                "revisao_id": "750ae4b7-67b5-4bca-89fe-1a50b790d19a",
                "processo_id": pid,
                "versao_revisao": "v1",
                "instancia_id": None,
                "deletado": False,
            }
        ],
        "medicoes": [],
        "investimentos": [],
        "recurso_custos": [],
        "revisao_recursos_compartilhados": [],
    }
    assert detect_import_format(bundle) == "modern"
    errors = JsonBackupService(MagicMock()).validate_bundle(bundle)
    assert not any("instancia_id ausente" in err for err in errors)


def test_prepare_legacy_skips_processo_without_setor_id():
    bundle = _sample_bundle()
    bundle["processos"].append(
        {
            "processo_id": "99999999-9999-9999-9999-999999999999",
            "codigo_processo": "PROC-DEL",
            "nome_processo": "Sem setor",
            "filial_id": "01",
            "status_processo": "ativo",
            "deletado": True,
        }
    )
    JsonBackupService(MagicMock())._prepare_legacy_payload(bundle)
    assert len(bundle["processo_instancias"]) == 1


def test_insert_row_values_default_status_instancia_for_processo_instancias():
    from tm_app.infrastructure.persistence.json_backup_repository import ENTITY_SPECS

    spec = next(s for s in ENTITY_SPECS if s.bundle_key == "processo_instancias")
    row = {
        "instancia_id": "018e0c55-9b5e-48d5-9cfb-367741f527f9",
        "processo_id": "fc21dd6a-2a86-4e3e-b3cd-7279e662bc6f",
        "filial_id": "b30883bc-bc18-4598-81c9-3bc65a530897",
        "todas_filiais_ativas": False,
        "deletado": False,
    }
    normalized = JsonBackupService._normalize_row(spec, row)
    values = {col: normalized[col] for col in spec.columns if col in normalized}
    if "deletado" not in values:
        values["deletado"] = False
    assert values["status_instancia"] == "ativo"
    assert "created_at" not in values
    assert "updated_at" not in values


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
