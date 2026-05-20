# Dashboard RH

Microfrontend (Module Federation) para indicadores de **Recursos Humanos** via **api-delpi** (Portal RH).

## Rotas

| URL | Conteúdo |
|-----|----------|
| `/apps/dashboard-hr` | Visão geral (KPIs, gráficos por filial, tabela) |

## API

| Endpoint | Descrição |
|----------|-----------|
| `GET /apps/api-delpi/hr/snapshot` | Snapshot consolidado (absenteísmo, turnover, treinamento, PDI, satisfação) |
| `GET /apps/api-delpi/hr/branches` | Filiais ativas |

Permissão: `dashboard-hr.view` ou `api-delpi.access`.

## Deploy

```bash
npm run build
# Registrar manifesto
TOKEN=... ./scripts/register-manifest.sh
```

Atribuir `dashboard-hr.view` no RBAC. Subir serviço `dashboard-hr` no docker-compose do gateway.
