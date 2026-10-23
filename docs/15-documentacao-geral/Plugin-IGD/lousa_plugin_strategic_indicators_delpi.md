# Plugin Strategic Indicators — Lousa de definição inicial

## Objetivo
Consolidar tudo o que foi desenvolvido até aqui para o plugin de indicadores estratégicos da DELPI Central, incluindo:

- direção visual do dashboard
- estrutura de telas
- mapa de rotas
- permissões sugeridas
- wireframes textuais
- direção técnica do plugin
- rascunho inicial do manifesto

---

## 1. Contexto do plugin

O módulo será um **plugin da DELPI Central** para apresentação e análise dos indicadores estratégicos da empresa, com foco em:

- IGD (Índice Global Delpi)
- IDDs departamentais
- tendências históricas
- alertas gerenciais
- modo apresentação para reunião mensal

A proposta é que esse módulo tenha leitura executiva no topo e profundidade analítica conforme o usuário navega.

---

## 2. Conceito visual geral

### Direção de design
O dashboard deve seguir um estilo:

- corporativo
- clean
- premium
- legível em notebook e TV
- com forte hierarquia visual
- com foco em leitura rápida de performance

### Narrativa da interface
A navegação deve seguir uma lógica de cascata:

1. começa no **IGD**
2. desce para os **IDDs dos departamentos**
3. detalha os **indicadores internos**
4. termina em **alertas, tendências e ação gerencial**

### Uso dos tokens do portal
Base visual principal:

- `--bg`
- `--surface`
- `--surface-2`
- `--surface-3`
- `--primary`
- `--secundary`
- `--success`
- `--danger`
- `--border`
- `--border-2`
- `--shadow`

### Cores adicionais sugeridas
Para enriquecer o painel sem brigar com o design system atual:

- warning: `#f5b700`
- warning-soft: `#fff4cc`
- info-soft: `#e8f6fd`
- analytic-violet: `#6e59cf`
- support-teal: `#0f9d8a`

### Princípios visuais

- cards grandes
- bordas finas
- sombras suaves
- pouca saturação
- número principal sempre dominante
- gráficos elegantes e simples
- status em badges e faixas visuais
- evitar poluição visual

---

## 3. Estrutura de telas do plugin

### MVP visual recomendado

1. Visão Executiva
2. Departamentos
3. Detalhe do Departamento
4. Indicadores
5. Tendências
6. Modo Apresentação

### Segunda iteração

7. Alertas e Ações
8. Configurações

---

## 4. Tela 1 — Visão Executiva

### Objetivo
Responder rapidamente:

- qual o IGD do período
- qual a faixa de desempenho
- quais áreas puxaram o índice para cima
- quais áreas puxaram o índice para baixo

### Blocos

- header com filtros
- card hero do IGD
- faixa de classificação 0–10
- grid com cards de IDD por departamento
- gráfico de tendência do IGD
- gráfico de contribuição ponderada por departamento
- alertas do mês
- destaques positivos

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Painel Estratégico de Indicadores                                   │
│ [Unidade ▼] [Período ▼] [Departamento ▼]             [Exportar]     │
├──────────────────────────────────────────────────────────────────────┤
│  IGD                                                                │
│  7,8   Satisfatório com Alertas   +0,3 vs mês anterior              │
│  [Faixa 0–10 com marcador visual]                                   │
├──────────────────────────────────────────────────────────────────────┤
│ [Financeiro] [RH] [Comercial] [Produção] [Qualidade] [Suprimentos]  │
│ nota | peso | contribuição | tendência                              │
├──────────────────────────────────────────────────────────────────────┤
│ Evolução do IGD                        | Contribuição por área       │
│ gráfico de linha                       | barras por departamento     │
├──────────────────────────────────────────────────────────────────────┤
│ Alertas do mês                         | Destaques positivos         │
│ - PPM externo elevado                  | - OEE em alta               │
│ - Turnover acima da meta               | - Comercial acima da meta   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Tela 2 — Departamentos

### Objetivo
Comparar todos os departamentos em uma visão única.

