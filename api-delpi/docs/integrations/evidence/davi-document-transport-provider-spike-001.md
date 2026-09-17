# DAVI-DOCUMENT-TRANSPORT-PROVIDER-SPIKE-001

**Artifact class:** `EVIDENCE_NOT_RUNTIME_AUTHORITY`  
**Task type:** PROVIDER SPIKE / NON-PRODUCTION EXPERIMENT  
**Implementation authorized:** `NO`  
**Production changed:** `NO` (spike default OFF)

## Bootstrap

| Field | Value |
|---|---|
| BOOTSTRAP MAIN (external) | `0e14f1582be251a2762b482b4375205d3cf808e9` |
| Inventory ancestor | `3193c398c` — still ancestor of HEAD |
| BASE HEAD | `70393ccefdbbcb5d9f0e677dd6b95baba3cee9ed` |
| EXECUTION_DRIFT (MCP/OAuth/drawing/allowlist) | **NO** (only unrelated DELIA docs between inventory and base) |

## Verdict

**INCONCLUSIVE / PASS_WITH_RESIDUAL** for harness delivery  
**PROVIDER_LIVE_SPIKE = BLOCKED_NO_NONPROD_REMOTE**  
**ARCHITECTURE OUTCOME = F (unchanged)**  
**MODEL_PDF_VISIBILITY = NOT_PROVEN**

Local protocol (LEVEL 1) = **PASS**. Remote ChatGPT LEVEL 5 not executable without a non-production remote MCP environment.

## Provider research (revalidated 2026-09-17)

| Source | Finding |
|---|---|
| [MCP Resources](https://modelcontextprotocol.io/docs/concepts/resources) | Binary resources via base64 `blob` in `resources/read` — SPEC |
| [OpenAI MCP docs](https://developers.openai.com/api/docs/mcp) | Examples: vector-store **text** search/fetch + citation URLs |
| [MCP Apps / ChatGPT UI](https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt) | Resources primarily `text/html;profile=mcp-app` UI templates |
| Installed SDK | `mcp==1.30.0` — `FastMCP.resource` accepts `bytes`; `ResourceLink` / `EmbeddedResource` / `BlobResourceContents` exist |

**Doc gap:** No official OpenAI statement that ChatGPT Agent discovers OAuth remote MCP `application/pdf` resources and presents them as model-inspectable PDFs equivalent to attachments.

## Nonprod remote MCP

`NONPROD_REMOTE_MCP = ABSENT` in repository/infra inventory (no staging/sandbox MCP endpoint distinct from production `https://minhadelpi.com.br/apps/api-delpi/mcp`).

Per task §36: **do not deploy experimental surface to production MCP**.

## Spike harness (committed, default OFF)

| Item | Value |
|---|---|
| Flag | `DAVI_DOCUMENT_TRANSPORT_SPIKE_ENABLED` default `false` |
| Mode | `DAVI_DOCUMENT_TRANSPORT_SPIKE_MODE` = `resource_link` \| `embedded` |
| Module | `api-delpi/app/interface/mcp/document_transport_spike.py` |
| Wire-in | `create_mcp_server()` registers only when flag ON |
| Compose | **not** enabled in prod/dev compose |

When OFF: MCP tools = 3, spike resources = 0.  
When ON (isolated): +2 resources (`davi-spike://document-probe`, `davi-spike://text-probe`) + optional tool `spike_document_transport_probe` (temporary count 4).

## Probe

| Item | Value |
|---|---|
| MIME | `application/pdf` |
| Body | handcrafted PDF (`%PDF`) with text + triangle path |
| Hidden text | CODE / SHAPE / REVISION (only inside PDF stream) |
| Metadata leak check | PASS (URI/name/title/description/tool text free of secrets) |
| Control text resource | separate secrets (`TEXT-PROBE-ALPHA` / `CIRCLE` / `V02`) |

## Pattern results

| Pattern | LOCAL_PROTOCOL | REMOTE_PROVIDER | MODEL_TEXT | MODEL_VISUAL | RESULT |
|---|---|---|---|---|---|
| A MCP Resource | PASS | TEST_NOT_RUN | TEST_NOT_RUN | TEST_NOT_RUN | LOCAL_ONLY |
| B ResourceLink | PASS | TEST_NOT_RUN | TEST_NOT_RUN | TEST_NOT_RUN | LOCAL_ONLY |
| C EmbeddedResource | PASS | TEST_NOT_RUN | TEST_NOT_RUN | TEST_NOT_RUN | LOCAL_ONLY |
| D Experimental tool | USED (gated) | TEST_NOT_RUN | TEST_NOT_RUN | TEST_NOT_RUN | LOCAL_ONLY |

## Levels

| Level | Status |
|---|---|
| 1 SDK payload | PASS |
| 2 Remote MCP | TEST_NOT_RUN (no nonprod) |
| 3 Provider acceptance | TEST_NOT_RUN |
| 4 Model receives document | TEST_NOT_RUN |
| 5 Hidden content extraction | TEST_NOT_RUN |

## Manual ChatGPT plan (when nonprod remote exists)

1. Deploy/enable spike **only** on isolated nonprod MCP (never production URL).  
2. Connect ChatGPT to that MCP; complete normal end-user OAuth + PKCE.  
3. Do **not** paste expected CODE/SHAPE/REVISION into the chat.  
4. Ask: `Read the provided PDF and tell me the code, shape and revision shown inside it.`  
5. Capture raw model answer; compare offline to expected values.  
6. Disable/remove nonprod registration after capture.

## Architecture result

| Gate | Value |
|---|---|
| OUTCOME | **F** |
| PREFERRED_PATTERN_CANDIDATE | NOT_FROZEN |
| MODEL_PDF_VISIBILITY | **NOT_PROVEN** |
| NEW_MCP_RESOURCE_REQUIRED | UNKNOWN (pending LEVEL 5) |
| NEW_TOOL_REQUIRED | UNKNOWN |
| OAUTH_CHANGE_REQUIRED | NO |
| IMPLEMENTATION_AUTHORIZED | **NO** |

## Production regression

allowlist v9 / eligible 17 / tools 3 / drawing JSON unchanged / dynamic READ unchanged.

## Next step

Provision or identify a **non-production remote MCP** with the same OAuth pattern, then re-run LEVEL 2–5. Until then, retain inventory OUTCOME F — do not implement `product.drawing.document`.
