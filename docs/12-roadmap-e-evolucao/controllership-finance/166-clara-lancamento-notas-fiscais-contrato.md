# 166 — CLARA × Lançamento de Notas Fiscais (contrato F7)

> Status: **F7-R4** (entrada CF∨LNF + knowledge por escopo) · **F7.4 PENDING_OWNER**  
> Data: 2026-11-13  
> Tools públicas: **sempre as 6** (`get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete`)  
> Catálogo: `clara-semantic-v1` — novas entradas `(entity, action)`, sem tool nova

---

## 0. Porta de entrada e knowledge (F7-R4)

| Regra | Detalhe |
|---|---|
| Entrada MCP | `principal_type=user` (D8) **e** (`controllership-finance.access` **ou** `.manage` **ou** `.access.dre` **ou** qualquer `lancamento-notas-fiscais.*`) |
| Sem nenhuma | 403 `forbidden` / `authz` — log `clara_mcp_authz_denied gate=entry` |
| Catálogo | Gate `access` = CF efetiva; `lnf_*` = famílias LNF; `clara_entry` = knowledge visível a quem passou na porta |
| Negação por ação | `Você não tem permissão para <entity.action>.` — `gate=catalog` |
| BFF | Continua autoridade: CLARA chama a rota com o JWT do usuário |
| Knowledge `controllership` | Corpus PROC-0072 (itens com `domain_scope=controllership`, default V022) — liberado a quem tem CF* |
| Knowledge `lancamento-notas-fiscais` | Corpus LNF (`corpus_manifest_lnf.py`) — liberado a quem tem qualquer LNF* |
| Ambos | União dos escopos; get de item fora do escopo → 404/not found (sem vazar título) |

### Matriz perfil × tool (esperado)

| Perfil | get_context catalog | read/analyze/execute LNF | fechamento | knowledge |
|---|---|---|---|---|
| Só-LNF (P11/P6B/P2/P8) | só `lnf_*` + knowledge | conforme gate LNF | 403 | só domínio LNF |
| Só-CF | fechamento; sem `lnf_*` | 403 | igual hoje | só controllership |
| CF+LNF | ambos | ambos | ambos | ambos |
| P0 | 403 entry | 403 | 403 | 403 |
| P10 serviço | 401/403 D8 | — | — | — |

---

## 1. Inventário (CONFIRMADO_NO_CODIGO)

| Item | Evidência |
|---|---|
| Serviço MCP | In-process na BFF `controllership-finance-api` — mount `/mcp` (`main.py`) |
| Pasta | `controllership_finance_app/interface/mcp/` + `application/clara/` |
| Compose | `infra/docker-compose.yml` / `.hml.yml` serviço `controllership-finance-api` |
| Catálogo | `semantic_bridge.py` → `SEMANTIC_CATALOG_VERSION = clara-semantic-v1` |
| Governed | `governed_writes.py` + `invoice_posting_capabilities.py` |
| Apresentação LNF | `application/clara/invoice_posting_presentation.py` → merge em `operation_presentation._PRESENTERS` |
| HML | Mesma BFF (`delpi-hml-controllership-finance-api`) — sem container CLARA separado |
| Endpoint | `POST {PUBLIC}/apps/controllership-finance-api/mcp` JSON-RPC |

### Identidade (R2 / H2) — **SIM, JWT do usuário final**

1. Transporte MCP exige JWT humano; **service token proibido** (`auth_middleware` + `delpi_mcp`).
2. Tools leem ContextVar / Request reconstruída com o **mesmo Bearer**.
3. Rotas LNF usam `get_current_user()` + `@require_*` — AuthZ na BFF.
4. Não há hop MCP→BFF com principal de serviço.

---

## 2. Catálogo alvo (implementado)

