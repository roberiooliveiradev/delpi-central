# VISTA — Knowledge Intelligence Convergence V1 (roadmap canônico)

> **Status:** PLANNED (arquitetura aprovada; nenhuma fase executada)
> **Data:** 2026-10-08 · **HEAD de referência:** `8686552a1e`
> **Escopo:** documento de controle de todas as futuras frentes de inteligência VISTA.
> **Regra de ouro:** organizar antes de expandir; verdade antes de orientação; orientação antes de heurística duplicada; owner antes de integração; reuse antes de nova capability; *smallest sufficient truth set* antes de tool spam; eval antes de alegar melhoria; gate do roadmap antes de implementação.

---

## 1. Executive Summary

A VISTA já é uma especialista forte: 10 tools MCP / 8 GPT Actions sobre um dispatch único, 40 capabilities, 32 ops tipadas, 35 grupos de `agent_directives` vivos via `vista_agent_intelligence.json`, verificação visual por palco vivo do editor (`canonical_stage`), PREPARE→COMMIT governado e paridade Actions↔MCP testada. O que falta não é capability — é **orquestração explícita de conhecimento**: a VISTA ainda não distingue declarativamente verdade de domínio, orientação de produto, metodologia de design, contrato de execução e contexto de editor.

O TÉO (`transformometro-api`) já resolveu esse problema de forma provada em código: `knowledge_orchestration` declarativo (15 fontes, precedência, roteamento por intent, gates, suficiência, gap handling), Product Guide Registry V1 (24 tópicos, `GUIDANCE_NOT_DOMAIN_TRUTH`, validação cruzada fail-closed), Methodology V2 (intents/readiness/sufficiency/next-questions), `solution_read` sobre o catálogo Core, workspace context com estados `active|absent|stale|ambiguous`, projeção de transporte fail-closed e classificação epistêmica fechada.

Este roadmap define a convergência **arquitetural** — reutilizar os *padrões* do TÉO dentro do owner VISTA, sem copiar domínio, sem dependência runtime VISTA→TÉO e sem inflar a surface de tools.

---

## 2. Current State

### 2.1 VISTA (HEAD `8686552a1e`) — PROVEN

| Item | Evidência |
|---|---|
| Tools MCP | 10 tools, registry congelado `interface/mcp/constants.py:28-41`, drift guard `server.py:331-334` |
| GPT Actions | 10 operations + 2 support routes, `interface/http/routes/gpt_actions_routes.py:141-389` |
| Dispatch único | Ambos os transportes delegam a `GptActionsDispatchService` (`tool_bridge.py`) |
| Ops catalog | 40 capabilities / 32 typed ops (`presentation_ops_content.json` — capabilities L3272+, ops L883-3271) |
| Agent directives | 35 grupos + metadata (`vista_agent_intelligence.json` ~39 top-level keys), projeção por transporte `vista_agent_intelligence_service.py:102-209` |
| Serviços de inteligência | DesignIntelligence, Recipe, LayoutDigest, FilterDigest, StoryDigest, JoinPlan, DisplayFormatHints, ReadySlideQuality, VisualVerification, SlidePreviewRender, SlideAutoLayout, SafeAutoFix — todos em `application/services/` |
| NL→ops | `PresentationSuggestOpsService` (marker scoring + fan-out + arbitration); `matchedCapabilityKeys`/`clarificationKey` em resposta |
| Editor grounding | `EditorFocusStore` (TTL 90s, stale≤180s) + `PresentationRealtimeHub` (`selection_update`, `visual_capture_request`); `editorFocus` em `get_playlist_context` |
| Visual evidence | `slidePreview.rendered` `canonical_stage` — capturado **só** pelo editor vivo do usuário (`editor_live`+`clientId`); sem renderer autônomo |
| Governed write | PREPARE→COMMIT, `proposal_handle` opaco, `commit_now` (Actions) / `confirmation` (MCP), read-back VERIFY |
| History domain | `PlaylistHistoryChangeService` + repository + rotas `/playlists/{id}/history` (até 500 versões) — **domínio existe; não exposto à VISTA** |
| Eval corpus | `vista_ready_slide_corpus.json` (C1–C31 + G_*) + gate `test_vista_ready_slide_corpus_gate.py` |
| Paridade | `surface_parity.parity_map` no JSON + `test_vista_unified_boundary.py` |

### 2.2 Gaps atuais conhecidos (revalidados em HEAD)

| Gap | Status em HEAD |
|---|---|
| Telemetry de outcome do suggest | **ABSENT** — `matchedCapabilityKeys`/`clarificationKey` são response fields; nenhum log estruturado (`dispatch_service.py` sem logger) |
| `x-delpi.presentationStrategy` extraído, sem consumidor | **PARTIAL** (dead extraction) |
| `entity`/solução por rota de dados | **ABSENT** — `tv_data_routes.json` não persiste `entity`/`solution`/`owner` |
| Generic media upload | **TARGET** (matrix L191) |
| DÉLIA TV adapter | **TARGET** (ADR 7c/7h — zero runtime coupling) |
| MCP provisioning externo (`mcp-tv-dashboard` + go-live) | **PENDING** (matrix L18/L192; runbook `openai-plugin-mcp.md`) |
| Proposal store single-replica | **ACCEPT_WITH_RESIDUAL** (ADR item 10) |
| `CHATGPT_APP_IMAGE_DELIVERY` | **FAIL_OBSERVED** — wire `ImageContent` PROVEN; host não entrega bloco de imagem ao modelo |
| Display-format typed coverage | **PARTIAL** — `DisplayFormatHintsService` PROVEN; cobertura tipada por visual incompleta |
| `visual_verification` directive | **PARTIAL** — slot de projeção existe; bloco JSON removido intencionalmente (emite `{}`) |

---

## 3. Ownership / Authorities

| Conceito | Autoridade canônica | VISTA pode |
|---|---|---|
| Identidade | Keycloak | consumir JWT, nunca emitir |
| RBAC efetivo | Core API (`load_user_rbac(force_refresh=True)` em governed write) | — |
| Playlists/slides/blocos/DataModel/PresentationMutation | `tv-dashboard-api` (`TvPresentationWriteService`) | propor ops tipadas via PREPARE |
| Contratos de dados | `api-delpi` OpenAPI + `x-delpi` | descobrir via `tv_data_routes.json` derivado |
| Inteligência de especialista TV | VISTA (`vista_agent_intelligence.json` + services) | **owner desta evolução** |
| Solution ecosystem metadata | **Core** (`GET /solutions`) | consumir como projection (futuro) |
| Rendering/playback | `tv-dashboard-presentation` | — |
| Kiosk host | `public-hub` | — |
| UX de autoria | MFE `tv-dashboard` | — |
| TÉO | `transformometro-api` | **referência de padrão, nunca dependência** |

Inviolável: VISTA ≠ segunda autoridade de domínio; Product Guide ≠ verdade de domínio; metodologia ≠ estado persistido; visibilidade de conhecimento ≠ autorização; contexto de editor = hint de navegação ≠ autorização.

