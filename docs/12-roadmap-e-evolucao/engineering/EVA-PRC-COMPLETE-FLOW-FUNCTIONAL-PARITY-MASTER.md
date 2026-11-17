# EVA × PRC — Paridade Funcional Completa (Solicitações + Produtos Acompanhados)

**TASK_ID:** `EVA-PRC-COMPLETE-FLOW-SEMANTIC-PARITY-02`
**BASE_HEAD:** `6e9edf8ca3` (baseline funcional `74992dafd7`)
**Status:** DEPLOYED — HML + PRD publicados, ChatGPT smoke pendente PO
**Owner:** Engineering API (autoridade de dados, workflow, AuthZ)
**Fachada:** EVA/MCP — exatamente 6 tools, sem novas tools

---

## 1. Objetivo

Paridade funcional completa entre o módulo **Controle e Cadastro de
Produtos** da Engineering API e as capacidades semânticas da EVA,
abrangendo:

- **A. Solicitações** — ciclo completo: intake, consulta, atendimento,
  correções, rodadas de esclarecimento, validação, conclusão, rejeição,
  conversas e metadados documentais.
- **B. Produtos Acompanhados** — registros técnicos: lista, ficha,
  revisões, comparação, bandeiras (leitura **e** escritas governadas),
  eventos de auditoria.

A EVA executa as mesmas operações elegíveis que um usuário autorizado
executaria pelo Portal Engenharia, respeitando regras, estados e
permissões oficiais. A Engineering API permanece a autoridade — nenhuma
regra de negócio é duplicada no MCP.

## 2. Escopo e exclusões

**Dentro:** todos os endpoints PRC de
`engineering-api/engineering_app/interface/http/routes/product_registration_routes.py`
e seus use cases em
`engineering-api/engineering_app/application/use_cases/product_registration/service.py`,
mais os consumers frontend (`plugins/my-requests/.../product-registration/`,
`plugins/engineering/.../product-registration/`).

**Fora de escopo:** LMP, NC, desenhos/jobs, estruturas/roteiros,
qualquer escrita TOTVS/Protheus, migrations, mudanças de RBAC/Core.

## 3. Sources of truth

| Fonte | Papel |
|---|---|
| `product_registration_routes.py` | Contrato REST canônico (~57 rotas) |
| `service.py` (ProductRegistrationService) | Regras de domínio oficiais |
| `semantic_registry.py` | Catálogo `entity.action` + gate `proven` |
| `semantic_bridge.py` | Dispatch REST×MCP + AuthN obrigatória |
| `prc_semantic.py` | Handlers que delegam aos mesmos use cases |
| `prcApi.ts` / `prcConversationApi.ts` (MFEs) | Consumers frontend |

## 4. Arquitetura e ownership

```text
ChatGPT ──MCP──▶ tool_read/tool_execute (6 tools fixas)
                    │ registry proven + AuthN humano obrigatório
                    ▼
              prc_semantic handlers
                    │ mesmos use cases da REST
                    ▼
        ProductRegistrationService (owner)
                    │ AuthZ live por objeto + CAS + idempotência
                    ▼
        repo engineering + api-delpi delegado (Bearer humano, TOTVS read-only)
```

Decisões irrevogáveis preservadas: 6 tools (`get_context`, `read`,
`analyze`, `knowledge`, `execute`, `delete`); sem SQL/acesso a outro
bounded context; autor humano autenticado sempre; `channel="eva"`
auditado; terminais/destrutivos via proposta selada + confirmação
humana verificável; ACT flippado por `ENG_EVA_ACT_ENABLED`.

## 5. Inventário — Solicitações PRC

