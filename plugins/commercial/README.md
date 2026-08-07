# Portal Comercial

Microfrontend federado do domínio comercial — UX canônica a evoluir (**consolidação nativa**).

> Norte: [GESTAO-A-VISTA.md](../../docs/12-roadmap-e-evolucao/commercial/GESTAO-A-VISTA.md) · Perfis: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md)

Plugins irmãos (`pedidos-venda-abertos`, `dashboard-commercial`, `propostas-comerciais`) **coexistem** no menu; o Portal **não** hosteia nem deep-linka esses MFEs como produto.

## Rotas UI

| Rota | Descrição | Permissão |
|------|-----------|-----------|
| `/apps/commercial` | Início — hero + alertas + KPIs + teaser Gestão | `accounts.view` |
| `/apps/commercial/my-day` | Meu dia — worklist | `worklist.view` |
| `/apps/commercial/open-orders` | Pedidos em aberto (TOTVS) | `accounts.view` |
| `/apps/commercial/customers` | Carteira de clientes | `accounts.view` |
| `/apps/commercial/customers/:codigo/:loja` | Conta 360 híbrida | `accounts.view` |
| `/apps/commercial/propostas` | Propostas documento (ADY) | `propostas.view` |
| `/apps/commercial/propostas/:id` | Detalhe + PDF revisável | `propostas.view` |
| `/apps/commercial/gestao` | Gestão — visão geral | `analytics.view` |
| `/apps/commercial/gestao/otd` | Gestão — OTD | `analytics.view` |
| `/apps/commercial/gestao/equipe` | Gestão — equipe | `analytics.view` (+ team) |
| `/apps/commercial/gestao/oportunidades` | Oportunidades OV | `analytics.view` |
| `/apps/commercial/seller-portfolios` | Carteiras (admin) | `seller-portfolios.manage` |

Nav: `Início → Meu dia → Pedidos → Carteira → Propostas → Gestão → Carteiras†`

## APIs

| Base | Uso |
|------|-----|
| `/apps/commercial-api` | Carteiras, avatars, worklist, anexos, enrichment (`X-Delpi-Caller-App: commercial`) |
| `/apps/api-delpi/pedidos-venda-abertos/` | Pedidos em aberto (barra final) |
| `/apps/api-delpi/commercial/*` | KPIs, ROL, OTD, propostas OV |
| `/apps/api-delpi/propostas-comerciais` | Documento ADY + PDF |

Paths **relativos** ao gateway. `commercial-api` com `redirect_slashes=False`.

## RBAC (capacidades)

| Permissão | Escopo |
|-----------|--------|
| `commercial.accounts.view` | Portal / pedidos / carteira (aliases PVA / api-delpi) |
| `commercial.worklist.view` / `followups.manage` | Meu dia |
| `commercial.seller-portfolios.manage` | CRUD Carteiras (`is_admin`) |
| `commercial.audit.view` | Auditoria |
| `commercial.analytics.view` | **Toda** a Gestão |
| `commercial.propostas.view` / `.export` | ADY + PDF |
| `commercial.accounts.team.view` | Filtro multi-vendedor / Gestão Equipe |
| `commercial.worklist.team.view` | Meu dia `scope=team` |

Filtro de equipe no MFE: `accounts.team.view || seller-portfolios.manage`. Team **sem** alias legado.

Registrar no Core:

```bash
TOKEN=<jwt> BASE_URL=http://localhost ./plugins/commercial/scripts/register-manifest.sh
```

## Conteúdo PT

Help/tooltips/labels de UI em [`src/content/`](./src/content/) (`helpTooltips.ts` + bundles Gestão/Propostas). Não hardcode frases longas em JSX.

## Anexos de tarefa

Upload multipart → volume `${DELPI_DATA_HOST_DIR}/commercial-attachments`.

## Cutover PVA (F2c)

**Adiado** até o Comercial superar o PVA e pedido explícito. Artefatos: [F2C-CUTOVER-RUNBOOK.md](../../docs/12-roadmap-e-evolucao/commercial/F2C-CUTOVER-RUNBOOK.md).

```bash
docker exec -it delpi-commercial-api python scripts/backfill_from_pedidos_venda_abertos.py
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
  content/       — textos PT (help + gestao + propostas)
  features/      — home, my-day, open-orders, customers, gestao, propostas, seller-portfolios
  shared/        — formatadores
```