---

## 4. Problems Being Solved

1. **Sem fronteira declarativa entre tipos de conhecimento** — verdade de domínio, orientação de uso, metodologia e contrato de execução vivem misturados em `agent_directives` + instruções estáticas.
2. **Fan-out/marker scoring é frágil** — regressões provadas (create duplicado `novo bloco`; quoted-payload veto) mostram que a disambiguation de intent precisa de camada explícita eventual.
3. **Sem orientação de produto canônica** — perguntas "como funciona X no TV Dashboard?" são respondidas por memória do modelo ou diretivas operacionais, não por um registry de uso versionado.
4. **Help do Portal diverge** — copy semântica de ajuda não compartilha fonte com a inteligência da VISTA.
5. **Editor grounding sub-estruturado** — `editorFocus` existe mas não projeta estados `ACTIVE/STALE/ABSENT/AMBIGUOUS` nem resumo de objeto selecionado.
6. **Descoberta de dados sem ecossistema** — `search_data_routes` retorna rotas TV; nada conecta "preciso de EBITDA" a qual produto/solução DELPI detém a rota (0 resultados de busca ≠ ausência de solução).
7. **Inteligência não mensurada** — eval corpus existe para "ready slide", mas não há benchmark baseline↔candidate nem telemetria de decisão.
8. **Histórico existe e é invisível** — `PlaylistHistoryChangeService` persiste diffs; a VISTA não pode responder "o que mudou neste painel?".

---

## 5. Non-Goals

- Criar segunda autoridade de domínio do TV Dashboard.
- Dependência runtime VISTA→TÉO (nem cliente, nem shared module de domínio).
- Novo mutation engine, novo renderer, novo planner genérico.
- Aumentar a surface de Actions/MCP por conveniência (**default: NEW TOOL = NO**).
- SQL/HTTP/search-anything genérico (proibido pelo ADR VISTA).
- Copiar entidades TÉO (`record_read`, `prepare_record_change`) — VISTA é workflow de apresentação, não CRUD multi-entidade.
- Product Guide como autoridade de domínio, AuthZ ou contrato de dados.
- Reabrir `PresentationMutation`, ownership de write ou contrato OpenAPI.
- Implementação de qualquer fase neste documento.

---

## 6. TÉO Reference Patterns

Padrões provados em `transformometro-api` a reutilizar **conceitualmente**:

| Mecanismo | Owner TÉO | O que prova | Reusável pela VISTA | NÃO aplicável |
|---|---|---|---|---|
| `knowledge_orchestration` | `teo_agent_intelligence.json:116-490` | orquestração declarativa de fontes com zero tools novas | padrão sources/precedence/routing/gates/sufficiency/gap | os 11 intents TÉO (domínio diverso) |
| Product Guide Registry | `application/product_guide/` + `content/product_guides/*.json` (24 tópicos) | GUIDANCE_NOT_DOMAIN_TRUTH com fail-closed cross-ref | registry versionado + help-view projection + validation contra capability catalog | os 24 tópicos em si |
| Methodology V2 | `application/methodology/guide_v2.py` | routing/readiness/sufficiency/next-question com fatos tri-state | modelo de context facts + epistemic constraints + soft composition | os 13 métodos de processo |
| `solution_read` | `application/solutions/` + gateway Core | knowledge≠authorization; fit vocabulary fechado | Bearer-forwarded projection do catálogo Core; fit classification | — |
| Workspace context | `workspace_context_service.py` | estados `active/absent/stale/ambiguous` + ambiguous→candidates+next_step | estados + semântica de resolução | o shape de processo (VISTA = playlist/slide/bloco) |
| Transport projection | `capability_registry.py` + `transport_projection.py` | binding table única → 2 projeções derivadas, fail-closed | já equivalente: `surface_parity.parity_map` + projeção Actions/MCP | — |
| Execution contract | `governed_writes/orchestrator.py` | PREPARE selado + ACT único + read-back | já equivalente (VISTA PREPARE→COMMIT+VERIFY) | — |
| Epistemic labels | `guide.py`, `guide_v2.py`, `branding.py`, `process_context_service.py` | vocabulário fechado OBSERVED/CALCULATED/INFERRED/PROPOSED/UNKNOWN | vocabulário + `epistemic_status` por superfície | — |
| Help convergence | `product_guide_routes.py?view=help` | mesma registry serve especialista e Portal Help (campos internos stripped) | padrão de projeção `view=help` | rotas específicas |
| Eval/telemetry | — | **ausente no TÉO também** | — | não copiar ausência; VISTA pode liderar aqui |

---

## 7. VISTA Gap Matrix (VISTA × TÉO maturity)

| Dimensão | VISTA | TÉO | ACTION |
|---|---|---|---|
| Verdade de domínio | PROVEN (`get_playlist_context`, digests, history) | PROVEN (`get_process_context`, `record_read`) | KEEP_AS_IS |
| Orientação de produto | MISSING (só agent_directives operacionais) | PROVEN (Product Guide V1, 24 tópicos) | EXTEND (padrão → PHASE 2) |
| Metodologia de design | PARTIAL (`design_intelligence`, recipes, `designAudit` — sem readiness/sufficiency) | PROVEN (Methodology V2) | EXTEND (PHASE 5) |
| Contexto de workspace/editor | PARTIAL (`editorFocus` + `selectedIds`; sem estados de resolução) | PROVEN (`workspace_context` 4 estados + candidates) | EXTEND (PHASE 4) |
| Orquestração de conhecimento | PARTIAL (diretivas dispersas; sem routing/gates declarativos) | PROVEN (sources+precedence+routing+gates+sufficiency+gap) | EXTEND (PHASE 1) |
| Precedência de fontes | PARTIAL (em Instructions: catálogo > Knowledge; não declarativa por fonte) | PROVEN (8 regras declarativas) | EXTEND (PHASE 1) |
| Suficiência/stop rules | PARTIAL (`write_quality`/`READY` gates; sem stop-when-sufficient geral) | PROVEN (`sufficiency` + stop reasons) | EXTEND (PHASE 1) |
| Gap classification | PARTIAL (`clarificationKey` tipado; sem UNKNOWN/TO_INVENTORY geral) | PROVEN (labels fechados) | EXTEND (PHASE 1) |
| Solution ecosystem | MISSING (nenhum metadado de solução/owner nas rotas) | PROVEN (`solution_read` Core-projection) | EXTEND (PHASE 6) |
| Semântica de dados | PARTIAL (`x-delpi` entity/shape/category/locale importado; `entity` não persistido; `presentationStrategy` dead) | PROVEN (contexto por domínio) | EXTEND (PHASE 6) |
| Inteligência de design | PROVEN (visual_selection, composed_visuals, recipes, layout quality, auto-fix) | PARTIAL (métodos ≠ rendering) | KEEP_AS_IS |
| Governança de execução | PROVEN (PREPARE→COMMIT+VERIFY, proposal opaco) | PROVEN (idem) | KEEP_AS_IS |
| Paridade de transporte | PROVEN (parity_map + unified boundary) | PROVEN (binding table + projection fail-closed) | KEEP_AS_IS |
| Convergência de documentação/Help | MISSING | PROVEN (help view projection) | EXTEND (PHASE 3) |
| Avaliação (eval corpus) | PARTIAL (corpus C1–C31 ready-slide; sem baseline↔candidate geral) | MISSING (sem corpus conversacional) | EXTEND (PHASE 7) — VISTA pode liderar |
| Telemetria de decisão | MISSING | MISSING | EXTEND (PHASE 7) |
| História/auditoria awareness | PARTIAL (domínio history PROVEN; não exposto à VISTA) | PROVEN (timeline + evidence + diagnostic) | EXTEND (PHASE 9) |

