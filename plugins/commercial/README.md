# Portal Comercial

Microfrontend federado do domínio comercial — paridade F2b com o Portal do Vendedor (`pedidos-venda-abertos`) + **Wave G+** (UnderlineNav, Meu dia CRM, Home gestão).

## Rotas UI

| Rota | Descrição |
|------|-----------|
| `/apps/commercial` | Início — hero + alertas + KPIs (+ gestão admin) |
| `/apps/commercial/my-day` | Meu dia — worklist / follow-ups (`?createTask=1&customer_code=&customer_store=`) |
| `/apps/commercial/open-orders` | Pedidos de venda em aberto (TOTVS) |
| `/apps/commercial/customers` | Minha carteira de clientes |
| `/apps/commercial/customers/:codigo/:loja` | Conta 360 (+ Agendar follow-up) |
| `/apps/commercial/seller-portfolios` | Administração de carteiras |

## APIs

| Base | Uso |
|------|-----|
| `/apps/commercial-api` | Carteiras, avatars, worklist/tasks, enrichment (`X-Delpi-Caller-App: commercial`) |
| `/apps/api-delpi/pedidos-venda-abertos/` | Pedidos em aberto (read TOTVS) — **barra final** (evita Mixed Content atrás de HTTPS) |

Clients usam paths **relativos** ao gateway. A `commercial-api` roda com `redirect_slashes=False` (list/create de `seller-portfolios` **sem** barra final).

## RBAC

| Permissão | Escopo |
|-----------|--------|
| `commercial.accounts.view` | Acesso geral (alias cutover: `pedidos-venda-abertos.access`) |
| `commercial.worklist.view` | Meu dia / `GET /me/worklist` |
| `commercial.followups.manage` | Criar/concluir tarefas e atividades |
| `commercial.seller-portfolios.manage` | Admin carteiras (alias: `pedidos-venda-abertos.admin`) |
| `commercial.audit.view` | Auditoria (quando exposta) |

Papéis sugeridos: [PERFIS-E-PERMISSOES.md](../../docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md).

Registrar no Core:

```bash
TOKEN=<jwt> BASE_URL=http://localhost ./plugins/commercial/scripts/register-manifest.sh
```

## Ajuda (balões)

Textos dos `HelpTooltip` / `SectionCard.hint` / `titleHint` ficam em [`src/content/helpTooltips.ts`](./src/content/helpTooltips.ts) (`CM_HELP`). Não hardcode frases de explicação nos componentes.

## Cutover de carteira

Default Compose: `COMMERCIAL_PORTFOLIO_SOURCE=commercial` (após backfill).

```bash
docker exec -it delpi-commercial-api python scripts/backfill_from_pedidos_venda_abertos.py
./commercial-api/scripts/reconcile_portfolio_counts.sh
```

Não há dual-write com o schema legado. Paridade UX F2b no MFE; F2c (ocultar PVA) após homologação — [F2C-CUTOVER-RUNBOOK.md](../../docs/12-roadmap-e-evolucao/commercial/F2C-CUTOVER-RUNBOOK.md).

## Dev

```bash
cd plugins/commercial
npm install
npm run dev
npm run build
```

Smoke federado: `curl -I http://localhost/apps/commercial/assets/remoteEntry.js`

## Estrutura

```
src/
  api/           — httpClient + clients commercial-api / api-delpi
  app/           — rotas, shell, navegação, portfolio scope
  features/      — home, my-day, open-orders, customers, seller-portfolios
  shared/        — formatadores
```