| # | Operação REST | Capability EVA | Tool | Status | Observação |
|---|---|---|---|---|---|
| 1 | POST `/intake/requests` | `submit` | execute | proven | existente |
| 2 | GET `/requests` | `list` | read | proven | `view=pending` preset |
| 3 | GET `/requests/{id}` | `detail` | read | proven | |
| 4 | GET `/requests/{id}/timeline` | `timeline` | read | proven | |
| 5 | PATCH `/requests/{id}/draft` | `update_draft` | execute | proven | CAS |
| 6 | POST `…/actions/request-information` | `request_information` | execute | proven | |
| 7 | POST `…/actions/return-for-correction` | `return_for_correction` | execute | proven | |
| 8 | PATCH `…/returned-fields` | `save_returned_fields` | execute | proven | CAS |
| 9 | POST `…/actions/resubmit-correction` | `resubmit_correction` | execute | proven | |
| 10 | GET `…/correction-returns` | `correction_return_list` | read | **novo** | |
| 11 | GET `…/correction-returns/{rid}` | `correction_return_get` | read | **novo** | |
| 12 | POST `…/actions/route-divergence` | — | — | **EXCLUDED** | rota REST `deprecated` — REF-021 não é etapa compulsória do Portal; omitida de `allowedActions` |
| 13 | GET `…/information-rounds` | `information_round_list` | read | proven | |
| 14 | GET `…/information-rounds/{rid}` | `information_round_get` | read | proven | |
| 15 | PATCH `…/rounds/{rid}/answers` | `information_draft_answers` | execute | **novo** | requester-only, CAS round |
| 16 | POST `…/rounds/{rid}/actions/submit-answers` | `information_submit_answers` | execute | **novo** | requester-only, CAS |
| 17 | POST `…/questions/{qid}/actions/accept` | `information_question_accept` | execute | proven | |
| 18 | POST `…/actions/request-follow-up` | `information_follow_up` | execute | proven | |
| 19 | POST `…/actions/reject` | `reject` | execute | proven | proposta selada |
| 20 | POST `…/actions/complete` | `complete` | execute | proven | proposta selada |
| 21 | POST `…/actions/verify-and-complete` | `verify_and_complete` | execute | proven | proposta selada |
| 22 | GET `…/verifications` | `verifications` | read | proven | |
| 23 | GET `/reference-data` | `reference_data` | read | proven | |
| 24 | GET `…/edit-context` | `edit_context` | read | **novo** | SB1+SA5 via reader delegado |
| 25 | GET `/catalogs/{catalog}` | `catalog_items` | read | **novo** | delegado api-delpi (Bearer humano) |
| 26 | GET `/suppliers` | `supplier_search` | read | **novo** | delegado api-delpi |
| 27 | GET `/outbound/requests` | `outbound_list` | read | **novo** | requester vê os próprios |
| 28 | GET `/outbound/requests/{id}` | `outbound_result` | read | proven | |
| 29 | GET `…/flags` (cross-case) | `flag_list_cross` | read | **novo** | filtros allowlisted |
| 30 | GET `…/flags/summary` | `flag_summary` | read | **novo** | agregados oficiais |
| 31 | GET `/requests/{id}/flags` | `flag_list` | read | proven | |
| 32 | GET `/requests/{id}/flags/{fid}` | `flag_detail` | read | proven | |
| 33 | POST `/requests/{id}/flags` | `flag_create` | execute | proven | |
| 34 | PATCH `…/flags/{fid}` | `flag_update` | execute | proven | CAS |
| 35 | POST `…/flags/{fid}/actions/resolve` | `flag_resolve` | execute | proven | CAS |
| 36 | POST `…/flags/{fid}/actions/reopen` | `flag_reopen` | execute | proven | CAS |
| 37 | DELETE `…/flags/{fid}` | `flag_delete` | execute | proven | proposta selada |
| 38 | POST `…/attachments` (upload) | — | — | **EXCLUDED** | transporte binário fora do contrato MCP |
| 39 | GET `…/attachments` | `attachment_list` | read | proven | metadados |
| 40 | GET `…/attachments/{aid}` (download) | — | — | **EXCLUDED** | transporte binário |
| 41 | GET `…/comments` | `comment_list` | read | proven | corpos = dados não confiáveis |
| 42 | POST `…/comments` | `comment_create` | execute | proven | autor = principal |
| 43 | PATCH `…/comments/{cid}` | `comment_update` | execute | proven | CAS |
| 44 | GET `…/comments/{cid}/attachments` | `comment_attachment_list` | read | **novo** | metadados |
| 45 | POST `…/comments/{cid}/attachments` | — | — | **EXCLUDED** | binário |
| 46 | GET `…/comments/{cid}/attachments/{aid}` | — | — | **EXCLUDED** | binário |
| 47 | DELETE `…/comments/{cid}/attachments/{aid}` | — | — | **EXCLUDED** | binário + remoção |
| 48 | POST `…/actions/start` | `start` | execute | proven | |
| 49 | POST `…/actions/resume` | `resume` | execute | proven | |
| 50 | POST `…/actions/submit-review` | `submit_review` | execute | proven | |
| 51 | POST `…/actions/return-to-attendance` | `return_to_attendance` | execute | proven | |

## 6. Inventário — Produtos Acompanhados