---

## 8. Target Architecture

```text
                 ┌─────────────────── VISTA (specialist authority) ───────────────────┐
                 │                                                                    │
 NL intent ──►   │  INTENT ROUTING (PHASE 1)                                          │
                 │    route → smallest sufficient truth set                           │
                 │         │                                                          │
                 │         ▼                                                          │
                 │  ┌────────────── Knowledge sources (existing owners) ───────────┐  │
                 │  │ presentation_truth   get_playlist_context + digests          │  │
                 │  │ editor_context       editorFocus → editorContext (PHASE 4)   │  │
                 │  │ execution_contract   get_catalog (capability_surface)        │  │
                 │  │ data_contract        search_data_routes / inspect_data_model │  │
                 │  │ data_runtime         preview_data_block / preview_data_model │  │
                 │  │ visual_evidence      slidePreview.rendered (editor_live)     │  │
                 │  │ product_usage        Product Guide (PHASE 2)                 │  │
                 │  │ design_methodology   Methodology (PHASE 5, decision lens)    │  │
                 │  │ solution_ecosystem   Core solutions projection (PHASE 6)     │  │
                 │  │ history              playlist history READ (PHASE 9)         │  │
                 │  │ mutation             prepare_change → commit_proposal        │  │
                 │  └──────────────────────────────────────────────────────────────┘  │
                 │         │                                                          │
                 │    gates + sufficiency + gap handling + epistemic labels           │
                 │         │                                                          │
                 │         ▼                                                          │
                 │  typed ops only → TvPresentationWriteService (governed write)      │
                 └────────────────────────────────────────────────────────────────────┘

  Core/API-delpi permanecem owners: RBAC, soluções, contratos de dados.
  TÉO permanece especialista Transformômetro — padrões compartilhados
  conceitualmente, código/domínio nunca compartilhados.
```

---

## 9. Source-of-Truth Map

| Fonte | Owner | Verdade de | Runtime surface atual |
|---|---|---|---|
| `presentation_truth` | tv-dashboard-api | estado persistido playlist/slide/bloco | `get_playlist_context`, `list_playlists` |
| `editor_context` | `EditorFocusStore` + `PresentationRealtimeHub` | foco/seleção efêmera do editor | `editorFocus` em reads |
| `execution_contract` | `capability_surface.py` + ops catalog | o que é possível executar agora | `get_catalog` |
| `data_contract` | api-delpi OpenAPI → `tv_data_routes.json` | rotas de dados permitidas/params | `search_data_routes`, `inspect_data_model` |
| `data_runtime` | `TvDataPreviewService` | resultado real de rota/modelo | `preview_data_block`, `preview_data_model` |
| `visual_evidence` | editor vivo (canonical_stage) | pixels reais do palco | `slidePreview.rendered` |
| `product_usage` (futuro) | tv-dashboard-api content | como/quando/por que usar features | Product Guide (PHASE 2) |
| `design_methodology` | `design_intelligence.json` + recipes | lente de decisão de design | directives + PHASE 5 |
| `solution_ecosystem` (futuro) | Core | qual solução detém qual capacidade | projection (PHASE 6) |
| `history` | `PlaylistHistoryRepository` | o que mudou e quando | rotas `/history` (PHASE 9: read para VISTA) |
| `mutation` | `PresentationMutation` | o que foi escrito | `prepare_change`/`commit_proposal` |

---

## 10. Knowledge Orchestration V1 (PHASE 1)

**Owner:** `vista_agent_intelligence.json` (`agent_directives`) — mesma autoridade mutável atual; **zero tools novas** por padrão (padrão TÉO: orquestração é diretiva declarativa, não código novo).

### 10.1 Princípio

`ROUTE_TO_SMALLEST_SUFFICIENT_TRUTH_SET` — identificar o intent e consultar apenas as fontes autoritativas mínimas. Nunca todas as reads por default.

### 10.2 Precedência (validada contra HEAD — sem conflito)

```text
CURRENT PRESENTATION STATE > PRODUCT GUIDANCE
LIVE CAPABILITY / EXECUTION CONTRACT > STATIC BUILDER INSTRUCTIONS
api-delpi / OpenAPI OWNER CONTRACT > DERIVED TV DATA CATALOG
AUTHORITATIVE READ-BACK > TECHNICAL 2XX
CANONICAL STAGE PIXELS > SCHEMATIC CLAIMS ABOUT PIXELS
EDITOR CONTEXT = NAVIGATION/GROUNDING HINT != AUTHORIZATION
PRODUCT GUIDE = GUIDANCE != DOMAIN TRUTH
DESIGN METHODOLOGY = DECISION LENS != SAVED STATE
SEARCH MISS != PROOF OF ABSENCE
```

Todas já coerentes com invariants existentes em Instructions (`INFERRED != FACT`, `2xx != verified`, `search miss != absence`) e com o ADR de captura `editor_live`. Nenhum conflito em HEAD.

### 10.3 Intent routing (alvo)

| Intent | Route (smallest sufficient set) | Evita por default |
|---|---|---|
| SIMPLE_PRESENTATION_READ | `get_playlist_context` → answer | product guide, methodology, ecosystem |
| PRODUCT_USAGE | Product Guide → `get_catalog` se contrato vivo relevante → presentation state só se sobre objeto real | methodology, ecosystem |
| DESIGN_REVIEW | presentation_truth → data shape/runtime se relevante → design methodology → visual evidence se claim de pixel → typed recommendation/mutation | ecosystem |
| DATA_DISCOVERY | presentation context → data contract/search → runtime preview → semantic/visual recommendation | ecosystem (só se cruzar fronteira de produto) |
| DIGITAL_SOLUTION_NEED | understand → solution ecosystem → api-delpi ownership → approved TV route → preview → visual | `NEW_CAPABILITY_CANDIDATE` antes de inspecionar ecossistema |
| MUTATION | READ current → LIVE CATALOG → typed intent → PREPARE → policy → COMMIT → read-back → VERIFY | methodology, ecosystem, product guide |
| HISTORY_QUESTION (futuro) | history read → diff summary | mutation path |

### 10.4 Campos obrigatórios do bloco

