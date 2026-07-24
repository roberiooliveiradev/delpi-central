# Playbook — cobertura de testes em 100% das rotas (transformometro-api)

**Status:** concluído (jul/2026) — `gap=0`, `--check-complete` verde  
**Baseline:** [`tm_app/content/openapi_baseline.json`](../../tm_app/content/openapi_baseline.json) (~123 ops)  
**Inventário:** [`tm_app/content/route_test_coverage.json`](../../tm_app/content/route_test_coverage.json)  
**Gate:** `python scripts/audit_route_test_coverage.py`  
**CI:** [`.github/workflows/transformometro-api-routes.yml`](../../../.github/workflows/transformometro-api-routes.yml)

| Métrica | Valor |
|---------|-------|
| Operações | 123 |
| Covered | 123 |
| Gap | 0 |
| Exempt | 0 (WebSocket fora do baseline HTTP) |

## Objetivo

Toda operação HTTP do OpenAPI (`method` + `path` + `operationId`) tem cobertura **HTTP de contrato** rastreável. Lógica de negócio continua em testes de domínio/repositório; este playbook fecha o gap da **camada de rota**.

| Nível | Obrigatório para “100%”? | O que cobre |
|-------|--------------------------|-------------|
| **A — envelope smoke** | Sim | `success: true` no envelope `{success,message,data}` (ou health/binário documentado) |
| **B — Query fechado** | Não nesta entrega | 422 amostral (TM tem poucos enums Query tipados) |
| **C — comportamento** | Não bloqueia gate | RBAC filial, upload real em disco |
| **D — gate CI** | Sim | baseline sync + inventário + `--check-complete` |

**Contrato:** a TM **não** usa `meta.operationId` no envelope (diferente da api-delpi). O scanner de cobertura exige o `operationId` como substring em `tests/**/*.py`.

## Manutenção (rota nova ou alterada)

1. Declarar `operation_id=` estável no decorator FastAPI (igual ao nome da função).
2. Smoke Nível A (arquivo de fase ou harness) com o `operationId` literal.
3. Regenerar e validar:

```bash
cd transformometro-api
PYTHONPATH=.:../shared python scripts/sync_openapi_baseline.py --write
PYTHONPATH=.:../shared python -m pytest tests/test_route_phase*.py tests/test_route_phase0*.py -q
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --write
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --check
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --check-complete
```

## Estratégia canônica

```text
openapi_baseline → operationId
→ TestClient (create_test_app sem lifespan) + JWT fake + patch Repository/Service
→ assert envelope success (ou health/binário)
```

Helpers:

- [`tests/support/test_app.py`](../../tests/support/test_app.py) — app sem migrations
- [`tests/support/route_envelope_smoke.py`](../../tests/support/route_envelope_smoke.py)
- [`tests/support/route_smoke_mocks.py`](../../tests/support/route_smoke_mocks.py)
- [`tests/support/route_smoke_runner.py`](../../tests/support/route_smoke_runner.py)

### Inventário — status

| status | Significado |
|--------|-------------|
| `covered` | `operationId` aparece em `tests/**/*.py` |
| `gap` | sem menção em testes |
| `exempt` | isento documentado (`exemptReason`) — ex.: WebSocket |

### Gate

```bash
cd transformometro-api
PYTHONPATH=.:../shared python scripts/sync_openapi_baseline.py --check
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --report
PYTHONPATH=.:../shared python scripts/audit_route_test_coverage.py --check-complete
```

## Fases

| Fase | Escopo | Arquivo |
|------|--------|---------|
| **0** | harness + health/options/`list_processos` | `test_route_phase0_harness_smoke.py` |
| **1** | CRUD (catálogos, processo, revisão, medição, …) | `test_route_phase1_crud_smoke.py` |
| **2** | dashboard + integrations | `test_route_phase2_dashboard_smoke.py` |
| **3** | diagrama + decomposição | `test_route_phase3_diagram_decomposition_smoke.py` |
| **4** | evidência, arquivos, backup, colaboração | `test_route_phase4_files_backup_collab_smoke.py` |
| **5** | CI `gap=0` | `.github/workflows/transformometro-api-routes.yml` |

## O que não fazer

- Contar só teste de repositório/domínio como “rota coberta” no gate
- Introduzir `meta` no envelope só para o inventário (breaking no MFE)
- Exceção permanente sem `exempt` + `exemptReason`
- Entregar rota nova sem `operation_id=` + smoke + `--write` no inventário

## Checklist rota nova

1. `operation_id=` no decorator
2. Smoke Nível A (literal do oid no arquivo de teste)
3. `sync_openapi_baseline.py --write`
4. `audit_route_test_coverage.py --write && --check` (+ `--check-complete`)
