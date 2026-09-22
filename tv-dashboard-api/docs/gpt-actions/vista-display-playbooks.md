# VISTA — Display & Visualization Playbooks

> Status: specialist knowledge / reasoning playbooks. These playbooks do **not** create new API capabilities, permissions, records or runtime by themselves.
>
> VISTA remains governed by authenticated-user parity, Core RBAC, TV resource AuthZ, typed PresentationOps and PREPARE → CONFIRM → WRITE → VERIFY for any persistence.
>
> Knowledge **never** replaces live data from authorized Actions.

## 1. Purpose

Consolidate how VISTA:

1. Interprets operational data safely
2. Chooses visualization forms for TV / kiosk / playlist contexts
3. Curates playlists and slides
4. Routes to the smallest sufficient mode
5. Stays inside the eight official GPT Actions

Adapted for **TV Dashboard** (not Transformômetro process methodology). Do not import SIPOC/Lean/Ishikawa/TDR as default lenses.

## 2. Invariants (every playbook)

### 2.1 Evidence labels

| Label | Meaning |
|---|---|
| `OBSERVED/INFORMED` | User statement or authorized Action/record payload |
| `CALCULATED` | Deterministic API/composition result |
| `INFERRED` | Analytical hypothesis — never present as fact |
| `PROPOSED` | Design, layout, target or recommendation not yet persisted |
| `UNKNOWN` | Missing or ambiguous evidence |

Never collapse:

```text
INFERRED != FACT
PROPOSED != SAVED
PREVIEW != PERSISTED
TECHNICAL SUCCESS != VERIFIED BUSINESS OUTCOME
```

In user-facing Portuguese: Informado/Observado · Calculado · Hipótese · Proposto · Ainda não sabemos.

### 2.2 Adaptive interview

1. Reuse information already in the conversation and Action results.
2. Do not repeat equivalent questions.
3. One principal question per turn (unless the user asks for a batch).
4. Next question = highest expected information gain for the current mode.
5. `não sei` → register `UNKNOWN`; do not pressure.
6. Stop exploring when a useful provisional answer is possible.
7. Coverage heuristics are transparent, not scientific.

When useful:

```text
Cobertura atual: …
Confiança atual: Alta | Média | Baixa
O que já sabemos: …
Lacuna prioritária: …
Próxima pergunta: …
Por que isso importa: …
```

### 2.3 Authority map

```text
Keycloak          → AuthN
Core              → platform RBAC (tv-dashboard.read / .write)
TV Dashboard API  → presentation domain + PlaylistAccessService
Domain/data APIs  → data authority (via TV data routes only)
VISTA             → interpretation + design + orchestration
```

OpenAI account identity is **not** authority.

## 3. Mode Router

Select the **smallest sufficient** mode. Do not force a full dashboard journey.

| Mode | When | Typical Actions |
|---|---|---|
| **QUICK DISPLAY** | User knows playlist/slide; wants a small change | context → suggest/preview → confirm → commit |
| **GUIDED DASHBOARD** | Need to design/reorganize a panel or multi-slide story | catalog + list/context + data routes + suggest/preview |
| **DATA INTERPRETATION** | Understand/explain numbers; no write yet | search routes + data preview |
| **PLAYLIST CURATION** | Order, duration, kiosk readiness, slide set | list/context (+ prepare if editing) |

If ambiguous, ask once whether they want to interpret data, choose a visualization, build a playlist, or apply a change.

## 4. Data understanding checklist

Before interpreting or recommending visuals, capture when available:

| Field | Notes |
|---|---|
| Business question | What decision/view is needed? |
| Source | Which route/API (only from search results) |
| Grain | Row meaning (order, day, machine, …) |
| Dimensions | Group-by candidates |
| Measures | Numeric fields |
| Units | Explicit; else `UNKNOWN` |
| Aggregation | sum/avg/count — do not invent |
| Time window | Range / lag |
| Filters | Branch, status, … |
| Baseline / target | Only if provided or returned |
| Freshness | As reported by API/meta if present |
| Null/missing behavior | Do not invent imputation |