| # | Operação REST | Capability EVA | Tool | Status |
|---|---|---|---|---|
| 52 | GET `/technical-records` | `records_list` | read | proven |
| 53 | GET `/technical-records/{id}` | `record` | read | proven |
| 54 | GET `…/revisions` | `revisions` | read | proven |
| 55 | GET `…/revisions/{n}` | `revision` | read | proven |
| 56 | GET `…/comparison` | `revision_compare` | read | proven |
| 57 | GET `…/flags` | `record_flag_list` | read | proven |
| 58 | GET `…/flags/{fid}/events` | `record_flag_events` | read | **novo** |
| 59 | POST `…/flags` | `record_flag_create` | execute | **novo** |
| 60 | PATCH `…/flags/{fid}` | `record_flag_update` | execute | **novo** (CAS) |
| 61 | POST `…/flags/{fid}/actions/resolve` | `record_flag_resolve` | execute | **novo** (CAS, terminal) |
| 62 | POST `…/flags/{fid}/actions/remove` | `record_flag_remove` | execute | **novo** — destructive, proposta selada + confirmação humana |

## 7. Matriz REST × Frontend × EVA (síntese)

Consumers frontend: `plugins/my-requests/src/features/product-registration/`
(`prcApi.ts`, `prcConversationApi.ts`, `PrcCasePage`, `PrcRequestPage`) e
`plugins/engineering/src/features/product-registration/` — ambos chamam a
mesma superfície REST acima via adapters; **nenhuma operação frontend ficou
sem contraparte REST**.

| Bloco | REST | Frontend | EVA antes | EVA agora | Gap resolvido |
|---|---|---|---|---|---|
| Intake/consulta solicitações | 5 | sim | 5 | 5 | — |
| Correções | 6 (+list/get) | sim | 3 | 5 | return list/get |
| Rodadas de esclarecimento | 6 | sim | 4 | 6 | draft/submit answers |
| Workflow/ações | 8 | sim | 8 | 8 | — |
| Verificações | 1 | sim | 1 | 1 | — |
| Divergência (route) | 1 | oculto | 0 | 0 | EXCLUDED (deprecated) |
| Registros/revisões | 5 | sim | 5 | 5 | — |
| Bandeiras de produto | 6 | sim | 1 | 6 | events + writes governadas |
| Bandeiras de solicitação | 7 + 2 cross | sim | 7 | 9 | cross list + summary |
| Referência/catálogos/fornecedores | 4 | sim | 1 | 4 | edit_context, catalog, suppliers |
| Outbound | 2 | sim | 1 | 2 | outbound_list |
| Anexos (metadados) | 2 | sim | 1 | 2 | comment_attachment_list |
| Anexos (binários) | 5 | sim | 0 | 0 | EXCLUDED transporte |
| Comentários | 3 | sim | 3 | 3 | — |

## 8. Capabilities existentes (40)

list, detail, timeline, verifications, record, revisions, revision,
revision_compare, records_list, record_flag_list, reference_data,
outbound_result, flag_list, flag_detail, flag_create, flag_update,
flag_resolve, flag_reopen, flag_delete, comment_list, comment_create,
comment_update, attachment_list, information_round_list,
information_round_get, information_question_accept,
information_follow_up, submit, start, update_draft, request_information,
return_for_correction, save_returned_fields, resubmit_correction,
resume, submit_review, return_to_attendance, reject, complete,
verify_and_complete.

## 9. Capabilities adicionadas (16) — este ciclo

**Reads (10):** `correction_return_list`, `correction_return_get`,
`edit_context`, `catalog_items`, `supplier_search`, `outbound_list`,
`comment_attachment_list`, `record_flag_events`, `flag_list_cross`,
`flag_summary`.

**Executes (6):** `record_flag_create`, `record_flag_update`,
`record_flag_resolve`, `record_flag_remove` (destructive, proposta
selada), `information_draft_answers`, `information_submit_answers`.

## 10. Exclusões e decisões

| Operação | Decisão | Fundamento |
|---|---|---|
| `route_divergence` | **EXCLUDED** | Rota REST `deprecated`; REF-021 não é etapa compulsória e é omitida de `allowedActions` — expor na EVA reintroduziria fluxo legado |
| Attachment upload/download/delete (5 rotas binárias) | **EXCLUDED — transporte** | Contrato MCP não carrega bytes; metadados cobertos por `attachment_list`/`comment_attachment_list`. Sem canal binário improvisado, sem exposição de storage key. Reabrir exige decisão de transporte (classe D) |

