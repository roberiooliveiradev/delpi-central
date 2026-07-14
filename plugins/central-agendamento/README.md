# Central de Agendamento

Plugin microfrontend para reserva de salas, salas de treinamento, veículos e outros recursos por filial (ES / SC), com fluxo opcional de **aprovação prévia**.

## Rotas

- `/apps/central-agendamento/filial-es`
- `/apps/central-agendamento/filial-sc`
- Deep link de aprovação: `...?tab=approvals&bookingId={uuid}`
- Minhas reservas: `...?tab=mine&bookingId={uuid}`

## API

Base: `/apps/api-delpi/scheduling`

- `GET /resources?branch=ES|SC`
- `POST /resources` / `PATCH /resources/{id}` (gestores) — inclui `requires_approval`
- `GET /bookings?branch=ES|SC&from=&to=`
- `GET /bookings/pending?branch=&mine=`
- `GET /bookings/mine?branch=` — solicitações do usuário e status
- `POST /bookings` — confirma imediatamente ou cria `pending`
- `POST /bookings/{id}/approve` / `reject`
- `PATCH /bookings/{id}/cancel`

Doc completa: [api-delpi/docs/api/central-agendamento.md](../../api-delpi/docs/api/central-agendamento.md).

## Fluxo de aprovação

1. Gestor marca o recurso com **Exige aprovação prévia**.
2. Usuário com `view` solicita a reserva → status `pending` (ocupa o slot) + notificação aos aprovadores.
3. Usuário com `approve` confirma ou rejeita (motivo obrigatório na rejeição).
4. Solicitante recebe notificação com o resultado e quem decidiu.
5. Sem decisão até o **início do horário solicitado** → `expired` e slot liberado.

## Migrations

```bash
docker compose -f infra/docker-compose.dev.yml exec api-delpi \
  python scripts/run_plugins_migrations.py up --plugin scheduling
```

Inclui `V004` (aprovação, hold de `pending`, auditoria).

## Registro

```bash
export TOKEN="<jwt>"
./plugins/central-agendamento/scripts/register-manifest.sh
```

Reatribuir RBAC: papéis de aprovador precisam de `central-agendamento.approve.filial-*` (idealmente combinado com `view`).

## Dev local

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d api-delpi central-agendamento
```

Build isolado:

```bash
cd plugins/central-agendamento && npm run build
```

## Homologação

```bash
bash ./scripts/homologacao/check-central-agendamento.sh
export TOKEN="<jwt>"
bash ./scripts/homologacao/check-scheduling-api.sh
```

Cenários manuais de aprovação: recurso com `requires_approval` → pending → approve/reject → notificação; overlap com pending; 403 sem `approve`; TTL.

## Permissões

| Código | Uso |
|---|---|
| `central-agendamento.view.filial-es` / `…-sc` | Ver e reservar / solicitar |
| `central-agendamento.manage.filial-es` / `…-sc` | CRUD recursos |
| `central-agendamento.approve.filial-es` / `…-sc` | Confirmar ou rejeitar pendências |

## UI

Calendário (`react-big-calendar`), aba **Minhas reservas** (todos com `view`), aba **Aprovações** (só com `approve`), painel administrativo (só com `manage`), eventos pendentes em destaque âmbar.

## Roadmap

Ver [docs/12-roadmap-e-evolucao/central-agendamento/ROADMAP.md](../../docs/12-roadmap-e-evolucao/central-agendamento/ROADMAP.md).
