# Paridade P0 — invoice-issuance (legado × my-requests)

Espelho do checklist [PLAYBOOK.md §20.3](./PLAYBOOK.md). Suite automatizada:
`requests-api/tests/parity/test_invoice_issuance_parity.py`.

**Legado:** plugin `invoice-issuance` + rotas api-delpi `/invoice-issuance/*`  
**Novo:** MFE `my-requests` + `requests-api` `/v1/*` (lookups via `ApiDelpiAdapter`)

Dual-run: legado permanece intacto até E8.

## Matriz §20.3

| Caso | Legado | Novo | Automatizado | Status |
|------|--------|------|--------------|--------|
| Criar solicitação venda 1 item | `POST …/requests` | `POST /v1/requests` + validator | `test_p0_create_sale_one_item` | pass |
| Listar fila pending | `GET …/requests?status=open` | `GET /v1/requests/work-queue` | `test_p0_work_queue_lists_pending` | pass |
| start → issue | `POST start`, `POST issue` | `transitions/start`, `transitions/issue` (= `complete`) | `test_p0_start_then_issue_complete` | pass |
| return → edit → resubmit | PATCH + resubmit | `return` + PATCH payload + `resubmit` | `test_p0_return_patch_resubmit` | pass |
| cancel pending (owner) | `POST cancel` | `transitions/cancel` | `test_p0_cancel_pending_owner` | pass |
| cancel in_progress (process) | `POST cancel` | `transitions/cancel` | `test_p0_cancel_in_progress_processor` | pass |
| allowed_actions por papel | get detail | get detail / engine | `test_p0_allowed_actions_by_role` | pass |
| Gate filial 403 | `branch_access` | `branch_forbidden` | `test_p0_branch_gate_403` | pass |
| Notificação create | Core sino direto | outbox `request.created` → Core | `test_p0_notification_outbox_on_create` | pass |
| Lookup parties/products/carriers/OV/saldo | GET api-delpi | adapter + `/lookups/*` | `test_p0_lookup_shapes_match_golden` | pass |
| Aliases de status | `pending` / `returned` / `issued` | `statusAliases` no workflow | `test_p0_status_aliases_match_legacy` | pass |

## Gaps live (não bloqueiam CI)

| Gap | Motivo | Quando fechar |
|-----|--------|---------------|
| Dual-run UI lado a lado em staging | Exige operadores + stack TOTVS | Homologação E9 / checklist manual |
| Lookups contra TOTVS real | Suite usa `InMemoryOperationalLookupAdapter` + golden de chaves; shape HTTP live fica no smoke api-delpi | Smoke ambiente com Protheus |
| Migração de dados `invoice_issuance` → `my_requests` | Fora do escopo E6 | E8 |
| Remoção do plugin legado | Dual-run obrigatório | E8 cutover |

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
