# DESIGN-IA — Portal Suprimentos

> Padrão de navegação do Portal Comercial, adaptado ao domínio Suprimentos.  
> Root CSS: `.dashboard-supplies-portal` · prefixo `sp-` · tokens `--sp-*` → `--delpi-ui-*`.

---

## 1. Princípios

| | Início `/` | Visão geral `/overview` |
|---|---|---|
| Papel | ação e descoberta | diagnóstico gerencial |
| Conteúdo | alertas, busca, favoritos, recentes, cards de rota | **7 KPIs P0**, tendência, exceções, drill |
| Não traz | dashboard de 25 KPIs | filas operacionais completas |

- Capability-driven: nav/ações aparecem conforme effective permissions do Core; nunca `if role`.
- O MFE usa capabilities apenas para UX; backend continua a barreira real de segurança.
- `allowedUnits` é derivado das permissions efetivas do Core, não de claims do JWT.
- Nav não se duplica por SC/ES.
- Deep pages ficam fora da top nav.
- Favoritos/recentes seguem mecanismos canônicos do Portal/Comercial quando disponíveis.
- Modais host-contained.

---

## 2. Navegação

```text
PORTAL SUPRIMENTOS
Início                         /
Visão Geral                    /overview
Minhas Atividades              /my-tasks

COMPRAS
  Solicitações de Compras      /purchase-requests
  Pedidos de Compra            /purchase-orders
  Entregas / Atrasos           /deliveries
  Importações                  /imports          (bloqueado até E1)
  Alçadas                      /approvals        (bloqueado até validar workflow)

FORNECEDORES
  Fornecedores                 /suppliers
  Fornecedor 360               /suppliers/:code/:store
  OTD Fornecedores             /suppliers/otd

PRODUTOS E MATÉRIAS-PRIMAS
  Consulta de Item             /products
  Produto / MP 360             /products/:code
  Onde o Item é Usado          /products/:code/where-used

ESTOQUES
  Controle de Estoques         /inventory
  Estoque de Segurança         /safety-stock
  Análise de Consumo           /safety-stock/consumption-analysis

NEGOCIAÇÕES
  Savings                      /negotiations
  Histórico de Preços          /products/:code/price-history

GESTÃO
  Indicadores                  /indicators

ADMINISTRAÇÃO                  /administration
AJUDA                          /help
PERFIL (SPA)                   /users/:userId
```

Rotas novas usam identificadores em inglês. URLs PT só permanecem como aliases/redirects de legado quando necessário.

### Páginas generalistas (padrão Comercial)

| Página | Rota | Papel | Wireframe |
|---|---|---|---|
| Shell | chrome | TopBar, nav, Ctrl+K, estados | Shell comum |
| Início | `/` | hub ação/descoberta | WF-01 |
| Visão geral | `/overview` | placar KPI (≠ Início) | WF-02 |
| Ajuda | `/help` | Manual / Quero→onde / FAQ | WF-HELP |
| Perfil | `/users/:userId` | identidade + prefs do plugin | WF-USER |

O perfil **global** Minha DELPI (`/profile` do Portal) permanece no shell host. O WF-USER do plugin é o análogo ao Comercial (`/apps/commercial/users/:userId`): contexto do **Portal Suprimentos** (units, capabilities, preferências `supply_user_preferences`), sem carteiras/OV.

Preferências **não** ganham rota `/preferences` dedicada — edição no próprio perfil + API `/me/preferences`.

---

## 3. Capabilities de UX

| Área | Capability base |
|---|---|
| shell/Home/Ajuda/Perfil/Minhas Atividades | `supplies.portal.access` |
| Solicitações de Compras | `supplies.purchase-requests.access` |
| PC/entregas/fornecedor/produto/estoque/ESTSEG | `supplies.operations.access` |
| Overview/OTD gerencial/CPV/giro/savings | `supplies.analytics.access` |
| Administração | `supplies.administration.manage` |

Não criar navigation gates por permissions CRUD como `tasks.view`/`tasks.write`. Tasks e notas usam capability do recurso + unit + ownership/regra de negócio conforme ADR-007.

---

## 4. Shell

```text
TopBar kit (createDashboardTopBar)
  · collapseMode=hamburger · collapseTrigger=overflow  (igual Comercial)
  · secondary: busca Ctrl+K
  · actions: avatar+nome → perfil self + hint coexistência (Ajuda só na nav)
UnderlineNav embutida na TopBar (itens por capability)
PagePath nas internas
PageHero no Início (e Overview)
```

† itens de nav por capability. Ajuda na nav + rota `/help`. Entrada ao perfil: avatar/nome na TopBar → `/users/:userId` (E4.S4).

---

## 5. Component mapping `@delpi/plugin-ui`

Priorizar componentes existentes do kit:

| Uso | Componente |
|---|---|
| Chrome | `TopBar`, `UnderlineNav`, `PageHero`, `PagePath` |
| Hub | `SectionRouteCard`, `CatalogSearchBar`, `HubChipRow`, `RouteChip`, `CommandPalette` |
| Métricas | `MetricKpiCard`, `SectionCard`, `ChartCard` |
| Dados | `DataTable`, `StatusBadge`, `createDashboardFiltersKit` |
| Ação | `ActionButton`, `EmptyState`, `LoadingActivityCard` |
| Trabalho | `AlertQueue`, `WorklistItem` |
| Ajuda | `HelpTooltip`, `FieldLabel`, `SectionHintLabel` |

Zero CSS estrutural duplicado do kit no MFE. Novo primitivo com potencial de reuso deve ser avaliado no `plugin-ui`.

---

## 6. Responsivo / tema

| Viewport | Comportamento |
|---|---|
| Desktop | tabelas completas; nav underline |
| Tablet | filtros em wrap; KPIs 2 colunas |
| Mobile ≤768px | nav scroll; tabelas → cards/stacked; gráficos responsivos; hit target ≥44×44 |
| Light/dark | tokens do MFE mapeados para tokens do Portal |

Proibido CSS global do MFE (`body`, `:root`, `*`, `.delpi-ui-*`).

---

## 7. Busca, favoritos, recentes e alertas

- Busca do Hub: catálogo de rotas + busca de fornecedor/item somente quando contratos existirem.
- Favoritos: Core/Portal.
- Recentes: padrão Comercial enquanto não houver serviço canônico melhor.
- Alertas Home P0: composição on-read; persistência só com evidência de necessidade.

---

## 8. Estados e falha parcial

Toda página planeja loading, empty, error, 403 e 404.

BFFs compostos podem renderizar blocos parciais quando dependência auxiliar falhar; authz nunca é mascarada como partial success.

Overview deve exibir contexto temporal dos KPIs (snapshot, estado atual, intervalo, competência).