| Tool | entity.action | Rota BFF | Gate catálogo | Política |
|---|---|---|---|---|
| read | `invoice_posting.list` | GET `/requests` | `lnf_read` | — |
| read | `invoice_posting.get` | GET `/requests/{id}` | `lnf_read` | + `app_links` (PDF/XML no app) |
| read | `invoice_posting.purchase_orders` | GET `/requests/{id}/purchase-orders` | `lnf_read` | — |
| read | `purchase_order.open` | GET `/purchase-orders/open` | `lnf_create` | — |
| read | `received_invoice.list` | GET `/received-invoices` | `lnf_create` | — |
| read | `received_invoice.detail` | GET `/received-invoices/{id}/detail` | `lnf_create` | — |
| read | `unmapped_product.list` | GET `/unmapped-products` | `lnf_review_unmapped` | — |
| read | `supplier.search` | GET `/suppliers` | `lnf_create` | — |
| analyze | `invoice_posting_backlog` | composição dos reads | `lnf_read` | FACT/RECOMMENDATION; **wire enum** em `tools/list` (alias dispatch `invoice_posting.backlog`) |
| execute | `invoice_posting.comment` | POST `.../comments` | `lnf_write` | **direct** |
| execute | `reconciliation.refresh` | POST `/reconciliation/refresh` | `lnf_read` | **direct** |
| execute | `invoice_posting.create` | POST `/requests` | `lnf_create` | governed + presentation |
| execute | `invoice_posting.update` | PATCH `/requests/{id}` | `lnf_write` | governed + presentation |
| execute | `invoice_posting.link_purchase_order` | POST `.../link` | `lnf_process` | governed + presentation |
| execute | `invoice_posting.start` | POST `.../start` | `lnf_process` | governed + presentation |
| execute | `invoice_posting.block` | POST `.../block` | `lnf_process` | governed + presentation |
| execute | `invoice_posting.resume` | POST `.../resume` | `lnf_process` | governed + presentation |
| execute | `invoice_posting.post_manual` | POST `.../post-manual` | `lnf_process` | governed + **justificativa** + presentation |
| execute | `reconciliation.run` | POST `/reconciliation/run` | `lnf_manage` | governed + presentation |
| delete | `invoice_posting.cancel` | POST `.../cancel` | `lnf_write` | destructive + **justificativa** + presentation |

PDF/XML: **não** são tools — resposta aponta `app_links` → `/apps/lancamento-notas-fiscais`.

Gates mapeiam as mesmas famílias de permissão dos decorators BFF (`permissions.py`).

### F7-R — defeitos do conector (2026-11-13) e correção

| Defeito | Correção |
|---|---|
| `analyze.analysis_type` enum só `closing_blockers`/`report_comparison` | chave canônica `invoice_posting_backlog` em `ANALYZE_ACTIONS` → publicada no enum |
| `execute invoice_posting.start` prepare com `displayable=false` | `LNF_PRESENTERS` para todas as capabilities LNF |

---

## 3. Arquivos canônicos

| Peça | Path |
|---|---|
| Reads/analyze | `interface/mcp/invoice_posting_bridge.py` |
| Registry | `interface/mcp/semantic_bridge.py` |
| Governed LNF | `application/clara/invoice_posting_capabilities.py` |
| Presentation LNF | `application/clara/invoice_posting_presentation.py` |
| Merge/gates | `application/clara/governed_writes.py` |
| Identity flags | `interface/mcp/tool_bridge.py` (`_mcp_identity`) |
| Testes | `tests/test_clara_lnf_catalog.py`, `test_clara_lnf_presentation.py`, `test_clara_catalog_schema_callable.py` |

---

## 4. Plano de testes

### DEV / unitário
- `tools/list` = 6 tools
- Catálogo: entradas LNF só com flags `lnf_*`
- Capabilities: comment/refresh direct; demais governed; cancel destructive; justificativas obrigatórias
- **F7-R:** enum contém `invoice_posting_backlog`; toda entrada do catálogo valida contra `inputSchema` (jsonschema); presenters LNF com `displayable=true`

### HML (JSON-RPC MCP, usuários `lnf-contract-p*`)
- Positivo: perfil com permissão vê entrada e obtém mesmos dados que a rota BFF
- Negativo: sem permissão → ausente no catálogo / 403 na tool
- P10 serviço → 401/403 no `/mcp`
- Prepare não muta; commit com `confirmation=true` muta; proposta de outro ator rejeitada
- Cancel/post_manual sem justificativa → rejeitado
- **F7-R:** E2E prepare→commit (create/start/update/block/resume/cancel/post_manual/recon.run) + expire + branch deny + batch; canal `conversational` **somente HML** para automação

### PROD
- Deploy BFF; health; enum/tools/list; presentation
- Canal de consentimento: **`conversational`** (aceite operacional do owner — `mcp_tool_confirmation_owner_risk_accepted_v2`). **Não alterar** `CLARA_CONSENT_CHANNEL` em PROD nesta trilha; variação de canal só em HML.
- **Sem commit** com dados reais nos reworks F7-R / F7-R2
- Roteiro owner (F7.4) — ver Parte 6 da trilha 165; refrescar tools no conector

### F7-R2 (2026-11-13) — EXECUTION_DRIFT

No F7-R o Cursor forçou PROD para `portal` fora da trilha. Owner determinou reversão imediata para `conversational`. Regra permanente: trilha 165 §0.3 item 8.

---

## 5. Fora de escopo (explícito)

- Persona/ficha da CLARA
- MFE LNF
- Tools MCP novas além das 6
- Escrita Protheus (H3)
- F6 limpeza
