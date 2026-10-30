# 11 — Migration Execution Plan

Plano incremental. Cada etapa é independente e revisável; nenhuma
remove as 12 tools atuais sem evidência de migração de consumidores.
**Regra de progressão**: nenhuma etapa avança com regressões
materiais abertas; cada etapa declara baseline, testes de contrato/
negativa/equivalência, verificação de segurança, smoke/E2E quando
material, rollback seguro, evidência de outcome e critério
STOP THE LINE.

## Baseline (pré-condição de E0)

- 12 MCP tools + 12 GPT Actions verdes (suites MCP/Actions/conformance).
- `origin/main` com VISTA-AVATAR-001 v3 deployado e fumado.
- Docs da fase 1 (01-08) como baseline factual.

## E0 — Decisões e supersession ADR

| Campo | Valor |
|---|---|
| GOAL | Aprovar D-1..D-10; publicar ADR de supersession |
| OWNER | tv-dashboard-api (architecture) |
| BASE | `adr-vista-specialist-capability-surfaces.md` item 8 |
| ALLOWED | novo ADR `adr-vista-semantic-verbs-surface.md` marcando item 8 como **superseded-by**; atualizar capability-matrix refs |
| FORBIDDEN | qualquer código; editar o ADR antigo em vez de superseder |
| DEPENDENCIES | aprovação D-1..D-10 |
| CONTRACT IMPACT | nenhum (docs) |
| SECURITY | reafirmar: registry fechado, zero proxy genérico, AuthZ backend |
| TESTS | n/a (doc gate: links no README + referência cruzada) |
| ACCEPTANCE | ADR novo DECIDED com rationale: registry fechado + typed ops = não-CRUD-genérico |
| ROLLBACK | ADR volta a vigorar (supersession revertida) |
| EVIDENCE | ADR commit + diff do capability matrix |
| STOP THE LINE | owner rejeita supersession → convergência permanece fora de escopo; reportar |

## E1 — Modelo de confirmação verificável (D-5) + delete_data_model (D-8)

| Campo | Valor |
|---|---|
| GOAL | consent artifact por transporte (elicit/challenge) + `target_echo` como target-check; política `delete_data_model` decidida pelo owner |
| OWNER | tv-dashboard-api + security (consent mechanism) |
| BASE | `commit_service.py`, `presentation_ops_content.json`, EVA `_DestructiveConfirmation`+`ctx.elicit`, CLARA `step_up_consent.py`/`clara_consent_challenge` (V014) |
| ALLOWED | campos `target_echo` + `consent_artifact` no commit; consent challenge backend-mediado (reuso padrão CLARA); `ctx.elicit` MCP-capable; `CONFIRMATION_UNAVAILABLE` fail-closed; `CONFIRMATION_MISMATCH`/`CONSENT_MISMATCH`; política condicional delete_data_model **se aprovada em D-8** |
| FORBIDDEN | aceitar `confirmation=true` como prova humana em op `confirm`; fallback silencioso para echo; remover enforcement já ativo |
| DEPENDENCIES | E0 |
| CONTRACT IMPACT | **BEHAVIORAL + SECURITY-POLICY** — consumidores que hoje comitam ops `confirm` com `confirmation=true` **serão rejeitados** até adotarem o artifact. NÃO é ADDITIVE: é endurecimento de política que bloqueia fluxo anteriormente permitido. Mitigação de coexistência: (a) campo novo no schema é ADDITIVE; (b) exigência de artifact é a mudança comportamental — rollout via flag `VISTA_CONSENT_ARTIFACT_REQUIRED` com janela de transição em que `confirmation=true` ainda é aceito **com warning logado** (grandfather ≤ 1 release) e o campo `confirmation_model` no `get_context` anuncia a política nova |
| SECURITY | prova humana vinculada a (ator, proposta, alvo, plan_hash) — mitiga G-03 **de fato**, não por convenção |
| TESTS | contrato (schema aceita artifact); negativa (echo como único artefato → `CONFIRMATION_REQUIRED`; artifact de outra proposta → `CONSENT_MISMATCH`; transporte sem mecanismo → `CONFIRMATION_UNAVAILABLE`; replay de artifact → negado); equivalência (ops `direct` inalterados); elicit capaz/incapaz; challenge expirado/reusado/errado |
| ACCEPTANCE | op `confirm` nunca comita sem (a) echo correto E (b) artifact verificável; transporte sem mecanismo recebe bloqueio explícito |
| ROLLBACK | flag `VISTA_CONSENT_ARTIFACT_REQUIRED=false` — **só aceita com registro de motivo + TTL (não permanente)**; rollback não pode rebaixar segurança silenciosamente: volta ao estado `confirmation=true` aceito APENAS durante a janela grandfather, nunca depois da transição fechada; se já transicionado, rollback = remover tools novas, **não** rebaixar a política |
| EVIDENCE | testes novos + diff de commit_service + catalog + config flag |
| STOP THE LINE | qualquer caminho que comite op `confirm` sem artifact → STOP; host-alvo sem mecanismo de consentimento → escalar antes de prosseguir (não degradar para echo) |

