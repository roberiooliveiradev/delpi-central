# PRC Record Flags — fix FK idempotente (HML 500 com flag persistida)

**Data:** 2026-11-17 · **SHA:** `d60fed08b2` · **Escopo:** engineering-api (backend only)

## Sintoma (HML)

`POST /technical-records/{record_id}/flags` retornava **HTTP 500**, a UI
reportava erro de verificação, mas a flag **persistia** — visível após
reload (GET 200).

## Causa-raiz (CONFIRMADO_NO_CODIGO + evidência de banco)

`product_registration_idempotency.request_id` tem FK para
`product_registration_requests(id)` (V012). Os 3 fluxos record-scoped
(`create_record_flag`, `update_record_flag`, `close_record_flag`)
passavam `request_id=record_id` a `_idempotent_store` → `save_idempotent`
INSERT falhava por violação de FK numa **segunda** transação, depois do
commit da flag → envelope genérico 500.

Evidência HML (plugins_hub): `product_registration_record_flags` = 3
linhas; `product_registration_idempotency` com `operation LIKE
'record_flag%'` = **0 linhas** — todo INSERT idempotente abortou.

## Correção

`service.py` — 3 call sites: `request_id=record_id` → `request_id=None`
(coluna nullable; `_emit_change` com record_id já era misfire pois
`get_request` retorna `{}`). Nenhuma migration, contrato ou AuthZ.

Fix adicional pré-existente: `test_isolation_between_requests` enviava
`suppliers: []` — CORRECTION-10 (catalog.py) exige ≥1 fornecedor no
intake CREATE; teste atualizado com fornecedor válido (regra de domínio
não alterada).

## Validação HML (executada com hml-tester, record `40f533c4-…8ffd`)

| Caso | Antes | Depois |
|---|---|---|
| POST flags (create) | 500 + flag fantasma | **201** |
| Replay mesma Idempotency-Key | — | **200** |
| POST actions/resolve | — | **200** |
| Linha idempotente persistida | nenhuma | `request_id IS NULL`, op `record_flag_create`/`record_flag_resolved` |

- `delpi-hml-engineering-api` digest: `sha256:1ba2ef890183…` (healthy)
- Testes: 43/43 (record flags + attendance flags)

## Produção

- PRD tinha **0** record flags e **0** linhas idempotentes `record_flag%`
  → bug presente no código, nunca disparado em produção.
- Deploy: `delpi-engineering-api` `726e4fc0bbd6…` → `sha256:082bd86a63cd…`
  (healthy; container contém 3× `request_id=None`; zero erros novos).
- Rollback: retag da imagem anterior + `up-prod-sequential.sh
  engineering-api` (sem mudança de schema — rollback trivial).

## Verificador independente

`INCONCLUSIVE` — motor `devin` sem login (`Error: Not logged in. Run
devin auth login.`). Pedido registrado em
`.git/delpi-verifier/requests/prc-record-flag-idempotency-fk-fix.md`.

## Riscos residuais

- Smoke autenticado de flags em PRD: `TEST_NOT_RUN` (sem identidade
  produtiva para o agente); código-idêntico validado em HML.
- Flags criadas na era do bug em HML não possuem linha idempotente —
  retry com a mesma chave pode criar duplicata; mitigação existente:
  rejeição 409 por flag aberta no mesmo target.
