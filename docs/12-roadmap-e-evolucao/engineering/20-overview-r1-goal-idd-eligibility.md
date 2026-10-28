# OVERVIEW.R1 — Correção da elegibilidade de metas e IDD

> **Status:** implementado e deployado.  
> **Missão:** correção da associação indevida de metas/scores a indicadores operacionais.  
> **Baseline:** `origin/main` em `2178a2762c` (rebase sobre `8b173db467`).  
> **Autoridades:** doc 18 (design), `KPI-FICHAS.md` (elegibilidade canônica), doc 19 (implementação).

## 1. Sintoma

Na Visão geral, os cards **Soluções implementadas** e **ROI médio TRANSFORMA+**
exibiam metas, Meta mês, Nota IDD e badges de desempenho pertencentes ao
indicador estratégico de ganhos financeiros (`engineering-transforma-plus`).

## 2. Causa raiz

Camada: adapter do BFF — `engineering_app/infrastructure/gateways/overview_api_delpi.py`.

O resumo TRANSFORMA+ do owner (`api-delpi`) chega já enriquecido com os campos
`goal_*`/`value_*` do indicador estratégico `engineering-transforma-plus`. O
método `_indicator()` repassava `_goal_fields(payload)` para **todos** os
indicadores da família, fazendo `transforma_solutions` e `transforma_roi`
herdarem a meta dos ganhos brutos. O mesmo defeito latente existia na família
LMP (`lmp_lead_time`, `lmp_total_proposals` herdariam a meta de
`engineering-projects-on-time`).

O frontend (`buildKpiGoalPresentation` via `createDashboardKpiCard`) renderiza
fielmente os campos presentes no contrato — portanto o bug era de contrato,
não de renderização.

## 3. Regra correta (contrato de aceite)

| Indicador | Meta | IDD | Badges |
|---|---|---|---|
| `lmp_on_time` — % LMP dentro do prazo | Sim (owner) | Sim, quando disponível | Conforme SI |
| `lmp_lead_time` | Não | Não | Não |
| `lmp_total_proposals` | Não | Não | Não |
| `transforma_gross_savings` — Ganhos brutos | Sim (owner) | Sim, quando disponível | Conforme SI |
| `transforma_solutions` | Não | Não | Não |
| `transforma_roi` | Não | Não | Não |

Elegibilidade segue o **indicador canônico** (`engineering-projects-on-time`,
`engineering-transforma-plus`), nunca a família/fonte. IDs elegíveis:
`GOAL_ELIGIBLE_INDICATORS = {lmp_on_time, transforma_gross_savings}`.

## 4. Correção aplicada

### Backend (`engineering-api`)

- `overview_api_delpi.py`: `GOAL_ELIGIBLE_INDICATORS` (frozenset) + `_indicator()`
  só repassa `_goal_fields(payload)` quando o indicador é elegível.
- IDD já era correto (`SI_IDD_BY_INDICATOR` mapeia apenas os dois elegíveis) —
  nenhuma alteração.
- Nenhum cálculo novo; o owner continua sendo a fonte de metas/scores.

### Frontend (`plugins/engineering`)

- `overviewViewModel.ts`: `GOAL_ELIGIBLE_IDS` — indicadores não elegíveis nem
  chamam `buildKpiGoalPresentation`; renderizam apenas valor, unidade, período,
  escopo e fonte (defesa contra vazamento futuro de contrato).
- `HelpPage.tsx`: copy do manual esclarece que metas/Nota IDD só aparecem nos
  dois indicadores estratégicos (feature-help-sync).

## 5. Antes/depois do contrato

```text
antes (transforma_solutions):
  { value: 69, has_goal: true, goal_value: 10000, goal_label: "...", ... }
depois:
  { value: 69 }  # sem campos goal_*/value_*/idd — honesto
```

## 6. Testes

Backend (`tests/test_overview_gateways.py`, +2):

- `test_lmp_goal_fields_only_on_strategic_indicator` — metas do resumo LMP só
  em `lmp_on_time`; `lmp_lead_time`/`lmp_total_proposals` sem nenhum campo.
- `test_transforma_goal_fields_only_on_gross_savings` — soluções e ROI não
  herdam meta, prefixo/sufixo, direção de performance.

Frontend (`overviewViewModel.test.ts`, +1):

- Matriz negativa: os 4 operacionais recebem fixture com metadados
  estratégicos vazados → cards sem `goalLabel`, `monthlyGoalLabel`,
  `goalScopeBadge`, `goalPerformanceBadge`, `iddScoreLabel`; e o estratégico
  elegível continua exibindo meta/IDD.

## 7. Resultados

| Verificação | Resultado |
|---|---|
| pytest engineering-api | 195 passed |
| vitest plugins/engineering | 90 passed (10 arquivos) |
| `npm run typecheck` | 0 erros |
| `npm run lint` | 0 erros (corrigidos 2 unused-vars pré-existentes no teste do client) |
| `npm run build` | OK (warning pré-existente de chunk >500 kB) |
| audit_backend_boundaries | 0 findings |
| audit_platform_guardrails | 0 findings |
| audit_fastapi_authz | 0 findings |

## 8. Regressões preservadas

Valores/fórmulas dos seis KPIs, filtros (presets, datas, competência, unidade,
consolidado), refresh, estados parciais/forbidden/empty, delegação humana,
Core AuthZ, CTA TRANSFORMA+ condicionado, LMP futuro sem CTA — todos com
cobertura na suíte existente (nenhuma alteração).

## 9. Deploy e smoke

- Push para `main` (ff-only): SHA `f9e0264089` (após rebase sobre
  `0869a218f8`, avanço concorrente de origin/main).
- Deploy canônico em `srv-api`: `git pull --ff-only` +
  `./infra/scripts/up-prod-sequential.sh --build engineering-api engineering` →
  `delpi-engineering-api` e `delpi-engineering` Up/healthy.
- Smoke público pós-deploy (edge canônica `http://192.168.1.237` → gateway):
  `200` `/apps/engineering`, `/apps/engineering/overview`,
  `/apps/engineering/help`, `/apps/engineering-api/health`,
  remoteEntry `200`; `401` `/apps/engineering-api/v1/overview` sem JWT
  (fail-closed preservado).
- Bundle verificado no edge: `remoteEntry.js` →
  `__federation_expose_App-oZm440aI.js` → `App-B9P1jPDx.js` contém a nova
  copy do Help ("dois indicadores estratégicos") e o código da Visão geral.
- Observação operacional: `https://192.168.1.237` (sem porta) cai no server
  padrão :443 do host (`api-totvs` → :3000), não na stack do portal — falso
  401 "GPT_API_TOKEN" durante o smoke. A edge da plataforma é
  `http://192.168.1.237` (gateway :80) / `:8443` (delpi.local). Um restart de
  `delpi-gateway` foi feito por precaução (IPs de upstream re-resolvidos);
  nenhuma alteração de configuração.
- Smoke autenticado (metas ausentes em soluções/ROI com dados reais):
  `PENDING_GRANT_APPROVAL` — requer sessão com `engineering.access`.

## 10. Residuais

- QA visual autenticado pendente (gate administrativo herdado da F3.OVERVIEW).
- IDD depende de `DASHBOARD_IDD_ACCESS` efetivo no owner — sem grant, cards
  elegíveis exibem meta mas não Nota IDD (contrato honesto, não defeito).

## 11. SHA final

`f9e026408915501941a602befa5afec7941f9c2b` — código + documentação.
