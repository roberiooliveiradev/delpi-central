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
| 0 | Baseline + drift closure | — | DONE (§27) |
| 1 | Knowledge Orchestration V1 | 0 | DONE (§28) |
| 2 | TV Product Guide V1 | 1 | DONE (§30) |
| 3 | Help Convergence | 2 | DONE (§32·§33 runtime-verified) |
| 4 | Editor Grounding V2 | 0 | READY_FOR_EXECUTION (§34) |
| 5 | Design Methodology V1 | 1, 4 | READY_FOR_DIAGNOSTIC |
| 6 | Data + Solution Intelligence | 1 | READY_FOR_DIAGNOSTIC |
| 7 | Eval + Telemetry V2 | 0 | READY_FOR_EXECUTION (§35 diagnostic done — exec requer promoção) |
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
- **STATUS:** DONE — execução registrada em §27 (2026-10-08).

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
- **STATUS:** DONE — implementado e verificado em §28 (2026-10-08); `knowledge_orchestration` vive na autoridade única `vista_agent_intelligence.json`, projeção MCP full / Actions compact, parity PASS, budget PASS, zero tools novas.

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
- **STATUS:** DONE — implementado e verificado em §30 (2026-10-09): registry live com 11 tópicos Wave-1, validação fail-closed contra registries canônicos, `get_product_guide`/`gpt_get_product_guide` com paridade Actions↔MCP, help projection em `GET /product-guides`, `product_usage` PROVEN, budget Actions restaurado sem elevar cap.

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
- **STATUS:** DONE — implementado e verificado em §32 (2026-10-09): central Help em `/apps/tv-dashboard/help` (view `help` + nav «Ajuda» na home), `fetchProductGuideHelp` via httpClient existente sobre a projeção help-safe `product_guide_help_v1`, mapa seção→tópico 11×11 exato, merge server-semântica+local-UI, estados loading/401-403/404-422/5xx-network/empty-index/drift distintos sem fallback semântico duplicado, shared `createDashboardUserManual` reutilizado, zero backend/public/security change, testes novos verdes e `vite build` OK. Residual registrado em §32.6/§32.9.

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
- **STATUS:** READY_FOR_EXECUTION (§34 diagnostic, 2026-10-09).

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
- **STATUS:** READY_FOR_EXECUTION — diagnostic DONE (§35, 2026-10-09); measurement architecture proven; execução de corpus/telemetry requer promoção explícita.

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

---

## 27. PHASE 0 — EXECUTION RECORD (baseline freeze, 2026-10-08)

> Executado por `VISTA-KIC-V1-PHASE-0-BASELINE-DRIFT-CLOSURE`. Documentação + evidência somente; zero mudança de runtime/produção. Baseline de análise: HEAD `336d6b0f` (ancestor de `origin/main`; KIC commit `0cb4d437ea` confirmado em origin).

### 27.1 Baseline snapshot

```text
VISTA KIC-V1 BASELINE
HEAD             = 336d6b0f (ancestor of origin/main d6c1e3d2)
CATALOG          = 2026.10.05.presentation-authority.datamodel-patch.lossless
INTELLIGENCE     = vista_agent_intelligence.json v2026.09.28.3
RECIPES          = presentation_recipes.json v2026.09.22.10
DESIGN_INTEL     = design_intelligence.json v2026.09.23
CORPUS           = vista_ready_slide_corpus.json v2026.09.23 (C15-C31 + G_*)
FIXTURE PROVENANCE = corpus@b129bfa60c · intelligence@1c545fb934 · catalog@55cdc2974f
ACTIONS          = 10 operations (+2 support routes)
MCP              = 10 tools
PARITY           = PASS (126 tests — unified boundary, MCP conformance,
                   read/write surfaces, catalog budget, corpus gate,
                   builder-instructions budget, agent intelligence)
GROUNDING        = PARTIAL (mecânica PROVEN; estados semânticos ausentes)
VISUAL EVIDENCE  = ladder §27.8 (wire PROVEN; host delivery FAIL_OBSERVED)
DISPLAY FORMAT   = PARTIAL (typed op cobre 2 owners)
HISTORY          = DOMAIN PROVEN / VISTA_SURFACE ABSENT
PROPOSAL STORE   = SINGLE_PROCESS ACCEPT_WITH_RESIDUAL
MCP PROVISIONING = ENVIRONMENT_SCOPE_DIFFERENCE (§27.13)
EVAL BASELINE    = inventário §27.14 (medições NOT_MEASURED por design)
DRIFTS           = register §27.12 (1 open env-scope, 3 minor residuals)
```

### 27.2 Source-of-truth map (revalidado em HEAD)

| Concern | Canonical owner | Canonical source | Derived sources | Runtime consumers | Status | Drift |
|---|---|---|---|---|---|---|
| Identity | Keycloak | JWT/OIDC | — | todas as superfícies | PROVEN | — |
| Platform RBAC | Core API | `load_user_rbac` (fresh em governed write) | permission cache (não usado em write) | tv-dashboard-api | PROVEN | — |
| Playlist/slides/blocks | tv-dashboard-api | Postgres `tv_dashboard` + nativeConfig | `get_playlist_context` projections | MFE, VISTA, TV | PROVEN | — |
| PresentationMutation | tv-dashboard-api | `presentation_mutation/` + ops catalog | — | `TvPresentationWriteService` | PROVEN | — |
| Typed ops (32) | ops catalog | `presentation_ops_content.json` `operations` | `inputSchema` projections | suggest/PREPARE | PROVEN | — |
| Write boundary | `TvPresentationWriteService` | canonical writer | PREPARE→COMMIT facade | governed writes | PROVEN | — |
| Resource AuthZ | `PlaylistAccessService` | resource scope | — | writes + reads | PROVEN | — |
| Capability surface | `capability_surface.py` | `_canonical_surface` | Actions/MCP projections | `get_catalog` | PROVEN | — |
| Agent directives | `vista_agent_intelligence.json` | 35 grupos + metadata | transport projections | `get_catalog` | PROVEN | `visual_verification` slot emite `{}` (intencional) |
| Actions projection | parity map inversa | `surface_parity.parity_map` | compacted envelope | GPT Actions | PROVEN | — |
| MCP projection | neutral names | mesmo JSON | neutralized envelope | MCP | PROVEN | — |
| Data contracts | api-delpi OpenAPI | `openapi.json` + `x-delpi` | `tv_data_routes.json` | `search_data_routes` | PROVEN | `x-delpi.entity` não persistido; `presentationStrategy` extraído sem consumidor (residual) |
| Route overlays | `tv_data_route_overlays.json` | curadoria owner-local | merged catalog | discovery/suggest | PROVEN | — |
| DataModel | tv-dashboard-api | `upsert_data_model`/`inspect`/`preview` | — | ops + reads | PROVEN | — |
| Design intelligence | `design_intelligence.json` | `DesignIntelligenceService` | designAudit/semanticDigest/visualRecommendation | preview + context | PROVEN | — |
| Recipes | `presentation_recipes.json` | `PresentationRecipeService` | recipe catalog | compound creates | PROVEN | — |
| Layout intelligence | `LayoutDigestService` + `SlideAutoLayoutService` + `SafeAutoFixService` | digests + fixes | `layoutDigest`, `apply_safe_layout_fixes` | context + ops | PROVEN | — |
| Filter intelligence | `FilterDigestService` | digests + `re_layer_playlist_filters` | `filterDigest` | context + ops | PROVEN | — |
| Display formatting | `DisplayFormatHintsService`/`DisplayFormatService` | hints + `set_display_format` | format bindings | preview + ops | PARTIAL (§27.9) | — |
| Editor focus | `EditorFocusStore` + `PresentationRealtimeHub` | ephemeral focus rows | `editorFocus` projection | reads | PROVEN (mecânica) | — |
| Visual evidence | editor vivo (canonical_stage) | `slidePreview.rendered` | signed URL + MCP ImageContent | VERIFY | PROVEN wire / host gap | `CHATGPT_APP_IMAGE_DELIVERY=FAIL_OBSERVED` |
| History | `PlaylistHistoryRepository` + service | migrations V008/V009 + diff service | `/playlists/{id}/history` | admin API | PROVEN domínio / VISTA surface ABSENT | — |
| Eval corpus | `vista_ready_slide_corpus.json` | C15–C31 + G_* | gate test | CI | PROVEN | — |
| Proposal storage | `ProposalStore` (in-process) | `proposal.py` + `proposal_store.py` | HMAC opaque handle | PREPARE→COMMIT | ACCEPT_WITH_RESIDUAL | single-process |
| DÉLIA TV integration | — | TARGET documental | — | — | TARGET | — |

### 27.3 Live surface baseline

| Métrica | Valor | Status |
|---|---|---|
| GPT Actions operations | **10**: `gpt_get_catalog`, `gpt_list_playlists`, `gpt_get_playlist_context`, `gpt_search_data_routes`, `gpt_preview_data_block`, `gpt_preview_data_model`, `gpt_inspect_data_model`, `gpt_suggest_change`, `gpt_preview_change`, `gpt_commit_change` (+ `gpt_get_openapi_schema` schema route + `gpt_get_slide_preview_png` Actions-only asset helper) | PROVEN (`__init__.py:10-21`, routes L141-389) |
| MCP tools | **10**: `list_playlists`, `get_playlist_context`, `get_catalog`, `search_data_routes`, `inspect_data_model`, `preview_data_model`, `preview_data_block`, `suggest_change`, `prepare_change`, `commit_proposal` | PROVEN (`constants.py:28-41` + drift guard `server.py:331-334`) |
| Capabilities | **40** (`presentation_ops_content.json` L3272+) | PROVEN |
| Typed ops | **32** (`operations` L883-3271) | PROVEN |
| Agent directives | **35 grupos** + `actions_runtime` + metadata | PROVEN |
| catalogVersion | `2026.10.05.presentation-authority.datamodel-patch.lossless` | PROVEN |
| Parity map | `surface_parity.parity_map` 10 pares; `not_exposed_in_mcp=[gpt_get_slide_preview_png]` | PROVEN |

