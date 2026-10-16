# 90 — L1 Governed Link Binding Inventory & Contract Closure

**Status:** `INVENTORY_EXECUTED / LINK_L1_CAPABILITY_BINDINGS=PARTIAL / NAVIGABLE_LINK_EMISSION=BLOCKED / RUNTIME_NOT_AUTHORIZED`  
**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-BINDING-INVENTORY-01`  
**BASE_HEAD:** `c98870a6caa8d76340b6c860d2488024b15691e7`  
**CP:** `CP-333` — `PLANNED_NOT_PASS`  
**Tipo:** ARCHITECTURE + CONTRACT + INVENTORY + EVIDENCE — **sem** `presentation.v2` runtime, **sem** `ConversationMarkdown`, **sem** deploy, **sem** writes Domain/ACT.

Preserva doc [89](./89-presentation-v2-g1-g2-r3-independent-closure-review.md) (`ACCEPT_WITH_RESIDUAL`) e decisões D1–D12 + `LINK_SOURCE_TYPED=L1_APPROVED_CONDITIONAL`.

> Markdown B2 / CP-333 ≠ `C3-STAGE-02-B2` (PREPARE/ACT).

---

## A. L1 Owner Contract Inventory

| # | Owner | Contract surface | Field | Published semantics | AuthZ | Consumer today | Path into DÉLIA turn | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 | `api-delpi` mural_acessos | OpenAPI `list_mural_acessos_links` / `list_public_mural_acessos_menu*` + `_present_admin_link` / `_present_public_link` | `url` | Destino de atalho publicado no mural; write via `normalize_link_url` (`http`/`https`+netloc+≤2000) | `MURAL_ACESSOS_READ_PERMISSIONS` (admin); public menu by hub token | MFE `plugins/mural-acessos`; Chat action catalog **também** indexa oids (não é autoridade DÉLIA) | **ABSENT** — `rg mural` em `delia-api` = 0 | `PARTIAL_CONTRACT_PROVEN` |
| 2 | `api-delpi` external capabilities | `argument_validator._TRANSPORT_FORBIDDEN` | `url` (arg) | Transporte — **proibido** como argumento | n/a | capability execute | n/a | `NOT_AUTHORIZED` |
| 3 | `api-delpi` guias_procedimentos | `validate_external_video_url` | video URL | Mídia embutida de guia — não destino de navegação conversacional B2 | Domain | Guias MFE | ABSENT em DÉLIA turn | `OUT_OF_SCOPE` (não B2 textual link) |
| 4 | `core-api` notifications | `NotificationContentService` action targets | `action.target` | `portal_route` (`/` absolute, no `//`) ou `external_url` (**https** only) | Core notification AuthZ | Portal notification UI | ABSENT — não alimenta `SpecialistOutcome` | `PARTIAL_CONTRACT_PROVEN` (padrão reutilizável; **não** binding DÉLIA) |
| 5 | Portal shell | `sameAppAnchorNavigation` / AppHost | `<a href>` click | Consumer de navegação same-origin; **não** publica destino | live AuthZ no destino | MFEs embutidos | Consumer-only | `REUSE` como política de navegação interna; **não** fonte L1 |
| 6 | DÉLIA provenance | `GovernedCapabilityProvenance.to_projection` | — | Explicitamente **sem URLs** | n/a | Interactive turn | PROVEN URL-free | `NOT_AUTHORIZED` as link source |
| 7 | DÉLIA evidence | `SourceRef` | — | Identity/origin only | n/a | EvidenceDetails | PROVEN URL-free | `NOT_AUTHORIZED` |
| 8 | DÉLIA workspace | `WorkspaceEntityRef` | — | Untrusted client hint; no href | never grants AuthZ | prompt block | PROVEN no href | `NOT_AUTHORIZED` |
| 9 | presentation.v2 proposal | `owner_hint` notice | `text` | URL-free by schema description | n/a | future v2 | TARGET | `NOT_AUTHORIZED` |
| 10 | Specialists MCP/A2A | capability structured output | *(varies)* | Nenhum schema DÉLIA publica campo tipado `published_navigable_destination` | specialist AuthZ | `SpecialistOutcome.structured` | **no typed link field** found | `TO_INVENTORY` / `NOT_SUPPORTED_BY_CURRENT_CONTRACT` |

### Drift vs B2 emission policy

`normalize_link_url` (mural write) admite `http` e `https`. A política B2 de **emissão** conversacional exige `https` para externos (doc 84 §2.4). Isso é **gap de alinhamento** se o binding mural for algum dia ligado — não autoriza emitir `http` na conversa.

