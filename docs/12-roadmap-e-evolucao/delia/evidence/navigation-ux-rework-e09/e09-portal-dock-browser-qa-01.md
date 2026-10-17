# E09 — QA Portal/Dock: standalone local LIVE + Portal auth ainda pendente

**TASK_ID:** `DELIA-UX-NAV-REWORK-E09-PORTAL-DOCK-BROWSER-QA-01`  
**DATE:** 2026-10-17  
**BASE_HEAD (reanchor inicial):** `2f363b45bfe75cfbb02120d64abd08b498e68681`  
**REPO_HEAD ao fechar esta atualização:** `d6b999e21a18adb24b2b97db10631ce533b08a60` (+ docs desta sessão)  
**DEPLOY:** NOT_RUN (somente leitura/SSH na 1ª passagem; esta passagem = stack local)  
**PHASE_PROGRESSION:** NONE  
**E09_VERDICT:** `INCONCLUSIVE` — **não marcar** checklist E09 (Portal autenticado + Dock live ainda sem evidência)

## 1. Ambiente

### 1.1 Passagem srv-api (já registrada)

| Campo | Resultado |
|---|---|
| SSH `operador@192.168.1.237` (`srv-api`) | **PASS** |
| Containers Portal/DÉLIA/plugin-ui/gateway | UP; HTTP 200 |
| CSS E07 servido (`style-FEkHCoj8.css`) | **PROVEN** (`aria-current` `:before`, reduced-motion, `will-change:auto`) |
| Playwright no host WSL | download OK; launch **FAIL** (`libnspr4.so`) |

### 1.2 Passagem local (esta sessão)

| Campo | Resultado |
|---|---|
| Gateway `http://127.0.0.1/` | **200** |
| Keycloak container | **Up** (sem publish de porta no host; OIDC via gateway `/auth`) |
| plugin-ui Vite preview | `127.0.0.1:5010` |
| delia Vite `VITE_PLUGIN_UI_DEV=1` | `127.0.0.1:5020` → `/apps/delia/` **200** título `DÉLIA` |
| Playwright | imagem `mcr.microsoft.com/playwright:v1.64.1-jammy` `--network host` **PASS** |
| Credencial QA / password-grant | **não usada** (path com secrets bloqueado pelo auto-review) |
| Portal `/apps/delia/` sem sessão | spinner ~20s; **sem** rail e **sem** form de login observável → `PORTAL_AUTH_WALL=NOT_REACHED` |
| Dock unit (`portal` + `npx tsx --test`) | **23 PASS / 0 FAIL** |

Artefatos: [`local-standalone/`](./local-standalone/) (`matrix-result.json` + PNGs B01–B12/widths/portal).

## 2. Reuso de evidência visual do Product Master

Capturas roadmap 115 §14/§19: `VISUAL_OBSERVED_REUSED` para recortes estáticos B01–B04. **Superadas em parte** pela matriz LIVE standalone abaixo (mesma família de layout, superfície `delia` Vite local, não host Portal).

## 3. Matriz B01–B12

### 3.1 LIVE — DÉLIA standalone local (`http://127.0.0.1:5020/apps/delia/`)

