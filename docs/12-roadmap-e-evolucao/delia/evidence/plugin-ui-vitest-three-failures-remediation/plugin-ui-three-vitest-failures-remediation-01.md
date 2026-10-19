# plugin-ui — remediação das 3 falhas residuais Vitest

**TASK_ID:** `DELIA-PLUGIN-UI-THREE-VITEST-FAILURES-REMEDIATION-01`  
**DATE:** 2026-10-19  
**REFERENCE_HEAD:** `1b2d6a6662b7d0557231b15211bf9c9fa4ee553a` (quitação TypeScript)  
**BASELINE_HEAD (suite):** `353eec04ce` + working tree dos 3 testes (main avançou com I02-R3A durante a task)  
**SOURCE:** residual de [TypeScript remediation](../plugin-ui-typescript-remediation/plugin-ui-typescript-29-errors-remediation-01.md)  
**PHASE_PROGRESSION:** NONE  
**EXECUTION_STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Ambiente

| Item | Valor |
|---|---|
| Node | v20.20.0 |
| Vitest | 3.2.7 |
| TypeScript | 5.9.3 |
| React | 19.2.7 |
| Comando | `npm test` em `plugins/plugin-ui` |

## 2. Baseline

| Campo | Valor |
|---|---|
| EXIT | 1 |
| Pass | **2222** |
| Fail | **3** |
| Files | 3 failed / 373 passed (376) |

Falhas:

1. `SignatureCapturePanel > gera blob ao digitar o nome` — `ctx.measureText is not a function`
2. `cipa shared exports > exports RichTextEditor` — `typeof` object ≠ function
3. `mention-composer.css > pílula 1.25rem…` — CSS usa token `0.85rem`, não `1.25rem`

Artefato: [baseline-vitest.txt](./baseline-vitest.txt).

Concurrent preservado: `plugins/plugin-ui/docs/12-roadmap-e-evolucao/` (untracked).

## 3. Diagnósticos

### F01 — SignatureCapturePanel / measureText

| Campo | Valor |
|---|---|
| RESPONSIBILITY | Frontend / qualidade de testes |
| OWNER | `SignatureCapturePanel.test.tsx` (mock) |
| CANONICAL_SOURCE | `blobFromTypedSignatureName.ts` + mock em `blobFromTypedSignatureName.test.ts` |
| CONSUMERS | SignatureCapturePanel typed mode |
| CONTRACT | Canvas2D `measureText` → TextMetrics |
| CLASSIFICATION | **TEST_DEFECT** |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | REUSE (padrão de measureText do teste unitário do owner) |
| ROOT_CAUSE | Mock de `getContext` omitia `measureText` exigido pelo fit de fonte |
| FIX | Incluir `measureText` no mock do teste typed (sem alterar produto) |

### F02 — SignaturePad / RichTextEditor export

| Campo | Valor |
|---|---|
| RESPONSIBILITY | Frontend / contrato de export |
| OWNER | `RichTextEditor` (`forwardRef`) |
| CANONICAL_SOURCE | `RichTextEditor.tsx` + `displayName` |
| CONSUMERS | SignaturePad.test “cipa shared exports” |
| CONTRACT | Componente React exportado (ForwardRefExoticComponent) |
| CLASSIFICATION | **TEST_DEFECT** |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | REUSE (asserção por `displayName` canônico) |
| ROOT_CAUSE | `typeof forwardRef === "object"`, não `"function"` |
| FIX | Assert `displayName === "RichTextEditor"` (sem novo export) |

### F03 — MentionComposer / CSS radius

| Campo | Valor |
|---|---|
| RESPONSIBILITY | Frontend / design tokens |
| OWNER | `mention-composer.css` |
| CANONICAL_SOURCE | `border-radius: var(--delpi-ui-mention-composer-radius, 0.85rem)` |
| CONSUMERS | MentionComposer + hosts via CSS var |
| CONTRACT | Token com fallback 0.85rem |
| CLASSIFICATION | **TEST_DEFECT** (expectativa stale) |
| EXISTING_EQUIVALENT | YES |
| REUSE_DECISION | REUSE (contrato visual vigente no CSS) |
| ROOT_CAUSE | Teste ainda exigia `1.25rem` hardcoded após migração para token |
| FIX | Expectativa alinhada ao `var(--delpi-ui-mention-composer-radius, 0.85rem)` |

## 4. Gates finais

| Gate | Resultado |
|---|---|
| Vitest F01/F02/F03 | **38/38 PASS** |
| Vitest plugin-ui completo | **2225/2225 PASS** (EXIT 0) |
| Typecheck plugin-ui | **PASS** (0 erros) |
| Typecheck DÉLIA | **PASS** |
| Vitest DÉLIA | **212/212 PASS** |
| Build plugin-ui + host-exports | **PASS** |
| Build DÉLIA | **PASS** |
| Federation | **PASS** |
| NEW_REGRESSIONS | **0** |
| UNSAFE_TYPE_SUPPRESSIONS | **0** |
| Produto/CSS alterados | **NÃO** (somente testes) |

## 5. Flakes estabilizados na suíte completa (F04)

Após F01–F03 verdes isolados, a suíte completa revelou:

| ID | Sintoma | Classificação | Fix |
|---|---|---|---|
| F04a | `DisplayFormatDialog` option antes do loader (skeleton) | TEST_DEFECT timing | `findByRole("option")` |
| F04b | Unhandled `window is not defined` pós-teardown (FiltersRow / ElementTogglePopover portals) | TEST_DEFECT cleanup | `afterEach(cleanup)` |

Sem alteração de produto. Suíte final EXIT 0, 2225/2225, Errors 0.

## 6. Relação com quitação TypeScript

Fecha o residual Vitest registrado em §6.254 / relatório TypeScript (ledger §6.257). Não altera o histórico daquela task nem declara aceite D01–D04.