Chat (`minha-delpi-ai-api` operational route registry) indexa oids mural — **não** constitui capability DÉLIA nem binding L1 (standalone boundary).

---

## B. Capability Binding Traceability Matrix

Candidato primário: mural `url`.

| STEP | RESPONSIBILITY | OWNER | SOURCE_FILE | CONTRACT | INPUT | OUTPUT | AUTHZ | PROVENANCE | CONSUMER | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 Domain owner | Persist/publish shortcut | api-delpi mural | `link_url.py`, `mural_acessos_use_cases.py` | OpenAPI mural_access_link | write payload | row.url | mural perms | audit fields | DB | code | `PROVEN` |
| 2 Domain read contract | Present link | api-delpi | `_present_*_link` | OpenAPI list/get | hub_id | `{url,...}` | READ / public token | — | MFE mural | code | `PROVEN` |
| 3 Capability contract | Semantic capability exposing links | DÉLIA specialist registry | — | — | — | — | — | — | — | **no capability_id** | `TO_INVENTORY` |
| 4 Provider/MCP adapter | Wire Domain→specialist | delia-api interoperability | — | — | — | — | — | — | — | no mural adapter | `TO_INVENTORY` |
| 5 SpecialistOutcome | Untrusted structured | delia-api | `specialist_interop/model.py` | Mapping | remote result | `structured` | — | SpecialistResultProvenance | orchestration | `PROVEN` shape; **no link field** | `PROVEN` (container) / `NOT_SUPPORTED` (link) |
| 6 Governed projection | Sanitize/render | capability_provision | `render_specialist_outcome` | text projection | structured | content string | redaction | — | turn | R3 accepted | `PROVEN` — does **not** emit navigable links |
| 7 InteractiveTurnResult | Envelope | interaction | presentation.py v1 | presentation.v1 | content | JSON | — | provenance proj | MFE | v1 only | `PROVEN` |
| 8 presentation.v2 | Markdown blocks + links | — | proposal schema | doc 84 | — | — | — | — | — | CONTRACT_TARGET | `TARGET` |
| 9 MFE link policy | Render `<a>` or inert | plugin-ui (future) | ConversationMarkdown NEW | doc 84 §5 | blocks | React | — | — | delia MFE | not implemented | `PLANNED` |
| 10 Portal/external nav | Navigate | Portal | `sameAppAnchorNavigation.ts` | click policy | href | SPA or native | live | — | browser | code | `PROVEN` consumer |

**End-to-end navigable emission:** `NOT_PROVEN` — chain breaks at steps 3–4.

---

## C. L1 Contract Closure Proposal

### C.1 Origem (allowlist tipada — não nome de campo)

Um destino só é candidatável se existir entrada publicada:

```text
GovernedLinkBinding(
  owner_id,              # e.g. api-delpi.mural_acessos
  capability_id,         # semantic capability that returns the field
  field,                 # exact field name in structured
  field_semantics,       # must be "published_navigable_destination"
  disclosure_allowed,    # owner-declared
  destination_kind       # external_https | internal_portal
)
```

**Produção:** allowlist **vazia** até Architecture autorizar o primeiro binding real.

### C.2 Admissão (emissor backend — futuro G3)

| Rule | Value |
|---|---|
| Max length | 2000 |
| External scheme | `https` only + netloc |
| Internal | absolute `/…`, reject `//` |
| Reject | `javascript:`, `data:`, `blob:`, `attachment:`, `file:`, `mailto:`, `http:`, protocol-relative, credentials in URL, sensitive query (`token`, `access_token`, …) |
| Redirects | no automatic follow at admit time |
| Freshness | destination resolves own state (404/410/AuthZ) |

Executable probe (non-runtime): `delia-api/tests/test_l1_governed_link_admission_policy.py`.

### C.3 Navegação

- Interno: Portal `sameAppAnchorNavigation` + AuthZ live no destino.
- Externo: `target=_blank` `rel=noopener noreferrer`; no auto-open; no remote fetch.
- Companion Dock: mesmos `<a>`; sem bridge paralelo.

### C.4 Falhas

| Situation | Behavior |
|---|---|
| No binding / generic `url`/`href`/`*_url` | inert label text |
| Invalid/hostile URL with binding | inert label |
| Hostil payload / non-admitted presentation | `neutral_error` (doc 84 §2.5) |
| Destination AuthZ fail | destination owns error |

### C.5 Reuse Gate

```text
EXISTING_EQUIVALENT = YES (partial)
REUSE_DECISION = EXTEND
```

Reutilizar: mural Domain contract semantics + Core notification URL validation pattern (https/portal_route) + Portal same-app navigation.  
**Não** criar `LinkRef` registry, catálogo paralelo, ou planner URL branches.  
**Não** NEW abstraction nesta task.

