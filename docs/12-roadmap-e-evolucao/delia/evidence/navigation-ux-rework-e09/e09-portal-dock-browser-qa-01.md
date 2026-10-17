# E09 — QA Portal/Dock: ambiente provado, browser autenticado pendente

**TASK_ID:** `DELIA-UX-NAV-REWORK-E09-PORTAL-DOCK-BROWSER-QA-01`  
**DATE:** 2026-10-17  
**BASE_HEAD (reanchor inicial desta execução):** `2f363b45bfe75cfbb02120d64abd08b498e68681`  
**REPO_HEAD ao fechar documentação:** `6dd5f6d183138cb198496e77aafeefbc6bd7d940` (= `origin/main`)  
**DEPLOY:** NOT_RUN (somente leitura/SSH)  
**PHASE_PROGRESSION:** NONE  
**E09_VERDICT:** `INCONCLUSIVE` — **não marcar** checklist E09  

## 1. Ambiente

| Campo | Resultado |
|---|---|
| Workspace | WSL local; `main` sync |
| SSH `operador@192.168.1.237` (`srv-api`) | **PASS** (autorizado) |
| Containers | `delpi-delia`, `delpi-plugin-ui`, `delpi-portal`, `delpi-gateway`, `delpi-delia-api` UP |
| HTTP Portal `/apps/delia` | **200** (local + via srv-api) |
| `remoteEntry` delia / plugin-ui | **200** |
| Image git SHA labels | **ABSENT** |
| srv-api git HEAD (probe) | `2f363b45bf` → depois alinhado a `6dd5f6d183` |
| Browser MCP `cursor-ide-browser` | tools não invocáveis nesta sessão |
| Playwright Chromium local | download OK; launch **FAIL** (`libnspr4.so` missing) → probe unauth **ENVIRONMENT_FAILURE** |
| Credencial QA / storage state | **AUSENTE** → matriz autenticada **TEST_NOT_RUN** |

### Digests de assets (srv-api)

| Asset | Valor |
|---|---|
| DELIA_REMOTEENTRY_SHA256 | `4722efedff83f37554d1618a20d4d91690e32f7790f0f3ea2c471630d9c6d8a8` |
| PLUGIN_UI_REMOTEENTRY_SHA256 | `f1ff585567d265a54a150e68ba31e9e937d21f2457835b16ca1a12cd81515d7c` |
| Expose chunks | `App-DWZzVOov.js`, `Index-DYznBqB0.js`, CSS `style-FEkHCoj8.css` |
| plugin-ui container created | `2026-10-17T21:17:42Z` |
| delia container created | `2026-10-17T20:25:09Z` |

**DEPLOYED_SHA_VERIFIED:** parcial — git HEAD do checkout em srv-api == `origin/main` no momento do probe; labels OCI sem revision; correlação por remoteEntry + chunk names + CSS servido.

### CSS E07 nos assets servidos (`style-FEkHCoj8.css`)

| Marker | Count |
|---|---:|
| `prefers-reduced-motion` | 41 |
| `will-change:auto` | 1 |
| `navigation-rail__item[aria-current` | 3 |
| `overflow-x:hidden` | 9 |
| selected bar `:before` + `inset-inline-start:2px` | **PRESENT** |

## 2. Reuso de evidência visual do Product Master

Capturas já registradas no roadmap 115 §14/§19 (desktop rail+painel; mobile 375 drawer/contexto). Classificação: `VISUAL_OBSERVED_REUSED` para recortes estáticos B01–B04 **sem** prova de SHA dos assets da captura nem interação teclado/contraste/zoom/Dock.

## 3. Matriz B01–B12

| ID | Status | Evidência |
|---|---|---|
| B01 Desktop rail/painel | **VISUAL_OBSERVED_REUSED** + unit PASS | Screenshots PM + Vitest E02 |
| B02 Categorias | **VISUAL_OBSERVED_REUSED** + unit PASS | Screenshots PM + Delia E03 |
| B03 Drawer mobile | **VISUAL_OBSERVED_REUSED** + unit PASS | Screenshots PM 375 + Vitest E04 |
| B04 ContextPopover | **VISUAL_OBSERVED_REUSED** + unit PASS | Screenshot PM 375 + Vitest E05 |
| B05 Exclusividade overlays | **UNIT_PASS** / live **TEST_NOT_RUN** | Vitest E06; browser auth ausente |
| B06 Draft | **UNIT_PASS** / live **TEST_NOT_RUN** | Vitest; browser auth ausente |
| B07 Conversation state / stream | **TEST_NOT_RUN** | Sem fixture streaming autorizada |
| B08 Teclado real | **TEST_NOT_RUN** | Auth + browser automation |
| B09 ARIA/inert live | **TEST_NOT_RUN** (unit cobre parcial) | |
| B10 Contraste WCAG medido | **TEST_NOT_RUN** | Sem axe/medição |
| B11 Zoom 200% | **TEST_NOT_RUN** | |
| B12 Reduced motion live | **CODE_SERVED** (CSS) / runtime **TEST_NOT_RUN** | |

### Larguras / temas / Dock

| Cenário | Status |
|---|---|
| 1440/1280/1024/768/420/375/320 live | **TEST_NOT_RUN** (auth) |
| Tema claro/escuro live | **TEST_NOT_RUN** |
| Companion Dock live | **TEST_NOT_RUN** |
| Dock unit (`portal` globalDeliaDock) | **ENVIRONMENT_FAILURE** (`tsx` ausente no runner local desta sessão) |

## 4. Regressão técnica (sem alteração de produto)

| Comando | EXIT | Resultado |
|---|---|---|
| plugin-ui layout+rail Vitest | 0 | 15 PASS |
| DeliaConversationPage Vitest | 0 | 8 PASS |
| delia typecheck | 0 | PASS |

`FIXES_APPLIED=NONE` (nenhum defeito live reproduzido).

## 5. Classificação

| Classe | Item |
|---|---|
| ENVIRONMENT_FAILURE | Sem sessão autenticada Keycloak; Playwright Chromium não concluído; portal `tsx` missing para dock unit |
| PREEXISTING_DEBT | plugin-ui full tsc residual (E08) |
| NEW_REGRESSION | nenhuma observada |

## 6. Decisão

```text
E09_STATUS=INCONCLUSIVE
E09_ACCEPTED=NO
CHECKLIST_E09=[ ]
ROADMAP_PROGRESS=8/10 ACCEPTED
BLOCKER=AUTHENTICATED_BROWSER_QA_SESSION
SERVED_E07_CSS=PROVEN
NEXT=E09_AUTHENTICATED_PORTAL_DOCK_MATRIX_OR_PRODUCT_MASTER_LIVE_SESSION
PHASE_PROGRESSION=NONE
```

Conforme roadmap 115 § E09: sem browser autenticado **não marcar** E09.
