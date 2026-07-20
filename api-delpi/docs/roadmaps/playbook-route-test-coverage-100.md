# Playbook — cobertura de testes em 100% das rotas (api-delpi)

**Status:** concluído (jul/2026) — `gap=0`, `--check-complete` verde  
**Baseline:** ~368 operações OpenAPI (`app/content/openapi_baseline.json`)  
**Inventário:** [`app/content/route_test_coverage.json`](../../app/content/route_test_coverage.json)  
**Gate:** `python scripts/audit_route_test_coverage.py`

| Métrica | Valor |
|---------|-------|
| Operações | 368 |
| Covered | 367 |
| Gap | 0 |
| Exempt | 1 (`get_health` — JSON legado sem envelope) |

## Objetivo

Toda operação do OpenAPI (`method` + `path` + `operationId`) tem cobertura **HTTP de contrato** rastreável. Lógica de negócio continua em testes de use case/SQL; este playbook fecha o gap da **camada de rota**.

| Nível | Obrigatório para “100%”? | O que cobre |
|-------|--------------------------|-------------|
| **A — meta smoke** | Sim | `success`, `meta.operationId` / `entity` / `shape` (via `ROUTE_CONTRACTS`) |
| **B — Query fechado** | Sim (quando houver `enum`/`pattern`) | valor inválido → **422** |
| **C — comportamento** | Só rotas críticas | RBAC filial, upload, mutações, PDF |
| **D — gate CI** | Sim | inventário sincronizado + `--check-complete` |

## Manutenção (rota nova ou alterada)

1. Smoke Nível A (ou inclusão no harness parametrizado) com o `operationId` literal no arquivo de teste.
2. Preferir **TestClient** ou chamada ao handler com **kwargs explícitos** (default `Query()` = `FieldInfo`).
3. Helpers: [`tests/support/route_contract_smoke.py`](../../tests/support/route_contract_smoke.py).
4. Regenerar e validar:

```bash
cd api-delpi
python scripts/audit_route_test_coverage.py --write
python scripts/audit_route_test_coverage.py --check
python scripts/audit_route_test_coverage.py --check-complete
```

5. Se Query de domínio fechado: caso Nível B (422) — factories em `query_param_enums.py` usam `enum=` **e** `pattern=` (só `enum` não valida em runtime no FastAPI).

## Estratégia canônica

### Harness Nível A

```text
openapi_baseline → operationId → RouteContract
→ TestClient (router isolado) + auth mock + patch composer/use case
→ assert envelope meta
```

- Fixture mínima por `shape`: `scalar`, `paged_list`, `playbook_report`, `hierarchy`, …
- Binário (PDF/PNG/`FileResponse`): assert resposta + **string literal** do `operationId` no arquivo (o scanner é por substring).

### Inventário — status

| status | Significado |
|--------|-------------|
| `covered` | `operationId` aparece em `tests/**/*.py` |
| `gap` | sem menção em testes |
| `exempt` | isento documentado (`exemptReason`) — ex.: `/health` JSON legado sem envelope |

### Gate

```bash
cd api-delpi
python scripts/audit_route_test_coverage.py --report   # por módulo
python scripts/audit_route_test_coverage.py --write    # regenera inventário
python scripts/audit_route_test_coverage.py --check    # sync com baseline
python scripts/audit_route_test_coverage.py --check-complete  # zero gap
```

## Histórico das fases (concluídas)

| Fase | Escopo | Resultado |
|------|--------|-----------|
| **0** | Doc + inventário + audit + helpers + contratos faltantes | `--check` verde |
| **1** | canal-denuncia, cultura, supplies KPIs, hr, health, public | gaps óbvios fechados |
| **2** | products, production, engineering, commercial, system, scheduling, guias | ~80% |
| **3** | quality (PAC → PPM → kaizen → labels → 5S) | 135/135 |
| **4–5** | Nível B amostral + `--check-complete` | **100%** |

Smokes de referência: `tests/test_route_phase*.py`, `tests/test_route_meta_smoke.py`.  
Quality (fase 3): `test_route_phase3_quality_read_smoke.py`, `phase3b_quality_ppm_pac`, `phase3c_quality_kaizen`, `phase3d_quality_labels`, `phase3e_quality_audit5s`.

## Padrão de teste (template)

```python
from unittest.mock import MagicMock, patch
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

@patch("app.interface.http.routes….build_…_use_case")
def test_oid_returns_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"ok": True}))
    response = handler(branch=None, ...)  # kwargs explícitos
    assert_envelope_meta(body_json(response), operation_id="…", shape="scalar")
```

Mutações: mesmo smoke com mock; sem TOTVS/Postgres real.

## O que não fazer

- Contar só use case/SQL como “rota coberta” no gate
- Live TOTVS como critério de cobertura HTTP
- Exceção permanente sem `exempt` + `exemptReason` no inventário
- Chamada direta ao handler sem kwargs quando o default é `Query()`
- Entregar rota nova sem `--write` no inventário

## Checklist rota nova

Alinhar a [`new-api-route-checklist.mdc`](../../../.cursor/rules/new-api-route-checklist.mdc) e [`api-delpi-openapi-route-standards.mdc`](../../../.cursor/rules/api-delpi-openapi-route-standards.mdc):

1. `operation_id` estável + `ROUTE_CONTRACTS`
2. Smoke Nível A (ou harness parametrizado)
3. `audit_route_test_coverage.py --write && --check` (+ `--check-complete`)
4. Se Query fechado: caso 422 (`pattern=` nas factories)

## Referências

- Envelope / shapes: [`playbook-contrato-respostas-ia.md`](./playbook-contrato-respostas-ia.md)
- OpenAPI bilíngue: [`../api/openapi-bilingue-catalogo-canonico.md`](../api/openapi-bilingue-catalogo-canonico.md)
- Registry: `app/interface/http/route_contract_registry.py`
- Diretrizes Cursor: `new-api-route-checklist.mdc`, `api-delpi-openapi-route-standards.mdc`, `test-and-commit.mdc`
