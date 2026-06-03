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
  python scripts/run_plugins_migrations.py up --plugin scheduling
```

Inclui constraint `V002` que impede reservas confirmadas sobrepostas no mesmo recurso.

## Registro

```bash
export TOKEN="<jwt>"
./plugins/central-agendamento/scripts/register-manifest.sh
```

## Dev local

Stack mínima (da **raiz** do repositório):

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d api-delpi central-agendamento
```

Build isolado do plugin:

```bash
cd plugins/central-agendamento && npm run dev
```

## Produção

O serviço `central-agendamento` está em `infra/docker-compose.yml` (`delpi-central-agendamento`, `target: production`) e listado no `depends_on` do gateway.

Deploy:

1. Subir/rebuild o container `central-agendamento`
2. Rodar migrations `--plugin scheduling`
3. Registrar manifesto na Core API (se ainda não registrado)
4. Atribuir permissões RBAC por filial

## Homologação

```bash
bash ./scripts/homologacao/check-central-agendamento.sh          # Fase 1 — smoke
export TOKEN="<jwt>"
bash ./scripts/homologacao/check-scheduling-api.sh               # Fase 2 — API E2E
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

## Roadmap

Ver [docs/12-roadmap-e-evolucao/central-agendamento/ROADMAP.md](../../docs/12-roadmap-e-evolucao/central-agendamento/ROADMAP.md).
