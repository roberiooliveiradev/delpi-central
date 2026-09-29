# BPMN Modeler — API / E2E / Acceptance Spec Freeze (Prompt 7/7)

> **Status:** `FROZEN`
> **Escopo:** transporte HTTP, OpenAPI, DTOs, conditional requests, uploads/downloads, error mapping, paginação, idempotência/retry, health wire, E2E, acceptance e readiness final da V1.
> **Natureza:** freeze de especificação. **Não autoriza implementação por si só** — autoriza apenas o futuro Master Implementation Prompt.

Este é o sétimo e último documento do Specification Freeze. Fecha a única superfície ainda delegada (transporte + provas) e audita a coerência dos seis freezes anteriores. **Não existe Prompt 8.**

Autoridade documental por domínio (precedência por ownership, não por ordem temporal):

```text
produto/escopo          → V1-SCOPE-FREEZE.md
domínio/aplicação       → BACKEND-DOMAIN-SPEC-FREEZE.md
BPMN/validação          → BPMN-INTEROPERABILITY-SPEC-FREEZE.md
editor/UX/estado        → FRONTEND-EDITOR-UX-SPEC-FREEZE.md
layout/BPMN-DI          → LAYOUT-BPMN-DI-SPEC-FREEZE.md
segurança/persistência  → SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md
transporte/E2E/aceite   → ESTE DOCUMENTO
```

Conflito real → `EXECUTION_DRIFT` na parte afetada; corrigir a fonte proprietária, nunca sobrescrever silenciosamente.

---

## 1. Frozen inputs

Documentos autoritativos (HEAD, verificados sem drift não decidido):

- `V1-SCOPE-FREEZE.md` (P1)
- `BACKEND-DOMAIN-SPEC-FREEZE.md` (P2, com clarificação UC-WC-004 aplicada por este prompt — §4.1)
- `BPMN-INTEROPERABILITY-SPEC-FREEZE.md` (P3 corrigido)
- `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` (P4, dirty-state corrigido)
- `LAYOUT-BPMN-DI-SPEC-FREEZE.md` (P5, dirty-state corrigido)
- `SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md` (P6 corrigido, commit `ecaaa8e872`)

## 2. Baseline / inventory

- HEAD: `ecaaa8e872de7c75b5f3cbcbe0a54e2ae80ac9ea` (main, sincronizado com origin). Dirty work externo preservado (plugins/tv-dashboard etc. — fora de escopo).
- Nenhum commit paralelo alterou `bpmn-modeler/` ou os freezes após o P6.
- Convenções monorepo inventariadas:
  - Paginação wire existente: `page`/`page_size` query params com bounds (padrão `*-api`).
  - Error envelope canônico: `shared/delpi_api_client/envelope.py` — `{success, message, data, error:{code, recoverable}, meta}` (api-delpi).
  - Request-id: nenhuma convenção transversal consolidada encontrada → contrato definido aqui (§18).
  - ETag/If-Match: nenhum uso existente em código de produto → introduzido aqui como contrato deste contexto.
  - E2E framework: nenhum browser-E2E existente (sem Playwright/Cypress); testes existentes são pytest. Browser E2E introduzido como ferramenta nova e única (§24).
  - Uploads: `python-multipart` já locked (P6); downloads de arquivo existem em outros contextos via `Content-Disposition`.

## 3. Cross-freeze consistency corrections

### 3.1 ValidateWorkingCopy — candidate semantics (aplicada em P2)

`FROZEN` — reconciliação P2↔P4:

- `ValidateWorkingCopy` valida o **artefato candidato** enviado pelo editor (`exportXml()` do estado visível, possivelmente DIRTY), não apenas o artefato persistido.
- Semântica: `editor exportXml() → POST validate → CanonicalBpmnArtifact candidato → BpmnArtifactValidationPort → ValidationReport → zero write`.
- O XML enviado é `candidate` ≠ artefato persistido; ser validado não o torna canônico.
- Correção documental mínima aplicada em `BACKEND-DOMAIN-SPEC-FREEZE.md` (linhas do catálogo UC-WC-004 e da tabela de outputs) — nenhuma regra de negócio alterada.

### 3.2 Import PREPARE transport

`FROZEN` — `POST /imports/inspect` resolve o PREPARE do Prompt 2/4:

```text
upload bytes
→ InputSafetyEvidence
→ recognition
→ validation
→ operation-policy assessment
→ ImportInspectionResponse
→ ZERO persistence
```

- **Não** cria temporary model, draft row, upload session ou autoridade canônica temporária.
- O create definitivo (`POST /models/import`) reenvia o arquivo e reexecuta intake/recognition/validation completos — o resultado do inspect **nunca** autoriza bypass (sem prepare token).
- Classificado como **transport/orchestration support operation**, não use case de negócio.

## 4. API base & versioning

`FROZEN`:

| Camada | Valor |
|---|---|
| External base path | `/apps/bpmn-modeler-api` (gateway → service `--root-path`) |
| FastAPI router paths | **sem** prefixo — `/models`, `/models/{model_id}`, etc. Root path não é duplicado nos routers. |
| Path versioning | **unversioned** — convenção do monorepo não usa `/v1` em paths de plugin-api |
| Contract version | OpenAPI `info.version = "1.0.0"` — versão do contrato registrada no schema, independente de path |

## 5. Authoritative route map

`FROZEN` — mapa único e exato; nenhuma rota adicional sem requirement:

| # | Method | Router path | Operação | Classificação |
|---|---|---|---|---|
| 1 | GET | `/health` | liveness | runtime support (pública) |
| 2 | GET | `/ready` | readiness | runtime support (pública) |
| 3 | GET | `/models` | ListModels | business |
| 4 | POST | `/models` | CreateModel | business |
| 5 | POST | `/models/import` | ImportModel | business |
| 6 | POST | `/imports/inspect` | import PREPARE (inspect) | transport support (autenticada, `bpmn-modeler.edit`) |
| 7 | GET | `/models/{model_id}` | GetModel | business |
| 8 | PATCH | `/models/{model_id}` | RenameModel | business |
| 9 | POST | `/models/{model_id}/duplicate` | DuplicateModel | business |
| 10 | POST | `/models/{model_id}/archive` | ArchiveModel | business |
| 11 | POST | `/models/{model_id}/unarchive` | UnarchiveModel | business |
| 12 | GET | `/models/{model_id}/working-copy` | GetWorkingCopy | business |
| 13 | PUT | `/models/{model_id}/working-copy` | SaveWorkingCopy | business |
| 14 | POST | `/models/{model_id}/working-copy/validate` | ValidateWorkingCopy (candidate) | business |
| 15 | GET | `/models/{model_id}/working-copy/export` | ExportWorkingCopy | business |
| 16 | GET | `/models/{model_id}/revisions` | ListRevisions | business |
| 17 | POST | `/models/{model_id}/revisions` | CreateRevision | business |
| 18 | GET | `/models/{model_id}/revisions/{revision_number}` | GetRevision | business |
| 19 | POST | `/models/{model_id}/revisions/{revision_number}/restore` | RestoreRevision | business |
| 20 | GET | `/models/{model_id}/revisions/{revision_number}/export` | ExportRevision | business |

