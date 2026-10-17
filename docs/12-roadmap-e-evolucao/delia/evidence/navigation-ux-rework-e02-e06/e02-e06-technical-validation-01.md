# E02–E06 — Validação técnica acumulada

**TASK_ID:** `DELIA-UX-NAV-REWORK-E02-E06-TECHNICAL-VALIDATION-01`  
**DATE:** 2026-10-17  
**BASE_HEAD:** `30aaa3c0560428f60d080118bd7788e9bb61210f` (= `origin/main` no reanchor)  
**CODE_CHANGED:** YES — apenas testes (`ConversationThreeRegionLayout.test.tsx`) para T05/T07/T09/T12  
**DEPLOY:** NOT_RUN  
**PHASE_PROGRESSION:** NONE  

## 1. Ambiente

| Campo | Valor |
|---|---|
| OS | Linux WSL2 `6.18.33.2-microsoft-standard-WSL2` |
| Node / npm | v20.20.0 / 10.8.2 |
| Branch | `main` |
| Git status (reanchor) | clean vs `origin/main` |
| Browser autenticado Portal | `TEST_NOT_RUN` → residual E09 |

## 2. Reancoragem canônica

- Roadmap 115 §4/§12–§19: E02–E06 `IMPLEMENTED` + visual observado; aceite técnico `ACCEPTANCE_PENDING`.
- Owner shell: `plugins/plugin-ui` (`ConversationThreeRegionLayout`, rail/panel/actions).
- Consumer: `plugins/delia` (`DeliaConversationPage`).
- `EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND`.
- Sem conflito de ownership; sem E07; sem alteração Core/Keycloak/Domain APIs.

## 3. Comandos e exit codes

| Bloco | Comando | EXIT | Resultado |
|---|---|---|---|
| A Vitest | `plugins/plugin-ui`: layout + NavigationRail + NavigationCategoryPanel + NavigationActions | **0** | 4 files / **24** tests PASS |
| B Vitest | `plugins/delia`: `DeliaConversationPage.test.tsx` | **0** | 1 file / **8** tests PASS |
| A typecheck | `npx tsc -p tsconfig.json --noEmit` (plugin-ui) | **2** | PREEXISTING_DEBT (sem erros em arquivos de navegação E02–E06) |
| B typecheck | `npm run typecheck` (delia) | **2** | PREEXISTING_DEBT via plugin-ui: InitialsAvatar, UnifiedAvatar/`PublishedAvatarProfile`, TaskDetailCard |
| A build | `npm run build` (plugin-ui = vite + verify-host-exports) | **0** | PASS; exports incluem `ConversationThreeRegionLayout`, `NavigationRail`, `NavigationCategoryPanel`, `NavigationActions` |
| B build | `npm run build` (delia) | **0** | PASS |
| B federation | `npm run verify:federation` (delia) | **0** | OK patches React federation |

**Nota:** exit code zero de pipeline com `| tee | tail` não foi usado como autoridade; exit codes acima são do processo npm/tsc direto.

## 4. Matriz T01–T12

| ID | Comportamento | Resultado | Evidência |
|---|---|---|---|
| T01 | Rail + painel desktop | **PASS** | Layout E02 + Delia E02 |
| T02 | Recolher/expandir; rail permanece | **PASS** | Layout E02 + Delia E02 |
| T03 | Quatro categorias sem desmontar centro | **PASS** | Delia E03 (Projetos/Agentes/Plugins/Conversas) |
| T04 | Drawer → centro `inert` | **PASS** | Layout E04 |
| T05 | Backdrop fecha drawer | **PASS** | Layout T05 (+ E04) |
| T06 | Escape fecha superfície ativa | **PASS** | Layout E04/E06 |
| T07 | Tab/Shift+Tab no drawer | **PASS_UNIT** (JSDOM + `getClientRects` mock) | Layout T07 — teclado real → E09 |
| T08 | Contexto → drawer fecha contexto | **PASS** | Layout E06 |
| T09 | Drawer → Contexto fecha drawer | **PASS** | Layout T09 |
| T10 | Fechar Contexto restaura foco | **PASS** | Layout E06 |
| T11 | Draft intacto | **PASS** | E02/E03/E04/E05/E06/T05/T09/T12 |
| T12 | Resize reconcilia overlays | **PASS_UNIT** (ResizeObserver controlado) | Layout T12 — geometria CSS container → E09 |

## 5. Classificação de falhas

| Classe | Itens |
|---|---|
| NEW_REGRESSION | **Nenhuma** nos fluxos E02–E06 |
| PREEXISTING_DEBT | TypeScript: `InitialsAvatar.tsx:198`, `layout/index.ts:274` (`PublishedAvatarProfile`), `TaskDetailCard.tsx:136`; mais dívida ampla no `tsc` full do plugin-ui (catalog/bpmn/charts/tests) **fora do escopo** |
| ENVIRONMENT_FAILURE | Nenhuma |
| TEST_DEFECT | Nenhuma após correção do teste T12 com `act()` |
| CONTRACT_MISMATCH | Nenhuma |

## 6. Correções nesta task

Único diff de produto/teste: extensão de `ConversationThreeRegionLayout.test.tsx` com casos T05, T07, T09, T12. **Sem alteração de implementação React/CSS** — comportamento já presente no HEAD.

## 7. Revisão (limitação de independência)

Revisão feita pelo mesmo agente que executou testes/cobertura. **Não constitui aceite independente E10.** Verificação de contratos React, ARIA, exclusividade, listeners (keydown/pointerdown/ResizeObserver cleanup), reuse de tokens/shell e boundaries: sem desvio material observado no código E02–E06.

| Etapa | Veredicto |
|---|---|
| E02 | **ACCEPT** |
| E03 | **ACCEPT** |
| E04 | **ACCEPT_WITH_RESIDUAL** (QA browser/Dock/larguras → E09) |
| E05 | **ACCEPT_WITH_RESIDUAL** (geometria CSS/container real → E09; visual 375 reusado) |
| E06 | **ACCEPT_WITH_RESIDUAL** (teclado/foco/zoom reais → E09) |

## 8. Residuais encaminhados

1. Browser autenticado Portal/Dock — matriz 320/375/420 + desktop + temas (E09).
2. Geometria real de container queries / clipping / focus browser (não coberta por JSDOM).
3. Dívida TypeScript preexistente (InitialsAvatar / UnifiedAvatar / TaskDetailCard) — owner fora desta task.
4. Review independente formal — E10.

## 9. Decisão

```text
E02_ACCEPTED=YES
E03_ACCEPTED=YES
E04_ACCEPTED=YES_WITH_RESIDUAL
E05_ACCEPTED=YES_WITH_RESIDUAL
E06_ACCEPTED=YES_WITH_RESIDUAL
ROADMAP_PROGRESS=6/10 ACCEPTED
PHASE_PROGRESSION=NONE
NEXT=E07_VISUAL_MOTION_POLISH_IF_GATES_SATISFIED
```