| ID | Status | Evidência |
|---|---|---|
| B01 Desktop rail/painel | **PASS** | 1280: rail 64px + panel 249px + center; `aria-current=1`; sem overflow-x; `B01-1280.png` |
| B02 Categorias | **PASS** | Conversas/Projetos/Agentes/Plugins clicáveis; composer permanece; `B02-categories.png` |
| B03 Drawer mobile | **PASS** | 375 compact; panel overlay 288px; backdrop=1; center `inert=true`; `B03-375-drawer.png` |
| B04 ContextPopover | **PASS** | 375: contexto aberto (`opened=true`); `B04-context.png` |
| B05 Exclusividade overlays | **PASS** | drawer+contexto; Escape fecha; `escCloses=true` |
| B06 Draft | **PASS** | texto preservado após Projetos→Conversas |
| B07 Conversation state / stream | **TEST_NOT_RUN** | sem fixture de streaming |
| B08 Teclado real | **PASS** | Escape + Tab sample (rail→contexto→textarea); sem foco em ancestral `inert` após fechar |
| B09 ARIA/inert live | **PASS** | `inertCenter` true com drawer; false após Escape |
| B10 Contraste WCAG medido | **MEASUREMENT_INCONCLUSIVE** | probe leu `body` como `rgb(0,0,0)` vs fg `#111` (ratio 1.11) — artefato (UI branca nos PNGs); sem axe |
| B11 Zoom 200% | **PASS** | `documentElement.style.zoom=200%`; rail+composer visíveis; sem overflow-x |
| B12 Reduced motion live | **PASS** | `reducedMotion:'reduce'` → `transitionDuration=0s`, `willChange=auto`, MQ true |

### Larguras (standalone LIVE)

| Viewport | Status | compact | panel |
|---|---|---|---|
| 1440 / 1280 / 1024 | **PASS** | false | yes |
| 768 / 420 / 375 / 320 | **PASS** | true | collapsed until drawer |

### 3.2 Portal host + Companion Dock

| Cenário | Status |
|---|---|
| Portal autenticado matriz | **TEST_NOT_RUN** — sem sessão; unauth = spinner (`portal-unauth.png`, `portal-wait-*.png`) |
| Tema claro/escuro Portal | dark standalone **OBSERVED** (`theme-dark-1280.png`); Portal N/A |
| Companion Dock live | **TEST_NOT_RUN** |
| Dock unit | **PASS** (23 testes, `tsx --test`) |

## 4. Regressão técnica

| Comando | EXIT | Resultado |
|---|---|---|
| Playwright Docker matrix-probe | 0 | ver `local-standalone/matrix-result.json` |
| `npx tsx --test` globalDeliaDock*.test.ts | 0 | 23 PASS |
| (passagem anterior) plugin-ui layout+rail Vitest | 0 | 15 PASS |
| (passagem anterior) DeliaConversationPage Vitest | 0 | 8 PASS |
| (passagem anterior) delia typecheck | 0 | PASS |

`FIXES_APPLIED=NONE` (nenhum defeito de produto reproduzido no shell standalone).

## 5. Classificação

| Classe | Item |
|---|---|
| ENVIRONMENT_FAILURE | Portal local sem sessão OIDC observável (spinner); host Playwright `libnspr4` (mitigado via Docker image) |
| MEASUREMENT_INCONCLUSIVE | B10 contraste automático |
| PREEXISTING_DEBT | plugin-ui full tsc residual (E08) |
| NEW_REGRESSION | nenhuma no standalone LIVE |
| SCOPE_GAP_FOR_E09_ACCEPT | Portal autenticado + Dock live + B07 stream |

## 6. Decisão

```text
E09_STATUS=INCONCLUSIVE
E09_ACCEPTED=NO
CHECKLIST_E09=[ ]
LOCAL_STANDALONE_LIVE_MATRIX=PASS_PARTIAL (B01–B06,B08,B09,B11,B12 + widths; B07/B10/Portal/Dock gaps)
DOCK_UNIT=PASS
ROADMAP_PROGRESS=8/10 ACCEPTED
BLOCKER=AUTHENTICATED_PORTAL_AND_DOCK_LIVE_SESSION
SERVED_E07_CSS=PROVEN
PLAYWRIGHT_DOCKER_LOCAL=PROVEN
PHASE_PROGRESSION=NONE
NEXT=E09_AUTHENTICATED_PORTAL_DOCK_MATRIX_OR_PRODUCT_MASTER_LIVE_SESSION
```

Conforme roadmap 115 § E09: aceite exige QA integrado **Portal + Companion Dock**. Standalone local **não substitui** esse gate — por isso E09 permanece sem `[x]`.