## 6. Use case ↔ route matrix

`FROZEN` — **17/17** business use cases mapeados; 3 operações de suporte separadas:

| UC | Route | Permission | Mutating |
|---|---|---|---|
| UC-MODEL-001 CreateModel | `POST /models` | `bpmn-modeler.edit` | sim (novo agregado) |
| UC-MODEL-002 ImportModel | `POST /models/import` | `bpmn-modeler.edit` | sim (novo agregado) |
| UC-MODEL-003 GetModel | `GET /models/{model_id}` | `bpmn-modeler.view` | não |
| UC-MODEL-004 ListModels | `GET /models` | `bpmn-modeler.view` | não |
| UC-MODEL-005 RenameModel | `PATCH /models/{model_id}` | `bpmn-modeler.manage` | sim + If-Match |
| UC-MODEL-006 DuplicateModel | `POST /models/{model_id}/duplicate` | `bpmn-modeler.manage` + `.view` (origem) | sim (novo agregado) |
| UC-MODEL-007 ArchiveModel | `POST /models/{model_id}/archive` | `bpmn-modeler.manage` | sim + If-Match |
| UC-MODEL-008 UnarchiveModel | `POST /models/{model_id}/unarchive` | `bpmn-modeler.manage` | sim + If-Match |
| UC-WC-001 GetWorkingCopy | `GET .../working-copy` | `bpmn-modeler.view` | não |
| UC-WC-002 SaveWorkingCopy | `PUT .../working-copy` | `bpmn-modeler.edit` | sim + If-Match |
| UC-WC-003 ExportWorkingCopy | `GET .../working-copy/export` | `bpmn-modeler.view` | não |
| UC-WC-004 ValidateWorkingCopy | `POST .../working-copy/validate` | `bpmn-modeler.view` | **não** (candidate, zero write) |
| UC-REV-001 ListRevisions | `GET .../revisions` | `bpmn-modeler.view` | não |
| UC-REV-002 GetRevision | `GET .../revisions/{revision_number}` | `bpmn-modeler.view` | não |
| UC-REV-003 CreateRevision | `POST .../revisions` | `bpmn-modeler.manage` | sim + If-Match |
| UC-REV-004 RestoreRevision | `POST .../revisions/{revision_number}/restore` | `bpmn-modeler.manage` | sim + If-Match |
| UC-REV-005 ExportRevision | `GET .../revisions/{revision_number}/export` | `bpmn-modeler.view` | não |

**Revision selector `FROZEN`:** `{revision_number}` é o seletor de rota (alinhado ao frontend). `revision_id` (uuid) permanece identidade/metadata interna retornada no resource — **não** existem URLs concorrentes `/revisions/{revision_id}` ou `/revisions/by-number/{n}`.

Support ops: `/health`, `/ready` (públicas, runtime); `/imports/inspect` (autenticada `.edit`, transport support — não persiste). Nenhuma rota de write sem UC; nenhum UC sem rota.

## 7. Resource DTOs

`FROZEN` — JSON `application/json; charset=utf-8`, snake_case, campos exatos (Abstraction Gate aplicado — composição, não envelope por endpoint):

```text
ModelSummary = {
  id: uuid, display_name: string, archived_at: datetime|null,
  version: int, created_at: datetime, updated_at: datetime,
  latest_revision_number: int|null
}                                  // nunca contém XML

ModelDetail = ModelSummary + { created_by: string, updated_by: string }
                                  // working-copy XML NUNCA embutido — artefato tem endpoint próprio

RevisionSummary = {
  revision_number: int,            // seletor de rota
  revision_id: uuid,               // identidade interna (metadata)
  origin: "explicit"|"restore",
  created_at: datetime, created_by: string, artifact_sha256: hex64
}

RevisionDetail = RevisionSummary   // artefato via .../export — nunca XML embutido em JSON

ValidationIssueResponse = {
  rule_id: string, rule_source: "xml_w3c"|"omg_bpmn"|"omg_bpmn_di"|"product",
  stage: ValidationStage, severity: "error"|"warning"|"info",
  message: string, element_id: string|null, path: string|null
}

ValidationReportResponse = {
  evaluated_stages: ValidationStage[],
  not_evaluated_stages: ValidationStage[],
  issues: ValidationIssueResponse[]
}

ImportInspectionResponse = {
  recognition_state: RecognitionState,       // INPUT_REJECTED_SECURITY | NON_XML | MALFORMED_XML | XML_NOT_BPMN | BPMN_RECOGNIZED_INCOMPLETE | BPMN_RECOGNIZED_WITH_ISSUES | BPMN_RECOGNIZED
  eligible_to_import: boolean,               // operation policy já avaliada
  validation_report: ValidationReportResponse|null,
  artifact_byte_length: int|null,
  artifact_sha256: hex64|null
}

MutationResult = {
  changed: boolean,                          // false = NO_OP_SUCCESS
  model_id: uuid,
  version: int,                              // version resultante (igual ao anterior se no-op)
  artifact_sha256: hex64|null,
  revision_number: int|null,                 // create/restore revision
  message: string                            // pt-BR, segura
}

PagedModelsResponse    = { items: ModelSummary[],    page: int, page_size: int, has_more: boolean }
PagedRevisionsResponse = { items: RevisionSummary[], page: int, page_size: int, has_more: boolean }

ErrorResponse (envelope canônico da plataforma — §15)
HealthResponse = { status: "ok" }
ReadyResponse  = { status: "ready"|"not_ready", checks: { database: bool, xsd_bundle: bool, schema: bool } }
```

## 8. Working copy transport

`FROZEN` — representação única, sem reserialização:

| Operação | Request | Response |
|---|---|---|
| `GET .../working-copy` | — | `200 application/xml; charset=utf-8` — **bytes canônicos exatos**; headers `ETag: "vN"`, `X-Artifact-SHA256: <hex64>`, `Content-Length`, `Cache-Control: no-store` |
| `PUT .../working-copy` | `application/xml; charset=utf-8` (candidate `exportXml()`) + `If-Match: "vN"` | `200` `MutationResult` JSON |
| `POST .../working-copy/validate` | `application/xml; charset=utf-8` (candidate) | `200` `ValidationReportResponse` |
| `GET .../working-copy/export` | — | `200 application/xml` + `Content-Disposition: attachment` + `X-Content-Type-Options: nosniff` |

