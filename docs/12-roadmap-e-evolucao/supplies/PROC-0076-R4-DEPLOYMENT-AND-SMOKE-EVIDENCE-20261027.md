# PROC-0076.R4 — （2026-10-27）

EXECUTION ID: PROC-0076.R4-IMPLEMENTATION
DEPLOY SOURCE SHA: 3369a1327fc77e9ac98b79e5454099d9396eae6a（origin/main）
BASE HEAD: e3d81d9c7e（rebase  origin/main）

## 1. 

|  |  |  |
|---|---|---|
| external-data-api | V006 （granularity day/week/month/year + observation_timestamp + ）； selectable_in_ui / data_access_allowed / supported_granularities |  |
| supplies-api | week ISO ；quotes/series（ availability+summary）；quotes/compare ；filters / |  |
| plugins/supplies |  metals/fx/indicators；；；//；URL R4 + R3/R2 ；MarketInstrumentCard  |  |

 HEAD = 3369a1327f。 delpi-external-data-api / delpi-supplies-api / delpi-supplies ；delpi-supplies  App-BbTD0a67.js（Oct 26 22:26） R4 （sp-market-instrument）。

## 2. 

external_data.schema_migrations  = V001…V006。V006 ：metal_quote_observations CHECK  day/week/month/year；observation_timestamp TIMESTAMPTZ ；(instrument_id, observation_timestamp, source_id) 。。

## 3. （2026-10-27， https://minhadelpi.com.br）

 /tmp/r4_smoke.py（srv-api）。 user（user@local.com， supplies.access）； devin-smoke-r4（、）—— delpi-central direct grant  token，。

### 

|  |  |
|---|---|
|  token GET /market-intelligence/filters | 401 |
|  token GET /market-intelligence/quotes/series | 401 |
|  token GET /filters | 403 forbidden |
|  token GET /quotes/series | 403 forbidden |

### （）

|  |  |
|---|---|
| GET /filters | 200： aluminum/copper/lead/nickel/tin/zinc  selectable_in_ui=true、data_access_allowed=false；fx usd-brl  true；IPP  2；Comex NCM 0（feed 、） |
| GET /quotes/series?instruments=copper,aluminum,zinc&granularity=month | 200： points:0、availability source_use_pending、summary observed:null、meta data_status:no_data ——  |
| GET /quotes/series?instruments=nope-metal | 404 not_found |
| GET /quotes/series（ instruments） | 422 unprocessable |
| GET /quotes/series?granularity=bogus | 422 unprocessable |
| GET /quotes/compare?instruments=copper,aluminum | 200 comparable:false、reason:insufficient_authorized_series |
| GET /fx/series?fx_kind=ptax_closing_sell&granularity=week | 200：5  ISO 、observed:0、unavailable_reason:provider_unavailable（PTAX feed ） |
| GET /producer-prices/series?series_id=ipp-metalurgia-index | 200：13  11 ， 2026-08 = 186.3691（IBGE ） |
| GET /imports/series?ncm=74040000 | 404 unknown import ncm（Comex ， R4 ） |
| GET /apps/supplies/ | 200（MFE ） |

## 4. 

- R4_DASHBOARD_FUNCTIONAL_IN_PRODUCTION — 、、、、、URL/AuthZ/S2S 。
- METALS_REAL_DATA_PENDING_SOURCE_APPROVAL — ；source_use_pending  data_access_allowed=false ，。
- COMEX_FEED_EMPTY_PREEXISTING — Comex NCM ， R4 。
- PTAX_PROVIDER_UNAVAILABLE_HONEST — ，。

## 5. 

- external-data-api unit：238 passed, 9 skipped；PG /。
- supplies-api：588 passed（ 11  R4 BFF ）。
- plugins/supplies：503 passed（51 ）；feature 25；build ；lint  error。
- ： 3  up-prod-sequential。

## 6. 

- （owner：/），UI ； ingestion adapter + display_allowed 。
- Comex NCM  ——  feed ，。
- plugins_hub collation （ 2.41 vs  2.36），，。
-  bundle >500KB chunk （），。
