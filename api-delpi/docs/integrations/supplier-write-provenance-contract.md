# Contrato transversal de proveniência — escrita de fornecedores (v1)

> **IMPLEMENTED — SUPPLIER-PROVENANCE-01.** Infraestrutura transversal de
> proveniência de escrita SA2 na api-delpi. Authority operacional continua
> sendo `integration_tracking.integration_operations` (estado/máquina de
> estados); a proveniência registra **intenção por campo**, imutável, ligada
> por `operation_id`. Não altera o payload MATA020. Não habilita gates de
> escrita. Consulta externa de CNPJ/comparação/decisões ficam para etapa
> posterior na supplies-api.

## 1. Ownership e limites

| Camada | Responsabilidade |
|---|---|
| `api-delpi` | Contrato canônico de proveniência, validação fail-closed, persistência em `integration_tracking.supplier_field_provenance`, vínculo ao tracking real |
| BFFs consumidores (ex.: `supplies-api`) | AuthZ Core do produto, composição do `change_context`, decisões de usuário |
| Protheus MATA020 | Recebe **somente** o payload de campos homologados — nunca metadados de auditoria |
| Keycloak/Core | Identidade SSO e permissões efetivas |

Identidade `initiating_client_id`/`actor_subject` é derivada de credenciais
validadas (S2S token + Bearer do usuário). O cliente **nunca** declara esses
campos — envio resulta em `PROVENANCE_IDENTITY_CLIENT_FORBIDDEN` (422).

Cobertura: a trilha cobre apenas writes que passam pela api-delpi.
Alterações diretas no Protheus/MATA020 ou por outros writers não são
rastreáveis por este contrato (coverage start).

## 2. Contrato HTTP — `change_context` opcional

POST `/integrations/protheus/suppliers` e PUT
`/integrations/protheus/suppliers/{supplier_id}` aceitam, além de
`fornecedor`, um objeto opcional `change_context` (schema_version `"1"`):

```json
{
  "fornecedor": { "supplier_name": "NOME" },
  "change_context": {
    "schema_version": "1",
    "change_mode": "MANUAL_DIRECT",
    "reason_code": "CADASTRAL_REVIEW",
    "review_id": "opaque-review-id",
    "field_provenance": [
      {
        "field_key": "supplier_name",
        "source_type": "MANUAL_USER_INPUT",
        "source_id": "manual_form",
        "source_reference": "opaque-evidence-id",
        "source_retrieved_at": "2026-10-21T12:00:00Z",
        "decision_id": "opaque-decision-id"
      }
    ]
  }
}
```

### Enums do contrato

`source_type` (todos persistíveis; claimáveis pelo cliente em v1 marcados):

| Valor | Claimável em v1 | Exigência |
|---|---|---|
| `MANUAL_USER_INPUT` | sim | — |
| `INTERNAL_SYSTEM` | sim | `source_id` obrigatório |
| `IMPORT` | sim | `source_id` obrigatório |
| `GOVERNMENT_API` | **não** | rejeitado até contrato de evidência verificável |
| `THIRD_PARTY_API` | **não** | idem |
| `AUTOMATION_RULE` | **não** | idem (exige policy aprovada) |
| `UNKNOWN_LEGACY` | **não** — server-assigned | writes sem `change_context` |

`change_mode`:

| Valor | Claimável em v1 |
|---|---|
| `MANUAL_DIRECT` | sim |
| `SYSTEM_SYNC` | sim |
| `IMPORT_JOB` | sim |
| `EXTERNAL_SUGGESTION_USER_APPROVED` | não — requer evidência externa verificável |
| `BULK_SUGGESTION_USER_APPROVED` | não — idem |
| `AUTOMATED_BY_APPROVED_POLICY` | não — requer `policy_id` aprovado (chave proibida no body) |

### Regras de validação (fail-closed, 422)

| Código | Condição |
|---|---|
| `PROVENANCE_CONTEXT_INVALID` | `change_context` não é objeto |
| `PROVENANCE_SCHEMA_VERSION_UNSUPPORTED` | `schema_version` ≠ `"1"` |
| `PROVENANCE_CHANGE_MODE_INVALID` / `PROVENANCE_CHANGE_MODE_NOT_AUTHORIZED` | modo inválido ou não claimável |
| `PROVENANCE_FIELD_METADATA_REQUIRED` | `change_context` sem `field_provenance` |
| `PROVENANCE_FIELD_NOT_IN_PAYLOAD` | `field_key` fora do conjunto efetivamente enviado (pós-normalização) |
| `PROVENANCE_FIELD_DUPLICATED` | mesmo `field_key` duas vezes |
| `PROVENANCE_SOURCE_INVALID` / `PROVENANCE_SOURCE_NOT_VERIFIABLE` | tipo inválido ou não claimável |
| `PROVENANCE_SOURCE_ID_REQUIRED` | `INTERNAL_SYSTEM`/`IMPORT` sem `source_id` |
| `PROVENANCE_METADATA_INVALID` | limites/formato (`source_retrieved_at` deve ser ISO-8601) |
| `PROVENANCE_IDENTITY_CLIENT_FORBIDDEN` | `actor_subject`, `initiating_client_id`, `caller_app`, `policy_id` etc. no body |