- XML cru como media type (não JSON envelope para até 10 MiB) — a string canônica chega **byte-exata**, preservando checksum. `version`/`sha256` trafegam em headers.
- GET working-copy em model arquivado → permitido (read-only UX decide).
- Model inexistente → `404`.

### 8.1 Save → authoritative read-back sequence

`FROZEN` — sequência única:

```text
PUT working-copy (candidate + If-Match)
→ backend: intake evidence → validation pipeline → policy → CAS write → authoritative read-back → verify
→ 200 MutationResult{changed, version, artifact_sha256} + ETag "vN+1"
→ frontend: GET /working-copy → import authoritativeXml → markSaved() → CLEAN
```

- `markSaved()` **somente** após o GET autoritativo bem-sucedido — a resposta do PUT prova o write, mas o estado canônico do editor é re-importado do GET (elimina divergência de serialização).
- Se `changed=false` (NO_OP_SUCCESS), o GET de read-back continua obrigatório para o ciclo CLEAN.
- Falha no GET pós-save → estado `SAVE_VERIFY_PENDING` (UI: "salvo, confirmando estado" → retry do GET, que é operação segura). Nunca `markSaved()` sem artefato autoritativo.

## 9. Validate candidate transport

`FROZEN`: `POST /models/{model_id}/working-copy/validate`, body = candidate XML (`application/xml; charset=utf-8`).

- Zero write: não altera `version`, não cria revision, não toca `updated_at/by`, não marca model.
- Permitido em model ativo **e** arquivado (contrato backend permite).
- Resposta `200 ValidationReportResponse` mesmo quando issues existem — validation result não é erro de transporte.
- Rejeição de segurança no intake → `400 INPUT_REJECTED_SECURITY`; oversize → `413`; model inexistente → `404`.

## 10. Import PREPARE / Import create

`FROZEN`:

### 10.1 `POST /imports/inspect`

- `multipart/form-data`, campo `file` = bytes brutos.
- Backend **não confia** em filename/extension/Content-Type para recognition — evidence vem dos bytes.
- Resposta `200 ImportInspectionResponse` para **todos** os recognition states (inspect é diagnóstico — estados são dado, não erro): inclui `INPUT_REJECTED_SECURITY`, `NON_XML`, `MALFORMED_XML`, `XML_NOT_BPMN`, `BPMN_RECOGNIZED_INCOMPLETE`, `BPMN_RECOGNIZED_WITH_ISSUES`, `BPMN_RECOGNIZED`.
- `413` se upload bruto > `MAX_INPUT_BYTES` (transport error, antes de evidence); `400` se multipart sem `file`.
- Zero persistence (§3.2).

### 10.2 `POST /models/import`

- `multipart/form-data`: `file` (bytes) + `display_name` (string).
- Re-execução completa: re-read → re-safety → re-recognition → re-validation → policy → write. Resultado de `/imports/inspect` nunca é confiado.
- Rejections: `INPUT_REJECTED_SECURITY`/`NON_XML`/`MALFORMED_XML`/`XML_NOT_BPMN` → `422` `VALIDATION_BLOCKED` com `error.details.validation_report` + `error.details.recognition_state` (oversize continua `413`).
- `BPMN_RECOGNIZED*` → `201` `MutationResult` (version=1, sha256). Issues ERROR são admitidas no import conforme operation policy do Prompt 3 — reportadas no `details` opcional? Não: `MutationResult` não carrega report; a UI já tem o inspect. O create retorna apenas o resultado da mutation.
- Nenhum prepare token existe.

## 11. Create / Rename / Duplicate / Archive / Revision — request shapes

`FROZEN`:

| Route | Request body |
|---|---|
| `POST /models` | `{ "display_name": "..." }` — blank artifact é server-generated (P3); **não** aceita XML |
| `PATCH /models/{id}` | `{ "display_name": "..." }` + `If-Match` — **único** campo; `archived_at`/`version`/`created_by`/`working_copy` no body → `400`/`422` |
| `POST .../duplicate` | `{ "display_name": "..." }` — novo ID server-side; revision history **não** copiada; target ID do cliente rejeitado |
| `POST .../archive` / `.../unarchive` | **sem body** + `If-Match`. `DELETE` nunca é usado para archive; hard delete não existe |
| `POST .../revisions` | **sem body** + `If-Match` — V1 não tem label/note/reason editável; não inventar campos |
| `POST .../revisions/{n}/restore` | **sem body** + `If-Match` — snapshot autoritativo lido server-side; cliente nunca envia XML de revision; confirmação é UX (P4), não `confirm=true` |

## 12. Concurrency — ETag / If-Match contract

`FROZEN` — `expected_version` (P2) trafega como **conditional request**, única autoridade:

```text
ETag: "v7"        ← emitido em GET /models/{id}, GET working-copy e em toda resposta de mutation
If-Match: "v7"    ← obrigatório em toda mutation de agregado existente
```

- Sintaxe exata: quoted string `"v" + version decimal` (`W/` weak prefix **proibido**).
- `ETag` representa **aggregate concurrency state** (`Model.version`), **não** checksum do XML — `X-Artifact-SHA256` é identidade de artefato. Os dois nunca se substituem.
- `If-Match` ausente em mutation que exige → `428` `PRECONDITION_REQUIRED`.
- `If-Match` stale → `412` `PRECONDITION_FAILED` com `error.code = "CONFLICT"` (Prompt 4 entra no fluxo CONFLICT). Sem force overwrite.
- `If-Match` malformado (não casa `"v<int>"`) → `400`.
- Não existe `expected_version` no body — uma única autoridade no header.
- `If-None-Match` não é usado na V1; `If-Match: *` rejeitado (`400`) — sempre versão exata.

### 12.1 Mutation precondition matrix

`FROZEN`:

| Route | If-Match obrigatório |
|---|---|
| POST /models, /models/import, .../duplicate | não (agregado novo) |
| PATCH /models/{id} | **sim** |
| POST .../archive, .../unarchive | **sim** |
| PUT .../working-copy | **sim** |
| POST .../revisions | **sim** |
| POST .../revisions/{n}/restore | **sim** |
| POST .../working-copy/validate | não (não é mutation) |
| todos os GETs | não |

## 13. HTTP status matrix

`FROZEN` — somente estes status existem na superfície:

