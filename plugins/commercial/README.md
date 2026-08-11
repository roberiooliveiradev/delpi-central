# Portal Comercial

Microfrontend federado do domínio comercial. Reúne, no próprio Portal Comercial,
as bancadas e fichas de Minha carteira, Conta 360, pedidos, OP, oportunidades OV,
propostas e gestão.

> Norte: [GESTAO-A-VISTA.md](../../docs/12-roadmap-e-evolucao/commercial/GESTAO-A-VISTA.md) · Perfis: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md) · Wireframes: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) (WF-02R / WF-02R-D) · Excelência lista+detalhe: [playbook-mfe-page-excellence.md](../../docs/05-plugin-system/playbook-mfe-page-excellence.md)

Plugins irmãos (`pedidos-venda-abertos`, `dashboard-commercial`, `propostas-comerciais`) **coexistem** no menu. O `commercial` não usa iframe, remote, componente, URL nem fallback de interface de outro MFE: suas páginas são nativas e consomem apenas contratos HTTP.

```text
Portal Minha DELPI
  → MFE commercial (rotas SPA + RBAC + @delpi/plugin-ui)
    → commercial-api (carteiras, atividades, anexos e enrichment)
    → api-delpi (pedidos, faturamento, produção, OV e ADY)
```

## Rotas UI

| Rota | Descrição | Permissão |
|------|-----------|-----------|
| `/apps/commercial` | Início — hero + alertas + KPIs + teaser Gestão | `accounts.view` |
| `/apps/commercial/my-day` | Meu dia — worklist | `worklist.view` |
| `/apps/commercial/open-orders` | Pedidos em aberto (TOTVS) | `accounts.view` |
| `/apps/commercial/open-orders/:filial/:pedido/:linha` | Ficha nativa da linha do pedido | `accounts.view` |
| `/apps/commercial/open-orders/:filial/:pedido/:linha/op/:op` | Ficha nativa da OP vinculada à linha | `accounts.view` |
| `/apps/commercial/customers` | Carteira de clientes | `accounts.view` |
| `/apps/commercial/customers/:codigo/:loja` | Conta 360 híbrida | `accounts.view` |
| `/apps/commercial/proposals` | Propostas documento (ADY) | `proposals.view` |
| `/apps/commercial/proposals/:id` | Detalhe + PDF revisável | `proposals.view` |
| `/apps/commercial/analytics` | Gestão — visão geral | `analytics.view` |
| `/apps/commercial/analytics/otd` | Gestão — OTD | `analytics.view` |
| `/apps/commercial/analytics/team` | Gestão — equipe | `analytics.view` (+ team) |
| `/apps/commercial/analytics/opportunities` | Oportunidades OV | `analytics.view` |
| `/apps/commercial/analytics/opportunities/:proposalNumber` | Ficha nativa da OV | `analytics.view` |
| `/apps/commercial/seller-portfolios` | Carteiras (admin) | `seller-portfolios.manage` |

Nav: `Início → Meu dia → Pedidos → Carteira → Propostas → Gestão → Carteiras†`

## Pedidos em aberto

Bancada operacional em `/apps/commercial/open-orders` (WF-02R). Contrato UX: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) § WF-02R / WF-02R-D.

### Deep links (URL compartilhável)

Sincronizados com o estado da página (`replaceState`); **não** apagam filtros no mount.

| Query | Efeito |
|-------|--------|
| `q` | Busca livre |
| `branch` | Filial |
| `client` (repetível) | Clientes selecionados |
| `?stock=com_estoque\|parcial\|sem_estoque` | Chip de atenção (estoque) |
| `?focus=late` | Chip «Atraso» |
| `date_start` / `date_end` | Intervalo de entrega (`YYYY-MM-DD`) |
| `sort` / `dir=asc\|desc` | Coluna allowlisted e direção da ordenação |
| `page` | Página da lista em memória; volta a 1 quando filtro, escopo ou sort muda |
| `?pedido=&linha=&filial=` | Link legado: localiza a linha e migra para a rota nativa |
| `seller_id` | Escopo de carteira, aceito só com `team_scope` e id de carteira válido |

