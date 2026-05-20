# Dashboard Engenharia

Microfrontend (Module Federation) para o departamento **Engenharia** no escopo dos Indicadores Estratégicos — foco em **TRANSFORMA+ DELPI** (ganhos e processos de melhoria).

O indicador **% projetos/LMPs no prazo** permanece no plugin separado [`dashboard-lmps`](../dashboard-lmps/).

## API (`api-delpi`)

| Recurso | Endpoint |
|---------|----------|
| Resumo Transforma+ | `GET /engineering/transforma-mais/processes/summary` |
| Processos | `GET /engineering/transforma-mais/processes` |

Base no gateway: `/apps/api-delpi/engineering`

## Permissão

- `dashboard-engineering.view` (ou `api-delpi.access`; rotas Transforma+ aceitam também `dashboard-lmps.view` por compatibilidade)

## Desenvolvimento

```bash
cd plugins/dashboard-engineering
npm install
npm run dev
```

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-engineering api-delpi
docker compose restart gateway
```

Registro:

```bash
TOKEN=<jwt> ./plugins/dashboard-engineering/scripts/register-manifest.sh
```