Validação ocorre **antes** de qualquer byte upstream e antes do begin do
tracking. Chamadas legadas sem `change_context` registram `UNKNOWN_LEGACY`
por campo enviado — nunca fabricam `MANUAL_USER_INPUT`.

## 3. Persistência

`integration_tracking.supplier_field_provenance` (migration V003):

- `provenance_id` UUID PK, `operation_id` FK → `integration_operations`
  (RESTRICT) — inserida na **mesma transação** do CREATED.
- `supplier_code`, `supplier_store`, `environment_key`, `field_key`,
  `source_type`, `change_mode`, `source_id`, `source_reference`,
  `source_retrieved_at`, `reason_code`, `review_id`, `decision_id`,
  `initiating_client_id`, `actor_subject`, `provenance_schema_version`,
  `created_at`.
- Índices: `(operation_id)`, `(supplier_code, supplier_store, field_key)`,
  `(initiating_client_id)`.
- Sem valores de campo (sem before/after), sem payload externo, sem tokens.
  Retenção: mesma política vigente de `integration_tracking` — sem expurgo
  automático; política de retenção/expurgo segue decisão autorizada futura
  (DPO). `actor_subject` e vínculos já constituem categoria retida hoje.

## 4. Semântica de confirmação

O status operacional **não** é duplicado na tabela de proveniência — é lido
via join à `integration_operations` (authority). Última origem confirmada de
um campo = linha cuja operação está `CONFIRMED`, mais recente por
`confirmed_at`. Tentativas `SENDING`/`ACKNOWLEDGED`/`UNKNOWN`/
`RECONCILIATION_REQUIRED` permanecem visíveis como tentativas
(`has_unconfirmed_newer_attempts`), **nunca** promovidas.

## 5. Read API

`GET /integrations/protheus/suppliers/{supplier_id}/provenance`
(`operationId: list_supplier_field_provenance`).

- Auth: S2S `suppliers.read` com `allowed_clients=("supplies-api",)` ou
  permission Core `PROTHEUS_INTEGRATION_READ`.
- Escopo: S2S lê somente operações registradas pelo próprio `client_id`;
  usuário direto lê somente operações que ele próprio registrou sem caller
  S2S. Nenhum consumer lê trilha de outro.
- Query: `field_key` (filtro), `limit`/`offset` paginados.
- Resposta: `fields[]` com `latest_confirmed` (ou `null`),
  `has_unconfirmed_newer_attempts`, `attempt_count`; `attempts[]` com
  source/mode/operation_status/confirmed_at; `page`.

Exemplo (sanitizado):

```json
{
  "supplier_id": "00387801",
  "fields": [
    {
      "field_key": "supplier_name",
      "latest_confirmed": {
        "source_type": "MANUAL_USER_INPUT",
        "change_mode": "MANUAL_DIRECT",
        "initiating_client_id": "supplies-api",
        "operation_status": "CONFIRMED",
        "operation_id": "...",
        "confirmed_at": "..."
      },
      "has_unconfirmed_newer_attempts": false,
      "attempt_count": 1
    }
  ],
  "attempts": [ ... ],
  "page": { "limit": 100, "offset": 0 }
}
```

## 6. Limites conhecidos

- Proveniência **não** prova que o campo foi persistido — isso é o status
  `CONFIRMED` da operação.
- Sem cobertura de writes fora da api-delpi.
- Sem verificação de evidência externa em v1 (sources oficiais rejeitados
  até contrato de confiança).
- Rollout: `change_context` é opcional durante a janela de compatibilidade;
  consumers legados produzem `UNKNOWN_LEGACY`. Torná-lo obrigatório exige
  migração coordenada dos consumers e decisão formal.

## 7. Evidências desta etapa

- Testes: `tests/test_supplier_change_provenance.py`,
  `tests/test_supplier_provenance_routes.py`, V003 checks em
  `tests/test_integration_tracking_migration.py`.
- OpenAPI: rota em `openapi_baseline.json` + inventory (`stable`,
  `autoCount=0`).
- Deploy: **NOT RUN** nesta etapa (decisão operacional pendente).
- Gates: `PROTHEUS_SUPPLIER_*_ENABLED` OFF — inalterados.
