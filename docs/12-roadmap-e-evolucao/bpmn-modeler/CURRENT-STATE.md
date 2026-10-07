# BPMN MODELER — CURRENT STATE (pós-implementação)

> **Status:** CURRENT (G0 — Documentation Drift Reconciliation)
> **Baseline de evidência:** commit `3efdb7e2` (`main`), out/2026 — auditado contra `bpmn-modeler/`, `plugins/bpmn-modeler/`, `migrations/`, testes, CI e acceptance de runtime.
> **Natureza:** **fonte vigente** de estado implementado. Os `*-SPEC-FREEZE.md` são o registro histórico de decisões de especificação; onde uma decisão foi substituída após implementação, o freeze carrega marcação `SUPERSEDED (G0)` inline e a divergência está registrada em [`DOCUMENTATION-DRIFT-LEDGER.md`](DOCUMENTATION-DRIFT-LEDGER.md).
> **Regra de leitura:** este documento **não** autoriza features novas e **não** promove targets de escopo a implementação. `SPECIFICATION STATUS` (o que a V1 promete) e `EXECUTION STATUS` (o que está provado) são sempre separados.

---

## 1. Autoridade canônica e bounded context

| Conceito | Fonte canônica vigente |
|---|---|
| Artefato BPMN canônico | BPMN 2.0 XML + BPMN-DI no mesmo documento, persistido pelo backend (`WorkingCopy` + `Revision`) |
| JSON visual paralelo (`flowchart_v1`, moddle JSON, DI separado) | proibido como fonte canônica — invariante preservada |
| Identidade / SSO | Keycloak (`delpi_auth`, `validate_token`) |
| RBAC / permissões efetivas | Core API (`/me`, `user_permissions`, `rbac.manage`) |
| Resource authority dos modelos | BPMN Modeler — `Model.created_by` |
| Transformômetro | contexto externo; `flowchart_v1` = legado; integração profunda = `FUTURE` |

Bounded context: `bpmn-modeler/` (package `bpmn_modeler`) + MFE `plugins/bpmn-modeler/` (Module Federation via portal).

## 2. Arquitetura implementada

```text
domain      → entities/value objects (Model aggregate, Revision imutável,
              WorkingCopy, CanonicalBpmnArtifact opaco)
application → ports + use cases (17 UCs) + errors + policy + validation contract
infrastructure → persistence (psycopg, repository, migrations runner,
              connection) + validation engine (lxml + XSD vendored +
              regras custom) + intake (InputSafetyEvidence)
interface   → FastAPI routes + schemas + auth (CallerIdentity) + ETag + envelope
```

Enforcement: `tests/test_architecture.py` + gate CI "camadas limpas" (`domain`/`application` sem imports de fastapi/lxml/psycopg). **PROVEN.**

## 3. Ownership / autorização de recurso (P0 — CLOSED)

Contrato vigente (substitui o baseline "context-wide only" do freeze de segurança):

```text
authenticated principal (Bearer + delpi_auth)
AND required Core RBAC permission (view/edit/manage)
AND CallerIdentity.subject == Model.created_by   → para acesso ao recurso
```

- `Model.created_by` = resource owner V1; atribuído server-side no create/import/duplicate (`caller.subject`).
- `BpmnModelerService._get_owned_or_404` fecha **todos** os caminhos single-model: GET, working-copy read/write/validate/export, revisions (list/get/create/restore/export), rename/duplicate/archive/unarchive.
- `ModelRepositoryPort.list_summaries(owner_subject=…)` — contrato **fail-closed**: não existe caminho de listagem global; `WHERE created_by = owner_subject` no SQL; índice `idx_models_owner_list` (V004).
- Foreign resource → `404 MODEL_NOT_FOUND` (nunca `403` após o gate RBAC; nunca `MODEL_ARCHIVED` para foreign; nenhum metadata/artifact/checksum vaza).
- `is_superadmin=true` concede as três capabilities `bpmn-modeler.*` (RBAC), **mas não atravessa** `created_by` — ownership é invariante de aplicação, provado bilateralmente em runtime.
- Duplicação de resource de outro owner → 404 e **não cria** cópia (prova por conjunto de ids antes/depois).
- `REVISION_OWNERSHIP_MISMATCH` (revisão de outro Model) continua normalizado para `REVISION_NOT_FOUND`.

**Runtime acceptance (P0):** 57/57 checks + closure 18/18 com identidades reais governadas (incl. superadmin real). `PUBLIC UNSCOPED ACCESS: 0`, `CROSS-OWNER ACCESS: 0`, `SUPERADMIN CROSS-OWNER: 0`. Status: **CLOSED — não reabrir sem nova evidência.**

