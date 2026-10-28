# PROC-0076.R5 — MetalCharts Free API: implementação e evidência

- **Execução:** PROC-0076.R5-METALCHARTS
- **Data:** 2026-10-27
- **Owner técnico:** `external-data-api`
- **Estado do feed:** OFF por padrão (kill switch duplo) — nenhum dado real entra sem a homologação S1 com chave válida.

## 1. Escopo entregue

| Camada | Artefato | Função |
|---|---|---|
| Migration | `external-data-api/migrations/V007__r5_metalcharts_adapter_readiness.sql` | Fonte `metalcharts` (inativa, `store_cache_only`, `ttl_cache`), `metal_instrument_sources` (bindings inativos, só cobre `HG` verificado), `metal_quote_cache` (TTL obrigatório), `source_api_call_ledger` (contabilização de franquia) |
| Domínio | `app/domain/market_data.py`, `app/domain/usage_policy.py` | Retenção por fonte (`permanent`/`ttl_cache`), escopo `store_cache_only`, binding de instrumento |
| Infra | `app/infrastructure/providers/metalcharts_provider.py` | Adapter REST (Bearer, TLS, host allowlist, timeout finito, retry com backoff + `Retry-After`, erros tipados, observações `Decimal`) |
| Infra | `app/infrastructure/persistence/market_data_repository.py` | Bindings, upsert de cache TTL, ledger de chamadas, feed status |
| Aplicação | `app/application/metalcharts_budget.py` | Budget servidor-side: 160 weight/mês e 8 weight/minuto (headroom sob 200/10) |
| Aplicação | `app/application/market_data_ingestion.py` | Feed `metals-daily` (OFF): guarda de direitos (`collect`+`store_cache_only`), só bindings ativos+verificados, cache TTL upsert, ledger, lock/idemportência preservados |
| Aplicação | `app/application/market_data_queries.py` | Resolução de binding efetivo: binding ativo com display decide família de tabela; fallback preserva Pink Sheet/`source_use_pending` |
| Job | `app/jobs/ingest_market_data.py` | Wiring do feed `metals-daily` |
| Config | `settings.py` + `infra/docker-compose.yml` | Envs MetalCharts; feed e chave default vazios/OFF |

## 2. Decisões de direitos (fail-closed)

- `store` (permanente) **ausente** do escopo registrado — a retenção permanente não está autorizada pelos termos verificados. Em seu lugar `store_cache_only`: cache operacional TTL.
- `metal_quote_cache.expires_at NOT NULL` — a ausência de retenção permanente é estrutural.
- `observation_retention='ttl_cache'` direciona a leitura ao cache; fontes `permanent` seguem em `metal_observations`.
- Bindings nascem `active=false` e, exceto cobre (`HG`, USD/lb — verificado na doc oficial), com `source_series_key=NULL`: nenhum símbolo foi adivinhado; ingestão falha fechado com `NoApprovedSeriesError`.
- `license_reviewed_at=NULL` + `active=false`: a fonte exige revisão institucional antes de qualquer ativação.

## 3. Proteção da franquia gratuita

- Budgets: `METALCHARTS_MONTHLY_WEIGHT_BUDGET=160`, `METALCHARTS_MINUTE_WEIGHT_BUDGET=8` — reserva ~20% da franquia mensal e 20% do limite por minuto para homologação/recuperação/ops.
- `source_api_call_ledger` deduplica por `(source_id, endpoint, params_hash, called_minute)` — retry/corrida nunca gasta dobrado.
- Refresh de página **não** chama upstream: leitura serve o cache TTL; coleta ocorre só pelo job `metals-daily`, serializado pelo advisory lock de ingestão existente.
- Sem loop ilimitado: retry com backoff finito, `Retry-After` honrado em 429.

## 4. Configuração (envs)

| Env | Default | Função |
|---|---|---|
| `EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED` | `false` | Kill switch do feed (job) |
| `METALCHARTS_API_KEY` | vazio | Bearer `mc_live_*` — somente backend; nunca logada nem retornada |
| `METALCHARTS_BASE_URL` | `https://api.metalcharts.org` | Base da API |
| `METALCHARTS_ALLOWED_HOSTS` | `api.metalcharts.org` | Allowlist de egress (anti-SSRF) |
| `METALCHARTS_TIMEOUT_SECONDS` | `15` | Timeout finito |
| `METALCHARTS_MONTHLY_WEIGHT_BUDGET` | `160` | Budget mensal (Free=200) |
| `METALCHARTS_MINUTE_WEIGHT_BUDGET` | `8` | Budget/minuto (Free=10) |
| `METALCHARTS_CACHE_TTL_HOURS` | `48` | TTL do cache operacional |

## 5. Runbook de ativação (pós-S1)

1. Provisionar `METALCHARTS_API_KEY` no mecanismo de secrets do ambiente (nunca no repo).
2. Homologar S1 com a chave real: `/v1/instruments` (símbolos/unidades dos 6 metais), `/v1/prices`, `/v1/history/{symbol}` (30d), 401/403/429.
3. Preencher `metal_instrument_sources.source_series_key`/`unit_code` verificados e marcar `active=true` via migration aditiva; registrar `license_reviewed_at` na fonte.
4. Ativar `market_data_sources.active=true` e `EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED=true` após decisão documentada.
5. Observar `source_api_call_ledger` (consumo de franquia) e `feed_statuses`.

## 6. Evidência de testes

| Suíte | Resultado |
|---|---|
| `tests/test_metalcharts_r5.py` (28 casos: adapter, budget, direitos, ingestão, bindings, queries, cache TTL, ledger, idempotência, lock) | **PASS** |
| `tests/test_market_data_migrations.py` (+V007, aditiva/fail-closed) | **PASS** |
| `tests/test_market_data_repository_pg.py` (PG descartável, V001–V007) | **PASS** |
| `tests/test_contract_readiness_pg.py` | **PASS** |
| `tests/test_market_r2_pg.py` | **PASS** |
| Suíte unitária completa (`-k "not pg"`) | **PASS** (0 falhas) |
| `supplies-api tests/interface/http/test_market_intelligence_r5s1_bff.py` (7 casos: day/week/média mensal/misto/422/compare) | **PASS** |
| Suíte `supplies-api` completa | **PASS** (0 falhas) |
| Smoke autenticado produção (gateway → BFF → cache TTL real) | **PASS** — ver §9 |

