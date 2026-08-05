# 08 — Mapa de telas e arquitetura do MFE

## 1. Estrutura de pastas sugerida

```text
plugins/planejamento-orcamentario/
  planejamento-orcamentario.manifest.json
  src/
    bootstrap.tsx
    App.tsx
    index.css                 # tokens locais → delpi-ui; sem espelho de componentes
    api/httpClient.ts
    types/                    # contratos espelhando envelope
    data/                     # adapters REST
    state/                    # hooks de exercício, escopo, autosave
    features/
      home/
      orientations/
      revenue/
      headcount/
      capex/
      approvals/
      consolidation/
      exports/
      admin/
    ui/shared/                # shells de página, banners de status, empty/error
    routes.tsx
```

Integração host: `mount` / `updateRoute` / `unmount` + `getAccessToken` + `permissions`.  
Design system: `@delpi/plugin-ui/index` + `delpiUiClass`.

## 2. Mapa de rotas UI

| Rota | Tela | Persona |
|------|------|---------|
| `/` | Home do exercício (status, prazos, CTA) | todos |
| `/orientacoes` | Carta + docs + confirmar leitura | todos |
| `/receita` | Projeção (quando especificado) | receita |
| `/pessoal` | Grade headcount por unidade/área | pessoal |
| `/capex` | Lista/filtros + editor de item | capex |
| `/aprovacoes` | Fila de workflows | aprovador |
| `/consolidacao` | KPIs e tabelas gerenciais | consolidate |
| `/exportacoes` | Histórico e download | export |
| `/admin` | Exercício, escopos, listas | admin |

## 3. Componentes (não implementar agora)

- `ExerciseStatusBanner` — open/closing/locked/leitura pendente
- `ReadingGate` — bloqueia filhos até confirmação
- `ScopeSwitcher` — unidade / CC (apenas opções autorizadas)
- `AutosaveIndicator` — saving / saved / conflict / offline
- `HeadcountGrid` — hierarquia unidade→área (não “Excel cru”)
- `CapexTable` + `CapexItemDrawer` — formulário longo, validação
- `WorkflowActionsBar` — submit/approve/return
- `ConsolidationDashboard` — KPI cards plugin-ui
- Estados: loading / empty / error / success / locked / readonly

## 4. Diretrizes de UX

- Orientada a tarefas, não planilha transplantada
- Responsiva; tabelas densas com scroll e filtros
- Hierarquia clara: exercício → módulo → item
- Somente leitura visual quando status locked/approved
- Acessível: labels, foco, contraste tokens Delpi
- Modais: `HostContainedDialog` (não cobrir sidebar)

## 5. Tratamento de erros

- 409 revision → modal merge/recarregar
- 403 escopo → mensagem + link home
- 401 → host reauth
- Export falho → retry na lista de jobs
