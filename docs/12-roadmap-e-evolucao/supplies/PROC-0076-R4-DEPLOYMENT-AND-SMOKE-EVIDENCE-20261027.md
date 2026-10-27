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

## 7. R4.1 — refinamento visual (2026-10-27)

EXECUTION ID: PROC-0076.R4.1 — VISUAL CLEAN REFINEMENT
DEPLOY SOURCE SHA: 4d89e85079 (origin/main)

### Escopo

Somente `plugins/supplies` (composição/estilos da feature) + reconciliação documental dos docs R4. Sem alteração em BFF, external-data-api, migrations, permissões ou cálculos — sem EXECUTION_DRIFT.

### Mudanças aplicadas

- Hero sem o badge de fonte redundante; apenas o alternador de perspectivas no corpo.
- Filtros contextuais em `FiltersRow` própria abaixo do hero/cards (indicador/série/NCM/câmbio + Dia/Semana/Mês/Ano + De/Até).
- `MarketInstrumentCard`: `Fonte pendente` como nota secundária (não badge); grade 3×2 e seleção múltipla preservadas; `aria-pressed`, teclado e foco mantidos; destaque accent apenas nos selecionados.
- Painéis `MarketIntelligencePanel`/`MarketMetalsPanel`: modo Gráfico/Tabela/Comparação e exportações nos `actions` do `SectionCard`; tabela nula suprimida quando a fonte está indisponível (estado honesto).
- CSS `.dashboard-supplies-portal`: cluster `sp-panel-actions`, ícone decorativo do KPI oculto nesta feature, borda de card mais leve, classe `__pending` como texto secundário — apenas tokens `--sp-*`/`--delpi-ui-*`.
- Docs R4 (wireframe aprovado + contrato UX) anotam o refinamento R4.1 (badge → nota secundária).

### Verificação

- `tsc --noEmit`: exit 0.
- Vitest feature: 25 passed (2 files). Suite completa: 503 passed (51 files).
- `npm run build`: OK (`App-DhoBazo_.js`, `style-CFWUoALP.css`).
- eslint `src/features/market-intelligence`: 0 erros, 4 warnings pré-existentes (set-state-in-effect/exhaustive-deps — baseline idêntico com as alterações em stash; erros do plugin inteiro = 5, todos pré-existentes fora da feature).
- Evidência desktop/mobile, claro/escuro e teclado: INCONCLUSIVE (sem captura de navegador autenticado nesta execução; estados preservados por tokens e `aria-*` conforme kit oficial).

### Deploy e smoke

- `git pull --ff-only` + `up-prod-sequential.sh --build supplies` em srv-api — OK.
- Bundle novo em `delpi-supplies`: `App-DhoBazo_.js` + `style-CFWUoALP.css` (Oct 26 23:15); remoteEntry.js regenerado apontando `__federation_expose_App-Dt-vXRp4.js` (presente); CSS contém `sp-panel-actions` e `__pending`.
- Smoke `/tmp/r4_smoke.py` reexecutado: 401/403/200 idênticos; 6 metais selectable/pending; quotes/series 3 séries 0 pontos `source_use_pending`; 404/422 inválidos; compare `insufficient_authorized_series`; fx week 5 períodos `provider_unavailable`; IPP 13 pontos/11 observados, último 2026-08=186.3691; comex 404 allowlist vazia; shell 200.

### Residuais R4.1

- Evidência visual em navegador (screenshots antes/depois, mobile, temas) pendente de sessão autenticada — não há drift funcional; layout aprovado preservado.
- `R4_1_CLEAN_UX_FUNCTIONAL_IN_PRODUCTION`: estrutura publicada e smoke verde; postcondição visual completa aguarda confirmação visual autenticada.
