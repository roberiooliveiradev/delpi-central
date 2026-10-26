# PROC-0076.R2 — Plano tecnico para MDIC Comex Stat + IBGE IPP + BCB PTAX

> **TARGET / PLANNED — nao existem novas tabelas/rotas/feeds implantados por este documento.**
> **PO DIRECTION APPROVED:** [Decisao e UX](../supplies/PROC-0076-R2-DECISAO-FONTES-PUBLICAS-COMEX-IBGE-BCB-20261026.md).
> **Evidencia HEAD em 2026-10-26:** main 25060ff33fa324af24349358ecdcbbde0eac30b4.
> **Ordem:** contrato e fonte → external-data-api → supplies-api → MFE/plugin-ui → E2E/autorizacao.
> **Nao substitui** instrucoes oficiais, regras .cursor, ADR-009, contratos X0 CNPJ nem gates de pagina. P0/R1/R1.1/R1.2 e PR #113 preservados como trilha historica e de seguranca.

## 1. Arquitetura e boundary

    MDIC CSV por NCM (mensal) → ComexImportProvider adapter
    IBGE IPP SIDRA (mensal) → ProducerPriceIndexProvider adapter
    BCB PTAX OData (diaria) → provider PTAX JA EXISTENTE (reuso)
                ↓
    external-data-api application ingestion / provenance / rights / quality
                ↓ migrations owner external_data (postgres-plugins)
    external_data.comex_import_monthly_observations        [TARGET]
    external_data.producer_price_index_observations       [TARGET]
    external_data.fx_rate_observations                     [PROVEN existing]
    external_data.market_data_sources, market_data_ingestion_runs [PROVEN existing]
                ↑ consultas paginadas via internal REST + Keycloak S2S
    supplies-api Flask BFF + Core effective supplies.access
                ↑ via BFF (never direct external-data)
    plugins/supplies MarketIntelligencePage (kit-first, PT-BR)

Arquitetura evolui o bounded context existente, sem acesso da supplies-api a schema externo e sem espelho TOTVS. Os nomes fisicos sao candidatos sujeitos a revisao do migration runner real. Precisao Decimal/NUMERIC, migration aditiva, constraints e checksums; preservar todos os arquivos SQL ja aplicados. Separar data_reference, published_at (quando publicado pela fonte) e retrieved_at.

## 2. Producer EX0 — contrato da fonte ANTES do parser

### MDIC (fonte primaria de valor unitario de importacao)

Fonte oficial: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta . A pagina publica CSV anual de importacoes detalhado por NCM, com delimiter ponto-e-virgula. Layout informado oficialmente:

    CO_ANO;CO_MES;CO_NCM;CO_UNID;CO_PAIS;SG_UF_NCM;CO_VIA;
    CO_URF;QT_ESTAT;KG_LIQUIDO;VL_FOB;VL_FRETE;VL_SEGURO

**Nao inferir** que existe uma API REST privada e estavel do site de consultas. O contrato inicial recomendado e **download agendado de CSV oficial publicado**, com host/path allowlisted, tamanho bounded ou streaming seguro, checksums, manifesto de versao, schema validation e idempotencia.

O dataset e grande: nao inserir todas as linhas brutas em PostgreSQL por default. Fazer agregacao validada na external-data-api para subconjunto NCM explicitamente homologado com Compras; preservar somatorios e audit references por lote. Prevenir soma dupla ao reprocessar ano publicado/revisado. Escolher particao temporal por ano/mes, recalcular somente competencias afetadas e usar upsert atomico por chave canonica.

**Fonte ≠ cotacao de metal.** Valor unitario e razao FOB/kg. Validacao positive cobre NCM homologado (metal); sibling: outra NCM homologada e outro pais; negativos: peso zero, valor ausente, NCM invalida ou reclassificada, pais desconhecido, delimitador alterado, totas alterados, CSV truncado, duplicatas e varias granularidades. Conservar mapping NCM e versao de classificacao; nao assumir que uma NCM = metal puro.

