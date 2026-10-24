# E11.S1 — Estoque de Segurança: implementação Backend/BFF

**Data:** 2026-10-23 · **BASE HEAD:** `2fc8d17304` · **Escopo:** `supplies-api` apenas — read-only, zero frontend/deploy/migrations.

## Arquitetura

```text
plugins/supplies (E11.S2, futuro)
  → supplies-api /safety-stock/*   ← NOVO (esta etapa)
      → DelpiApiGateway (Bearer user JWT + X-Delpi-Caller-App: supplies-api
        + apply_internal_service_headers → service token)
      → api-delpi /supplies/safety-stock/*  → TOTVS
```

| Camada | Arquivo |
|---|---|
| Rotas | `supplies-api/app/interfaces/http/routes/safety_stock_routes.py` (`safety_stock_bp`, registrado em `root_composer.py`) |
| Service | `supplies-api/app/application/services/safety_stock_service.py` |
| Gateway | `supplies-api/app/infrastructure/gateways/supplies_delpi_reads.py` (3 métodos novos + extensão compatível de summary/items) |
| Testes | `supplies-api/tests/interface/http/test_safety_stock_bff.py` (18 testes) |

## Rotas implementadas

| Rota Portal (`/apps/supplies-api`) | Upstream | branch |
|---|---|---|
| `GET /safety-stock/filters` | `/supplies/safety-stock/filters` | scope `all`\|`01`\|`02`, default `all` |
| `GET /safety-stock/summary` | `/supplies/safety-stock/summary` | idem |
| `GET /safety-stock/items` | `/supplies/safety-stock/items` | idem + `page`, `page_size` ≤ 200, `sortBy`, `sortDirection`, `status`, `productGroup`, `unit`, `search`, `includeBlocked`, `includeWithoutSafetyStock` |
| `GET /safety-stock/items/<code>/details` | `/supplies/safety-stock/items/{code}/details` | **filial concreta obrigatória** (`01`\|`02`) |
| `GET /safety-stock/items/<code>/suppliers` | `/supplies/safety-stock/items/{code}/suppliers` | idem |

## Semântica de `branch`

- Scope (`filters`/`summary`/`items`): `all` (default), `01`, `02` — repassado ao produtor como **uma chamada** (o produtor une 01+02 no SQL; **sem fan-out** do BFF). Inválido → **422**.
- Detalhe/fornecedores: filial concreta obrigatória; `all`/ausente/inválida → **422**.
- Nenhum grant por filial: validação é contra `OPERATIONAL_UNITS`, não permissions (ADR-009 / decisão PO `611cb8c0dc`).

## AuthZ

- `@require_policy(can_use_operations)` → `supplies.access` via Core effective permissions (`g.current_user`). 401 anônimo, 403 sem capability, 503 se Core indisponível (fail-closed), zero chamada upstream quando não autorizado.
- `supplies.manage` sozinho **não** concede (contrato vigente — mesmo de E10).

## Trusted BFF

- Gateway envia `X-Delpi-Caller-App: supplies-api` + headers internos via `apply_internal_service_headers` (credencial de `delpi_auth.service_token`, nunca em logs/frontend).
- Produtor verifica `is_trusted_supplies_bff_call()` = caller + **service token válido** — header sozinho não basta; testes do produtor (`test_supplies_bff_service_access.py`, **4 pass**) cobrem: token exigido, caller exigido, isolamento por caller, `BranchAccessGate` pulado **apenas** para BFF confiável.
- `BranchAccessGate` intacto para consumidores diretos; nenhum bypass novo criado.

## Contratos

- **Filters:** o campo upstream `authorized_branches` (escopo do consumidor legado) é **descartado**; o BFF expõe `branch_catalog = ["01","02"]` + `all_scope = "all"` + demais dados de domínio (grupos, UMs, statuses, warehouses metadata).
- **Summary/items/details/suppliers:** passthrough do `data` do envelope — nenhum recálculo de status/déficit/saldos/projeção; 404 upstream → 404; lista vazia real ≠ erro.
- **Erros:** `unauthorized` 401 · `forbidden` 403 · `not_found` 404 · `unprocessable` 422 (validação local) · `upstream_client_error` <500 · `bad_gateway` 502 (5xx/timeout/falha de rede).

## Correção de contrato incluída

`SuppliesDelpiReads.get_safety_stock_items` enviava `sort_by`/`sort_direction` (ignorados pelo produtor) — agora `sortBy`/`sortDirection` (aliases corretos). Retrocompatível: assinatura e defaults inalterados.

## Testes

- **18 novos** (`test_safety_stock_bff.py`): authz (401/403/503 Core-down/zero upstream), filters + `branch_catalog`, summary `all` single-call, filtros de domínio, paginação/sort válidos e 422 inválidos, empty real, details/suppliers com filial concreta + 404, supplier code+store preservados, mapeamento de erros upstream, registro de rotas.
- **Suíte completa supplies-api: 499 passed, 21 skipped** (regressão E10/Overview/inventory/users/suppliers incluída).
- **Produtor:** `test_supplies_bff_service_access` 4 pass + `test_safety_stock_routes` + `test_branch_access_gate` 26 pass (executado em E11.P0).

## Residuais

- `authorized_branches` upstream pode vir vazio em chamada BFF — mitigado por `branch_catalog` próprio.
- Export CSV do legado: fora de escopo (`TO_INVENTORY`, decisão E11.P0).
- `E11_S1_OUTCOME = ACCEPT`. **Readiness E11.S2:** rotas vivas e testadas; MFE pode consumir conforme contrato desta doc.


## Revisão GPT — E11.S1 (2026-10-24)

**Veredito: `ACCEPT_WITH_RESIDUAL`** para a implementação BFF; **`E11_S2_READY_TO_AUTHORIZE=YES`**, mas sem autorização automática de implementação frontend/deploy. Inspecionados no SHA `b21462896a`: este relatório, `safety_stock_service.py`, `safety_stock_routes.py`, `supplies_delpi_reads.py` e testes de rota. Foram confirmadas cinco rotas, `can_use_operations`, filial como filtro `all/01/02`, filial concreta nos detalhes, validação de paginação/sort e gateway BFF-only. Os resultados 499 PASS +21 SKIP e os quatro testes trusted-BFF são evidências do executor, não reexecutadas pelo GPT.

**Residual de robustez de contrato a verificar:** métodos do gateway `SuppliesDelpiReads` retornam `{}` quando o `data` desenvelopado não é `dict`; em `SafetyStockService.get_filters/get_summary` há fallback semelhante. Checar resposta HTTP 200 com envelope `success:true,data:null/list` ou payload inválido, e envelope de erro `success:false`, para evitar que indisponibilidade/má formação pareça sucesso vazio. Provar caso real e caso irmão/negativo antes de alterar código. Se reproduzido, tratar como erro de integração distinto de empty/404 em task bounded ou antes do gate final E11; não bloquear o planejamento de E11.S2.

**Não alterado:** ADR-009, sem permissions por filial, `api-delpi`, manifest, write ERP, frontend, deploy ou X4.PROD-C1. Gate federado/visual de E11 permanece `TEST_NOT_RUN`.
