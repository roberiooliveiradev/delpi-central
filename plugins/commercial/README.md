# Portal Comercial

Microfrontend federado do domínio comercial — UX canônica a evoluir (**consolidação nativa**).

> Norte: [GESTAO-A-VISTA.md](../../docs/12-roadmap-e-evolucao/commercial/GESTAO-A-VISTA.md) · Perfis: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md) · Wireframes: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) (WF-02R / WF-02R-D)

Plugins irmãos (`pedidos-venda-abertos`, `dashboard-commercial`, `propostas-comerciais`) **coexistem** no menu; o Portal **não** hosteia nem deep-linka esses MFEs como produto.

## Rotas UI

| Rota | Descrição | Permissão |
|------|-----------|-----------|
| `/apps/commercial` | Início — hero + alertas + KPIs + teaser Gestão | `accounts.view` |
| `/apps/commercial/my-day` | Meu dia — worklist | `worklist.view` |
| `/apps/commercial/open-orders` | Pedidos em aberto (TOTVS) | `accounts.view` |
| `/apps/commercial/customers` | Carteira de clientes | `accounts.view` |
| `/apps/commercial/customers/:codigo/:loja` | Conta 360 híbrida | `accounts.view` |
| `/apps/commercial/proposals` | Propostas documento (ADY) | `proposals.view` |
| `/apps/commercial/proposals/:id` | Detalhe + PDF revisável | `proposals.view` |
| `/apps/commercial/analytics` | Gestão — visão geral | `analytics.view` |
| `/apps/commercial/analytics/otd` | Gestão — OTD | `analytics.view` |
| `/apps/commercial/analytics/team` | Gestão — equipe | `analytics.view` (+ team) |
| `/apps/commercial/analytics/opportunities` | Oportunidades OV | `analytics.view` |
| `/apps/commercial/seller-portfolios` | Carteiras (admin) | `seller-portfolios.manage` |

Nav: `Início → Meu dia → Pedidos → Carteira → Propostas → Gestão → Carteiras†`

## Pedidos em aberto

Bancada operacional em `/apps/commercial/open-orders` (WF-02R). Contrato UX: [WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/commercial/WIREFRAMES.md) § WF-02R / WF-02R-D.

### Deep links (URL compartilhável)

Sincronizados com o estado da página (`replaceState`); **não** apagam filtros no mount.

| Query | Efeito |
|-------|--------|
| `?stock=com_estoque\|parcial\|sem_estoque` | Chip de atenção (estoque) |
| `?focus=late` | Chip «Atraso» |
| `?pedido=&linha=&filial=` | Abre o modal da linha; ao fechar, limpa só esses params |
| `seller_id` | Escopo de carteira (já existente) |

A Home pode emitir `?focus=late` / `?stock=…`. Helpers: [`src/utils/openOrdersDeepLink.ts`](./src/utils/openOrdersDeepLink.ts).

Deep link inverso (produção → comercial): detalhe OTD com pedido preenchido → mesma URL `pedido/linha/filial` (ver README do `dashboard-production`).

### Modal Detalhe da linha (WF-02R-D)

Snapshot e KPIs locais da linha não bloqueiam o loading dos extras. Ao abrir:

- Status fabril (`factory-status?branch=` da filial da linha) — chips PA/PI, expedição, capacidade de MP
- OPs: prefetch limitado + fetch on-demand; prazo OTD + tabela PI; timeline; apontamentos agregados
- BOM (`/products/{code}/structure`) com empty/erro/loading visíveis
- Helps: `SectionHintLabel` + textos em [`src/content/helpTooltips.ts`](./src/content/helpTooltips.ts) (linguagem de negócio, sem paths de API)

**OV:** se a lista trouxer `proposal_number`, usa direto; senão `GET /commercial/proposals?search={pedido}&branch=` com match por filial+cliente ([`resolveProposalForOpenOrder.ts`](./src/utils/resolveProposalForOpenOrder.ts)). **Não** chamar `GET /proposals/{pedido}` como se pedido (`C5_NUM`) fosse número de OV.

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
| `commercial.accounts.view` | Portal / pedidos / carteira (aliases PVA / api-delpi) |
| `commercial.worklist.view` / `followups.manage` | Meu dia |
| `commercial.seller-portfolios.manage` | CRUD Carteiras (`is_admin`) |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | **Toda** a Gestão (`/analytics/*`) |
| `commercial.proposals.view` / `.export` | ADY + PDF (`/proposals/*`) |
| `commercial.accounts.team.view` | Filtro multi-vendedor / Gestão Equipe |
| `commercial.worklist.team.view` | Meu dia `scope=team` |

Filtro de equipe no MFE: `accounts.team.view || seller-portfolios.manage`. Team **sem** alias PVA. Alias curto `commercial.propostas.*` ainda aceito na API.

Registrar no Core:

```bash
TOKEN=<jwt> BASE_URL=http://localhost ./plugins/commercial/scripts/register-manifest.sh
```

## Conteúdo PT

Help/tooltips/labels de UI em [`src/content/`](./src/content/) (`helpTooltips.ts` + bundles Gestão/Propostas). Não hardcode frases longas em JSX. No modal de pedidos, preferir hover no rótulo (`SectionHintLabel`), sem ícone «?» solto.

## Anexos de tarefa

Upload multipart → volume `${DELPI_DATA_HOST_DIR}/commercial-attachments`.

## Cutover PVA (F2c)

**Adiado** até o Comercial superar o PVA e pedido explícito. Artefatos: [F2C-CUTOVER-RUNBOOK.md](../../docs/12-roadmap-e-evolucao/commercial/F2C-CUTOVER-RUNBOOK.md).

```bash
docker exec -it delpi-commercial-api python scripts/backfill_from_open_orders_legacy.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

## Dev

```bash
cd plugins/commercial
npm install
npm run build
```

Rebuild sequencial: `./infra/scripts/up-dev-sequential.sh --fase mfe --build commercial`

Smoke: `curl -I http://localhost/apps/commercial/assets/remoteEntry.js`

## Estrutura

```
src/
  api/           — clients commercial-api / api-delpi
  app/           — rotas, shell, navegação, portfolio scope
  components/    — open-orders (tabela, modal, strips) e UI compartilhada
  content/       — textos PT (help + analytics + proposals)
  features/      — home, my-day, open-orders, customers, analytics, proposals, seller-portfolios
  hooks/         — dashboard open-orders, extras do modal, layout
  pages/         — implementações de página (ex.: OpenOrdersPageImpl)
  utils/         — deep links, OV, timeline OP, formatação
```
