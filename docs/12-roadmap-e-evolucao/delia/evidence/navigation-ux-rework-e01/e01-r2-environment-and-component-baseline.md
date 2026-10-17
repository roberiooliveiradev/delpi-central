# E01-R2 — Baseline técnico, ambiente e evidência (sem fix)

**TASK_ID:** `DELIA-UX-NAV-REWORK-E01-BASELINE-ENVIRONMENT-VALIDATION-R2`
**DATE:** 2026-10-17
**LOCAL_HEAD / ORIGIN_MAIN / REMOTE_HEAD:** `8a194d4a8c3d5c1e1cb84ac0983b106238547d80`
**CODE_CHANGED:** NO
**DEPLOY:** NOT_RUN (read-only)

## 1. Ambiente

| Campo | Valor |
|---|---|
| Workspace | WSL local + SSH `operador@192.168.1.237` (`HOST=srv-api`) |
| Git status | clean; `main...origin/main` |
| Node / npm | v20.20.0 / 10.8.2 (local) |
| Containers (srv-api) | `delpi-delia`, `delpi-plugin-ui`, `delpi-portal`, `delpi-gateway`, `delpi-delia-api` UP |
| HTTP | gateway `/` 200; `/apps/delia-api/health` 200; `remoteEntry` delia+plugin-ui 200; `https://minhadelpi.com.br/apps/delia` 200 (from srv-api) |
| Docker image git SHA label | **ABSENT** — compose labels have image digests only |
| delia image digest | `sha256:acf88d3510df…` (compose label); container created `2026-10-17T19:43:17Z` |
| plugin-ui image digest | `sha256:b64810ca0b91…`; created `2026-10-17T19:43:09Z` |
| SERVED delia `remoteEntry.js` sha256 | `4f63383e0a23fadf9b4282190688d446d3d14937ce6b75925992a2308f2a4ad5` |
| SERVED plugin-ui `remoteEntry.js` sha256 | `399828a82c19b283a525ede00888bb01b18eda538651ee8fe4be3d4cb37438ee` |
| BUILD_SOURCE_SHA | workspace HEAD `8a194d4a…` equals REMOTE_HEAD; image labels do not embed commit — correlation = HEAD + container recreate timestamp, not git-in-image proof |

## 2. Composição comprovada no código (HEAD)

### 2.1 Consumer — `DeliaConversationPage.tsx`

```text
left={({ collapsed, onExpand }) => collapsed
  ? <NavigationRail … onSelectCategory={(…) => { setCategory(…); onExpand(); }} />
  : <NavigationCategoryPanel …>}
```

- **Category owner:** local `useState` in DÉLIA (`category`).
- **Expansion owner:** `ConversationThreeRegionLayout` (`leftExpanded`).
- **Defect for AC-D01 / E02:** exclusive `rail XOR panel` — never simultaneous.
- Selecting a rail category calls `onExpand()` → panel replaces rail (AC-C01 target unmet).

### 2.2 Shell — `ConversationThreeRegionLayout.tsx` + CSS

| Concern | Evidence |
|---|---|
| Container measure | `ResizeObserver` on `rootRef.parentElement`; `compact = width <= 920` |
| Entering compact | auto `setLeftExpanded(false)` once |
| Backdrop | CSS `.delpi-ui-conversation-three-region__backdrop` exists; **no JSX element** → not clickable |
| Escape | closes **context only**; does not close left drawer |
| Context outside click | `pointerdown` outside context closes context |
| Context vs left | **no mutual exclusion** |
| Context position | absolute popover `top/right`, `width:min(360px,…)`, compact overrides |
| Center remount | layout keeps single `center` slot; unit tests prove text node identity across category toggles |

Structural probes executed (Python assert on sources): `EXCLUSIVE_LEFT_COMPOSITION`, `BACKDROP_CSS_WITHOUT_JSX`, `ESCAPE_CLOSES_CONTEXT_ONLY` = PASS.

## 3. Matriz AC — baseline (não correção)

