# E10 / WF-15 — E10.S4 final acceptance evidence

**Date:** 2026-09-22  
**BASE HEAD:** `2faee80b24f6dec1b3a52fafdee561ffa797a11e`  
**Decision:** `GATE-FEATURE E10 = INCONCLUSIVE`  
**Reason:** federated Minha DELPI MFE bundle does not contain InventoryPage / `stock-balances` (deploy required). Help sync + automated suites + authenticated local BFF smoke are PASS.

## Ancestry (S1–S3)

| Step | SHA | Ancestor of HEAD |
|---|---|---|
| E10.S1 api-delpi | `abf47ec1cb283033266f1fcec9b13fae55f84808` | YES |
| E10.S2 supplies-api | `379ac45937a777a8e10f7ae419721a8555c0d0c9` | YES |
| E10.S3 MFE | `1970fb9150d29228600d3d21fae84047282dc4e6` | YES |

## Help sync

Minimal sync only (no duplicate ESTSEG definition):

- `SP_HELP.inventory*` tooltips (branch / warehouse / physical balance / stock value / filters / refresh / table meta)
- Quero→onde: «Consultar o estoque físico» → Estoque
- Mapa: Estoque = posição física; saldos +/0/−; ≠ disponível; ≠ ESTSEG
- FAQ: «Saldo físico é o mesmo que saldo disponível?»
- Glossário: «Saldo físico»
- `MANUAL_TOOL_TARGETS` Estoque → `inventory` preserved
- InventoryPage / Filters / ListTable wired to `SP_HELP`

## Automated tests

| Suite | Command | Result |
|---|---|---|
| api-delpi | `pytest -k 'stock_balances or branch_scope_normalization'` | **34 passed** |
| supplies-api | `docker exec … pytest -k 'inventory or stock_balance…'` | **12 passed** (11 BFF + 1 blueprint) |
| plugins/supplies | `npm test -- --run` | **180 passed** (35 files) |
| plugins/supplies build | `npm run build` | **PASS** |

## Authenticated BFF runtime smoke (local stack)

Environment: `http://localhost` + JWT via `infra/scripts/get-dev-token.sh` (token not persisted).  
Note: gunicorn workers were restarted once so bind-mounted inventory routes loaded; prior 404 was stale process, not contract failure.

| Case | Result |
|---|---|
| `GET …/summary` (Todas) | **200** `applied_filters.branches=["01","02"]`; product/warehouse/value present |
| `summary?branch=01` | **200** branches=`["01"]` |
| `summary?branch=02` | **200** branches=`["02"]` |
| `summary?branch=03` | **422** `Unknown branch: 03` |
| `items` page_size=5 | **200** pagination + `unit_of_measure` key |
| `items?sort=quantity_asc&page_size=50` | **200** `has_negative=true` (qty_min≈-6891) |
| zero sample | **PASS** — with `page_size=200&sort=quantity_asc`, 111 zeros observed |
| empty warehouse code | **PASS** — 4 rows with `warehouse=""` in sample (general list visibility) |
| null UM | **PASS** — 2 rows with `unit_of_measure=null` in sample |

`S2_AUTHENTICATED_BFF_SMOKE` residual → **PASS (local)**.

Prod path probe (unauthenticated): `https://minhadelpi.com.br/apps/supplies-api/inventory/stock-balances/summary` → **401** (route present). Authenticated prod BFF not completed in this session (SSO/Cloudflare headless instability); local auth smoke is the executed evidence.

## Federated smoke

| Check | Result |
|---|---|
| Prod App chunk `App--PbIEavc.js` | **no** `stock-balances` / `Controle de Estoques` / `Saldo físico`; still has `deliveries/late` |
| Local gateway MFE `App-omdSFLt9.js` (container from 2026-09-18) | same — **no** inventory strings |
| Local `plugins/supplies/dist` build | **has** inventory strings |
| Browser SSO to minhadelpi (Playwright) | session did not land on `/apps/supplies` reliably (`ERR_NETWORK_CHANGED` / bounce to `/login`) |
| **FEDERATED_SMOKE** | **INCONCLUSIVE** |
| **DEPLOY_REQUIRED_FOR_FINAL_GATE** | **YES** (MFE `plugins/supplies` + confirm BFF image on federated host) |

## UX / a11y / security runtime

| Item | Result |
|---|---|
| desktop/mobile/light/dark/keyboard | **INCONCLUSIVE** — blocked by missing federated InventoryPage |
| security negative (no `supplies.access`) | **INCONCLUSIVE** — no safe non-access identity exercised this session; automated AuthZ tests remain evidence |
| unit scope branch=03 | **PASS** (BFF 422) |

## FILTER_EMPTY_WAREHOUSE

| Rule | Status |
|---|---|
| Row with `warehouse=""` visible in general list | **PASS** (BFF runtime sample) |
| Dedicated “Sem código” filter | **RESIDUAL ACCEPTABLE** — not required for P0; not expanded in S4 |

## Residual search (code)

- No MFE→api-delpi for inventory (structural + query tests)
- No `only_positive` emission from MFE
- Copy distinguishes saldo físico ≠ disponível; ESTSEG separate
- No new permission introduced
- Placeholder inventory removed in HEAD App (not yet in deployed bundles)

## Gate

```text
GATE-FEATURE E10 = INCONCLUSIVE
E10.S4 = INCONCLUSIVE (Help+tests+BFF local PASS; federated missing deploy)
DEPLOY_REQUIRED = YES
E11 = NOT STARTED
```

Next: Infra/Deploy of `plugins/supplies` (and verify `supplies-api` on federated host) → re-run federated smoke → re-decide gate.
