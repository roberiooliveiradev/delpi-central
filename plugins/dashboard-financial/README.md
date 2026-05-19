# Dashboard Financeiro

Microfrontend (Module Federation) com indicadores financeiros da **api-delpi**:

| Indicador | Endpoint |
|-----------|----------|
| ROL | `GET /financial/rol` |
| EBITDA / ROL | `GET /financial/ebitda_pct` |
| Custos fixos / ROL | `GET /financial/fixed_cost_pct` |
| PMR (dias) | `GET /financial/pmr` |

Base da API no gateway: `/apps/api-delpi/financial` (alias legado: `/apps/api-delpi/finacial`).

## Permissão

- `dashboard-financial.view` (ou `api-delpi.access`)

## Desenvolvimento

```bash
cd plugins/dashboard-financial
npm install
npm run dev
```

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-financial api-delpi
docker compose restart gateway
```

Registro do manifesto:

```bash
TOKEN=<jwt> ./plugins/dashboard-financial/scripts/register-manifest.sh
```