`sources` (por família, com `authority` declarado), `precedence`, `routing` (intent→route+avoid), `gates` (ex.: `PRESENTATION_TRUTH_GATE`, `PRODUCT_USAGE_GATE`, `EXECUTION_CONTRACT_GATE`, `METHODOLOGY_GATE` — "nunca para leituras simples", `SOLUTION_GATE`), `composition` (composição permissiva de fontes), `sufficiency` (stop-when-sufficient; sem tool spam), `gap_handling` (labels `UNKNOWN|TO_INVENTORY|PROPOSED|INFERRED`; nunca inventar), `epistemic` (INFORMED/INFERRED/PROPOSED/UNKNOWN — vocabulário já parcialmente em Instructions).

### 10.5 Anti-patterns

- Product Guide respondendo sobre estado atual ("quantos slides tem esta playlist?" → verdade é `get_playlist_context`).
- Methodology invocada em leitura simples.
- Solution discovery em authoring rotineiro.
- Metodologia/orientação tratada como autorização ou estado persistido.
- Routing por fan-out de markers (limitação atual — PHASE 8 avalia arbitragem estrutural).

---

## 11. Product Guide V1 (PHASE 2)

### 11.1 Owner

`tv-dashboard-api` content/intelligence layer — mesmo owner de `vista_agent_intelligence.json` e `presentation_ops_content.json`. O padrão TÉO (`product_guide_registry.py` + `product_guide_schema.py` + `content/product_guides/*.json` + `product_guide_service.py` + `product_guide_routes.py`) é o modelo de referência; VISTA implementa o seu próprio registry no próprio bounded context.

### 11.2 Princípio

`GUIDANCE_NOT_DOMAIN_TRUTH` — enforced no schema (o TÉO força `authority=GUIDANCE_NOT_DOMAIN_TRUTH` no contrato). Ensina *como/quando/por que/relações/expectativa de qualidade*; nunca carrega estado de domínio, AuthZ, contrato de mutação ou contrato de dados.

### 11.3 Source model (a finalizar no diagnostic de PHASE 2)

Campos candidatos (espelho TÉO, adaptado): `schema`, `id` (== filename), `title`, `summary`, `authority`, `purpose`, `use_when[]`, `do_not_use_when[]`, `how_to_use[]`, `field_guidance[]` (`field`+`guidance`+`contract_ref?`), `quality_rules[]`, `common_mistakes[]`, `related_topics[]`, `capability_refs[]`, `operation_refs[]`, `read_refs[]`, `write_refs[]`, `ui_refs[]`, `source_refs[]` (`PROVEN|INFERRED|PROPOSED`), `agent_guidance?`. Seções projetáveis (index compacto vs full).

### 11.4 Anti-drift

- `related_topics` devem resolver (fail-closed no load).
- `capability_refs` validados contra `capability_surface` viva.
- `operation_refs` validados contra `presentation_ops_content.json` ops.
- `data` refs validados contra `tv_data_routes.json`/owners canônicos.
- Referência desconhecida → falha de CI/teste, nunca fallback silencioso.
- Proibido duplicar schemas de capability no Guide.

### 11.5 Seed topics — classificação inicial (revalidar em PHASE 2)

| Tópico | Classe |
|---|---|
| tv_dashboard_overview, playlist, slide, block_types, data_sources, data_bindings, filters_and_layering | WAVE_1 |
| display_formats, data_route_discovery, visual_verification, design_quality | WAVE_1 |
| sections, editor, published_templates, presentation_recipes, media, history, sharing_and_kiosk, MDD import/export | LATER |
| (todos os demais) | NOT_NEEDED até evidência de demanda |

### 11.6 Action Surface Gate

`NEW TOOL REQUIRED? TO_INVENTORY`. Alternativas a provar antes de criar tool: (1) índice compacto dentro de `get_catalog`; (2) as 10 tools atuais já servem guidance com segurança. Tool dedicada `get_product_guide` só se consumidor real + budget + owner justificarem. Portal Help (`view=help`) pode ser consumidor via rota HTTP existente — não via tool de agente.

---

## 12. Help Convergence (PHASE 3)

`ONE PRODUCT SEMANTIC SOURCE → VISTA guidance → Portal Help → docs derivados`. Padrão TÉO: `GET …/product-guides?view=help` projeta campos seguros (strip de `capability_refs`/`contract_refs`/`agent_guidance`/internos) para o MFE consumir; mapeamento de seções do manual → tópicos; teste falha se seção mapeada reintroduzir copy semântica própria. Copy específica de UI (links, tooltips, empty states) permanece local; o frontend nunca bundla a autoridade semântica.

---

## 13. Editor Grounding V2 (PHASE 4)

Atual (PROVEN): `EditorFocusStore` (TTL 90s, grace stale≤180s, per-user, `clientId`), `PresentationRealtimeHub.selection_update`, `editorFocus` `{slideId, selectedIds, updatedAt, stale, selectedDataSourceId?}` injetado em `get_playlist_context`/`list_playlists`.

Alvo: projeção compacta canônica `editorContext`:

```yaml
editorContext:
  status: ACTIVE | STALE | ABSENT | AMBIGUOUS   # deriva de TTL/grace/multi-clientId
  playlistRevision: int
  focusedSlideId: string?
  selectedObjects:
    - id, type, contentSummary?, frame?, styleDigest?, dataBindingDigest?, formatBindings?, modelId?
  resolutionStatus: resolved | needs_disambiguation
```

Regras: não duplicar nativeConfig completo; respeitar payload budget (Actions ~100 KiB já próximo do teto — projeção compacta obrigatória); grounding ≠ autorização; `AMBIGUOUS` (múltiplos clientes vivos) → pergunta discriminante, nunca guess por recência. Fontes de verdade existem (`blockIndex`, `focusedBinding`, `focusedSlide.nativeConfig`) — a fase decide o menor recorte.

---

## 14. Design Methodology (PHASE 5)

Evoluir o que já existe — `design_intelligence`, `visual_selection`, `visual_impact`, `layout_perception`, recipes, `designAudit`, `preview_data_block.semanticDigest`/`visualRecommendation` — para um modelo de decisão explícito (padrão Methodology V2 do TÉO, adaptado a slides):

- **Intents candidatos:** `review`, `improve`, `choose_visual`, `compose_slide`, `fix_layout`, `diagnose_data`, `prepare_kiosk`.
- **Context facts candidatos (tri-state/epistemic):** `slide_purpose_known`, `data_shape_known`, `primary_metric_known`, `time_series_known`, `category_count_known`, `goal_known`, `filter_scope_known`, `layout_density_known`, `visual_evidence_available`.
- **Outputs:** `readiness` (`READY|PARTIAL|NOT_READY|UNKNOWN`), `missing_information`, `candidate_strategy`, `reason`, `next_question`, `sufficiency` (`SUFFICIENT|NOT_SUFFICIENT|UNKNOWN` + stop reasons).
- **Invariantes:** methodology ≠ truth; recommendation ≠ persisted state; nunca vaza autoridade de domínio.