### IBGE IPP (indice setorial nacional)

Fonte: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9282-indice-de-precos-ao-produtor-industrias-extrativas-e-de-transformacao.html . Serie mensal, divulga resultados em SIDRA; indice por atividade. **A atividade Metalurgia e serie de referencia, nao preco individual de metal**.

Em EX0, localizar no SIDRA oficial tabela, variavel, classificacao, atividade, unidade, data base e revisoes. Tabela 6903 e CANDIDATA; nao hardcodar URL API ate obter resposta real e estabilidade documental. A external-data-api guardara value NUMERIC e metric_type distinto: ipp_index (numero-indice) ou ipp_month_over_month_pct (variacao), sem conversao para USD/t. Fonte mensal com publication lag sujeito ao calendario IBGE; sem stale falso.

### BCB PTAX (reutilizar)

Catalogo oficial com licença ODbL: https://dadosabertos.bcb.gov.br/dataset/taxas-de-cambio-todos-os-boletins-diarios . Reutilizar series fx_rate_observations, rate_kind, provider e DTO ja presentes. Validar compra vs venda e boletim fechamento. Egress de producao tem historico de 403: nao contornar mecanismos de acesso; feed OFF ate teste oficial/autorizacao. Separar visao USD/t Comex de conversao opcional para BRL/t. Conversion policy para valor unitario FOB deve ser explicitamente rotulada "equivalencia cambial indicativa", NAO custo real convertido de compra.

### Rights and readiness

Por fonte, registrar URL, owner, metadado de licença/uso, limites, atribuicao, data de revisao, resolucao de terceiros, downstream exposure, retention e operacoes collect/store/derive/internal_display. Pendencia nao e grant. Nao usar o source rights antigo WB/LME para habilitar Comex/IBGE/BCB. Validar contratos de dados abertos e compliance especifico; autorizar ingestion e display apenas apos evidencia adequada.

## 3. Modelo de dados TARGET (DDL nao autorizado aqui)

### comex_import_monthly_observations

| Campo candidato | Semantica |
|---|---|
| observation_id | PK tecnico |
| reference_month | DATE no primeiro dia do mes, sem fingir dia de preco |
| ncm_code, ncm_version | Codigo da mercadoria e versao/correlacao |
| country_code, state_code, transport_mode | Dimensoes da agregacao; nullable apenas se politica de agrupamento explicita |
| source_id | MDIC official source |
| fob_usd_total | SUM(VL_FOB), NUMERIC |
| net_weight_kg_total | SUM(KG_LIQUIDO), NUMERIC |
| unit_value_usd_per_t | Valor derivado NUMERIC ou NULL se peso invalido |
| contributing_rows | Quantidade de linhas elegiveis processadas |
| quality_status, coverage_status | validado/parcial/rejeitado e cobertura |
| dataset_year, dataset_revision, checksum_ref | Referencia ao arquivo/versao e reprocessamento |
| retrieved_at, updated_at | Trilha tecnica |

Chave de dedup: source+reference_month+ncm+country+state+transport_mode+politica_de_agregacao+dataset_scope. Escolher unica chave dimensionada antes do migration freeze; preservar consistencia sob reimport. Se a consulta exigir um subtotal nacional, computar explicitamente conforme cobertura, sem somar subtotais preagregados com folhas (double count).

### producer_price_index_observations

| Campo candidato | Semantica |
|---|---|
| observation_id | PK |
| reference_month | Mes da serie |
| table_code, variable_code, activity_code | SIDRA/atividade/serie |
| metric_kind | ipp_index / ipp_monthly_change_pct, conforme fonte |
| base_reference | Base do numero-indice, se aplicavel |
| value | NUMERIC, unidade index ou percent |
| source_id, source_revision | IBGE official metadata |
| published_at, retrieved_at, quality_status | Proveniencia/qualidade |

Chave: series identity+reference_month+source_revision policy (upsert current e trilha de revisoes). Nao substituir base de indice silenciosamente se IBGE mudar referencial.

### Estruturas existentes reutilizadas

