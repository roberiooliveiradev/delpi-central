# Playbook 25 — Composição multi-rota de meta departamental (jul/2026)

## Objetivo

Quando o usuário pergunta a **meta / indicadores de um departamento**, o chat pode planejar **várias** `execute_external_action` (não só uma), no mesmo padrão do multi-scope de produto — **sem LLM escolhendo rotas**.

## Princípio

| Etapa | Quem decide |
|-------|-------------|
| Departamento, período, filial | Rules / regex / `department_idd` (já existem) |
| Quais rotas chamar | JSON declarativo `department_meta_composition.json` |
| Execução | Loop já existente em `ChatToolContextExecutionService` |
| Prosa unificada | Opcional pós-tool (`llm_synthesis`) — **não** planeja rotas |

## Arquitetura

```text
plan_actions
  → ChatDepartmentMetaCompositionPlanningService.plan(...)
       → resolve department_id
       → lê byDepartment[id].primaryRouteId + composeRouteIds
       → select_registry_route_id × N (cap maxToolCalls)
  → senão fallback select_action (1)
```

- Catálogo: `app/content/pt-BR/assistant/department_meta_composition.json`
- Planner: `app/domain/services/chat_department_meta_composition_planning_service.py`
- Resolução: `ExternalActionSelectionService.select_registry_route_id` → registry `route_by_id` + resolver (bypassa `match` vocabulary)
- Gancho: `ChatExternalActionOrchestrationService.plan_actions` (antes do fallback `select_action`)

## Fases

### P0 — Engineering (mínimo viável)

- [x] Triggers coloquiais («meta para», «metas e realizado», …)
- [x] `engineering`: primary `dashboardDepartmentIndicators` + compose `dashboardDepartmentIdd`, `engineeringTransformaSummary`
- [x] Testes unit + regressão `plannedCount >= 2`
- [x] **Sem LLM no planner**

### P1 — Demais departamentos

- [x] Entradas em `byDepartment` para commercial, financial, production, quality, hr, supplies
- [x] Primary = IDD indicators; compose = nota IDD + 1 KPI bandeira do depto (quando houver routeId estável)

### P2 — Heurística primary vs compose completo

- [x] «meta para X» curta → `primary` (só `primaryRouteId`)
- [x] Termos «painel / indicadores / visão integrada / metas e realizado» → pacote `compose`
- [x] Declarativo em `composeModeTerms` + `defaultMode: primary`

### P3 — (backlog) Agregar na api-delpi

- Se `department-indicators` passar a cobrir o suficiente, reduzir fan-out

## Anti-padrões

- LLM escolhendo `operationId`
- `if department ==` em use case / presenter
- Expandir `select_action` para top-K
- Presenter por rota

## Aceite

1. «meta para engenharia desse mês» → 1 toolCall primary (`dashboardDepartmentIndicators`, `department_id=engineering`)
2. «painel de indicadores da engenharia» → ≥ 2 toolCalls (indicators + IDD + Transforma)
3. Sticky comercial não impede o pacote (já coberto por conflito de departamento)
4. Latência ≈ soma das APIs; sem round-trip LLM extra no planejamento
