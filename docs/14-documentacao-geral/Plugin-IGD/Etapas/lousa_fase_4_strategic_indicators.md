# Lousa da Fase 4 — Strategic Indicators

## Etapa atual
**Fase 4 — Departamentos e drill-down**

## Status da fase
**Concluída**

## Objetivo da fase
Conectar as telas de departamentos à API real, com foco exclusivo em:

- `GET /apps/api-delpi/strategic-indicators/departments`
- `GET /apps/api-delpi/strategic-indicators/departments/{departmentId}`

Esta fase foi concluída com a visão comparativa de departamentos e o drill-down por área deixando de usar mock e passando a renderizar dados reais da API.

---

## Escopo que entrou nesta fase
- tela `/apps/strategic-indicators/departments`
- tela `/apps/strategic-indicators/departments/{departmentId}`
- contrato real de `departments`
- contrato real de `departments/{departmentId}`
- backend das duas rotas
- frontend data layer das duas telas
- loading, erro e sucesso das duas telas
- regra de agregação por unidade (`average_of_units`, `consolidated`, `mixed_scope`)
- modelagem de indicadores com `scope_type`

## Escopo que não entrou nesta fase
- `GET /indicators`
- `GET /trends`
- `GET /alerts`
- integração real da tela de presentation
- novas evoluções de settings/audit/change-requests
- qualquer etapa futura do roadmap

---

## Contrato entregue de `/departments`
- `items[]`
  - `id`
  - `name`
  - `short_name`
  - `weight_pct`
  - `score`
  - `classification`
  - `contribution`
  - `aggregation_mode`
  - `strategic_summary`
  - `variation`

## Contrato entregue de `/departments/{departmentId}`
- `id`
- `name`
- `short_name`
- `weight_pct`
- `score`
- `classification`
- `contribution`
- `aggregation_mode`
- `strategic_summary`
- `variation`
- `units[]`
  - `unit_id`
  - `unit_name`
  - `score`
  - `classification`
- `indicators[]`
  - `id`
  - `name`
  - `weight_pct`
  - `goal_2026`
  - `strategic_description`
  - `scope_type`
  - `realized`
  - `score`
  - `gap`
  - `trend`

---

## Regra funcional consolidada da fase
- os **7 departamentos continuam únicos**
- o **IGD usa o score consolidado do departamento**
- departamentos como Financeiro, RH, Produção, Qualidade e Engenharia usam **média entre unidades**
- Suprimentos é **consolidado**
- Comercial é **mixed_scope**
- o drill-down exibe unidades e indicadores com escopo operacional

---

## Arquivos criados nesta fase

### Backend
- ports de catálogo e snapshot de departamentos
- DTOs de `departments` e `departments/{departmentId}`
- use cases de listagem e detalhe de departamentos
- repository de catálogo dos departamentos
- providers temporários de snapshot consolidado e detalhado
- migration evolutiva do catálogo para unidades e agregação

### Frontend
- tipos de `departments`
- tipos de `departmentDetails`
- clients de API das duas rotas
- adapters das duas telas
- hooks das duas telas

---

## Arquivos alterados nesta fase

### Backend
- `api-delpi/app/composition/strategic_indicators_composer.py`
- `api-delpi/app/interface/http/routes/strategic_indicators_routes.py`
- migrations de seed/catálogo do módulo

### Frontend
- `plugins/strategic-indicators/src/ui/pages/DepartmentsPage.tsx`
- `plugins/strategic-indicators/src/ui/pages/DepartmentDetailsPage.tsx`
- `plugins/strategic-indicators/src/ui/components/DepartmentOverviewTable.tsx`
- `plugins/strategic-indicators/src/App.tsx`

---

## Entregas consolidadas da fase
- backend de `/departments` implementado
- backend de `/departments/{departmentId}` implementado
- frontend da visão comparativa conectado à API real
- frontend do drill-down conectado à API real
- `departmentsMock` removido da visão comparativa
- `getDepartmentById` do mock removido do detalhe
- catálogo preparado para matriz/filial/consolidado
- contratos compatíveis com a lógica de duas unidades

---

## Validação final da fase
### Validado
- `/apps/api-delpi/strategic-indicators/departments` respondendo corretamente
- `/apps/api-delpi/strategic-indicators/departments/{departmentId}` respondendo corretamente
- comparativo de departamentos funcionando com API real
- detalhe de departamento funcionando com API real
- correção do conflito de tipos em `DepartmentOverviewTable`

### Observação
As fontes analíticas reais por indicador e por unidade ainda podem evoluir nas próximas fases, sem bloquear o fechamento funcional da Fase 4.

---

## Critério de conclusão
A Fase 4 foi considerada concluída porque:

- `DepartmentsPage` deixou de usar `departmentsMock`
- `DepartmentDetailsPage` deixou de usar `getDepartmentById`
- existem as rotas:
  - `GET /apps/api-delpi/strategic-indicators/departments`
  - `GET /apps/api-delpi/strategic-indicators/departments/{departmentId}`
- ambas as telas renderizam dados reais
- as demais páginas permaneceram fora do escopo desta fase

---

## Próxima fase
**Fase 5 — Indicators**

### Objetivo da próxima fase
Conectar a tela de indicadores à API real, com foco exclusivo em:

- `GET /apps/api-delpi/strategic-indicators/indicators`

### Escopo inicial da próxima fase
- catálogo analítico de indicadores
- filtros e leitura comparativa de indicadores
- backend e frontend da rota de indicadores

### Proibição de escopo na próxima fase
- `GET /trends`
- `GET /alerts`
- qualquer avanço para fases seguintes antes do fechamento da Fase 5