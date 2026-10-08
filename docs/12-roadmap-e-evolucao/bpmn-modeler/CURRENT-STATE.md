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
- **Round-trip per-construct (G4, PASS):** import real → read-back byte-exact → validate → open editor → `exportXml()` capturado via ação "Validar" → compare estrutural QName/ns/DI-aware (`e2e/rt-compare.ts`, test-only) → reimport → read-back → idempotência + `incoming`/`outgoing` consistency check. Corpus `e2e/fixtures/roundtrip/` (13 fixtures XSD-validadas), specs `e2e/specs/roundtrip-*.spec.ts` (16 testes) + adapter-level `src/editor/roundtrip-adapter.test.ts` (14 testes) + `src/editor/extensionPreservation.test.ts` (7 testes). Transforms vendor classificados e allow-listados por caso: drilldown plane de subprocess colapsado (EXTRA `BPMNDiagram`), `isMarkerVisible="true"` em DI de gateway, DI gerado no path no-DI (elk transitório, §7), `BPMNLabel` adicionado em shape renomeado; serializer omite XSD-defaults e `exporter*` (normalizados).
- **Extensões desconhecidas (G4-EXT-1, CLOSED):** duas perdas vendor provadas e tratadas em `src/editor/extensionPreservation.ts` (adapter boundary — fonte canônica). (a) `bpmn:extension/@definition` é dropada no PARSE (descriptor a declara `isReference` para `ExtensionDefinition`, mas o valor é QName léxico, não id resolvível) → `repairExtensionDeclarations` reinstala referência léxica `{id: "<qname>"}` — serializer reemite o attr intacto. (b) Attr namespaced `{ns}x` em elemento `{ns}e` de `extensionElements` (mesma URI) é irremediável no serializer (`nsAttributeName`/`isLocalNs` compara URIs e stripa o prefixo — incorreto, attrs não herdam default ns) → `hasUnpreservableExtensionContent` detecta via DOM estruturado → `UNSUPPORTED_EXTENSION_SERIALIZATION` → **read-only + save bloqueado** (fail-closed; artefato permanece byte-exact). Attrs namespaced cross-ns em qualquer posição, elementos/nested/texto de extensão: preservados. Evidência: `extensionPreservation.test.ts` (minimal moddle + detecção), `roundtrip-adapter.test.ts` (ext-false/ext-true com 0 diffs; ext-risky asserta a perda vendor como evidência do gate), RT-EXT-01..04.

## 7. Layout / BPMN-DI (vigente)

- ELK (`elkjs`) executa **exclusivamente em Web Worker** (`layout.worker.ts` via `workerFactory`); **não existe fallback main thread** — worker indisponível/falha/timeout → `LAYOUT_FAILED`/`LAYOUT_TIMEOUT`/`LAYOUT_CANCELLED` e canvas principal permanece intacto. Gate CI "worker-only" prova.
- Fluxo: `Organizar` → grafo ELK (`elkGraph.ts`) → `runLayout` → proposta DI (`diProposal.ts`) → **preview em `NavigatedViewer` separado** (canvas principal intocado; banner "nada foi alterado").
- **ACCEPT** = `applyDiLayout` = UM comando lógico no command stack → DIRTY → **autosave pode persistir**; undo reverte o batch. **CANCEL** = preview destruído, zero write canônico.
- O gesto explícito obrigatório é **Accept/Cancel**; não existe write de geometria sem Accept, mas o persist após Accept é o autosave (não um clique "Salvar" obrigatório).
- BPMN sem DI: DI transitório calculado/injetado só para render no open (não persiste); edições produzem DI pelo serializer do vendor.
- Evidência: `diProposal.test.ts`, `layout-*.spec.ts` E2E, gates CI. **PROVEN** para o mecanismo; cobertura de constructs G1.

## 8. Editor / vendor boundary (vigente)