- external_data.fx_rate_observations — PTAX diaria.
- external_data.market_data_sources — metadados/licencas/grants por operacao.
- external_data.market_data_ingestion_runs — feed/run/outcome/contagens/erros saneados.
- Nao inserir serie IBGE em metal_quote_observations nem valores FOB em fx_rate_observations.
- Sem importacao de dominio de outro service.
- Backup, retenção, pagination indexes por ncm+month e activity+month e upgrade/rollback demonstrados em PG descartavel com a guarda segura da R1.2.

## 4. Contratos REST internos TARGET — external-data-api

Todas as rotas abaixo sao **propostas e NAO implementadas**, a validar contra o endpoint OpenAPI atual do owner.

| Method | Path TARGET | operationId TARGET | Parametros e conteudo |
|---|---|---|---|
| GET | /v1/market-data/comex/imports | listComexImportObservationsV1 | ncm_code(s) homologados, reference_from/to, country/state quando aplicavel, page cursor+limit |
| GET | /v1/market-data/producer-prices/observations | listProducerPriceIndexObservationsV1 | table_code/variable/activity canonicamente permitidos, reference_from/to, cursor+limit |
| GET | /v1/market-data/catalog | listMarketDataCatalogV1 | EVOLUIR com metric_kind, source, unit, coverage, allowed uses, granularity |
| GET | /v1/market-data/fx/observations | listFxObservationsV1 | **EXISTENTE**, manter contrato; PTAX |
| GET | /v1/market-data/ingestion-status | getMarketDataIngestionStatusV1 | **EXISTENTE**, incluir novos feeds/status sem quebrar consumers |

### DTO de exemplo SEM valores sinteticos apresentados como dados reais

    {
      "metric_kind": "comex_import_unit_value",
      "reference_month": "2026-09",
      "ncm_code": "APPROVED_NCM",
      "dimensions": { "country_code": null, "state_code": null },
      "fob_usd_total": null,
      "net_weight_kg_total": null,
      "unit_value_usd_per_t": null,
      "unit": "USD/metric ton",
      "quality_status": "no_data",
      "source": {
        "source_id": "mdic-comex-stat",
        "dataset_revision": null,
        "retrieved_at": null
      }
    }

NCM acima e PLACEHOLDER para contrato, nao cadastro autorizado nem exemplo factual de dado de mercado. Numeros reais serao strings decimais ou null, segundo contrato de precisao canônico. Erros: 400 query, 401 S2S ausente, 403 consumidor sem allowlist/source_use not approved (codigo distinto), 404 serie nao existe, 422 filtro, 429 cota, 502 dado upstream invalido, 503 storage/source unavailable, 504 timeout; semanticamente manter error envelope da external-data-api. Usar URL allowlist (SSRF), limites de intervalo/linhas, retriable/no-retry, provenance e correlation ID.

O chart **nao chama as fontes**: as rotas leem o banco persistido. Jobs devem ser internos, idempotentes, com lock e run status, sem gatilho no browser.

## 5. Contratos BFF TARGET — supplies-api

Manter rotas existentes para serie metals/FX ate reconciliar clientes; evoluir sem quebrar DTO de quote para apresentar indices ou razoes FOB. Contratos candidatos aditivos:

| Method | Path TARGET | operationId TARGET | Produto |
|---|---|---|---|
| GET | /market-intelligence/imports/series | listMarketImportBenchmarkSeriesV1 | Serie Comex por NCM e periodo, USD/t FOB medio e volume |
| GET | /market-intelligence/producer-prices/series | listMarketProducerPriceSeriesV1 | Serie IPP atividade Metalurgia, indice e variacao |
| GET | /market-intelligence/fx/series | listMarketFxSeriesV1 | Serie PTAX, tipo e data |
| GET | /market-intelligence/filters | listMarketIntelligenceFiltersV1 | Contrato existente EVOLUIR com grupos/metric_kind/fonte/unidades |