---

## 15. Data + Solution Intelligence (PHASE 6)

Inventário atual: `x-delpi` do OpenAPI da api-delpi importa `entity`, `shape`, `category`, `locale`, `params`, `tv` audience, `presentationStrategy` — mas `entity` só serve overlays e `presentationStrategy` não tem consumidor. `tv_data_routes.json` não carrega solução/owner/grão/unidade.

Alvo (só campos com owner canônico provado — inventário em PHASE 6): `sourceSolutionId`, `sourceOwner`, `businessMeaning`, `grain`, `metricUnit`, `freshness`, `timeDimension`, `dimensionHints`, `relatedRoutes`. Proibido catálogo semântico paralelo se metadado de owner puder ser projetado.

Princípio adotado (padrão TÉO `solution_read`): `KNOWLEDGE_VISIBILITY != ACCESS_AUTHORIZATION`; fit classification fechada `REUSE_EXISTING|EXTEND_EXISTING|INTEGRATE_EXISTING|NEW_CAPABILITY_CANDIDATE|TO_INVENTORY`; nunca recomendar nova capability antes de inspecionar ecossistema existente; nunca invocar solution discovery em authoring rotineiro de TV. Owner da solução permanece **Core** — VISTA consome projeção Bearer-forwarded como o TÉO faz.

---

## 16. Eval + Telemetry V2 (PHASE 7)

### 16.1 Benchmark

Estender o corpus `vista_ready_slide_corpus.json` para cobertura de inteligência geral: intent routing, object grounding, CREATE vs ALTER discrimination, clarification correctness, typed-op validity, data-route retrieval, visual selection, filter layering, display-format selection, write safety, proposal validity, VERIFY outcome. Toda mudança de inteligência exige `BASELINE → CANDIDATE → SAME CORPUS → SAME CONFIG → DELTA`. Proibido aceite por "parece melhor".

### 16.2 Telemetria segura

Hoje `presentation_mutation_telemetry.py` só conta `preview`/`apply`. Alvo: campos agregados/não-secretos — `matchedCapabilityKeys`, `clarificationKey`, `status` do suggest, `prepare` rejection reason, família `OUTCOME_NOT_VERIFIED`, `resolution` state, `visual evidence` status. Proibido logar: JWT, secrets, payloads sensíveis completos, prompts privados por default.

---

## 17. Semantic Arbitration (PHASE 8 — avaliação futura)

Regressões provadas (fan-out create duplicado; veto por quoted payload) indicam limite estrutural de marker scoring. **Não desenhar engine nova agora.** Avaliar extensão declarativa dos metadados existentes: `intentMode` (`create|alter|delete|layout|bind|data`), `targetPolicy` (`new|selected|explicit|none`), `exclusiveGroup` (`block-create`). Equivalentes existentes a inventariar primeiro: `actionTermSet` (39/40 caps), `excludeMarkers` (37/40), `requiresFilledPlaceholders` (21/40), `isComposite` (3/40), `clarificationMessageKey` (23/40), post-materialization arbitration no suggest service. Gate: só entra se eval (PHASE 7) demonstrar necessidade material + brief de arquitetura dedicado.

---

## 18. History Intelligence (PHASE 9)

Domínio existente (PROVEN): `PlaylistHistoryChangeService` (snapshot diff → summaries), `PlaylistHistoryRepository` (persistência, migrations V008/V009), rotas `/playlists/{id}/history` (até 500 versões) + `POST /{history_id}/restore`. Fase: read-only history intelligence para perguntas como "o que mudou neste painel?" / "quando este slide começou a falhar?" / "compare com a versão anterior". **Restore/write fora de escopo** — permanece no domínio atual. Gate: só depois de user stories reais + inventário de owner/RBAC/payload/consumer.

---

## 19. Roadmap Phases

Ordem inicial por hipótese; reorder só com evidência registrada.

| Phase | Entrega | Depende de | Status |
|---|---|---|---|
| 0 | Baseline + drift closure | — | READY_FOR_EXECUTION |
| 1 | Knowledge Orchestration V1 | 0 | READY_FOR_DIAGNOSTIC |
| 2 | TV Product Guide V1 | 1 | READY_FOR_DIAGNOSTIC |
| 3 | Help Convergence | 2 | BLOCKED |
| 4 | Editor Grounding V2 | 0 | READY_FOR_DIAGNOSTIC |
| 5 | Design Methodology V1 | 1, 4 | READY_FOR_DIAGNOSTIC |
| 6 | Data + Solution Intelligence | 1 | READY_FOR_DIAGNOSTIC |
| 7 | Eval + Telemetry V2 | 0 | READY_FOR_DIAGNOSTIC |
| 8 | Semantic Intent Arbitration | 7 (evidência material) + brief dedicado | BLOCKED |
| 9 | History Intelligence | stories reais + owner inventory | PLANNED |

### PHASE 0 — BASELINE + DRIFT CLOSURE

- **GOAL:** congelar fatos de arquitetura; nenhuma mudança de comportamento.
- **USER VALUE:** baseline confiável para todas as fases.
- **OWNER:** tv-dashboard-api (docs/intelligence).
- **AUTHORITIES:** este documento, capability matrix, ADR, ops catalog, `vista_agent_intelligence.json`, inventários VISTA/TÉO.
- **CURRENT FACTS:** inventário §2.2 (gaps), MCP drift pendente de classificação final (§24).
- **EXISTING_EQUIVALENT:** YES (docs canônicos existem).
- **REUSE_DECISION:** REUSE.
- **ALLOWED SCOPE:** docs + drift register + eval baseline.
- **FORBIDDEN SCOPE:** qualquer runtime code.
- **CONTRACT IMPACT:** NONE. **SECURITY IMPACT:** NONE. **SURFACE IMPACT:** NONE. **DATA/PRIVACY:** NONE.
- **TESTS:** doc validation + link check.
- **EVALS:** baseline do corpus atual congelada.
- **ACCEPTANCE:** todas as fontes identificadas; conflitos classificados; zero reconciliação silenciosa.
- **EVIDENCE TO RETURN:** source map final, drift register, corpus baseline.
- **DEPENDENCIES:** nenhuma.
- **STOP CONDITIONS:** descoberta de código/runtime divergente dos docs.
- **STATUS:** READY_FOR_EXECUTION.

### PHASE 1 — KNOWLEDGE ORCHESTRATION V1

