# BPMN MODELER — DOCUMENTATION DRIFT LEDGER (G0)

> **Propósito:** registrar toda divergência entre documentação de especificação (`*-SPEC-FREEZE.md`, escritos antes da implementação) e o estado vigente provado por código/testes/runtime.
> **Método:** CURRENT CODE → CURRENT TESTS → CURRENT MIGRATIONS → CURRENT RUNTIME EVIDENCE → CURRENT DOCS → DRIFT → CORRECTION → RESIDUAL SEARCH.
> **Regra:** `documentation != runtime proof`. Decisão histórica substituída não é apagada — recebe `SUPERSEDED (G0)` inline no freeze e entra neste ledger. Estado vigente consolidado em [`CURRENT-STATE.md`](CURRENT-STATE.md).

## Classification legend

| Classe | Significado |
|---|---|
| `DOCUMENTATION_STALE` | doc descreve estado antigo; implementação evoluiu com decisão aceita |
| `SUPERSEDED_CONTRACT` | decisão congelada foi revogada/substituída formalmente depois |
| `IMPLEMENTATION_GAP` | spec diz `IN_V1`, implementação ainda não prova o capability |
| `EXECUTION_DRIFT` | status de execução do doc diverge do runtime observado |
| `ALIGNED` | doc e implementação convergem |
| `TO_INVENTORY` | evidência insuficiente no G0 — deferred ao gate seguinte |

## Ledger

### DRIFT-BPMN-001 — Resource ownership (per-model ACL)

- **AREA:** authorization / resource ownership
- **OLD DOCUMENT:** `SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md` §12 T03, §27/§29 (`PER-MODEL ACL: NOT IN V1 (context-wide Core RBAC)`); `V1-SCOPE-FREEZE.md` (matriz de capabilities por permissão context-wide)
- **OLD CLAIM:** autorização = permissão `bpmn-modeler.*` context-wide; qualquer principal com `view` lê qualquer model; per-model ACL fora da V1
- **CURRENT EVIDENCE:** `Model.created_by` = owner V1; `_get_owned_or_404` em todo single-model path; `list_summaries(owner_subject=)` fail-closed; foreign → `404 MODEL_NOT_FOUND` sem leak; sem bypass superadmin/service principal; migration V004; `test_ownership_isolation.py` (14 testes); P0 runtime acceptance 57/57 + closure 18/18 (superadmin real incluído)
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT` (CRITICAL DOCUMENTATION DRIFT)
- **DECISION:** contrato de ownership vigente prevalece; freeze anotado inline
- **FILES UPDATED:** `SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** baixo — freeze histórico ainda contém o texto original com marker
- **OWNER:** 02/06 (policy), histórico preservado

### DRIFT-BPMN-002 — Owner-scoped list index (V004)

- **AREA:** persistence / pagination
- **OLD DOCUMENT:** `SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md` §5.4; `API-E2E-ACCEPTANCE-SPEC-FREEZE.md` §18.3
- **OLD CLAIM:** `FROZEN: no additional pagination index required` — `idx_models_list`/`idx_models_name_lower`/`idx_revisions_model` bastam
- **CURRENT EVIDENCE:** `migrations/V004__owner_scoped_list_index.sql` cria `idx_models_owner_list (created_by, archived_at, updated_at DESC, id DESC)`; presente em runtime (Index Only Scan observado no P0)
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT` — consequência direta de DRIFT-BPMN-001 (list passou a ser owner-scoped, exigindo índice iniciado por `created_by`)
- **DECISION:** V004 prevalece; o freeze registra o rationale histórico e a emenda G0
- **FILES UPDATED:** `SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE.md`, `API-E2E-ACCEPTANCE-SPEC-FREEZE.md`
- **RESIDUAL RISK:** nenhum — índice é aditivo e imutável após aplicado
- **OWNER:** 04 (persistência) — fechado

### DRIFT-BPMN-003 — Autosave

- **AREA:** save contract / UX de persistência
- **OLD DOCUMENT:** `V1-SCOPE-FREEZE.md` §17 (`Autosave OUT_OF_V1`); `BACKEND-DOMAIN-SPEC-FREEZE.md` §2/§7 (`não existe autosave`, `save é sempre explícito`); `BPMN-INTEROPERABILITY-SPEC-FREEZE.md` §2; `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` §2/§12/§14; `LAYOUT-BPMN-DI-SPEC-FREEZE.md` §2
- **OLD CLAIM:** não existe autosave; todo save é gesto explícito (botão Salvar / Ctrl+S)
- **CURRENT EVIDENCE:** `AutosaveController` (debounce 1,5s, coalescing, single-flight, read-back verify) + `SaveMachine` com estados OFFLINE/SESSION_EXPIRED; wiring em `ModelEditorPage`; E2E `autosave-auth.spec.ts` (AUTO-*/NAV-*/UNLOAD-*); autosave escreve **apenas** working copy
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT` — decisão pós-freeze aceita e implementada
- **DECISION:** contrato vigente = `EDIT→DIRTY→DEBOUNCE→AUTOSAVE WC→READ-BACK→VERIFY→SAVED`; `AUTOSAVE != REVISION`; `Ctrl+S` = flush secundário
- **FILES UPDATED:** os 6 freezes acima (emendas inline) + `CURRENT-STATE.md`
- **RESIDUAL RISK:** baixo — texto histórico preservado com marker
- **OWNER:** 03 (orquestração frontend) + 01 (use case write)