- `BpmnEditorAdapter` = única superfície React↔vendor (`src/editor/`); vendor leakage gate no CI.
- `Modeler` (bpmn-js 18.30.1) + `BpmnPropertiesPanelModule`/`BpmnPropertiesProviderModule` + módulos do produto (`ptBrTranslateModule`, `propertiesPanelModule`, `profileGovernanceModule`).
- **Editing profile governance (G2A, vigente — após correction pass):** `editingProfile.ts` = autoridade central testável do profile V1 (`CREATE_EDIT`/`RENDER_PRESERVE_ONLY`/fora do profile); `profileGovernanceModule.ts` envolve os providers vendor oficiais (`paletteProvider`, `contextPadProvider`, `replaceMenuProvider`) via `injector.instantiate` e filtra entries **fail-closed por allowlist** (option vendor não classificada no profile = não exposta, em todas as surfaces: palette, context pad, replace body, replace header, properties group e properties entry). `ProfileGovernedPanelProvider` (mesmo `propertiesPanelModule.ts`) remove grupos fora do profile (multiInstance, compensation, adHocCompletion) e filtra entries por allowlist do inventário real da surface vendor — `isExecutable` é atributo **BPMN normativo** cuja edição é intencionalmente não exposta (produto modela, não executa; blank artifact fixa `false`; valor importado é preservado no round-trip). Boundary sem definição não é criável/replace target; `append.compensation-activity` negado (compensation é preserve-only). Preserve-only continua importando/renderizando/preservando — governança só atua nas surfaces de create/replace/panel, nunca no canônico. Evidência: `editingProfile.test.ts`, `profileGovernance.test.ts`, `e2e/specs/profile-governance.spec.ts`.
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
| Frontend unit | `vitest` — saveMachine, autosave, diProposal, canvas-reg, propertiesPanelModule, i18n, editingProfile, profileGovernance | executados em CI |
| Frontend build | tsc, eslint, vite build, worker chunk, vendor leakage, notices/watermark | gates verdes |
| Browser E2E | `e2e/specs/` — 18 specs: acceptance-journey, autosave-auth, bpmn-id-governance, i18n, interaction-chrome, layout-*, modeler-journeys, profile-governance, revisions-metadata, runtime-messages, sidebar-*, theme, visual-regression | executados contra stack real local (não rodam no CI remoto) |
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

### 13a. CREATE_EDIT evidence (G2B — vigente)

Todos os constructs do profile `CREATE_EDIT` têm o **caminho estrutural PROVEN** por execução real: 24 testes E2E em `e2e/specs/create-edit-{activities,gateways,events,collaboration,artifacts}.spec.ts` (executados com `workers=2`, baseline determinístico), cada um percorrendo `create → configure basic shape/type → connect (quando aplicável) → autosave → authoritative read-back (GET working-copy) → reload → verify QName + render`. Helpers compartilhados em `e2e/ce-helpers.ts` (incl. `fetchWorkingCopyXml`, `attachBoundary`, `newShapeId`/`newConnectionId` por diff de DOM).

A **breadth de properties** do profile permanece **PARTIAL**: `timerEventDefinitionType`/`timerEventDefinitionValue` PROVEN (CE-EVT-06); `name`/`lane name`/`task type`/annotation text PROVEN; event refs (`messageRef`/`errorRef`/`signalRef`/`escalationRef`) expostos mas sem evidência dedicada; `calledElement`, `conditionExpression`, `defaultFlow` **ausentes da surface `bpmn` carregada** (IMPLEMENTATION_GAP → WAVE E).

| Família | Spec | Prova |
|---|---|---|
| Activities | CE-ACT-01..04 | Task (rename/delete/undo) + 7 typed tasks via Replace + CallActivity + SubProcess expanded/collapsed |
| Gateways | CE-GW-01..05 | Exclusive palette + Parallel/Inclusive/EventBased via replace + connect + EventBased append governance (conditional deny — regressão G2A) |
| Events | CE-EVT-01..06 | start/catch/throw/boundary/end defs, boundary attach em task (interrupting + non-interrupting `cancelActivity="false"`), timer type/value via panel |
| Collaboration | CE-COL-01..05 | participant expanded (`processRef`+`laneSet`), lanes insert/divide/nested/rename/move (`childLaneSet`+`flowNodeRef`), black-box pool, 2 pools + MessageFlow |
| Artifacts | CE-ART-01..04 | DataObject, DataStoreReference, TextAnnotation+texto, Group, Association, dataInput+dataOutputAssociation |

Gaps residuais desta wave: `calledElement`, `conditionExpression`, `defaultFlow` **não existem na surface do provider `bpmn` carregado** (vivem nos providers Zeebe/Camunda não instalados) — classificados como `IMPLEMENTATION_GAP` na properties matrix (WAVE E, owner 03), não como falha de governance nem como VENDOR_ONLY.

## 14. Produtividade — classificação por evidência (G0)