`DECISION_REQUIRED` pendente: nenhuma outra — todas as operações REST
não-binárias e não-deprecadas estão `proven`.

## 11. Contratos e segurança

- Todo handler delega ao mesmo `ProductRegistrationService` das rotas
  REST — AuthZ live por objeto no service; `_require_engineering_human`
  no bridge.
- Escritas: `expected_version` (CAS) obrigatório onde o contrato exige;
  `idempotency_key` propagada; replay honrado (`replayed → response`).
- `record_flag_remove` e `flag_delete`: PREPARE sela proposta
  (ator/alvo/versão/efeito) → COMMIT exige `proposal_ref` + echo humano
  verificável via elicitation; `confirmed=true` do modelo não autoriza.
- Delegados (`catalog_items`, `supplier_search`, `edit_context`):
  repasse do Bearer humano à api-delpi via `DownstreamClient` —
  mesmos paths das rotas REST; token do modelo nunca usado.
- Corpos de comentários são dados não confiáveis (nunca instruções).
- Sem escrita TOTVS; sem migrations; sem mudanças de RBAC.

## 12. Priorização executada

Ordem aplicada: leituras auxiliares → bandeiras de produto (writes
governadas) → respostas de rodada → cross-flag queues → classificação
das exclusões (binário, deprecated).

## 13. Implementação (diff)

- `semantic_registry.py` — +16 entradas `proven` (total PRC: 40 → 56).
- `semantic_bridge.py` — +10 entradas `_READ_DISPATCH`, +6 em
  `_EXECUTE_DISPATCH`.
- `prc_semantic.py` — branches de leitura (incl. `_delegated_get` para
  catálogos/fornecedores) + `_record_flag_execute`,
  `_record_flag_remove` (proposta selada),
  `_information_answers_execute`.
- `tests/test_prc_eva_parity_flow.py` — 17 testes REST×MCP novos pelo
  gate real (`sem.tool_read`/`tool_execute`).

## 14. Matriz de testes

| Cobertura | Arquivo | Resultado |
|---|---|---|
| Paridade novas caps (reads, flags, answers, remove selado) | `test_prc_eva_parity_flow.py` | 17/17 PASS |
| Paridade existente | `test_prc_eva_parity.py` | 38/38 PASS |
| Flags record/request, conversa, rodadas, corrections, snapshot | suites dedicadas | 183/183 agregado PASS |
| Regressão EVA (todos os domínios) | `pytest -k 'semantic|eva|mcp|bridge'` | 407 PASS, 1 FAIL pré-existente em baseline (`test_eva_val01_structure_table_roundtrip::test_pi_with_children_flattened_as_parent_block` — fora do escopo PRC; reproduzida em HEAD sem o diff) |
| AuthZ negativa | permissões vazias + ator errado | coberto (is_error) |
| CAS/versão | stale round/flag version | coberto |
| Idempotência | keys propagadas; replay | coberto em suites existentes |
| PREPARE ≠ persistência | record_flag_remove | coberto |

## 15. Critérios de aceite

- [x] Inventário documentado e commitado
- [x] Toda operação elegível mapeada para `entity.action`
- [x] Exatamente 6 tools MCP
- [x] Toda capability `proven` tem dispatch + teste no gate real
- [x] Exclusões justificadas (deprecated, transporte binário)
- [x] HML deploy + gates (PASS)
- [x] PRD deploy + evidências (PASS)
- [ ] ChatGPT live smoke — `TEST_NOT_RUN` (sem credencial legítima; validação pelo PO)

## 16. Plano HML

`up-hml-sequential.sh --build engineering-api` em
`/home/operador/projetos-teste/delpi-central` → health → OAuth
discovery → `get_context` catalog → count PRC caps (esperado 56) →
tools == 6 → smoke read (`list` pending, `records_list`) com identidade
legítima se disponível.

## 17. Plano PRD

Promover artefato aprovado em HML via `up-prod-sequential.sh --build
engineering-api`; registrar digest antes/depois; rollback = retag do
digest anterior. Não habilitar flags novas; `ENG_EVA_ACT_ENABLED`
permanece como está em PRD (não alterar sem autorização específica).

## 18. Rollback

Sem schema change → rollback por imagem: retag do digest anterior +
script canônico. Commits podem ser revertidos sem migração reversa.

## 19. Evidências e histórico

