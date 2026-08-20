# Portal Comercial

Microfrontend federado do domínio comercial. Reúne, no próprio Portal Comercial,
as bancadas e fichas de Minha carteira, Conta 360, pedidos, OP, oportunidades OV,
propostas, Visão geral e Administração.

> Norte: [GESTAO-A-VISTA.md](../../docs/12-roadmap-e-evolucao/commercial/GESTAO-A-VISTA.md) · Perfis: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md) · Wireframes: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) (WF-02R / WF-02R-D) · Excelência lista+detalhe: [playbook-mfe-page-excellence.md](../../docs/05-plugin-system/playbook-mfe-page-excellence.md) · Ata × inventário: [ATA-MAPA-NECESSIDADES.md](../../docs/12-roadmap-e-evolucao/commercial/ATA-MAPA-NECESSIDADES.md) · **Ata alinhamento 2:** [ATA-ALINHAMENTO-AGO2026-2.md](../../docs/12-roadmap-e-evolucao/commercial/ATA-ALINHAMENTO-AGO2026-2.md)

Plugins irmãos (`pedidos-venda-abertos`, `dashboard-commercial`, `propostas-comerciais`) **coexistem** no menu. O `commercial` não usa iframe, remote, componente, URL nem fallback de interface de outro MFE: suas páginas são nativas e consomem apenas contratos HTTP.

### Gaps P0 (ata alinhamento 2)

W0 entregue — detalhe em [PARCIAL-INVENTARIO.md](../../docs/12-roadmap-e-evolucao/commercial/PARCIAL-INVENTARIO.md):

| ID | Entrega |
|----|---------|
| P0-META | Meta = soma proporcional por dia (SI); % incompleto = sum diária; YTD % = average |
| P0-LABEL | Chip MTD·YTD + Meta / Meta parcial / Meta acumulada |
| P0-RENAME | Timeline/ficha OP: «data de faturamento» |
| P0-OPP | Filtros Conta: status, período, OV, produto/família |
| P0-OTD-COPY | Help OTD = DatFat × prometida |
| P0-FAV | Favoritos no `PluginShell` (strip em todas as rotas) |

**GR de Vendas** = [tv-dashboard](../tv-dashboard/README.md) (não feature deste MFE; **sem** atalho Home/ficha para o TV).

```text
Portal Minha DELPI
  → MFE commercial (rotas SPA + RBAC + @delpi/plugin-ui)
    → commercial-api (carteiras, atividades, anexos e enrichment)
    → api-delpi (pedidos, faturamento, produção, OV e ADY)
```

## Rotas UI

Rotas com parâmetros (`:userId`, `:codigo`, …) são resolvidas pelo SPA — **não** entram no manifesto Core (`PATH_RE` = `^/[-a-z0-9/]*$`).

| Rota | Descrição | Permissão |
|------|-----------|-----------|
| `/apps/commercial` | Início — hero + eventos do dia + launcher de funcionalidades | `commercial.access` |
| `/apps/commercial/overview` | Visão geral — KPIs (incl. carteira aberta), filtros/período, ROL + YoY, funil, série hit rate + YoY | `commercial.access` |
| `/apps/commercial/my-tasks` (alias `/my-day`) | Minhas tarefas — worklist | `commercial.access` |
| `/apps/commercial/users/:userId` | Perfil de usuário (SPA; não declarado no manifesto) | `commercial.access` |
| `/apps/commercial/open-orders` | Pedidos em aberto (TOTVS) | `commercial.access` |
| `/apps/commercial/open-orders/:filial/:pedido/:linha` | Ficha nativa da linha do pedido | `commercial.access` |
| `/apps/commercial/open-orders/:filial/:pedido/:linha/op/:op` | Ficha nativa da OP vinculada à linha | `commercial.access` |
| `/apps/commercial/customers` | Carteira de clientes | `commercial.access` |
| `/apps/commercial/customers/:codigo/:loja` | Conta 360 híbrida | `commercial.access` |
| `/apps/commercial/proposals` | Propostas documento (ADY) | `commercial.access` |
| `/apps/commercial/proposals/:id` | Detalhe + PDF revisável | `commercial.access` |
| `/apps/commercial/analytics` (legado) | Redireciona para a Visão geral | `commercial.access` |
| `/apps/commercial/analytics/otd` | Pontualidade (OTD) — drill da Visão geral | `commercial.access` |
| `/apps/commercial/analytics/team` | Equipe — redireciona Administração | `commercial.manage` |
| `/apps/commercial/analytics/opportunities` | Oportunidades OV | `commercial.access` |
| `/apps/commercial/analytics/opportunities/:proposalNumber` | Ficha nativa da OV | `commercial.access` |
| `/apps/commercial/administration` | Administração — Painel | `commercial.manage` |
| `/apps/commercial/administration/seller-portfolios` | Administração — Carteiras | `commercial.manage` |
| `/apps/commercial/administration/seller-portfolios/:id` | Detalhe de carteira | `commercial.manage` |
| `/apps/commercial/administration/team` | Administração — Equipe (presença online via WS) | `commercial.manage` |
| `/apps/commercial/administration/groups` | Administração — Grupos operacionais | `commercial.manage` |
| `/apps/commercial/seller-portfolios` (legado) | Alias → Carteiras do hub | `commercial.manage` |
| `/apps/commercial/interaction-rooms` | Inbox da sala de interação (lista) | `commercial.access` |
| `/apps/commercial/interaction-rooms/:roomId` | Thread da sala (SPA; não declarado no manifesto) | `commercial.access` |