A URL é restaurada em `popstate`; valores inválidos e defaults são removidos. O
`replaceState` canônico roda somente na rota exata `/open-orders`, nunca nas
fichas. Linha e OP preservam todos os parâmetros acima no retorno. A Home pode
emitir `?focus=late` / `?stock=…`. Helpers:
[`src/utils/openOrdersDeepLink.ts`](./src/utils/openOrdersDeepLink.ts).

Deep link inverso (produção → comercial): detalhe OTD com pedido preenchido → mesma URL `pedido/linha/filial` (ver README do `dashboard-production`).

## Minha carteira — WF-03R

A lista representa **clientes da carteira com pedidos de venda em aberto**; não é
a base SA1 completa. O `PageHero` concentra escopo, recortes e busca. Há dois
eixos independentes: **Foco** operacional (`focus`) e **Tendência** de NF
(`trend`). A lista usa `DataTable` no desktop e `DataRecordCard` no mobile, com
a mesma paginação e ordenação em memória. Colunas, ordem e larguras são
preferências locais versionadas; o gráfico de faturamento fica acima da lista,
com presets de calendário e `ChartToolbar` (dia/semana/mês/ano) na rota
existente `customers/billing-series`.

O estado compartilhável é sincronizado na URL por `replaceState`, sem recarregar
o MFE:

| Query | Efeito |
|-------|--------|
| `q` | Busca por cliente, código, loja, vendedor ou pedido |
| `focus=attention\|active\|no_sale_60` | Recorte operacional (atraso/parcial, em dia, sem venda 60d) |
| `trend=up\|stable\|down` | Tendência de faturamento; combina com o foco |
| `seller_id` | Carteira selecionada; aceito apenas para escopo de equipe e vendedor válido |
| `sort` | Ordenação allowlisted da carteira |
| `dir=asc\|desc` | Direção da ordenação |
| `page` | Página da lista em memória |

Somente `q`, `focus`, `trend`, `seller_id`, `sort`, `dir` e `page` são
preservados ao abrir e retornar do detalhe. Valores inválidos são removidos, e
os defaults `focus=all` / `trend=all` são omitidos da URL. `focus=growth` legado
vira `trend=up`; `focus=inactive` vira `all`. O contrato canônico está em
[`src/utils/customersListDeepLink.ts`](./src/utils/customersListDeepLink.ts).

As colunas visíveis por padrão seguem o WF-03R: Cliente, Última venda,
Fat. 12 meses, Tendência, Status, Em aberto, Atrasos e Próxima entrega.
Vendedor aparece por padrão somente no escopo de equipe; Cidade / UF permanece
oculta. Enrichment e faturamento são enviados em lotes determinísticos de no
máximo 200 clientes. Falha parcial preserva a lista base e explicita cobertura;
células sem cobertura mostram `Dado indisponível` e ficam vazias no Excel.

Presets são fixos nesta etapa; saved views nomeadas/compartilhadas ficam para uma
evolução com contrato de persistência e visibilidade próprio.

## Conta 360 — WF-04R

`/apps/commercial/customers/:codigo/:loja` é a página canônica da conta. Usa
`CommercialPagePath` para retornar à Minha carteira preservando `q`, `focus`,
`trend` e `seller_id`, e sincroniza a aba ativa em `?secao=`:

| `secao` | Conteúdo |
|---------|----------|
| omitida / `resumo` | Visão geral, indicadores, evolução, pedidos e atividades recentes |
| `pedidos` | Pedidos e linhas do cliente |
| `historico` | Faturamento, filtros e notas fiscais |
| `oportunidades` | Explicação e CTA interno permissionado |
| `atividades` | Timeline real e follow-ups |

Aliases legados (`faturamento`, `contatos`, `section`) são normalizados sem
apagar os demais parâmetros. Faturamento/notas e atividades usam **lazy loading
de dados por aba**: só consultam a fonte quando a seção correspondente está
ativa. Loading, erro, vazio, retry e atualização permanecem isolados por fonte.
Os CTAs aparecem apenas quando o usuário possui a capacidade necessária.

No resumo, `Pontos para conversa` apresenta badges derivados do snapshot real
(atrasos, cobertura cadastral parcial e valor em aberto), com vazio explícito
quando nenhum fato está disponível. Identidade, KPIs e próxima ação ficam no
`PageHero` da conta — sem rail sticky nem faixa de KPI duplicada. Pedidos e
previews abrem a página nativa da primeira
linha com chaves completas; o CTA `Ver OV n` só aparece com
`proposal_number` recebido no payload e `commercial.analytics.view`, sem probe
adicional e sem modal.

