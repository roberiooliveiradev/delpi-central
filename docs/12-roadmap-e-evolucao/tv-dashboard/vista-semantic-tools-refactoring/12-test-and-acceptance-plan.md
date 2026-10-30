# 12 — Test and Acceptance Plan

Estratégia de prova por etapa. Nenhuma implementação começou — este é
o contrato de validação a ser usado quando cada E* executar.

## 1. Camadas

| Camada | Propósito | Onde |
|---|---|---|
| unit | registry, projeções, schemas, echo, consent artifacts, mapeamentos | `tv-dashboard-api/tests/test_vista_semantic_*.py` (novos) |
| contrato | MCP tools/list, wire, OpenAPI gerado | `test_mcp_platform_conformance`, `test_mcp_streamable_http_wire`, `test_gpt_actions_*` |
| equivalência | semântico produz resultado idêntico ao legado | novos specs comparando outputs |
| negativa | fail-closed em todos os casos do doc 05 §4 | battery por tool |
| E2E | fluxo completo host→tool→backend→read-back | harness Playwright (task 026) |
| budget | Actions ≤100 KiB; instructions gates | `test_gpt_actions_catalog_budget`, `test_vista_builder_instructions_budget` |

## 2. Bateria positiva (por tool)

- `get_context`: context devolve `principal`+`effectiveCapabilities`
  +`catalogVersion`; catalog devolve surface completa com `status`
  por capability.
- `read`: cada `(entity,action)` mapeado → resposta byte-equivalente
  à tool legada correspondente; `projection` honrada; `filters`
  declarados passam.
- `analyze`: preview_data_block/model + intent_materialization
  funcionam; `evidenceClass` presente quando aplicável.
- `knowledge`: search/get retornam entradas com `source`/`locator`/
  `evidence_class`.
- `execute`: single op direct → VERIFIED; plano composto
  (create_playlist→add_slide→upsert_section→patch_native_config)
  → VERIFIED; op `confirm` sem artifact → CONFIRMATION_REQUIRED;
  artifact válido + echo correto → VERIFIED; `operations[]`
  reenviado divergente no commit → `PLAN_MISMATCH`; CAS conflict →
  REVISION_CONFLICT; PARTIAL_COMMIT reporta estado real; retry com
  mesma key → resultado replayed/consistente.
- `delete`: prepare mostra impacto; commit artifact válido +
  echo correto → VERIFIED.

## 3. Bateria negativa (cada uma obrigatória)

| Caso | Esperado |
|---|---|
| entity desconhecida | `UNKNOWN_ENTITY` |
| action fora da allowlist | `UNKNOWN_ACTION` |
| filters com campo não declarado | `VALIDATION_ERROR` |
| capability `not_implemented` | `NOT_IMPLEMENTED` 501 |
| sem auth | 401 |
| sem permissão no recurso | 403 |
| proposal inválido/expirado/outro ator | `PROPOSAL_NOT_FOUND` |
| `operations[]` reenviado divergente no commit | `PLAN_MISMATCH` |
| op `confirm` sem `consent_artifact` | `CONFIRMATION_REQUIRED` |
| `consent_artifact` de outra proposta/ator/alvo | `CONSENT_MISMATCH` |
| artifact replay (já consumido) | `CONSENT_MISMATCH`/`PROPOSAL_NOT_FOUND` |
| `confirmation=true` como única "prova" | `CONFIRMATION_REQUIRED` (nunca suficiente) |
| `target_echo` divergente do alvo | `CONFIRMATION_MISMATCH` |
| transporte sem mecanismo de consentimento | `CONFIRMATION_UNAVAILABLE` (bloqueio, sem fallback) |
| CAS divergente | `REVISION_CONFLICT` 409 + `currentRevision` |
| ops vazias | `NO_OPS`/`VALIDATION_ERROR` |
| principal_type=service em write | 403 |
| replay de handle usado | `PROPOSAL_NOT_FOUND` |
| host MCP sem elicit | `CONFIRMATION_UNAVAILABLE` (não fallback silencioso) |
| delete_data_model c/ consumidores sem artifact | `CONFIRMATION_REQUIRED` (se D-8 aprovado) |

## 4. Sibling cases

- `execute` com `operations[]` misturando direct+confirm no mesmo
  plano → confirm op exige echo + consent artifact; direct executam.
- Multi-playlist no mesmo plano → chain_revision por playlist.
- `read` em playlist de outro escopo/filial → 403 igual ao legado.
- `delete` para cada entity (block/section/slide) — não só um.
- `knowledge` em tópico inexistente → resultado vazio honesto, não 500.

## 5. Equivalência legado↔semântico (a prova-chave)

Para cada tool nova, teste que executa a mesma intenção via legado
e via semântico e compara payload de resultado:

| Legado | Semântico |
|---|---|
| `get_playlist_context(id)` | `read(playlist,context,ref=id)` |
| `preview_data_block(...)` | `analyze(data_block_preview,...)` |
| `prepare_change(ops)` | `execute(phase=prepare,operations=ops)` |
| `commit_proposal(h,k)` | `execute(phase=commit,proposal_handle=h,idempotency_key=k)` |
| op `delete_slide` via prepare/commit | `delete(slide,delete,ref,phase)` |

Divergência de resultado = **STOP THE LINE** (a facade nunca deve
produzir semântica própria).

## 6. E2E previstos

- Fluxo A: get_context → read(playlist,list) →
  analyze(intent_materialization) → execute(prepare) →
  execute(commit,artifact+echo) → read-back VERIFIED.
- Fluxo B: delete prepare → consent challenge aprovado por humano
  no Portal (ou elicit em host capaz) → commit com artifact+echo →
  história registra mutação com canal `mcp`/`gpt_actions` (D-10).
- Fluxo C: plano composto Caso A (playlist+slides+config) end-to-end.
- Regressão: as 12 tools legadas continuam passando nas suites
  existentes durante toda a coexistência.

## 7. Aceite por etapa (resumo)

| Etapa | Aceite |
|---|---|
| E1 | op `confirm` nunca comita sem artifact verificável + echo; transporte cego → bloqueio explícito; rollback não rebaixa política após transição |
| E2 | context+catalog+status via 1 tool; caps derivadas de AuthZ |
| E3 | 9 handlers alcançáveis por verbos com equivalência provada |
| E4 | execute produz resultados idênticos a prepare/commit |
| E5 | delete dedicada com prova verificável |
| E6 | capabilities aprovadas via execute/read; ops novas testadas |
| E7 | evidência documentada de migração de consumidores externos |
| E8 | instructions no vocabulário novo; provenance por canal |
| E9 | E2E + equivalência verdes; zero regressão legada |

## Program B expanded acceptance matrix — 2026-10-30

The product target now includes previously deferred/excluded D-6 blocks. Use [15 — master plan](15-d6-product-direction-and-master-plan.md) as execution ordering and keep the existing test matrix for Program A. For B1: playlist fields/activation, slide duplication, section ordering, media/preset reads — positive+sibling+wrong resource/branch+revision and parity. For B2 templates: publish/archive permissions, lifecycle, consumer parity and version behavior. For B3 delete/restore: signed-off trusted consent path, CAS, replay, wrong actor, invalid/expired handle, blast radius and history read-back. For B4 MDD: schema versions, invalid archives/path traversal, asset handling, export→preview→apply→roundtrip and permissions. For B5 sharing/invites/permissions: recipient/role identity, Core effective RBAC, resource scope, self-elevation, grant/revoke, invite expiry, audit, negative cross-branch and no service-account privilege substitution. Execute each suite at its bounded step, not only E9. Current state: tests for expanded items are PLANNED, not run.
