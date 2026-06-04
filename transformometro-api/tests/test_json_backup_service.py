from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.application.services.json_backup_service import JsonBackupService, SCHEMA_VERSION
from tm_app.infrastructure.persistence.json_backup_repository import JsonBackupRepository


def _sample_bundle() -> dict:
    pid = "11111111-1111-1111-1111-111111111111"
    rid = "22222222-2222-2222-2222-222222222222"
    rcid = "33333333-3333-3333-3333-333333333333"
    return {
        "schema_version": SCHEMA_VERSION,
        "exported_at": "2026-01-01T00:00:00+00:00",
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


def test_validate_bundle_rejects_missing_fk():
    errors = JsonBackupService().validate_bundle(_sample_bundle())
    assert any("recursos_compartilhados" in err for err in errors)


def test_validate_bundle_accepts_consistent_fk():
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
    assert JsonBackupService().validate_bundle(bundle) == []


def test_validate_bundle_dedupes_repeated_fk_errors():
    bundle = _sample_bundle()
    bundle["recursos_compartilhados"] = []
    bundle["revisoes"].append(
        {
            "revisao_id": "55555555-5555-5555-5555-555555555555",
            "processo_id": "99999999-9999-9999-9999-999999999999",
            "versao_revisao": "v2",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2025-02-01",
            "deletado": False,
        }
    )
    errors = JsonBackupService().validate_bundle(bundle)
    fk_errors = [e for e in errors if "processo_id" in e]
    assert len(fk_errors) == 1


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
    repo.fetch_rows_by_ids.assert_called_once()


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
    repo.load_export_bundle.return_value = MagicMock(
        processos=[{}],
        revisoes=[],
        medicoes=[],
        investimentos=[],
        recursos_compartilhados=[],
        revisao_recursos_compartilhados=[],
        recurso_custos=[],
    )

    preview = JsonBackupService(repo).preview(bundle, "merge")
    assert preview["valid"] is True
    assert preview["entities"]["processos"]["update"] == 1
    assert preview["entities"]["processos"]["insert"] == 0
    assert preview["entities"]["revisoes"]["insert"] == 1
