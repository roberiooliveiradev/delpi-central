# DAVI-GENERIC-DOCUMENT-TRANSPORT-INVENTORY-001

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Task type:** INVENTORY / FEASIBILITY / ARCHITECTURE FREEZE PROPOSAL  
**Implementation authorized:** `NO`  
**Runtime changed:** `NO`

## Bootstrap

| Field | Value |
|---|---|
| BOOTSTRAP MAIN (external) | `7f90a3adc4aef73b6aae9751eb1c3d63d1e1752e` |
| BASE / FINAL HEAD (this inventory) | `da6e1cbbc57601732d4e8d3fc8968cd5b5fdece4` |
| origin/main | same as HEAD at inventory start |
| Branch | `main` |
| Working tree | unrelated dirty: openapi catalog + egg-info (preserved) |

No EXECUTION_DRIFT vs expected counts (allowlist v9 / eligible 17 / MCP tools 3).

## Verdict

**OUTCOME F — INCONCLUSIVE — MORE PROVIDER EVIDENCE REQUIRED**

`PREFERRED_PATTERN = NOT_FROZEN`

Rationale (evidence layers separated):

| Layer | Finding | Class |
|---|---|---|
| MCP specification | Resources + binary `blob` (base64) + templates exist | SPEC SUPPORT = PROVEN |
| Python MCP SDK (`mcp==1.30.0`) | `FastMCP.resource`, `BlobResourceContents`, `EmbeddedResource`, `ResourceLink` exist | SDK SUPPORT = PROVEN |
| Our MCP server | Exactly 3 tools; **zero** `@mcp.resource`; tools return `TextContent` + JSON `structuredContent` only | CURRENT_SERVER = PROVEN |
| OpenAI Apps / ChatGPT MCP docs | Document UI resources (`text/html;profile=mcp-app`) and vector-store **text** fetch/search; do **not** prove ChatGPT Agent auto-discovers OAuth remote MCP `application/pdf` blobs as model-visible PDFs | PROVIDER_SUPPORT for PDF model visibility = TO_INVENTORY |
| Live provider spike | Not executed (no safe non-material spike) | `PROVIDER_LIVE_SPIKE = TEST_NOT_RUN` |

Therefore: do **not** freeze A–D. Do **not** force a fourth tool or new resource into implementation without Architecture/Coordination + provider spike proving model PDF visibility under end-user OAuth.

## Frozen architecture (unchanged)

```text
FILESERVER → api-delpi → consumers
DAVI = orchestrator (future document consumer)
PCP = consumer (S2S pattern is NOT a DAVI identity template)
GET /products/{code}/drawing/pdf = canonical PDF route (no new drawing route)
```

Identity: end-user OAuth + PKCE; backend AuthZ final; **no** `API_DELPI_INTERNAL_SERVICE_TOKEN` for DAVI.

## Current capability state

| Capability | Class | Status |
|---|---|---|
| `product.drawing.catalog` | READ | PROVEN LIVE (external evidence; allowlisted) |
| `product.drawing.metadata` | READ | PROVEN LIVE |
| `product.drawing.document` | READ_DOCUMENT | PENDING (HTTP route exists; DAVI transport unproven) |
| `product.drawing.analysis` | DERIVED_ANALYSIS | PENDING (AI API skill PROVEN; blocked on transport) |
| `product.drawing.compare` | DERIVED_ANALYSIS | TARGET |
| `product.drawing.batch_analysis` | ORCHESTRATION | TARGET |

## Current MCP surface (source)

| Item | Evidence |
|---|---|
| Server | `ApiDelpiFastMCP` / FastMCP streamable HTTP (`app/interface/mcp/server.py`, `asgi.py`) |
| SDK | `mcp>=1.28,<2` → installed **1.30.0** |
| Transport | Streamable HTTP, `stateless_http=True`, `json_response=True` |
| Tools | `search_products`, `discover_delpi_information`, `execute_delpi_information` (count **3**) |
| Resources | **ABSENT** (no `@mcp.resource`, no templates registered) |
| Tool output | `CallToolResult` with `TextContent` + `structuredContent` JSON |
| Binary / PDF in tools | **ABSENT** |
| PDF in JSON broker | **ABSENT** (`get_product_drawing_pdf` in `explicitlyNotApproved`) |