## 4. Autosave do Working Copy (contrato vigente)

**Substitui o baseline "autosave OUT_OF_V1" do freeze.** Estado vigente:

```text
edit (commandStack.changed)
  → SaveMachine: branch-aware state tokens → DIRTY
  → AutosaveController: debounce 1500ms + coalescing + single-flight
  → WRITE (PUT working-copy, If-Match version)
  → AUTHORITATIVE READ-BACK → VERIFY (bytes exatos)
  → CLEAN / SAVED
```

- Implementação: `plugins/bpmn-modeler/src/state/autosave.ts` + `saveMachine.ts`; wiring em `ModelEditorPage.tsx` (`notifyCommand`, `flush`, navigation guard).
- **AUTOSAVE ≠ REVISION** — autosave só grava working copy; revision continua checkpoint explícito e governado (MANAGE).
- `Ctrl/Cmd+S` = flush imediato (não é o único caminho); "Tentar novamente" reaparece em `SAVE_FAILED`/`OFFLINE`.
- Falhas classificadas: rede→`OFFLINE` (retry no `online`), 401→refresh via host + 1 retry→`SESSION_EXPIRED`, 403→`READ_ONLY` (fail closed), `CONFLICT`→dialog (sem merge), `VALIDATION_BLOCKED`→DIRTY + painel.
- "Salvo" só após read-back verificado; edições in-flight durante write voltam a DIRTY (token `pendingSaveToken`).
- Guards: navigation guard faz flush antes de navegar; `beforeunload` só em estado inseguro.
- Evidência: `autosave.test.ts` + `saveMachine.test.ts` (unit), `e2e/specs/autosave-auth.spec.ts` (AUTO-*/AUTH-*/NAV-*/UNLOAD-*/REV-*). **PROVEN.**

## 5. Revision contract (vigente)

- `Revision` imutável, append-only; restore cria **nova** revisão `origin=restore` + working copy replace na mesma transação — história nunca reescrita.
- **Metadata de revisão é vigente** (emenda pós-freeze): `name` (≤120), `description` (≤500), `created_by_name`, além de `revision_number`, `revision_id`, `origin`, `created_at`, `created_by`, `artifact_sha256`.
- Evidência: migrations `V002__add_revision_provenance` + `V003__add_revision_metadata`, domain `Revision`, `CreateRevisionRequest`/`RevisionSummaryResponse`, `CreateRevisionDialog` (frontend), `test_revision_immutability.py`, `revisions-metadata.spec.ts`. **PROVEN.**
- Claim histórico "POST /revisions sem body / sem label" = SUPERSEDED: body opcional `{name?, description?}` aceito; ausência continua válida.

## 6. Validação e interoperabilidade (vigente)

- Pipeline: intake (`InputSafetyEvidence`: bytes, charset, doctype/XXE, limites) → `lxml` parse → XSD vendored (offline, sem `schemaLocation` fetch; `MANIFEST.json` com checksums — gate CI) → regras custom (`BPMN-STRUCT-*`, `BPMN-SEM-*`, `BPMNDI-*`, `PROD-*`).
- `ValidationReport` = evidência; save é gate por operation policy (`VALIDATION_BLOCKED`); create revision não bloqueia.
- `mustUnderstand=true` não suportado → open/read-only ALLOW, edit DISABLED, save BLOCKED.
- Preservação: edição/save preservam constructs desconhecidos; falha de preservação bloqueia write destrutivo.
- Evidência: `test_validation_contract.py`, `test_validation_engine.py`, fixtures FX-*.

## 7. Layout / BPMN-DI (vigente)

- ELK (`elkjs`) executa **exclusivamente em Web Worker** (`layout.worker.ts` via `workerFactory`); **não existe fallback main thread** — worker indisponível/falha/timeout → `LAYOUT_FAILED`/`LAYOUT_TIMEOUT`/`LAYOUT_CANCELLED` e canvas principal permanece intacto. Gate CI "worker-only" prova.
- Fluxo: `Organizar` → grafo ELK (`elkGraph.ts`) → `runLayout` → proposta DI (`diProposal.ts`) → **preview em `NavigatedViewer` separado** (canvas principal intocado; banner "nada foi alterado").
- **ACCEPT** = `applyDiLayout` = UM comando lógico no command stack → DIRTY → **autosave pode persistir**; undo reverte o batch. **CANCEL** = preview destruído, zero write canônico.
- O gesto explícito obrigatório é **Accept/Cancel**; não existe write de geometria sem Accept, mas o persist após Accept é o autosave (não um clique "Salvar" obrigatório).
- BPMN sem DI: DI transitório calculado/injetado só para render no open (não persiste); edições produzem DI pelo serializer do vendor.
- Evidência: `diProposal.test.ts`, `layout-*.spec.ts` E2E, gates CI. **PROVEN** para o mecanismo; cobertura de constructs G1.

