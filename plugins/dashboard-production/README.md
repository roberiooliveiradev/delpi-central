# Dashboard Produção

Microfrontend com indicadores de produção via **api-delpi** (`/production`).

## KPIs e painéis

| Indicador | Endpoint | Fonte |
|-----------|----------|--------|
| MO direta / ROL | `GET /production/direct_labor_cost_pct` | Google Sheets + ROL TOTVS |
| Custo produção / ROL | `GET /production/production_cost_pct` | Google Sheets + ROL |
| Depreciação / ROL | `GET /production/depreciation_pct` | Google Sheets + ROL |
| OEE (%) | `GET /production/overall_equipment_effectiveness_pct` | View fabril (`EFICIENCIA_PERCENTUAL` — tempo previsto ÷ real) |
| **OEE — painel** | `GET /production/oee` | Resumo, evolução e listagem de apontamentos |
| **OEE — detalhe** | `GET /production/oee/appointments/{id}` | Roteiro, estrutura, tempos e alertas (`time_analysis.findings`) |
| OTD (%) | `GET /production/on_time_delivery_pct` | TOTVS SC2010 (OP mãe `001`, PA prefixos 9/8) |
| **OTD — painel** | `GET /production/otd` | Resumo e listagem de OPs PA mãe (`C2_SEQUEN = 001`, prefixos 9/8) |

Rotas no Portal: `/apps/dashboard-production/oee`, `/apps/dashboard-production/otd`, etc.

## OEE — listagem de apontamentos

Layout alinhado ao plugin [eficiência fabril](../eficiencia-fabril/README.md):

- Colunas: Data, Início, Fim, Qtd. apontada, Filial, OP, Descrição produto, CT, Operador, Eficiência, Status
- Faixa válida **0–199%** via módulo compartilhado `production_efficiency_valid_range` / `build_fabril_view_filters`
- Mesma métrica e escopo da eficiência fabril (eficiência por tempos, view fabril)
- Outliers: linha vermelha + badge **Verificar**; válidos: **OK**
- Clique na linha → detalhe (`OeeAppointmentDetailPage`) com **análise de tempos** e alertas automáticos (`findings`: faixa, intervalo curto, roteiro incompleto, etc.)

## Painel principal — auto-refresh

O dashboard em `/apps/dashboard-production` recarrega KPIs e gráficos de evolução **a cada 5 minutos** enquanto a aba está visível (`useAutoRefresh`). O botão **Atualizar** na barra de filtros força refresh imediato.

## Detalhe do apontamento — textos de cálculo

O bloco `time_analysis` exibe explicações em linguagem operacional (sem códigos Protheus):

- **Cálculo do tempo previsto** — setup + tempo padrão × proporção da quantidade apontada na OP
- **Cálculo do tempo real** — intervalo início/fim ou tempo informado no apontamento
- **Cálculo da eficiência** — previsto ÷ real × 100

Ver [producao-eficiencia-changelog-jun2026.md](../../api-delpi/docs/api/producao-eficiencia-changelog-jun2026.md).

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