| Capacidade | Freeze | Implementação atual | Classificação |
|---|---|---|---|
| copy/cut/paste (mesmo modelo) | IN_V1 | `CopyPasteModule` + `KeyboardModule` vendor + governança `copyPaste.canCopyElements` → `isClipboardElementAllowed` (recursivo: filhos de subprocesso + boundary attachers); paste não cria preserve-only | `PROVEN` — PROD-CLIP-01..07: single/multi/flows, ids novos (paste) e unicidade (cut→paste), refs válidas, undo/redo, autosave/RB/reload; bypass preserve-only negado (§14a) |
| multi-select (Shift+click / lasso) | IN_V1 | `SelectionModule`, `LassoToolModule`, `KeyboardMoveSelectionModule` vendor | `PROVEN` — PROD-SEL-01..05: Shift+click, lasso (L+drag), Ctrl+A, deselect vazio, bulk move (geometria relativa + DI + undo/redo + RB/reload), bulk delete (flows removidas, refs limpas, undo/redo, RB) |
| keyboard shortcuts | IN_V1 | vendor bindings (undo/redo/del/copy) + produto `Ctrl+S` flush + `Ctrl+F` searchPad + fix de foco pós-drag (§14a) | `PROVEN` — PROD-KEY-01..06: Ctrl+S, E direct editing, R replace menu, Backspace, context pad governado, replace morph task→userTask |
| search in diagram (Ctrl+F overlay) | IN_V1 (§34) | vendor `searchPad` + `BpmnSearchProvider` (busca por name/id) | `PROVEN` — PROD-SRCH-01..04: Ctrl+F abre, busca por nome/id, Enter seleciona, ArrowDown navega, Escape fecha, zero mutação |
| palette search | IN_V1 | componente produto `PaletteSearch` (overlay) — fonte única = `palette.getEntries()` já filtrada pela governança; aliases PT-BR/EN; `/` abre, setas navegam, Enter ativa, Escape fecha | `PROVEN` — PROD-PAL-01..05: a11y (role combobox/aria-label), teclado completo, CREATE_EDIT-only, preserve-only nunca lista, clique posiciona + RB |
| resize funcional | IN_V1 | `ResizeModule` vendor; `BpmnRules.canResize` — SubProcess(expandido)/Lane/Participant/Group/TextAnnotation(e/w)/labels | `PROVEN` — PROD-RSZ-01..05: resize real via `.djs-resizer-*` drag muda DI, undo/redo, save/RB/reload; task/event/gateway/data-object = `BLOCKED_AS_EXPECTED` (fixed-size vendor) |
| snap/grid | IN_V1 (vendor) | `SnappingModule` + `GridSnappingModule` (grid 10) no bundle; grid configurável pelo usuário = `FUTURE` (inalterado) | `PROVEN` — PROD-SEL-06: drag livre quantiza bounds DI no grid 10 |
| palette restrita ao profile + vendor features off | IN_V1 (§31/§95 do freeze) | **vigente (G2A)** — `editingProfile.ts` central + `profileGovernanceModule.ts` (palette/context-pad/replace fail-closed) + `ProfileGovernedPanelProvider` (panel); preserve-only e MultiInstance não criáveis nem replace targets | `IMPLEMENTED`+`PROVEN` (unit+integration+E2E `profile-governance.spec.ts`); ferramentas não-semânticas (align/distribute/space/hand/global-connect) permanecem `TO_INVENTORY` |
| thumbnails na library | `FUTURE` no freeze | **entregue** — `BpmnModelThumb` renderiza SVG do working copy (cache `model@version`) | `SUPERSEDED` (DRIFT-BPMN-011) |

Extras do bundle vendor presentes sem UX/evidência de produto dedicada (TO_INVENTORY, não contam como entrega): `AlignElementsModule`, `DistributeElementsModule`, `SpaceTool`, `HandTool`, `AutoPlace`, `GlobalConnect`.

Drift classificado como `IMPLEMENTATION_GAP` (não documentation drift): documentação congelou capability `IN_V1` que o produto ainda não prova em UX. Owner: `03 — Frontend & UX` → G3. **Resolvido em G3 (§14a).**

### 14a. G3 — descobertas e fixes de produtividade

**Defeito de produto corrigido — foco do canvas após drag.** O `Keyboard` vendor é bound ao `<svg>` do canvas (`tabindex=0`). Drags iniciados em overlays HTML sem tabindex (resizers `.djs-resizer-*`) levam `document.activeElement` a `body`, e o mouseup final de qualquer drag é capturado por `trapClickAndEnd` no `document` (capture phase) com `stopPropagation` — listeners DOM no container nunca veem esse evento. Resultado: após resize/move, **todos** os atalhos (Ctrl+Z/Y, Ctrl+C/X/V, Ctrl+A, Del) morriam silenciosamente. Fix no boundary do adapter (`BpmnEditorAdapter`): `eventBus.on('drag.ended')` + `mouseup` no container delegam a `canvas.restoreFocus()` — a API canônica do vendor (debounced, só age quando `activeElement===document.body`, nunca rouba foco de inputs/textareas do direct editing). Evidência: antes `FOCUS_AFTER_DRAG=BODY`/`UNDO_DIFF=80`; depois `svg`/`UNDO_DIFF=0` — regressão coberta por PROD-RSZ-01 (undo/redo pós-resize).

