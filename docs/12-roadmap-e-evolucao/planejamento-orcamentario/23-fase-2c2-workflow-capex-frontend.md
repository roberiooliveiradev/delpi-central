# 23 — Fase 2C.2 — Workflow CAPEX frontend (submissão e aprovação)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** UI de resumo/submissão/histórico no centro de custo; fila de aprovação; tela de análise; decisões (aprovar / solicitar ajustes / reprovar); bloqueio visual; testes.  
**Fora:** migrations/backend, e-mail, exportação, consolidação executiva, restore, conta contábil.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO
```

---

## 1. Tela do responsável

Na página CAPEX (`/capex?cost_center_id=`), o painel `CapexPlanWorkflowPanel`:

- resolve o plano via `POST /capex/plans/resolve`;
- exibe exercício, unidade, área, CC, status (labels PT), contagens, valor total, última alteração, submissão, comentário da decisão e histórico.

---

## 2. Submissão

Botão **Enviar planejamento para aprovação** quando:

- permissão `planejamento-orcamentario.capex.submit` (ou admin);
- status `draft` | `changes_requested`.

Confirmação com CC, quantidade, valor total e aviso de bloqueio. Envia `version` atual.

`budget_capex_plan_incomplete` → lista itens + campos + links de edição.

---

## 3. Histórico

Timeline (`CapexPlanHistoryTimeline`) com ação, status anterior/novo, comentário, usuário e data/hora — só dados da API.

---

## 4. Fila de aprovação

Rota: `/apps/planejamento-orcamentario/capex/aprovacoes`  
Permissão: `planejamento-orcamentario.capex.approve`  
Menu no manifesto (`showInMenu: true`).

Filtros: exercício (ativo), unidade, área, CC, status, responsável; paginação. Enriquecimento de quantidade/valor via detalhe de revisão.

---

## 5. Tela de análise

Rota: `/apps/planejamento-orcamentario/capex/aprovacoes/:planId`  
Somente leitura: resumo, investimentos, categorias, prioridades, fornecedores, datas, anexos (download), histórico, responsável.

---

## 6. Decisões

- Aprovar (confirmação)
- Solicitar ajustes (comentário obrigatório)
- Reprovar (justificativa obrigatória)

Sempre com `version`. Conflito 409 → mensagem + **Recarregar dados**.

---

## 7. Bloqueio visual

Status `submitted` | `rejected` | `approved`: oculta novo/arquivar; formulário e anexos read-only; banner explicativo.  
`changes_requested`: destaca comentário do aprovador e libera edição/reenvio.  
Backend permanece autoridade.

---

## 8. Permissões

Helpers `hasCapexSubmitAccess` / `hasCapexApproveAccess`. Manifesto já tinha as permissões; rota de menu da fila adicionada. Sem auto-import/atribuição.

---

## 9. Testes e validação

Vitest (escopo 2C.2 + regressão CAPEX): **43 passed**.  
`npm run lint` (0 errors), `typecheck`, `build` OK.  
Rebuild MFE sequencial + `remoteEntry.js` HTTP 200.

---

## 10. Arquivos principais

| Área | Path |
|------|------|
| API/types | `budgetPlanningApi.ts`, `budgetPlanning.ts`, `httpClient.ts` |
| Utils | `capexPlans.ts`, `routing.ts`, `permissions.ts` |
| UI responsável | `CapexPlanWorkflowPanel.tsx`, `CapexPlanHistoryTimeline.tsx`, `CapexMyCostCentersPage.tsx` |
| Aprovação | `CapexReviewQueuePage.tsx`, `CapexReviewDetailPage.tsx` |
| Form lock | `CapexInvestmentFormPage.tsx` |
| Rotas/menu | `App.tsx`, manifesto |
| Testes | `*.test.ts(x)` do workflow |
| Doc | este arquivo |

---

## 11. Pendências

- Notificações por e-mail
- Exportações / consolidação executiva
- Atribuição operacional das permissões a grupos
- Smoke autenticado ponta a ponta (depende de sessão com perms submit/approve)

---

## 12. Validação executada

| Check | Resultado |
|-------|-----------|
| Vitest (foco 2C.2) | 43 passed |
| Lint | 0 errors |
| Typecheck | OK |
| Build | OK |
| Rebuild MFE | sequencial |
| remoteEntry.js | 200 |
| Commit | não |