**SURFACE_PARITY = PASS** — unified boundary + neutralization + MCP manifest guard + budget: 126 testes verdes (§27.16). Nenhum `gpt_*`/`commit_now` no surface MCP; nenhuma semantic MCP-only em Actions; parity map completo e derivado.

### 27.4 Intelligence baseline (por diretiva)

35 grupos em `vista_agent_intelligence.json` — todos PROVEN como conteúdo vivo servido via `agent_directives`; consumers reais e testes cobrem a maioria (`design_intelligence`, `visual_selection`, `filter_layering`, `layout_perception`, `compound_slide`, `write_quality`, `editor_focus`, `object_resolution`, `data_discovery`, `display_format`, `presentation_recipes`, `media_limits`, `published_templates`, `branch_scope`, `si_goals`, `continuous_review`, `playlist_curation`, `slide_craft`, `slide_design`, `data_transform`, `data_model`, `shape_chrome`, `composed_visuals`, `visual_impact`, `execution_posture`, `screenshot_parity`, `param_expressions`, `modes`, `write_flow`, `write_flow_mcp`, `anti_patterns`, `auth_errors`, `mcp_delia`, `surface_parity`, `brand_logo`). PARTIAL conhecido: `visual_verification` (bloco removido intencionalmente; slot de projeção emite `{}` — testado). TARGET: nenhum.

### 27.5 Intelligence services baseline

Todos PROVEN em `tv_app/application/services/`: `VistaAgentIntelligenceService` (projeção de diretivas por transporte), `DesignIntelligenceService` (audit/digest/recommendation), `PresentationRecipeService`, `LayoutDigestService`, `FilterDigestService`, `StoryDigestService`, `JoinPlanService` (joinHints), `DisplayFormatHintsService`/`DisplayFormatService`, `ReadySlideQualityService`, `VisualVerificationService`, `SlidePreviewRenderService` (schematic + signed URL), `SlideAutoLayoutService`, `SafeAutoFixService`, `PresentationOpsContentService` (catálogo autoridade), `PresentationSuggestOpsService` + `PresentationCommandPlannerService` + `PresentationCommandRecognitionService` + `PresentationHttpCommandPlannerService`, `TvDataRouteCatalogService`/`TvDataRouteDiscoveryService`/`TvDataRouteSuggestService`/`TvDataPreviewService`/`TvCatalogSelectionEvidenceService`, `TvDataBuilderService`+`presentation_builder_facade`, `EditorFocusStore`, `PresentationRealtimeHub`, `TvPresentationWriteService`/`TvGptCommitService`, `TvOpenApiCatalogSyncService`, `PlaylistHistoryChangeService`/`PlaylistHistoryRepository`, `BrandLogoMediaService`. Residual de fragilidade (não-drift): gerador OpenAPI vive em `scripts/` raiz e stub vazio em `tv-dashboard-api/tools/` (dual-location resolvido por `TV_OPENAPI_GENERATOR_SCRIPT`).

### 27.6 Editor grounding baseline

`EditorFocusStore`: efêmero por usuário; campos `playlistId`, `slideId`, `clientId`, `selectedIds[]`, `selectedDataSourceId?`, `updatedAt`; TTL 90s + grace `stale`<=180s; heartbeat MFE 30s; `PresentationRealtimeHub.selection_update` → focus; `visual_capture_request` direcionado por `clientId`. `get_playlist_context` projeta `editorFocus` `{slideId, selectedIds, updatedAt, stale, selectedDataSourceId?}` (clientId/playlistId internos não projetados) + `focusedSlide` (nativeConfig completo) + `blockIndex`/`objectMatches`/`focusedBinding`. **GROUNDING_STATUS = PARTIAL** — mecânica PROVEN; estados semânticos `ACTIVE/STALE/ABSENT/AMBIGUOUS` e `selectedObjects` digest **ausentes** (alvo PHASE 4). `selectedBlockIds`/`focusBlockType` não existem — nomes canônicos: `selectedIds`; tipo via `blockIndex`/`focusedBinding`. Baseline que PHASE 4 deve melhorar.

### 27.7 Data intelligence baseline

| Classe | Itens | Owner |
|---|---|---|
| SOURCE CONTRACT | api-delpi `openapi.json` + `x-delpi` (entity, shape, category, locale, params, tv, presentationStrategy) | api-delpi |
| DERIVED METADATA | `tv_data_routes.json` (gerado), `tv_data_route_overlays.json` (curadoria), aliases, `paramSchema` | tv-dashboard-api |
| RUNTIME EVIDENCE | `preview_data_block`, `preview_data_model`, `inspect_data_model`, `semanticDigest`, `visualRecommendation`, `joinHints`, `displayFormatHints` | tv-dashboard-api |

`SEARCH MISS != ABSENCE` está codificado em Instructions (princípio imutável) e `agent_directives.data_discovery`. `x-delpi.entity` usado só para overlays (não persistido por rota); `presentationStrategy` extraído sem consumidor.

### 27.8 Visual evidence ladder

| Degrau | Status |
|---|---|
| schematic layout / `layoutDigest` / `designAudit` | PROVEN |
| `canonical_stage` (editor-live capture, revision-bound, `source=editor_live`+`clientId`, signed TTL URL) | PROVEN (policy + provenance + E2E stack real) |
| MCP `ImageContent` serializer | PROVEN (`mcp 2.2.0`, `mimeType` correto) |
| MCP streamable-HTTP wire (`content=[text,image]` + structuredContent) | PROVEN (`test_mcp_streamable_http_wire.py`) |
| ChatGPT host image forwarding | **FAIL_OBSERVED** (host runtime delivery gap) |
| Model pixel inspection | **TEST_NOT_RUN** |

`artifact exists != model inspected pixels` — degrau final permanece aberto por limitação do host, não do backend.

### 27.9 Display format baseline

`set_display_format` typed op: `target.owner ∈ {contentRunDataRef, textProjection}` apenas — **2 owners** endereçáveis pelo op dedicado. Demais owners (`kpiOptions.displayValueFormat`, `kpiProjection.metrics[].displayFormat`, `chartOptions.displayValueFormat`/`displayCategoryFormat`, `tableOptions.displayValueFormat`, `tableProjection.columns[].displayFormat`, canvas table) graváveis só via payloads de bloco (`upsert_block`/`bind_visual`), sem op tipado dedicado. **DISPLAY_FORMAT_COVERAGE = PARTIAL** — carregado no roadmap (fora do escopo P0).

### 27.10 History baseline

`PlaylistHistoryChangeService` (snapshot diff→summaries) + `PlaylistHistoryRepository` + rotas `/playlists/{id}/history` (list/get, até 500 versões) + `POST /{history_id}/restore` + actor snapshot (V009). **DOMAIN_HISTORY = PROVEN. VISTA_HISTORY_SURFACE = ABSENT** (nenhuma tool/Action expõe; correto para P0). Restore é write de domínio — fora de escopo de agente (§18).

### 27.11 Proposal store baseline

`ProposalStore` in-process (`threading.RLock` dict), handle HMAC-SHA256 opaco (`b64(id).b64(mac)`), TTL **900s** (`DEFAULT_TTL_SECONDS`), binding: `actor_id` + `capability` + `catalog_version` + `base_revision`; consume único; `PROPOSAL_NOT_FOUND|EXPIRED|CHANGED`; idempotency no commit path (Idempotency-Key em `commit_now`). **SINGLE_PROCESS_SUITABILITY = ACCEPT_WITH_RESIDUAL** (documentado no docstring). **MULTI_WORKER_SUITABILITY = UNSUITABLE** — review trigger: workers>1, réplicas>1 ou cross-process prepare/commit.

### 27.12 Boundary + drift register

**Boundary:** `CHAT = HANDOFF_ONLY` (sem tool de mutação TV; bundle `tv_dashboard_handoff` → resposta direta); `DELIA_TV_ADAPTER = TARGET` (documental, zero coupling); `VISTA = DOMAIN_SPECIALIST` (TV Dashboard = authority — invariante confirmado).

| DRIFT_ID | TYPE | SOURCE_A | SOURCE_B | Description | Owner | Severity | Status | Action |
|---|---|---|---|---|---|---|---|---|
| D-01 | ENVIRONMENT_SCOPE_DIFFERENCE | capability matrix/runbook (`mcp-tv-dashboard` provisioning PENDING) | conector ChatGPT atual invoca tools MCP VISTA | escopos distintos: formal dedicated client+go-live vs connector funcional por caminho OAuth existente (incl. legacy `plugin` client id aceito por `oauth_contract.py:83-89`) | tv-dashboard-api | medium | OPEN (env-scope, não drift de doc) | §27.13 — manter PENDING formal; verificar credencial em uso com operador antes de qualquer emenda |
| D-02 | STALE_EVIDENCE (menor) | generator script em `scripts/` raiz | stub vazio `tv-dashboard-api/tools/` | dual-location resolvida por env; frágil | tv-dashboard-api | low | OPEN residual | reavaliar em manutenção futura |
| D-03 | CONTRACT residual | `x-delpi.presentationStrategy` extraído | sem consumidor downstream | dead extraction | tv-dashboard-api | low | OPEN residual | PHASE 6 decide consumir ou remover |
| D-04 | DOC/intent | `visual_verification` directive slot | bloco removido intencionalmente (emite `{}`) | decisão registrada, não bug | tv-dashboard-api | info | CLOSED | testado (`test_canonical_rendered_preview.py`) |

