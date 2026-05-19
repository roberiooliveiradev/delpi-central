# Dashboard Produção

Microfrontend com indicadores de produção via **api-delpi** (`/production`).

## KPIs

| Indicador | Endpoint | Fonte |
|-----------|----------|--------|
| MO direta / ROL | `GET /production/direct_labor_cost_pct` | Google Sheets + ROL TOTVS |
| Custo produção / ROL | `GET /production/production_cost_pct` | Google Sheets + ROL |
| Depreciação / ROL | `GET /production/depreciation_pct` | Google Sheets + ROL |
| OEE | `GET /production/overall_equipment_effectiveness_pct` | TOTVS SH6010 |
| OTD | `GET /production/on_time_delivery_pct` | TOTVS SC2010 |

## Registro

```bash
export TOKEN="<jwt com apps.manage>"
./scripts/register-manifest.sh
```

Atribuir permissão `dashboard-production.view` no RBAC.

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-production api-delpi
docker compose restart gateway
```