Nav de topo: `Início → Visão geral† → Minhas tarefas‡ → Meus pedidos → Minha Carteira → Administração°`
(†‡ `commercial.access` · ° `commercial.manage`). Propostas, OTD, Oportunidades
e Equipe analytics saem do topo: chega-se a elas pelo launcher do Início ou pelos drills da Visão geral.
Alias `/administration/members` → Equipe; detalhe legado `/seller-portfolios/:id` permanece válido.

## Pedidos em aberto

Bancada operacional em `/apps/commercial/open-orders` (WF-02R). Contrato UX: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) § WF-02R / WF-02R-D.

Chip «Pode faturar» e badge da nav **Meus pedidos** usam a mesma regra: estoque **FIFO** calculado no BFF (`estoque_alocado` / `kanbanStageCounts.ready_to_invoice`). O MFE reaplica `allocateStockToOrders` só para previsão de OP — não para a contagem do badge.

### Deep links (URL compartilhável)

Sincronizados com o estado da página (`replaceState`); **não** apagam filtros no mount.

| Query | Efeito |
|-------|--------|
| `q` | Busca livre |
| `branch` | Filial |
| `client` (repetível) | Clientes selecionados |
| `?stock=com_estoque\|parcial\|sem_estoque` | Chip de atenção (estoque FIFO: alocado ≥ saldo) |
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
com presets de calendário **paridade Visão geral** (incl. mês passado),
`ChartToolbar` (dia/semana/mês/ano) e toggle **Comparar ano anterior** (2ª
chamada a `customers/billing-series` com datas −1 ano — sem rota nova).

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

**Histórico da carteira:** um único `SectionCard` colapsável (padrão fechado)
abaixo da lista (`MyPortfolioAuditSection`) com `GET /seller-portfolios/{id}/audit`
(membro autorizado). Com filtro «Todas» e mais de uma carteira, o seletor fica
no corpo do mesmo card. Eventos WebSocket `portfolio.changed` disparam toast e
refetch do histórico.

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
| `contatos` | Contato TOTVS somente leitura e contatos locais com CRUD |
| `atividades` | Timeline real e follow-ups |

Aliases legados (`faturamento`, `section`) são normalizados sem
apagar os demais parâmetros. Faturamento/notas e atividades usam **lazy loading
de dados por aba**: só consultam a fonte quando a seção correspondente está
ativa. Loading, erro, vazio, retry e atualização permanecem isolados por fonte.
Os CTAs aparecem apenas quando o usuário possui a capacidade necessária.

A seção Contatos consome exclusivamente a `commercial-api`: o bundle
`GET /customers/{code}/{store}/contacts-bundle` combina o contato cadastral
TOTVS com os contatos locais, mantidos por `POST/PATCH/DELETE .../contacts`.

No resumo, `Pontos para conversa` apresenta badges derivados do snapshot real
(atrasos, cobertura cadastral parcial e valor em aberto), com vazio explícito
quando nenhum fato está disponível. Identidade, KPIs e próxima ação ficam no
`PageHero` da conta — sem rail sticky nem faixa de KPI duplicada. Pedidos e
previews abrem a página nativa da primeira
linha com chaves completas; o CTA `Ver OV n` só aparece com
`proposal_number` recebido no payload e `commercial.access`, sem probe
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

## Administração de carteiras — WF-05R

`/apps/commercial/administration/seller-portfolios` é lista + detalhe (kit). Alias
legado `/seller-portfolios`. O estado compartilhável usa `replaceState` nestas rotas:

| Query | Efeito |
|-------|--------|
| `q` | Busca por nome, usuário ou e-mail |
| `filter=active\|inactive\|overlapping\|uncovered` | Recorte de situação, overlapping ou painel de clientes sem cobertura (`all` é omitido) |
| `view=list\|org` | Lista ou organização |
| `axis=portfolio\|person` | Eixo da visão organização |

Detalhe: `/administration/seller-portfolios/:id` (query da lista preservada). Legado `?id=` na lista migra para o path.

