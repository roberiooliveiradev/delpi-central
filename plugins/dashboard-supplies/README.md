# Dashboard Suprimentos

Microfrontend com indicadores de suprimentos via **api-delpi** (`/supplies`).

## KPIs e gráficos

| Recurso | Endpoint | Descrição |
|---------|----------|-----------|
| CPV | `GET /supplies/cpv` | Custo de produto vendido e % sobre ROL |
| OTD compras | `GET /supplies/otd` | Pontualidade de fornecedores |
| Estoque | `GET /supplies/stock-value` | Valor total por localização |
| Giro IDD | `GET /supplies/inventory-turnover` | Giro de estoque em meses |

## Registro

```bash
export TOKEN="<jwt com apps.manage>"
./scripts/register-manifest.sh
```

Atribuir permissão `dashboard-supplies.view` no RBAC.

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-supplies api-delpi
docker compose restart gateway
```
