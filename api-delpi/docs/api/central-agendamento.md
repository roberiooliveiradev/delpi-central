# Central de Agendamento — API

Base: `/scheduling` (gateway: `/apps/api-delpi/scheduling`)

## Permissões

| Código | Uso |
|--------|-----|
| `central-agendamento.view.filial-es\|sc` | Ver calendário e solicitar/criar reservas |
| `central-agendamento.manage.filial-es\|sc` | CRUD de recursos (inclui flag `requires_approval`) |
| `central-agendamento.approve.filial-es\|sc` | Confirmar ou rejeitar reservas pendentes |

`manage` **não** implica `approve`. Combine as permissões nos papéis conforme a política.

Aprovadores devem em geral ter também `view` da filial para abrir o app no portal.

## Recursos

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/resources?branch=` | view/approve/manage |
| POST | `/resources` | manage |
| PATCH | `/resources/{id}` | manage |

Campo novo: `requires_approval` (boolean). Quando `true`, `POST /bookings` cria status `pending`.

## Reservas

| Método | Path | Permissão |
|--------|------|-----------|
| GET | `/bookings?branch=&from=&to=` | view (+ pending no calendário) |
| GET | `/bookings/pending?branch=&mine=` | fila da filial (`approve`); `mine=true` com view |
| GET | `/bookings/mine?branch=` | reservas do usuário autenticado (todos os status) |
| POST | `/bookings` | view — imediato ou pendente conforme recurso |
| POST | `/bookings/{id}/approve` | approve |
| POST | `/bookings/{id}/reject` | approve — body `{ "reason": "..." }` |
| PATCH | `/bookings/{id}/cancel` | dono, manage ou approve |

### Status

`confirmed` · `pending` · `rejected` · `expired` · `cancelled`

- `pending` e `confirmed` **ocupam** o horário (constraint exclusão).
- Expiração: `expires_at` = início do horário solicitado (`start_at`). Sem aprovação até lá → `expired` + notificação.
- Recorrência **não** é permitida em recursos com `requires_approval`.
- Autoaprovação bloqueada (exceto superadmin).

## Notificações

Quando `SCHEDULING_NOTIFICATIONS_ENABLED=true` e Core API S2S configurada:

1. Solicitação → destinatários com `approve` da filial (`permissionCodes`) + CTA para `?tab=approvals&bookingId=`
2. Confirmação / rejeição / expiração → solicitante

Categoria catálogo: `central_agendamento`.

## Migrations

```bash
python scripts/run_plugins_migrations.py up --plugin scheduling
```

Relevante: `V004__booking_approval_workflow.sql`.
