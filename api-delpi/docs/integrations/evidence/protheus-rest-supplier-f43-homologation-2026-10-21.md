# F4.3 — Correção pós-homologação POST/PUT + Integration Tracking

**Registro:** 2026-10-21
**Base de código:** `origin/main` `b3c9724941` + correções F4.3
**Escopo:** defeitos materiais da homologação real POST+PUT em `DELPI_TST01` (runtime `srv-api`, REST `192.168.1.233:8701`, tracking PostgreSQL `plugins_hub.integration_tracking`).

Não é autorização de escrita produtiva. Gates `PROTHEUS_SUPPLIER_CREATE_ENABLED`/`PROTHEUS_SUPPLIER_UPDATE_ENABLED` permanecem OFF por padrão.

## 1. Defeitos tratados

| ID | Defeito | Causa raiz | Correção |
|---|---|---|---|
| F4.3-01 | UPDATE persistido mas operação travada em `ACKNOWLEDGED` com `tracking_warning=confirmation_record_failed` | `ProtheusWriteTracker.confirm()` chamava `IntegrationTrackingService.confirm()` sem o argumento obrigatório `evidence` → `TypeError` engolido pelo handler defensivo | Chamada passa `evidence=None`, delegando ao builder canônico (`method`, `resource_key`, `environment_key`, `checked_fields`, `result`, `schema_version`) preenchido com dados da operação persistida |
| F4.3-02 | HTTP 400 upstream com `details` (ex.: `SA2MASTER | VLDDATA_OBRIGAT | A2_TEL`) virava 502 genérico e, sem `code_error`, caía em `UNKNOWN` | `_extract_error_text()` não lia `details`/`detail`; fallback 4xx sem evidência reconhecida virava `PROTHEUS_UPSTREAM_ERROR` (indeterminado) | Parser extrai `details`/`detail` (string, dict ou lista); 4xx com evidência de erro extraível → `PROTHEUS_SUPPLIER_WRITE_REJECTED`/`PROTHEUS_SUPPLIER_UPDATE_REJECTED` (400, `recoverable=False`, REJECTED no tracking); 4xx sem conteúdo parseável permanece `PROTHEUS_UPSTREAM_ERROR`/UNKNOWN (conservador) |
| F4.3-03 | `tax_id` enviado no contrato, `A2_CGC` persistiu vazio | **Boundary upstream** — ver §3 | Diagnóstico + handoff Gabriel; sem correção local possível |

## 2. Evidência S1 — confirm()

Regressão: `MagicMock(spec=...)` aceita kwargs inexistentes, então o TypeError só apareceu com o serviço real. Novos testes usam `IntegrationTrackingService` real sobre repositório in-memory:

- `test_tracker_confirm_promotes_to_confirmed_with_evidence` — begin→ack→confirm → `CONFIRMED` com `confirmation_evidence` completo.
- `test_use_case_update_confirmed_with_real_tracker` — use case de UPDATE end-to-end promove a `CONFIRMED` e expõe `update_confirmed=true`.

## 3. Diagnóstico S2 — `tax_id` → `A2_CGC` (boundary Gabriel/TOTVS)

Cadeia de evidência (sem novo POST):

| Etapa | Evidência |
|---|---|
| Payload recebido pela BFF/API DELPI | `request_payload.fields.tax_id = [REDACTED]` — valor submetido existia |
| Outbound real enviado ao upstream | `outbound_payload.body.fornecedor.tax_id` presente na operação `8708fd66-4763-49d9-a12e-b25748641526` — a `api-delpi` entregou a chave contratual |
| Resposta upstream | HTTP 200, `supplier_code=003874`, `supplier_store=01` |
| GET REST posterior | `003874/01` retorna sem `tax_id` |
| SQL `DELPI_TST01.SA2010` | `A2_CGC = ''` (vazio) |
| Tracking | `RECONCILIATION_REQUIRED`, `mismatched_fields=["tax_id"]` — classificação conservadora correta |

**Conclusão:** a perda ocorre no endpoint REST/Execauto MATA020 (owner Gabriel/TOTVS), não na `api-delpi`. O POST de 2026-10-20 (`003878/01`) persistiu `A2_CGC` com a mesma chave contratual — suspeita de mudança upstream entre as execuções (o retorno de `supplier_code` no POST também é comportamento novo, coerente com o ajuste anunciado pelo owner).

### Handoff técnico — perguntas objetivas ao owner

1. O endpoint `/delpi/api/v1/suppliers` (POST) mapeia `fornecedor.tax_id` para `A2_CGC`? Se sim, em quais condições o valor é descartado silenciosamente (validação DV, `person_type`, `state_registration`, empresa/filial)?
2. Houve deploy do endpoint entre 2026-10-20 e 2026-10-21 (o POST passou a retornar `supplier_code`/`supplier_store`)? O novo código alterou o mapeamento de `A2_CGC`?
3. Shape formal do erro `SA2MASTER | VLDDATA_OBRIGAT | ...`: `code_error`/`details` podem ser documentados para classificação determinística?

**Chave de correlação:** `operation_id=8708fd66-4763-49d9-a12e-b25748641526`, `correlation_id=e9b5ab11-24a8-47b2-9c61-38f4b89b6e62`, fornecedor criado `003874/01` (bloqueado, `A2_MSBLQL='2'`), `DELPI_TST01`, 2026-10-21 ~10:13 (America/Sao_Paulo).

**Sem correção local:** `tax_id` não pode ser reenviado via PUT (campo imutável no contrato — `PROTHEUS_SUPPLIER_FIELD_IMMUTABLE`). `CREATE_CONTRACT = PENDING_UPSTREAM`.

## 4. Contrato atualizado (S4)

- `protheus-rest-supplier-api-contract.md` §3.4 — POST retornando `supplier_code`/`supplier_store` (PROVEN runtime, contrato formal PENDING); divergência `tax_id` registrada; `CONTRACT_GAPS` atualizado.
- `protheus-rest-supplier-post-field-matrix.md` — `tax_id` marcado `DIVERGENCE_UPSTREAM`; `supplier_short_name` PUT promovido a PROVEN runtime; `rohs_indicator` mantido TO_INVENTORY (enviado no POST, obrigatoriedade não comprovada).

## 5. Re-homologação runtime (S6)

Pendente de deploy do SHA corrigido no `srv-api` — PUT controlado em `003878/01` esperando `CONFIRMED` + `confirmation_evidence` persistido. Resultado registrado na seção final após execução.