BFF resolve user Core effective supplies.access (sem branch artificial para estatistica publica), falha Core fail-closed, usa HTTP/S2S Keycloak individual e allowlist no produtor, sem SELECT no Postgres do vizinho. Se nao houver data em BRL por PTAX 403, manter US$/t e IBGE independentes e expor conversao null/partial. Quando selected NCM estiver pendente, error/filtro explicito em vez de valores errados. Manter read-only e sem nova permission.

Requisitos do consumer: source_method, date_reference, publication_date se conhecida, retrieved_at, period_count, coverage, unit, quality, de-dup, periodicidade, modulo/metric_kind discriminado. Nao misturar series IPP (%) com valores USD/t. Implementar contract tests producer→BFF→MFE no mesmo PR de feature ou fatias bounded.

## 6. Plano por owner (next delivery, um owner por fatia)

### EX0 — Freeze das dimensoes e source rights

- **Goal:** congelar NCM (produtos efetivamente relevantes para DELPI, mapping metal_family↔NCM), competencia/historico, dimensoes Comex, tabela/serie IPP no SIDRA, atribuição, rights e combinacao eventual de PTAX.
- **Evidence:** tres fontes oficiais e amostras de payload/CSV SEM dump massivo, layout NCM e correlacoes, contratos existentes, proprietario de business formula (Compras).
- **Allowed:** inventario read-only, aprovacao mapeamento e DTOs finais; **Not allowed:** feed, migrations produtivas ou menu.
- **Accept:** matriz fonte→metric_kind→unit→grain→method→revision→rights com exemplos e contrato OpenAPI candidato congelado; sem NCM ou SIDRA inventados.
- **STOP:** NCM/politica sem aprovacao → somente esse modulo TO_INVENTORY; continuar modulos independentes.

### EX1 — Producer external-data-api

- **Goal:** construir historico real MDIC + IBGE, mantendo CNPJ e PTAX.
- **Do:** adapters/ports, migration **ADITIVA** com catalog seed rights comprovados, jobs/backfill por competencias bounded, tratamento de revisoes e idempotencia, schema owner, audit/run statuses, REST S2S, OpenAPI/testes.
- **Dont:** reescrever V001–V004, importar CSV inteiro sem limite, inferir price do peso zero, alterar LME rights ou politica da quarentena, bloquear CNPJ.
- **Tests:** parser MDIC header/revisoes/totais, NCM mapping, peso zero, Comex sibling NCM/origem, IBGE indice/variacao/rebase, fonte offline, retries 429, sem creds, PostgreSQL disposable (checksums/unique/idempotent/corrida), CNPJ/S2S regression.
- **Postcondition:** API interna retorna dados persistidos verificaveis por mes/fonte; **TEST_NOT_RUN** para infra sem acesso.

### EX2 — BFF supplies-api

- **Goal:** fornecer read models tipados e autorizados.
- **Do:** clients HTTP S2S, DTO metric_kind, calculo valor FOB agregado e FX indicativo (regra approved), filtros e series endpoints, safe errors, OpenAPI real.
- **Dont:** SQL direto external_data, novo RBAC, dados Comex tratados como LME quotes, React calculando regras.
- **Tests:** positive + sibling + negative por fonte, unidade, variacao, sem PTAX, Core denied/unavailable, S2S denied, pagina/cap; regressao antiga.
- **Postcondition:** rotas BFF documentadas, capazes de renderizar dados reais autorizado sem mocks.

### EX3 — MFE e Help

- **Goal:** evoluir a pagina ja existente mantendo identidade do Portal.
- **Do:** tabs Importacoes/IPP/Cambio, kit @delpi/plugin-ui (SeriesCharts, filters, cards, tables), source attribution, query URL, loading/empty/partial/stale/403/404, Help com definicoes corretas, dark/mobile/keyboard.
- **Dont:** copiar kit, recalcular US$/t ou indice no frontend, ativar nav antes gate E11, inserir fonte sem readiness/licenca.
- **Tests:** Vitest interactions, URL/F5/race, source/quarantine/no-data, tema+mobile+focus, typecheck/build; smoke federado autenticado no E2E.
- **Postcondition:** pagina comunica diferencias reais entre indicadores; nao inventa quote.