### DRIFT-BPMN-004 — Auto-layout × save

- **AREA:** layout persistence semantics
- **OLD DOCUMENT:** `V1-SCOPE-FREEZE.md` §12 (`ACCEPT → SAVE explícito`), `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` §50/checklist (`accept→DIRTY; sem auto-save`), `LAYOUT-BPMN-DI-SPEC-FREEZE.md` §2
- **OLD CLAIM:** após Accept, persist exige save explícito do usuário
- **CURRENT EVIDENCE:** preview em `NavigatedViewer` separado; Accept = `applyDiLayout` (1 comando, undoable) → DIRTY → autosave persiste; Cancel = zero write; forced navigate durante preview = auto-Cancel
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT` (consequência de DRIFT-BPMN-003)
- **DECISION:** gesto obrigatório vigente = **Accept/Cancel**; `CALCULATE != WRITE`, `PREVIEW != WRITE`; persist pós-Accept via autosave
- **FILES UPDATED:** `V1-SCOPE-FREEZE.md`, `FRONTEND-EDITOR-UX-SPEC-FREEZE.md`, `LAYOUT-BPMN-DI-SPEC-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** nenhum — preview continua nunca escrevendo
- **OWNER:** 03/05 (layout)

### DRIFT-BPMN-005 — Revision metadata

- **AREA:** revision contract / API
- **OLD DOCUMENT:** `API-E2E-ACCEPTANCE-SPEC-FREEZE.md` §11 (`POST .../revisions — sem body — V1 não tem label/note/reason editável`); `BACKEND-DOMAIN-SPEC-FREEZE.md` §4 (campos de `Revision` sem name/description)
- **OLD CLAIM:** revision sem metadata de label; request sem body
- **CURRENT EVIDENCE:** V003 adiciona `name`/`description`/`created_by_name`; domain valida limites (120/500); `CreateRevisionRequest` aceita body opcional; `RevisionSummaryResponse` expõe os campos; `CreateRevisionDialog` coleta no frontend; `revisions-metadata.spec.ts` E2E
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT`
- **DECISION:** body opcional `{name?, description?}` é vigente; ausência de body continua aceita (backward compatible)
- **FILES UPDATED:** `API-E2E-ACCEPTANCE-SPEC-FREEZE.md`, `BACKEND-DOMAIN-SPEC-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** nenhum — aditivo e opcional
- **OWNER:** 02/06 — fechado

### DRIFT-BPMN-006 — BPMN element ID editing

- **AREA:** editor properties
- **OLD DOCUMENT:** `V1-SCOPE-FREEZE.md` §8/§17 (`Element id edição = OUT_OF_V1/FUTURE`); `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` §30 (`id` read-only)
- **OLD CLAIM:** `id` de elemento visualizável mas não editável na V1
- **CURRENT EVIDENCE:** `AdvancedIdProvider` realoca `id`/`processId` para "Configurações avançadas" mantendo entry vendor (command stack, referências atualizadas, undo/redo); `e2e/specs/bpmn-id-governance.spec.ts` prova edição governada; `Model.id` API permanece autoridade separada
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT`
- **DECISION:** edição de BPMN `id` = vigente e governada (advanced group); não confundir com `model_id` (imutável)
- **FILES UPDATED:** `V1-SCOPE-FREEZE.md`, `FRONTEND-EDITOR-UX-SPEC-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** baixo — edição via vendor entry com refs consistentes
- **OWNER:** 03 — fechado

