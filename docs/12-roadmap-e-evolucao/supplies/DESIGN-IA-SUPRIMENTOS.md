# DESIGN-IA — Portal Suprimentos

> Padrão de navegação do [Portal Comercial](../commercial/DESIGN-IA-COMERCIAL.md) · regras visuais distintas (domínio Suprimentos).  
> Root CSS: `.dashboard-supplies-portal` · prefixo `sp-` · tokens `--sp-*` → `--delpi-ui-*`.

---

## 1. Princípios

| | Início `/` | Visão geral `/overview` |
|--|------------|-------------------------|
| Papel | Ação e descoberta | Diagnosis gerencial |
| Conteúdo | AlertQueue, busca, favoritos, recentes, SectionRouteCards | ≤8 KPIs, tendência, exceções, drill |
| Não traz | Funil de 25 KPIs | Filas operacionais completas |

- Capability-driven: item de nav some se o usuário não tem cap (não `if role`).
- **Unidade:** filtro e default vêm de `allowedUnits` (eixo B). Nav **não** se duplica por SC/ES. Sem `if unidade == SC`.
- Deep pages (360, OTD detalhe, consumo) **fora** da top nav — catálogo + Ctrl/Cmd+K.
- Favoritos/recentes: Core (mesmo mecanismo do portal); HubChipRow no Início.
- Command Palette: `createDashboardCommandPalette` + `createHostContainedModalShell`.
- Modais: host-contained (`mfe-modal-host-contained.mdc`).

---

## 2. Navegação (hipótese revisada pelo inventário)

```text
PORTAL SUPRIMENTOS
Início                         /
Visão Geral                    /overview
Minhas Atividades              /my-tasks

COMPRAS
  Solicitações de Compras      /purchase-requests
  Pedidos de Compra            /purchase-orders
  Entregas / Atrasos           /deliveries
  Importações                  /imports          (cap se dump confirmar)
  Alçadas                      /approvals        (P1, cap se dump)

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
  Histórico de Preços          /products/:code/price-history  (detalhe)

GESTÃO
  Indicadores                  /indicators
  (CPV, OTD, Estoque, Giro, Savings = páginas de foco ou âncoras do Overview)

ADMINISTRAÇÃO                  /administration
AJUDA                          /help
```

**Removido da hipótese inicial:** duplicar OTD em Gestão e Fornecedores como dois produtos — um Overview + uma página de foco `/supplies/otd` (alias `/analytics/otd`). Qualidade de fornecedor **não** é item de menu próprio (card no 360 + deep link Inspeções).

**Aliases PT de URL:** no máximo redirects de legado (`/analise-consumo` → `/safety-stock/consumption-analysis`). Rotas **novas** só EN.

---

## 3. Shell

```
TopBar (Portal Suprimentos | ações contexto)
UnderlineNav: Início · Visão geral · Minhas atividades · Solicitações† · Estoques† · Administração†
PagePath nas internas
PageHero só no Início
```

† visível por cap. Help no TopBar overflow + rota `/help`.

---

## 4. Component mapping `@delpi/plugin-ui`

Todos **existem** (CONFIRMADO_NO_CODIGO no kit):

| Uso | Componente |
|-----|------------|
| Chrome | `TopBar`, `UnderlineNav`, `PageHero`, `PagePath` |
| Hub | `SectionRouteCard`, `CatalogSearchBar`, `HubChipRow`, `RouteChip`, `CommandPalette` |
| Métricas | `MetricKpiCard` / `createMetricKpiCard`, `SectionCard`, `ChartCard` |
| Dados | `DataTable`, `StatusBadge`, `createDashboardFiltersKit` |
| Ação | `ActionButton`, `EmptyState`, `LoadingActivityCard` |
| Trabalho | `AlertQueue`, `WorklistItem` |
| Ajuda | `HelpTooltip`, `FieldLabel`, `SectionHintLabel` |

Bind: `plugins/supplies/src/app/suppliesUi.ts` (padrão `commercialUi.ts`). **Zero** CSS de componente no MFE. Se faltar primitivo com 2+ consumidores → estender `plugin-ui`, não copiar.

---

## 5. Responsivo / tema

| Viewport | Comportamento |
|----------|----------------|
| Desktop | Tabelas completas; nav underline |
| Tablet | Filtros em wrap; KPIs 2 colunas |
| Mobile ≤768px | UnderlineNav scroll; tabelas → cards/`DataRecordCard`; gráficos `ResponsiveContainer`; hit target ≥44×44 |
| Light / dark | Tokens `--sp-*` + `:root[data-theme="dark"] .dashboard-supplies-portal` |

**Proibido:** `body{}`, `:root{}` global, `*{}`, `.delpi-ui-*`, `@media (prefers-color-scheme)`.

---

## 6. Busca, favoritos, recentes, alertas

- Busca do Hub: rotas do catálogo + (P1) fornecedor/item via BFF search (reusar `GET /products/search` e busca SA2 se existir; senão só catálogo até gap).
- Favoritos: rotas Core do app `supplies`.
- Recentes: localStorage do MFE (padrão Comercial) até haver API de recents.
- Alertas Home: composição BFF (déficit, OTD late, SC aging) **sem** persistência na P0; persistência = E13.

---

## 7. Estados

Toda página planeja: loading (`LoadingActivityCard`), empty, error, 403 (filial/cap), 404. Copy em `content/` PT.
