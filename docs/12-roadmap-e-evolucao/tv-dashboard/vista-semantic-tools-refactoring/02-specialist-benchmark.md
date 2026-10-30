# 02 — Specialist Benchmark (evidência de código real)

HEAD de inspeção: `28943d4d9b` · A comparação usa código no HEAD — não
documentação aspiracional. Nota: após a inspeção, commit local não-pushed
`cbe02f655e` ("SURI — claim atômico V005") endureceu ainda mais o
`execute` de SURI — reforça a direção do benchmark.

## 1. Resumo das famílias de superfície

| Especialista | App | Tools | Padrão | Registry |
|---|---|---|---|---|
| **VISTA** | tv-dashboard-api | **12** | per-domain tools (1 tool/op) | parity_map + typed ops (32) |
| **SURI** | supplies-api | **5** | semantic verbs | closed vocab inline (`constants.py` + bridge) |
| **CAIO** | commercial-api | **6** | semantic verbs | `SemanticAction` registry — 123 entradas |
| **CLARA** | controllership-finance-api | **6** | semantic verbs | (entity,action) specs inline — ~39 read + writes/delete |
| **EVA** | engineering-api | **23 + 6** | coexistência: domain tools + semantic verbs | `SemanticAction` registry — ~35 entradas |
| **TÉO** | transformometro-api | **23** | per-domain reads + `prepare_*` family + `commit_proposal` | (ancestral do modelo VISTA) |
| **DAVI** | api-delpi | **2** | meta discover→execute (read-only) | bounded candidate tokens |
| DÉLIA | delia-api | — | provider/consumer, sem MCP server | — |

## 2. Padrão semântico — anatomia (SURI como referência mínima)

`supplies-api/app/interfaces/mcp/server.py` — freeze rev.3:

| Tool | Signature | Semântica |
|---|---|---|
| `get_context` | `action: context\|catalog` | identidade+capabilities efetivas **ou** catálogo semântico |
| `read` | `entity: purchase_orders`, `action: search\|get`, `filters`, `identity` | vocabulário fechado; unknown keys rejeitados |
| `analyze` | `analysis: purchase_orders_summary`, `filters`, `sample_size` | análises determinísticas homologadas; fatos rotulados FACT/CALCULATION/RECOMMENDATION |
| `knowledge` | `action: search\|get\|sources`, `query/topic/knowledge_id/limit` | corpus governado com citações verificáveis (`knowledge.py`, `suri_knowledge.json`, classes PROVEN/OWNER_REPORTED/TO_INVENTORY) |
| `execute` | `entity: suppliers`, `action: create\|update`, `operations[]≤10` | writes diretos via BFF canônica; per-op `idempotency_key`; resultados `confirmed/acknowledged/sent/rejected/indeterminate/replayed` |

SURI **não tem `delete`** e **não tem proposal store** — writes são
diretos com idempotência por operação (`tool_bridge.py:733+`,
`supplier_execute.py`); commit `cbe02f655e` adicionou claim atômico
durável ao execute.

## 3. CAIO — registry-driven (o mais completo)

`commercial_app/application/caio/semantic_registry.py`:
`SemanticAction(entity, action, tool, description, risk, status,
destructive, ref_arg, requires, fields, phases, notes)` —
**123 entradas**: read=49, analyze=21, execute=40, delete=10,
knowledge=2, get_context=1. `risk`: read/analysis/moderate/destructive;
`status`: proven | planned | not_implemented (honesto, nunca executável).

`semantic_bridge.py` — dispatch `_resolve(entity, action, tool)`:
allowlist only → `_READ_DISPATCH` (49 pares) → handlers oficiais
(mesmos use cases REST); `_filters` rejeita campos não declarados;
`projection` seletiva em read.

- `get_context`: catalog_version, semantic_tools+annotations,
  entities_summary, actions (filtrável por entity/topic),
  commercial_capabilities do usuário, confirmation_model textual,
  agent_directives, planned_actions.
- `execute`: campos validados contra `entry.fields`; dispatch →
  `tool_bridge_parity.execute_*` (40 handlers); executa **direto**
  quando autorizado — "sem confirmações repetitivas"; envelope
  `{executed, write_policy}`.
- `delete`: **apenas sealed prepare→commit** —
  `proposal_store.seal_proposal` (actor-bound, TTL, single-use, HMAC)
  + `claim_valid_proposal` (claim atômico sob lock antes do executor);
  `phase=prepare` devolve impact honesto; `phase=commit` exige
  `proposal_ref` exato — "`confirmed=true` model-side nunca é prova".

## 4. CLARA — governance mais profunda

`controllership_finance_app/`:
- 6 tools; registry inline no `semantic_bridge.py` (~39 specs
  `(entity, action) → handler + ref_param + required + allowed`).
- `application/clara/governed_writes.py`: PREPARE sela operação
  server-side; ACT revalida ator/expiração/estado e delega à BFF —
  BFF reaplica `access/eligibility/assignment/resource_scope/
  business_rule` fail-closed.
- **`ClaraProposalRepository` — proposals persistidas em Postgres**
  (`infrastructure/persistence/clara_proposal_repository.py`) —
  supera o in-process residual da VISTA.
- **Step-up consent**: `application/clara/step_up_consent.py` —
  `CONSENT_TYPE_PORTAL_STEP_UP`, `clara_consent_url`, desafio de
  consentimento persistido (`ClaraConsentChallengeRepository`).
- Read-back: divergência ⇒ `OUTCOME_VERIFICATION_FAILED` — nunca
  sucesso afirmado.
- Trilha de auditoria `mcp/clara`.

## 5. EVA — coexistência + confirmação verificável