| Status | Quando |
|---|---|
| `200` | reads; PUT save; validate; inspect; mutations com `changed=true` sobre recurso existente; no-op `changed=false` |
| `201` | POST /models, /models/import, .../duplicate, .../revisions |
| `400` | request malformado; multipart sem `file`; `If-Match` malformado/`'*'`; INPUT_REJECTED_SECURITY em `/working-copy/validate` |
| `401` | token ausente/inválido/expirado |
| `403` | `UNAUTHORIZED_OPERATION` |
| `404` | `MODEL_NOT_FOUND`, `REVISION_NOT_FOUND` |
| `409` | `MODEL_ARCHIVED` (mutation em arquivado), `NO_CHANGES` |
| `412` | `If-Match` stale → `CONFLICT` |
| `413` | upload bruto > `MAX_INPUT_BYTES` (transport error — nunca `NON_XML`/`MALFORMED_XML`) |
| `415` | Content-Type errado (ex.: JSON em PUT working-copy) |
| `422` | `INVALID_DISPLAY_NAME`, `VALIDATION_BLOCKED` (com report estruturado), validação de framework normalizada |
| `428` | `If-Match` ausente → `PRECONDITION_REQUIRED` |
| `429` | rate limit do gateway (wire expectation; `Retry-After` propagado quando o gateway emitir) |
| `500` | `OUTCOME_VERIFICATION_FAILED` (semântica: não retentar; ler estado autoritativo) |
| `503` | `INFRASTRUCTURE_FAILURE` (dependência indisponível); `/ready` degradado |

Nenhum status por `rule_id` individual; não criar códigos fora da tabela.

## 14. Error envelope & application error mapping

`FROZEN` — **um único** envelope no produto, alinhado à convenção `shared/delpi_api_client/envelope.py` (`{success, message, data, error, meta}`):

```json
{
  "success": false,
  "message": "O modelo foi alterado por outra operação.",
  "data": null,
  "error": { "code": "CONFLICT", "recoverable": true, "details": {} },
  "meta": { "request_id": "..." }
}
```

- `error.details`: schema limitado por código (ex.: `VALIDATION_BLOCKED` → `{recognition_state, validation_report}`; `PRECONDITION_REQUIRED` → `{required_header: "If-Match"}`). Nunca vazio de significado nem dump livre.
- **Nunca** em qualquer campo: stack trace, SQL, hostnames internos, JWT, XML bruto, `repr` de exceção.
- `message`: pt-BR segura; `code`: estável em inglês (machine-readable).
- **Framework normalization `FROZEN`:** erros `422` nativos do FastAPI/pydantic são convertidos ao envelope (`code = "INVALID_REQUEST"`, `details.issues` = lista de field errors) — o formato default `{"detail": [...]}` **não** vaza para o cliente.

| Application error (P2) | HTTP | wire code | Safe detail | Retry policy |
|---|---|---|---|---|
| `MODEL_NOT_FOUND` | 404 | `MODEL_NOT_FOUND` | nenhum | read: seguro repetir |
| `REVISION_NOT_FOUND` | 404 | `REVISION_NOT_FOUND` | nenhum | seguro |
| `REVISION_OWNERSHIP_MISMATCH` | 404 | `REVISION_NOT_FOUND` | **normalizado** — nunca vaza existência do recurso em outro model | seguro |
| `MODEL_ARCHIVED` | 409 | `MODEL_ARCHIVED` | `{archived_at}` | usuário decide unarchive |
| `INVALID_DISPLAY_NAME` | 422 | `INVALID_DISPLAY_NAME` | `{constraint}` | corrigir input |
| `CONFLICT` (If-Match stale) | 412 | `CONFLICT` | `{current_version}` | reload + re-save manual; nunca auto-retry |
| `NO_CHANGES` | 409 | `NO_CHANGES` | nenhum | não retentar |
| `VALIDATION_BLOCKED` | 422 | `VALIDATION_BLOCKED` | `{recognition_state, validation_report}` estruturado | corrigir artefato |
| `UNAUTHORIZED_OPERATION` | 403 | `UNAUTHORIZED_OPERATION` | `{required_permission}` | não retentar sem grant |
| `OUTCOME_VERIFICATION_FAILED` | 500 | `OUTCOME_VERIFICATION_FAILED` | `{hint: "read_authoritative_first"}` | **nunca** auto-retry do write; GET autoritativo antes |
| `INFRASTRUCTURE_FAILURE` | 503 | `INFRASTRUCTURE_FAILURE` | nenhum | writes: resultado incerto → re-read antes de retentar; reads: retry seguro |

Erros de transporte (`PRECONDITION_REQUIRED` 428, `INVALID_REQUEST` 400/415, `PAYLOAD_TOO_LARGE` 413, `RATE_LIMITED` 429) usam o mesmo envelope com seus próprios codes.

## 15. Media types

`FROZEN` por endpoint:

| Endpoint | Request | Response |
|---|---|---|
| `/models` POST, `PATCH`, duplicate, archive, unarchive, revisions POST/restore | `application/json` (ou vazio) | `application/json` |
| `GET .../working-copy`, `PUT .../working-copy`, `.../validate` | `application/xml; charset=utf-8` | `application/xml; charset=utf-8` (GET) / `application/json` (PUT/validate) |
| `GET .../export` (WC e revision) | — | `application/xml; charset=utf-8` + `Content-Disposition: attachment` |
| `/models/import`, `/imports/inspect` | `multipart/form-data` | `application/json` |
| demais GETs | — | `application/json` |

- Nenhum MIME proprietário `*.bpmn` inventado — `application/xml; charset=utf-8` é o tipo congelado para artefatos `.bpmn` (segurança nunca depende da extensão).

## 16. Export / filename contract

`FROZEN`:

- `Content-Type: application/xml; charset=utf-8`, `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff` — nunca renderização HTML do XML.
- Conteúdo = bytes canônicos exatos (working copy ou snapshot da revision). Zero resserialização.
- Headers `filename=` + `filename*=UTF-8''` (RFC 5987) derivados do `display_name` **sanitizado**:

```text
1. remove chars proibidos:  / \ : * ? " < > |  e controles 0x00–0x1F, 0x7F
2. colapsa whitespace, trim de espaços/pontos nas pontas (Windows-reserved)
3. trunca a 100 chars
4. vazio → "model" (working copy) | "revision" (revision)
5. working copy:  <san>.bpmn
   revision:      <san>-rev-<revision_number>.bpmn
6. filename  = versão ASCII (non-ASCII → "_")
   filename* = versão UTF-8 percent-encoded (acentos preservados)
```

