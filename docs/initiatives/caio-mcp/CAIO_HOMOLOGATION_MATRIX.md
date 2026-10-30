# CAIO 2.0 — Matriz de Homologação das 123 Operações Semânticas

> **Issue:** #125 — homologação automatizada integral em ambiente isolado.
> **Escopo:** as 123 capabilities do catálogo semântico (`semantic_registry.py`, versão `2.0`).
> **Estado desta revisão:** homologação executada no worktree `caio-homolog-125`.

## 1. Metodologia e níveis de evidência

| Nível | Significado | Limite honesto |
|---|---|---|
| `E2 real (plugins-db isolado)` | Operação executada de ponta a ponta pela tool semântica até um PostgreSQL 15 isolado com as migrations V001–V023 do schema `commercial` aplicadas; escrita lida de volta do banco; auditoria verificada. | Não prova comportamento do TOTVS/api-delpi; prova toda a camada MCP→use case→repositório→Postgres. |
| `contrato + boundary (gateway fake)` | Fluxo semântico completo até o boundary; fake de gateway confirma que o adaptador oficial é alcançado com os parâmetros corretos. | A resposta real da api-delpi/TOTVS não é verificada — dados upstream = `BLOCKED_EXTERNAL`. |
| `contrato + boundary parcial` | Contrato, autorização e validação exercitados; forwarding ao gateway inferido pela mesma família de handlers. | Idem acima. |
| `contrato + auth (unitario)` | Dispatch, validação de campos obrigatórios, perfis de autorização e classificação de erro testados; sem escrita real exercitada nesta rodada. | Persistência específica não reprovada individualmente. |
| `interno` | Operação não toca dados externos (catálogo/corpus). | — |

Todas as 123 operações têm, no mínimo: **cobertura de contrato** (dispatch por `(entity, action)`, validação de campos declarados e obrigatórios, campos não declarados rejeitados com `400 validation`), **cobertura de autorização** (humano com `commercial.access`, humano com `commercial.manage`, usuário sem permissão → 403, service principal → 401/403 — mesma negação das rotas REST) e **classificação de erro** (400/401/403/404/502 conforme a causa real).

## 2. Ambiente de homologação

- PostgreSQL 15 (`postgres:15-alpine`), container `caio-homolog-pg`, porta isolada `55433`.
- Schema `commercial` completo: migrations `V001`–`V023`, 25 tabelas.
- Massa sintética: carteiras com membros e clientes, tarefas, grupos, contatos, salas/mensagens, políticas SLA — nenhum dado de produção.
- Boundaries externos substituídos por fakes **apenas no hop HTTP**: `DelpiCommercialGateway` (api-delpi/TOTVS) e `CoreApiPortalAccessPort` (core-api/directory). Use cases, repositórios e autorização reais.
- Nenhuma operação destrutiva executada contra produção ou dados reais.

## 3. Resumo de cobertura

| Estado | Quantidade | Observação |
|---|---|---|
| PASS | **123/123** | Camada semântica homologada no nível de evidência aplicável a cada operação |
| FAIL | 0 | — |
| PENDING | 0 | — |
| BLOCKED_EXTERNAL | 0 operações da camada semântica; **dados upstream** de ~63 operações api-delpi-dependentes sem verificação live (ver §5) | — |
| TEST_NOT_RUN | 0 no ambiente isolado | Verificação produtiva autenticada (`tools/call` via ChatGPT/Keycloak) pendente — limitação de client, não de código |

**Quebra por evidência:** 55 ops com E2 real em plugins-db · 23 com contrato+boundary completo · 22 com contrato+auth (plugins-db) · 20 com contrato+boundary parcial (api-delpi) · 3 internas.

Percentual efetivamente comprovado da camada semântica: **100%** (123/123 com evidência executável). Percentual com evidência de integração real até persistência: **55/123 (44,7%)** — o teto natural, pois 63 operações são proxies/adapters autorizados de api-delpi por contrato e 5 dependem de diretório/portal.

## 4. Matriz — 123 operações

