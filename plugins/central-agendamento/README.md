# Central de Agendamento

Plugin microfrontend para reserva de salas, salas de treinamento, veículos e outros recursos por filial (ES / SC).

## Rotas

- `/apps/central-agendamento/filial-es`
- `/apps/central-agendamento/filial-sc`

## API

Base: `/apps/api-delpi/scheduling`

- `GET /resources?branch=ES|SC`
- `POST /resources` (gestores)
- `PATCH /resources/{id}` (gestores)
- `GET /bookings?branch=ES|SC&from=&to=`
- `POST /bookings`
- `PATCH /bookings/{id}/cancel`

## Migrations

```bash
docker compose -f infra/docker-compose.dev.yml exec api-delpi \
  python scripts/run_plugins_migrations.py --plugin scheduling
```

## Registro

```bash
export TOKEN="<jwt>"
./plugins/central-agendamento/scripts/register-manifest.sh
```

## Dev local

```bash
cd plugins/central-agendamento && npm run dev
```

Build produção / Docker:

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d central-agendamento
```

## Permissões

| Código | Uso |
|---|---|
| `central-agendamento.view.filial-es` | Ver e reservar (ES) |
| `central-agendamento.view.filial-sc` | Ver e reservar (SC) |
| `central-agendamento.manage.filial-es` | CRUD recursos (ES) |
| `central-agendamento.manage.filial-sc` | CRUD recursos (SC) |

## UI

Calendário com `react-big-calendar` (semana/dia/mês), sidebar de filtros por tipo/recurso, modais de reserva e painel administrativo para gestores.