- Filename é **derivado**, nunca metadata canônica; header injection impossível por construção (CR/LF removidos no passo 1).
- **SVG/PNG export (P1 `CAP-OUT-001/002`)**: derivados client-side gerados do canvas do editor (`OUT_OF_V1` para o backend por design) — **nenhum** endpoint de export SVG/PNG existe ou é necessário; contrato congelado é "sem transporte".

## 17. Request ID & cache contract

`FROZEN`:

- `X-Request-ID`: response header presente em **toda** resposta (sucesso e erro). Cliente pode enviar `X-Request-ID`; se casar `^[A-Za-z0-9._-]{1,128}$` é preservado/ecoado; caso contrário o servidor gera `uuid4`.
- `meta.request_id` presente em todo `ErrorResponse`; mesmo valor nos logs estruturados (correlação ponta-a-ponta).
- `Cache-Control: no-store` em todas as respostas da API (artefatos e metadata contêm informação corporativa; nenhuma resposta é cacheável publicamente). Sem `ETag` de cache-conditional em GETs — `ETag` existe apenas como token de concorrência, não para `If-None-Match` caching.

## 18. Pagination contract

`FROZEN` — decisão final (delegação P2/P6 resolvida): **offset page-based**.

| Param | Tipo | Default | Bound | Violation |
|---|---|---|---|---|
| `page` | int | `1` | `>= 1` | 422 `INVALID_REQUEST` |
| `page_size` | int | `25` | `1..100` | 422 `INVALID_REQUEST` |

- `has_more` computado por fetch `page_size+1` (descarta o extra); **sem `total_count`** (não requerido; evita COUNT caro).
- `next_page` implícito (`page+1` quando `has_more`); cursor encoding não existe na V1.
- Nenhuma listagem ilimitada — `page_size` sempre bounded.

### 18.1 Models list query

`GET /models?query=&archived=&sort=&direction=&page=&page_size=`:

| Param | Enum/Type | Default |
|---|---|---|
| `query` | string (max 120) | — |
| `archived` | `active` \| `archived` \| `all` | `active` |
| `sort` | `updated_at` \| `created_at` \| `display_name` | `updated_at` |
| `direction` | `asc` \| `desc` | `desc` |

Sort desce ao SQL via allowlist mapping (P6 §5.5) + `id` tie-breaker; `query` parametrizado (contains por `lower(display_name)`, UUID-exact quando parseável).

### 18.2 Revisions list

`GET .../revisions?page=&page_size=` — mesmo mecanismo; sort fixo `revision_number DESC`; índice `idx_revisions_model` cobre. Nunca retorna histórico inteiro.

### 18.3 Index impact

`FROZEN`: **no additional pagination index required** — `idx_models_list (archived_at, updated_at DESC)` cobre o default sort; `idx_models_name_lower` cobre sort por nome; `created_at` sort tolera seq scan no volume V1 (catálogo modesto, page_size ≤ 100); `idx_revisions_model` cobre revisions. Autorização P6 §5.4 exercida: nenhum índice novo.

## 19. Idempotency & retry contract

`FROZEN`:

- **`Idempotency-Key`: `OUT_OF_V1`** — não existe ledger de idempotência no schema (P6 não criou; não se inventa persistência). Não há idempotência falsa em memória.
- **Frontend nunca auto-retenta writes.** Em resultado incerto (timeout/network/5xx pós-envio): UI mostra estado indeterminado → re-read autoritativo (`GET`) antes de qualquer retry manual. Especialmente `CreateModel`/`ImportModel`/`DuplicateModel` (retry cria agregado duplicado — mitigação V1: ação desabilitada durante in-flight + read-back; aceito sem ledger).
- Reads (`GET`) podem auto-retry (idempotentes por natureza).
- Mutations de agregado existente são naturalmente protegidas: `If-Match` stale → `412`, retry inofensivo.
- `429`: UI apresenta estado "muitas requisições", respeita `Retry-After` quando presente; nunca mapear para erro de validação.

## 20. OpenAPI contract

`FROZEN`:

| Propriedade | Valor |
|---|---|
| Fonte | gerado pelo FastAPI do código HTTP (sem spec paralela manual) |
| OpenAPI version | `3.1.x` (saída nativa do FastAPI) |
| `info.title` | `BPMN Modeler API` |
| `info.version` | `1.0.0` |
| `servers` | `[{"url": "/apps/bpmn-modeler-api"}]` |
| Security scheme | `bearerAuth` — `type: http, scheme: bearer, bearerFormat: JWT` |
| `/health`, `/ready` | `security: []` (públicas — marcadas explicitamente) |
| Permission docs | cada operation documenta `x-required-permission: "bpmn-modeler.view|edit|manage"` (extensão OpenAPI — Core RBAC não é OAuth scope; não fingir scope) |
| `operationId`s | explícitos, estáveis, camelCase — nunca gerados por path/função |
| `docs`/`redoc` | **desabilitados** (`docs_url=None`, `redoc_url=None`) em todo ambiente |
| `/openapi.json` | habilitado (insumo CI); sem conteúdo sensível além do contrato |

### 20.1 operationIds (exatos)

```text
health, ready,
listModels, createModel, importModel, inspectImport,
getModel, renameModel, duplicateModel, archiveModel, unarchiveModel,
getWorkingCopy, saveWorkingCopy, validateWorkingCopy, exportWorkingCopy,
listRevisions, createRevision, getRevision, restoreRevision, exportRevision
```

**20 operations** no schema.

### 20.2 Examples mínimos obrigatórios

`CreateModel`, `ListModels`, `SaveWorkingCopy`, `ValidationReport`, `ImportInspection`, `CONFLICT`, `VALIDATION_BLOCKED`, `CreateRevision`, `RestoreRevision` — fixtures mínimas, sem XML gigante.

## 21. Health / Ready wire contract

`FROZEN`:

| Endpoint | Status | Body |
|---|---|---|
| `GET /health` | `200` | `{ "status": "ok" }` |
| `GET /ready` | `200` | `{ "status": "ready", "checks": {"database": true, "xsd_bundle": true, "schema": true} }` |
| | `503` | `{ "status": "not_ready", "checks": {...true/false...} }` |

- Nunca expõe internals: sem hostname/DSN, sem versões de migração detalhadas, sem stack. `checks` booleanos apenas.
- Ambas públicas (única exceção AuthN da superfície).

## 22. Frontend ↔ API matrix (final audit)

`FROZEN` — toda ação de UI tem endpoint suficiente; nenhum botão depende de endpoint inexistente:

