# plugin-ui — remediação integral da dívida TypeScript

**TASK_ID:** `DELIA-PLUGIN-UI-TYPESCRIPT-29-ERRORS-REMEDIATION-01`  
**DATE:** 2026-10-19  
**BASE_HEAD / REFERENCE_HEAD:** `304583debb51248414eea60c36e8f1bbdd9965c8`  
**SOURCE_TASK (context):** `DELIA-UX-D03-PRESENCE-MOTION-AUTOMATED-VALIDATION-01` (registrou `TYPECHECK_PLUGIN_UI=FAIL_PREEXISTING_29`)  
**PHASE_PROGRESSION:** NONE (não avança C0–C7 nem aceita D01/D03/D04)  
**EXECUTION_STATUS:** `IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`

## 1. Ambiente

| Item | Valor |
|---|---|
| Node | v20.20.0 |
| TypeScript | 5.9.3 |
| React | 19.2.7 |
| `@types/react` | 19.2.17 |
| Package manager | npm (lockfile do pacote) |
| Comando canônico | `npx tsc -p tsconfig.json --noEmit --pretty false` (cwd `plugins/plugin-ui`) |

## 2. Baseline

| Campo | Valor |
|---|---|
| HEAD | `304583debb51248414eea60c36e8f1bbdd9965c8` (= `origin/main`) |
| EXIT | 2 |
| `INITIAL_TSC_ERRORS` | **29** |
| Códigos | TS2345×12, TS2741×5, TS7053×3, TS2353×3, TS2352×3, TS4104×1, TS2739×1, TS2532×1 |

Artefato bruto: [baseline-tsc.txt](./baseline-tsc.txt).

Concurrent preservado (não commitado nesta task): `plugins/plugin-ui/docs/12-roadmap-e-evolucao/`.

## 3. Reuse gate

| Necessidade | EXISTING_EQUIVALENT | REUSE_DECISION |
|---|---|---|
| Meta opcional de `vc()` | YES (`addedAt` já defaulta) | EXTEND typing (`Partial<Pick<…>>`) |
| Patch parcial de KPI frame | YES (merge runtime já parcial) | EXTEND `KpiPartStatePatch.frame` |
| CSS custom props do portal theme | YES (valores já emitidos) | EXTEND tipo `DelpiUiCssCustomProperties` |
| `points` readonly no layout | YES (`buildSeriesChartLayout`) | EXTEND input `readonly` |
| `source` opcional no preview loader | YES (nullable + `previewState`) | EXTEND `source?` |
| Fixtures BPMN incompletas | YES (cast de fixture) | REUSE via `as unknown as` justificado |
| Labels/classNames de testes | YES contratos públicos | EXTEND fixtures |

## 4. Matriz de causas-raiz (agrupada)

| Grupo | IDs | Causa-raiz | Correção | Contrato público |
|---|---|---|---|---|
| A Catalog | TS-001…011 | `vc` meta exigia `addedAt` via `Pick` | `Partial<Pick<…>>` | Não (helper interno) |
| B BPMN fixtures | TS-012…013 | cast parcial insuficiente | `as unknown as FlowchartEditorLabels` | Não (teste) |
| C Chart layout fixture | TS-014 | fixture com `width/height` obsoletos | stub alinhado a `SeriesChartLayout` | Não |
| D Chart kinds | TS-015 | faltava `horizontal_bar` no Record | entrada + seletor | Não |
| E Readonly points | TS-016 | input mutável vs golden readonly | `readonly SeriesChartPoint[]` | Compatível (alarga) |
| F Conversation | TS-017 | `footer` possibly undefined | assert + non-null | Não |
| G DataTable labels | TS-018 | faltava `loadingMessage` | fixture | Não |
| H ChartToolbar | TS-019 | faltavam `actions`/`exportButton` | fixture | Não |
| I FiltersRow | TS-020…021 | faltava `filterBoxSpacer` | fixture | Não |
| J KPI patch | TS-022 | patch `{x}` vs frame completo | `Partial<KpiPartFrame>` + defaults no merge | Sim (alarga patch) |
| K FilePreview | TS-023…024 + follow-on | estado legado `status/objectUrl`; `source` required-key | fixture canônica + `source?` | Sim (alarga options) |
| L CSS vars | TS-025…027 | index em `CSSProperties` | tipo custom props | Sim (tipo exportável) |
| M Canvas mock | TS-028 | assinatura `toBlob` errada | mock arrow | Não |
| N Print images | TS-029 | cast `Document.images` | `defineProperty` + cast HTMLCollection | Não |
| O Catalog assert | (Vitest) | expected `updatedAt` stale | alinhar ao inventário | Não |

## 5. Evolução da contagem

```text
INITIAL_ERRORS=29
BATCH_01_AFTER=18   # catalog Partial meta
BATCH_02_AFTER=2    # restantes + testes/fixtures/contracts
BATCH_03_AFTER=0    # source? no loader
FINAL_ERRORS=0
```

## 6. Gates

| Gate | Resultado |
|---|---|
| `TYPECHECK_PLUGIN_UI` | **PASS** (EXIT 0, 0 errors) — [final-tsc.txt](./final-tsc.txt) |
| `TYPECHECK_DELIA` | **PASS** (`npm run typecheck`) |
| `TYPECHECK_AFFECTED_CONSUMERS` | DÉLIA PASS; Portal `TEST_NOT_RUN` (diff não toca Portal) |
| Vitest plugin-ui | **2222 PASS / 3 FAIL_PREEXISTING** (SignatureCapturePanel typed blob, SignaturePad RichTextEditor export shape, MentionComposer CSS radius) — catálogo alinhado nesta task |
| Vitest DÉLIA | **212/212 PASS** |
| Build plugin-ui + host-exports | **PASS** |
| Build DÉLIA | **PASS** |
| Federation (delia verify patch) | **PASS** (`remoteEntry.js` + React patch OK) |
| `UNSAFE_TYPE_SUPPRESSIONS` | **0** (`@ts-ignore`/`@ts-nocheck`/`as any`/tsconfig weakenings: nenhum) |
| `NEW_REGRESSIONS` | **0** (3 falhas Vitest reproduzidas em HEAD limpo pré-diff) |
| `CONTRACT_BREAKING_CHANGES` | **0** (apenas alargamento opcional / typing) |

## 7. Relação com D02/D03

- D02/D03 registraram `TYPECHECK_PLUGIN_UI=FAIL_PREEXISTING_29` sem quitar a dívida.
- Esta task quita o typecheck; **não** altera retrospectivamente os resultados D02/D03 nem declara aceite formal de D01/D03/D04.
- Melhorias de presença/motion preservadas (suíte DÉLIA 212 PASS).

## 8. Residuais

1. Vitest plugin-ui: 3 falhas preexistentes fora do escopo TypeScript (canvas `measureText`, export RichTextEditor shape, CSS mention composer).
2. Portal typecheck/build: `TEST_NOT_RUN`.
3. Preferências/proatividade D03 Group E: permanece `PLANNED`/`TO_INVENTORY`.

## 9. Arquivos modificados (código)

Ver diff Git desta task (17 arquivos em `plugins/plugin-ui`). Evidência + ledger sob `docs/12-roadmap-e-evolucao/delia/evidence/`.