## 8. Editor / vendor boundary (vigente)

- `BpmnEditorAdapter` = única superfície React↔vendor (`src/editor/`); vendor leakage gate no CI.
- `Modeler` (bpmn-js 18.30.1) + `BpmnPropertiesPanelModule`/`BpmnPropertiesProviderModule` + módulos do produto (`ptBrTranslateModule`, `propertiesPanelModule`).
- Viewer de leitura/preview = `NavigatedViewer` (sem módulos de mutação por construção).
- Theming via CSS vars da shell (`BPMN_RENDERER_THEME`); DI colors do documento prevalecem.
- **Edição de BPMN `id`:** vigente — o entry `id`/`processId` do properties panel do vendor é realocado para grupo "Configurações avançadas" (`AdvancedIdProvider`); edição passa pelo command stack vendor (undo/redo/read-back, refs atualizadas). Claim freeze "id read-only/FUTURE" = SUPERSEDED. Evidência: `propertiesPanelModule.ts`, `e2e/specs/bpmn-id-governance.spec.ts`. `Model.id` da API é autoridade separada — nunca alterado por edição BPMN.
- Tablet = read-only (`pointer:coarse` + `<1280px`); mobile fora de escopo.
- Residual aceito: `PROPERTIES_PANEL_VENDOR_TRANSLATION_LIMITATION` — strings leaf do vendor sem extension point permanecem em EN (workaround documentado `PanelChromePtBr`). `ACCEPTED_RESIDUAL`, `NON_BLOCKING`.

## 9. API surface (vigente)

- 20 operações congeladas (gate CI compara `operationId`s do `openapi.json`).
- `If-Match`/`ETag` = token de versão do agregado (`"v<n>"`); `X-Artifact-SHA256` = identidade do artefato. `expected_version` nunca no body.
- Missing `If-Match`→428; stale→412/`CONFLICT`; envelope `{success,message,data,error,meta}`; `message` PT-BR, `error.code` EN.
- Working-copy GET = XML raw + `X-Artifact-SHA256`; exports com `Content-Disposition` sanitizado.
- `POST /models/{id}/revisions` aceita body opcional `{name?, description?}` (§5).

## 10. Persistência (vigente)

- `plugins_hub` (database compartilhado) + schema `bpmn_modeler` + `PLUGINS_DB_*` (`plugins_user`) — decisão de database dedicado revogada e emendada no próprio freeze.
- Migrations up-only V001–V004; `BPMN_RUN_MIGRATIONS_ON_STARTUP` no startup da API; runner idempotente (CI executa 2×).
- `V004__owner_scoped_list_index` — `idx_models_owner_list (created_by, archived_at, updated_at DESC, id DESC)` — vigente (criado pelo P0; claim "nenhum índice adicional" SUPERSEDED).
- Revisions append-only: ausência de UPDATE/DELETE em `revisions` = invariante de aplicação + gate CI static scan.

## 11. Testes e evidência de execução

| Superfície | Evidência | Status |
|---|---|---|
| Backend unit/contract/journeys | `bpmn-modeler/tests/` — 98 testes em 10 arquivos (`test_use_cases`, `test_domain_model`, `test_api_contract`, `test_validation_*`, `test_ownership_isolation` (14), `test_revision_immutability`, `test_e2e_journeys`, `test_repository_integration`, `test_architecture`) | executados em CI |
| CI backend | pytest, migrations idempotentes, repository integration sobre plugins_hub real, schema isolation, append-only scan, OpenAPI 20 ops, camadas, XSD checksums | gates verdes |
| Frontend unit | `vitest` — saveMachine, autosave, diProposal, canvas-reg, propertiesPanelModule, i18n | executados em CI |
| Frontend build | tsc, eslint, vite build, worker chunk, vendor leakage, notices/watermark | gates verdes |
| Browser E2E | `e2e/specs/` — 17 specs (~5,7k linhas): acceptance-journey, autosave-auth, bpmn-id-governance, i18n, interaction-chrome, layout-*, modeler-journeys, revisions-metadata, runtime-messages, sidebar-*, theme, visual-regression | executados contra stack real local (não rodam no CI remoto) |
| Runtime multi-user | P0 acceptance: 57/57 + closure 18/18 (subjects reais, superadmin real) | PASS |

Nota de execução E2E: baseline suportado `workers=1/2` determinístico; `workers=8` = best-effort (contenção de host).