Nenhum CONTRACT_DRIFT ou EXECUTION_DRIFT encontrado. Escopos distintos não foram classificados como drift automático.

### 27.13 MCP provisioning truth (mandatory closure)

| Item | Evidência em HEAD |
|---|---|
| Backend MCP route mounted | PROVEN (`/mcp` mount; streamable-HTTP) |
| MCP adapter + tool registry | PROVEN (10 tools, `constants.py` + drift guard + conformance) |
| OAuth/Bearer contract | PROVEN (RFC 9728 metadata, audience = MCP URL exata, scope `mcp:tools`; service principals rejeitados em governed write) |
| Keycloak client `mcp-tv-dashboard` | **PENDING** — nenhum script de provisioning em `infra/` (só scripts DÉLIA MCP existem); runbook lista requisitos (confidential, Auth Code+PKCE, scope `mcp:tools`, audience mapper) e marca "do not mark live" até evidência |
| Connector ChatGPT atual | FUNCIONAL em ambiente observado — via caminho OAuth existente (`oauth_contract.py:83-89` aceita `mcp-tv-dashboard` **ou** legacy `plugin` client id); credencial exata em uso não é provável por código |
| Formal go-live | PENDING (runbook + matrix consistentes) |

**MCP_STATUS = ENVIRONMENT_SCOPE_DIFFERENCE.** Backend PROVEN; AUTH CLIENT formal PENDING; CONNECTOR funcional por escopo alternativo; GO-LIVE formal PENDING. Tool-callable-here != rollout formal — a documentação está correta em escopo; **sem reescrita de PENDING**. Ação: operador confirma qual client id está configurado no conector antes de qualquer atualização do claim.

### 27.14 Eval baseline

**Assets (PROVEN):** `vista-ready-slide-eval-corpus.md` (C1–C31 doc), `vista_ready_slide_corpus.json` v2026.09.23 (C15–C31 + G_* gate cases, fixture@b129bfa60c), `test_vista_ready_slide_corpus_gate.py` (gate vivo), `test_presentation_suggest_ops_service.py` (NL→ops regressões), `test_vista_unified_boundary.py` + MCP read/write surfaces + `test_mcp_platform_conformance.py` + `test_mcp_streamable_http_wire.py` (parity/wire), `test_canonical_rendered_preview.py` (visual evidence), `test_vista_builder_instructions_budget.py` + `test_gpt_actions_catalog_budget.py` (envelopes), suites adjacentes de materialization/merge/patch/planner/contract.

**Baseline matrix (coverage != qualidade do modelo):**

| Dimensão | Coverage atual | Measurement? | Baseline value | Gap |
|---|---|---|---|---|
| OBJECT_RESOLUTION | tests + corpus C6/C13/C18 | gate binário | NOT_MEASURED | rubrica/score |
| CREATE_VS_ALTER | suggest suite (recent fixes) | gate binário | NOT_MEASURED | corpus dedicado |
| CLARIFICATION | tests (createBlockTypeRequired, suggestNeedSelection…) | gate binário | NOT_MEASURED | corpus dedicado |
| SINGLE_CREATE | tests (novo bloco family) | gate binário | NOT_MEASURED | corpus dedicado |
| TYPED_OP_VALIDITY | op contract + catalog audit | gate binário | NOT_MEASURED | — |
| DATA_ROUTE_DISCOVERY | discovery service tests | gate binário | NOT_MEASURED | retrieval corpus |
| DATA_PREVIEW | preview tests | gate binário | NOT_MEASURED | — |
| VISUAL_SELECTION | corpus C27–C31 + hints | gate binário | NOT_MEASURED | rubrica de escolha |
| LAYOUT_QUALITY | quality service + auto-fix tests | gate binário | NOT_MEASURED | threshold metrics |
| FILTER_LAYERING | filterDigest/relayer tests | gate binário | NOT_MEASURED | corpus dedicado |
| DISPLAY_FORMAT | bridge tests + hints | gate binário | NOT_MEASURED | coverage matrix |
| WRITE_SAFETY | mutation/merge suites | gate binário | NOT_MEASURED | negative corpus |
| PREPARE_VALIDITY | proposal/commit tests | gate binário | NOT_MEASURED | — |
| VERIFY_OUTCOME | commit+read-back tests | gate binário | NOT_MEASURED | runtime signals |
| TRANSPORT_PARITY | unified boundary + conformance | gate binário | PROVEN (PASS) | — |

`MEASURABLE_NOW` (gate→delta binário): parity, typed-op validity, single-create, CREATE_VS_ALTER, clarification, corpus C15–C31. `NEEDS_FIXTURE`: visual selection rubric, route retrieval corpus, filter-layering corpus, display-format coverage. `NEEDS_TELEMETRY`: outcome/VERIFY em runtime (PHASE 7). `NEEDS_HUMAN_RUBRIC`: design review quality (PHASE 5). **Test pass count != quality score** — valores numéricos ficam NOT_MEASURED por design.

### 27.15 Readiness + consistency

**PHASE 1 readiness gate — todos os critérios PROVEN:** (1) authority conhecida (`vista_agent_intelligence.json`→`agent_directives`); (2) fontes inventariadas (§27.2); (3) zero contract drift afetando orquestração; (4) precedência definível sem mover ownership (todas as fontes permanecem nos owners atuais); (5) `agent_directives` é o host correto (padrão TÉO prova orquestração declarativa no mesmo tipo de artefato); (6) zero tool nova exigida. **PHASE_1 = READY_FOR_EXECUTION** (implementation brief dedicado obrigatório).

**Consistency check:** P0 DONE; P1 READY_FOR_EXECUTION; P2–P7 inalterados (READY_FOR_DIAGNOSTIC/BLOCKED); P8 BLOCKED; P9 PLANNED. Nenhum NEEDS_ROADMAP_AMENDMENT.

**PHASE 7 provenance:** HEAD `336d6b0f` · catalog `2026.10.05.presentation-authority.datamodel-patch.lossless` · intelligence `2026.09.28.3` · corpus `2026.09.23` · fixture@`b129bfa60c` · intelligence@`1c545fb934` · catalog@`55cdc2974f`.

### 27.16 Checks executados

`pytest test_vista_unified_boundary test_mcp_platform_conformance test_vista_mcp_read_surface test_vista_mcp_write_surface test_gpt_actions_catalog_budget test_vista_ready_slide_corpus_gate test_vista_builder_instructions_budget test_vista_agent_intelligence` → **126 passed**. Zero mudança de runtime; nenhum teste enfraquecido.

---


---

## 28. PHASE 1 — EXECUTION RECORD (Knowledge Orchestration V1, 2026-10-08)

> Executado por `VISTA-KIC-V1-PHASE-1-KNOWLEDGE-ORCHESTRATION`. Mudança bounded de inteligência: declarativa + projeção existente; zero novas tools/ops/autoridades.

### 28.1 Implementação

- **FIX_STRATEGY = BOUNDED_PROJECTION** — `agent_directives()` projeta o documento por chave explícita, então a nova seção exigiu uma linha de projeção (`NEEDS_PROJECTION_ONLY`), não plumbing novo.
- `vista_agent_intelligence.json` ganhou `knowledge_orchestration` (principle `ROUTE_TO_SMALLEST_SUFFICIENT_TRUTH_SET`): 11 source families, precedence ladder (9 regras), routing de 9 intents com required/conditional/optional/avoid/stop/sequence/branches + referências a famílias de diretivas existentes (zero duplicação de corpos), 8 gates, composition_order, sufficiency, gap_handling (vocabulário UNKNOWN/TO_INVENTORY/PARTIAL/UNAVAILABLE_IN_CURRENT_SURFACE/UNSUPPORTED), epistemology (9 regras `IS_NOT`), forbidden (9 anti-padrões).
- Version bump: `2026.09.28.3` → `2026.10.08.1`.
- Projeção: `vista_agent_intelligence_service.py` — `knowledge_orchestration` projetada em ambos transportes; `_compact_orchestration_for_actions` reduz a Actions para `{principle, precedence, routing.required}` por budget (~100 KiB); MCP recebe o bloco completo. Mesma fonte semântica.
- Formato evitado na fonte: `!=` era destruído pelo neutralizador MCP (espaço antes de `!`) → vocabulário `IS_NOT` adotado nas regras epistêmicas.

### 28.2 Status das famílias gated (honesto por fase)

`product_usage` = PARTIAL (PHASE 2) · `design_methodology` = PARTIAL (PHASE 5) · `solution_ecosystem` = UNAVAILABLE_IN_CURRENT_SURFACE (PHASE 6) · `history` = UNAVAILABLE_IN_CURRENT_SURFACE (PHASE 9).

### 28.3 Evidência

- `tests/test_vista_knowledge_orchestration.py` (novo, 11 testes): seções requeridas, famílias, statuses, precedence, routing matrix (eval fixture — famílias requeridas por intent), resolução de refs de diretivas contra o documento, gates, sufficiency, gap vocabulary, sequência governada da mutação, ausência de `gpt_*` na projeção MCP, não-duplicação de corpos.
- Gate completo: `pytest test_vista_knowledge_orchestration test_vista_agent_intelligence test_vista_unified_boundary test_mcp_platform_conformance test_vista_mcp_read_surface test_vista_mcp_write_surface test_gpt_actions_catalog_budget test_vista_ready_slide_corpus_gate test_vista_builder_instructions_budget test_presentation_suggest_ops_service` → **206 passed**.
- Budget: envelope Actions voltou abaixo de 102400 com headroom ≥ 4 KiB via compactação — limite não alterado.
- Residual search: zero import TÉO runtime, zero tools/ops novas, refs de diretivas válidas.