**E6.1 cobertura:** `GET /seller-portfolios/coverage-audit` (manage) — overlapping entre carteiras ativas; gap (sem cobertura) usa universo de clientes com pedido aberto (`gap.universe=open_orders`). Chip «Sem cobertura» (`?filter=uncovered`) troca a lista por painel de clientes descobertos. Ao vincular cliente já presente em outra carteira ativa, o `POST .../customers` mantém o vínculo e devolve `coverage_warning` (aviso soft).

**E6.2 carga:** `GET /seller-portfolios/load-summary` — `customer_count` / `member_count` por carteira e por pessoa; `open_value` / `attention_count` via agregação TOTVS (`totvs_metrics.available`); fallback «—» se a chamada falhar.

**E6.3 histórico:** `GET /seller-portfolios/{id}/audit` (manage ou `audit.view`) — timeline paginada do `audit_log` (membros, responsável, transferência, ativar/inativar) no detalhe da carteira.

**E6.4 compartilhado:** `POST /seller-portfolios/customer-coverage` (accounts.view) — batch por códigos no escopo; Minha Carteira / Conta exibem badge «Compartilhado» + «Também em: …».

**E6.5 bulk + export:** `POST /seller-portfolios/transfer-customers-bulk` — wizard origem→clientes→destino; botão **Exportar matriz** (Excel client-side a partir do load-summary).

**E7 (backlog, não implementar aqui):** mapa territorial, AI carve, rotate de leads, inbox e-mail — ver [UX-E-TASKS-EVOLUTION.md § 6](../../docs/12-roadmap-e-evolucao/commercial/UX-E-TASKS-EVOLUTION.md).

`DELETE /seller-portfolios/{id}` **inativa** (soft). Excluir de verdade é
`DELETE /seller-portfolios/{id}/permanent` (`purge_seller_portfolio`): apaga a
linha, desvincula clientes (`ON DELETE CASCADE`) e libera o `user_id`. Contrato
em [`src/utils/sellerPortfoliosDeepLink.ts`](./src/utils/sellerPortfoliosDeepLink.ts).

## APIs

| Base / path | Uso |
|-------------|-----|
| `/apps/commercial-api` | Carteiras, avatars, worklist, anexos, enrichment, open-orders BFF |
| `/apps/commercial-api/analytics/*` | KPIs, ROL, OTD, propostas OV (escopo `seller_id`/membership no BFF) |
| `/apps/commercial-api/proposal-documents*` | Documento ADY + PDF |
| `/apps/commercial-api/production/*` e `/products/*` | OP, apontamentos, status fabril, BOM |
| `/apps/commercial-api/interaction-rooms*` | Sala de interação (inbox, resolve, mensagens, pins, tarefas) |

O MFE **nunca** chama `/apps/api-delpi` — só a `commercial-api` faz gateway TOTVS. Diretriz: `.cursor/rules/mfe-own-api-no-direct-api-delpi.mdc`.

Paths **relativos** ao gateway. `commercial-api` com `redirect_slashes=False`.

## Sala de interação

Inbox e thread nativos no **mesmo workspace** (WF-SALA-01): lista ~20% | conversa ~80%. Sem sala selecionada, a inbox ocupa 100% (sem coluna vazia). Na thread, o painel **Neste chat** (`RoomSidePanel`) abre à direita e encolhe msgs+composer; fechado, some. Não é terceira coluna da inbox. Painel embutido na ficha do pedido/conta/OV/OP resolve a sala sob demanda (`POST …/resolve`). Chrome só via `@delpi/plugin-ui` (`ResizableColumns`, `RoomInboxList`, `MessageThread`, `MentionComposer`, `RoomSidePanel`, `RoomContextPanel`, `ReactionBar`, `EmojiInsertMenu`).

**Entregue (E1–E7):** fill viewport, lista 100% sem sala, chips no hero, Contexto à direita, composer markdown + mentions, anexos na bolha, reply (`parent_id`), editar in-place, excluir com confirm host-contained, reações, inbox empty/loading/preview. Roadmap e fecho: [ROADMAP-INTERACTION-ROOM.md](../../docs/12-roadmap-e-evolucao/commercial/ROADMAP-INTERACTION-ROOM.md). **Próximo:** E8 docs (contrato/catálogo). Smoke de containers se o Docker estiver offline no host — rebuild `plugin-ui` antes do MFE `commercial`.

Rebuild: remote `plugin-ui` **antes** do MFE `dashboard-commercial` (`./infra/scripts/up-dev-sequential.sh`).

Contrato HTTP completo: [API-ROUTES.md § 3.21](../../docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md). Paths EN (prefixo `/interaction-rooms`):