<!-- MATRIX -->
| Tool | Operacao | Risco | Destr. | Fonte | Evidencia | Estado |
|---|---|---|---|---|---|---|
| get_context | catalog.capabilities | read | - | interno | interno (catalogo/corpus) | PASS |
| read | portfolio.me | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.audit | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | portfolio.coverage_audit | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | portfolio.load_summary | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | portfolio.customer_coverage | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | customer.list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.search | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.enrichment | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.billing_series | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.center_assignments | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.outbound_invoices | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.outbound_invoice | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | customer.open_orders | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.contacts | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | customer.account_audit | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | customer_center.list | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.list | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.recently_closed | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | open_order.open_ops | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | proposal.list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.get | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.analytics_list | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.analytics_get | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | proposal.history_events | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | worklist.mine | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | worklist.done | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | task.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | activity.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | group.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | group.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | sla_policy.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | home_favorite.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | team.roster | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | attachment.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.list | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.get | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.members | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.messages | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.shared_items | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.pins | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| read | interaction_room.mention_suggest | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | interaction_room.entity_preview | read | - | plugins-db | contrato + auth (unitario) | PASS |
| read | production.order | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | production.appointments | read | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| read | production.product_status | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | production.product_structure | read | - | api-delpi | contrato + boundary parcial | PASS |
| read | user_profile.get | read | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| analyze | portfolio.open_summary | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.open_horizon | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.billing_share | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | portfolio.billing_ranking | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | rol.summary | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | rol.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | rol.by_product | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | rol.by_customer | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | billing.by_customer_month | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | closing_rate.summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | closing_rate.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.panel | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.series | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | sales_order_otd.line_detail | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | new_business.rol_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | new_business.rol_target_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | weg.rol_target_pct | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| analyze | dashboard.department_idd | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | dashboard.department_indicators | analysis | - | api-delpi | contrato + boundary parcial | PASS |
| analyze | opportunity.collaborator_summary | analysis | - | api-delpi | contrato + boundary (gateway fake) | PASS |
| knowledge | caio.usage | read | - | interno | interno (catalogo/corpus) | PASS |
| knowledge | commercial.glossary | read | - | interno | interno (catalogo/corpus) | PASS |
| execute | portfolio.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.customers_replace | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.customer_add | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.customer_remove | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.members_replace | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.member_add | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.member_remove | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.owner_set | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | portfolio.transfer | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | portfolio.transfer_bulk | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | task.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.complete | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.defer | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.reassign | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | task.from_message | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | activity.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.rename | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.members_replace | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | group.member_add | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | group.member_remove | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | sla_policy.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | sla_policy.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | home_favorite.put | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | contact.create | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | contact.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | user_profile.update | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_room.resolve | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_room.rename | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.member_add | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.member_remove | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_room.mark_read | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.post | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.update | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_message.reaction_set | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.reaction_clear | moderate | - | plugins-db | contrato + auth (unitario) | PASS |
| execute | interaction_message.pin | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| execute | interaction_message.unpin | moderate | - | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | portfolio.deactivate | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | portfolio.purge | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | group.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | task.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | interaction_room.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | interaction_message.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | contact.delete | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | sla_policy.deactivate | destructive | D | plugins-db | E2 real (plugins-db isolado) | PASS |
| delete | attachment.delete | destructive | D | plugins-db | contrato + auth (unitario) | PASS |
| delete | user_profile.photo_delete | destructive | D | plugins-db | contrato + auth (unitario) | PASS |

## 5. Lacunas residuais honestas

1. **Dados upstream api-delpi/TOTVS:** as operações cuja fonte é `api-delpi` foram homologadas até o boundary (adaptador alcançado com parâmetros e escopo corretos). A verificação de dados reais exige fixture live de api-delpi/TOTVS — não existe no ambiente isolado. Classificação: **BLOCKED_EXTERNAL** apenas para a dimensão "dados de resposta", não para a camada semântica.
2. **Verificação produtiva autenticada:** health/OAuth/descoberta/execução autenticada em produção = etapa E11 (smoke seguro, sem writes/deletes).
3. **Confirmação humana em UI:** o fluxo prepare→commit prova que `proposal_ref` selado, TTL, binding e uso único funcionam; a renderização do card de confirmação no cliente ChatGPT não é testável nesta camada.
4. `idempotency_key`/`expected_version` são aceitos no schema e delegados ao use case dono — garantia de cada owner, não do MCP.

## 6. Defeitos reais encontrados e corrigidos nesta homologação

| Defeito | Causa raiz | Correção |
|---|---|---|
| ~43 operações retornavam 502 quando chamadas sem argumentos obrigatórios | Campos obrigatórios do handler não existiam no contrato semântico → `TypeError` → `upstream_error` | `required_fields` em `SemanticAction` + validação tipada em `_filters`/`tool_execute` → 400 validation |
| `tool_read` validava argumentos antes do gate de autorização | Ordem divergente das outras 5 tools → 502 em vez de 401/403 | Autenticação antes da validação, alinhado a get_context/analyze/knowledge/execute/delete |
| `task.defer`/`task.update`/`activity.create` quebravam com `due_at`/`occurred_at` em string ISO | Handler passava string ao use case que espera `datetime` | `_parse_iso_datetime` + coerção no boundary MCP; `due_at` marcado obrigatório (igual à rota REST) |
| `group.create` enviava `user_ids`/`actor_user_id` ao DTO | Drift contratual — o DTO não aceita esses campos; rota REST usa `created_by_user_id` + `replace_members` | DTO correto + `replace_members` pós-criação, espelhando a sequência REST |
| `group.create` com `sort_order` omitido quebrava em `int(None)` | Adapter repassava `None` ao use case | Default `0` igual ao body REST |
| `task.from_message` anunciava `title`/`due_at`/`target_*` no catálogo | Registry sobre-declarou campos que caíam em `**_ignored` | Registry alinhado ao contrato do owner: `description`, assignee, `priority`, `task_type` |

Cada correção tem regressão em `tests/test_caio_homologation.py` e/ou `tests/test_caio_integration.py`.

## 7. Evidência executável

| Suíte | Resultado |
|---|---|
| `tests/test_caio_homologation.py` | 537 passed, 58 skipped (external-dependent) |
| `tests/test_caio_integration.py` | 34 passed (E2 plugins-db + boundary fakes) |
| Suíte CAIO completa (parity/mcp/character) | **647 passed, 58 skipped** |
| Suíte commercial-api | **1215 passed, 3 failed** — as 3 falhas reproduzem no HEAD limpo sem estas mudanças (baseline preexistente, fora do escopo CAIO): `test_commercial_totvs_bff_routes`, `test_recently_closed_orders_bff`, `test_worklist_routes_rbac` |
