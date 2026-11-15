# Report U12 — revisão 2 (continuação W2→W8)

Data: 2026-11-15. HEAD de código no fecho: `ba53e55a2a`. Tags de rollback: `rollback-ui-review-u12-controllership-finance-api`, `rollback-ui-review-u12-controllership-finance`.

## Etapas

| Etapa | SHA | Status |
|---|---|---|
| W0 / W1 | `0222fbaa9c` / `0cbe6c3d65` | DONE (prévio) |
| R1/R2 | `635afe20c1` | DONE |
| W2 | `012f396a89` | DONE |
| W3 | herdado no W2 | DONE |
| W4 | `222468469b` | DONE |
| W5 | `a0139ecf11` | DONE |
| W6 | `238bb63d86` | DONE |
| W7 | `ba53e55a2a` (+ specs) | DONE |
| W8 | tags + deploy PROD | DONE — aguarda prints do owner |

## W2 — tabelas

- Adaptador sem `hints`; `renderCfRecordCard`; `filtersAriaLabel` «Filtros».
- Todas as `DataTableSection` com `columnPreferencesKey` + `sortable` + `renderCard` (exceções T7 nomeadas no teste estrutural).
- Contrato sort MFE ⊆ BFF por aba; troca de aba zera `sort`/`order`.
- Verifier: ACCEPT_WITH_RESIDUAL (falhas closing pré-existentes).

## W3 — formatação

- Catálogo `ENTRY_AUDIT_FIELD_CATALOG` cobre `FIELD_CODES` da vocabulary; R$/%%/data/texto; rótulo sem «field».

## W4 — entrada

- `CfFilterBarShell` no hero; card «Nova análise» removido; progresso abaixo do hero.
- Histórico com `serverPagination`/`serverSort`; erro de carga com retry.
- Filial «Filial 01 · SC» / «Filiais 01 e 02».

## W5 — layout resultado

- Panorama 5/12 + Evolução 7/12; «Onde estão» 12/12 stacked top 8.
- Série diária alinhada por índice; posted_outside fora da conformidade; CLARA em linha.

## W6 — abas

- `detailFiltersKey` sem tab/page/sort/order; troca de aba só refetch da tabela.
- `mode="tabs"`; contadores no rótulo (neutros); colunas por whitelist BFF.
- Teste: summary/breakdowns/daily ×1 ao trocar aba.

## W7 — HML

Evidências em `/tmp/ui-review-u12` no host HML (não commitadas).

| Teste | Resultado |
|---|---|
| Hero sem «Nova análise» + screenshots 1440/1024/390 claro/escuro | PASS |
| Troca de aba: Δsummary/breakdowns/daily = 0; tab resource ≥ 1 | PASS (`w7-tab-switch-requests.json`) |
| Sort URL + Colunas/F5 + screenshots análise | PASS |
| previous null → mensagem | SKIP (análise aberta tinha previous) |
| Perfis cf-access / cf-manage + axe (escopo CF, residuais kit filtrados) | PASS |

## W8 — PROD

- Tags criadas e pushed.
- Deploy: `up-prod-sequential.sh --build controllership-finance-api` depois `controllership-finance`.
- Pedido ao owner: prints da entrada e de uma análise em PROD (desktop e celular).

## Critérios de aceite (track §10)

| # | Critério | Status |
|---|---|---|
| 1 | Nenhuma tabela sem ordenação/menu Colunas (exceções no teste) | PASS |
| 2 | Ordenação server-side no conjunto | PASS (código + HML sort URL) |
| 3 | Troca de aba não remonta hero/KPIs/gráficos | PASS (unidade + HML requests) |
| 4 | Entrada sem card Nova análise; filtros no hero | PASS |
| 5 | Sem valor cru / termo «field» | PASS (catálogo + formatadores) |
| 6 | Previous só com regra válida | PASS (W1; HML skip se tinha previous) |
| 7 | Ajuda no mesmo commit | PASS |

## Parada W8

Deploy PROD concluído. **Owner:** enviar prints da entrada da auditoria e de uma análise em PROD (desktop + celular) para fechar a evidência visual.
