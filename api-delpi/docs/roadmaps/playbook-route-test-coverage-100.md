# Playbook — cobertura de testes em 100% das rotas (api-delpi)

**Status:** em andamento (Fase 0 entregue; ondas 1–5 no backlog)  
**Baseline:** ~368 operações OpenAPI (`app/content/openapi_baseline.json`)  
**Gate:** `python scripts/audit_route_test_coverage.py`

## Objetivo

Toda operação do OpenAPI (`method` + `path` + `operationId`) tem cobertura **HTTP de contrato** rastreável. Lógica de negócio continua em testes de use case/SQL; este playbook fecha o gap da **camada de rota**.

| Nível | Obrigatório para “100%”? | O que cobre |
|-------|--------------------------|-------------|
| **A — meta smoke** | Sim | `success`, `meta.operationId` / `entity` / `shape` (via `ROUTE_CONTRACTS`) |
| **B — Query fechado** | Sim (quando houver `enum`/`pattern`) | valor inválido → **422** |
| **C — comportamento** | Só rotas críticas | RBAC filial, upload, mutações, PDF |
| **D — gate CI** | Sim | inventário sincronizado; depois `--check-complete` |

## Baseline (jul/2026)

| Métrica | Valor aproximado |
|---------|------------------|
| Operações OpenAPI | 368 |
| `operationId` citado em algum teste | ~50% |
| Em `test_*route*` / `*smoke*` | ~26% |
| Maior gap | `quality`, `guias-procedimentos`, `scheduling`, KPIs commercial/production |

## Estratégia canônica

### Harness Nível A

```text
openapi_baseline → operationId → RouteContract
→ TestClient (router isolado) + auth mock + patch composer/use case
→ assert envelope meta
```

- Preferir **TestClient** (evita defaults `Query()` = FieldInfo em chamada direta).
- Fixture mínima por `shape`: `scalar`, `paged_list`, `playbook_report`, `hierarchy`, …
- Helpers: `tests/support/route_contract_smoke.py`.

### Inventário

Arquivo: [`app/content/route_test_coverage.json`](../../app/content/route_test_coverage.json)

Cada operação tem `status`:

| status | Significado |
|--------|-------------|
| `covered` | `operationId` aparece em `tests/**/*.py` |
| `gap` | sem menção em testes |
| `exempt` | isento documentado (`exemptReason`) — ex.: `/health` JSON legado sem envelope |

### Gate

```bash
cd api-delpi
# Relatório por módulo
python scripts/audit_route_test_coverage.py --report

# Regenera inventário a partir do baseline + scan de testes
python scripts/audit_route_test_coverage.py --write

# CI (Fase 0): inventário sincronizado com o baseline (mesmo conjunto de operationIds)
python scripts/audit_route_test_coverage.py --check

# Meta final: zero gap (exceto exempt)
python scripts/audit_route_test_coverage.py --check-complete
```

`--check-complete` só deve entrar no CI quando o inventário estiver sem `gap`.

## Fases

| Fase | Escopo | Critério |
|------|--------|----------|
| **0** | Doc + inventário + audit + helpers + contratos faltantes | `--check` verde; `--report` útil |
| **1** | Módulos pequenos: canal-denuncia, cultura, supplies KPIs, hr, health, public | reduzir gaps óbvios |
| **2** | products + production + engineering + commercial KPIs | ~80% covered |
| **3** | quality (PAC → 5S → kaizen → labels → mutações) | maior bloco |
| **4** | guias-procedimentos + scheduling + system tables | fechar restante |
| **5** | Nível B gerado + amostra Nível C + `--check-complete` no CI | **100%** |

### Ordem sugerida na Fase 1

1. `canal-denuncia`, `cultura-delpi`, `health` (exempt ou assert plain JSON)
2. `supplies` OTD / stock-value / inventory-turnover
3. `hr` active-pdi / performance-reviews
4. Demais gaps de 1–2 ops (`public`, KPIs órfãos)

## Padrão de teste (template)

```python
from unittest.mock import MagicMock, patch
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

@patch("…composer.build_…_use_case")
def test_oid_returns_meta(mock_build) -> None:
    mock_build.return_value = MagicMock(execute=MagicMock(return_value={"ok": True}))
    # Preferir kwargs explícitos ou TestClient
    response = handler(...)
    assert_envelope_meta(body_json(response), operation_id="…", shape="scalar")
```

Mutações: mesmo smoke com mock; sem TOTVS/Postgres real.

## O que não fazer

- Contar só use case/SQL como “rota coberta” no gate
- Live TOTVS como critério de cobertura HTTP
- Exceção permanente sem `exempt` + `exemptReason` no inventário
- Chamada direta ao handler sem kwargs quando o default é `Query()`

## Checklist rota nova

Alinhar a [`new-api-route-checklist.mdc`](../../../.cursor/rules/new-api-route-checklist.mdc) e:

1. `operation_id` estável + `ROUTE_CONTRACTS`
2. Smoke Nível A (ou entrada no harness parametrizado)
3. `python scripts/audit_route_test_coverage.py --write && --check`
4. Se Query fechado: caso 422

## Referências

- Envelope / shapes: [`playbook-contrato-respostas-ia.md`](./playbook-contrato-respostas-ia.md)
- OpenAPI bilíngue: [`../api/openapi-bilingue-catalogo-canonico.md`](../api/openapi-bilingue-catalogo-canonico.md)
- Smoke legado por amostra: `tests/test_route_meta_smoke.py`
- Registry: `app/interface/http/route_contract_registry.py`
