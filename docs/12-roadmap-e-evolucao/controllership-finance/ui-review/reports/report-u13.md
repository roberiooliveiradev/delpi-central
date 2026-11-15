# Report U13 — residuais da U12

Data: 2026-11-15. HEAD: `f546acd388`. Tag: `rollback-ui-review-u13-controllership-finance` (peel `f546acd388`). Verifier: `ACCEPT_WITH_RESIDUAL` (rodada 1).

## X1 — filtro axe + Exportar primary

| Item | Resultado |
|---|---|
| Filtro | `AXE_COLOR_CONTRAST_EXCEPTIONS` + `element.closest` em `.delpi-ui-action-btn`, `.delpi-ui-segment-toggle`, avatar/TopBar; sem `cf-action-with-icon` |
| Exceções | ActionButton `#ffffff`/`#089bdb`; SegmentToggle idem; Avatar/TopBar; host `.avatar` |
| Comercial | heros usam `variant="primary"` na ação principal → Exportar alinhado a `primary` |
| Residuais kit | registrados em [U10-desempenho-e-perfis.md](./U10-desempenho-e-perfis.md) (tabela U13 X1) |
| Commit | `a5f5bc57ff` |

## X2 — suíte MFE verde

| Teste | Commit que quebrou | Classificação | Correção |
|---|---|---|---|
| DocumentDetailPanel «trilha de auditoria» | pré-U12 (`be614649b7` base) | TESTE DESATUALIZADO | `within` na section Histórico |
| MonthlyDocumentsPanel «Exigido» | pré-U12 | TESTE DESATUALIZADO | `within` por cartão |
| P3CutoffPanel length 3→4 | pré-U12 | TESTE DESATUALIZADO | `within` lista «Bloqueios de prontidão» |
| PackagesPage «congelada» | pré-U12 | TESTE DESATUALIZADO | texto «Revisão de pacotes congelada» |
| reportQueryCache 403 / sessão | pré-U12 | TESTE DESATUALIZADO | assert negativo na frase canônica |
| BillingMod* realKit (recharts) | resolução de teste | CONFIG | alias `recharts` → `plugin-ui/node_modules` |
| closingTablePanel.structural | `012f396a89` (U12 W2) | TESTE DESATUALIZADO | exige `renderCard` + `viewLayoutPreferencesKey` |

`npm test`: **518 vitest + 26 mjs PASS, 0 falhas**. Commit: `329790bd78`.

## X3 — filtro de detalhamento

| | Antes | Depois |
|---|---|---|
| deps do reset | `[analysisId, detailFiltersKey]` | `[analysisId]` |
| ao filtrar | hero/KPIs/gráficos somem («carregando») | stale-while-revalidate; `aria-busy` nos KPIs; `loading` nas tabelas |
| teste | — | `EntryAuditAnalysisPage.detailFilter.test.tsx` |

Commit: `f546acd388`.

## HML

- Deploy MFE `controllership-finance` em `projetos-teste` @ `f546acd388` (healthy).
- Playwright U12 (`u12-ui-review.spec.ts`, desktop): **5 PASS, 1 SKIP** (previous null). Axe cf-access/cf-manage PASS com filtro novo.
- X3 one-shot (filtro Alta mantém hero/KPIs): **PASS**. Artefatos `/tmp/ui-review-u13` no host HML.

## PROD

- Tag `rollback-ui-review-u13-controllership-finance`.
- Deploy: `up-prod-sequential.sh --no-cache --build controllership-finance` @ `f546acd388`.
- Smoke: `remoteEntry.js` HTTP 200; bundle contém Exportar.

## Parada

U13 concluída. Residuais do kit (ActionButton/SegmentToggle contraste) permanecem com o dono plugin-ui. Prints de PROD da U12 seguem com o owner.