### Páginas da linha e da OP (WF-02R-D)

Snapshot e KPIs locais da linha não bloqueiam o loading dos extras. Ao abrir:

- Status fabril (`factory-status?branch=` da filial da linha) — chips PA/PI, expedição, capacidade de MP
- OPs: prefetch limitado + fetch on-demand; prazo OTD + tabela PI; timeline; apontamentos agregados
- BOM (`/products/{code}/structure`) com empty/erro/loading visíveis
- Helps: `SectionHintLabel` + textos em [`src/content/helpTooltips.ts`](./src/content/helpTooltips.ts) (linguagem de negócio, sem paths de API)

A linha abre diretamente na ficha SPA
`/open-orders/:filial/:pedido/:linha`, preservando o estado canônico completo da
lista (filtros, escopo, ordenação e página).
Links legados com `pedido`, `linha` e `filial` na query são resolvidos no escopo
carregado e substituídos pela rota nativa. A OP mantém
`/open-orders/:filial/:pedido/:linha/op/:op`, valida linha e OP na carteira e
reutiliza o mesmo `OpenOrdersProductionDetailContent` integral. Seu retorno aponta
para a página da linha; a troca entre múltiplas OPs atualiza a URL compartilhável.
O breadcrumb da OP inclui o produto após a carga e a própria ficha não repete o
CTA de abrir a OP atual.
Linha, OP, OV, proposta e conta usam `CommercialPagePath`.

**OV:** se a lista trouxer `proposal_number`, usa direto; senão `GET /commercial/proposals?search={pedido}&branch=` com match por filial+cliente ([`resolveProposalForOpenOrder.ts`](./src/utils/resolveProposalForOpenOrder.ts)). **Não** chamar `GET /proposals/{pedido}` como se pedido (`C5_NUM`) fosse número de OV.

### Página nativa da OV (WF-OV-D)

`/apps/commercial/analytics/opportunities/:proposalNumber` é o único detalhe da
OV. A página mostra status, datas, proposta, cliente/vendedor, itens, estrutura
dos produtos e histórico em timeline/tabela. `CommercialPagePath` volta para
Oportunidades preservando apenas os filtros internos allowlisted. Não existe
modal de OV nem navegação para outro plugin.

**Empty / freshness:** `portfolio.empty` → empty state + CTA Carteiras; toolbar com «Atualizado às HH:MM» após carga.

## APIs

| Base / path | Uso |
|-------------|-----|
| `/apps/commercial-api` | Carteiras, avatars, worklist, anexos, enrichment (`X-Delpi-Caller-App: commercial`) |
| `/apps/api-delpi/pedidos-venda-abertos/` | Lista pedidos em aberto (+ `portfolio.empty`) |
| `/apps/api-delpi/commercial/*` | KPIs, ROL, OTD, propostas OV |
| `/apps/api-delpi/commercial-proposals` | Documento ADY + PDF (EN; alias legado: `/propostas-comerciais`) |
| `GET /apps/api-delpi/products/{code}/factory-status` | Status fabril no modal (`?branch=`) |
| `GET /apps/api-delpi/production/orders/by-op/{op}` | Detalhe OP / OTD / PIs vinculadas |
| `GET /apps/api-delpi/production/appointments/by-op` | Apontamentos agregados da OP |
| `GET /apps/api-delpi/products/{code}/structure` | BOM no accordion |
| `GET /apps/api-delpi/commercial/proposals` | Probe OV (`?search=&branch=`) |

Paths **relativos** ao gateway. `commercial-api` com `redirect_slashes=False`.

## RBAC (capacidades)

| Permissão | Escopo |
|-----------|--------|
| `commercial.accounts.view` | Portal / pedidos / carteira (aliases legados) |
| `commercial.worklist.view` / `followups.manage` | Meu dia |
| `commercial.seller-portfolios.manage` | CRUD Carteiras (`is_admin`) |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | **Toda** a Gestão (`/analytics/*`) |
| `commercial.proposals.view` / `.export` | ADY + PDF (`/proposals/*`) |
| `commercial.accounts.team.view` | Filtro multi-vendedor / Gestão Equipe |
| `commercial.worklist.team.view` | Meu dia `scope=team` |