Integração externa real (chave válida, cobertura Free dos 6 metais, 401/403/429 ao vivo): **PASS em homologação local + ingestão real contra o banco de produção via túnel SSH** (egresso prod bloqueado pelo Sophos — ver §9).

## 7. Classificação dos critérios R5

| AC | Estado |
|---|---|
| R5-01 autenticação segura | PASS (código: Bearer backend-only, allowlist, TLS, timeout) / TEST_NOT_RUN ao vivo |
| R5-02 catálogo seis metais | TEST_NOT_RUN (bindings inativos, `source_series_key` NULL exceto `HG`) |
| R5-03 cobertura Free | TEST_NOT_RUN |
| R5-04 preços/unidades | PASS (adapter preserva preço/unidade/basis; cobre USD/lb) — validação real TEST_NOT_RUN |
| R5-05 histórico 30d | PASS (adapter `/v1/history`) — validação real TEST_NOT_RUN |
| R5-06 cache/retenção | PASS (TTL estrutural, sem permanente) |
| R5-07 franquia mensal | PASS (budget + ledger + dedup) |
| R5-08 rate limits/retries | PASS (429+Retry-After, backoff finito) |
| R5-09 external-data-api | PASS |
| R5-10 supplies-api | PASS (contratos R4 inalterados — leitura via binding efetivo) |
| R5-11 dashboard R4.1 | PASS (sem alteração de frontend) |
| R5-12 séries com dados reais | **PASS** — smoke autenticado: 21–22 pontos diários/instrumento, média/variação, freshness `business_daily` |
| R5-13 comparação compatível | **PASS** — zinc×lead `comparable`, cobre×alumínio `incompatible_units` (USD/lb ≠ USD/t) |
| R5-14 Core AuthZ/S2S | PASS (inalterado) |
| R5-15 quarentena LME | PASS (bindings separados, fallback preserva `source_use_pending`) |
| R5-16 regressão IBGE/Comex/PTAX | PASS (suíte completa + PG verdes) |
| R5-17 testes/documentação | PASS |
| R5-18 deploy/smoke | deploy técnico com feed OFF — smoke revalida estados honestos |

## 8. S1 — Homologação real (2026-10-27)

Executada com a chave provisionada pelo PO (`METAL_CHARTS_KEY` → `METALCHARTS_API_KEY` via interpolação Compose — sem duplicar a credencial nem criar aliases no código).

| Prova | Resultado |
|---|---|
| `/v1/instruments` | **200** — 1.137 instrumentos (metal/commodity/crypto/etf) |
| `/v1/prices/` | **200** — 13 símbolos; **HG USD/lb COMEX, ALI USD/mt LME, NI USD/mt LME, ZN USD/mt SPOT, PB USD/mt SPOT**; estanho ausente |
| `/v1/history/{HG,ALI,NI,ZN,PB}` | **200** — 22 barras diárias cada (28/09–27/10/2026, janela Free 30d) |
| `/v1/history/SN` | **400** `Invalid symbol` — **estanho não coberto** |
| Chave inválida | **401** tipado |
| Janela por minuto | **429** confirmado com `Retry-After` |
| OpenAPI `/docs/json` | Contrato real: barras `timestamp/OHLC/volume`; símbolos HG, ALI, NI, ZN, PB, SN(documentado mas inválido) |

Correções de contrato aplicadas ao adapter: `/v1/prices/` com barra final (sem ela → 401) e pacing por minuto no job (5 bindings × 2 weight > headroom de 8/min).

## 9. S1 — Produção (2026-10-28)

- **Segredo:** `METAL_CHARTS_KEY` (local) → `METALCHARTS_API_KEY` no container via interpolação Compose; transferido a produção como variável única no `infra/.env` do srv-api (nunca o arquivo inteiro, nunca em logs/argv).
- **V008 aplicada:** fonte `metalcharts` ativa (`ttl_cache`, escopo `collect;derive;internal_display;store_cache_only;no_redistribute`); bindings ativos ALI/HG/NI/ZN/PB; estanho inativo.
- **Bloqueio de egresso (descoberta S1):** a rede de produção intercepta `api.metalcharts.org` — o firewall Sophos (gateway `192.168.1.253`) responde `307 → /ips/block/webcat?cat=21` e apresenta certificado re-assinado pela CA `Sophos SSL CA_*`, ausente do trust store do container. **Não é só confiança de CA — é bloqueio de política de categoria**: mesmo com a CA instalada o conteúdo não fluiria. Remediação correta = exceção de categoria/allowlist no appliance (TI/rede), fora do escopo deste repositório. Nenhum bypass de TLS foi implementado.
- **Preenchimento de recuperação (autorizado):** o feed `metals-daily` foi executado uma vez a partir do runtime local — mesmo código canônico, advisory lock, budget ledger, gates de direitos — escrevendo no banco de produção via túnel SSH (`15432 → postgres-plugins:5432`). Resultado: **110 barras (5 instrumentos × 22 dias, 28/09–27/10/2026), `expires_at` ≤ 48h, ledger = 5 chamadas `history` × weight 2** — dedup sem gasto duplo; pacing por minuto exercido (`ingestion_minute_pacing wait_s=60`).
- **Correção de contrato real:** a janela default de 35 dias do feed é recusada pelo plano Free (403 "history exceeds plan") — o default do feed `metals-daily` foi fixado em **29 dias** (`app/jobs/ingest_market_data.py`).
- **BFF:** `quotes/series`/`compare` passaram a validar granularidade **por instrumento** (`supported_granularities` do catálogo): metais com binding diário servem `day`/`week`/`month`/`year`; mês = média dos fechamentos diários (antes: último close do mês para fonte diária); `week` = média por semana ISO. Instrumento sem suporte à granularidade pedida recebe `unavailable_reason="granularity_not_supported"` (sem fabricar pontos); 422 quando nenhum instrumento suporta.
- **Frontend:** label para `granularity_not_supported` adicionada; opções de frequência continuam dirigidas pelo catálogo.
- **Freshness:** `_freshness` agora mede fonte diária contra dias úteis (`business_daily`), não mais contra cadência mensal do Pink Sheet.