### EX4 — Verify final, deploy gated

- **Goal:** comprovar end-to-end e go-live quando autorizado.
- **Do:** sample MDIC por NCM homologada e IBGE IPP por periodo real, hash/source, ingestion→PG→S2S→BFF→MFE, Core user autorizado/negativo, CNPJ regression, rollback, backup, SHA/digest, env/feed observability.
- **Dont:** producao sem gate; bypass BCB WAF; merge PR113 sem review; promover QA mock a PASS.
- **Accept:** codigo+dados+source rights+smoke e gate anterior PASS. Sem smoke=INCONCLUSIVE.

## 7. Traceability ledger

| RQ | Etapa | Prova |
|---|---|---|
| R2-01 Comex por NCM | EX0/EX1 | CSV oficial comparado com row count e soma FOB/KG |
| R2-02 IBGE IPP | EX0/EX1 | serie atividade/unidade/base real; no fabricated metal quotes |
| R2-03 BCB PTAX | EX1/EX2 | reuso contrato e falha 403 isolada |
| R2-04 Persistencia owner | EX1 | PG migration/constraints/retention/idempotency |
| R2-05 S2S REST | EX1 | OpenAPI positive/sibling/negative e auth |
| R2-06 BFF | EX2 | Core AuthZ e series metric_kind |
| R2-07 kit UX | EX3 | Chart/tabela/filters e labels corretos |
| R2-08 regressao/quarentena | ALL | CNPJ+WB LME policy negative, no source leakage |
| R2-09 Help/smoke | EX3/EX4 | help sync, F5, 403, mobile, visual |
| R2-10 operacao/gate | EX4 | image digest, source provenance, rollback |

## 8. Runbook e stop conditions

- Iniciar com git fetch, HEAD/git status, authorities .cursor, README/IMPLEMENTATION-PLAN, ADRs/contratos, apps reais. Se nova fonte/licenca/contrato invalida premissa, **EXECUTION_DRIFT** e freeze da fatia.
- Data acquisition via hosts oficiais allowlisted, timeout finite, limites/safe CSV/XLS/JSON parser, retry/backoff compliant e header identificavel. Nao usar credenciais no frontend/commits/log.
- Ingestion incremental orientada a mes; novas revisoes devem ser reprocessadas idempotentemente, com provenance e rollback/kill switch, nunca guardar dados ficticios como reais.
- Feeds e UI feature OFF em producao ate aprovacao operacional, testes PG em banco PROVADAMENTE descartavel. Protecao da quarentena LME antiga fica independente e obrigatoria.
- O pipeline so e PASS se usuario autorizado visualizar metricas reais de Comex/IBGE/BCB disponiveis com fonte, unidade, qualidade, e a pagina anterior estiver com gate fechado. Falha de egress BCB impede **a fatia cambial real**, nao invalida dados USD/indice se estes estiverem corretos.
- Cursor/Devin deve retornar BASE/FINAL HEAD, STATUS, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES, CONTRACT IMPACT, TESTS, SECURITY, RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION, UNRESOLVED, NEXT STEP.

## 9. Decisoes e evidencias externas

- MDIC dados abertos CSV oficiais: https://www.gov.br/mdic/pt-br/assuntos/comercio-exterior/estatisticas/base-de-dados-bruta (consulta 2026-10-26).
- IBGE IPP oficial: https://www.ibge.gov.br/estatisticas/economicas/precos-e-custos/9282-indice-de-precos-ao-produtor-industrias-extrativas-e-de-transformacao.html (consulta 2026-10-26).
- BCB boletins PTAX: https://dadosabertos.bcb.gov.br/dataset/taxas-de-cambio-todos-os-boletins-diarios (consulta 2026-10-26).
- Repo authority: docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md; .cursor/rules; ADR-009; X0/X3; codigo no HEAD. **Datasets abertos nao equivalem a licenca irrestrita para todos os usos.**