Filtro de equipe no MFE: `accounts.team.view || seller-portfolios.manage`. Team **sem** alias legado. Alias curto `commercial.propostas.*` ainda aceito na API.

Aplicação nas páginas deste fluxo:

- Minha carteira, Conta e OP: `commercial.accounts.view`;
- `seller_id`: somente `commercial.accounts.team.view` (ou administração de carteiras);
- OV e CTA Oportunidades: `commercial.analytics.view`;
- atividades: `commercial.worklist.view`;
- criar follow-up: `commercial.worklist.view` + `commercial.followups.manage`;
- Propostas ADY: `commercial.proposals.view`.

## Componentes compartilhados e composições

O MFE importa os primitivos de `@delpi/plugin-ui` por Module Federation e mantém
localmente apenas composição, responsividade e regra de domínio.

- Navegação/detalhe: `PagePath`, `UnderlineNav` em modo tabs, `PageHero`;
- dados: `DataTable`, `DataRecordCard`, `DetailCard`, `DetailFieldGrid`,
  `Timeline`, `StatusBadge`, `KpiCard` e `ChartCard`;
- operação: `SectionCard`, `ScopeChipBar`, `FilterBarShell`, `ChartToolbar`,
  `TableColumnVisibilityMenu`, `CompactPagination`, `ActionButton`,
  `StateBanner`, `EmptyState` e `LoadingActivityCard`;
- composições do domínio: `CustomersTable`, `CustomerDetailHeader`,
  `CustomerOrdersTable`, `CustomerBillingPanel`,
  `CustomerBillingSeriesChart`, `CustomerPurchaseEvolutionChart` e
  `OpenOrdersProductionDetailContent`.

Registrar no Core:

```bash
TOKEN=<jwt> BASE_URL=http://localhost ./plugins/commercial/scripts/register-manifest.sh
```

## Conteúdo PT

Help/tooltips/labels de UI em [`src/content/`](./src/content/) (`helpTooltips.ts` + bundles Gestão/Propostas). Não hardcode frases longas em JSX. No detalhe de pedidos, preferir hover no rótulo (`SectionHintLabel`), sem ícone «?» solto.

## Anexos de tarefa

Upload multipart → volume `${DELPI_DATA_HOST_DIR}/commercial-attachments`.

## Cutover F2c

Redirects F2c ativos nos gateways canônicos de produção e desenvolvimento por
`gateway/snippets/commercial-f2c-redirects.conf`. Artefatos operacionais:
[F2C-CUTOVER-RUNBOOK.md](../../docs/12-roadmap-e-evolucao/commercial/F2C-CUTOVER-RUNBOOK.md).

```bash
docker exec -it delpi-commercial-api python scripts/backfill_from_open_orders_legacy.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

## Dev

```bash
cd plugins/commercial
npm install
npm test
npm run lint
npm run build
```

Rebuild sequencial: `./infra/scripts/up-dev-sequential.sh --fase mfe --build commercial`

Smoke: `curl -I http://localhost/apps/commercial/assets/remoteEntry.js`

Smoke autenticado da API operacional:

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: commercial" \
  "http://localhost/apps/api-delpi/pedidos-venda-abertos/"
```

Validação do checkpoint Carteira/Conta:

```bash
cd plugins/commercial
npm test
npm run lint
npm run build
git diff --check
```

Baseline conhecido do `plugin-ui`: a suíte global possui 5 falhas preexistentes
fora deste escopo. A validação focada de `PagePath`, `DataRecordCard`,
`UnderlineNav` e `BackLink` passa; este checkpoint não mascara nem altera esses
componentes.

Rebuild operacional, quando necessário, deve usar o script sequencial acima;
como este checkpoint não altera `plugin-ui`, não há rebuild do remote do kit.

## Estrutura

```
src/
  api/           — clients commercial-api / api-delpi
  app/           — rotas, shell, navegação, portfolio scope
  components/    — open-orders (tabela, conteúdo de detalhe, strips) e UI compartilhada
  content/       — textos PT (help + analytics + proposals)
  features/      — home, my-day, open-orders, customers, analytics, proposals, seller-portfolios
  hooks/         — dashboard open-orders, extras do detalhe, layout
  pages/         — implementações de página (ex.: OpenOrdersPageImpl)
  utils/         — deep links, OV, timeline OP, formatação
```