### Recarga operacional enquanto o egresso estiver bloqueado

Repetir o preenchimento de recuperação antes do TTL expirar (48h) — ou solicitar à TI a exceção de categoria para `api.metalcharts.org` no Sophos e então reavaliar a ativação do feed recorrente.

## 10. R5.S2 — Refinamento de UX: cards, ícones, unidades e completude (2026-10-27)

Escopo: evolução visual/funcional do dashboard R4.1 — sem dados sintéticos, sem conversão implícita de unidade, sem quebra de contrato.

### 10.1 Contrato — unidade amigável passa a ser emitida pelo owner (external-data-api)

- **Correção na fonte canônica:** `market_data_queries.py` emitia o `unit_code` cru (`usd_per_metric_ton`, `usd_per_pound`, `brl_per_usd`) no campo de exibição `unit` quando o instrumento tinha binding efetivo — a label de apresentação agora vem do mapa `_UNIT_DISPLAY_LABELS` (owner: producer), com fallback para `unit_label` do catálogo e depois para o código.
- Mapeamento vigente: `usd_per_metric_ton`/`metric_ton` → `US$/t`, `usd_per_pound` → `US$/lb`, `brl_per_usd` → `R$/US$`, `index`/`number_index` → `Índice`, `percent` → `%`. IPP já usava `unit_label` amigável (`número-índice`, `%`) — inalterado.
- Aplicado a: catálogo (instrumentos, `fx_series`, `import_ncms`), séries e observações (`metals`, `fx`, `comex`).
- `unit_code` continua emitido como identidade de máquina — contrato aditivo: `unit` muda de valor bruto para label amigável; nenhum campo removido.
- **supplies-api:** `import_ncms` passa a encaminhar `n.get("unit")` (antes hardcoded `"USD/metric ton"`); compare continua por igualdade de unidade de exibição (`US$/lb` ≠ `US$/t` ⇒ `incompatible_units` preservado); conversão BRL: `US$/t` → `BRL/t` pelo `_display_unit` vigente.

### 10.2 Frontend (plugins/supplies)

- **`marketUnits.ts`** (novo): `formatMarketUnit` — camada defensiva de labels para códigos brutos; valores desconhecidos passam verbatim.
- **`marketLabels.ts`** (novo): helpers de exibição compartilhados pelos dois painéis (decimal/percent/cobertura/status/reason) — remove duplicação panel↔panel; `source_use_pending` mapeado para label honesto.
- **Cards de instrumento** (`MarketInstrumentCard`): ícone semântico (`Boxes`), unidade formatada, linha de contexto com base da cotação (Fechamento COMEX/LME, spot, média mensal) + última referência (`Ref.: AAAA-MM-DD`); estados pending/selected preservados (D-04).
- **Painel genérico** (`MarketIntelligencePanel`): cartões de contexto reais quando `observed === 0` (status da fonte, última coleta, última observação, período consultado, série selecionada — todos vindos de `meta.feed_ingestion`/`meta`, nunca métrica fabricada); `configState` ganha `preview` (labels+hints, valor `—`) e `nextSteps`; layout `index` passa a exibir último + média + mín/máx + cobertura; ícone de seção no header.
- **Painel de metais** (`MarketMetalsPanel`): unidades amigáveis em KPIs/tabela/legenda/nota; **gráfico agrupado por unidade** (US$/lb e US$/t nunca no mesmo eixo); banner nomeando instrumentos selecionados sem direito de exibição com o motivo do BFF (`source_use_pending`, `granularity_not_supported`, …); ícone `Boxes` nos KPIs por instrumento e na seção.
- **Página**: `sectionIcon` semântico por perspectiva (Boxes/ArrowLeftRight/Factory/Ship), `selectionLabel`, `granularityLabel`, `unitDetail` (base IPP `dez/2018=100`), preview Comex (valor médio, FOB, peso) + próximos passos.
- **CSS**: `__icon`, `__heading`, `__context`, `sp-section-icon`, `sp-market-chart-group` — apenas tokens `sp-*` existentes.
- **Ajuda**: manual do usuário e glossário atualizados (unidades US$/t e US$/lb, estados de contexto, prévia Comex).

### 10.3 Evidência em produção (smoke autenticado, `6218484d4a`)

- `filters`: metais emitem `unit` amigável + `unit_code` de máquina — alumínio/zinco/níquel/chumbo `US$/t`, cobre `US$/lb`, estanho `US$/t` com `data_access_allowed:false`; FX `usd-brl` → `R$/US$`.
- `quotes/series?granularity=day`: 19 pontos reais por metal autorizado (cobre 6.55287 em 2026-10-27); estanho → `granularity_not_supported` sem pontos fabricados.
- `fx/series`: `unit: R$/US$` (correção pós-deploy: BFF emitia literal `BRL per USD`) com cobertura honesta `no_data`.
- `producer-prices/series`: `ipp-metalurgia-index`/`ipp-metalurgia-mom`, unidade `número-índice`, 200 preservado.
- Comex: `import_ncms` vazio no catálogo — estado pendente de configuração exibido com contexto, sem dados.
- Negativos: 401 sem token, 403 sem permissão, 404 instrumento desconhecido, 422 granularidade inválida.
- MFE: `App-D6ikkn8M.js` servido contendo `US$/lb`, `US$/t`, `R$/US$`, `granularityNotSupported` e classes `market-chart-group`/`sp-section-icon`.
- Deploy: `09cc5ea115` (external-data-api + supplies-api + supplies) e `6218484d4a` (supplies-api) via `up-prod-sequential.sh --build`, containers healthy.