### 28.4 Residuals

- Actions carrega a forma compacta (required families + precedence); gates/sufficiency/epistemology completas são MCP-primary — mesma fonte, projeção assimétrica já prevista pelo mecanismo existente.
- Orquestração é guidance declarativa para o especialista; não há enforcement runtime (fora do escopo — PHASE 7 avalia outcome).

### 28.5 Efeito downstream

Dependência P1 satisfeita → P5 (Design Methodology) e P6 (Data+Solution) permanecem READY_FOR_DIAGNOSTIC — requerem diagnóstico próprio antes de execução.

---

## 29. PHASE 2 — DIAGNOSTIC RECORD (TV Product Guide V1, 2026-10-08)

> Executado por `VISTA-KIC-V1-PHASE-2-TV-PRODUCT-GUIDE-DIAGNOSTIC`. Diagnóstico/inventário somente — zero código de produção. Baseline: HEAD `48a188148f` == origin/main.

### 29.1 Decisão de owner

`PRODUCT_GUIDE_OWNER = tv-dashboard-api` → content/intelligence layer (mesmo owner de `vista_agent_intelligence.json`, `presentation_ops_content.json`). Autoridade: `GUIDANCE_NOT_DOMAIN_TRUTH` enforced no schema (literal). Nenhum registry existente em `tv_app/content/` é host adequado: `vista_agent_intelligence.json` é policy operacional (não tópicos de uso), `tv_data_route_overlays.json`/`design_intelligence.json`/`presentation_recipes.json` são autoridades por-facet que viram `source_refs`, não o registry. `tv_dashboard_content.json`/`native_screens.json`/`dashboard_slide_presets.json` são labels/catálogos, sem camada semântica. Conclusão: registry novo no bounded context, padrão TÉO adaptado.

### 29.2 Referência TÉO (transformometro-api — não api-delpi)

Padrão PROVEN: `tm_app/application/product_guide/{schema,registry,service}.py` + `tm_app/content/product_guides/*.json` (24 tópicos) + `routes/product_guide_routes.py` (`GET /transformometro/product-guides?view=help`) + `gpt_get_product_guide`/`get_product_guide` (Actions+MCP via capability binding único) + MFE `helpGuideContent.ts` (`HELP_SECTION_TOPICS` + `mergeManualWithGuides` + fallback) + `HelpPage.tsx` via `createDashboardUserManual` (`plugin-ui`).

Classificação dos mecanismos: REUSE_PATTERN — file-per-topic `id==filename`, schema fail-closed bounded, cross-refs validados no load contra catálogo vivo via provider injetável, versão registry+payload, projeção agent-full vs help-whitelist, testes de invariantes semânticos + coverage matrix. ADAPT — `capability_refs` devem validar contra `capability_surface`/ops catalog VISTA (não o catálogo TÉO); parity binding VISTA tem mecanismo próprio (parity_map); `contract_refs` TÉO valida só shape — VISTA deve validar existência de `operation_refs`/`read_refs`/`write_refs` contra registries canônicos. NOT_APPLICABLE/DO_NOT_COPY — conteúdo pt-BR/domínio TÉO, gates TÉO-específicos, acoplamento ao `UserManualSection` do transformometro (o *padrão* de merge transfere, o código não).

### 29.3 Inventário + duplicação (veredito)

SINGLE_SOURCE/AUTHORITY preservados: roadmap README (overview humano), PLAYBOOK-EXCELENCIA (design doctrine dev), PLAYBOOK-POWER-QUERY-M (transform contract), MDD-MINHA-DELPI-DECK (guia MDD), ADRs (decisões), `presentation_ops_content.json` (execution contract + `whenToUse` por capability), `tv_data_route_overlays.json` (semântica por rota), `design_intelligence.json` (semântica por bloco), `native_screens.json`/`dashboard_slide_presets.json`/`slide_templates/` (catálogos de produto), `helpTooltips.ts` (copy UI, MFE-local correto), `data-route-nl-suggest.md`, api README.

UNCONTROLLED_DUPLICATION (drift risk real): **block_types** (5+ vocabulários: `design_intelligence.json` × `*AddElementMenuCatalog.ts`/`chartQuickLayouts.ts` × `helpTooltips` × playbook §6.2b × E1 inventory); **filter_layering** (4 fontes: directive L595 + playbooks §3.2 + helpTooltips + roadmap §18.5.1); **design_quality** (playbook §1/§6 × `visual_impact`/`slide_design`/`layout_perception` × MFE `*StyleRecipes.ts`/`comunicadoSlideThemes.ts` — sem cross-validation). Drift moderado: media limits (settings.json × directive), slide duration/section defaults (help × directives).

**EXISTING_EQUIVALENT = YES** (fontes semânticas fragmentadas existem; nenhum registry canônico unificado). **REUSE_DECISION = EXTEND** — portar o mecanismo TÉO para o bounded context próprio; reusar fontes existentes como `source_refs`, não copiar prosa.

### 29.4 Target schema (adaptado de `product_guide_v1`)

Campos: `schema`("product_guide_v1") · `id`(==filename) · `title` · `summary` · `authority`("GUIDANCE_NOT_DOMAIN_TRUTH") · `purpose` · `use_when[]` · `do_not_use_when[]` · `how_to_use[]` · `field_guidance[]{field,guidance,contract_ref?}` · `quality_rules[]` · `common_mistakes[]` · `related_topics[]` · `capability_refs[]` · `operation_refs[]` · `read_refs[]` · `write_refs[]` · `source_refs[]{ref, PROVEN|INFERRED|PROPOSED}` · `agent_guidance?`. Seções projetáveis: overview/when_to_use/how_to_use/field_guidance/quality/relationships/all.

`ui_refs` **rejeitado em V1**: não existe registry canônico de rotas/seções de UI em tv-dashboard (`routing.ts` é estático, não validável) — incluir criaria ref não-validável; Help MFE mantém navegação local.