## E2 — Modelo semântico neutral + `get_context` (D-2, D-7)

| Campo | Valor |
|---|---|
| GOAL | `capability_surface` ganha `semantic_mapping`+`status`; `get_context`/`vista_get_context` |
| OWNER | tv-dashboard-api |
| BASE | `capability_surface.py`, CAIO `SemanticAction` (campos), SURI `get_my_context` |
| ALLOWED | campos novos nas entries; tool/opId `get_context` novo; `effectiveCapabilities` derivado de AuthZ real |
| FORBIDDEN | registry paralelo fora do surface; capabilities auto-declaradas |
| DEPENDENCIES | E0 |
| CONTRACT IMPACT | ADDITIVE (tool/opId novo; entradas surface com campos novos) |
| SECURITY | effective caps derivados de `PlaylistAccessService` — nunca do modelo |
| TESTS | context: usuário A vs B caps diferentes; catalog: status proven/planned reflete registry; parity gate atualizado (6 tools) |
| ACCEPTANCE | host descobre contexto+catálogo+status via 1 tool |
| ROLLBACK | tool removida; surface fields ignorados (aditivos) |
| EVIDENCE | MCP tools/list + Actions OpenAPI diffs; testes |
| STOP THE LINE | derivação de capabilities exigir mudança no Core → escalar |

## E3 — `read`, `analyze`, `knowledge` (projeção sobre handlers existentes)

| Campo | Valor |
|---|---|
| GOAL | 3 tools semânticas delegando aos 9 handlers read/analysis |
| OWNER | tv-dashboard-api |
| BASE | `dispatch_service.py` métodos read/analyze; CAIO `_READ_DISPATCH` |
| ALLOWED | tools novas; allowlist `(entity,action)→método`; filters estritos; `evidenceClass` opcional; `slide_preset.list`/`media_asset.list` **se D-6 aprovado** |
| FORBIDDEN | novos handlers de domínio; dispatch por nome; SQL/HTTP arbitrário |
| DEPENDENCIES | E2 (vocabulário no surface) |
| CONTRACT IMPACT | ADDITIVE |
| SECURITY | mesma AuthZ dos handlers — zero bypass |
| TESTS | cada (entity,action) → resposta idêntica à tool legada; unknown → `UNKNOWN_ENTITY`/`UNKNOWN_ACTION`; filters extras → `VALIDATION_ERROR`; projection honrada |
| ACCEPTANCE | paridade funcional read/analyze/knowledge vs 9 tools legadas |
| ROLLBACK | tools removidas (legadas intactas) |
| EVIDENCE | conformance + testes de equivalência |
| STOP THE LINE | handler sem cobertura por teste → cobrir antes de expor |

## E4 — `execute` (phase + operations[]) (D-3)

| Campo | Valor |
|---|---|
| GOAL | facade fina sobre preview_change/commit_change |
| OWNER | tv-dashboard-api |
| BASE | `dispatch_service.preview_change`/`commit_change`, SURI `execute`, CAIO `phase` |
| ALLOWED | tool/opId `execute`; schema `{entity:"presentation",action:"apply_mutation",operations[],phase,...}`; `commit_now` Actions-only |
| FORBIDDEN | orquestrador novo; lógica de plano duplicada; CAS alterado |
| DEPENDENCIES | E1 (consent artifact + echo), E2 |
| CONTRACT IMPACT | ADDITIVE |
| SECURITY | reusa proposal handle/CAS/read-back; `operations[]` ≤ 20; handle binds plan — `operations[]` não reenviado no commit (substituição de plano bloqueada); single-shot só sem op `confirm` |
| TESTS | single op; plano composto (create_playlist+slides); confirm c/ artifact+echo; CAS conflict; partial commit; retry idempotente; `PLAN_MISMATCH` (operations reenviado divergente); unknown outcome |
| ACCEPTANCE | mesmos resultados que prepare_change/commit_proposal para planos idênticos; commit executa o plano selado, não um reenviado |
| ROLLBACK | tool removida |
| EVIDENCE | testes de equivalência + E2E composto |
| STOP THE LINE | divergência execute vs prepare/commit → NÃO corrigir facade — corrigir no dispatch canônico ou não lançar |