### 10.4 Semântica preservada

- Nenhum valor sintético/placeholder: previews usam `—` explícito; cartões de contexto exibem apenas evidência real do `meta`.
- Tin permanece selecionável mas não autorizado — agora nomeado no banner com motivo.
- Comparação continua por igualdade estrita de unidade de exibição; granularidades dirigidas pelo catálogo.

## 11. R5.S3 — PTAX: causa-raiz, correção e UX de Câmbio (2026-10-27)

### 11.1 Diagnóstico

- Runtime: `fx_rate_observations` vazia; 3 runs `fx-daily` falhas (26/10) com `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` em ~2 ms; feed `fx-daily` desabilitado por env flag (`EXTERNAL_DATA_FEED_FX_DAILY_ENABLED=false`).
- Conectividade do container de produção até `olinda.bcb.gov.br`: **DNS ok, TCP 443 ok, TLS ok (DigiCert/Thawte, `*.bcb.gov.br`) — sem interceptação Sophos** para este host.
- **Causa-raiz 1 (bloqueio 403):** o adapter chamava `/v1/CotacaoDolarPeriodo` sem o segmento `/odata/` → BCB responde `403 Access Denied`. Com `/v1/odata/CotacaoDolarPeriodo` → 200.
- **Causa-raiz 2 (contrato):** a resposta real traz apenas `cotacaoCompra`, `cotacaoVenda`, `dataHoraCotacao` — sem `tipoBoletim` — e exatamente 1 linha por dia útil (o boletim de fechamento, timestamp ~13:0x). O filtro `tipoBoletim == 'Fechamento'` descartaria todas as linhas mesmo com o endpoint correto.
- Paginação: endpoint aceita `$top`; 1 ano = 250 linhas em ~0,1 s; janela de fim de semana → 0 linhas (ausência honesta).

### 11.2 Correção (external-data-api)

- URL do `CotacaoDolarPeriodo` passa a incluir `/odata/` (idempotente se `PTAX_BASE_URL` já terminar em `/odata`); `$top=1000` + seguimento de `@odata.nextLink` com bound de 8 páginas.
- `_normalize` passa a aceitar linhas sem `tipoBoletim` (semântica do endpoint = fechamento); quando o campo existe, o filtro `Fechamento` permanece.
- Feed `fx-daily` habilitado em produção (`infra/.env`, fonte `bcb-ptax` ativa/ODbL — direitos já comprovados).

### 11.3 Evidência em produção (smoke autenticado, `fffdb6cff5`)

- **Backfill real:** job canônico `fx-daily` executado no container de produção → `fetched=250 inserted=500` (250 dias úteis × compra+venda), janela 27/10/2025–27/10/2026, `outcome=success`.
- **Persistência:** `fx_rate_observations` = 250 linhas por `rate_kind`, `min=2025-10-27`, `max=2026-10-26`; último fechamento `compra 5.4998 / venda 5.5007` (26/10) — confere com a resposta viva da API.
- **BFF `fx/series`:** `unit: R$/US$`; `day` 250 obs (`latest 5.5007`, média 5.189, `+2,35 %`, cobertura 250/262 → `partial` honesto — feriados indisponíveis na estimativa de dias úteis); `week` 53/53 ISO; `month` 13/13 (mês = média das diárias); `year` 2/2; compra e venda como séries distintas.
- **`feed_ingestion`:** `last_run_outcome=success`, `last_run_started_at=2026-10-27T08:09:23-03:00` encaminhado ao MFE.
- **Efeito colateral positivo:** metais em BRL agora convertem — zinco `2026-09 → 19.809,28 BRL/t`, `2026-10 → 18.977,26 BRL/t` (PTAX disponível nos meses); meses sem observação de metal seguem `no_data`.
- **Regressão:** metais diários intactos (cobre `US$/lb`, zinco `US$/t`), IPP preservado (8 competências, última `2026-08`), negativos 401/403/422 íntegros.

### 11.4 BFF/Frontend (R5.S3)

- `feed_ingestion` passa a encaminhar `last_run_started_at`/`last_run_finished_at` (evidência real da última tentativa).
- Cards de estado zerado: no máximo 3 itens compactos (última tentativa, última observação, cobertura) — motivo longo permanece no banner contextual, nunca como valor de KPI; outcome `failed`→"Falhou" etc.; datas/timestamps em pt-BR (`27/10/2026`, `27/10/2026 às 04:48`); card redundante de série removido.
- `partialNote` corrigida: cita apenas observações da própria série (IPP não depende de câmbio).

### 11.5 Auditoria end-to-end (R5.S4, `b90f2d51de`)

**Causa-raiz dos KPIs IPP vazios:** o BFF (`_perspective_summary`) emitia `include_average`/`include_min_max` apenas para séries de variação (`metric_kind != ipp_index`); o layout `index` do MFE renderiza cards de média/mín/máx, então exibia `—`. O teste de contrato R2 travava os `null`. Correção no owner (supplies-api): índice recebe `mean_of_valid_observations/v1` + `extremes_of_valid_observations/v1`; série `%` segue com amplitude apenas (média de % não é métrica aprovada e não há card para ela).

**Smoke autenticado de produção (recomputação independente dos KPIs a partir dos pontos emitidos):**

