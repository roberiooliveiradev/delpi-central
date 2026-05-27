# Documentação — Dashboard Comercial

Plugin **microfrontend** (Module Federation) para indicadores do departamento **Comercial**, dados TOTVS via **api-delpi** (`/commercial`). Metas vêm do **Indicadores Estratégicos** (`commercial_rol` e demais `source_key` do catálogo).

## Identificação

| Item | Valor |
|------|--------|
| ID | `dashboard-commercial` |
| URL | `/apps/dashboard-commercial` |
| Container | `delpi-dashboard-commercial` |
| Permissão | `dashboard-commercial.view` ou `api-delpi.access` |

## Indicadores na tela

| KPI | Endpoint | Meta SI (`source_key`) |
|-----|----------|------------------------|
| ROL — Filial 01 | `GET /commercial/head_office_rol_target_pct` | `commercial_rol`, filial `01` |
| ROL — Filial 02 | `GET /commercial/branch_rol_target_pct` | `commercial_rol`, filial `02` |
| OTD — pedidos de venda | `GET /commercial/sales-order-otd` | `commercial_sales_order_otd` |
| Taxa de conversão | `GET /commercial/closing-rate` | `commercial_closing_rate` |
| % ROL — novos negócios | `GET /commercial/new-business-rol-pct` | `commercial_new_business_rol` |

Gráficos: evolução do ROL (filiais 01 e 02) e funil propostas × ganhas.

Catálogo SI: um indicador `commercial-rol` (`per_unit`, curva R$); `commercial-rol-matrix` e `commercial-rol-branch` ficam inativos.

## Filtros

| Campo | Query API |
|-------|-----------|
| Data inicial / final | `start_date`, `end_date` (YYYY-MM-DD) |
| Filial | `branch` — afeta conversão, OTD e novos negócios; cards de ROL sempre exibem 01 e 02 |

Persistência: URL (`start_date`, `end_date`, `branch`) + `sessionStorage` (`delpi.dashboard-commercial.filters`).

## Metas na UI

Os KPIs exibem meta comparável, badge de escopo (ex.: meta filial 01) e desempenho (dentro/abaixo da meta), quando a API enriquece a resposta com dados do SI — mesmo padrão do dashboard de Produção.

## Padrão alinhado ao dashboard-quality

- Module Federation + token do portal
- `FilterBar`, KPIs, impressão (`@media print`)
- Carga paralela com `Promise.allSettled` e erros por seção
- Scripts: `scripts/ci/build-dashboard-commercial.sh`, `scripts/homologacao/check-dashboard-commercial.sh`

## Deploy

```bash
docker compose up -d --build dashboard-commercial
```

Ver [TESTING.md](./TESTING.md).