### DRIFT-BPMN-007 — Implementation/test status markers

- **AREA:** execution status
- **OLD DOCUMENT:** `API-E2E-ACCEPTANCE-SPEC-FREEZE.md` §40/§41 (`IMPLEMENTATION STATUS: NOT IMPLEMENTED`, `RUNTIME ACCEPTANCE: TEST_NOT_RUN`, matrizes todas `TEST_NOT_RUN`)
- **OLD CLAIM:** estado de execução = zero implementação/zero execução
- **CURRENT EVIDENCE:** backend+frontend+persistence+HTTP+validation+layout+autosave+revisions+ownership implementados; 98 testes backend + vitest + 17 specs E2E; CI gates ativos; runtime acceptance executado
- **CLASSIFICATION:** `STALE_EVIDENCE` / `EXECUTION_DRIFT` (contextual, não contraditório: o freeze era pré-implementação por desenho)
- **DECISION:** `SPECIFICATION STATUS` permanece no freeze; `CURRENT EXECUTION STATUS` vive em `CURRENT-STATE.md`; freeze recebe banner + nota no §41
- **FILES UPDATED:** `API-E2E-ACCEPTANCE-SPEC-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** implementador pode ler `TEST_NOT_RUN` como estado atual — mitigado por banner/ledger
- **OWNER:** 08 (este gate)

### DRIFT-BPMN-008 — BPMN breadth claims (scope target)

- **AREA:** BPMN profile coverage
- **OLD DOCUMENT:** `V1-SCOPE-FREEZE.md` §6–7 (profile `CREATE_EDIT`/`RENDER_PRESERVE_ONLY`)
- **OLD CLAIM:** profile amplo declarado `CREATE_EDIT` (User/Service/Manual/BusinessRule/Script/Send/Receive Task, Call Activity, Parallel/Inclusive/EventBased Gateway, Intermediate/Boundary Events, timer/message/signal/error/escalation/link, associations, nested lanes, black-box pool, …)
- **CURRENT EVIDENCE:** nenhuma prova capability-por-capability de create/edit/save/export/reimport em G0; editor usa bpmn-js completo + properties provider padrão
- **CLASSIFICATION:** `TO_INVENTORY` — **scope target ≠ implementation proven** (não é drift de doc; é trabalho do G1)
- **DECISION:** profile permanece TARGET; `CURRENT-STATE.md` §13 proíbe promoção a PROVEN sem evidência
- **FILES UPDATED:** `CURRENT-STATE.md` (+ banners nos freezes)
- **RESIDUAL RISK:** breadth superestimado até G1 — mitigado pela separação target/proven
- **OWNER:** 02+03+06 (G1)

### DRIFT-BPMN-009 — Diagram search overlay / productivity UX

- **AREA:** editor UX / productivity
- **OLD DOCUMENT:** `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` §32/§34 (`Ctrl+F` overlay do produto, `[Buscar]` na toolbar, search como alternativa a11y §564); `V1-SCOPE-FREEZE.md` §8 (`Search in diagram`, `palette search` IN_V1)
- **OLD CLAIM:** overlay de busca do produto + botão Buscar + Ctrl+F entregues como IN_V1
- **CURRENT EVIDENCE:** `adapter.findElements` implementado e unit-tested; **nenhum SearchOverlay/Ctrl+F/botão** no código; navegação por issue do ValidationPanel usa `selectElement`; palette search vendor (`BpmnSearchProvider`) presente sem UX/teste dedicado
- **CLASSIFICATION:** `IMPLEMENTATION_GAP` (spec vigente, entrega parcial — não é doc errada)
- **DECISION:** documentação mantém spec; gap registrado como follow-up G3; classificação explícita em `CURRENT-STATE.md` §14
- **FILES UPDATED:** `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` (nota §34), `CURRENT-STATE.md`
- **RESIDUAL RISK:** médio — a11y alternativa "busca" prometida está parcial; `selectElement` via painel de validação é caminho residual
- **OWNER:** 03 → G3

### DRIFT-BPMN-010 — Palette/vendor-surface restriction

- **AREA:** editor UX / profile enforcement
- **OLD DOCUMENT:** `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` §31 (`Palette expõe somente o profile CREATE_EDIT … palette provider custom`; `Vendor defaults fora do profile são desabilitados explicitamente`)
- **OLD CLAIM:** palette filtrada ao profile + vendor features fora do profile desligadas
- **CURRENT EVIDENCE:** `BpmnEditorAdapter` instancia `Modeler` com `additionalModules = [ptBrTranslateModule, BpmnPropertiesPanelModule, BpmnPropertiesProviderModule, propertiesPanelModule]` — **sem palette provider custom nem módulo de restrição**; a palette vendor completa do bpmn-js está exposta (inclui constructs `RENDER_PRESERVE_ONLY` do profile e demais elementos BPMN padrão)
- **CLASSIFICATION:** `IMPLEMENTATION_GAP` — spec vigente não entregue; nenhum teste exige restrição de palette
- **DECISION:** doc mantém spec; gap registrado → G3 (ou G2 se a breadth do profile guiar a restrição); **não** classificar palette vendor completa como drift de segurança (round-trip preserva o que é criado)
- **FILES UPDATED:** `FRONTEND-EDITOR-UX-SPEC-FREEZE.md` (nota §31), `CURRENT-STATE.md` §14
- **RESIDUAL RISK:** usuário pode criar elementos fora do profile congelado; resultado segue preservation policy normal, mas UX promete palette restrita
- **OWNER:** 03 → G3

### DRIFT-BPMN-011 — Library thumbnails

- **AREA:** Model Library UX
- **OLD DOCUMENT:** `V1-SCOPE-FREEZE.md` §8/§17 (`Thumbnails na library | FUTURE`)
- **OLD CLAIM:** thumbnails fora da V1
- **CURRENT EVIDENCE:** `src/components/BpmnModelThumb.tsx` + `src/editor/modelThumbnail.ts` + uso em `ModelLibraryPage` — thumbnail SVG do working copy renderizado por card, cache `model@version` (limite 60)
- **CLASSIFICATION:** `SUPERSEDED_CONTRACT` — entregue além do scope target
- **DECISION:** registrado como entregue; nenhuma ação de código
- **FILES UPDATED:** `V1-SCOPE-FREEZE.md`, `CURRENT-STATE.md`
- **RESIDUAL RISK:** nenhum
- **OWNER:** 03 — fechado

### DRIFT-BPMN-012 — Stale runtime (deploy/process drift)

- **AREA:** runtime/deploy
- **OLD DOCUMENT:** nenhum — incidente novo, não coberto pelos freezes
- **OLD CLAIM:** (implícito) código no bind mount ≡ código em execução
- **CURRENT EVIDENCE:** durante P0 acceptance, `delpi-bpmn-modeler-api` executava processo uvicorn de 4h com código anterior ao bind mount atualizado — foreign read retornou 200; após `docker restart`, 404 conforme esperado (18/18 PASS)
- **CLASSIFICATION:** `EXECUTION_DRIFT` — `APPLICATION POLICY DEFECT: NONE PROVEN`; `RUNTIME/DEPLOYMENT DRIFT: DETECTED, REMEDIATED, VERIFIED`
- **DECISION:** follow-up `RUNTIME_STALE_CODE_PREVENTION` aberto; não misturado ao P0
- **FILES UPDATED:** `CURRENT-STATE.md` §16
- **RESIDUAL RISK:** ambiente dev pode servir código velho até restart — mitigação operacional pendente
- **OWNER:** 09 — DevOps/CI/Runtime — `OPEN`, `NON_BLOCKING`

## Residual search record (G0)

Busca executada sobre `docs/12-roadmap-e-evolucao/bpmn-modeler/` + `plugins/bpmn-modeler/README.md` por: `autosave`, `OUT_OF_V1`, `explicit save`, `PER-MODEL ACL`, `context-wide`, `sem body`, `read-only` (id), `FUTURE` (element id), `TEST_NOT_RUN`, `NOT IMPLEMENTED`, `no additional pagination index`, `idx_models_list`, `V004`, `save explícito`. Cada ocorrência foi classificada em contexto (historical / superseded / still-valid / gap). Resultado: nenhuma contradição vigente sem classificação remanescente após as emendas deste gate.