### Blocos

- tabela premium ou grid analítica
- ordenação por nota, peso, contribuição, gap
- filtros por período e status
- clique para abrir drill-down

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Departamentos                                                       │
│ [Período ▼] [Ordenar por ▼] [Status ▼]                              │
├──────────────────────────────────────────────────────────────────────┤
│ Departamento | IDD | Peso | Contribuição | Meta | Tendência | Status│
│ Financeiro   | 7,5 | 15%  | 1,125        | 8,0  | ↗         | Alerta│
│ RH           | 6,2 | 15%  | 0,930        | 8,0  | ↘         | Crítico│
│ Comercial    | 8,1 | 17%  | 1,377        | 8,0  | ↗         | Bom    │
│ ...                                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ [Clique na linha para abrir detalhe do departamento]                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Tela 3 — Detalhe do Departamento

### Objetivo
Explicar a composição do IDD de uma área específica.

### Blocos

- cabeçalho com nome do departamento
- nota do IDD
- peso no IGD
- contribuição ponderada
- variação vs período anterior
- lista dos indicadores do departamento
- meta x realizado x nota x peso
- resumo gerencial
- histórico mensal

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Produção                                          [Voltar]          │
│ IDD 7,8 | Peso 17% | Contribuição 1,326 | +0,2 vs mês anterior      │
├──────────────────────────────────────────────────────────────────────┤
│ Indicadores do departamento                                         │
│ Custo MOD/ROL      [valor] [meta] [peso] [nota] [status]            │
│ Custos Produção    [valor] [meta] [peso] [nota] [status]            │
│ Depreciação/ROL    [valor] [meta] [peso] [nota] [status]            │
│ OEE                [valor] [meta] [peso] [nota] [status]            │
│ OTD                [valor] [meta] [peso] [nota] [status]            │
├──────────────────────────────────────────────────────────────────────┤
│ Histórico do IDD                     | Resumo gerencial              │
│ linha mensal                         | maior risco                   │
│                                      | maior avanço                  │
│                                      | impacto no IGD                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Tela 4 — Indicadores

### Objetivo
Ser a visão analítica completa do plugin.

### Blocos

- busca
- filtros avançados
- tabela analítica
- meta x realizado
- exportação
- painel lateral de detalhe

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Indicadores                                                         │
│ [Buscar] [Departamento ▼] [Status ▼] [Período ▼] [Exportar]         │
├──────────────────────────────────────────────────────────────────────┤
│ Indicador | Departamento | Realizado | Meta | Peso | Nota | Gap     │
│ EBITDA    | Financeiro   | 12,2%     | 13%  | 40%  | 7,1  | -0,8    │
│ OEE       | Produção     | 68%       | 70%  | 20%  | 7,4  | -2      │
│ ...                                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ Paginação / ordenação / painel lateral de detalhe                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 8. Tela 5 — Tendências

### Objetivo
Mostrar a evolução temporal do desempenho.

### Blocos

- linha histórica do IGD
- série dos IDDs
- heatmap por departamento x mês
- ranking de melhora
- ranking de piora

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Tendências                                                          │
│ [Período ▼] [Comparar com ▼]                                        │
├──────────────────────────────────────────────────────────────────────┤
│ Evolução do IGD (linha principal)                                   │
├──────────────────────────────────────────────────────────────────────┤
│ Heatmap mensal por departamento                                     │
│ Fin | RH | Com | Prod | Qual | Sup | Eng                            │
├──────────────────────────────────────────────────────────────────────┤
│ Melhores evoluções                     | Piores quedas               │
│ ranking                                | ranking                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Tela 6 — Alertas e Ações

### Objetivo
Traduzir indicadores em foco gerencial.

### Blocos

