# Diagnóstico F3 passo 1b — notificações = 0 no inbox

## Classificação

**NOT_EMITTED_IN_DEV** (comportamento do código, não falha de consulta do inbox).

## Evidência

1. `lnf_portal_notification_service.should_notify_block_assignee` retorna `False` quando `assignee_user_id == actor_user_id` (`api-delpi/.../lnf_portal_notification_service.py:81-92`).
2. O ciclo caixa-preta (`test_lifecycle.py`) bloqueia com `assignee_user_id = me["id"]` do próprio processador — autoatribuição → notificação de block **não é emitida**.
3. Comentário com menção usa o mesmo `me["id"]` do ator; o serviço de menções também evita notificar o próprio autor.
4. `LNF_NOTIFICATIONS_ENABLED=true` e Core local (`http://core-api:8000`) estão ativos no container api-delpi DEV — o gate de env não é o bloqueio.

## Implicação para paridade F3

A paridade de payload de notificação será coberta por teste unitário com cliente Core falso (captura do POST `/integrations/notifications`) nas duas implementações (api-delpi e BFF), não só por observação do inbox.

## Não classificado como

- `TEST_QUERY_ISSUE` — a consulta ao histórico do Core responde 200; o contador 0 reflete ausência de emissão.
- `BUG_AS_IS` — a omissão de auto-notificação é regra explícita do serviço.

## F3-R R2 (2026-11-12)

Tentativa caixa-preta P6→P6B: block/comentário 200, mas Core `/integrations/notifications` responde 400
`no recipients have access to the source application` mesmo com `lancamento-notas-fiscais.access` em P6B.
Classificação caixa-preta: **INCONCLUSIVE** (gate RBAC de app no Core, não falha do módulo LNF).
Paridade de payload coberta por `test_notification_payload_parity.py` (**PASS** api-delpi × BFF).
