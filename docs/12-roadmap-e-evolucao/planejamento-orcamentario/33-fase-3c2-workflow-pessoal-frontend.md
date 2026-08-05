# 33 — Fase 3C.2 — Workflow Pessoal frontend (submissão e aprovação)

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-05  
**Escopo:** painel de workflow na tela de Pessoal, submissão, histórico, fila e detalhe de aprovação, decisões, bloqueio visual, concorrência otimista, permissões, testes MFE.  
**Fora:** consolidação, exportação, notificações, salários/benefícios/encargos, dependência de Receita, alterações de backend.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: CONCLUÍDO COM RESSALVAS
```

---

## 1. Painel de workflow

Componente `PersonnelPlanWorkflowPanel` embutido em `/pessoal` (quando há `edit` ou `submit`).

Exibe: status (labels PT), versão, filial, CC, exercício, cargos, totais headcount, incompletas, submissão/decisão e comentário.

## 2. Submissão

Botão **Enviar para aprovação** com `confirm`, versão atual, bloqueio se autosave pendente.  
Incompleto → `budget_personnel_plan_incomplete` + lista de cargos/campos + foco na linha.

## 3. Bloqueio da grade

Editável só em `draft` / `changes_requested` (`isPersonnelPlanEditable`).  
`budget_personnel_plan_locked` recarrega o plano e explica a mudança.

## 4. Ajustes solicitados

Destaque do comentário/data/ator; reenvio liberado com `submit`.

## 5. Histórico

`GET …/personnel/plans/{id}/history` via `PersonnelPlanHistoryTimeline` (timeline genérica `PlanHistoryTimeline` também usada pelo CAPEX).

## 6. Fila

Rota `/pessoal/aprovacoes` — filtros (incl. URL), paginação, totais Dez/2027, Analisar.

## 7. Detalhe

Rota `/pessoal/aprovacoes/:planId` — somente leitura (tabela headcount + totais + histórico). Fora do menu.

## 8. Decisões

Solicitar ajustes / Reprovar (comentário obrigatório) / Aprovar orçamento — com confirmação e versão.

## 9. Concorrência

409 `budget_personnel_plan_version_conflict` → não retry automático; «Recarregar dados»; comentário preservado no detalhe.

## 10. Permissões e manifesto

`view` / `edit` / `submit` / `approve`. Manifesto **0.2.5** com rota de aprovações no menu (`personnel.approve`). Sem auto-import.

## 11. Testes

Vitest: panel, fila, detalhe, routing, utils + regressão Pessoal/CAPEX — **189 passed**.

## 12. Build e smoke

| Check | Resultado |
|-------|-----------|
| Typecheck (`tsc --noEmit`) | OK |
| ESLint (arquivos do workflow) | OK |
| Vitest | **189 passed** |
| `vite build` (local) | OK |
| Rebuild MFE (`up-dev-sequential.sh --fase mfe --build planejamento-orcamentario`) | OK (sessão anterior) |
| `remoteEntry.js` | HTTP **200** |
| Shell `/pessoal` | HTTP **200** |
| Shell `/pessoal/aprovacoes` | HTTP **200** |
| Shell `/pessoal/aprovacoes/:planId` | HTTP **200** |
| Smoke autenticado (API com token) | **Não executado** — nenhuma chave `SMOKE_ACCESS_TOKEN` / `DELPI_SMOKE_TOKEN` em `infra/.env` |

## 13. Arquivos principais

| Área | Path |
|------|------|
| API | `plugins/planejamento-orcamentario/src/api/budgetPlanningApi.ts` |
| Utils | `src/utils/personnelPlans.ts`, `routing.ts` |
| UI | `PersonnelPlanWorkflowPanel`, `PersonnelPlanHistoryTimeline`, `PlanHistoryTimeline` |
| Páginas | `PersonnelBudgetPage`, `PersonnelReviewQueuePage`, `PersonnelReviewDetailPage` |
| Testes | `*.personnel.workflow*`, `PersonnelPlanWorkflowPanel.test`, `PersonnelReview*.test` |
| Manifesto | `planejamento-orcamentario.manifest.json` **0.2.5** |
| Doc | este arquivo |

## 14. Pendências

- Importação manual do manifesto **0.2.5** e atribuição de `personnel.submit` / `personnel.approve`.
- Smoke autenticado quando houver sessão + permissões.
- Consolidação / exportação / notificações (fases futuras).
- Rota de detalhe só via router interno (fora do menu do manifesto — esperado).
