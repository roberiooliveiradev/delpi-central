# Integration Execution Tracking — api-delpi (implementado)

Registro persistente, auditoria e reconciliação das operações de escrita que a
`api-delpi` encaminha ao TOTVS Protheus REST. Reutilizável por outras rotas de
integração de escrita; começa por `supplier` `create`/`update`.

> Nota de reconciliação: este documento descreve a **implementação vigente**.
> O documento de design do PR #101 (`docs/api-delpi-protheus-write-tracking-owner-*`,
> não integrado à `main` no momento desta implementação) foi usado como entrada
> de design; divergências deliberadas estão registradas na seção "Reconciliação".

## Ownership e storage

| Item | Decisão |
|---|---|
| Owner | `api-delpi` (executa e rastreia o que ela própria envia) |
| Banco | `postgres-plugins` (`PLUGINS_DB_*`), pool existente |
| Schema | `integration_tracking` (slug de migrations `integration-tracking`) |
| Tabelas | `integration_operations`, `integration_operation_events` |
| Migrations | `api-delpi/migrations/plugins/integration-tracking/V001__...` via `run_plugins_migrations.py` (só `up` em produção) |
| Retenção | Sem expurgo automático nesta entrega; política de retenção/expurgo exige decisão futura autorizada |

## Camadas

```text
domain   app/domain/integrations/integration_operation.py
         IntegrationOperation, IntegrationOperationEvent,
         IntegrationStatus, ALLOWED_TRANSITIONS, invariantes
application app/application/services/integration_tracking/
         contracts.py      → IntegrationOperationRepository (port),
                             NewOperationInput, TransitionPatch
         tracking_service  → begin/mark_sending/ack/reject/unknown/
                             failed_pre_send/confirm/reconciliation/
                             get/list/assert_can_view
         payload_sanitizer → redaction recursiva, truncamento, hash SHA-256
         integrations/protheus_write_tracker.py
                           → ponte Protheus: classificação de resultado,
                             read-after-write helpers
infrastructure
         persistence/plugins/repositories/integration_tracking/
         postgres_integration_operation_repository.py
interface  GET /integrations/operations/{id}
           GET /integrations/operations/{id}/events
```

## Garantias transacionais

- `CREATED` + evento `operation_created` são persistidos **atomicamente** e
  **antes** de qualquer byte enviado ao Protheus. Se falhar →
  `PROTHEUS_TRACKING_UNAVAILABLE` (503), **nenhum envio**.
- `SENDING` + evento `send_started` commitam antes da transmissão. Se falhar →
  idem: nenhum envio. `SENDING` nunca é prova de entrega.
- Cada transição é `UPDATE ... WHERE version = N AND status = esperado`
  (optimistic lock) + `INSERT` de evento na **mesma transação**.
- Falha de persistência **após** o envio nunca dispara retry do write;
  a operação permanece em estado indeterminado (`SENDING`/`UNKNOWN`) e o
  retorno carrega `tracking_warning`.
- HTTP calls nunca ficam dentro de transação de banco.

## Máquina de estados

| Estado | Significado |
|---|---|
| CREATED | Registro durável; envio não iniciado |
| SENDING | Envio iniciado ou potencialmente iniciado |
| ACKNOWLEDGED | Resposta upstream 2xx; persistência **não** comprovada |
| CONFIRMED | Read-after-write (ou evidência equivalente) conferiu os campos |
| REJECTED | Rejeição determinística comprovada sem efeito de escrita |
| FAILED_PRE_SEND | Falha definitivamente anterior ao envio |
| UNKNOWN | Timeout/5xx/perda de resposta após possível envio — **nunca** auto-retry |
| RECONCILIATION_REQUIRED | Investigação exigida (ex.: mismatch de confirmação) |

Transições válidas (todas as demais lançam `InvalidTransitionError`):

```text
CREATED → SENDING | FAILED_PRE_SEND
SENDING → ACKNOWLEDGED | REJECTED | UNKNOWN
ACKNOWLEDGED → CONFIRMED | RECONCILIATION_REQUIRED
UNKNOWN → CONFIRMED | RECONCILIATION_REQUIRED
RECONCILIATION_REQUIRED → CONFIRMED
CONFIRMED | REJECTED | FAILED_PRE_SEND → (terminais)
```

## Integração nos writes de fornecedor

`POST /integrations/protheus/suppliers` e `PUT .../suppliers/{id}`:

1. validação + gate (`*_ENABLED`) + identidade Core (`codusr`) + payload +
   params + token — tudo antes de qualquer tracking write;
2. `begin` → `CREATED`+`SENDING` persistidos (fail closed);
3. chamada gateway existente — **sem retry**;
4. sucesso → `ACKNOWLEDGED` (+ `http_status`, resposta sanitizada);
5. exceção determinística (`4xx`, `*_WRITE_*`, `NOT_FOUND`, `TOKEN_INVALID`)
   → `REJECTED`; timeout/5xx/indefinido → `UNKNOWN`;
