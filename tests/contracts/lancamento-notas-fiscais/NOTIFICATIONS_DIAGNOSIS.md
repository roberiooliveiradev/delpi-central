# Diagnóstico F3/F3-R/F4 — notificações LNF no inbox

## Classificação atual (F4 passo 0d)

**CORE_APP_ROUTE_PERMISSION** — o app `lancamento-notas-fiscais` **está** registrado no Core DEV
(`apps.active=true`, 8 permissions, 3 `app_routes`). O gate em
`dispatch_notifications_use_case.py:59-72` chama
`filter_user_ids_with_app_access` (`notification_app_access_service.py:157-209`),
que usa a mesma regra de `GET /me/apps`:
`AppAuthorizationService.filter_app_ids` só libera o app se o usuário tiver a
`permission_code` de **alguma** `app_route`.

Rotas LNF no Core:

| path | permission |
|---|---|
| `/apps/lancamento-notas-fiscais/filial-01` | `view.filial-01` |
| `/apps/lancamento-notas-fiscais/filial-02` | `view.filial-02` |
| `/apps/lancamento-notas-fiscais/unmapped-products` | `review-unmapped-products` |

`.access` e `.process` **não** estão em nenhuma rota → destinatário só com essas
permissões é filtrado → Core 400
`no recipients have access to the source application`.

Correção de provisionamento (DEV): P6B = `process` + `view.filial-01`.

## Histórico F3

**NOT_EMITTED_IN_DEV** no lifecycle autoatribuído:

1. `should_notify_block_assignee` retorna `False` quando `assignee_user_id == actor_user_id`.
2. Comentário com menção ao próprio autor também é omitido.
3. `LNF_NOTIFICATIONS_ENABLED=true` e Core local ativos — env não era o bloqueio.

## Paridade de payload

Coberta por `test_notification_payload_parity.py` (**PASS** api-delpi × BFF).