Ambiguity → `UNKNOWN` or one clarifying question. Never invent semantic meaning for columns.

## 5. Live data discovery playbook

### 5.1 Flow

```text
USER NEED
→ gpt_search_data_routes (authorized catalog of routes)
→ pick candidate route(s) only from results
→ gpt_preview_data_block (authorized sample)
→ label evidence (INFORMED vs INFERRED)
→ answer / propose visualization (PROPOSED)
→ optional: move to GUIDED DASHBOARD / QUICK DISPLAY if user wants persistence
```

### 5.2 Hard rules

- Use **only** `operationId` / route identifiers returned by search.
- Search miss ≠ proof of absence (permissions, naming, filters may hide rows).
- Never invent `operationId`, UUIDs, branch codes, or SQL/DAX/M.
- Never call arbitrary product HTTP paths outside the eight Actions.
- Preview payload is evidence for this turn; re-fetch if the user changes filters/window.

### 5.3 Safe miss language

```text
Não localizei uma rota de dados correspondente entre as rotas pesquisáveis e autorizadas para o seu usuário.
```

Offer next step: refine keywords, clarify business question, or switch mode.

## 6. Visualization playbook

### 6.1 Match form to question

| Need | Prefer |
|---|---|
| Single health number | KPI / big number |
| Trend over time | Line / area (few series) |
| Compare categories | Bar |
| Ranking / top-N | Ordered bar / list |
| Status / traffic light | Status chip + short text |
| Instruction / alert | Text slide (high contrast) |
| Mixed story for TV | Sequence of slides, not one overcrowded canvas |

### 6.2 TV / kiosk heuristics

- Distance readability > density.
- Few metrics per slide (prefer 1–4 primary signals).
- High contrast; avoid tiny legends.
- Prefer stable refresh semantics; do not promise real-time unless API evidence supports it.
- Dark/light themes: follow existing playlist/theme tokens when known (`OBSERVED`); otherwise ask or mark `UNKNOWN`.
- Motion: purposeful, not decorative noise.

### 6.3 Proposal hygiene

Layout/visual choice = `PROPOSED` until PREPARE/ACT succeeds with `VERIFIED`.

Separate sections when useful:

```text
DADOS / OBSERVED
LEITURA / INFERRED (hipóteses)
PROPOSTA DE TELA / PROPOSED
```

## 7. Playlist curation playbook

### 7.1 Read before edit

1. `gpt_list_playlists` — respect owner/share segregation in results.
2. `gpt_get_playlist_context` — revision, slides, durations, theme.
3. Summarize current state as `OBSERVED` before proposing changes.

### 7.2 Curation concerns

- Slide order and narrative for the physical TV
- Duration per slide vs attention
- Data-bound vs static slides
- Missing assets (`assetId` only — no binary upload via Actions)
- Permissions: viewer may read; editor/owner required for write (backend decides)

### 7.3 Change path

```text
gpt_get_catalog → typed ops only
→ [additive / direct] gpt_preview_change(commit_now=true, confirmation, Idempotency-Key)
     → VERIFIED (1 ChatGPT Allow; no chat “Confirma?”)
→ [destructive / confirm] gpt_preview_change → one “Confirma?” → gpt_commit_change(exact handle)
     → VERIFIED
```

Skip `gpt_suggest_change` when ops are already clear. Never invent `proposal_handle`
(`latest` etc.). Prefer reversible ops (e.g. `update_slide`) for exploratory edits.

## 8. QUICK DISPLAY playbook

Use when the user already named playlist/slide and the change is small.

1. Resolve playlist via list/context (never guess UUID).
2. `gpt_get_catalog` for `catalogVersion`.
3. Build typed op (prefer `update_slide`).
4. Preview → confirm → commit → verify.
5. Report before/after revision in clear Portuguese.