| UI action | Endpoint | Suficiência |
|---|---|---|
| Library list/search/sort/page | `GET /models` | query+archived+sort+direction+page cobertos |
| Create | `POST /models` | display_name |
| Import inspect | `POST /imports/inspect` | recognition+issues+eligible |
| Import create | `POST /models/import` | re-valida e cria |
| Open (editor) | `GET /models/{id}` + `GET .../working-copy` | metadata + XML + ETag + sha |
| Save | `PUT .../working-copy` + `GET` read-back | §8.1 |
| Validate | `POST .../working-copy/validate` | candidate report |
| Rename | `PATCH` + If-Match | — |
| Duplicate | `POST .../duplicate` | — |
| Archive/Unarchive | `POST` actions + If-Match | — |
| History | `GET .../revisions` | paginado |
| Revision view | `GET .../revisions/{n}` + `.../export` | metadata + XML read-only |
| Create revision | `POST .../revisions` + If-Match | — |
| Restore | `POST .../restore` + If-Match + confirm UX | — |
| Export | `GET .../export` | canonical bytes + filename seguro |

**Backend audit `FROZEN`:** toda rota business delega ao use case autoritativo (P2); nenhuma rota escreve repository diretamente, reconstrói policy no handler, bypassa validation ou AuthZ.

**Security audit `FROZEN`:** toda rota exceto health/ready exige `bearerAuth` + permission do mapa §6; uploads obedecem `MAX_INPUT_BYTES`/intake evidence; downloads carregam `nosniff`+`attachment`+filename sanitizado.

## 23. E2E architecture

`FROZEN`:

| Camada | Ferramenta | Justificativa |
|---|---|---|
| HTTP contract/integration tests | `pytest` + `httpx`/`TestClient` (convenção repo) | cobre toda a matriz rota/status/erro sem browser |
| Browser E2E | **Playwright** — `@playwright/test@1.62.1` (única framework; Node 20) | jornadas de editor/canvas/SVG/worker impossíveis por HTTP |
| Deployment smoke | `curl` `/health`+`/ready` via compose | convenção monorepo |

- Playwright é **introdução nova e única** — proibido segundo framework E2E.
- Stack E2E mínima: gateway + portal/MFE + `bpmn-modeler-api` + database `bpmn_modeler` efêmero + Keycloak/test identity + Core RBAC test permissions. **Não** mockar justamente os boundaries que o E2E prova.
- Data isolation: cada suite cria seus próprios models; sem IDs hardcoded; cleanup por database/container efêmero destruído pós-suite (hard delete não existe na API — nunca adicionar endpoint de delete para testes).

## 24. E2E actor matrix

`FROZEN` — identidades de teste provam a permission matrix real:

| Actor | Grants | Prova |
|---|---|---|
| viewer | `bpmn-modeler.view` | lê/exporta; write → 403 |
| editor | `view`+`edit` | create/save/import/validate; manage → 403 |
| manager | `view`+`edit`+`manage` | rename/duplicate/archive/restore |
| authenticated-no-permission | nenhuma | qualquer rota business → 403 |
| unauthenticated | — | qualquer rota → 401 |

## 25. Mandatory E2E journeys

`FROZEN` — IDs `E2E-*` (referência para acceptance matrix):

| ID | Jornada | Prova |
|---|---|---|
| E2E-01 | create→open blank→create elementos suportados→save→authoritative reload→reopen→export | canonical persistence, dirty state, ETag/version, read-back |
| E2E-02 | inspect→import BPMN válido+DI→open→export | sem normalização destrutiva (P3) |
| E2E-03 | edit→save→reopen→round-trip | preservation pós-edição |
| E2E-04 | import sem DI→transient render→DIRTY false→save sem edição persiste **sem** DI | transient DI nunca canônica |
| E2E-05 | Organizar→Preview→Cancel→estado idêntico | cancel neutro |
| E2E-06 | Organizar→Accept→DIRTY→undo→redo→Save→reopen DI persistida | one logical undo batch |
| E2E-07 | import BPMN com issue estrutural→issues visíveis→navegação→repair→save→revalidate→issue some | repair não bloqueado |
| E2E-08 | inspect malformed→`MALFORMED_XML`→import blocked→nenhum Model | ≠ `NON_XML` |
| E2E-09 | oversized/DOCTYPE/external entity/expansion→`INPUT_REJECTED_SECURITY`→nada escrito→sem rede | input safety |
| E2E-10 | `mustUnderstand=false`→import→edit seguro→save→reopen→extensão preservada | extension policy |
| E2E-11 | `mustUnderstand=true` não suportado→open read-only→banner persistente→save indisponível→export/revision permitidos | capability gate |
| E2E-12 | save→create rev #1→edit+save→create rev #2→open #1 read-only→export #1→restore #1→rev #3 origin=restore→WC==#1→#1/#2 intactas | append-only |
| E2E-13 | create revision 2× seguidas→`NO_CHANGES`→nada appended→version inalterada | rejeição |
| E2E-14 | archive→version bump→read-only→export/history ok→save/rename/revision/restore bloqueados→duplicate ok→unarchive→editable | lifecycle |
| E2E-15 | rename mesmo nome / save idêntico / archive já arquivado / unarchive ativo / restore artefato corrente | `changed=false`, version inalterada |
| E2E-16 | dois clients N→A escreve N+1→B com token stale→`CONFLICT`→B exporta local/reload—sem force overwrite | concurrency UX |
| E2E-17 | simular read-back divergente→`OUTCOME_VERIFICATION_FAILED`→sem success UI→sem re-write automático→read autoritativo | verification gate |
| E2E-18 | multi-BPMNDiagram→seletor→abrir cada→organizar ativo→Accept→save→reopen→demais diagramas preservados | multi-diagram |
| E2E-19 | layout representativo: pools/lanes, subprocess, boundary events, message flows | L-gates (unit cobre L01–L16 completos) |
| E2E-20 | auth: no token→401; expired→401; sem permissão→403; viewer/editor/manager | auth matrix |
| E2E-21 | accessibility smoke: keyboard shell, focus visível, toolbar names, validation list navegável por teclado, dialog focus trap/restore, status não color-only | a11y smoke (não certificação WCAG) |
| E2E-22 | tablet breakpoint→viewer read-only→sem mutation controls→pan/zoom/search/export/history | device scope |

Integration-level (não-browser): DB least-privilege grants (§26.3), migration flow efêmero (§26.4), XSD offline (§26.5), export contract (§26.6).

## 26. API contract test matrix

`FROZEN` — HTTP contract tests (pytest) cobrem **toda** a matriz §5/§13/§14 sem browser:

| Bloco | Cobertura |
|---|---|
| Rotas×status | todo route map com happy + cada status da tabela aplicável |
| Precondition | missing `If-Match`→428; stale→412; malformado→400 |
| Envelope | todo erro casa `ErrorResponse` (incl. 422 de framework) |
| Media types | 415 em content-type errado; XML exato em GET/export |
| Auth | 401/403 por rota×actor |
| Pagination | bounds, defaults, `has_more` |
| Headers | `ETag`, `X-Artifact-SHA256`, `X-Request-ID`, `Cache-Control`, `Content-Disposition` |

