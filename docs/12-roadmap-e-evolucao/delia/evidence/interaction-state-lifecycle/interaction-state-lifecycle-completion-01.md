# DÉLIA — Validação e correção do ciclo de estados de interação

**TASK_ID:** `DELIA-UX-INTERACTION-STATE-LIFECYCLE-COMPLETION-01`  
**DATE:** 2026-10-19  
**REFERENCE_HEAD:** `dfd05a78b8ed608f3632f2222471c1adb2523fef`  
**BASE_HEAD (reanchor):** `cae0300bc23fbfb947ee86eef7b47223f6b908ab`  
**PHASE_PROGRESSION:** NONE  
**EXECUTION_STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Reuse gate

| Necessidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Avatar motion idle/processing/responding | YES `UnifiedAvatar` | EXTEND (null-safe matchMedia) |
| Pending row + ActivityViewer | YES `App.tsx` D02 | REUSE |
| Abort / requestEpoch / requestMode | YES `App.sendTurn` / `handleStopResponse` | REUSE |
| Composer stop | YES `MessageComposer` | REUSE |
| Lifecycle matrix A–E | Partial em interaction/demo/App tests | EXTEND (`interactionStateLifecycle.test.tsx`) |

Owners: plugin-ui = apresentação; DÉLIA = estado/composição; Portal = Dock host (não alterado).

## 2. Baseline

| Gate | Resultado |
|---|---|
| Vitest DÉLIA (pré-diff) | **212 PASS** |
| Matriz lifecycle (nova) | RED: 1 FAIL + uncaught `matchMedia().matches` |
| Causa-raiz | `UnifiedAvatar`: `matchMedia?.(q).matches` sem `?.` no resultado → throw quando MediaQueryList ausente |

## 3. Defeito corrigido (PRODUCT_DEFECT)

**Arquivo:** `plugins/plugin-ui/src/components/layout/UnifiedAvatar.tsx`  
**Bug:** optional chaining incompleto — ambiente sem `matchMedia` ou com retorno `undefined` derruba o efeito de `responding` e pode desmontar a árvore React.  
**Fix:** `window.matchMedia?.(…)?.matches`  
**RED/GREEN:** `UnifiedAvatar.test.tsx` (reduced motion + matchMedia ausente/undefined) → PASS.

Sem novo state machine, timer artificial ou engine paralelo.

## 4. Matriz automatizada (Vitest)

Arquivo: `plugins/delia/src/interactionStateLifecycle.test.tsx` — **13 PASS**.

| Grupo | Cobertura | Resultado |
|---|---|---|
| A fluxo normal | A01–A08 idle/processing/responding/multi-turn | PASS |
| B erros | B01/B02/B04/B06 HTTP + rede + retry | PASS |
| C cancel/concorrência | C01–C04, C06–C08 stop/late/unmount/double-stop | PASS |
| D motion/a11y | um avatar processing, aria-hidden | PASS |
| E conversa | bloqueio de envio durante pending | PASS |

B03 timeout transporte: **não inventado** — contrato atual não define timeout de frontend; lacuna `TO_INVENTORY` no owner de transporte se produto exigir.

## 5. Gates finais

| Gate | Resultado |
|---|---|
| Vitest DÉLIA completo | **225 PASS** (212 + 13) |
| Vitest plugin-ui completo | **2227 PASS** (+2 avatar) |
| Typecheck DÉLIA / plugin-ui | **PASS** |
| Build DÉLIA / plugin-ui + host-exports | **PASS** |
| Federation verify | **PASS** |
| Playwright standalone (demo MF) | **TEST_NOT_RUN** — dual-preview local falha MF React (`useState` null) sem gateway oficial; ver `playwright-mf-block.txt` |
| Portal/Dock autenticado | **TEST_NOT_RUN** |

## 6. Relação D02/D03 / 118

Preserva binding D02 e validação D03. Não avança C0–C7 nem declara aceite formal D01–D04. Residual Playwright/Portal auth permanece aberto (mesmo eixo D03).