| ID | Baseline status | Evidence class | Owner stage for fix |
|---|---|---|---|
| AC-D01 | **FAIL_CURRENT** (rail+panel not simultaneous) | CODE + prior user screenshots | E02 |
| AC-D02 | **CODE_PARTIAL** (920px compact + auto-collapse); live resize **TEST_NOT_RUN** | CODE | E04 (+ E09 live) |
| AC-C01 | **FAIL_CURRENT** (switch expands → loses rail) | CODE + unit | E03 |
| AC-M01 | **FAIL_CURRENT** (no backdrop JSX; Escape ignores left) | CODE + prior screenshots | E04 |
| AC-M02 | **CODE_PROVEN** positioning; live mobile **TEST_NOT_RUN** | CODE | E05 / E09 |
| AC-O01 | **FAIL_CURRENT** (no overlay exclusivity) | CODE | E06 |
| AC-A01 | **UNIT_PARTIAL**; live a11y/zoom/dark **TEST_NOT_RUN** | UNIT | E06 / E07 / E09 |
| AC-R01 | **PASS_UNIT** (center node preserved across category/collapse) | UNIT | — (regress in E08) |
| AC-B01 | **PASS_PARTIAL** (vitest/build/federation); browser matrix **TEST_NOT_RUN** | COMMANDS | E08 / E09 |

## 4. Comandos executados

```text
COMMAND: npm test -- ConversationThreeRegionLayout NavigationRail NavigationCategoryPanel NavigationActions
WORKDIR: plugins/plugin-ui
SOURCE_SHA: 8a194d4a8c3d5c1e1cb84ac0983b106238547d80
EXIT_CODE: 0
RESULT: 4 files / 16 tests PASS

COMMAND: npm test -- src/ui/DeliaConversationPage.test.tsx
WORKDIR: plugins/delia
EXIT_CODE: 0
RESULT: 5 tests PASS

COMMAND: npm run typecheck
WORKDIR: plugins/delia
EXIT_CODE: 0 (tsc prints pre-existing kit errors; no new nav errors)
RESULT: PASS_WITH_PREEXISTING_DEBT (InitialsAvatar / UnifiedAvatar / TaskDetailCard)

COMMAND: npm run build && verify-host-exports
WORKDIR: plugins/plugin-ui
EXIT_CODE: 0
RESULT: PASS; exports include ConversationThreeRegionLayout, NavigationRail, NavigationCategoryPanel, …

COMMAND: npm run build && npm run verify:federation
WORKDIR: plugins/delia
EXIT_CODE: 0
RESULT: PASS
```

## 5. Browser QA

```text
AUTHORIZED_PORTAL_BROWSER_MATRIX = TEST_NOT_RUN
REASON = no authenticated interactive browser session available to the executor;
         public HTTPS returns 200 from srv-api but login/session cannot be used here without exposing credentials.
LOCAL_UNIT_BASELINE ≠ PRODUCTION_VISUAL_QA
PRIOR_USER_SCREENSHOTS = retained as observational DEFECT_REPRODUCED_VISUALLY (doc 115 §10.3), not re-executed by this agent.
DOCK / light-dark / zoom200 / reduced-motion live = TEST_NOT_RUN → owned by E09
```

## 6. Defect ledger (for E02–E09; no fix in E01)

1. `DeliaConversationPage.tsx` → exclusive left composition → AC-D01 → E02 compose rail+panel
2. `onSelectCategory` → `onExpand()` → AC-C01 → E03 keep rail while switching
3. `ConversationThreeRegionLayout.tsx` missing backdrop node → AC-M01 → E04
4. Escape/outside only for context → AC-M01/AC-O01 → E04/E06
5. No drawer↔context exclusivity → AC-O01 → E06
6. Context absolute sizing on small containers → AC-M02 → E05

## 7. Verdict recommendation

```text
REVIEW_VERDICT = ACCEPT_WITH_RESIDUAL
E01_SCOPE_CLOSED = environment + canonical reanchor + code baseline + unit/build gates
RESIDUAL = AUTHORIZED_BROWSER_MATRIX → E09 (blocker for E10, not for starting E02 design)
INDEPENDENT_REVIEW = PENDING
PHASE_PROGRESSION = NONE
```
