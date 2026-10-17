# E08 — Validação integrada e fechamento técnico (E07+E08)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E08-INTEGRATED-VALIDATION-AND-CLOSURE-01`  
**DATE:** 2026-10-17  
**BASE_HEAD:** `7cce718c3d8fd0fdfacff0ec4bb2438c227f21e1` (= `origin/main` no reanchor)  
**RELATED:** roadmap 115 §22–§24; ledger §6.226  
**DEPLOY:** NOT_RUN  
**PHASE_PROGRESSION:** NONE  

## 1. Ambiente

| Campo | Valor |
|---|---|
| OS | Linux WSL2 |
| Node / npm | v20.20.0 / 10.8.2 |
| Branch | `main` clean vs origin no reanchor |
| Browser Portal autenticado | `TEST_NOT_RUN` → residual E09 |

## 2. Reancoragem

- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND` (shell/CSS/scripts existentes).
- OWNER=`plugin-ui`; CONSUMER=`plugins/delia`; Portal host; Core/Domain inalterados.
- E02–E06 aceites preservados; sem reabertura sem defeito novo.
- E07 CSS presente no HEAD (`aria-current` marker, reduced-motion, sem `will-change` permanente).

## 3. Comandos executados

| # | Comando | EXIT | Resultado |
|---|---|---|---|
| 1 | plugin-ui Vitest nav (layout/rail/panel/actions) | **0** | 4 files / **24 PASS** |
| 2 | delia Vitest `DeliaConversationPage` | **0** | 1 file / **8 PASS** |
| 3 | delia `npm run typecheck` | **0** | **PASS** |
| 4 | plugin-ui `npx tsc -p tsconfig.json --noEmit` | **2** | **FAIL** — 29 erros PREEXISTING (após fix do cast T07); **0** no escopo Navigation/ThreeRegionLayout |
| 5 | plugin-ui `npm run build` (+ host-exports embutido) | **0** | **PASS** |
| 6 | plugin-ui `npm run verify:host-exports` | **0** | **PASS** (exports de navegação presentes) |
| 7 | delia `npm run build` | **0** | **PASS** |
| 8 | delia `npm run verify:federation` | **0** | **PASS** |
| 9 | Re-run nav Vitest após fix T07 cast | **0** | **24 PASS** |

## 4. Correção nesta task

| Arquivo | Motivo |
|---|---|
| `ConversationThreeRegionLayout.test.tsx` | Cast T07 `DOMRectList` incompleto → `as unknown as DOMRectList` + `Symbol.iterator` (erro TS no escopo de navegação) |

Sem alteração React/CSS de produto.

## 5. Inspeção E07 (código ≠ visual QA)

| Critério | Evidência de código | Status |
|---|---|---|
| Quatro categorias no rail | `NavigationRail` + testes | CODE_PASS |
| Selected marker não só cor | `aria-current=page` + `::before` + `font-weight:650` | CODE_PASS |
| focus-visible | outline 2px accent em rail/chrome/drawer | CODE_PASS |
| Tokens light/dark | `--delpi-ui-*` / `data-theme="dark"` focus rules | CODE_PASS (contraste medido → E09) |
| prefers-reduced-motion | múltiplos `@media` com `transition:none` | CODE_PASS |
| Sem will-change permanente | só `will-change:auto` no bloco reduced-motion | CODE_PASS |
| overflow-x | rail `overflow-x:hidden`; context compact idem | CODE_PASS |
| Geometria E04/E05 | medidas compact/rail inalteradas nesta inspeção | CODE_PASS |
| Seletores scoped | prefixo `.delpi-ui-conversation-*` / `.delpi-ui-navigation-rail` | CODE_PASS |
| Visual QA browser | — | **TEST_NOT_RUN → E09** |

## 6. Regressão E02–E06 (unit)

| Tema | Resultado |
|---|---|
| Rail + painel / collapse | PASS (layout + Delia) |
| Categorias + draft | PASS |
| Drawer inert / backdrop / Escape | PASS |
| Exclusividade drawer↔Contexto | PASS |
| Tab trap (JSDOM) / focus restore | PASS_UNIT |
| Resize reconcile | PASS_UNIT |

## 7. Classificação TypeScript

| Classe | Itens |
|---|---|
| NEW_REGRESSION (escopo nav) | Cast T07 — **corrigido** nesta task |
| PREEXISTING_DEBT | 29 erros: catalog(11), bpmn/charts/layout/preview/shape/signature/pdf/tests; `ConversationWorkspace.test.tsx` (1) fora do polish E07 |
| ENVIRONMENT_FAILURE | nenhuma |

`plugin-ui` full tsc permanece **FAIL exit 2** — residual justificado, não bloqueia gates delia/navegação.

## 8. Veredictos

| Etapa | Veredicto |
|---|---|
| E07 | **ACCEPT_WITH_RESIDUAL** (visual/contraste/zoom/Dock → E09) |
| E08 | **ACCEPT_WITH_RESIDUAL** (tsc full plugin-ui residual; browser → E09) |

```text
ROADMAP_PROGRESS=8/10 ACCEPTED
PHASE_PROGRESSION=NONE
INDEPENDENT_REVIEW=LIMITATION (mesmo agente) → E10
NEXT=E09_PORTAL_DOCK_BROWSER_QA
```