`engineering-api`:
- **Duas superfícies coexistem**: 23 tools per-domain legadas +
  6 tools semânticas (`server.py`, `semantic_bridge.py`,
  `application/eva/semantic_registry.py` ~35 entradas).
- **Feature flags de tier**: `ENG_EVA_ACT_ENABLED` (master write),
  `ENG_EVA_ACT_IMPORT_ENABLED` (bulk destructive), `ENG_EVA_ACT_DELETE_ENABLED`.
- **MCP elicitation** (`semantic_bridge.py:115-198`): para destrutivas,
  `ctx.elicit` com schema `_DestructiveConfirmation{confirm,
  target_echo}` — o humano **redigita o identificador** dentro do
  request; consumidor sem elicitation ⇒ `confirmation_unavailable`
  (403, honesto, bloqueado — nunca fallback silencioso). Isto é uma
  **prova de confirmação em nível de protocolo**, superior ao
  `confirmation=true` declarado pelo modelo usado pela VISTA.
- `application/eva/proposal_store.py`: `seal_proposal` /
  `load_valid_proposal` + `fingerprint`.

## 6. TÉO — ancestral do modelo VISTA

`transformometro-api/tm_app/interface/mcp/server.py` — **23 tools**:
reads per-domain (`get_my_context`, `get_workspace_context`,
`get_catalog`, `get_methodology_guide`, `get_product_guide`,
`solution_read`, `helpdesk_read`, `get_process_context`, `analyze`,
`record_read`, `evidence_read`, `get_process_timeline`,
`meeting_minute_read`, `collaboration_read`, `diagnostic_read`) +
família `prepare_*` por domínio (`prepare_record_change`,
`prepare_governed_operation`, `prepare_evidence_change`,
`prepare_meeting_minute_change`, `prepare_collaboration_change`,
`prepare_diagnostic_change`, `prepare_helpdesk_change`) + 1
`commit_proposal` universal. **Este é o padrão que o ADR VISTA
imitou** (prepare/commit unificado sobre typed ops) — e também o
padrão que o ADR item 8 recusou generalizar para entity CRUD.
Upstream adicionou plano "TEO Semantic MCP V3" (commits
`910e7e24b4`/`0add63b067`/`5f6e36645a`) — convergência semântica de
TÉO também está em planejamento; vale alinhar direção.

## 7. DAVI — meta discover→execute

`api-delpi/app/interface/mcp/server.py` — apenas 2 tools:
`discover_delpi_information(query, top_k)` → `candidate_token`
opacos; `execute_delpi_information(candidate_token, arguments)` →
executa o candidato. Read-only, AuthZ backend-first, sem URL/method/
operationId/SQL livres. Modelo diferente: descoberta NL + execução
por token — útil como referência de *resource discovery*, não de
write governance.

## 8. Comparação estrutural — VISTA vs padrão semântico

| Dimensão | VISTA (12) | Semântico (SURI/CAIO/CLARA/EVA) |
|---|---|---|
| Cardinalidade | 1 tool = 1 operação | 1 tool = 1 verbo; `(entity,action)` interno |
| Crescimento | nova capability → nova tool + nova Action + parity entry | nova capability → entrada no registry; tools estáveis |
| Catálogo interno | `capability_surface` (entidades/workflows/analyses) + typed ops | `SemanticAction` registry (risk/status/requires/fields) |
| get_context | `get_catalog` (projection transport-aware) | dedicado, com capabilities do usuário + honest status |
| read | `list_playlists`, `get_playlist_context`, `get_playlist_history`, `search_data_routes`, `inspect_data_model`, `get_product_guide` | `read(entity, action, ref, filters, pagination, projection)` |
| analyze | `preview_data_block`, `preview_data_model`, `suggest_change` | `analyze(analysis_type, subject_refs, question, parameters)` |
| knowledge | `get_product_guide` (topic/section) | `knowledge(action\|topic)` com corpus citável |
| execute | `prepare_change`+`commit_proposal` (ops[] typed, compound PlanCompiler) | `execute(entity, action, payload/changes, idempotency_key)` direto |
| delete | dentro do envelope prepare/commit via 3 typed ops `confirm` | `delete` tool dedicada, sealed proposals / elicitation |
| Confirmação | `confirmation=true` declarado pelo modelo | sealed proposal (CAIO/CLARA) ou elicitation verificável (EVA) |
| Proposal store | in-process, ACCEPT_WITH_RESIDUAL | CAIO in-process+lock (+ claim atômico V005 em SURI); **CLARA Postgres**; EVA aplicação-level |
| Feature flags de tier | não existe | EVA `ENG_EVA_ACT_*` |

## 9. O que é efetivamente reutilizável

- **`delpi_mcp` shared package** (`shared/delpi_mcp/`): auth, errors,
  identity, protocol, resource_contract, tool_metadata,
  tool_validation, transport, conformance — já é o substrato comum
  de todos os MCPs incluindo VISTA.
- **Padrão registry**: `SemanticAction` dataclass (CAIO/EVA) —
  `capability = f"{entity}.{action}"`, status honesto, `requires`
  documental, `fields` para validação estrita — diretamente
  transponível; VISTA já tem `capability_surface` + typed ops que
  carregam metadados equivalentes (confirmationPolicy, produces/
  consumes) — convergência = projeção, não engine nova.
- **Sealed proposal pattern**: CAIO `proposal_store.claim_valid_proposal`
  (atomic claim) — análogo conceitual ao `proposal_store.py` VISTA;
  SURI V005 adicionou claim atômico durável no execute.
- **Elicitation**: EVA `_require_human_confirmation` — eleva a
  confirmação de boolean declarado para prova de protocolo;
  **candidato direto para os 3 ops `confirm` da VISTA**.
- **Honest status**: `planned`/`not_implemented` respondendo 501 —
  VISTA hoje não expõe estado de capability não-implementada.