- **GOAL:** intent → smallest sufficient truth set, declarativo.
- **USER VALUE:** respostas certas com menos reads e sem tool spam.
- **OWNER:** tv-dashboard-api (`vista_agent_intelligence.json` → `agent_directives`).
- **AUTHORITIES:** padrão `teo_agent_intelligence.json:knowledge_orchestration`; capability surface VISTA.
- **CURRENT FACTS:** 35 grupos de diretivas já vivos; precedência parcial já em Instructions; `clarificationKey` tipado existe.
- **EXISTING_EQUIVALENT:** YES — `agent_directives` é o canal mutável canônico; precedência/gates TÉO provados.
- **REUSE_DECISION:** EXTEND (novo bloco `knowledge_orchestration` no JSON existente).
- **ALLOWED SCOPE:** `vista_agent_intelligence.json` + `vista_agent_intelligence_service.py` (projeção) + testes de contrato.
- **FORBIDDEN SCOPE:** novas tools/Actions; runtime routing em código novo; markers do suggest.
- **CONTRACT IMPACT:** NONE (conteúdo de `agent_directives`, já versionado por deploy).
- **SECURITY IMPACT:** NONE. **SURFACE IMPACT:** envelope de catálogo — respeitar budget 100 KiB (projeção Actions já compacta).
- **DATA/PRIVACY:** NONE.
- **TESTS:** projeção por transporte, zero tools novas, cobertura de família de intents, gates, precedência, suficiência, gap labels — espelho `test_teo_knowledge_orchestration.py`.
- **EVALS:** corpus existente sem regressão.
- **ACCEPTANCE:** routing table + precedence + gates + sufficiency + gap handling + testes.
- **EVIDENCE TO RETURN:** bloco projetado em `get_catalog` (ambos transportes), test report.
- **DEPENDENCIES:** PHASE 0.
- **STOP CONDITIONS:** se exigir nova tool ou mudança de dispatch → STOP → Architecture.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 2 — TV PRODUCT GUIDE V1

- **GOAL:** registry canônico de orientação de uso (`GUIDANCE_NOT_DOMAIN_TRUTH`).
- **USER VALUE:** VISTA responde "como/quando usar" com fonte versionada, não memória.
- **OWNER:** tv-dashboard-api content/intelligence (novo sub-package `product_guide/` no bounded context).
- **AUTHORITIES:** padrão TÉO `product_guide_*`; ops catalog; capability surface.
- **CURRENT FACTS:** inexistente em VISTA (MISSING confirmado); TÉO registry PROVEN com 24 tópicos e validação fail-closed.
- **EXISTING_EQUIVALENT:** YES (padrão a replicar no próprio owner).
- **REUSE_DECISION:** EXTEND (porta do mecanismo, não do conteúdo).
- **ALLOWED SCOPE:** registry + schema + content topics WAVE_1 + service + testes; Action Surface Gate decide transporte.
- **FORBIDDEN SCOPE:** virar autoridade de domínio/AuthZ/contrato; duplicar schemas de capability; frontend bundling semântico.
- **CONTRACT IMPACT:** ADDITIVE (novo recurso read-only; Action Surface Gate decide se vira tool).
- **SECURITY IMPACT:** read-only; guidance nunca autoriza.
- **SURFACE IMPACT:** NEW TOOL = TO_INVENTORY (gate §11.6).
- **DATA/PRIVACY:** NONE.
- **TESTS:** schema rejection, seeds determinísticos, cross-ref vs capability/ops registries, seções, 404/400 tipados, help-view field exclusion.
- **EVALS:** perguntas de uso respondidas com `source_refs` — medir em PHASE 7.
- **ACCEPTANCE:** registry versionado + schema validation + cross-reference validation + derived index + testes.
- **EVIDENCE TO RETURN:** registry, índice, resultado do Action Surface Gate.
- **DEPENDENCIES:** PHASE 1 (orquestração sabe quando consultar o guide).
- **STOP CONDITIONS:** guide precisar de mutation authority ou duplicar contrato de domínio → STOP.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 3 — HELP CONVERGENCE

- **GOAL:** Portal Help consome a mesma semantics do Product Guide.
- **USER VALUE:** ajuda do produto e especialista dizem a mesma coisa.
- **OWNER:** tv-dashboard-api (projeção help) + plugins/tv-dashboard (consumo MFE).
- **AUTHORITIES:** PHASE 2 registry; padrão `view=help` do TÉO.
- **CURRENT FACTS:** Help/editor docs MFE hoje são copy local (TO_INVENTORY os arquivos exatos).
- **EXISTING_EQUIVALENT:** TO_INVENTORY (mapear manual atual do MFE).
- **REUSE_DECISION:** EXTEND.
- **ALLOWED SCOPE:** projeção `view=help` + mapeamento seções→tópicos + consumo MFE.
- **FORBIDDEN SCOPE:** copy semântica duplicada no bundle; UI copy específica fora do escopo (fica local).
- **CONTRACT IMPACT:** ADDITIVE (route read-only).
- **SECURITY IMPACT:** session auth `tv-dashboard.read`-equivalente; strip de refs internas.
- **SURFACE IMPACT:** NEW TOOL = NO (HTTP route MFE, não agent tool).
- **DATA/PRIVACY:** NONE.
- **TESTS:** help-view não vaza campos internos; seção mapeada sem copy própria; fallback controlado.
- **EVALS:** N/A.
- **ACCEPTANCE:** zero prosa semântica duplicada nos tópicos mapeados; UI-only local; fallback controlado.
- **EVIDENCE TO RETURN:** lista de tópicos convergidos + teste de não-duplicação.
- **DEPENDENCIES:** PHASE 2.
- **STOP CONDITIONS:** guide registry indisponível; MFE exigir bundle da autoridade semântica.
- **STATUS:** BLOCKED (dependência).

### PHASE 4 — EDITOR GROUNDING V2

- **GOAL:** grounding de seleção/foco mais forte e declarado.
- **USER VALUE:** "o bloco selecionado" resolve com menos ambiguidade e menos ghost-ops.
- **OWNER:** tv-dashboard-api (`EditorFocusStore` + projection em `get_playlist_context`).
- **AUTHORITIES:** `editor_focus_store.py`, `presentation_realtime_hub.py`, `response_compact.py`, padrão `workspace_context` do TÉO.
- **CURRENT FACTS:** `editorFocus` PROVEN com TTL/grace; sem estados `ACTIVE/STALE/ABSENT/AMBIGUOUS` declarados; `selectedIds` existe; tipo vem via `blockIndex`/`focusedBinding`.
- **EXISTING_EQUIVALENT:** YES (store + projeção existem; falta shape semântico).
- **REUSE_DECISION:** EXTEND.
- **ALLOWED SCOPE:** projeção `editorContext` compacta + estados + testes.
- **FORBIDDEN SCOPE:** duplicar nativeConfig; autorização via contexto; estourar payload budget.
- **CONTRACT IMPACT:** ADDITIVE (campo novo read).
- **SECURITY IMPACT:** contexto continua hint de navegação.
- **SURFACE IMPACT:** NEW TOOL = NO.
- **DATA/PRIVACY:** dados efêmeros de sessão do próprio usuário.
- **TESTS:** estados, TTL/grace, AMBIGUOUS multi-cliente, budget de envelope.
- **EVALS:** delta em CREATE-vs-ALTER e grounding no corpus.
- **ACCEPTANCE:** projeção compacta + 4 estados + budget preservado + melhora mensurável de grounding.
- **EVIDENCE TO RETURN:** shape do payload + testes + eval delta.
- **DEPENDENCIES:** PHASE 0.
- **STOP CONDITIONS:** precisar de estado novo não efêmero ou cruzar ownership do WS hub.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 5 — DESIGN METHODOLOGY V1

