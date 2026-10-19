# D03 — Validação automatizada de presença, estados e microinterações

**TASK_ID:** `DELIA-UX-D03-PRESENCE-MOTION-AUTOMATED-VALIDATION-01`  
**DATE:** 2026-10-19  
**BASE_HEAD (reanchor):** `552ff2e5cc` → ff `06cf0f22dab4ad4e294f882b3844027f170d1e28`  
**TESTED_SHA:** `06cf0f22dab4ad4e294f882b3844027f170d1e28` (+ fix de teste interaction no SHA final)  
**PHASE_PROGRESSION:** NONE  
**EXECUTION_STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`  
**D03_REVIEW_RECOMMENDATION:** `ACCEPT_WITH_RESIDUAL`

## 1. Reuse gate

| Necessidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Avatar motion idle/processing/responding/attention | YES (`UnifiedAvatar` + CSS) | REUSE |
| Pending row + ActivityViewer | YES (`App.tsx` D02) | REUSE |
| Composer stop cancelável | YES (`MessageComposer` + `App.requestMode`) | REUSE |
| Reception greeting | YES (`DeliaReception`) | REUSE |
| Dock host geometry (D01 CSS) | YES (`.global-delia-dock` overrides) | REUSE |
| Preferências / proatividade runtime | NO (editorial only) | — (não implementar) |

Owners preservados: plugin-ui / delia / Portal.

## 2. Comandos

| COMMAND | EXIT | RESULT |
|---|---:|---|
| `npx vitest run` (delia) — inicial | 1 | 211 PASS / 1 FAIL (`interaction` Enviando…) |
| fix `interaction.test.tsx` → retest | 0 | 212/212 PASS |
| plugin-ui related Vitest (avatar/activity/composer/layout/workspace) | 0 | 73 PASS |
| `npm run typecheck` delia | 0 | PASS |
| plugin-ui full `tsc --noEmit` | 2 | **29 PREEXISTING** (igual baseline D02) |
| `npm run build` + federation delia | 0 | PASS |
| `npm run build` plugin-ui (+ host-exports) | 0 | PASS; CSS `global-delia-dock`×12; processing `1.9s` |
| `npx tsx --test` Dock unit | 0 | 23 PASS |
| Playwright Docker standalone LIVE | 0 | ver §3 |
| Portal autenticado / Dock live | — | **TEST_NOT_RUN** |

## 3. Defeito corrigido

**FAIL:** `interaction.test.tsx` esperava botão `Enviando…` disabled durante MESSAGE in-flight.  
**CAUSA:** App seta `requestMode=responding_cancelable` → composer mostra `Interromper resposta` (contrato correto).  
**FIX:** teste alinhado ao stop cancelável; assert negativa de `Enviar`/`Enviando…`.  
**RETEST:** interaction 34 PASS; suite delia 212 PASS.  
**Código de produto:** inalterado.

## 4. Matriz D03-A01…A12

| ID | Status | Evidência |
|---|---|---|
| A01 Idle | **PASS** | Playwright full/docklike |
| A02 Sem progresso inventado | **PASS** | status textual único; sem etapas fictícias |
| A03 Processing pendente | **PASS** | `delpi-ui-unified-processing` 1.9s infinite |
| A04 Cleared | **PASS** | processing=0 pós-demo |
| A05 Responding one-shot | **PARTIAL** | captura pós-animação; assistente idle |
| A06 Return idle | **PARTIAL** | processing ausente; idle no turno |
| A07 Erro | **PASS** | demo error + Vitest |
| A08 Timeout | **TEST_NOT_RUN** | POST real |
| A09 Abort/cancel | **PASS** (Vitest) / browser demo **TEST_NOT_RUN** | interaction + MessageComposer |
| A10 Attention | **PASS** | clarification demo |
| A11 Multi-turn | **PASS** | 2+ turnos, sem processing residual |
| A12 Reduced motion | **PASS** | anim=none / 0s |

### Grupos B–E (resumo)

- **B Comunicação:** PASS — 1× `role=status`; ícone ActivityViewer `display:none`; sem segundo progresso no pending-row.
- **C Conversação:** PASS — reception, composer, draft em erro, stop cancelável (Vitest).
- **D Dock/full-page:** full 768–1440 + docklike 320–420 + dark + reduced + zoom200 **PASS** no standalone; CSS inject dock **PASS_PARTIAL**; Portal/Dock live **TEST_NOT_RUN**.
- **E Preferências/proatividade:** `TO_INVENTORY` / `PLANNED` — `personality/02` `RUNTIME_IMPLEMENTATION=NOT_PROVEN`; zero código em `plugins/delia/src`.

### Cobertura

```text
TOTAL_RQ=12 (A01–A12) + B/C/D/E gates materiais
APPLICABLE_A=12
VERIFIED_A=9
PARTIAL_A=2
BLOCKED_A=1 (A08) + A09 browser residual
TASK_VERIFIED_COVERAGE_PCT≈75 (A-only strict) | ≈83 se A09 Vitest conta
```

## 5. Residuais

- Portal autenticado + Companion Dock live (D01/D02/E09).
- Timeout / cancel transport real.
- Responding one-shot timing em captura.
- Preferências/proatividade: sem runtime — não implementar nesta task.
- plugin-ui tsc 29 PREEXISTING.

## 6. Decisão

```text
FIXES_APPLIED=TEST_ONLY (interaction.test.tsx)
D03_ACCEPTED=NO
D03_REVIEW_RECOMMENDATION=ACCEPT_WITH_RESIDUAL
NEXT=D01_DOCK_AUTH_LIVE_QA_OR_D04_PARITY_IF_AUTHORIZED
PHASE_PROGRESSION=NONE
```