### 26.1 OpenAPI contract test (CI)

Schema gerado e verificado por invariantes (não diff byte-a-byte): 20 operations, operationIds únicos/estáveis, `bearerAuth` em todas exceto health/ready, `x-required-permission` correto por operação, content types por endpoint, error schema único, nenhuma write sem UC.

### 26.2 OpenAPI examples

Os exemplos mínimos de §20.2 presentes no schema.

### 26.3 DB least-privilege (integration)

PASS: `SELECT/INSERT/UPDATE models`, `SELECT/INSERT revisions`. FAIL: `UPDATE revisions`, `DELETE` (ambas), `SELECT schema_migrations`, `CREATE TABLE`, `ALTER TABLE`, acesso a outro database.

### 26.4 Migration flow (integration)

Ephemeral DB: bootstrap→migration job(admin)→verify schema/grants/checksum→start API app-only→`/ready` 200. Sem admin creds no processo API.

### 26.5 XSD offline (integration)

Rede indisponível→validator inicializa do bundle vendored→validação funciona. Checksum divergente→startup/deploy falha.

### 26.6 Export (integration)

Bytes exatos = canônico; filename sanitizado; `Content-Disposition`; `application/xml`; `nosniff`; WC e revision.

## 27. Use case acceptance matrix

`FROZEN` — 17/17 com prova planejada (status `TEST_NOT_RUN` até implementação):

| UC | Route | Perm | Happy | Failure | Read-back/postcondition |
|---|---|---|---|---|---|
| UC-MODEL-001 | POST /models | edit | E2E-01 | 403/422 | get: version=1, blank artifact |
| UC-MODEL-002 | POST /models/import | edit | E2E-02 | 413/422/403 | checksum==sha256(input) |
| UC-MODEL-003 | GET /models/{id} | view | contract | 404/403/401 | metadata fiel |
| UC-MODEL-004 | GET /models | view | contract+E2E library | 403 | filtros/sort/paginação |
| UC-MODEL-005 | PATCH /models/{id} | manage | contract | 412/428/404/409/422 | name+version+1 |
| UC-MODEL-006 | POST .../duplicate | manage+view | contract | 404/403 | checksum(novo)==origem |
| UC-MODEL-007 | POST .../archive | manage | E2E-14 | 412/404 | archived_at set |
| UC-MODEL-008 | POST .../unarchive | manage | E2E-14 | 412/404 | archived_at null |
| UC-WC-001 | GET .../working-copy | view | contract | 404 | bytes exatos+ETag+sha |
| UC-WC-002 | PUT .../working-copy | edit | E2E-01/03 | 412/422/413/403 | checksum==sha256(input), version+1 |
| UC-WC-003 | GET .../export | view | E2E-01 | 404 | canonical bytes+filename seguro |
| UC-WC-004 | POST .../validate | view | E2E-07 | 400/404/413 | report, zero write |
| UC-REV-001 | GET .../revisions | view | contract | 404 | paginado desc |
| UC-REV-002 | GET .../revisions/{n} | view | contract | 404 | metadata+identidade |
| UC-REV-003 | POST .../revisions | manage | E2E-12 | 409/412/409-arch | append revisão relida íntegra |
| UC-REV-004 | POST .../restore | manage | E2E-12 | 404/412/409 | WC==#N, nova rev origin=restore |
| UC-REV-005 | GET .../revisions/{n}/export | view | E2E-12 | 404 | snapshot bytes exatos |

## 28. BPMN validation acceptance

`FROZEN`: as **47 regras** do catálogo Prompt 3 têm 100% de fixture-mapping exigido na implementação. Este documento **referencia, não recria** o catálogo. Acceptance exige execução da matriz de fixtures P3 (incl. FX-SEC-*, FX-BADXML-*, FX-NS-*, FX-NODI-*, FX-EXT-*) — status `TEST_NOT_RUN`.

## 29. Editor acceptance

`FROZEN`: todo construct `CREATE_EDIT`/`RENDER_PRESERVE_ONLY` do profile (P1/P3) ligado a frontend integration fixtures — referência às matrizes existentes, sem re-listar. Journey E2E-01/03 cobre o caminho feliz de edição; suíte de integração do adapter cobre o profile completo — `TEST_NOT_RUN`.

## 30. Layout acceptance

`FROZEN`: L01–L16 100% mapeados — hard gates do Prompt 5 permanecem (determinismo, semantic immutability, pools/lanes/subprocess/boundary/message flows, partial DI, preview/accept/cancel, undo único). E2E-19 é a prova browser representativa; adapter unit tests cobrem o restante. Timeout hard `30_000ms` (P6) — não é performance target; acceptance = fixtures completam antes do timeout no ambiente E2E; runtime medido por fixture registrado na implementação (TARGET futuro com evidência, não agora) — `TEST_NOT_RUN`.

## 31. Security acceptance

`FROZEN`: T01–T18 100% mapeados → nível apropriado (unit/integration/E2E/CI gate conforme P6 §12) — `TEST_NOT_RUN`. Auth matrix = E2E-20; grants = §26.3; input safety = E2E-09; worker/CSP = E2E-19 + contract tests.

## 32. Migration / grant acceptance

`FROZEN`: §26.3 + §26.4 = prova de least privilege e de fluxo separado de migration (admin fora do processo API) — `TEST_NOT_RUN`.

## 33. Accessibility / device acceptance

`FROZEN`: E2E-21 (a11y smoke) + E2E-22 (tablet read-only) — `TEST_NOT_RUN`.

## 34. Traceability matrix

`FROZEN` — forma exigida; todas as linhas `STATUS = TEST_NOT_RUN`:

| REQ_ID | SOURCE FREEZE | FEATURE/RULE/UC | IMPLEMENTATION SURFACE | TEST LEVEL | EVIDENCE | STATUS |
|---|---|---|---|---|---|---|
| R-UC-* (17) | P2 | cada UC | route §5 | contract+E2E §25/§27 | matrix row | TEST_NOT_RUN |
| R-VAL-47 | P3 | 47 regras | validation adapter | fixture suite | FX-* | TEST_NOT_RUN |
| R-PROFILE | P1/P3 | editing profile | editor adapter | integration fixtures | construct×fixture | TEST_NOT_RUN |
| R-LAYOUT-01..16 | P5 | L01–L16 | layout adapter/worker | unit+E2E-19 | hard gates | TEST_NOT_RUN |
| R-SEC-01..18 | P6 | T01–T18 | full stack | unit/int/E2E/CI | threat controls | TEST_NOT_RUN |
| R-TRANSPORT | P7 | route map/ETag/envelope/media/pagination | HTTP layer | contract tests §26 | matrix | TEST_NOT_RUN |
| R-DB | P6 | schema/grants/migrations | persistence | §26.3/§26.4 | grants+migration | TEST_NOT_RUN |
| R-A11Y/DEV | P1/P4 | a11y+tablet | MFE | E2E-21/22 | smoke | TEST_NOT_RUN |