- indicadores críticos
- impacto estimado no IGD
- recorrência
- severidade
- priorização

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Alertas e Ações                                                     │
│ [Severidade ▼] [Departamento ▼] [Período ▼]                         │
├──────────────────────────────────────────────────────────────────────┤
│ Indicadores críticos                                                │
│ - PPM Externo abaixo do esperado                                    │
│ - Turnover acima da meta                                            │
│ - OTD em queda                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ Impacto estimado no IGD                 | Recorrência                │
│ cards por item                          | lista/contagem             │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10. Tela 7 — Modo Apresentação

### Objetivo
Ser a versão de reunião mensal do painel.

### Blocos

- IGD grande
- classificação textual
- cards resumidos dos departamentos
- gráfico principal
- alertas principais
- destaques positivos

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Painel Estratégico — Modo Apresentação                              │
├──────────────────────────────────────────────────────────────────────┤
│                IGD 7,8                                               │
│         Satisfatório com Alertas                                     │
│       +0,3 vs mês anterior                                           │
├──────────────────────────────────────────────────────────────────────┤
│ 7 cards grandes com IDDs                                             │
├──────────────────────────────────────────────────────────────────────┤
│ Gráfico principal do IGD + 3 alertas + 3 destaques                  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 11. Tela 8 — Configurações

### Objetivo
Governar pesos, metas e parâmetros do painel.

### Blocos

- pesos por departamento
- catálogo de indicadores
- metas por competência
- parâmetros de cálculo
- regras de exibição

### Wireframe textual

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Configurações do Painel                                             │
│ [Pesos] [Indicadores] [Metas] [Regras de exibição]                  │
├──────────────────────────────────────────────────────────────────────┤
│ Peso do IGD por departamento                                         │
│ Financeiro 15%                                                       │
│ RH 15%                                                               │
│ Comercial 17%                                                        │
│ ...                                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ Catálogo de indicadores / metas / ativação / observações            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Mapa de rotas do plugin

```text
/apps/strategic-indicators
/apps/strategic-indicators/departments
/apps/strategic-indicators/departments/:departmentId
/apps/strategic-indicators/indicators
/apps/strategic-indicators/trends
/apps/strategic-indicators/alerts
/apps/strategic-indicators/presentation
/apps/strategic-indicators/settings
```

---

## 13. Permissões sugeridas

```text
strategic-indicators.view
strategic-indicators.departments.view
strategic-indicators.indicators.view
strategic-indicators.trends.view
strategic-indicators.alerts.view
strategic-indicators.presentation.view
strategic-indicators.settings.manage
```

Permissões adicionais futuras:

```text
strategic-indicators.export
strategic-indicators.meta.manage
strategic-indicators.weights.manage
```

---

## 14. Estrutura sugerida do frontend

```text
plugins/strategic-indicators/
  src/
    ui/
      pages/
        ExecutiveDashboardPage.tsx
        DepartmentsPage.tsx
        DepartmentDetailsPage.tsx
        IndicatorsPage.tsx
        TrendsPage.tsx
        AlertsPage.tsx
        PresentationPage.tsx
        SettingsPage.tsx
      components/
        IgdHeroCard.tsx
        DepartmentCard.tsx
        DepartmentTable.tsx
        IndicatorTable.tsx
        TrendChart.tsx
        ContributionChart.tsx
        AlertList.tsx
        StatusBadge.tsx
        FilterBar.tsx
    state/
      hooks/
        useExecutiveDashboard.ts
        useDepartments.ts
        useDepartmentDetails.ts
        useIndicators.ts
        useTrends.ts
        useAlerts.ts
      store/
        strategicIndicatorsFiltersStore.ts
    data/
      api/
        strategicIndicatorsApi.ts
      adapters/
        executiveDashboardAdapter.ts
        departmentsAdapter.ts
        indicatorsAdapter.ts
      mappers/
        statusMapper.ts
        chartMapper.ts
    routes/
      index.tsx
    bootstrap/
      bootstrap.tsx
    App.tsx
    main.tsx
    index.css
  vite.config.ts
  package.json
  delpi.manifest.json
```

---

## 15. Direção técnica do plugin

### Tipo de integração
- microfrontend
- `renderMode: federated`

### Motivo
O plugin se encaixa no padrão oficial da DELPI Central para apps plugáveis carregados dinamicamente no portal.