### C.6 Menor trabalho para fechar binding mural (recomendado — não executar aqui)

1. Owner api-delpi declara disclosure policy “link.url publicável em capability read X”.
2. Capability semântica DÉLIA (ou OpenAPI-imported governed read) com schema de saída tipando o campo.
3. Adapter projeta para `SpecialistOutcome.structured` sem promover outros `*_url`.
4. Allowlist entry registrada no emissor presentation.v2.
5. Positive+negative probes + independent review → então G3 brief.

---

## D. Security / AuthZ Review

| Trust boundary | Finding |
|---|---|
| Model / prose | Never source — probe `model_prose` → inert |
| MCP metadata / tool schema | Never source — probes |
| SourceRef / EntityRef / WorkspaceEntityRef / owner_hint | URL-free / no grant — PROVEN |
| `_TRANSPORT_FORBIDDEN` | Blocks `url` as capability **argument** — PROVEN |
| Domain mural write | Validates scheme; allows http — stricter emit policy needed |
| Core notifications | https external / `/` portal — good reuse pattern; wrong product surface for B2 body links |
| Portal navigation | Consumer only; AuthZ at destination |
| Redaction (R3) | `token` key redacted — accepted; query `?token=` rejected at admit |

---

## E. Test Evidence

| Suite | Result | SHA / config |
|---|---|---|
| `tests/test_l1_governed_link_admission_policy.py` | **35 PASS** | BASE_HEAD `c98870a6ca`; Python 3.12 / pytest delia-api `.venv` |
| `tests/test_presentation_v2_proposal.py` + fidelity | PASS (combined with L1 = 76) | same |
| `api-delpi` `test_mural_acessos_use_cases` `-k link_url\|normalize_link` | **2 PASS** | api-delpi |
| plugins/delia / plugin-ui markdown | `TEST_NOT_RUN` (inventory não altera frontend) | — |
| Build / Federation | `TEST_NOT_RUN` | — |

Fixtures are synthetic; **positive admit does not prove production binding**.

---

## F. SSH Validation (read-only)

Target: `operador@192.168.1.237` (`srv-api`). No deploy/restart/writes.

| Check | Result |
|---|---|
| SSH_ACCESS | PASS (BatchMode) |
| REMOTE_HEAD | `6a7aeed999` — **behind** inventory HEAD (`c98870a6ca`); transformometro/docs commits not pulled |
| DELIA mural refs | **0** (grep) |
| `_TRANSPORT_FORBIDDEN` `url` | present |
| `PRESENTATION_CONTRACT_VERSION` | `"1"` |
| `normalize_link_url` / schemes | present (`http`,`https`) |
| Containers | delia-api / api-delpi / portal / gateway healthy |
| Gateway health | `/apps/delia-api/health` → 200 |
| DEPLOYED_RUNTIME_SHA | image `sha256:d149abbdebb…` (R3-era; **not** labeled with git SHA) |
| SSH_RESIDUALS | remote checkout stale vs origin; does not invalidate zero-binding evidence |

---

## G. Architecture Decision / Residual Register

| ID | Decision / Residual | Status |
|---|---|---|
| L1 | Product Master — approved conditional | FROZEN |
| BINDINGS | Domain contracts PARTIAL; DÉLIA path NOT_PROVEN | `PARTIAL` |
| EMISSION | Zero navigable links | `BLOCKED` |
| HTTP vs HTTPS | mural write allows http; B2 emit https-only | `CONTRACT_GAP` for future binding |
| Chat mural oids | Parallel Chat catalog — not DÉLIA authority | `OUT_OF_SCOPE` |
| G3 | Still blocked | `BLOCKED` |
| ADR | No new LinkRef; EXTEND existing seams when binding lands | RECOMMENDED |

---

## H. Independent Review Handoff

```text
VERDICT_FOR_COORDINATION: READY_FOR_INDEPENDENT_REVIEW
EXIT: B — PARTIAL
LINK_L1_CAPABILITY_BINDINGS = PARTIAL
RESIDUAL = CAPABILITY_BINDING_TO_DELIA_MISSING (+ http/https emit gap)
NAVIGABLE_LINK_EMISSION = BLOCKED
G3 = BLOCKED
CP_333 = PLANNED_NOT_PASS
NEXT_BOUNDED = DELIA-UX-CONVERSATION-MARKDOWN-B2-L1-MURAL-CAPABILITY-BINDING-01
  (or Architecture Decision if Product Master prefers first B2 slice without links)
```

Do **not** auto-unlock G3 from this inventory.