- **GOAL:** readiness de decisão de design estruturada.
- **USER VALUE:** "melhore este slide" vira decisão com fatos, não opinião.
- **OWNER:** tv-dashboard-api intelligence (`design_intelligence` + recipes + digests).
- **AUTHORITIES:** padrão `guide_v2.py` do TÉO (adaptado); `design_intelligence.json`; `ReadySlideQualityService`.
- **CURRENT FACTS:** serviços de design PROVEN; sem modelo readiness/sufficiency/next-question.
- **EXISTING_EQUIVALENT:** YES (parcial — fatos já existem como digests; falta o modelo).
- **REUSE_DECISION:** EXTEND.
- **ALLOWED SCOPE:** modelo de intents/context facts/readiness em content+service; testes.
- **FORBIDDEN SCOPE:** metodologia como autoridade de estado; novo renderer; vazar domain truth.
- **CONTRACT IMPACT:** NONE (enriquece respostas existentes).
- **SECURITY IMPACT:** NONE. **SURFACE IMPACT:** NEW TOOL = NO.
- **DATA/PRIVACY:** NONE.
- **TESTS:** intents, tri-state facts, readiness, stop reasons, next-question não-repetição.
- **EVALS:** corpus de design review (PHASE 7).
- **ACCEPTANCE:** intent routing + context facts + sufficiency + next-question metadata; zero vazamento de autoridade.
- **EVIDENCE TO RETURN:** modelo + testes + eval.
- **DEPENDENCIES:** PHASE 1, PHASE 4.
- **STOP CONDITIONS:** exigir mutação fora de PresentationMutation ou segundo renderer.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 6 — DATA + SOLUTION INTELLIGENCE

- **GOAL:** melhor seleção de fonte/rota/contexto de negócio; visibilidade de ecossistema.
- **USER VALUE:** "quero EBITDA na TV" mapeia para o produto/rota dona, não para busca cega.
- **OWNER:** tv-dashboard-api (projeção); Core permanece owner do catálogo de soluções; api-delpi owner dos contratos.
- **AUTHORITIES:** `x-delpi` injector, `generate_tv_data_routes_from_openapi.py`, `tv_data_routes.json` + overlays, `solution_read` TÉO (padrão), Core `/solutions`.
- **CURRENT FACTS:** `x-delpi` import PROVEN; `entity` não persistido; `presentationStrategy` dead; zero solution metadata nas rotas.
- **EXISTING_EQUIVALENT:** YES (parcial — metadados existem na fonte; falta persistir/projetar).
- **REUSE_DECISION:** EXTEND (gerador/overlay + projeção Core).
- **ALLOWED SCOPE:** persistir metadados de owner/grão/unidade com fonte canônica provada; projeção solution_context quando o pedido cruzar fronteira de produto.
- **FORBIDDEN SCOPE:** catálogo semântico paralelo; chamar ecossistema em authoring rotineiro; conectar Core sem contrato.
- **CONTRACT IMPACT:** ADDITIVE em `tv_data_routes.json` + possível read de solução.
- **SECURITY IMPACT:** visibility ≠ authorization (declarado); Bearer-forwarded user-parity.
- **SURFACE IMPACT:** NEW TOOL = TO_INVENTORY (reuso de `search_data_routes`/`get_catalog` primeiro).
- **DATA/PRIVACY:** metadados públicos de produto.
- **TESTS:** generator/overlay, projeção, 0-results ≠ ausência, fit vocabulary fechado.
- **EVALS:** data-route retrieval accuracy no corpus.
- **ACCEPTANCE:** metadados com owner provado; reuse do Core; zero catálogo paralelo; search-miss tratado corretamente.
- **EVIDENCE TO RETURN:** field→owner map, projeção, eval delta.
- **DEPENDENCIES:** PHASE 1 (gate de quando consultar ecossistema).
- **STOP CONDITIONS:** sem owner canônico para metadado → não persistir; exigir autoridade nova.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 7 — EVAL + TELEMETRY V2

- **GOAL:** inteligência VISTA mensurável.
- **USER VALUE:** melhorias provadas por delta, não por opinião.
- **OWNER:** tv-dashboard-api (corpus + gates + telemetry service existente).
- **AUTHORITIES:** corpus C1–C31 + fixture gate; `presentation_mutation_telemetry.py`; protocolo `ai-intelligence-evaluation.mdc`.
- **CURRENT FACTS:** corpus ready-slide PROVEN; benchmark geral e telemetry de decisão MISSING.
- **EXISTING_EQUIVALENT:** YES (corpus + gate + telemetry service existem para estender).
- **REUSE_DECISION:** EXTEND.
- **ALLOWED SCOPE:** corpus ampliado + harness baseline/candidate + campos de telemetria seguros.
- **FORBIDDEN SCOPE:** logar JWT/secrets/payloads sensíveis/prompts privados por default.
- **CONTRACT IMPACT:** NONE (observabilidade).
- **SECURITY IMPACT:** allowlist de campos de log — revisar cada campo novo.
- **SURFACE IMPACT:** NONE.
- **DATA/PRIVACY:** agregados apenas.
- **TESTS:** gate do corpus; harness; redaction.
- **EVALS:** é a própria fase.
- **ACCEPTANCE:** corpus congelado + comparação baseline/candidate + sinais seguros em runtime + relatório de qualidade.
- **EVIDENCE TO RETURN:** baseline congelada + formato de relatório de delta.
- **DEPENDENCIES:** PHASE 0.
- **STOP CONDITIONS:** telemetria exigir dados privados ou novo serviço externo.
- **STATUS:** READY_FOR_DIAGNOSTIC.

### PHASE 8 — SEMANTIC INTENT ARBITRATION

- **GOAL:** reduzir colisão marker/fan-out estruturalmente.
- **USER VALUE:** menos ops candidatas erradas (classe de bug do create duplicado).
- **OWNER:** tv-dashboard-api suggest layer.
- **AUTHORITIES:** `presentation_suggest_ops_service.py` + catalog fields existentes.
- **CURRENT FACTS:** `actionTermSet`/`excludeMarkers`/`requiresFilledPlaceholders`/`isComposite`/arbitration pós-materialização existem; regressões provam limite.
- **EXISTING_EQUIVALENT:** YES (metadados declarativos já existem — avaliar extensão, não engine nova).
- **REUSE_DECISION:** EXTEND (avaliado) — NEW proibido sem brief de arquitetura.
- **ALLOWED SCOPE:** TBD pelo brief dedicado.
- **FORBIDDEN SCOPE:** engine nova genérica; dedup semântico arbitrário; registry de equivalência.
- **CONTRACT IMPACT:** TBD. **SECURITY IMPACT:** NONE esperado. **SURFACE IMPACT:** NONE.
- **DATA/PRIVACY:** NONE.
- **TESTS:** regressões + corpus.
- **EVALS:** requisito de entrada (evidência material de PHASE 7).
- **ACCEPTANCE:** brief de arquitetura aprovado primeiro.
- **EVIDENCE TO RETURN:** eval delta mostrando necessidade.
- **DEPENDENCIES:** PHASE 7.
- **STOP CONDITIONS:** qualquer push para implementar sem gate de arquitetura.
- **STATUS:** BLOCKED.