6. UPDATE: read-after-write automático — GET do fornecedor e comparação dos
   campos enviados. Match → `CONFIRMED` (`persistence_proven=true`);
   mismatch → `RECONCILIATION_REQUIRED`; GET indisponível/sem evidência →
   permanece `ACKNOWLEDGED` + evento `confirmation_attempt_failed`;
7. CREATE: upstream não retorna `A2_COD` (evidência F4) → permanece
   `ACKNOWLEDGED` até reconciliação externa; se a chave vier no futuro, o
   mesmo read-after-write é executado.

Resposta ao consumidor ganha `operation_id` (additive, compatível) e, quando
aplicável, `tracking_warning` / `mismatched_fields`.

## Segurança e privacidade

- `caller_app` vem **exclusivamente** do `client_id` do token S2S validado —
  `X-Delpi-Caller-App` é metadado, nunca identidade.
- `actor_subject` = id do usuário autenticado; `protheus_user_id` = `codusr`
  resolvido pelo Core. Nada disso é aceito do body.
- Redação recursiva (qualquer profundidade): `tax_id`, `email`, `phone`,
  `area_code`, `contact_name`, `state_registration`,
  `municipal_registration`, `codusr`, senhas/tokens/headers de auth.
- Strings limitadas a 300 chars; JSON limitado a 16 KB (excedente vira stub
  `oversized`). Payloads persistem como JSONB — dados inertes.
- `request_hash`/`outbound_hash` usam **HMAC-SHA256** com chave de servidor
  (`INTEGRATION_TRACKING_HMAC_SECRET`, fallback `JWT_SECRET`); SHA-256 puro
  seria reversível por dicionário sobre CPF/CNPJ/e-mails previsíveis. Sem
  chave configurada o hash é omitido (NULL), nunca enfraquecido.
- Sem senhas/tokens no banco; erros upstream guardam apenas
  `code`/`message` sanitizados (`raw_error_stored=false`).
- Consulta (`GET operations`): S2S `supplies-api` + `suppliers.read` **ou**
  permissão `api-delpi.integrations.protheus.read`; **e** vínculo duplo —
  `caller_app` igual E `actor_subject` igual. Outra aplicação ou outro
  usuário → `INTEGRATION_OPERATION_FORBIDDEN` (403).

## Idempotência e concorrência

- `operation_id` (UUID) = identidade do registro de acompanhamento.
- `correlation_id` = `X-Correlation-ID`/`X-Request-ID` de entrada ou UUID gerado.
- `idempotency_key`: coluna e índice único `(caller_app, idempotency_key)`
  criados, mas **deduplicação ativa não implementada** — o REST Protheus não
  expõe semântica de idempotência; duplicidade é tratada como operação nova
  (limitação documentada). `attempt_count` permanece 1 (nenhum retry).
- Optimistic lock por `version`; conflito → `INTEGRATION_OPERATION_CONFLICT`.

## Reconciliação com o design do PR #101 (não integrado)

| Tema | PR #101 (design) | Implementação |
|---|---|---|
| Owner | api-delpi | api-delpi (igual) |
| Storage | TO_INVENTORY | postgres-plugins, schema `integration_tracking` |
| Estados | 8 candidatos | os mesmos 8, com transições explícitas testadas |
| Query | projeção autorizada futura | implementada com vínculo caller+actor e scope S2S |
| Confirmação | mecanismo seguro quando comprovado | read-after-write automático no UPDATE |
| Deduplicação | "se contratada" | esquema pronto, dedup desligada (documentado) |

## Operação

- Migration: `python scripts/run_plugins_migrations.py up --plugin integration-tracking`
  (dev já aplicada; produção segue o runner padrão — nunca `reset`).
- Tracking **não depende** dos gates `PROTHEUS_SUPPLIER_*_ENABLED`; com o
  gate fechado a escrita é negada antes de qualquer registro.
- Operações em `SENDING`/`UNKNOWN`/`RECONCILIATION_REQUIRED` exigem
  investigação manual (SQL/REST no ambiente correto). Nunca re-emitir o write
  sem prova de não-efeito.


## Consumo pela supplies-api (BFF)

- `GET /suppliers/operations/{operation_id}` — proxy read-only para
  `GET /integrations/operations/{id}`. O BFF usa a credencial S2S individual
  `supplies-api` (scope `suppliers.read`); o vínculo caller_app+actor é
  aplicado no backend da api-delpi. A resposta é minimizada para UX
  (`project_operation` em `suppliers_dto.py`):
  `operation_id`, `status`, `outcome` (`sent`/`acknowledged`/`confirmed`/
  `indeterminate`/`rejected`/`reconciliation_required`),
  `persistence_proven`, `tracking_warning`, `http_status`, `resource_key`,
  `correlation_id` e timestamps — sem payloads brutos, hashes ou identidade.
- Respostas POST/PUT da BFF expõem `operation_id` e `tracking_warning` no
  top-level (além de `data.operation_id`, já propagado do envelope da
  api-delpi).
- O frontend nunca acessa a api-delpi diretamente.
