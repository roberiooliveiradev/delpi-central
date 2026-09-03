# Paridade P0 — invoice-issuance (legado × my-requests)

Espelho do checklist [PLAYBOOK.md §20.3](./PLAYBOOK.md). Suite automatizada:
`requests-api/tests/parity/test_invoice_issuance_parity.py`.

**Legado:** plugin `invoice-issuance` + rotas api-delpi `/invoice-issuance/*`  
**Novo:** MFE `my-requests` + `requests-api` `/v1/*` (lookups via `ApiDelpiAdapter`)

Dual-run: legado permanece intacto até cutover completo; E8 entregou script de migração + banner/guia de depreciação.

## Matriz §20.3

| Caso | Legado | Novo | Automatizado | Status |
|------|--------|------|--------------|--------|
| Criar solicitação venda 1 item | `POST …/requests` | `POST /v1/requests` + validator | `test_p0_create_sale_one_item` | pass (CI) |
| Listar fila pending | `GET …/requests?status=open` | `GET /v1/requests/work-queue` | `test_p0_work_queue_lists_pending` | pass (CI) |
| start → issue | `POST start`, `POST issue` | `transitions/start`, `transitions/issue` (= `complete`) | `test_p0_start_then_issue_complete` | pass (CI) |
| return → edit → resubmit | PATCH + resubmit | `return` + PATCH payload + `resubmit` | `test_p0_return_patch_resubmit` | pass (CI) |
| cancel pending (owner) | `POST cancel` | `transitions/cancel` | `test_p0_cancel_pending_owner` | pass (CI) |
| cancel in_progress (process) | `POST cancel` | `transitions/cancel` | `test_p0_cancel_in_progress_processor` | pass (CI) |
| allowed_actions por papel | get detail | get detail / engine | `test_p0_allowed_actions_by_role` | pass (CI) |
| Gate filial 403 | `branch_access` | `branch_forbidden` | `test_p0_branch_gate_403` | pass (CI) |
| Notificação create | Core sino direto | outbox `request.created` → Core | `test_p0_notification_outbox_on_create` | pass (CI) |
| Lookup parties/products/carriers/OV/saldo | GET api-delpi | adapter + `/lookups/*` | `test_p0_lookup_shapes_match_golden` | pass (CI) |
| Aliases de status | `pending` / `returned` / `issued` | `statusAliases` no workflow | `test_p0_status_aliases_match_legacy` | pass (CI) |

## E9 verify (2026-09-03)

| Checagem | Resultado |
|----------|-----------|
| `pytest requests-api/tests` | **91 passed** |
| `plugins/my-requests` vitest + typecheck + build | **16 passed** / OK |
| `plugins/invoice-issuance` vitest (banner E8) | **45 passed** |
| Homologação live dual-run / TOTVS | **não executado live** neste verify |
| Dry-run migração em staging | Runbook pronto; apply fica a cargo do operador |
| Rebuild sequential (plugin-ui → MFEs → requests-api) | **OK** (2026-09-03) |

## Gaps live (não bloqueiam CI)

| Gap | Motivo | Quando fechar |
|-----|--------|---------------|
| Dual-run UI lado a lado em staging | Exige operadores + stack TOTVS | Homologação operacional |
| Lookups contra TOTVS real | Suite usa `InMemoryOperationalLookupAdapter` + golden de chaves; shape HTTP live fica no smoke api-delpi | Smoke ambiente com Protheus |
| Apply migração de dados em prod | Script + runbook E8 prontos; dry-run obrigatório antes | Operação após staging |
| Remoção do plugin legado | Dual-run obrigatório | Release major pós-janela |

## Como rodar

```bash
cd requests-api
.venv/bin/python -m pytest tests/parity/ -q
# ou
pytest tests/parity/ -q
```

## Contrato de aliases (referência)

| Canônico (novo) | Alias (legado / UI) |
|-----------------|---------------------|
| `submitted` | `pending` |
| `needs_information` | `returned` |
| `completed` | `issued` |
| ação `complete` | alias `issue` |