### Base path
```text
/apps/strategic-indicators
```

### Entry esperado
```text
/apps/strategic-indicators/assets/remoteEntry.js
```

---

## 16. Rascunho inicial do manifesto

```json
{
  "schemaVersion": "1.0.0",
  "id": "strategic-indicators",
  "name": "Strategic Indicators",
  "description": "Painel estratégico corporativo com IGD, IDDs, tendências e alertas.",
  "category": "analytics",
  "version": "1.0.0",
  "icon": "bar-chart-3",
  "type": "microfrontend",
  "basePath": "/apps/strategic-indicators",
  "entry": "/apps/strategic-indicators/assets/remoteEntry.js",
  "healthcheck": "/apps/strategic-indicators/health",
  "permissions": [
    {
      "code": "strategic-indicators.view",
      "name": "Acessar painel estratégico",
      "description": "Permite acessar a visão executiva do painel estratégico.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.departments.view",
      "name": "Visualizar departamentos",
      "description": "Permite acessar a visão comparativa dos departamentos.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.indicators.view",
      "name": "Visualizar indicadores",
      "description": "Permite acessar a visão analítica dos indicadores.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.trends.view",
      "name": "Visualizar tendências",
      "description": "Permite acessar a visão histórica e temporal.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.alerts.view",
      "name": "Visualizar alertas",
      "description": "Permite acessar a visão de alertas e priorizações.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.presentation.view",
      "name": "Visualizar modo apresentação",
      "description": "Permite acessar o modo apresentação do painel.",
      "module": "strategic-indicators"
    },
    {
      "code": "strategic-indicators.settings.manage",
      "name": "Gerenciar configurações do painel",
      "description": "Permite alterar pesos, metas e parâmetros do painel.",
      "module": "strategic-indicators"
    }
  ],
  "routes": [
    {
      "path": "/apps/strategic-indicators",
      "label": "Painel Estratégico",
      "permission": "strategic-indicators.view",
      "icon": "bar-chart-3",
      "showInMenu": true,
      "order": 10,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/departments",
      "label": "Departamentos",
      "permission": "strategic-indicators.departments.view",
      "icon": "building-2",
      "showInMenu": true,
      "order": 11,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/indicators",
      "label": "Indicadores",
      "permission": "strategic-indicators.indicators.view",
      "icon": "table-properties",
      "showInMenu": true,
      "order": 12,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/trends",
      "label": "Tendências",
      "permission": "strategic-indicators.trends.view",
      "icon": "line-chart",
      "showInMenu": true,
      "order": 13,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/alerts",
      "label": "Alertas",
      "permission": "strategic-indicators.alerts.view",
      "icon": "triangle-alert",
      "showInMenu": true,
      "order": 14,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/presentation",
      "label": "Modo Apresentação",
      "permission": "strategic-indicators.presentation.view",
      "icon": "presentation",
      "showInMenu": false,
      "order": 15,
      "menuGroup": "Analytics"
    },
    {
      "path": "/apps/strategic-indicators/settings",
      "label": "Configurações",
      "permission": "strategic-indicators.settings.manage",
      "icon": "settings",
      "showInMenu": false,
      "order": 16,
      "menuGroup": "Analytics"
    }
  ],
  "backend": {
    "required": true,
    "validateJwt": true,
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi/strategic-indicators",
    "issuer": "https://www.minhadelpi.com.br/auth",
    "audience": "delpi-central"
  },
  "ui": {
    "renderMode": "federated"
  },
  "metadata": {
    "owner": "Equipe DELPI",
    "domain": "analytics",
    "product": "strategic-indicators"
  }
}
```

---

## 17. Resumo final

O plugin foi concebido como um **painel em cascata executiva**:

- começa com o IGD
- desce para os IDDs
- aprofunda nos indicadores
- mostra tendências e alertas
- oferece modo apresentação para reunião
- mantém uma camada administrativa para governança futura

A base já está pronta para seguir para o próximo passo de implementação em React.

