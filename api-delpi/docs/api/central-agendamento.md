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

Campo: `requires_approval` (boolean). Quando `true`, `POST /bookings` cria status `pending`.

Campos públicos (V005): `public_booking_enabled`, `public_token` (opaco). Com o flag ligado, o
admin copia o link `/p/central-agendamento/book/{token}` no public-hub.

## Público (sem JWT)

Base: `/public/scheduling` (gateway: `/apps/api-delpi/public/scheduling`)

| Método | Path | Uso |
|--------|------|-----|
| GET | `/resources/{token}` | Metadados do recurso (sem PII de outras reservas) |
| GET | `/resources/{token}/availability?from=&to=` | Faixas ocupadas (`confirmed`/`pending`) |
| POST | `/resources/{token}/bookings` | Solicitação — sempre `pending`; honeypot `website` |

Body da solicitação: `requester_name`, `requester_email`, `requester_phone?`, `title`, `notes?`, `start_at`, `end_at`.

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
# Diagnóstico
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin scheduling

# Aplicar pendentes (produção: só up — nunca reset)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin scheduling
```

Relevante: `V004__booking_approval_workflow.sql`, `V005__public_booking.sql`.

Se a API retornar **503** com «Schema do banco de plugins desatualizado» (ou **500** genérico
em listagens de recursos/reservas após deploy de código novo), o código está à frente do
schema: confira `status` e rode `up` — tipicamente V004/V005 pendentes.