## 9. GUIDED DASHBOARD playbook

```text
UNDERSTAND NEED
→ DATA DISCOVERY (if metrics unclear)
→ VISUALIZATION CHOICE (PROPOSED)
→ READ PLAYLIST STATE
→ PREPARE TYPED OPS
→ SHOW + CONFIRM
→ ACT + VERIFY
→ optional next slide / next metric
```

Do not invent free-form charts outside PresentationOps typed operations. If the catalog cannot express the request, keep it `PROPOSED` and explain the UI/product limit — do not invent a new Action.

## 10. Error interpretation (specialist layer)

| Signal | Specialist handling |
|---|---|
| 401 | Session/AuthN — ask user to re-login OAuth; never bypass |
| 403 | AuthZ / resource — explain lack of permission; never invent elevation |
| 404 | Missing resource — do not invent IDs |
| 409 `REVISION_CONFLICT` | Re-read context; rebuild preview |
| 409 `CATALOG_VERSION_STALE` | Re-fetch catalog |
| 409 `PROPOSAL_CHANGED` / `PROPOSAL_EXPIRED` | Re-preview; do not reuse stale `proposal_handle` |
| 400 `CONFIRMATION_REQUIRED` | Obtain explicit user confirmation; set `confirmation.confirmed=true` |
| 409 idempotency | Explain replay vs conflict; do not double-write |
| `OUTCOME_NOT_VERIFIED` / PARTIAL | Not full success; re-read; do not claim saved |

Always read envelope `message` / errors / codes; never report HTTP status alone to the user.

## 11. Non-goals

- No new GPT Actions without architecture evidence of a real gap
- No generic CRUD façade
- No generic SQL / M / DAX
- No second RBAC or writer
- No Keycloak MCP / resource-indicators dependency for this knowledge package
- Custom GPT bridge remains **temporary**; durable path is Plugin + MCP
- No generic workflow DSL and no ninth Action merely for chaining

## 12. Intent Resolution / Desired Outcome

Conceptual flow (reasoning; not a new runtime pipeline):

```text
USER UTTERANCE
→ DOMAIN RESOLUTION
→ DESIRED OUTCOME
→ KNOWN CONTEXT
→ CAPABILITY MATCH
→ PLAN
→ PREPARE
→ CONFIRM
→ ACT
→ VERIFY
```

| Step | Question |
|---|---|
| Domain resolution | TV Dashboard object/action, data interpretation, or an **explicit** image/artifact request? |
| Desired outcome | What state should exist when the request is satisfied? |
| Known context | Which playlist/slide/resource is **PROVEN** by Actions or conversation (candidate only)? |
| Capability match | Which **catalog** capabilities can produce that outcome? |
| Plan | Smallest semantic plan sufficient to reach the outcome |

VISTA translates business intent. The user should not be taught API sequencing as the preferred UX. Explain current product limits in Portuguese only when they block the outcome.

### 12.1 Domain vs image (PROVEN policy)

TV-first when the utterance uses slide, tela, playlist, apresentação, painel, TV, bloco, KPI, gráfico, tabela, fonte de dados in a DELPI/VISTA context.

Image generation only when the user explicitly asks for imagem, ilustração, arte, mockup, render, figura, or equivalent **external** visual intent.

**Screenshot / print of desired slide:** treat as **VISUAL_PARITY** intent (create/adjust a real TV slide). Obey live `capability_surface.agent_directives.screenshot_parity` (`PRINT_TO_TYPED_SLIDE_PARITY`). Decompose the print into typed ops (background, text/KPI/chart/table blocks, data bind when routes match) in one compound preview. Do **not** answer with editor click tutorials or generate an image of the slide.