## API DELPI PDF contract (unchanged this task)

| Field | Value |
|---|---|
| Route | `GET /products/{code}/drawing/pdf` |
| operationId | `get_product_drawing_pdf` |
| AuthZ | `API_DELPI_ACCESS` (`@require_permission`) |
| Response | Starlette/FastAPI `FileResponse` |
| Content-Type | `application/pdf` |
| Disposition | `inline` + safe filename |
| Not found | 404 (`DrawingPdfLibraryStorageError`) |
| Source unavailable | 503 (`DrawingPdfLibraryUnavailableError`) |
| Path leak | forbidden (no filesystem path in API contract) |
| Owner | api-delpi use cases + `DrawingPdfLibraryStorage` |
| Storage | FILESERVER via `DRAWING_PDF_LIBRARY_DIR` |

Direct PDF live acceptance (after deploy tooling): products `90261805`, `90262957` → 200 / `%PDF` / non-empty — plan only; not executed here.

## Provider inventory (official docs)

Sources consulted (2026-09-17 inventory):

- [MCP Resources](https://modelcontextprotocol.io/docs/concepts/resources) — binary resources use base64 `blob` in `resources/read` (**protocol encoding**, distinct from forbidden PDF-in-`execute_delpi_information` JSON).
- [OpenAI MCP for plugins/API](https://developers.openai.com/api/docs/mcp) — examples center on vector-store **text** search/fetch + citation URLs, not PDF visual handoff from remote MCP.
- [OpenAI Apps / MCP Apps UI](https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt) — resources documented primarily as **UI** (`text/html;profile=mcp-app`).

**Not proven from official provider docs for DAVI:** ChatGPT Agent automatically fetches OAuth-protected remote MCP `application/pdf` resources and presents them to the model as inspectable PDF pages equivalent to a user attachment.

## Candidate patterns

| Pattern | STATUS | Identity | Model PDF visibility | Changes |
|---|---|---|---|---|
| A MCP Resource / template | TARGET / TO_INVENTORY | Compatible **if** resource read uses end-user token + backend AuthZ | **TO_INVENTORY** (ChatGPT) | `NEW_MCP_RESOURCE_REQUIRED=YES` → escalation |
| B Tool returns ResourceLink / EmbeddedResource | TARGET / TO_INVENTORY | Compatible if tool uses end-user context | **TO_INVENTORY** | May keep 3 tools **or** need doc tool; escalation if new tool |
| C Provider-native file handoff | TO_INVENTORY | Unknown | TO_INVENTORY | Possibly OAuth/App change |
| D New document tool | TARGET | Compatible | Depends on return type | `NEW_TOOL_REQUIRED=YES` (3→4) → escalation |
| E Opaque authorized reference | TARGET | Must bind subject/TTL/audience | Depends on provider resolve | Escalation; SSRF/replay risks |
| F Unsupported / inconclusive | **SELECTED** | — | — | No implementation |

Forbidden: Patterns that place PDF bytes/base64 inside `execute_delpi_information`, arbitrary URL/path fetch, service-account DAVI.

## Semantic contract proposal (not implemented)

`product.drawing.document`:

- **Input:** product code (and only proven revision/variant fields if later approved) — never path/URL/host/share
- **Output conceptual:** document identity + safe filename + media_type + size/provenance + **provider-proven transport primitive** (resource URI / ResourceLink / other) — schema **not invented** until provider spike
- **Terminology:** `server-resolved drawing` (not official/approved/released)
- **AuthZ:** same as HTTP PDF (`API_DELPI_ACCESS` via end-user)

## Drawing analysis workflow (reuse)

| Item | Evidence |
|---|---|
| Skill | `minha-delpi-ai-api/app/domain/prompt_policies/drawing-analysis-delpi-skill.md` |
| Validation | `drawing_validation.json` / `drawing_validation_rules.json` (+ rules) |
| Statuses | OK / Pendente / Erro / Erro crítico |
| PDF today | User attachment in Minha DELPI AI chat + vision/OCR pipeline |
| ChatGPT Skill packaging | **TO_INVENTORY** |
| Reuse | **PARTIAL** — procedure reusable; transport packaging for DAVI unproven |

## Attached vs server (design only)

```text
USER_ATTACHED PDF (ChatGPT attachment) + SERVER_RESOLVED drawing (future transport)
→ Drawing Analysis Skill
→ explicit two-source comparison (no silent substitution)
```

Model dual-PDF visibility = TO_INVENTORY.

## Batch (design only)

```text
get_product_structure → bounded codes → metadata → document transport → per-doc analysis → aggregate
```

Budgets **not frozen** (need library distribution + provider limits). Local `/drawing-pdfs` currently **empty** in this environment → size/page distribution = **TO_INVENTORY**. Live catalog evidence previously reported `scanned_files=4796` (external) — use for planning only, not as local proof.

## Security (inventory)

| Risk | Mitigation owner | Status |
|---|---|---|
| Path traversal | api-delpi code normalize | PROVEN on HTTP route |
| Arbitrary URL / SSRF | Do not accept user URL; no generic proxy | REQUIRED in future design |
| Service token for DAVI | Forbidden | PROVEN requirement |
| PDF in JSON broker | Keep deferred | PROVEN absent |
| Reference replay / cross-user | Bind subject+TTL+audience if opaque ref | TO_INVENTORY |
| Malicious/oversized PDF | Size/time bounds + parser limits | TO_INVENTORY |
| Path/credential leak | Projection + redaction | PROVEN for JSON; TBD for resource logs |
| Base64 in MCP resource protocol | Spec uses blob encoding — must not equate to JSON broker violation; still size-bound | SPEC PROVEN / policy TO_INVENTORY |

## Document budget

| Metric | Value | Quality |
|---|---|---|
| Live scanned_files (external evidence) | 4796 | LIVE_OBSERVED (prior task) |
| Examples | 90261805≈35 930 B; 90262957≈199 268 B | LIVE_OBSERVED |
| Local size distribution | EMPTY mount | TO_INVENTORY |
| Page distribution | not measured | TO_INVENTORY |
| Recommended single-doc / batch bounds | **NOT_FROZEN** until distribution + provider limits | — |

## Architecture gates

| Gate | Value |
|---|---|
| OUTCOME | **F** |
| PREFERRED_PATTERN | **NOT_FROZEN** |
| ARCHITECTURE_ESCALATION_REQUIRED | **YES** (any new MCP resource **or** 4th tool **or** OAuth/App primitive) |
| NEW_TOOL_REQUIRED | UNKNOWN (depends on spike) |
| NEW_MCP_RESOURCE_REQUIRED | UNKNOWN (depends on spike) |
| OAUTH_CHANGE_REQUIRED | Default **NO**; prove per candidate |
| AGENT_CHANGE_REQUIRED | Default **NO** for transport spike |
| IMPLEMENTATION_AUTHORIZED | **NO** |

## Residual search (this task)

NEW MCP TOOL / RESOURCE / PDF base64 in broker / generic file|HTTP proxy / allowlist|agent|deploy change / DAVI service token = **ABSENT** (docs-only inventory).

## Next step

Return to **DAVI — Architecture / Coordination** before any implementation.

Suggested future sequence (only after provider spike + freeze):

1. Prove ChatGPT model PDF visibility for chosen primitive under end-user OAuth  
2. Implement single governed document transport  
3. Prove api-delpi PDF live independently  
4. Integrate Drawing Analysis Skill packaging  
5. Single analysis → attached-vs-server → bounded batch  

## Sources read

- `docs/12-roadmap-e-evolucao/davi/README.md`
- `api-delpi/docs/integrations/openai-plugin-mcp.md`
- `api-delpi/docs/api/14-desenhos-pdf.md`
- Evidence: `davi-product-drawing-capability-001`, `davi-product-drawing-pcp-access-001`, `davi-product-drawing-canonical-access-001`
- Code: `app/interface/mcp/server.py`, `product_drawing_routes.py`, `davi_external_read_allowlist.json`
- Skill: `drawing-analysis-delpi-skill.md`
- Cursor rules: centralized-rules-first, ai-external-tools-security, ai-context-and-tool-budget, evidence-driven-execution, platform-security-identity-authorization, contract-evolution, architecture-ci-enforcement (and siblings listed in task)
