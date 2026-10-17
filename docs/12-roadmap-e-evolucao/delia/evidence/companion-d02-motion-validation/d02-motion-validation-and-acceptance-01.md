# D02 — Avatar Motion: validação automatizada e evidência de aceite

**TASK_ID:** `DELIA-UX-COMPANION-D02-MOTION-VALIDATION-AND-ACCEPTANCE-01`  
**DATE:** 2026-10-17  
**BASE_HEAD / TESTED_SHA:** `a7869a5d4527d251a3f99ef549aa81979ed6d535` (= `origin/main` no reanchor)  
**FINAL_HEAD:** (commit desta evidência)  
**PHASE_PROGRESSION:** NONE  
**D02_ACCEPTANCE_RECOMMENDATION:** `ACCEPT_WITH_RESIDUAL` (executor; review final = GPT)  
**EXECUTION_STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Reanchor e reuse

| Campo | Valor |
|---|---|
| Branch | `main` |
| Concurrent dirty | `delia-api/.../orchestration.py` **preservado** (fora do escopo) |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | REUSE_AND_EXTEND_COMPOSITION |
| AVATAR_OWNER | plugin-ui (`UnifiedAvatar` + `unified-avatar.css`) |
| INTERACTION_STATE_OWNER | plugins/delia (`App.loading` → pending row) |
| DOCK_HOST_OWNER | Portal (`GlobalDeliaDock`) |

Implementação D02 já publicada (§118 §5 / ledger §6.239): `UnifiedAvatar(motionState="processing")` somente com `loading`; ActivityViewer icon oculto no pending-row; teste demo `?delia-demo=loading`.

## 2. Comandos e exit codes

| COMMAND | WORKSPACE | EXIT | RESULT |
|---|---|---:|---|
| `npx vitest run src/App.test.tsx src/demoMode.test.tsx src/s2.shell.test.tsx` | plugins/delia | 0 | 44 PASS (incl. D02 pending avatar) |
| `npx vitest run UnifiedAvatar.test.tsx ActivityViewer.test.tsx` | plugins/plugin-ui | 0 | 32 PASS |
| `npx vitest run MessageComposer.test.tsx` | plugins/plugin-ui | 0 | 23 PASS (stop cancelable) |
| `npm run typecheck` | plugins/delia | 0 | PASS |
| `npx tsc -p tsconfig.json --noEmit` | plugins/plugin-ui | 2 | **29 erros PREEXISTING** (catalog/bpmn/charts/tests); avatar scoped tsc EXIT 0 |
| `npm run build` + `verify:federation` | plugins/delia | 0 | PASS |
| `npm run build` (+ host-exports) | plugins/plugin-ui | 0 | PASS; `UnifiedAvatar` exportado |
| `npx tsx --test globalDeliaDock*.test.ts` | portal | 0 | 23 PASS |
| Playwright Docker motion matrix | standalone `:5020` demo | 0 | ver §3 |
| Portal autenticado / Dock live | — | — | **TEST_NOT_RUN** |

## 3. CSS / bundle

`plugins/plugin-ui/dist/assets/style-FEkHCoj8.css` contém:

- `animation:delpi-ui-unified-processing 1.9s ease-out infinite`
- keyframes respond/attention
- `@media (prefers-reduced-motion:reduce)` → `animation:none`

`plugins/delia/dist` CSS contém `.delia-interaction__pending-row` e `.delpi-ui-activity-viewer__icon{display:none}`.

## 4. Matriz AC-01…AC-16

Superfície primária: **DÉLIA standalone Vite** `http://127.0.0.1:5020/apps/delia/?delia-demo=…` (Playwright `mcr.microsoft.com/playwright:v1.64.1-jammy --network host`).  
Artefatos: PNGs + `motion-result.json` + `cancel-error-result.json` + `remeasure.json` neste diretório.

| ID | Status | Evidência |
|---|---|---|
| AC-01 Idle | **PASS** | sem `data-motion=processing` antes do submit |
| AC-02 Submit → pending | **PASS** | pending-row após Enviar (demo loading) |
| AC-03 Processing pulse | **PASS** | `animationName=delpi-ui-unified-processing`, `duration=1.9s`, `iteration=infinite`, `playState=running` |
| AC-04 Cleared | **PASS** | processing ausente após fim do delay demo |
| AC-05 Responding one-shot | **PARTIAL** | assistente volta a idle; one-shot `responding` frequentemente já concluído antes do capture |
| AC-06 Error clears | **PASS** | `delia-demo=error`: processing visto e removido; composer + draft OK |
| AC-07 Cancel local | **TEST_NOT_RUN** (demo) | `sendDemoTurn` não seta `requestMode=responding_cancelable`; stop real coberto por MessageComposer Vitest; request real exige auth |
| AC-08 Attention ≠ processing | **PASS** | `delia-demo=clarification` → `data-motion=attention`, processing=0 |
| AC-09 Light | **PASS** | screenshots full-* |
| AC-10 Dark | **PASS** | `colorScheme=dark` + processing medido |
| AC-11 Reduced motion | **PASS** | `animationName=none`, `duration=0s` com `reducedMotion:reduce` |
| AC-12 Halo clipping | **PASS** | remeasure 360: `clippedBy=[]`; padding pending 3px cobre inset -2px |
| AC-13 A11y live | **PASS** | 1× `[role=status]` visível; ícone ActivityViewer `display:none` |
| AC-14 Nav apps / Dock host | **TEST_NOT_RUN** | Portal unauth = spinner; sem sessão OIDC |
| AC-15 Full page | **PASS** | 1280/1440 standalone |
| AC-16 Composer após erro | **PASS** | enabled + draft preservado |

### Cobertura

```text
TOTAL_RQ=16
APPLICABLE_RQ=16
IMPLEMENTED_RQ=13
PARTIAL_RQ=1   (AC-05)
NOT_IMPLEMENTED_RQ=0
BLOCKED_RQ / TEST_NOT_RUN=2  (AC-07 demo cancel path; AC-14 Portal/Dock)
TASK_VERIFIED_COVERAGE_PCT=81.25
```

**Demo PASS ≠ integração real PASS.** Pending/pulse/reduced-motion/erro/attention provados em demo+CSS live. Request autenticado Portal/Dock e cancel transport real = residual.

## 5. Defeitos e correções

| Classe | Item |
|---|---|
| NEW_REGRESSION | nenhuma |
| FIXES_APPLIED | **NONE** |
| PREEXISTING_DEBT | plugin-ui full tsc 29 erros |
| ENVIRONMENT | Portal auth / Companion Dock live |
| MEASUREMENT | 1º probe AC12/AC13 falso-positivo (corrigido por remeasure) |

## 6. Decisão do executor

```text
D02_IMPLEMENTATION_VERIFIED=YES (composition + CSS + Vitest + demo LIVE)
D02_ACCEPTED=NO  (aceite formal = review GPT)
D02_ACCEPTANCE_RECOMMENDATION=ACCEPT_WITH_RESIDUAL
RESIDUALS=AC-05 timing capture; AC-07 demo stop; AC-14 Portal/Dock auth live; real POST pending
NEXT=D01_COMPANION_DOCK_UX_IF_ACCEPTED
PHASE_PROGRESSION=NONE
```