## 12. Accepted residuals vigentes

| Residual | Classificação |
|---|---|
| Properties panel — chrome leaf não traduzível (vendor) | `ACCEPTED_RESIDUAL`, `NON_BLOCKING` |
| Watermark bpmn.io (attribution requirement) | `BLOCKED_BY_ATTRIBUTION_REQUIREMENT`, não é bug de produto |
| E2E `workers=8` | best-effort, não contrato |

## 13. BPMN profile — SCOPE TARGET ≠ IMPLEMENTATION PROVEN

O profile do `V1-SCOPE-FREEZE.md` §6–7 (`CREATE_EDIT`/`RENDER_PRESERVE_ONLY`) é **scope target congelado**, não prova de implementação. Nenhum item do profile deve ser declarado entregue sem evidência create/edit/save/export/reimport. Inventário capability-by-capability = **G1**.

Status de auditoria G0: `TO_INVENTORY` (a matriz detalhada será produzida no G1; o G0 não reivindica breadth).

## 14. Produtividade — classificação por evidência (G0)

| Capacidade | Freeze | Implementação atual | Classificação |
|---|---|---|---|
| copy/cut/paste (mesmo modelo) | IN_V1 | `CopyPasteModule` + `KeyboardModule` no bundle vendor; sem teste produto dedicado | `TARGET` (vendor presente, evidência produto pendente — G3) |
| multi-select (Shift+click / lasso) | IN_V1 | `SelectionModule`, `LassoToolModule`, `KeyboardMoveSelectionModule` vendor + "Selecionar tudo" do produto (context menu canvas) | `TARGET` parcial — lasso/Ctrl+A vendor sem UX test dedicado |
| keyboard shortcuts | IN_V1 | vendor bindings (undo/redo/del/copy) + produto `Ctrl+S` flush; `Ctrl+F` **ausente** | `PARTIAL` / `IMPLEMENTATION_GAP` (search shortcut) |
| search in diagram (Ctrl+F overlay) | IN_V1 (§34) | `adapter.findElements` implementado + unit-tested; **overlay/produto UI ausente** | `IMPLEMENTATION_GAP` — spec vigente sem entrega |
| palette search | IN_V1 | `SearchModule`/`BpmnSearchProvider` + search-pad no bundle vendor; UX produto sem evidência dedicada | `TARGET` (TO_INVENTORY) |
| snap/grid | IN_V1 (vendor) | `SnappingModule` + `GridSnappingModule` no bundle; grid configurável pelo usuário = `FUTURE` (inalterado) | vendor presente; config gap permanece FUTURE |
| palette restrita ao profile + vendor features off | IN_V1 (§31/§95 do freeze) | **sem palette provider custom** — palette vendor completa exposta; nenhum módulo de restrição | `IMPLEMENTATION_GAP` → G3 |
| thumbnails na library | `FUTURE` no freeze | **entregue** — `BpmnModelThumb` renderiza SVG do working copy (cache `model@version`) | `SUPERSEDED` (DRIFT-BPMN-011) |

Extras do bundle vendor presentes sem UX/evidência de produto dedicada (TO_INVENTORY, não contam como entrega): `AlignElementsModule`, `DistributeElementsModule`, `SpaceTool`, `HandTool`, `AutoPlace`, `GlobalConnect`.

Drift classificado como `IMPLEMENTATION_GAP` (não documentation drift): documentação congelou capability `IN_V1` que o produto ainda não prova em UX. Owner: `03 — Frontend & UX` → G3.

## 15. Gates de implementação (roadmap registrado)

```text
G0 — Documentation Drift Reconciliation   OWNER 08   este gate
G1 — V1 Capability Evidence Inventory     OWNER 02+03+06   COORD 00
G2 — BPMN Professional Breadth Wave 1     OWNER 02→03→01→06
G3 — Modeling Productivity                OWNER 03→06
G4 — Broad Round-trip / Interoperability  OWNER 02+06
G5 — Transformômetro ↔ BPMN Modeler       OWNER 00+06
G6 — Runtime Provenance / stale-process   OWNER 09
```

## 16. Open follow-ups

| Item | Owner | Status |
|---|---|---|
| RUNTIME_STALE_CODE_PREVENTION — processo uvicorn executava código pré-deploy apesar do bind mount atualizado (foreign read 200 → 404 após `docker restart`); incidente de deploy, não defeito de policy | 09 — DevOps/CI/Runtime | `OPEN`, `NON_BLOCKING` |
| Diagram search overlay (§34 freeze) | 03 | `IMPLEMENTATION_GAP` → G3 |
| BPMN profile breadth proof | 02+03+06 | `TO_INVENTORY` → G1 |