Validação fail-closed no load (não no read): schema/authority literals, id==filename, ids únicos, `related_topics ⊆ registry`, `capability_refs ⊆ capability_surface`, `operation_refs ⊆ presentation_ops_content.json operations`, `read_refs`/`write_refs ⊆ tool/op names canônicos, `contract_refs` existência-deep (aprendizado: TÉO valida só shape — VISTA faz melhor). Ref desconhecida → erro de load/teste; tópico desconhecido → 404 tipado; seção desconhecida → 400 tipado; nunca fallback silencioso.

Versioning: `schema` literal por arquivo + `REGISTRY_VERSION` único + payload markers (`product_guide_index_v1`, `product_guide_help_v1`). Sem versão por tópico. Bump de schema só para mudança de contrato de campos; tópico novo/texto alterado = sem bump.

### 29.5 Wave 1 (evidence-based)

| Tópico | Justificativa |
|---|---|
| tv_dashboard_overview | âncora de vocabulário (playlist/slide/dados/TV) |
| playlist | conceito-mãe; 4 fontes AUDIENCE_COPY convergem |
| slide | inclui native vs custom (confusão real, presets/native_screens existem) |
| block_types | **maior UNCONTROLLED_DUPLICATION**; `design_intelligence.json` vira source_ref |
| data_sources | overlays já trazem whenToUse/params |
| data_models | DataModel vs fonte vs binding = confusão top; directive `data_model` existe |
| data_bindings | ops `bind_visual` + helpTooltips existentes |
| filters_and_layering | UNCONTROLLED (4 fontes) — registry vira projeção canônica |
| display_formats | ADR + directive; PARTIAL conhecido documentável |
| data_route_discovery | miss≠absence já documentado (data-route-nl-suggest) |
| visual_verification | ladder §27.8 — guidance estável |

**WAVE_1 = 11 tópicos.** DEFERRED: sections (fold em slide), editor (UI-local, tooltips bastam), published_templates, presentation_recipes, media, sharing_and_kiosk, MDD (doc próprio é autoridade — link via related/source_refs), history (PHASE 9). REJECTED/deferido: **design_quality** movido para WAVE_2 — fronteira com PHASE 5 (metodologia) torna o escopo ambíguo hoje.

### 29.6 Surface decision

`PRODUCT_GUIDE_SURFACE = DEDICATED_READ_TOOL` (recomendado; gate final no execution brief de PHASE 2): consumidor real existe (VISTA PRODUCT_USAGE + Portal Help), payload de tópicos não cabe no catálogo (index ~1.5KB cabe; corpos ~2-4KB/tópico não), owner claro, schema estável, precedente TÉO PROVEN. Índice compacto projetável em `get_catalog` quando a capability existir. `NEW GPT ACTION/MCP TOOL = RECOMMENDED` via capability binding único (parity_map), não como decisão final desta fase.

### 29.7 Budget / projeção

Baseline pós-P1: surface Actions 79,497B de 102,400 (headroom ~22.9KB unicode; envelopeAscii headroom ~4-5KB). Guide **index** cabe em Actions; **corpos de tópicos só on-demand** (tool/HTTP). Projeções derivadas da mesma autoridade: MCP full · Actions index+fetch · Portal `?view=help` whitelist · docs derivados. **ZERO paralelismo de fonte.**

### 29.8 Help convergence readiness

`HELP_CONVERGENCE_FEASIBILITY = PARTIAL→READY`. Blocos prontos: `createDashboardUserManual` (plugin-ui compartilhado), padrão merge+fallback TÉO, convenção `content_routes`/service, `feature-help-sync.mdc` prescreve o padrão commercial (`userManualContent` + `/help`). Gaps reais (PHASE 3, não P2): `routing.ts` sem rota `/help`; sem `userManualContent.ts`; `helpTooltips.ts` é component-scoped (precisa de mapa seção→topic-id); kiosk público precisaria de projeção sem auth (não escopo). `helpTooltips.ts` permanece autoridade local de navegação/labels — não vira fonte semântica.

### 29.9 Implementation boundary (próxima fase)

PHASE 2 runtime files: `tv_app/content/product_guides/*.json` (Wave-1), `tv_app/application/product_guide/{product_guide_schema.py, product_guide_registry.py, product_guide_service.py}`, rota help (novo `product_guide_routes.py` ou `content_routes` existente), capability binding + openapi builder **somente se Action Surface Gate passar**, `tests/test_tv_product_guide.py`, roadmap record. PHASE 3 files (depois): `/help` route + `helpGuideContent` map + api client no MFE tv-dashboard.

### 29.10 Status

**PHASE 2 = READY_FOR_EXECUTION** — owner provado, equivalentes inventariados, schema/validação/versionamento desenhados, Wave-1 evidenciada, surface decidida com gate documentado, zero drift estrutural novo (duplicações registradas para convergência futura, não para correção nesta fase). PHASE 3 permanece BLOCKED até PHASE 2 produzir registry + projeção help.

## 30. PHASE 2 — EXECUTION RECORD (TV Product Guide V1, 2026-10-09)

> Executado por `VISTA-KIC-V1-PHASE-2-TV-PRODUCT-GUIDE-EXECUTION`. IMPLEMENTATION + VALIDATION + ACTION SURFACE GATE + TESTS + ROADMAP EVIDENCE. Base efetiva: `122898a948` (origin/main). Sem commit nesta execução (working tree preservado; mudanças estrangeiras de DÉLIA/api-delpi/public-hub intocadas).

### 30.1 Implementação

| Camada | Artefato |
|---|---|
| Content registry | `tv_app/content/product_guides/*.json` — 11 tópicos Wave-1 (exatos): `tv_dashboard_overview`, `playlist`, `slide`, `block_types`, `data_sources`, `data_models`, `data_bindings`, `filters_and_layering`, `display_formats`, `data_route_discovery`, `visual_verification` |
| Application | `tv_app/application/product_guide/{product_guide_schema,product_guide_registry,product_guide_service}.py` + `__init__.py` |
| Help projection | `GET /product-guides` em `content_routes.py` (whitelist server-side; refs internas nunca saem) |
| Actions | `GET /gpt-actions/v1/product-guides` (`gpt_get_product_guide`; params bounded `topic`/`section`) |
| MCP | `get_product_guide` (TOOL_CLASS=READ; via `tool_bridge`→dispatch compartilhado) |
| Parity | `surface_parity.parity_map["gpt_get_product_guide"]="get_product_guide"` — binding único |
| OpenAPI | operação compacta em `openapi_builder.py`; artifact `docs/gpt-actions/openapi-gpt-actions.json` regenerado |
| KO | `vista_agent_intelligence.json`: `product_usage` PARTIAL→PROVEN (reads: `get_product_guide`), `PRODUCT_USAGE_GATE` atualizado, parity entry, version bump |
| Testes | `tests/test_tv_product_guide.py` (37 testes) + updates de superfície/paridade/budget |

Versões: `SCHEMA_VERSION=product_guide_v1` · `REGISTRY_VERSION=product-guide-registry-v1` · payloads `product_guide_index_v1` / `product_guide_help_v1`.

### 30.2 Validação fail-closed (load-time)

Registry rejeita: schema/authority inválidos, unknown keys, campos unbounded, id≠filename, ids duplicados, registry vazio/ausente, `related_topics`/`capability_refs`/`operation_refs`/`read_refs`/`write_refs` não-resolvidos contra `capability_surface`, `presentation_ops_content.operations` e tool/op names canônicos (providers injetáveis). `ui_refs` rejeitado em V1. Runtime: tópico desconhecido → 404 tipado (`ProductGuideNotFoundError`); seção desconhecida → 400 tipado; sem fallback.

### 30.3 Action Surface Gate — executado

| Opção | Resultado |
|---|---|
| A — só `get_catalog` | REJEITADA: envelope Actions já no teto (~100 KiB OpenAI); index mostraria tópicos sem caminho bounded para corpos → `PRODUCT_USAGE` inutilizável |
| B — `get_product_guide(topic?, section?)` | **SELECIONADA**: consumidores reais (VISTA PRODUCT_USAGE + PHASE 3 Portal Help), schema bounded, read-only, owner claro, paridade via binding único, corpos on-demand |
| C — sem superfície | REJEITADA: deixaria `product_usage=PARTIAL`, contrariando o objetivo da fase |

`PRODUCT_GUIDE_SURFACE = DEDICATED_READ_TOOL`. UMA capability: Actions 10→11 ops, MCP 10→11 tools, zero tool por tópico, zero mudança em write tools.

### 30.4 Actions budget — remediação sem aumento de cap

Descoberta: clean HEAD já estava **~193B acima** do limite (envelopeAscii 102,593 > 102,400 — regressão pré-existente marginal). Compaction honesta na projeção Actions (mesmo precedente de `fieldVocabulary` MCP-only): índice `operations` Actions mantém apenas o gate contract (`risk`/`confirmationPolicy`/`requiresPlaylist`/`requiresSlide`/`sideEffectHints`); `fields`/`requiredFields` ficam com o OpenAPI `requestBody` oneOf (documentado no serviço); `produces`/`consumes` espelham os flags requires-* → MCP-only; `allowedOps` (derivável de `operations` keys) e a entrada `product_guide` em `analyses` (`transports:["mcp"]`; Actions descobre via operationId) → MCP-only. **Resultado:** envelopeAscii 102,922→**92,544** (unicode 88,354) — headroom ~9.9KB ≥ 4KiB exigido. Cap inalterado (102,400). MCP full projection preservada; zero semântica de diretivas removida.

### 30.5 Invariantes de conteúdo

`authority=GUIDANCE_NOT_DOMAIN_TRUTH` em todos os tópicos; `display_formats` declara cobertura tipada PARTIAL; `data_route_discovery` preserva SEARCH_MISS≠ABSENCE; `visual_verification` preserva a ladder (schematic/layoutDigest≠pixel; canonical_stage=artefato do editor live; ImageContent PROVEN / host forwarding FAIL_OBSERVED / pixel inspection TEST_NOT_RUN); zero refs a surfaces aposentadas (`/data/copilot/*`); zero `ui_refs`; zero conteúdo de domínio/AuthZ/OpenAPI duplicado; semântica normalizada, não bulk-copy de docs.

### 30.6 Testes executados

`test_tv_product_guide.py` 37/37 (schema, authority, bounded fields, unknown-key, id≠filename, duplicados, registry vazio, cross-refs, help projection, KO PROVEN, parity, gate, sem dependência TÉO). Matriz de regressão: budget(8) + facade + MCP conformance + knowledge_orchestration + unified_boundary + client_migration + read/write surface + patch_service + focused_context = **261 PASS**; sweep adicional (agent_intelligence, suggest_ops, ready-slide corpus, content_routes, capabilities_route, streamable_http_wire, data_route facade, display_format) = **121 PASS**. Total **382 verde, 0 falha**.

### 30.7 Fronteiras preservadas

`PresentationMutation`/`TvPresentationWriteService`/`PlaylistAccessService`: intocados. api-delpi/OpenAPI data contracts: intocados. AuthZ: inalterada (guide descreve capability ≠ permissão; backend decide). MFE Help: intocado (PHASE 3). Sem runtime TÉO: zero imports `tm_app`; padrão portado, conteúdo/domínio não. Sem generic knowledge/RAG engine. `DOMAIN STATE > GUIDE · LIVE CONTRACT > GUIDE · OpenAPI > GUIDE · GUIDE > remembered copy` — enforced.

### 30.8 PHASE 3 readiness — gate satisfeito

registry PROVEN · topic IDs estáveis (id==filename enforced) · help-safe projection PROVEN (`GET /product-guides`, whitelist) · contrato de erro tipado (404/400) · campos semânticos estáveis (`product_guide_help_v1`). **PHASE 3: BLOCKED→READY_FOR_DIAGNOSTIC.** Residual: `design_quality` Wave-2 (fronteira PHASE 5); kiosk público precisa projeção sem-auth (fora de escopo); `ui_refs` segue adiado até existir registry canônico de UI.

**VERDICT: ACCEPT** — 30/30 acceptance criteria.

## 31. PHASE 3 — DIAGNOSTIC RECORD (Help Convergence, 2026-10-09)

> Executado por `VISTA-KIC-V1-PHASE-3-HELP-CONVERGENCE-DIAGNOSTIC`. DIAGNOSTIC/INVENTORY somente — zero código de produção, zero mudança de schema. Baseline: HEAD `912ac3ba99` == origin/main (pós-PHASE 2 commit).

### 31.1 Current Help architecture (proven)

| Surface | File | Owner | Content type | Consumers | Auth | Fallback | Status |
|---|---|---|---|---|---|---|---|
| Contextual tooltips | `src/content/helpTooltips.ts` (728 ln, 14 seções) | MFE | UI labels + hints de controle | 87 arquivos (ribbon, filmstrip, data builder, context menus, inspectors) | sessão (MFE autenticado) | n/a (estático) | PROVEN — correto como copy UI-local |
| Página Help/manual central | — | — | — | — | — | — | **MISSING** (`routing.ts` tem 8 views; nenhuma `help`) |
| `userManualContent` | — | — | — | — | — | — | **MISSING** no tv-dashboard (existe em supplies/commercial/transformometro) |
| Manual shell compartilhado | `plugins/plugin-ui/components/layout/UserManual.tsx` + `createDashboardUserManual` | plugin-ui | shell de apresentação | TÉO/commercial/supplies | — | — | REUSABLE — remote `@delpi/plugin-ui` já configurado no vite.config do tv-dashboard |
| Backend help projection | `GET /product-guides` (`content_routes.py`) | tv-dashboard-api | `product_guide_help_v1` whitelist (id/title/summary/purpose/use_when/do_not_use_when/how_to_use/field_guidance/quality_rules/common_mistakes/related_topics) | futuro MFE | `tv-dashboard.read` | 404 tipado | PROVEN (PHASE 2) |
| API client | `src/api/httpClient.ts` + `tvDashboardApi.ts` | MFE | httpGet + envelope unwrap + AbortSignal + HttpRequestError(status) | todo o MFE | Bearer via `configureHttpClient` | throw | REUSABLE — nenhum segundo HTTP layer |

### 31.2 Semantic duplication map

| Content | Atual | Target | Action |
|---|---|---|---|
| `data.catalogSearch` (rotas, chips, binding) | helpTooltips | Product Guide `data_route_discovery` | MIXED → tooltip fica UI-local; Help page deriva semântica |
| `data.sourceConfig` (camada dados sobrescreve tela/programação) | helpTooltips | `filters_and_layering` | MIXED → semântica no guide; tooltip mantém instrução de controle |
| `data.dateRangePreset` (parágrafo grande de períodos relativos) | helpTooltips | `filters_and_layering` field_guidance | MIXED → candidato a SPLIT: tooltip resume; semântica no guide |
| `data.paramExpression`, `paramGranularity`, `paramBranch` | helpTooltips | `data_bindings`/`data_sources` | MIXED → tooltip local + help semântico |
| `ribbon.playlistFilters`, `ribbon.playbackMode`, `ribbon.masterSlide` | helpTooltips | `playlist`/`slide` | MIXED → SPLIT candidato |
| ~600 tooltips de controle (format, shapes, context menus) | helpTooltips | MFE | KEEP_LOCAL (UI_LABEL_EXPLANATION) |
| `dataBuilderChatContent` | MFE | MFE | KEEP_LOCAL (microcopy de fluxo) |
| Semântica de produto em Help page | MISSING | Product Guide | DERIVE_FROM_GUIDE (novo) |

### 31.3 Section → topic map (proposto)

`HELP_SECTION_TOPICS` no futuro `src/content/helpGuideContent.ts` — seção MFE → topic ids:

| Help section | Topics | Local UI content | Status |
|---|---|---|---|
| overview | `tv_dashboard_overview` | nav entry, como abrir editor | COVERED |
| playlists | `playlist` | list/new/share UI | COVERED |
| slides | `slide` | filmstrip, duração, sections | COVERED |
| blocks | `block_types` | insert/element controls | COVERED |
| data-sources | `data_sources` | catalog picker UI | COVERED |
| data-models | `data_models` | prepare modal, inspector | COVERED |
| bindings | `data_bindings` | field linking UI | COVERED |
| filters | `filters_and_layering` | camadas na UI | COVERED |
| formats | `display_formats` | format ribbon | COVERED (PARTIAL honesto) |
| data-discovery | `data_route_discovery` | busca de rotas | COVERED (miss≠absence) |
| visual-review | `visual_verification` | preview vs TV | COVERED (ladder honesta) |

Zero seções sem tópico; zero topics orfãos na Help page. Wave-1 cobre o escopo.

### 31.4 Auth / public decision

`HELP_AUTH_MODEL = AUTHENTICATED_HELP` — `GET /product-guides` exige `tv-dashboard.read`; a Help page vive dentro do MFE autenticado (mesmo `configureHttpClient` Bearer). `PUBLIC_HELP_REQUIREMENT = NO` — public link/preview/kiosk são superfícies de exibição, não de edição; nenhuma journey comprovada exige Help pública. `KIOSK_HELP_REQUIREMENT = NO`. Nenhuma rota pública nova.

### 31.5 Fallback matrix (design)

| Estado | User outcome | Local help | Retry | Telemetria (design) |
|---|---|---|---|---|
| loading | seções mostram nota "Carregando conteúdo de ajuda…" | links/nav renderizam | automático (fetch único) | n/a |
| success | intro/bullets do guide + links locais | merge | — | n/a |
| 401/403 | nota de sessão; orientar relogin | nav local | re-fetch após login | console warn (sem dados) |
| 404 topic | seção mostra nota de configuração/drift (id não resolvido) | nav local | manual | warn com topic id — drift detection |
| 5xx/network | `HELP_UNAVAILABLE_NOTE` em seções mapeadas | nav local + tooltips continuam | botão "Tentar novamente" | warn (sem payload) |
| empty index | nota indisponível global | nav local | manual | warn |
| registry version drift | IDs testados contra index no teste do MFE | — | — | gate de teste |

Semântica **nunca** cai para prosa local duplicada — seções mapeadas mostram nota explícita de indisponibilidade (padrão TÉO provado).

### 31.6 Architecture decision

`HELP_ARCHITECTURE = CENTRAL_PAGE`. Evidência: MFE já tem help contextual coberto por 87 consumidores de `helpTooltips` (CONTEXTUAL_ONLY não agrega nada novo); falta exatamente o manual semântico central; TÉO/commercial/supplies provam o padrão `UserManual` shell + merge. Contextual entry points (links de seções) são detalhe de navegação dentro da página, não segunda arquitetura.

`HELP_ROUTE = NEW_REQUIRED` — `view: "help"` em `routing.ts` + `HelpPage.tsx` + nav entry (PlaylistsPage/library shell header é o candidato natural; decisão final no brief de execução).

### 31.7 Implementation boundary (futuro)

ALLOWED: `plugins/tv-dashboard/src/pages/HelpPage.tsx` (novo), `src/content/helpGuideContent.ts` (mapa+merge), `src/content/userManualContent.ts` (nav/links locais), `src/api/tvDashboardApi.ts` (+`fetchProductGuideHelp` usando httpClient existente), `src/routing.ts` (+view `help`), entry de navegação, testes. FORBIDDEN: backend routes/schema/topics, `helpTooltips.ts` semântica, AuthZ, public-hub, KO, tool surface, `PresentationMutation`. **BACKEND CONTRACT IMPACT = NONE.**

### 31.8 TÉO pattern assessment

REUSE_PATTERN: fetch único `?view=help`-equivalente + `indexTopicsById` + `mergeManualWithGuides` (intro/bullets do guide, links locais) + `HELP_UNAVAILABLE_NOTE` explícita + `createDashboardUserManual` shell + `HELP_SECTION_TOPICS` map. ADAPT: fetch por `GET /apps/tv-dashboard-api/product-guides` (help-safe é o default da rota VISTA, sem `?view=`); seções/títulos locais conforme UX tv-dashboard. NOT_APPLICABLE: domínio/conteúdo TÉO. DO_NOT_COPY: `UserManualSection` semantics do portal Transforma+ (padrão estrutural transfere, copy não).

### 31.9 Test strategy (futura)

mapa seção→tópico completo vs index; tópico desconhecido → nota drift; loading/success/unavailable; merge preserva links locais; sem fallback para prosa duplicada; fields internos ausentes; `registry_version` observável para provenance; deep-link `/apps/tv-dashboard/help`; contrato de envelope `ApiEnvelope`.

### 31.10 Status

**PHASE 3 = READY_FOR_EXECUTION** — HELP_PROJECTION=SUFFICIENT (whitelist cobre o contrato), AUTH=AUTHENTICATED_HELP, FALLBACK=controlado sem prosa duplicada, arquitetura=CENTRAL_PAGE com precedente interno provado, boundary pequeno e frontend-only, zero backend change.

## 32. PHASE 3 — EXECUTION RECORD (Help Convergence, 2026-10-09)

Reanchor: `HEAD == origin/main == 9dd90cdc43`. EXECUTION_DRIFT check: commits posteriores a `da79260925` não tocaram Help arch, API client, federation, routing model nem projeção help-safe → **drift = NONE**.

### 32.1 Implementation

CENTRAL_PAGE implementada conforme §31.6/§31.7 — boundary exato, frontend-only:

| File | Change |
|---|---|
| `src/api/tvDashboardApi.ts` | `fetchProductGuideHelp()` + `ProductGuideHelpTopic`/`ProductGuideHelpFieldGuidance`/`ProductGuideHelpResponse` — `httpGet` + envelope `unwrap` + `AbortSignal` via httpClient existente; rejeita `schema !== product_guide_help_v1` |
| `src/content/userManualContent.ts` | 11 seções locais (nav labels + links want/where/how/path + scopeNote). Zero prosa semântica de produto |
| `src/content/helpGuideContent.ts` | `HELP_SECTION_TOPICS` (11×11 exato, §31.3), `indexTopicsById`, `missingConfiguredTopics` (drift gate), `sectionIdForTopic`, `relatedSectionsFor`, `mergeManualWithGuides` (intro/bullets do guide, bullets locais anexados, links nunca substituídos), notas explícitas LOADING/UNAVAILABLE/AUTH/CONFIG/DRIFT |
| `src/pages/HelpPage.tsx` | `TvLibraryPageLayout` + `TvPageHeader` (nav=Voltar) + `createDashboardUserManual({prefix:"td"})` + `TvSectionCard`; fetch único on-mount com `AbortController`; retry; «Veja também» via related_topics |
| `src/routing.ts` | `view: "help"` + `helpPath()` (`/apps/tv-dashboard/help`); `"help"` adicionado às exclusões do legacy `/:id` match (sem colisão com playlist id) |
| `src/App.tsx` | `case "help"` + `isLibraryShell` inclui help + `onOpenHelp` → `helpPath()` |
| `src/pages/PlaylistsPage.tsx` | prop `onOpenHelp` + `TvNavigationCard` «Ajuda» (BookOpen) na actions grid da home |

### 32.2 Route / nav

`HELP_ROUTE = /apps/tv-dashboard/help` (view `help`, deep-link provado em `routing.test.ts`); `NAV_ENTRY = PlaylistsPage.actions «Ajuda»` (mesmo padrão `TvNavigationCard` de «Biblioteca de templates»). Sem rota pública; preview/share/kiosk intocados.

### 32.3 Fetch / cache / merge

`FETCH = single projection GET /apps/tv-dashboard-api/product-guides` (sem `?view=` — help-safe é default da rota) via `fetchProductGuideHelp` → envelope `unwrap`. `CACHE = component lifecycle` (AbortController; fetch único por mount, retry manual) — sem novo cache service. `MERGE = server intro(summary+purpose)/bullets(how_to_use+quality_rules) + bullets locais anexados + links locais intactos`; tópico ausente → `HELP_DRIFT_NOTE` na seção; `related_topics` → navegação «Veja também» entre seções mapeadas.

### 32.4 Error semantics (conforme §31.5)

loading (`HELP_LOADING_NOTE`, links visíveis) · success (merge) · 401/403 (`HELP_AUTH_NOTE`, HttpRequestError.status) · 404/422 (`HELP_CONFIG_NOTE`) · 5xx/network (`HELP_UNAVAILABLE_NOTE` + retry) · empty index (`HELP_CONFIG_NOTE`, não-sucesso) · missing configured topic (`HELP_DRIFT_NOTE` por seção + `missingConfiguredTopics` gate de teste). **Zero stale semantic fallback.**

### 32.5 Tests

| Suite | Result |
|---|---|
| `tvDashboardApi.productGuide.test.ts` (7) | PASS — URL/envelope/GET-sem-body, whitelist help-safe, AbortSignal, 401/403/404/5xx/network, schema mismatch |
| `helpGuideContent.test.ts` (10) | PASS — mapa 11×11 exato, drift detection, loading/unavailable/auth note, merge semântica+local, drift por seção, related→seções |
| `routing.test.ts` (+3) | PASS — deep-link `/help`, sem colisão legacy, rotas existentes intactas |
| `HelpPage.test.tsx` (6) | PASS — loading, render merge, 5xx+retry+links locais, 401, 404, empty index |
| `App.smoke.test.tsx` (2) | PASS — stale-mock repair (`listMFunctions`, `listPlaylistMedia`, `fetchProductGuideHelp`) + label de aba atual («Inserir», «Página inicial» renomeada no refactor do editor) |

### 32.6 Build / typecheck / lint

`vite build` PASS (remote `@delpi/plugin-ui` resolve em build real; UserManual shell provado) · `check:css-scope` PASS · vitest MFE 1379/1386 pass — **7 falhas pré-existentes** em área comunicado/deck WIP do usuário (`applySlideTheme`, `DeckRevisionHistoryPanel`, `deckRibbonCollapseIcons`, `FormatRibbonFrameSection`, `PlaylistPreviewPage.loading`, `comunicadoBlockLabels`, `comunicadoSameSize`), zero relacionadas ao diff · `tsc -p tsconfig.build.json` **baseline RED** (~110 erros pré-existentes `src/utils/*`+`tv-dashboard-presentation`, verificado com os arquivos modificados stashados: falha existe sem o diff; **zero erros nos arquivos do diff**) · eslint nos arquivos do diff: 0 erros novos (baseline já tinha erros em `App.tsx`/`PlaylistsPage.tsx`).

### 32.7 Residual search

Sem prosa do guide no MFE (userManualContent = nav/links apenas) · sem campos internos (`capability_refs`/`operation_refs`/`agent_guidance`/`ui_refs`) · sem import TÉO · sem segundo HTTP/auth client · sem rota pública · sem dependência nova · `helpTooltips.ts` intocado (87 consumers operacionais) · `dataBuilderChatContent` intocado.

### 32.8 Invariants

`DISPLAY_FORMAT PARTIAL`, `SEARCH MISS IS_NOT ABSENCE`, `schematic != pixels`/`ImageContent != inspeção visual` — preservados (semântica vem do guide server-side, não de paráfrase local). Backend/Product Guide schema/registry/topics/rotas: **intocados**. AuthZ/MCP/GPT Actions/KO/`PresentationMutation`/public-hub: **intocados**. Semântica de Design Methodology: não absorvida (PHASE 5). `registry_version` flui no payload (provenance), não renderizado (ruído técnico).

### 32.9 Status

**PHASE 3 = DONE** — CENTRAL HELP = LIVE, PRODUCT GUIDE SEMANTIC SOURCE = PROVEN, SECTION→TOPIC MAP = PROVEN (teste), HELP-SAFE FETCH = PROVEN, LOCAL UI HELP = PRESERVED, STALE SEMANTIC FALLBACK = ABSENT, BACKEND/PUBLIC/SECURITY CHANGES = NONE. Residual: typecheck baseline RED pré-existente (refactor comunicado do usuário em voo — não do escopo); 7 falhas de teste pré-existentes idem; tooltip MIXED splits de §31.2 adiados (rule: central help first, cleanup mínimo/zero).

## 33. PHASE 3 — POST-DEPLOY LIVE SMOKE (2026-10-09)

Reanchor: `HEAD == origin/main == 32661f98dd` (inclui `e5c794e718` P3). Stack dev completo via gateway :80.

### 33.1 Evidence

| Check | Evidence | Result |
|---|---|---|
| Endpoint auth | `GET /apps/tv-dashboard-api/product-guides` sem token → `401 {"detail":"Unauthorized"}` | PASS — AUTHENTICATED_HELP enforced |
| Endpoint autenticado | Bearer dev (`infra/scripts/get-dev-token.sh`) → `product_guide_help_v1`, `registry_version=product-guide-registry-v1` | PASS |
| Topic coverage live | 11/11 ids == `HELP_SECTION_TOPICS` exatamente (1:1) | PASS |
| Whitelist help-safe | zero `capability_refs`/`operation_refs`/`read_refs`/`write_refs`/`source_refs`/`agent_guidance`/`ui_refs` no payload live | PASS |
| Invariants live | display_formats contém «parcial»; data_route_discovery contém miss≠absence; visual_verification contém escala pixel | PASS |
| MFE delivery | container `delpi-tv-dashboard` rebuilt from HEAD (`vite build`); bundle contém `tv-dashboard/help` | PASS — DELIVERY real |
| remoteEntry | `GET /apps/tv-dashboard/remoteEntry.js` → 200 via gateway | PASS — federation remote live |
| Deep link | `GET /apps/tv-dashboard/help` → 200 (Portal SPA shell → MFE remote) | PASS |
| Manifest | rota única `/apps/tv-dashboard` + `tv-dashboard.read`; help é subrota interna do MFE (sem rota pública nova) | PASS |
| Tooltips | `helpTooltips.ts` intocado; suites existentes verdes (§32.6) | PASS |
| Fallback auth path | standalone MFE sem `getAccessToken` → fetch 401 → `HELP_AUTH_NOTE` (design + teste; browser aberto para confirmação visual) | PASS (headless) / PENDING captura |
| Browser DOM | browser_preview aberto em `/apps/tv-dashboard` e `/apps/tv-dashboard/help` — captura do usuário pendente | PENDING |

### 33.2 Status

`PHASE 3 = DONE + RUNTIME VERIFIED (headless)` — API auth/projection/topic-coverage/whitelist/invariants PROVEN live; delivery e remoteEntry PROVEN; DOM autenticado render = evidência visual pendente da captura do usuário (preview aberto). Nenhum defect reproduzido; zero patch nesta etapa.

## 34. PHASE 4 — EDITOR GROUNDING V2 DIAGNOSTIC (2026-10-09)

Mode: DIAGNOSTIC only. Revalidado em `32661f98dd`.

### 34.1 Current context contract (PROVEN)

```
MFE editor ──WS selection_update (canEdit + clientId match)──▶
EditorFocusStore.record(user_id, playlist_id, slide_id,
                        selected_ids≤100 dedup, client_id)
  row = {playlistId, slideId, selectedIds, clientId, updatedAt, _mono}
  TTL: ≤90s fresh · ≤180s stale=true · >180s evicted (lazy)
```

Consumers:
- `list_playlists` → `editorFocus` prepend (continuous_review / «esta programação»)
- `get_playlist_context` (MCP + Actions — mesmo dispatch, paridade automática) → `editorFocus{slideId, selectedIds, updatedAt, stale, selectedDataSourceId?}` + `focusedBinding` (single-selection only: `{blockId, modelId, dataSourceId, bindingField}`) + `blockIndex{slideId, revision, items[], cursor}` + `objectMatches`
- `blockIndex` item = `project_block_index_item`: `{id,type,frame,zIndex,role,groupId,contentPreview,label,dataSourceId,modelId,bindingField,hasDataBinding,formatBindings[]}` — persisted state only, nunca id inventado
- rendered-preview upload → provenance `editor_live` binds fresh focus + clientId

### 34.2 Object resolution pipeline (PROVEN gap)

`suggest_change` resolve alvos **somente** de `host_context` do caller (`selectedBlockIds`, `selectedBlockId`, `focusBlockId`, `focusBlockType`, `selectedDataSourceId`, `focusedBinding`, `focusedModel`, `blockIndex`, `dataSources`, `dataModels`, `nativeConfig`). O server-side `EditorFocusStore` **não é consultado** no suggest — VISTA externa precisa ler `editorFocus.selectedIds` do context e re-ferry os ids manualmente.

### 34.3 Stale/fresh semantics (today)

`stale: bool` binário — sem vocabulário tipado. Seleção de bloco deletado → `focusedBinding` retorna `None` silenciosamente; multi-seleção → `focusedBinding` `None` silenciosamente; `selectedIds` são strings nuas (VISTA faz join manual com blockIndex).

### 34.4 Gap map

| Gap | Hoje | Target |
|---|---|---|
| selectedIds bare | strings sem tipo/summary | `selectedObjects[]` compact rows (reuse `project_block_index_item`) |
| estado | `stale` bool | `selectionState`: ACTIVE/STALE/ABSENT/AMBIGUOUS |
| bloco deletado | silent | `exists:false` + `missingIds[]` |
| multi-seleção | `focusedBinding=None` silent | AMBIGUOUS unless op multi-target (`blockIds`) |
| suggest grounding | host_context only | fallback merge do focus fresco do servidor |
| slideId drift | focus.slideId pode divergir de detail | resolve vs detail_slide authoritative |

### 34.5 Target state vocabulary

```
ACTIVE     = focus fresco (≤TTL) ∧ ≥1 selectedId resolvido em bloco persistido
STALE      = focus existe mas age>TTL (window grace) → RE-RESOLVE antes de usar
ABSENT     = sem focus, sem selectedIds, ou ids todos fora do slide focado
AMBIGUOUS  = >1 selectedId resolvido ∧ op não multi-target declarada
```

Regras determinísticas — derivadas de (stale flag, resolução vs blocos persistidos, cardinalidade). Nenhum estado improvisado.

### 34.6 Selected object projection

`editorFocus.selectedObjects[]` = para cada `selectedId`, `project_block_index_item`-equivalente **resolvido do `nativeConfig` persistido do detail_slide** + `exists: bool`. Fields: `id, type, contentPreview?, frame?, role?, dataSourceId?, modelId?, bindingField?, formatBindings?` — mesmo shape do blockIndex item (nenhum field novo inventado). Deletados → `missingIds[]` explícito para clareza.

### 34.7 Payload analysis

Seleções reais ≪ 100; compact rows ≈ 200–400 B cada → orçamento compatível com Actions 100 KiB (`fit_editor_focus_block_index` já existe como pattern de shrink se necessário). Sem duplicação de block state completo — projection compacta compartilhada com blockIndex.

### 34.8 Domain read relationship

`editor_context` = grounding/navegação (hint + resolved compact). Nunca autoridade: mutação sempre re-lê estado canônico via domain read; AuthZ inalterada (focus nunca concede capacidade). `preview != commit` preservado.

### 34.9 Ambiguity rules

- 1 selectedId resolvido → target claro.
- N>1 resolvidos + op com `blockIds` (ex.: duplicar/alinhar) → multi-target explícito.
- N>1 + op single-target → AMBIGUOUS → clarification (não escolher arbitrariamente).
- ids ausentes do slide → `missingIds` + se nenhum resolve → ABSENT.
- slideId do focus ≠ slideId do detail → re-resolve contra detail_slide (persistido vence).

### 34.10 CREATE vs ALTER benefit

«aumente esse título» → `editorFocus.selectedObjects` fornece `{id,type:heading}` → suggest recebe `selectedBlockId` resolvido → ALTER_EXISTING ancorado, eliminando ghost-create e ferry manual de ids. Anti-ghost rule ganha alvo confiável.

### 34.11 Knowledge orchestration relationship

Nenhuma fonte nova de conhecimento — `editor_context` já é family de orquestração; a extensão enriquece a mesma projeção. KO inalterada.

### 34.12 Security

Focus é do próprio `user_id` autenticado (store key), alimentado apenas por WS `canEdit` com clientId match — sem leak cross-user. `selectedObjects` revela dados do slide que o usuário já pode ler (mesma `tv-dashboard.read`). Nenhum permission broadening.

### 34.13 Test plan

ACTIVE/STALE/ABSENT/AMBIGUOUS estados · deleted block → missingIds · slide changed → re-resolve · heading/text/chart/table/DataModel-bound selection · multi-target op com blockIds · single-target com multi-selection → clarification · focus merge em suggest_change quando host_context omite seleção · host_context explícito prevalece sobre focus · stale focus não autoriza · payload budget · paridade MCP↔Actions automática.

### 34.14 Eval plan (link §35)

Fixtures determinísticas: single-selected heading/text/chart/table, stale focus, deleted block, multi-selection compatible/incompatible, slide drift. Dimensões: OBJECT_GROUNDING, TARGET_RESOLUTION, CREATE_VS_ALTER, CLARIFICATION_CORRECTNESS. Baseline: NOT_MEASURED (nova métrica).

### 34.15 Implementation boundary

ALLOWED: `response_compact.py` (+`selectedObjects`/`selectionState`/`missingIds` em `editorFocus`), `dispatch_service.get_playlist_context` (resolver vs detail_slide), `dispatch_service.suggest_change` ou planner (merge fallback focus→host_context), testes. FORBIDDEN: novo store, novo endpoint/tool/action, AuthZ, `PresentationMutation`, duplicar block state completo, frontend como autoridade.

`EXISTING_EQUIVALENT = YES` · `REUSE_DECISION = EXTEND` (mesma projeção, mesmo store, item shape reutilizado).

**PHASE 4 = READY_FOR_EXECUTION** — extensão bounded provada: projection + merge fallback, ambos transports automáticos, zero authority nova.

## 35. PHASE 7 — EVAL + TELEMETRY V2 DIAGNOSTIC (2026-10-09)

Mode: DIAGNOSTIC/measurement design only. Nenhuma implementação de telemetria nesta etapa.

### 35.1 Current measurement inventory

- `presentation_mutation_telemetry.py`: contadores in-process (`preview_ok/rejected`, `apply_ok/rejected`, `op_rejected`) + deque 500 eventos — **internal only**, sem rota de exposição (única rota `/copilot/telemetry` é retired stub).
- Corpus precedent: `test_vista_ready_slide_corpus_gate.py` — fixture gate já existe.
- 156 arquivos de teste = contract/regression coverage PROVEN.
- Cognitive quality metrics = NOT_MEASURED (confirmado — nenhum scorer/eval de qualidade existe).

### 35.2 Metric catalog (classificação)

| Dimensão | Classificação | Instrumento |
|---|---|---|
| OBJECT_GROUNDING | NEEDS_FIXTURE | corpus §35.3 + assertion em selectionState |
| CREATE_VS_ALTER | NEEDS_FIXTURE | corpus com intent anotado |
| CLARIFICATION_CORRECTNESS | NEEDS_FIXTURE | corpus + clarificationKey esperado |
| TARGET_RESOLUTION | NEEDS_FIXTURE | corpus single/multi/stale/absent |
| DATA_ROUTE_RETRIEVAL | MEASURABLE_NOW (parcial) | testes discovery + fixture top-k |
| DATA_DIAGNOSIS | NEEDS_FIXTURE | corpus data-bound |
| VISUAL_SELECTION | NEEDS_HUMAN_RUBRIC | rubric + fixtures |
| FILTER_LAYERING | MEASURABLE_NOW (parcial) | testes existentes + fixture |
| DISPLAY_FORMAT_SELECTION | MEASURABLE_NOW (parcial) | corpus format |
| TYPED_OP_VALIDITY | MEASURABLE_NOW | schema validation já testada |
| PROPOSAL_VALIDITY | MEASURABLE_NOW | prepare/act tests |
| WRITE_SAFETY | MEASURABLE_NOW | governed write tests |
| VERIFY_OUTCOME | NEEDS_TELEMETRY | evento OUTCOME_NOT_VERIFIED |
| USER_CORRECTION | NEEDS_TELEMETRY | correction event (definir) |
| TRANSPORT_PARITY | MEASURABLE_NOW | parity suite existente |

### 35.3 Corpus plan

Fixtures determinísticas (mesmo padrão ready-slide gate): `tests/eval/grounding/*.json` + runner — intents: create-vs-alter, seleção ambígua/stale/multi/ausente, heading/text/chart/table/DataModel-bound, route miss, route ambiguity, filter layering, visual recommendation, display format, verify outcome. Frozen baseline corpus antes de medir deltas.

### 35.4 Telemetry event model (design)

Estender o padrão `presentation_mutation_telemetry` (in-process counters + bounded deque) — nunca generic telemetry service. Campos seguros: `intentFamily`, `matchedCapabilityKeys[]`, `resolutionStatus` (ACTIVE/STALE/ABSENT/AMBIGUOUS), `clarificationKey`, `candidateCount`, `selectedObjectType`, `prepareRejectionFamily`, `outcomeNotVerified`, `correctionKind`, `visualEvidenceState`. FORBIDDEN: JWT, secrets, prompt raw, business payload, private rows.

### 35.5 Privacy / sampling / retention

In-memory only (deque maxlen, mesmo padrão mutation telemetry); sem persistência, sem rota pública; opt-in debug snapshot interno se necessário. Retention = process lifetime. Sem dados de usuário identificável além de enums/keys.

### 35.6 Dashboard/report plan

Sprint-report manual via snapshot + corpus runner output; nenhum dashboard novo nesta fase.

### 35.7 Per-phase measurement plans

P4: corpus grounding + `resolutionStatus` telemetry field. P5: rubric visual_choice + corpus design intents. P6: route top-k + false-absence + owner classification fixtures.

### 35.8 Implementation boundary

Diagnostic only. Execução de telemetry/corpus requer promotion explícita do P7 para execution com boundary próprio.

**PHASE 7 diagnostic = DONE (measurement architecture proven).** BASELINE = NOT_MEASURED — nenhuma métrica cognitiva existia; nada foi inventado como score.
