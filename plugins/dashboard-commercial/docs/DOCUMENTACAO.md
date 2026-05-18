# Documentação — Dashboard Comercial

Plugin **microfrontend** (Module Federation) para indicadores do departamento **Comercial**, dados TOTVS via **api-delpi** (`/commercial`).

## Identificação

| Item | Valor |
|------|--------|
| ID | `dashboard-commercial` |
| URL | `/apps/dashboard-commercial` |
| Container | `delpi-dashboard-commercial` |
| Permissão | `dashboard-commercial.view` ou `api-delpi.access` |

## Indicadores na tela

| KPI | Endpoint |
|-----|----------|
| Meta ROL — Matriz (01) | `GET /commercial/head_office_rol_target_pct` |
| Meta ROL — Filial (02) | `GET /commercial/branch_rol_target_pct` |
| Taxa de conversão | `GET /commercial/closing-rate` |
| Média mensal clientes novos | `GET /commercial/new-clients-average` |
| % ROL clientes novos | `GET /commercial/new-clients-rol-pct` |

Gráficos: barras comparando metas ROL matriz/filial e funil propostas × ganhas.

## Filtros

| Campo | Query API |
|-------|-----------|
| Data inicial / final | `start_date`, `end_date` (YYYY-MM-DD) |
| Filial | `branch` — afeta conversão e clientes novos; metas ROL usam filiais fixas 01/02 na API |

Persistência: URL (`start_date`, `end_date`, `branch`) + `sessionStorage` (`delpi.dashboard-commercial.filters`).

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
