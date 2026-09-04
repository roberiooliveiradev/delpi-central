# Paridade P0 — invoice-issuance (legado × my-requests)

Espelho do checklist [PLAYBOOK.md §20.3](./PLAYBOOK.md). Suite automatizada:
`requests-api/tests/parity/test_invoice_issuance_parity.py`.

**Legado (retido):** schema/volume `invoice_issuance` + rotas api-delpi `/invoice-issuance/*` (lookups até E17+)  
**Canônico:** MFE `my-requests` + `requests-api` `/v1/*`  
**Cutover:** soft E12 (menu + redirect) + hard E13 (MFE fora do Compose) — entregues.

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

## E15 verify (2026-09-04) — evidência automatizada

| Checagem | Resultado |
|----------|-----------|
| `pytest requests-api/tests/parity/ -q` | **15 passed** |
| Dry-run migração (`delpi-requests-api`) | JSON sem erros; `legacy_requests=0`, `missing_attachment_files=[]` (ambiente local sem histórico legado) |
| `--apply` migração (mesmo container) | No-op idempotente; `migrated=0`, `errors=[]` |
| Health api-delpi | **200** |
| Homologação UI live (wizard + fila + TOTVS) | **Pendente assinatura Ops** — ver gate abaixo itens 1–2 |

### Migração aplicada (evidência)

```json
{
  "legacy_requests": 0,
  "already_migrated": 0,
  "to_migrate": 0,
  "migrated": 0,
  "attachments_copied": 0,
  "missing_attachment_files": [],
  "errors": []
}
```

Ambientes com histórico: repetir dry-run → `--apply` em staging e depois prod conforme [MIGRATION-RUNBOOK.md](./MIGRATION-RUNBOOK.md); colar o JSON aqui.

## Gaps live (não bloqueiam CI)

| Gap | Motivo | Quando fechar |
|-----|--------|---------------|
| UI live wizard + fila + transitions | Exige operadores + stack TOTVS | Gate itens 1–2 (Ops) |
| Lookups contra TOTVS real no browser | Suite usa memory/golden; smoke Protheus | Gate item 2 |
| Apply migração com dados reais | Este ambiente tinha `legacy_requests=0` | Staging/prod com volume legado |
| Remoção rotas lookup `/invoice-issuance/*` | Adapter ainda usa até E17 | E17+ |

## Gate soft cutover / ops (E12–E15)

| # | Item | Responsável | Feito |
|---|------|-------------|-------|
| 1 | Checklist §20.3 exercitado live (criar / fila / start→issue / return / cancel) no canônico my-requests | Ops | [ ] UI |
| 2 | Smoke lookups TOTVS reais via wizard my-requests (`parties` / `products` / `carriers`) | Ops | [ ] UI |
| 3 | Dry-run migração sem `missing_attachment_files` críticos | Ops/Dev | [x] 2026-09-04 (env local; 0 legado) |
| 4 | `--apply` migração + amostragem de anexos | Ops/Dev | [x] 2026-09-04 no-op local; **reaplicar** se staging/prod tiverem dados |
| 5 | Comunicação: menu oculto + redirect gateway; MFE fora do Compose (E12–E13) | Produto | [x] |
| 6 | Lookups api-delpi disponíveis enquanto adapter precisar (E17 migra path) | Dev | [x] |

## Como rodar

```bash
cd requests-api
.venv/bin/python -m pytest tests/parity/ -q

docker exec delpi-requests-api \
  python scripts/migrate_invoice_issuance_to_my_requests.py
# apply (staging/prod após dry-run OK):
docker exec delpi-requests-api \
  python scripts/migrate_invoice_issuance_to_my_requests.py --apply
```

## Contrato de aliases (referência)

| Canônico (novo) | Alias (legado / UI) |
|-----------------|---------------------|
| `submitted` | `pending` |
| `needs_information` | `returned` |
| `completed` | `issued` |
| ação `complete` | alias `issue` |
