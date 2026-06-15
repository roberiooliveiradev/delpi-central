# Dashboard Produção

Microfrontend com indicadores de produção via **api-delpi** (`/production`).

## KPIs e painéis

| Indicador | Endpoint | Fonte |
|-----------|----------|--------|
| MO direta / ROL | `GET /production/direct_labor_cost_pct` | Google Sheets + ROL TOTVS |
| Custo produção / ROL | `GET /production/production_cost_pct` | Google Sheets + ROL |
| Depreciação / ROL | `GET /production/depreciation_pct` | Google Sheets + ROL |
| OEE (%) | `GET /production/overall_equipment_effectiveness_pct` | TOTVS SH6010 |
| **OEE — painel** | `GET /production/oee` | Resumo, evolução e listagem de apontamentos |
| **OEE — detalhe** | `GET /production/oee/appointments/{id}` | Roteiro, estrutura, tempos e alertas (`time_analysis.findings`) |
| OTD (%) | `GET /production/on_time_delivery_pct` | TOTVS SC2010 |
| **OTD — painel** | `GET /production/otd` | Resumo e listagem de OPs PA |

Rotas no Portal: `/apps/dashboard-production/oee`, `/apps/dashboard-production/otd`, etc.

## OEE — listagem de apontamentos

Layout alinhado ao plugin [eficiência fabril](../eficiencia-fabril/README.md):

- Colunas: Data, Início, Fim, Qtd. apontada, Filial, OP, Descrição produto, CT, Operador, Eficiência, Status
- Faixa válida **0–199%** via módulo compartilhado `production_efficiency_valid_range` / `build_fabril_view_filters`
- Mesma métrica e escopo da eficiência fabril (eficiência por tempos, view fabril)
- Outliers: linha vermelha + badge **Verificar**; válidos: **OK**
- Clique na linha → detalhe (`OeeAppointmentDetailPage`) com **análise de tempos** e alertas automáticos (`findings`: faixa, divergência, intervalo curto, roteiro incompleto, etc.)

Componentes: `DataTableSection` (colunas no padrão eficiência fabril), `constants/businessRules.ts`.

## Registro

```bash
export TOKEN="<jwt com apps.manage>"
./scripts/register-manifest.sh
```

Atribuir permissão `dashboard-production.view` no RBAC.

## Deploy

```bash
cd infra
docker compose -f docker-compose.dev.yml build api-delpi dashboard-production eficiencia-fabril
docker compose -f docker-compose.dev.yml up -d --force-recreate api-delpi dashboard-production eficiencia-fabril gateway
```

Após mudanças só no backend:

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```