## E5 — `delete` dedicada (D-4, D-5)

| Campo | Valor |
|---|---|
| GOAL | tool `delete` com entity∈{block,section,slide} + echo (alvo) + consent artifact (humano) |
| OWNER | tv-dashboard-api |
| BASE | os 3 typed ops `confirm`; EVA elicit; CLARA challenge; E1 |
| ALLOWED | tool nova delegando a execute/prepare internamente; echo+artifact obrigatórios |
| FORBIDDEN | executor próprio; delete sem artifact; echo como única prova; deletes fora dos 3 typed ops |
| DEPENDENCIES | E1, E4 |
| CONTRACT IMPACT | ADDITIVE |
| SECURITY | superfície mais protegida: consent artifact + echo + handle + single-use + CAS |
| TESTS | prepare mostra impacto; commit artifact válido+echo ok; echo mismatch; artifact de outra proposta; `CONFIRMATION_UNAVAILABLE` host cego; replay |
| ACCEPTANCE | delete semântico só com prova humana verificável |
| ROLLBACK | tool removida |
| EVIDENCE | testes + wire |
| STOP THE LINE | qualquer delete sem artifact → STOP |

## E6 — Capability Expansion (Programa B, D-6)

| Campo | Valor |
|---|---|
| GOAL | typed ops/leituras novas aprovadas em D-6 — **Programa B**, separado do refactoring semântico (Programa A) |
| OWNER | tv-dashboard-api (backend domain) |
| BASE | `UpdatePlaylistBody` 11 campos; endpoints REST existentes; D-6 classificação |
| ALLOWED | INCLUIR: `patch_playlist`, `activate_playlist`/`deactivate_playlist`, `duplicate_slide`, `reorder_sections`, reads `slide_preset.list`/`media_asset.list` · CONDICIONADO: `delete_playlist` **só após E1+E5 provarem consent artifact em produção** |
| FORBIDDEN | shares/invites/ACL (EXCLUIR DO ESCOPO); history restore; templates admin; import/export .mdd; public-url/qr (ADIAR — decisão própria); qualquer typed op → Action automática |
| DEPENDENCIES | E0 aprovação por bloco; `delete_playlist` adicionalmente E1+E5 |
| CONTRACT IMPACT | ADDITIVE (typed ops catalog + reads no surface) |
| SECURITY | ops confirm herdam consent artifact + echo; playlist-level AuthZ = mesmo `require_playlist_access(edit)` |
| TESTS | por op: positive + sibling + negative + confirm policy; paridade REST↔typed op |
| ACCEPTANCE | cada capability aprovada alcançável via execute/read |
| ROLLBACK | remover entries do catalog (não-deployed ops são metadata) |
| EVIDENCE | catalog diff + testes por op |
| STOP THE LINE | op exige mudança em PatchService → escalar como sub-projeto; `delete_playlist` sem E1+E5 → STOP |

## E7 — Depreciação controlada das 12 legadas

| Campo | Valor |
|---|---|
| GOAL | consumidores migrados antes de qualquer remoção |
| OWNER | tv-dashboard-api + consumidores externos |
| BASE | doc 08 §5 — GPT externo usa opIds importados |
| ALLOWED | `deprecated:true` nos 12 gpt_* (OpenAPI) e marcação nas 12 tools MCP; monitoramento de uso |
| FORBIDDEN | remover tools/opIds sem evidência de migração do Custom GPT e hosts MCP |
| DEPENDENCIES | E3-E5 lançadas e adotadas |
| CONTRACT IMPACT | DEPRECATED → BREAKING só na remoção futura |
| SECURITY | n/a |
| TESTS | OpenAPI reflete deprecated; legadas ainda funcionam |
| ACCEPTANCE | evidência documentada de consumidores migrados; janela mínima (propor ≥2 releases) |
| ROLLBACK | undeprecate |
| EVIDENCE | OpenAPI diff + relatório de uso |
| STOP THE LINE | qualquer consumidor ativo detectado → manter |

## E8 — Diretivas, instruções, observabilidade (D-9, D-10)