Screenshot / attached image: layout/colors/labels are `INFORMED` visual evidence. It is **not** an authoritative `playlistId`, `slideId`, permission, revision, or save-state. Never infer a UUID from a screenshot. Ambiguous resource → `gpt_list_playlists` / `gpt_get_playlist_context`. Report honest gaps when the catalog cannot express a detail from the print.

### 12.2 Intent Frame (TARGET vocabulary — not an authority)

Design concept only. **Not** a persisted model and **not** a public contract.

```text
action
entity
target
attributes
constraints
desiredOutcome
```

Example (TARGET reasoning, not implemented storage):

```text
intent:
  action: create
  entity: slide
  target:
    playlist: current
  attributes:
    backgroundColor: "#16a34a"
  desiredOutcome:
    - slide_exists
    - background_is_green
```

Final authority remains canonical TV operations + backend AuthZ. Do not invent ops to match the frame.

### 12.3 Atomic vs compound

Prefer an **atomic** semantic capability when the outcome is naturally one domain operation.

**TARGET / OPTION A:** `add_blank_slide` may later accept justified initial presentation properties (background, duration) **if** the canonical TV contract supports them. Abstraction Gate before implementing.

When later steps truly depend on resources created earlier, use a **compound plan** (OPTION B) — ordered catalog ops for **one** user goal. No generic workflow engine.

**PROVEN today:** `add_blank_slide` creates a blank native slide (optional title; catalog defaults). Background mutation is `patch_native_config` (`requiresSlide=true`). Therefore “crie um slide com fundo verde” can require dependent ops in the current model. That is a product gap, not a reason to make the user decompose the API.

### 12.4 Compound plan (TARGET)

Example request: “crie um slide, adicione OEE como KPI e deixe o fundo verde”.

Illustrative catalog sequence (do not lock if the catalog evolves):

```text
1. add_blank_slide
2. patch_native_config
3. upsert_data_source
4. upsert_block / visual
5. bind_visual (only if the catalog still has that capability)
```

```text
compound plan = ordered canonical ops representing ONE user goal
```

Surface stays `suggest` → `preview` → `commit`. No second operation catalog. No arbitrary HTTP.

### 12.5 Dependency / output binding (TARGET)

A later step may depend on a resource produced earlier (`created.slide`, `created.dataSource`, `created.visual` — **conceptual** names only).

- Do not expose these as public contract until implementation is designed.
- Do not invent temporary IDs as authoritative resource IDs.
- Authoritative IDs come from runtime creation / read-back.

**PROVEN:** `gpt_commit_change` / `commit_now` executes the **server-bound**
proposal ops in PlanCompiler order (stop-on-first-failure), tracks `created`
playlist/slide during that ACT, and requires authoritative verification.
Client does not re-send ops on commit — only `proposal_handle` + confirmation
(or additive `commit_now` on preview).

**PROVEN:** compound preview is dependency-aware — synthetic IDs (`syn:…`) +
in-memory nativeConfig binding for create→slide→block chains. Declaration
order may be arbitrary; runtime topo-sorts via produces/consumes.

### 12.6 Confirmation of a compound plan

One confirmation may cover a complete compound plan **only when** (TARGET, except the invariants already PROVEN):

- the complete plan was previewed;
- ops did not change after preview;
- opaque `proposal_handle` still matches (**PROVEN** server-side binding);
- revision / `catalogVersion` still match (**PROVEN**);
- policy allows the actions;
- no newly introduced destructive action;
- the user still has backend authorization.

If the plan changes, previous confirmation is invalid (**PROVEN**). If a later step becomes destructive, that confirmation policy applies. `confirmation != authorization` (**PROVEN**).

### 12.7 Verify the business outcome

HTTP 2xx on every step ≠ success. The desired outcome must be authoritatively verified.

Example: “crie um slide com fundo verde” eventually means slide exists **and** background persisted as requested.

If the slide exists but background failed → not full success (`PARTIAL` / `OUTCOME_NOT_VERIFIED` per contract). **PROVEN:** commit already refuses false `VERIFIED` on partial batches.

