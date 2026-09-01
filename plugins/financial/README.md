# Portal Financeiro (MFE)

Microfrontend federado do **Portal Financeiro** (`id`: `financial`): shell com rail de subplugins — gestão à vista, faturamento (ROL), inadimplência, despesas por centro de custo e indicadores IDD/IGD.

## Fluxo técnico

```text
Portal → financial (remoteEntry.js)
      → /apps/financial-api/*
      → api-delpi (/financeiro/*, /financial/*) e strategic-indicators-api
      → @delpi/plugin-ui (Module Federation)
```

O MFE **não** chama `/apps/api-delpi`. Header: `X-Delpi-Caller-App: financial`.

## Rotas UI

| Rota | Tela |
|------|------|
| `/apps/financial?branch=` | Gestão à vista (ROL, EBITDA, custo fixo, PMR, inadimplência, top CC, IDD). Clique no card de ROL para o faturamento. |
| `…/billing?branch=&startDate=&endDate=&granularity=` | Faturamento: composição da ROL, evolução, unidades e ranking de clientes |
| `…/delinquency?startDate=&endDate=&q=&customer=&status=` | Inadimplência (consolidada na origem — sem seletor de filial) |
| `…/cost-centers?branch=&startDate=&endDate=&costCenter=&supplier=` | Despesas por centro de custo |
| `…/indicators?branch=` | IDD do Financeiro e IGD da Delpi |

Subplugins futuros (`budget`, `cash-flow`) aparecem na rail como *Em breve*.

Plugins legados (`financeiro-inadimplencia`, `financeiro-centro-custo`, `dashboard-financial`) continuam registrados e intocados.

## API

Base: `/apps/financial-api`

| Método | Path | Uso |
|--------|------|-----|
| GET | `/health` | Liveness |
| GET | `/subplugins` | Catálogo filtrado por permissão + `capabilities.export` |
| GET | `/overview?branch=&startDate=&endDate=` | Gestão à vista (blocos isolados) |
| GET | `/billing/dashboard?branch=&startDate=&endDate=&granularity=` | Faturamento (ROL + série + clientes + unidades) |
| GET | `/billing/invoices?branch=&startDate=&endDate=` | Extrato de notas da ROL (Excel de conferência; exige `financial.export`) |
| GET | `/delinquency/{summary,monthly,aging,customers,titles}` | Inadimplência |
| GET | `/cost-centers/{filters,summary,series,ranking-cost-centers,ranking-suppliers,entries}` | Despesas por CC |
| GET | `/indicators/{department,global}` | IDD / IGD |

## Permissões

- `financial.access` — abrir o portal
- `financial.delinquency.view` / `financial.cost-centers.view` / `financial.indicators.view`
- `financial.export` — Excel de clientes e lançamentos
- `financial.view.filial-01` / `financial.view.filial-02` — gate de filial no BFF

Consultas consolidadas (`branch=all` e a inadimplência) exigem as **duas** filiais.

## Dev e smoke

```bash
cd plugins/financial
npm install
npm run test
npm run build

# Stack
./infra/scripts/up-dev-sequential.sh --fase api --build financial-api
./infra/scripts/up-dev-sequential.sh --fase mfe --build financial

curl -sS http://localhost/apps/financial-api/health
curl -sS http://localhost/apps/financial/assets/remoteEntry.js | head

TOKEN=… ./plugins/financial/scripts/register-manifest.sh
```

## Estrutura `src/`

```text
src/
  api/           httpClient + financialApi (só /apps/financial-api)
  components/    shell, rail, header, dialog host-contained
  content/       copy + helpTooltips (sem path de API)
  hooks/         overview, delinquency, cost-centers, indicators
  pages/         gestão à vista, faturamento, inadimplência, centros de custo, indicadores
  utils/         rota, query, formatação, Excel
```
