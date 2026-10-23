# Lousa da Fase 3 — Strategic Indicators

## Etapa atual
**Fase 3 — MVP 1: Visão Executiva**

## Status da fase
**Concluída**

## Objetivo da fase
Conectar a **home do plugin** à **API real** por meio do endpoint:

`GET /apps/api-delpi/strategic-indicators/executive-summary`

Esta fase foi concluída com a tela principal deixando de usar mock e passando a renderizar dados reais da API.

---

## Escopo que entrou nesta fase
- home do plugin (`/apps/strategic-indicators`)
- IGD da visão principal
- classificação do IGD
- variação do período
- departamentos resumidos da home
- alertas resumidos da home
- loading, erro e sucesso da home
- backend do endpoint `executive-summary`
- frontend data layer da home

## Escopo que não entrou nesta fase
- `GET /departments`
- `GET /departments/{departmentId}`
- `GET /indicators`
- `GET /trends`
- `GET /alerts`
- integração real da tela de presentation
- novas evoluções de settings/audit/change-requests
- qualquer etapa futura do roadmap

---

## Contrato do endpoint entregue
O endpoint entrega:

- `competence`
- `igd`
- `igd_exact`
- `classification`
- `variation`
- `departments[]`
  - `id`
  - `name`
  - `short_name`
  - `weight_pct`
  - `score`
  - `contribution`
  - `trend`
  - `strategic_summary`
  - `key_indicators`
  - `executive_goal`
- `alerts_summary[]`

---

## Arquivos criados nesta fase

### Backend
- DTO/response de `executive-summary`
- ports de agregação do summary
- use case orquestrador do `executive-summary`
- repository de leitura de settings para summary
- providers iniciais para fontes do summary

### Frontend
- tipo de `executive-summary`
- client da API de `executive-summary`
- hook da home executiva
- adapter da resposta da API para o shape da UI

---

## Arquivos alterados nesta fase

### Backend
- `api-delpi/app/interface/http/routes/strategic_indicators_routes.py`
- `api-delpi/app/composition/strategic_indicators_composer.py`
- `api-delpi/app/application/use_cases/strategic_indicators/get_executive_summary_use_case.py`
- migrations de estrutura/seed do módulo

### Frontend
- `plugins/strategic-indicators/src/ui/pages/ExecutiveDashboardPage.tsx`
- `plugins/strategic-indicators/src/App.tsx`
- `plugins/strategic-indicators/src/ui/components/InfoState.tsx`

---

## Correções prévias concluídas
- fluxo de auditoria alinhado ao padrão do módulo
- port de auditoria criada
- composer ajustado para auditoria
- rota de auditoria refatorada
- client de `change-requests` corrigido
- home preparada para receber token
- `InfoState` ajustado para suportar `actionLabel` e `onAction`

---

## Entregas consolidadas da fase
- backend do `executive-summary` implementado
- frontend da home conectado à API real
- home sem dependência de `executiveDashboardMock`
- `goals.summary` persistido com os 7 departamentos
- seed completo do módulo consolidado
- `indicators.catalog` persistido com short_name e strategic_summary
- `executive-summary` refatorado para agregação de fontes, sem uso do fluxo antigo monolítico

---

## Validação final da fase
### Validado
- `/apps/api-delpi/strategic-indicators/executive-summary` respondendo corretamente
- `/apps/api-delpi/strategic-indicators/settings` consistente com os dados persistidos
- 7 departamentos com `executive_goal` preenchido
- contrato da home executiva entregue

### Observação
A evolução futura das fontes analíticas reais de score/trend/alerts ficará para fases posteriores, sem bloquear o fechamento funcional da Fase 3.

---

## Critério de conclusão
A Fase 3 foi considerada concluída porque:

- `ExecutiveDashboardPage` deixou de usar mock
- o endpoint `GET /apps/api-delpi/strategic-indicators/executive-summary` existe e responde
- a home renderiza dados reais
- a home trata loading, erro e sucesso
- as demais páginas permaneceram fora do escopo desta fase

---

## Próxima fase
**Fase 4 — Departamentos e drill-down**

### Objetivo da próxima fase
Conectar as telas de departamentos à API real, com foco exclusivo em:

- `GET /apps/api-delpi/strategic-indicators/departments`
- `GET /apps/api-delpi/strategic-indicators/departments/{departmentId}`

### Escopo inicial da próxima fase
- visão comparativa de departamentos
- drill-down por área
- contrato real de departamentos
- backend e frontend dessas duas rotas

### Proibição de escopo na próxima fase
- `GET /indicators`
- `GET /trends`
- `GET /alerts`
- qualquer avanço para fases seguintes antes do fechamento da Fase 4