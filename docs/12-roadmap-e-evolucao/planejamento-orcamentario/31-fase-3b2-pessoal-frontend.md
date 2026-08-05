# 31 — Fase 3B.2: Orçamento de Pessoal (frontend)

**Data:** 2026-08-05  
**Branch:** `feat/planejamento-orcamentario`  
**Tipo:** MFE — preenchimento de headcount por cargo (texto livre)  
**Pré-requisito:** Fases 3B.1 / 3B.1.1 (backend V008–V009)  
**Manifesto:** `0.2.3`

---

## Escopo entregue

- Rota `/apps/planejamento-orcamentario/pessoal` (permissão `personnel.view`)
- Seleção dos centros atribuídos ao módulo `personnel` (filial · código · descrição)
- Resolve do plano (`POST …/plans/resolve`) para quem tem `.edit`; consulta via list/get para somente `.view`
- Grade editável: Cargo, Dez/2025, Out/2026, **Previsto**, Dez/2027, Observações, estado, ações
- Criação («Adicionar cargo»), autosave com debounce por linha, arquivamento com confirmação
- Totais oficiais do backend (não recalculados no MFE)
- Modo somente leitura com `.view` sem `.edit`

## Fora de escopo

Workflow, submissão, aprovação, consolidação, exportação, salários, encargos, benefícios, catálogo de cargos.

## Contrato consumido

| Operação | Path |
|----------|------|
| Resolve | `POST /personnel/plans/resolve` |
| List/Get | `GET /personnel/plans`, `GET /personnel/plans/{id}` |
| Linha | `POST …/lines`, `PUT /personnel/lines/{id}`, `POST …/archive` |
| Meus CCs | `GET /capex/my-responsibilities?module=personnel` |
| Descrição CC | `GET /org/erp-cost-centers?branch=` (enriquecimento do label) |

Campo de cargo: `position_name` (trim, ≤200, acentos). Duplicidade: `budget_personnel_line_duplicate_position`. Conflito: HTTP 409 `budget_personnel_line_version_conflict` (sem merge; recarregar linha).

## Autosave

Padrão CAPEX: debounce 1s, estados **Alterado / Salvando / Salvo / Erro**, uma requisição por linha, `version` obrigatória no update.

## Permissões

| Permissão | UI |
|-----------|-----|
| `personnel.view` | Consulta, grade read-only |
| `personnel.edit` | Incluir, editar, arquivar, resolve |

## Manifesto

Versão **0.2.3** — rota menu «Orçamento de Pessoal» com `personnel.view`. Pronto para importação manual (sem auto-import/atribuição).

## Validação (entrega)

| Gate | Resultado |
|------|-----------|
| typecheck | ok |
| Vitest (plugin completo) | **165 passed** |
| Vitest (pessoal) | 23 passed |
| build Vite | ok |
| rebuild MFE sequencial | `delpi-planejamento-orcamentario` recriado |
| `remoteEntry.js` | HTTP **200** |
| shell `/apps/…/pessoal` (portal) | HTTP **200** |
| smoke autenticado | pendente (sem sessão com `personnel.*` neste ambiente) |

## Arquivos principais

- `src/pages/PersonnelBudgetPage.tsx` (+ testes)
- `src/utils/personnelPlans.ts` (+ testes)
- `src/api/budgetPlanningApi.ts` / `src/types/budgetPlanning.ts`
- `src/utils/routing.ts`, `permissions.ts`, `App.tsx`, `HomePage.tsx`
- `planejamento-orcamentario.manifest.json` `0.2.3`