- IPP índice: 11/14 competências (`partial` honesto, faltantes `2025-09/2026-09/2026-10`), `latest 186.3691` (2026-08), `avg 180.8905`, `min 172.8565` (2025-11), `max 186.3691`, `chg +7,45 %` — todos PASS vs. recomputação.
- IPP variação mensal: `latest 2.13 %`, `min -1.01`, `max 2.75`, `chg`/`avg` = `null` por contrato — PASS.
- PTAX venda/compra: 250 obs cada, `R$/US$`, latest/avg PASS; week 53/53, month 13/13, year 2/2.
- Metais: cobre `US$/lb` COMEX, alumínio/níquel `US$/t` LME, zinco/chumbo `US$/t` SPOT — latest/avg PASS; chumbo `partial` (5/6) honesto; estanho `selectable=false` e `422` em consulta solo (fail-closed).
- Compare: mesmo eixo só dentro da unidade — misto retorna séries separadas por unidade (`US$/lb`,`US$/t`), agrupamento é do MFE.
- Comex: 0 NCMs → `404 unknown import ncm` honesto, sem dados fictícios.
- Negativos: 401/403/404/422 íntegros.
- Datas: contextos de KPI em pt-BR (`Competência 08/2026`, `Semana 44/2026`, `27/10/2026`); `partialNote` em produção já sem menção a câmbio (o aviso observado era do bundle anterior ao deploy S3).

## 12. Pendências

1. ~~Chave e homologação S1~~ → **concluído** (V008 ativa fonte + 5 bindings verificados; estanho permanece inativo).
2. **Egresso de produção:** exceção para `api.metalcharts.org` no Sophos (bloqueio webcat cat=21) — depende de TI; até lá a ingestão é manual via túnel dentro do orçamento de franquia.
3. Revisão institucional da licença (`license_reviewed_at`) — pendente por decisão; ativação registra permissões comprovadas.
4. Estanho: sem cobertura Free nesta API — binding inativo até fonte alternativa homologada ou inclusão upstream.
5. Decisão sobre exibição pública/redistribuição (crédito visível; ALI/NI têm lastro LME upstream).

## 13. Comex configurável — S0 inventário + contract freeze (2026-10-27)

