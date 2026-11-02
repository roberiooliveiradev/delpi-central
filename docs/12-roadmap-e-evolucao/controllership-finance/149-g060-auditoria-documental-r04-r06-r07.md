# Gate 060 — Auditoria documental R04/R06/R07 (2026-11-02)

Escopo: inventário exaustivo, matriz de contradições, cobertura técnica e lacunas reais.

## Descoberta central — contradição com gates anteriores

Os registros G052–G059 classificaram R06/R07 como "não implementados" por busca restrita ao namespace `financeiro`. O HEAD prova o contrário: **R06 e R07 estão completos em todas as camadas** (IMPLEMENTATION-015, fichas `IMPLEMENTED`). `SEARCH_MISS != ABSENCE`.

## Matriz de cobertura técnica — evidência no HEAD

| Camada | R04 Consumo por OP | R06 Kardex/CPV | R07 Inventários |
|---|---|---|---|
| api-delpi | `supplies/consumption_audit_*` (search/get/comparison) — `PROVEN` | `financeiro_stock_kardex/` (get, summary, cpv, export, _engine) — `PROVEN` | `supplies/inventory_adjustments*` (list, summary, shared) — `PROVEN` |
| BFF | NÃO existe — `TO_INVENTORY` | `/closing/stock-kardex`, `/summary`, `/products/{code}` — `PROVEN` | `/closing/inventory-adjustments`, `/summary` — `PROVEN` |
| CLARA | Não registrada — `TO_INVENTORY` | `read(report.stock_kardex)`, `_summary` — `PROVEN` | `read(report.inventory_adjustments)`, `_summary` — `PROVEN` |
| Portal | Não existe — `TO_INVENTORY` | `StockKardexPage` + `stockKardexApi` + REPORT_META — `PROVEN` | `InventoryAdjustmentsPage` + REPORT_META — `PROVEN` |
| Testes | `test_consumption_audit_*` (api-delpi) — PASS | `26/26` família kardex/cpv — `PASS` | `list/get_inventory_adjustments` — `PASS` |
| Paridade oficial | Não declarada (sem artefato MATR860) — `PENDING` | G1–G6 homologados (doc 61/83/84) — `PASS` | Reconciliação 45/45 (doc 66) — `PASS` |
| Lacuna real | Integração BFF/CLARA/Portal + decisão de boundary | nenhuma | nenhuma |

## Dossiê R04 — Consumo por Ordem de Produção

- Produtor canônico: `api-delpi` — use cases `supplies/search_consumption_audit_orders`, `get_consumption_audit_order`, `get_consumption_audit_comparison`; scope `consumption-audit.read`.
- Cadeia vigente: `Portal Suprimentos → supplies-api → api-delpi → TOTVS`.
- Cadeia TARGET aprovada: `Portal Controladoria → controllership-finance-api → api-delpi → TOTVS` (padrão R09).
- `CF_S2S_SCOPE` vazio = carrega defaults do client — provável cobertura de `consumption-audit.read` (verificar Keycloak).
- **Lacuna real**: somente a integração BFF/CLARA/MFE — o produtor já existe.
- MATR860: artefato oficial ausente — `officialParity=pending`; visão `operational_view`.

## Dossiê R06 — Kardex/CPV — IMPLEMENTADO

- Produtor: `api-delpi/use_cases/financeiro_stock_kardex/` — engine + get/summary/cpv/export.
- BFF: `closing_routes.py` `/closing/stock-kardex*` → `/financeiro/stock-kardex*`.
- MFE: `StockKardexPage.tsx`, `stockKardexApi.ts`, REPORT_META + report list.
- CLARA: `read(report.stock_kardex)` + `_summary` no `semantic_bridge`.
- Docs: `61` (matriz CPV), `83` (crosswalk), `84` (paridade monetária), `122` (gate contratual R06/R07).
- Ficha declara `IMPLEMENTED` — homologação anterior comprovada.
- **Lacuna**: nenhuma técnica. Acompanhamento = homologação operacional/perf, não implementação.

## Dossiê R07 — Inventários — IMPLEMENTADO

- Produtor: `api-delpi/use_cases/supplies/` — `list/get_inventory_adjustments*`, `inventory_adjustments_shared`.
- BFF: `/closing/inventory-adjustments` + `/summary` → `/financeiro/inventory-adjustments*`.
- MFE: `InventoryAdjustmentsPage.tsx` + REPORT_META + report list.
- CLARA: `read(report.inventory_adjustments)` + `_summary`.
- Docs: `66` (movimentos inventário), `122` (gate contratual).
- Ficha declara `IMPLEMENTED`.
- Natureza: relatório informacional (A), não rotina operacional — correta a separação R12/R15.
- **Lacuna**: nenhuma técnica.

## Matriz de contradições resolvidas

| ID | Fonte A | Fonte B | Resolução |
|---|---|---|---|
| C01 | G052–G058 "R06 não implementado" | Ficha R06 `IMPLEMENTED` + código HEAD | **HEAD vence** — busca anterior era só em `financeiro`; produtor em `supplies` |
| C02 | G052–G058 "R07 não implementado" | Ficha R07 `IMPLEMENTED` + código HEAD | **HEAD vence** — mesmo erro de busca |
| C03 | G053 "R04 não implementado" | consumption-audit completo | Parcial — produtor existe; falta só a integração BFF |

## Correções de documentação necessárias

1. Ledger G052–G058: corrigir "R06/R07 não implementado" → `IMPLEMENTED` (código prova).
2. R04: o único trabalho real é integração BFF/CLARA/Portal ao produtor existente — não produtor novo.

## Conclusão

- R06: **completo** — não reimplementar; só homologação operacional.
- R07: **completo** — idem.
- R04: **única lacuna real** = rota BFF + CLARA + MFE sobre o produtor `consumption-audit` existente — padrão R09.