| Campo | Valor |
|---|---|
| GOAL | `agent_directives`+`specialist-instructions` no vocabulário novo; provenance por canal |
| OWNER | tv-dashboard-api |
| BASE | `vista_agent_intelligence.json`, `specialist-instructions.md` |
| ALLOWED | reescrever write_flow/read_flow para verbos; `channel` na provenance history; budgets re-gated |
| FORBIDDEN | re-declarar operações nas instructions (apontar para catálogo); base64 avatar (já resolvido) |
| DEPENDENCIES | E2-E5 |
| CONTRACT IMPACT | comportamento de modelo (docs) + coluna/valor em history (ADDITIVE) |
| SECURITY | instructions não carregam autoridade |
| TESTS | budget tests; instructions leak-gate; history registra canal |
| ACCEPTANCE | modelo descobre verbs pelo catalog; forense por canal disponível |
| ROLLBACK | versão anterior das instructions |
| EVIDENCE | diffs + tests |
| STOP THE LINE | instructions re-declarando ops (leak-gate falha) → corrigir diretiva, não o gate |

## E9 — E2E + avaliação de comportamento (**certificação final**)

| Campo | Valor |
|---|---|
| GOAL | prova E2E dos 6 verbos + regressão das 12 legadas — **etapa de certificação: nenhuma etapa anterior avança com regressões materiais abertas** |
| OWNER | tv-dashboard-api |
| BASE | E2E harness real (task 026), MCP wire tests |
| ALLOWED | specs novos para verbos; suite de equivalência legado↔semântico; negative battery (unknown entity/action, echo, handle, CAS, auth) |
| FORBIDDEN | alterar fixtures para passar; smoke manual como evidência |
| DEPENDENCIES | E3-E5 |
| CONTRACT IMPACT | n/a |
| SECURITY | negative battery cobre os casos do doc 05 §4 |
| TESTS | E2E + unit + conformance + wire |
| ACCEPTANCE | verde completo + equivalência comprovada |
| ROLLBACK | — |
| EVIDENCE | CI run + spec list |
| STOP THE LINE | qualquer divergência semântica vs legado → bloquear lançamento |

## Matriz de rastreabilidade

| CURRENT TOOL | DOMAIN CAPABILITY | TARGET TOOL | HANDLER | AUTHZ | TEST | MIGRATION STEP |
|---|---|---|---|---|---|---|
| get_catalog | catalog.capability | get_context(action=catalog) | `build_capability_surface` | auth (401 sem) | unified_boundary, catalog_budget | E2 |
| (novo) | principal capabilities | get_context(action=context) | novo, derivado de `PlaylistAccessService` | RBAC Core+resource | contexto A/B | E2 |
| list_playlists | playlist.list | read(playlist,list) | `dispatch.list_playlists` | playlist read | vista_mcp_read_surface | E3 |
| get_playlist_context | playlist.context | read(playlist,context) | `dispatch.get_playlist_context` | playlist read | vista_mcp_read_surface | E3 |
| get_playlist_history | playlist.history | read(playlist_history,history) | `dispatch.get_playlist_history` | playlist read + digest | vista_playlist_history | E3 |
| search_data_routes | datablock.route | read(data_route,search) | `dispatch.search_data_routes` | auth + allowlist rotas | gpt_routes tests | E3 |
| inspect_data_model | datamodel.inspect | read(data_model,inspect) | `dispatch.inspect_data_model` | playlist read | gpt_datamodel tests | E3 |
| get_product_guide | guide.product | knowledge(get) | `dispatch.get_product_guide` | auth | tv_product_guide | E3 |
| preview_data_block | datablock.preview | analyze(data_block_preview) | `dispatch.preview_data_block` | playlist read + route auth | gpt_preview tests | E3 |
| preview_data_model | datamodel.preview | analyze(data_model_preview) | `dispatch.preview_data_model` | playlist read | gpt_datamodel tests | E3 |
| suggest_change | change.suggest | analyze(intent_materialization) | `dispatch.suggest_change` | playlist edit | gpt_suggest tests | E3 |
| prepare_change | change.prepare | execute(phase=prepare) | `dispatch.preview_change` | playlist edit | gpt_actions_facade | E4 |
| commit_proposal | change.commit | execute(phase=commit) | `dispatch.commit_change` | playlist edit+CAS+handle | commit tests | E4 |
| (via ops) | block/section/slide delete | delete(entity,delete) | `dispatch.commit_change` (ops confirm) | playlist edit + echo + consent artifact + CAS | facade confirm tests | E1+E5 |
| (gap) | playlist.update | execute(patch_playlist) | typed op nova | playlist edit | op-level tests | E6 |
| (gap) | presets listing | read(slide_preset,list) | REST `GET /slide-presets` | auth | preset tests | E6 |
