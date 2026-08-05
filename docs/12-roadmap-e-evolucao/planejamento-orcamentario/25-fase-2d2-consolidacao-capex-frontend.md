# 25 — Fase 2D.2: Consolidação gerencial CAPEX (frontend)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Escopo:** painel MFE de consolidação CAPEX, filtros, indicadores, gráficos, detalhamento paginado, exportação Excel e testes Vitest.  
**Fora:** alterações de backend/migrations/workflow/investimentos; Receita; Pessoal; PDF.

---

## 1. Rota e painel

| Item | Valor |
|------|--------|
| Path | `/apps/planejamento-orcamentario/capex/consolidacao` |
| Título | Consolidação de Investimentos |
| Menu portal | Manifesto `showInMenu: true`, perm `.capex.consolidation.view` |
| Atalho home | Visível com `hasCapexConsolidationViewAccess` |

Proteção visual no MFE + autorização no backend (2D.1).

---

## 2. Filtros

Barra com exercício, unidade, área, CC, categoria, prioridade, origem, status do plano, Data Rcbto inicial/final.

- Aplicação sob demanda («Aplicar filtros» / «Limpar») — sem request por tecla.
- Sync na URL via `history.replaceState`.
- Cascata Unidade → Área → Centro de custo (catálogo admin/scopes ou derivado do agrupamento por CC).

---

## 3. Indicadores

KPIs via `createSimpleKpiCard` (`@delpi/plugin-ui`): totais e contagens **somente** do payload `summary` (sem recalcular no frontend). Formatação BRL com `formatMoneyBr`.

---

## 4. Gráficos

Barras CSS acessíveis (`CapexConsolidationBarChart`):

- horizontal: unidade, área, categoria, prioridade, origem, status, CC;
- vertical: mês (Data Rcbto);
- CC: top 12 por valor + opção de expandir.

Erro parcial de um agrupamento não apaga KPIs/outros gráficos.

---

## 5. Detalhamento

Tabela paginada server-side; ordenação whitelist; links para planejamento do CC, investimento e aprovação (`submitted` + `plan_id`). Layout em cards em telas estreitas (CSS existente `.po-table`).

---

## 6. Exportação Excel

Botão **Exportar Excel** só com `.capex.export` (ou admin).

- Chama `GET …/export.xlsx` com filtros ativos;
- blob autenticado + nome do `Content-Disposition`;
- anti double-click; feedback; erros 401/403/422/rede;
- conflito `budget_capex_consolidation_currency_conflict` com mensagem clara.

---

## 7. Permissões e manifesto

Perms já existentes na 2D.1. Manifesto **0.2.0**:

- rota consolidação order `33`;
- admin orders deslocados (34–36).

JSON pronto para importação manual — **não** importar automaticamente nesta fase.

---

## 8. Testes

- `CapexConsolidationPage.test.tsx` — perms, filtros, KPIs, gráficos, empty, export, conflitos, 401/403/rede, ordenação;
- `capexConsolidation.test.ts` — helpers/routing/perms;
- `budgetPlanningApi.consolidation.test.ts` — query string + códigos no download.

---

## 9. Build e smoke

Rebuild sequencial do MFE após validação local:

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build planejamento-orcamentario
```

Conferir `remoteEntry.js` e shell da rota HTTP 200. Smoke autenticado depende de importar as perms novas no core.

---

## 10. Arquivos principais

- `src/pages/CapexConsolidationPage.tsx` (+ `.test.tsx`)
- `src/components/CapexConsolidationBarChart.tsx`, `KpiCard.tsx`
- `src/api/budgetPlanningApi.ts`, `httpClient.ts` (`downloadAuthenticatedBinary`)
- `src/utils/capexConsolidation.ts`, `permissions.ts`, `routing.ts`
- `App.tsx`, `HomePage.tsx`, `index.css`
- `planejamento-orcamentario.manifest.json` (0.2.0)

---

## 11. Pendências

- Importar manifesto/perms no core;
- Smoke autenticado com usuário consolidator/export;
- Catálogo org dedicado sem depender de `/admin/scopes` (fallback atual via agrupamento).

---

## 12. Status

**STATUS: CONCLUÍDO COM RESSALVAS**