**Governança de clipboard (PRESERVE_ONLY ≠ CREATE).** `copyPaste.canCopyElements` é o extension point oficial que decide o que entra no clipboard — cobre copy, cut, duplicate e paste-as-tree (filhos de subprocesso e boundary events são avaliados recursivamente via `isClipboardElementAllowed`). Preserve-only importado (ex.: `ComplexGateway`, `Transaction`) é excluído do clipboard — `canCopy [Task, ComplexGateway] => [Task]` provado em PROD-CLIP-07; cut só remove o que efetivamente copiou. `UNCONTROLLED OUT-OF-PROFILE CREATE PATHS: 0`.

**Particularidades vendor mapeadas (fixtures determinísticas):**
- `create.participant-expanded` cria participant **sem lanes**; lanes surgem via context-pad governado `lane-divide-two/three`, `lane-insert-above/below` — renderizadas no plane do root como `.djs-element[data-element-id^="Lane_"]` (não aninhadas no DOM do pool).
- Create de elemento com label abre direct editing automaticamente (foco em `.djs-direct-editing-content`); Escape cancela mantendo o elemento — `canvas.restoreFocus` devolve o foco ao svg.
- Resizers só existem após transição real de seleção (`deselect → reselect`); re-click em elemento já selecionado não re-emite `selection.changed`.
- Entries do context pad são `draggable` — clique real pode não entregar `click` ao delegate (grupos com flyout); specs usam dispatch DOM nos mesmos handlers.
- SearchPad vendor pesquisa no `keyup` do input (não no `input` event) — specs digitam via `pressSequentially`.
- Palette vendor ocupa a faixa esquerda do canvas — helpers são layout-aware (`canvasBox`, coordenadas fora da faixa).

## 15. Gates de implementação (roadmap registrado)

```text
G0 — Documentation Drift Reconciliation   OWNER 08   este gate
G1 — V1 Capability Evidence Inventory     OWNER 02+03+06   COORD 00
G2 — BPMN Professional Breadth Wave 1     OWNER 02→03→01→06
      G2A Editing Profile Governance         PASS/CLOSED (34244d8)
      G2B CREATE_EDIT Evidence Closure       PASS — ver §13a
G3 — Modeling Productivity                OWNER 03→06   PASS/CLOSED — 33 E2E `productivity-*.spec.ts` (workers=2, determinístico): clipboard governado, seleção/bulk, searchPad Ctrl+F, palette search (IG-1 implementado), resize funcional + fixed-size blocked, shortcuts; fix de foco pós-drag (§14a)
G4 — Broad Round-trip / Interoperability  OWNER 02+06   PASS/CLOSED — 16/16 E2E roundtrip-* + 14/14 adapter-level + 7/7 extensionPreservation unit; G4-EXT-1 resolvido (§6)
G5 — Transformômetro ↔ BPMN Modeler       OWNER 00+06
G6 — Runtime Provenance / stale-process   OWNER 09
```

## 16. Open follow-ups

| Item | Owner | Status |
|---|---|---|
| RUNTIME_STALE_CODE_PREVENTION — processo uvicorn executava código pré-deploy apesar do bind mount atualizado (foreign read 200 → 404 após `docker restart`); incidente de deploy, não defeito de policy | 09 — DevOps/CI/Runtime | `OPEN`, `NON_BLOCKING` |
| Diagram search overlay (§34 freeze) | 03 | `CLOSED` (G3) — searchPad vendor provado PROD-SRCH-01..04 (Ctrl+F, nome/id, navegação, sem mutação) |
| BPMN profile breadth proof | 02+03+06 | `TO_INVENTORY` → G1 → G2B fechou CREATE_EDIT (§13a) → **G4 fechou per-construct round-trip (§6)** |
| E2E-38b (`visual-regression.spec.ts`) — teste importa modelo como `editor` e abre como `viewer`; falha com HTTP 404 desde a fail-closed ownership (`_get_owned_or_404`). Falha **pré-existente** ao G4 (teste de `7832e1adc6`), incompatível com a política vigente — precisa ser reescrito (modelo criado como `viewer`) ou a política revisada com decisão de produto | 03+02 | `OPEN`, `NON_BLOCKING` |
| G4-EXT-1 — extension serialization: `bpmn:extension/@definition` reparado via referência léxica `{id}` (adapter boundary); attr same-ns em `extensionElements` é irremediável no serializer vendor → gate `UNSUPPORTED_EXTENSION_SERIALIZATION` fail-closed read-only (§6) | 02+06 | `CLOSED` — mitigado em produto; possível contribuição upstream ao `moddle-xml` é follow-up opcional, não-bloqueante |