| Método | Path relativo | `operationId` |
|--------|---------------|---------------|
| GET | `/interaction-rooms` | `list_interaction_rooms` |
| POST | `/interaction-rooms/resolve` | `resolve_interaction_room` |
| GET | `/interaction-rooms/{room_id}` | `get_interaction_room` |
| GET | `/interaction-rooms/{room_id}/members` | `list_interaction_room_members` |
| POST | `/interaction-rooms/{room_id}/members` | `add_interaction_room_member` |
| DELETE | `/interaction-rooms/{room_id}/members/{user_id}` | `remove_interaction_room_member` |
| POST | `/interaction-rooms/{room_id}/read` | `mark_interaction_room_read` |
| GET | `/interaction-rooms/{room_id}/messages` | `list_interaction_messages` |
| POST | `/interaction-rooms/{room_id}/messages` | `post_interaction_message` |
| PATCH | `/interaction-rooms/{room_id}/messages/{message_id}` | `update_interaction_message` |
| DELETE | `/interaction-rooms/{room_id}/messages/{message_id}` | `delete_interaction_message` |
| PUT | `/interaction-rooms/{room_id}/messages/{message_id}/reactions/{code}` | `set_interaction_message_reaction` |
| DELETE | `/interaction-rooms/{room_id}/messages/{message_id}/reactions/{code}` | `clear_interaction_message_reaction` |
| GET | `/interaction-rooms/{room_id}/pins` | `list_interaction_room_pins` |
| POST | `/interaction-rooms/{room_id}/messages/{message_id}/pin` | `pin_interaction_message` |
| DELETE | `/interaction-rooms/{room_id}/messages/{message_id}/pin` | `unpin_interaction_message` |
| GET | `/interaction-rooms/mention-suggest` | `suggest_interaction_mentions` |
| GET | `/interaction-rooms/entity-preview` | `preview_interaction_entity` |
| POST | `/interaction-rooms/{room_id}/messages/{message_id}/tasks` | `create_task_from_interaction_message` |

Anexos de mensagem: `owner_type=room_message` em `/attachments` (mesmo volume `commercial-attachments`). Publisher interno `post_system_message` (`otd_event` / `process_stage`) **não** tem rota HTTP.

RBAC: **`commercial.access` (global)** — inbox e thread para todos com acesso ao Portal; **sem** permission code novo. Unfurl de entidade continua fail-closed por carteira. Tempo real: mesmo WS `/commercial/realtime/ws` — thread via `subscribe` `room:{uuid}`; inbox via handshake `interaction` + `room.inbox.changed`.

## RBAC (capacidades)

Catálogo condensado — **3 codes**. Detalhe e política para features novas: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md).

| Permissão | Escopo |
|-----------|--------|
| `commercial.access` | Funcionalidades do produto (pedidos, tarefas, visão geral, propostas, …) |
| `commercial.manage` | Administração + vê **todas** as carteiras (escopo irrestrito) |
| `commercial.billing.notify` | Destinatário da notificação «Pronto para faturar» (não libera telas) |

Notificações de **tarefas** usam só envolvidos (`userIds`) + categoria catálogo `commercial_tasks` («Tarefas comerciais») — **sem** permission code novo. Job: `POST /integrations/jobs/task-due-scan` (`manage`). Faturar permanece em categoria `commercial`.

Minha Carteira na topbar: membership **ou** `manage`. Pedidos sem membership: consolidado (todos os clientes).

Antes de criar permission nova: preferir `access` ou `manage`; code específico só para efeito estreito (ver PERFIS).

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

Help/tooltips/labels de UI em [`src/content/`](./src/content/) (`helpTooltips.ts`, `shellNav`, `homeLauncher`, `overviewMetricsCatalog`, `administration`). Não hardcode frases longas em JSX. No detalhe de pedidos, preferir hover no rótulo (`SectionHintLabel`), sem ícone «?» solto.

Cobertura de `hint` / `headerHint` em campos e colunas: inventário e isenções em [`docs/12-roadmap-e-evolucao/commercial/HELP-COVERAGE.md`](../../docs/12-roadmap-e-evolucao/commercial/HELP-COVERAGE.md). Auditoria: `node scripts/audit_help_coverage.mjs` + gate `src/content/helpCoverage.structural.test.mjs` (C16 em `helpTooltips.structural.test.mjs`).

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

Smoke autenticado do BFF commercial (open-orders):

```bash
curl -H "Authorization: Bearer $TOKEN" \
  -H "X-Delpi-Caller-App: commercial" \
  "http://localhost/apps/commercial-api/open-orders/"
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
  content/       — textos PT (help + nav de topo + launcher + analytics + proposals)
  features/      — home, overview, my-day (Minhas tarefas), open-orders, customers, analytics, proposals, administration, seller-portfolios
  hooks/         — dashboard open-orders, extras do detalhe, layout
  pages/         — implementações de página (ex.: OpenOrdersPageImpl)
  utils/         — deep links, OV, timeline OP, formatação
```