| Item | Valor |
|---|---|
| Baseline | `74992dafd7` (40 caps) |
| HEAD de partida | `6e9edf8ca3` |
| PRC caps | 40 → **56** (todas proven) |
| MCP tools | 6 (inalterado) |
| REST inventariadas | ~62 rotas (incl. actions workflow) |
| Elegíveis mapeadas | 56 |
| Excluídas | 6 (5 binárias, 1 deprecated) |
| Decisão requerida | 0 |
| Testes novos | 17 (parity flow) |
| Falha pré-existente | 1 (`val01 structure_table_roundtrip`, baseline) |
| HML SHA | `21eb7f627f` |
| HML digest | `sha256:810a0edeaf51` — healthy, /health 200, discovery 200, 0 erros |
| HML runtime | 56 caps proven, 0 planned, 6 tools, 16 novas presentes |
| PRD SHA | `21eb7f627f` (mesmo commit — artefato equivalente) |
| PRD digest before | `sha256:380919358b64` (retido p/ rollback) |
| PRD digest after | `sha256:5c1212331307` — healthy, discovery 200, 0 erros |
| PRD runtime | 56 caps proven, 0 planned, 6 tools |
| ChatGPT live | `TEST_NOT_RUN` — token exige aud=URL-MCP + scope `mcp:tools`; validação pelo PO |
| Rollback | retag `380919358b64` + `up-prod-sequential.sh --build engineering-api`; sem schema change |
| Verificador | INCONCLUSIVE — motor `devin` sem login (persistente; não contornado) |

---

## Adendo — EVA-PRC-HOME-FORBIDDEN-ROOT-CAUSE-FIX-PROD-01 (17/11/2026)

### Sintoma

`read(entity="engineering", action="home")` → `data.status="partial"`
com `sections.requests/tasks = "forbidden"`, enquanto
`read(entity="product_registration", action="list")` retornava a fila
autorizada com sucesso para a mesma identidade.

### Root cause (CONFIRMADO_NO_CODIGO)

`tool_bridge._source_context` (caminho MCP) construía
`HomeSourceContext` **sem `permissions` e `is_superadmin`** — defaults
`frozenset()`/`False`. A rota REST (`home_routes.py`) projetava ambos
corretamente. As fontes in-process da Home
(`PrcQueueHomeSource`/`PrcMineHomeSource`) montavam então
`PrcActor(permissions=∅)` → `can_read=False` → `PrcForbiddenError` →
seção degradada para `forbidden`.

Caminho divergente validado: `product_registration.list` usa
`prc_actor_from_principal(context.user)` — projeção completa — por
isso funcionava. Hipóteses H1 (identidade) e H2 (permissões)
confirmadas como manifestações do mesmo defeito; H3–H6 descartadas
pelo diff de construção de contexto.

### Correção (menor mudança, owner correto)

`tool_bridge._source_context` passa a projetar
`permissions=frozenset(...)` e `is_superadmin` do principal humano —
mesma projeção da rota REST. Sem concessão de permissão, sem fallback
privilegiado, sem alterar a autoridade do domínio PRC.

### Testes (+3 em `test_eva_mcp.py`)

- `test_home_source_context_propagates_identity` — ctx carrega
  permissions/superadmin do humano.
- `test_home_prc_sections_authorized_via_mcp` — full-path MCP → Home
  → PRC: `requests`/`tasks` `available` com caso real.
- `test_home_prc_scope_isolation_preserved` — `own_scope` mantido:
  caso alheio nunca aparece (AC-04).

Suíte: 172/172 (home + PRC + MCP). Falha residual fora do escopo:
nenhuma nova.

### Deploy

| Ambiente | SHA | Digest | Saúde |
|---|---|---|---|
| HML | `b05bb83b62` | `sha256:24c99dc9de32` | healthy, 0 erros, fix no runtime |
| PRD | `b05bb83b62` | `sha256:0386937783af` (anterior `5c1212331307` retido) | healthy, discovery 200, 0 erros, fix no runtime |

Rollback: retag `5c1212331307` + `up-prod-sequential.sh --build
engineering-api`. Live smoke via ChatGPT: `TEST_NOT_RUN` — depende de
sessão legítima do PO; código do fix confirmado ativo no container PRD.
Verificador independente: INCONCLUSIVE (motor `devin` sem login).

### Residual search

Único builder MCP de `HomeSourceContext` era `tool_bridge._source_context`
(corrigido); rotas REST já projetavam permissões; demais fontes (LMP,
overview, NC) usam `access_token` para delegação HTTP — não afetadas.