## 35. Final feature matrix

`FROZEN` — revisão do P1: nenhum item `IN_V1` ficou sem implementation/test contract; `OUT_OF_V1`/`FUTURE` permanecem inalterados. Nenhum feature IN_V1 órfão detectado → gate PASS.

## 36. Cross-document consistency audit

`FROZEN` — verificado nos 7 docs:

| Topic | Source A | Source B | Consistent? | Correction |
|---|---|---|---|---|
| SAVE ≠ REVISION | P2 | P4/P7 | ✅ | — |
| revision numbering | P2 | P6/P7 (selector=number) | ✅ | — |
| version semantics | P2 | P6 CAS / P7 ETag | ✅ | wire = `"v"+version` |
| archived policy | P2 | P6/P7 (no delete, mutations 409) | ✅ | — |
| validation operation policy | P3 | P7 (import/validate/import-create) | ✅ | — |
| `MALFORMED_XML`/`NON_XML` | P3 | P6/P7 | ✅ | corrigido no gate P6 |
| BPMN namespaces | P3 | P6 | ✅ | 20100524 final / 20100501 XSD paths |
| mustUnderstand | P3 | P4/P7 (E2E-10/11) | ✅ | — |
| BPMN without DI | P3/P5 | P7 (E2E-04) | ✅ | — |
| read-only reasons | P4 | P7 (archived/mustUnderstand/tablet) | ✅ | — |
| multiple diagrams | P4 | P7 (E2E-18) | ✅ | — |
| layout preview | P5 | P7 (E2E-05/06) | ✅ | — |
| database ownership | P6 | P7 | ✅ | dedicated db+roles |
| permissions | P6 | P7 (x-required-permission) | ✅ | — |
| dependencies | P6 | P7 (peer graph) | ✅ | PASS |
| migration flow | P6 | P7 (§26.4) | ✅ | separate step |
| API routes | P7 | P2 (17 UCs) | ✅ | 17/17 |
| ValidateWorkingCopy input | P2↔P4 | P7 §3.1 | ✅ | clarificação aplicada em P2 |

**Implementation-critical contradictions: NONE.**

## 37. Residual decision audit

`FROZEN` — busca nos 7 documentos por `TODO`/`TBD`/`maybe`/`perhaps`/`talvez`/`a decidir`/`probably`/`implementation decides`/`TO_INVENTORY`/`DELEGATED_TO_PROMPT_*`/`expected_version`/`ETag`/`If-Match`/`pagination`/`idempotency`/`retry`:

- Toda delegação `DELEGATED_TO_PROMPT_7` está **resolvida neste documento** (paginação §18, idempotência §19, transport/wire §5–§17, benchmark de layout §30).
- Wording de delegações históricas em P2/P5/P6 atualizado para apontar a este documento (edições mínimas §38 — ver abaixo; se marcador residual permanecer, lê-se como "resolvido por API-E2E-ACCEPTANCE-SPEC-FREEZE").
- `TO_INVENTORY`: nenhum remanescente implementation-critical.
- `expected_version`: autoridade domain (P2) preservada; wire = `If-Match` — documentado §12.
- **Implementation-critical unresolved questions: NONE.**

## 38. Implementation sequence

`FROZEN` — ordem lógica recomendada para o Master Prompt (não reabre design):

```text
1. migrations/bootstrap contract (db, roles, grants, V001)
2. backend Domain/Application completion
3. repository + validation adapters (lxml, XSD bundle, intake evidence)
4. HTTP/OpenAPI layer (routes, envelope, ETag, pagination)
5. frontend plugin shell + federation
6. bpmn-js adapter/editor
7. validation UI
8. revisions/library UI
9. layout adapter + ELK worker
10. integration/security wiring (auth, headers, rate zone, compose)
11. fixtures/tests (P3 catalog + contract + grants)
12. E2E (Playwright journeys §25)
13. runtime/deploy verification (health/ready, smoke)
```

## 39. Test pyramid

`FROZEN` — responsabilidades distribuídas (não "tudo por E2E"):

```text
Domain unit | Application unit | Validation fixture suite | Repository integration |
HTTP contract | Frontend unit/component | Editor integration | Layout adapter |
Security/grants integration | Browser E2E (§25) | Deployment smoke
```

## 40. Definition of Done — V1 implementation

`FROZEN` — implementação só é `PASS` quando **todas** as condições:

- 17 use cases implementados e cobertos;
- API/OpenAPI conforme este freeze (incl. 20 operations, envelope único, ETag, paginação);
- canonical XML/DI persistence comprovada (round-trip byte-exato quando exigido);
- toda a matriz de fixtures BPMN (47 regras) passa;
- jornadas de editor passam (P4);
- preservation tests passam (P3);
- revision tests passam (P2);
- layout hard gates L01–L16 passam (P5);
- security/AuthZ tests passam (P6/P7);
- grant tests passam (§26.3);
- migrations + checksum + grants passam (§26.4);
- OpenAPI contract invariants passam (§26.1);
- E2E journeys E2E-01..22 passam;
- read-back verification comprovada em todo write;
- deployment smoke passa (`/health`+`/ready`);
- residual search limpa;
- **nenhum** gap implementation-critical restante.

## 41. Final specification status

```text
V1 SPECIFICATION FREEZE:
FROZEN

IMPLEMENTATION STATUS:
NOT IMPLEMENTED

RUNTIME ACCEPTANCE:
TEST_NOT_RUN

DEPLOYMENT ACCEPTANCE:
TEST_NOT_RUN
```

Specification freeze ≠ implementation pass — documentação fechada não implica software pronto.

## 42. Master Prompt readiness

```text
MASTER IMPLEMENTATION PROMPT READINESS:
READY
```

Significado: zero itens implementation-blocking indecisos — **não** software pronto. O Master Implementation Prompt implementa exatamente os sete freezes: do not redesign, do not substitute libraries, do not change schema, do not change permissions, do not simplify BPMN scope, do not invent endpoint, do not create second source of truth. Contradição real descoberta na implementação → `EXECUTION_DRIFT` na parte afetada; partes não bloqueadas continuam.