### PHASE 9 — HISTORY INTELLIGENCE

- **GOAL:** awareness read-only de mudanças.
- **USER VALUE:** "o que mudou neste painel?" respondível.
- **OWNER:** tv-dashboard-api (`PlaylistHistoryChangeService`/`Repository` + projection).
- **AUTHORITIES:** rotas `/history` existentes, migrations V008/V009.
- **CURRENT FACTS:** domínio PROVEN; sem exposição à VISTA; restore existe no domínio (fora de escopo aqui).
- **EXISTING_EQUIVALENT:** YES (domínio inteiro já existe — falta projeção read).
- **REUSE_DECISION:** EXTEND.
- **ALLOWED SCOPE:** read-only projection + perguntas de diff/comparação.
- **FORBIDDEN SCOPE:** restore/write via agente; expor trilha além do RBAC existente.
- **CONTRACT IMPACT:** NONE/ADDITIVE (read).
- **SECURITY IMPACT:** RBAC `tv-dashboard.read`-equivalente; nada além.
- **SURFACE IMPACT:** NEW TOOL = TO_INVENTORY (gate).
- **DATA/PRIVACY:** actor names já snapshotados (V009); manter.
- **TESTS:** RBAC, payload, consumer real.
- **EVALS:** perguntas de história no corpus.
- **ACCEPTANCE:** owner + RBAC + payload + consumer real provados antes de qualquer tool.
- **EVIDENCE TO RETURN:** inventory + decisão do gate.
- **DEPENDENCIES:** user stories reais.
- **STOP CONDITIONS:** pedido de restore/write → out of scope.
- **STATUS:** PLANNED.

---

## 20. Phase Gates

Gate de entrada em execução (qualquer fase): brief dedicado citando `ROADMAP_PHASE` + seção; HEAD re-ancorado; owner confirmado; EXISTING_EQUIVALENT inventariado; escopo allowed/forbidden revisado contra HEAD (este mapa pode ter driftado).

Gate de saída: acceptance da fase + evidência listada + eval delta quando aplicável + atualização de status nesta tabela (§19) com commit do resultado.

---

## 21. Security

Preservado em todas as fases: backend-first AuthZ; VISTA capability ≤ capability do usuário; catalog ≠ authorization; guide ≠ authorization; methodology ≠ authorization; solution visibility ≠ authorization; confirmation ≠ authorization; editor context = hint ≠ authorization; writes só via PREPARE→COMMIT com RBAC fresco do Core. Nenhuma fase muda segurança por default; telemetria passa por allowlist de campos.

---

## 22. Transport / Surface Strategy

Actions e MCP são projeções do mesmo dispatch — toda nova fonte de conhecimento entra como dado/conteúdo de superfícies existentes antes de se considerar tool nova. `NEW TOOL REQUIRED?` = **NO** por default em todas as fases; exceções só via Action Surface Gate documentado (consumidor real + budget + owner). O parity registry (`surface_parity.parity_map`) continua a fonte única Actions↔MCP.

---

## 23. Test Strategy

Espelhar o padrão TÉO onde couber: contract/boundary tests por mecanismo (orquestração, guide, metodologia), gates de corpus para comportamento, budget tests para envelopes, unified-boundary para paridade. Toda fase adiciona positive + sibling + negative. Nunca alterar expected para acomodar comportamento inesperado.

---

## 24. Drift / Documentation Policy

**Classificação registrada neste documento:**

- **MCP go-live:** capability matrix diz backend PROVEN + provisioning externo PENDING; ambiente ChatGPT atual já invoca tools VISTA MCP usáveis. Classificação: **ENVIRONMENT_SCOPE_DIFFERENCE** (provável) — "go-live pendente" refere-se a provisioning formal do client Keycloak `mcp-tv-dashboard` + go-live de provider/gateway, enquanto o conector dev já opera. **Não reconciliar silenciosamente:** PHASE 0 deve verificar com o operador qual credencial está em uso e corrigir o claim com evidência (→ `DOCUMENTATION_DRIFT` se o provisioning já ocorreu de fato).
- **`/data/copilot/*`:** 410 Gone — sem drift.
- **Render worker:** retirado; docs dizem `editor_live` único produtor — sem drift.
- Regra permanente: divergência doc↔código é registrada neste documento (§24) antes de qualquer edição reconciliatória.

---

## 25. Success Metrics

- Corpus VISTA ampliado com delta baseline→candidate em toda mudança de inteligência.
- Routing: % de intents resolvidos com o conjunto mínimo de fontes (medido por PHASE 7).
- Grounding: redução de ghost-ops e clarificações desnecessárias (eval PHASE 4/7).
- Product Guide: % de perguntas de uso respondidas com tópico versionado + zero referências quebradas em CI.
- Superfície: 10 tools MCP mantidas salvo gate aprovado.

---

## 26. Deferred / Rejected Ideas

| Ideia | Decisão | Razão |
|---|---|---|
| VISTA chamar TÉO para entender TV | REJECTED | boundary violada; TÉO é padrão, não backend |
| Nova tool por fase | REJECTED | Action Surface Gate; default NO |
| Product Guide como autoridade | REJECTED | GUIDANCE_NOT_DOMAIN_TRUTH enforced |
| Engine genérica de dedup/arbitration | DEFERRED (PHASE 8) | precisa de evidência de eval antes |
| Restore de histórico via agente | REJECTED nesta trilha | write; fora do escopo read-only |
| Renderer autônomo | REJECTED (decisão vigente) | `editor_live` é o único produtor de pixels |
| Copiar `record_read`/CRUD TÉO | REJECTED | VISTA é workflow de apresentação, não multi-entity CRUD |
| Catálogo semântico paralelo de rotas | REJECTED | projetar metadados do owner canônico |

---

## Change Control

Toda emenda a este documento registra: WHAT CHANGED / WHY / EVIDENCE / OWNER / IMPACT ON OTHER PHASES. Prompts futuros de implementação devem declarar `ROADMAP_PHASE = PHASE_<N>_<NAME>` + seção; prompt sem mapeamento para fase documentada → STOP → Architecture/Coordination, salvo emenda deliberada prévia deste roadmap.

## Status Semantics

`PLANNED` (conceito aprovado, sem diagnostic gate) · `READY_FOR_DIAGNOSTIC` (escopo/owner conhecidos, mecânica atual a provar) · `READY_FOR_EXECUTION` (causa/mecanismo/owner/contratos provados) · `BLOCKED` (dependência não resolvida) · `DONE` (implementado + verificado + documentado).