Baseline: `486831a025`. Planos de referência em branches de PR (ainda não mergeados): `docs/proc-0076-comex-configurable-analysis-plan-20261027` (#120) e `docs/proc-0076-perspectives-comex-validation-20261027` (#119) — lidos sem merge.

### 13.1 Inventário SB1010 (leitura autorizada via owner `delpi-api-delpi`)

| Métrica | Valor real |
|---|---|
| Total `SB1010` ativa (`D_E_L_E_T_ = ''`) | 55.347 |
| `B1_TIPO = MP` | 11.708 (11.697 com `B1_POSIPI`, **11.694 válidas** 8 dígitos) |
| `B1_TIPO = PI` | 14.077 (14.077 com NCM, 14.076 válidas) |
| `B1_TIPO = PA` | 22.553 (22.553 com NCM, 22.448 válidas) |
| Outros tipos | II 3.610, MC 1.389, AI 897, MS 247, MX 189, GG 158, MO 145, EM 138, MH 137, OI 45, MR 37, SV 6, ME 4, PC 2, GN 1, PR 1 |
| NCMs malformadas | 109 produtos / 6 valores (`8544.49.00`, `8544.42.00` pontuados; `V`; `8544420085`; `85444200 8`) |
| NCMs distintas entre MPs | **211** |
| NCM mais compartilhada (MP) | `85444900` → 3.834 produtos; `85369090` → 2.473 |
| MPs de metais com NCM válida | COBRE 74, ALUMÍNIO 62, NÍQUEL 37, ESTANHO 14, ZINCO 5, CHUMBO 1 |
| `B1_EX_NCM` | 0 usos |
| Atenção | `B1_POSIPI` é `char(10)` com padding; `00000000` ocorre e **não** é NCM válida (tratar como ausente) |

### 13.2 Contratos vigentes inspecionados

- `GET /apps/api-delpi/products/search` existe, paginada, projeta `Product` completo — `ncm_ipi_position` já vem no DTO — mas **não tem filtro `product_type`** e exige `ENGINEERING_LMP_ACCESS` → **403 para usuário de Suprimentos** (provado em produção).
- Superfície canônica Suprimentos: `api-delpi /supplies/*` com `require_any_permission_or_supplies_bff(KPI_SUPPLIES_ACCESS)` (user-parity `dashboard-supplies.view` ou S2S confiável `caller=supplies-api`).
- `external_data.comex_ncm_allowlist` (V005) já é o registro operacional de homologação; `comex_import_monthly_observations` persiste FOB/kg/US$/t por NCM×país×UF; feed `comex-monthly` recusa execução com allowlist vazia; normalizador exige allowlist explícita.
- BFF: `GET /market-intelligence/imports/series?ncm=` existe (404 honesto hoje); filtros expõem `selectable`/`selectable_in_ui`.
- Permissões disponíveis: `supplies.access` (leitura) e `supplies.manage` (gestão). Sem código por operação.

### 13.3 Contract freeze (menor diff por owner)

| Serviço | Mudança |
|---|---|
| `api-delpi` | `search_products` ganha filtros aditivos `product_type` (lista) e `subgroup`; nova rota `GET /supplies/products/search` (mesma use case, projeção reduzida + `ncm_status` derivado: `missing`/`malformed`/`present`) |
| `external-data-api` | V009: `comex_ncm_allowlist` + `status` (`candidate`/`pending_fiscal_review`/`approved`/`rejected`/`inactive`), `reviewed_*`, `updated_at` + auditoria; rotas S2S de governança; consultas e ingestão só com `status=approved AND active` |
| `supplies-api` | V004 `supplies.market_saved_views` (owner_user_id + unit_scope); BFF `comex/products/search` (api-delpi + estado de homologação), `comex/ncm-governance` GET/POST + `/{id}/transition` (manage-only), `comex/views` CRUD por ownership, `imports/series` multi-NCM com dedup |
| `plugins/supplies` | Perspectiva Comex: tipo, busca paginada, multiselect chips, badges NCM, saved views, KPIs FOB/kg/US$/t ponderado |

**Decisão de governança:** com apenas `supplies.access`/`supplies.manage`, todas as transições de estado da NCM exigem `supplies.manage`; a trilha de auditoria (ator+nota+timestamp) registra a responsabilidade de negócio — distinção Compras/Fiscal/Suprimentos como permissões dedicadas ficaria `PENDING` de decisão Core (não criar permission por operação).


## 14. Comex configurável — S1–S5 implementação e evidência (2026-10-27)

### 14.1 S1 — catálogo de produtos (api-delpi, commit 484f39441a)

- `search_products` ganhou filtros aditivos `product_type` (lista) e `subgroup`; nova rota `GET /supplies/products/search` na superfície Suprimentos (`dashboard-supplies.view` user-parity ou S2S `caller=supplies-api`), projeção reduzida e `ncm_status` derivado (`missing`/`malformed`/`present`) — NCM nunca é inferida, apenas formatada.
- Busca por `description` evoluiu de prefixo para substring (scoring mantém bônus de prefixo) — provado: `cobre` retorna 74 MPs reais.
- 10 testes novos + 40 regressões da api-delpi verdes.

### 14.2 S2 — governança NCM (external-data + supplies, commits 5bd8ca1e3a, 0aafd520e1)

- external-data-api: use case `upsert_ncm_allowlist` (S2S, preserva `active` quando omitido; `ncm_version` recebe default `2022` quando omitido no create). 9 testes verdes.
- supplies-api: migration V004 `supplies.comex_ncm_governance` + `supplies.market_saved_views`; máquina de estados `candidate → pending_fiscal_review → approved|rejected`, `approved → inactive`, `inactive|rejected → pending_fiscal_review`, protegida por `revision` (optimistic concurrency); aprovação/desativação sincronizam a allowlist (`sync: synced`); `inactive → approved` rejeitado com 409 (re-revisão obrigatória, contrato legítimo).

### 14.3 S3 — BFF (commit ee304e6589, fix 1f39358359)

- Rotas: `comex/products/search`, `comex/ncm-governance` GET/POST, `comex/ncm-governance/{id}/transition`, `comex/views` CRUD por ownership, `imports/series` multi-NCM (dedup CSV ≤20, agregação FOB/peso, `US$/t = ΣFOB/(Σkg/1000)` — nunca média simples de preços médios).
- NCM malformada (≠8 dígitos) → **422** antes da resolução de catálogo; desconhecida/não aprovada/inativa → **404**; `granularity=day` → 422.

### 14.4 S4 — frontend (commits 9b0b6c936d, 81212c75cb)

- `MarketComexSelector`: busca paginada MP/PI/PA, multiselect de produtos, união deduplicada de NCMs dos produtos selecionados + seleção manual de NCMs aprovadas, ações de governança por permissão (`supplies.access` solicita; `supplies.manage` aprova/rejeita/desativa/ressubmete), saved views CRUD.
- Selecionabilidade por `selectable_in_ui` (allowlist ativa), não `selectable` (direitos de exibição da fonte).
- URL: `ncm` CSV + `products` persistem F5/compartilhamento/voltar-avançar.
- Sem NCM ativa: estado neutro de configuração pendente + prévia de KPIs. Vitest 51 arquivos/509 testes; `tsc` limpo; build Vite ok.

### 14.5 S5 — deploy e smoke autenticado (SHAs 1f39358359 / 81212c75cb)

Ordem canônica respeitada: api-delpi → external-data-api → supplies-api → supplies. Evidência em produção:

| Caso | Resultado |
|---|---|
| `product_type=MP` + `description=cobre` | 200, 74 resultados reais |
| Ciclo `pending_fiscal_review → approved` | `sync: synced`, `selectable_in_ui: true`, série 200 (`data_status: no_data` honesto) |
| `inactive → approved` | 409 (re-revisão obrigatória) → `inactive → pending → approved` OK |
| Desativação | `sync: synced`, NCM sai da seleção |
| `ncm=123` / CSV com valor não-numérico | **422** (após fix) |
| `ncm=99999999` | 404 |
| `granularity=day` | 422 |
| Views CRUD | ownership fail-closed (403 cross-owner, 401 sem token) |
| 401/403 | íntegros |

**Pendência material:** feed `comex-monthly` segue desabilitado — sem observações reais MDIC a série retorna `data_status: no_data` (honesto). Ativação exige NCMs homologadas pelas autoridades de negócio + habilitação do feed/scheduler.

**Rollback:** SHA anterior + rebuild dos serviços afetados; migration V004 já aplicada (imutável, forward-only); allowlist/governança revertíveis via transições.

## 15. EXECUTION REPORT — PROC-0076.COMEX-CONFIGURABLE-ANALYSIS

- **FINAL HEAD:** rebase fast-forward sobre `origin/main`; commits 484f39441a, 5bd8ca1e3a, ee304e6589, 9b0b6c936d, 0aafd520e1, 1f39358359, 81212c75cb + docs.
- **S0–S4 GATES:** PASS. **S5 GATE:** PASS parcial — infraestrutura, composição, ciclo de governança e smoke provados; dados MDIC `PENDING` (feed desabilitado, 0 NCMs homologadas em produção).
- **AC-01..20:** AC-01/02/03/04/05/06/07/09/10/12/13/14/15/18/19 PASS; AC-08/11 PENDING (fonte sem observações); AC-16 INCONCLUSIVE (exportação herdada do painel); AC-17 INCONCLUSIVE (responsivo/a11y via kit, sem captura); AC-20 PASS parcial (deploy + smoke autenticado; visual não capturado).
- **POSTCONDITION:** `PROC_0076_COMEX_CONFIGURABLE_ANALYSIS_FUNCTIONAL` = **PENDING** — catálogo, governança, BFF e UX configurável funcionais e verificados em produção; a pós-condição de dados reais aguarda homologação de NCMs pelas autoridades de negócio e ativação do feed `comex-monthly`, conforme seção 18 do brief (sem dados fictícios).

## 16. Comex S6 — UX refinement + entrada direta de NCM (2026-10-27)

Commit `82cbb13f03` — diff 100% no `plugins/supplies`; **zero mudança de backend** (a consulta direta resolve na lista de governança já carregada pelo seletor + catálogo `import_ncms` da allowlist; `request_ncm` cobre a criação/resubmissão e o BFF continua a única autoridade).

### 16.1 Implementado

- **Alternador de origem** (`comex-origin`): «Produtos DELPI» | «Consultar NCM» — a seleção e os chips são compartilhados entre as origens.
- **Entrada direta**: campo aceita um ou mais códigos com espaços/pontos/vírgulas; cada token é normalizado (`\D` strip) e exige exatamente 8 dígitos — tokens inválidos são rejeitados com aviso nominando-os; dedup contra as três origens; união limitada a 20 NCMs (contrato BFF multi-NCM). Formato válido **nunca** implica vigência fiscal.
- **Promoção**: NCM direta ativa na allowlist (`selectable_in_ui`) entra na análise na hora — mesma regra da origem produto.
- **Remoção**: chip de remoção nas NCMs diretas; ao remover, a contribuição na análise cai junto se nenhum produto selecionado usar a mesma NCM.
- **Persistência**: novo param `direct_ncm` (CSV 8 dígitos validado) — F5, link compartilhado e voltar/avançar restauram; views salvas carregam a seleção direta em `selected_materials` (slot genérico do contrato existente).
- **Empty state**: removidos os cards `—` de prévia; mensagem + próximos passos curtos e orientados à ação (selecionar/solicitar homologação).
- **Layout**: rodapé análise+views em grid 2 colunas (empilha no mobile); conteúdo/help/manual sincronizados.

### 16.2 Smoke autenticado em produção

| Caso | Resultado |
|---|---|
| `POST ncm-governance {ncm_code: "8544.42.00"}` | **422 `invalid_ncm`** |
| `POST {ncm_code: "99999999", initial_status: pending_fiscal_review}` | **201** `pending_fiscal_review` (sem vínculo de produto) |
| `POST` em NCM inativa existente | **409 `ncm_already_registered`** (contrato — UI usa resubmit) |
| Cleanup `pending → rejected` (manage) | 200 |
| `GET ncm-governance` sem token | 401 |

### 16.3 Verificações

Vitest 51 arquivos / **511 testes** verdes (2 novos: parse + round-trip `direct_ncm`); `tsc -b` limpo; build Vite ok; ESLint 5 warnings pré-existentes, 0 erros. Bundle produção `App-EXWSSnSw.js` contém `direct_ncm`/`comex-origin`.

**Residuais:** AC visual (desktop/mobile/temas) `INCONCLUSIVE` sem captura de browser; o registro de teste `99999999` permanece como `rejected` na trilha de auditoria (rows de governança não são deletáveis por desenho).

## 17. Comex S7 — catálogo compartilhado de NCMs + fluxo simplificado (2026-10-27)

Commits `8cc1d8ab02` (backend), `605d35ebad` (fixture do teste), `3941c44c36` (frontend). Deploy `supplies-api` + `supplies`; bundle `App-BiAXN3iP.js`.

### 17.1 S7.P0 — contract freeze

Inventário concluiu que `supplies.comex_ncm_governance` **já é o catálogo compartilhado**: uma linha global por NCM (`UNIQUE ncm_code`, check de 8 dígitos, auditoria, revisão otimista) — não por usuário. O POST existente exige apenas `supplies.access` (`can_use_market_intelligence`) e `list_governance` retorna todos os registros. Gaps reais: (a) `SELECT`-then-`INSERT` com janela de corrida → `UniqueViolation` não tratada; (b) `initial_status="candidate"` em registro existente seguia o caminho de resubmissão em vez de resposta idempotente. Nenhuma tabela ou endpoint novo foi criado.

### 17.2 S7.S1 — backend (`supplies-api`)

- `create_governance`: tenta o insert, captura `IntegrityError` (violação do UNIQUE concorrente), faz rollback da transação abortada, relê por `ncm_code` e retorna a linha existente com `_existing=True` — o insert e o evento de auditoria seguem atômicos no caminho normal.
- `request_ncm` (serviço): `initial_status="candidate"` com registro existente retorna a linha intacta + `already_registered=True` — qualquer que seja o status (inclui `inactive`/`rejected`, que **não** são reativados). O caminho explícito `pending_fiscal_review` preserva o resubmit `candidate|rejected → pending` e o 409 para `approved`/`inactive`.
- Sem aprovação fiscal implícita, sem sincronização de allowlist no cadastro, sem reativação.

### 17.3 S7.S2 — frontend (`plugins/supplies`)

- Fluxo `BUSCAR OU INFORMAR → ADICIONAR → SELECIONAR → ANALISAR`. A aba «Consultar NCM» agora mostra o **catálogo compartilhado** (todos os registros, filtrável por código/descrição) com toggle Selecionar/Selecionada por linha; a entrada direta cadastra e seleciona em uma única ação (`Adicionar`).
- Estados funcionais (AC-05): `Disponível` (allowlist ativa), `Cadastrada` (candidate), `Em revisão` (pending/approved-ainda-inativo), `Inativa` (rejected/inactive), `Não cadastrada` — sem jargão de workflow na superfície principal.
- Administração separada (D-05): decisões de ciclo de vida (aprovar/rejeitar/inativar/reenviar) foram movidas para `<details>` exclusivo de `canManage`; a linha de seleção só tem status + selecionar + remover. `rejected → pending` segue visível para `supplies.access` (contrato do ciclo de vida).
- Removido o multiselect redundante de «NCMs na análise» — a seleção via catálogo/chips é a única origem; `Limpar seleção` limpa a união. NCM malformada/ausente de produto não entra nos chips.
- Empty states AC-08 implementados nos textos (`emptySelection`, `catalogEmpty`, `catalogNoMatch`, `alreadyInCatalog`, `catalogAdded`); ajuda contextual, manual e FAQ sincronizados.

### 17.4 S7.S4 — testes

- Backend: 48 testes verdes — incluindo o teste de corrida no repositório (insert concorrente → `IntegrityError` → reselect) e serviço (idempotência `candidate`, resubmit de `rejected` preservado).
- Frontend: Vitest 51 arquivos / **518 testes** (1 novo teste estrutural S7: `initial_status: "candidate"`, catálogo, `<details>` admin, ausência do multiselect, strings de empty-state); `tsc -b` limpo; ESLint 5 warnings pré-existentes; build Vite ok.

### 17.5 Smoke autenticado em produção (NCM `84798990`)

| Caso | Resultado |
|---|---|
| `POST {ncm_code, initial_status:"candidate"}` (user `supplies.access`) | **201** `status: candidate` — sem `supplies.manage`, sem aprovação |
| Re-add mesmo usuário | **201** `already_registered: true`, `candidate` |
| Listagem pelo segundo usuário autorizado (`devin-smoke-g16` c/ `supplies.access`) | **200** — encontra a mesma linha |
| Re-add pelo segundo usuário | **201** `already_registered: true`; total **1 linha** (sem duplicidade) |
| `selectable_in_ui` da nova NCM | **None** — allowlist não contornada |
| `GET imports/series` da candidate | **404** — nenhum dado MDIC |
| `POST` NCM malformada | **422** `invalid_ncm` |
| Sem token / sem permissão | **401 / 403** |
| Re-add de `85444200` (inativa) | **201** `already_registered`, status permanece `inactive` — **não reativada** |

Estado final honesto: `84798990` permanece `candidate` no catálogo compartilhado (registro auditável); conta de fumaça `devin-smoke-g16` foi habilitada e recebeu a role «Portal Suprimentos - Acesso» via Core RBAC admin para a prova de reutilização por outro usuário.

**Residuais:** dados MDIC reais seguem `PENDING` (feed `comex-monthly` desabilitado); evidência visual em browser `INCONCLUSIVE` sem captura.

## 18. Comex S8 — refinamento UX e organização do frontend (2026-10-28)

Commit `ba9d19b074` (frontend only — zero backend/contrato/migration). Deploy `supplies`; bundle `App-pFwxCZOo.js`. Plano autorizado em `docs/12-roadmap-e-evolucao/supplies/PROC-0076-COMEX-S8-UX-REFINEMENT-PLAN-20261028.md` (PR #121, branch de docs não mergeada — conteúdo lido na origem).

### 18.1 S8.1 — layout e hierarquia

- Grade de duas colunas (`sp-comex-selector__columns`, 3fr/2fr): «Encontrar materiais» à esquerda (alternador Produtos/NCM, pesquisa ampla, filtro MP/PI/PA, resultados, entrada direta de NCM e catálogo compartilhado) e «Minha análise» à direita (contagem, chips de produtos e NCMs com estado funcional, remover por item, «Limpar seleção» e visualizações salvas com nomear/salvar/atualizar/excluir).
- Painel de resultados «Importações — Comex Stat (MDIC)» permanece em largura total abaixo do seletor, sem duplicar filtros de período/granularidade da página.
- Catálogo como lista vertical estruturada (código, descrição multi-linha, badge de estado, ação contextual única Selecionar/Selecionada) com rolagem interna — substitui a leitura de sequência dispersa.
- Responsivo: colunas empilham abaixo de 980px; regras mobile 720px existentes preservadas; sem rolagem horizontal de página.
- Administração continua em `<details>` secundário, exclusivo de `supplies.manage` efetiva — fora das colunas de seleção.

### 18.2 S8.2 — interações e estados

- Dropdown NCM duplicado removido do `FiltersRow` da página — a seleção acontece exclusivamente no seletor (catálogo/produtos/NCM direta); `ncmOptions`/`selectedNcm` e o fallback implícito «primeira NCM disponível» foram removidos.
- `configured` do painel agora exige seleção real: seleção vazia → estado «Comex — sem seleção» (AC-11, «Selecione produtos ou NCMs para iniciar a análise»); seleção presente mas nenhuma NCM habilitada → «Comex — aguardando habilitação» (AC-12) — inclusive quando a NCM selecionada é `candidate`/`pending`/`inactive`, coberto por `filters.state.ncm` bruto.
- Seleção sobrevive à alternância Produtos/NCM, URL/F5 e links compartilhados (contrato `ncm` CSV/`direct_ncm`/`comex_products` intacto); deduplicação e limite de 20 preservados.
- `configPendingTitle` generalizado — o título «Comex — seleção pendente» era reusado incorretamente pelos painéis Metais/IPP/Câmbio.

### 18.3 Testes e evidências

- Vitest **51 arquivos / 525 testes** verdes (+1 estrutural S8: colunas, títulos, resumo de seleção, lista do catálogo, `aria-pressed`, CSS grid + breakpoint 980px, `comexHasSelection`, ausência de `ncmOptions` e do fallback `selectableNcms[0]`).
- `tsc -b --force` limpo; ESLint 0 erros (warnings pré-existentes de `set-state-in-effect`); build Vite ok.
- Ajuda contextual e manual sincronizados ao fluxo «encontrar → selecionar → configurar → analisar» e às duas colunas.
- Smoke federado: `remoteEntry` 200, `supplies-api` health 200, bundle de produção contém `sp-comex-selector__columns`/`comexEmptySelection`/`Encontrar`.
- Aceite visual em navegador autenticado (1440/1920/768/390, claro/escuro): **INCONCLUSIVE** — sem captura disponível; CSS/estrutura não substituem evidência visual.

### 18.4 Inventário de dados de teste (§12 do plano)

Registros em `supplies.comex_ncm_governance` (todos fixtures de homologação S6/S7, auditáveis — **não alterados** nesta execução):

| NCM | Status | Descrição | Criado |
|---|---|---|---|
| 85444200 | inactive | SMOKE cobre | 2026-10-27 |
| 99999999 | rejected | (vazio) | 2026-10-27 |
| 85369090 | approved | (vazio) | 2026-10-27 |
| 84798990 | candidate | smoke S7 — fluxo catálogo | 2026-10-28 |

Proposta: tratamento via workflow de governança (inativar/rejeitar) ou limpeza autorizada pelo PO — nenhuma linha/auditoria foi removida automaticamente.