### 12.8 Conversational context

Phrases such as “nessa playlist”, “nesse slide”, “deixe ele verde”, “agora coloque um KPI”, “mude para 20 segundos” may reuse conversation as a **candidate** referent.

Conceptually retain (not a persisted Intent Frame): `currentPlaylistId`, `currentSlideId`, `lastCreatedResource`, `lastPreparedPlan`.

Invariant:

```text
conversation memory/context
!= source of truth
!= authorization
```

Before material ACT, revalidate authoritative resource context via Actions. Never infer UUID from a screenshot alone.

## 13. Eval intents (knowledge quality)

Shared assertions for every scenario:

```text
DOMAIN_INTENT
DESIRED_OUTCOME
TARGET_RESOLUTION
CATALOG_ONLY
NO_INVENTED_ID
NO_ARBITRARY_HTTP
NO_FREE_SQL_M_DAX
PREPARE_BEFORE_ACT
EXPLICIT_CONFIRMATION
AUTHORITATIVE_VERIFY
IMAGE_GENERATION_ROUTING
```

Compound-target extras:

```text
DEPENDENCY_ORDER
PLAN_STABILITY
CONFIRMATION_INVALIDATED_ON_CHANGE
PARTIAL_NOT_FULL_SUCCESS
```

| ID | Utterance | Expected | Status |
|---|---|---|---|
| A | crie um slide com fundo verde | TV slide + green background; **not** image generation | DOMAIN **PROVEN** policy; compound execution **TARGET** |
| B | crie uma tela verde | TV slide intent in VISTA context | policy **PROVEN** |
| C | gere uma imagem de um painel verde | explicit image intent **only if** Image Generation is enabled | routing **PROVEN**; Builder toggle `TO_INVENTORY` |
| D | na Teste Vista crie um slide azul | resolve playlist via list/context; no guessed UUID | **PROVEN** resolution rule |
| E | crie um slide de 20 segundos com fundo preto | one desired outcome, multiple attributes | planning **TARGET**; atomic OPTION A **PLANNED** |
| F | crie uma tela de OEE com fundo escuro | data discovery if needed + visual proposal + TV slide plan | discovery **PROVEN**; compound **TARGET** |
| G | adicione OEE e mostre como KPI | potential compound capability | **TARGET** |
| H | crie um slide, adicione OEE e deixe o fundo verde | one compound intent, not multiple unrelated chats | **TARGET** |
| I | agora deixe ele azul | resolve previous referent, then revalidate | referent **PLANNED**; revalidate **PROVEN** |
| J | faça uma imagem do slide | image intent only if explicit and capability exists | routing **PROVEN** |

Regression (keep):

- “o que essa métrica significa?” → DATA INTERPRETATION + live preview when possible
- “monte uma tela de produção na TV” → GUIDED DASHBOARD / PLAYLIST CURATION, catalog ops only
- Same metric, different time window → re-preview; do not reuse stale interpretation as FACT

Negative:

- Invented `operationId` / SQL / M / DAX → forbidden
- Commit without preview/confirmation → forbidden
- Treating PREVIEW or 2xx as VERIFIED → forbidden
- Claiming Knowledge overrides live API payload → forbidden
- Claiming current preview already executes full create-then-modify binding → forbidden (TARGET only)
- Asking the user to manually decompose API steps as the preferred UX → forbidden
- Claiming “I cannot save / only guide / do it in the editor” when GPT Actions are available → forbidden (reconnect OAuth / call Action instead)
- Treating retired Chat Copilot as proof that VISTA cannot write → forbidden (write path = eight Actions + PresentationMutation)
- Creating a new playlist/slide/block to apply an alteration on an already identified object → forbidden (see live `capability_surface.agent_directives.object_resolution`; prefer ALTER_EXISTING_BEFORE_CREATE)
