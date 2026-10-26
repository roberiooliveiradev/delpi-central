# PROC-0076 — Dashboard Inteligência de Mercado: BFF + Wireframes

> Status: **TARGET / PROPOSED / NOT IMPLEMENTED** · 2026-10-26
> Inventário: main 270054a84243c0ee1aa60f06d1857be86f9095f2.
> Contexto: TÉO PROC-0076 e GLPI #527. Regras: .cursor, ADR-009, ADR-010, README/IMPLEMENTATION-PLAN. E11 em foco, GATE-FEATURE INCONCLUSIVE (smoke autenticado pendente).
> Dependência: [Contrato external-data-api / PROC-0076 P0](../shared-integrations/PROC-0076-EXTERNAL-MARKET-DATA-P0-ARCHITECTURE-AND-API-CONTRACTS-20261026.md).

## 1. Produto e navegação

Página proposta: **Inteligência de Mercado — Cotações de Metais e Câmbio**.
Deep link candidato: /apps/supplies/market-intelligence. Este path ainda **não** existe nem está autorizado no manifest. Área de navegação a validar com a IA vigente: Compras/Negociações ou atalho da Visão Geral.

Finalidade: apresentar séries históricas confiáveis, período diário/mensal/anual, USD/BRL convertido e médias mensais para subsidiar Compras e Vendas. Sem compra automática, savings automático, precificação TOTVS, previsão ou CRUD de cotação.

AuthZ: effective permission Core supplies.access via supplies-api (fail-closed). supplies.manage não implica access; nenhuma permission nova. Dados de mercado podem ser globais sem filtro de filial; nunca impor unidade fictícia. MFE só consome supplies-api.

## 2. BFF REST — PROPOSTA, SEM ROTAS EXISTENTES

| Method | Path supplies-api | operationId proposto | Responsabilidade |
|---|---|---|---|
| GET | /market-intelligence/filters | listMarketIntelligenceFiltersV1 | Catálogo de instrumentos/séries, moedas, granularidades, coverage e fontes homologadas |
| GET | /market-intelligence/summary | getMarketIntelligenceSummaryV1 | Último valor, média, variação e câmbio de referência + frescor |
| GET | /market-intelligence/series | listMarketIntelligenceSeriesV1 | Série temporal para gráfico/tabela, com proveniência e unidade |
| GET | /market-intelligence/monthly-averages | listMarketIntelligenceMonthlyAveragesV1 | Média por mês, número de observações e cobertura |

Base pública de gateway: /apps/supplies-api. Estes paths e nomes são **candidatos a contract freeze**, não contrato implementado. O BFF lê external-data-api por HTTP S2S (GET /v1/market-data/catalog, /metals/observations, /fx/observations), sem acesso PostgreSQL cross-context ou consulta direta à internet.

Filtros: instrument_code identificado por catálogo, currency USD|BRL, granularity day|month|year, date_from/date_to ISO, fx_kind homologado. Listas e ranges ficam bounded; máximos definitivos dependem da fonte e do P0. No browser: URL parametrizada com instrument, currency, granularity, from, to e fx_kind (keys finais a congelar), permitindo F5/back-forward, sem confiar no cliente.

### BFF response /series TARGET

~~~json
{
  "instrument": {"code":"APPROVED_INSTRUMENT","label":"Cobre","unit":"SOURCE_UNIT","quote_basis":"APPROVED_BASIS"},
  "currency": "USD",
  "granularity": "month",
  "points": [{"period":"2026-09","value":null,"observation_count":0,"coverage":"no_data"}],
  "meta": {
    "source_id":"APPROVED_SOURCE",
    "fx_source_id":null,
    "fx_kind":null,
    "method_version":"PENDING_APPROVAL",
    "as_of":null,
    "data_status":"no_data",
    "last_successful_ingestion_at":null,
    "partial_reason":null
  }
}
~~~

Números decimais devem preservar precisão em contratos/serialização e UI. Null não equivale a zero. BRL exige pareamento pelo tipo/data do USD/BRL e regra de média/conversão homologados. Diferenciar falta de FX de ausência de metal. Period averages incluem contagem/coverage e fonte. Nunca somar metais de unidades ou modalidades diferentes.

### BFF response /summary TARGET

~~~json
{
  "last_quote":{"value":null,"reference_date":null,"currency":"USD","unit":"SOURCE_UNIT"},
  "period_average":{"value":null,"valid_observations":0,"coverage":"no_data"},
  "period_variation":{"percent":null,"calculation_method":"PENDING_APPROVAL"},
  "fx_reference":{"value":null,"pair":"USD/BRL","rate_kind":"PENDING_APPROVAL","reference_date":null},
  "meta":{"data_status":"no_data","source_id":"APPROVED_SOURCE","updated_at":null}
}
~~~

Erro por classe: 401 sem sessão; 403 sem access Core; 404 instrumento inexistente; 422 filtros inválidos; 429 upstream/budget e Retry-After; 502 resposta inválida; 503 source/storage indisponível; 504 timeout. A negativa técnica 401/403 de S2S downstream **não** vira 403 de usuário; resolver status conforme padronização BFF. Estale/stale autorizado mostra última data explícita, não “cotação atual”. Toda rota deve ter OpenAPI/operationId, paginador e teste contratual.

## 3. WIREFRAME DESKTOP — estado sem dados real

~~~text
+--------------------------------------------------------------------------------+
| Início › Visão geral › Inteligência de Mercado                       [? AJUDA]|
+--------------------------------------------------------------------------------+
| COTAÇÕES DE METAIS E CÂMBIO                                                |
| Contexto de mercado para decisões de Compras e Vendas                       |
| Origem: não homologada  | Atualizado: indisponível | Unit/base: a confirmar|
+--------------------------------------------------------------------------------+
| SÉRIE / METAL            MOEDA            GRANULARIDADE        PERÍODO       |
| [ Cobre (série) v ]      [ USD | BRL ]    [ Diário | Mensal | Anual ]       |
| [De:__/__/____] [Até:__/__/____]   [Limpar]  [? metodologia]               |
+------------------+------------------+------------------+------------------+
| ÚLTIMA COTAÇÃO   | MÉDIA PERÍODO    | VARIAÇÃO         | DÓLAR REFERÊNCIA |
| —                | —                | —                | —                |
| Ref.: —          | Amostras: 0      | Sem comparação   | Tipo: pendente   |
+------------------+------------------+------------------+------------------+
| EVOLUÇÃO HISTÓRICA                                                            |
| Cobre · USD · Mensal                                                          |
| +---------------------------------------------------------------------------+  |
| |              Gráfico indisponível: não existem dados homologados         |  |
| +---------------------------------------------------------------------------+  |
| Fonte, unidade, quote_basis, período, cobertura e FX devem acompanhar pontos |
+--------------------------------------------------------------------------------+
| HISTÓRICO E MÉDIAS                                                           |
| Período | Média | Amostras válidas | Cobertura | Fonte | Referência        |
| —       | —     | 0               | sem dados | —     | —                 |
| [Paginação server-side quando necessária]                                     |
+--------------------------------------------------------------------------------+
| FONTE E METODOLOGIA: licenciamento, data de referência, taxa FX, média       |
| [? Como converter?] [? Por que faltam alguns dias?]                         |
+--------------------------------------------------------------------------------+
~~~

### Wireframe mobile

~~~text
+-------------------------------+
| < Inteligência de Mercado [?] |
| Cotações de Metais e Câmbio   |
| Fonte e atualização          |
+-------------------------------+
| Metal / série [Cobre v]       |
| Moeda: [USD] [BRL]            |
| Período: [Dia][Mês][Ano]      |
| [Data início] [Data fim]      |
+-------------------------------+
| Última cotação: —             |
+-------------------------------+
| Média do período: —           |
| Observações válidas: 0        |
+-------------------------------+
| Variação: —                   |
+-------------------------------+
| Dólar de referência: —        |
+-------------------------------+
| EVOLUÇÃO                      |
| [Gráfico / estado vazio]      |
| [Ver como tabela acessível]   |
+-------------------------------+
| MÉDIAS                       |
| > Mês · valor · cobertura     |
+-------------------------------+
| Fonte / Unidade / Metodologia |
+-------------------------------+
~~~

## 4. Componentes do Portal e UX

Inventário de wrappers reais em plugins/supplies/src/app/suppliesUi.ts: SuppliesPageHero, SuppliesPagePath, SuppliesFilterBarShell, SuppliesSelectField, SuppliesDateField, SuppliesSegmentToggle, SuppliesSectionCard, SuppliesLoadingCard, SuppliesEmptyState, SuppliesStateBanner, SuppliesDataTable, SuppliesCompactPagination e SuppliesChartGranularityToggle. Usar @delpi/plugin-ui e wrappers existentes antes de novo componente/chart library. CSS confinado em .dashboard-supplies-portal.

Gráfico: linha de evolução com tooltip para metal/série, moeda, UM, preço, data de referência, quote_basis, fonte, status e taxa FX quando BRL. A tabela é alternativa acessível ao gráfico. Cards mostram — quando null, nunca 0, e datas/fonte legíveis. Filtros refletem URL (incluindo reload), sem cálculo financeiro no browser. Comparação multiproduto, previsão, integração direta com PC e export ficam FORA do P0 até decisão/licença.

## 5. Estado da tela e casos

| Estado | Comportamento |
|---|---|
| Initial/loading | Skeleton kit-first sem pular layout; catálogo e filtro dependente protegidos |
| Success | Dados, fonte, unidade/base, reference date e last refresh visíveis |
| Empty/no_data | Não há cotações no período; zeros fictícios proibidos |
| Stale | Histórico permitido exibido com aviso de defasagem |
| Partial | FX sem dados: USD continua utilizável; BRL indisponível, sem conversão fictícia |
| Rate limited | 429/Retry-After informado sem loop de retry |
| Provider down | Banner erro + retry de leitura, jamais coleta acionada pelo MFE |
| 401/403/404 | Estados distintos com mensagens neutras e sem vazamento |
| Invalid filter | 422 com correção acessível |
| Mobile | Cards empilhados, tabela responsiva sem largura forçada |
| Theme/keyboard | Claro/escuro, contraste, foco visível, Tab/order, labels e alternativa tabular |
| URL/F5 | Persistência via query, back/forward, validação allowlisted |

## 6. Ajuda sincronizada

Atualizar no mesmo commit da feature user-facing: plugins/supplies/src/content/userManualContent.ts, FAQ/glossário/Quero→onde e docs necessários. Glossário: cotação de referência, metal/série, UM, bolsa/provedor, base da cotação, data observada versus data coletada, câmbio USD/BRL, taxa de referência, média, cobertura, stale e fonte. Explicar que cotação de mercado não representa preço negociado/PC real, nem substitui decisão humana.

## 7. RQ/AC ledger e testes

| RQ | AC | Owner/test |
|---|---|---|
| RQ-76-01 catálogo metais | AC-76-01: instrumento, UM, base, fonte aprovados; não aceitar código arbitrário | external-data + BFF |
| RQ-76-02 granularidade | AC-76-02: data/mês/ano e ranges com limites, paginação e URL/F5 | BFF + MFE |
| RQ-76-03 moeda | AC-76-03: USD nativo, BRL somente com FX/formula por data homologados | S1 + BFF |
| RQ-76-04 médias | AC-76-04: média reproduzível + count/coverage, ausências explícitas | external-data/BFF |
| RQ-76-05 proveniência | AC-76-05: fonte, data, unidade, referência e método versionado | all |
| RQ-76-06 erros/stale | AC-76-06: empty/partial/stale/timeout/rate limit não simulam dados | all |
| RQ-76-07 UX | AC-76-07: kit-first, responsivo, temas, teclado, Help e smoke autenticado | MFE/runtime |
| RQ-76-08 AuthZ | AC-76-08: Core effective supplies.access; S2S individual; zero permission nova | BFF/external |
| RQ-76-09 storage | AC-76-09: external-data schema owner isolado e sem acesso cruzado | external-data |

## 8. Roadmap de execução e GATE

S1 = fontes/termos, formulação FX/UM/média, ownership DB, migrations e contract freeze. S2 = external-data-api (schema proprietário, job e read APIs). S3 = supplies-api BFF. S4 = MFE + Ajuda, somente com GATE E11 reconciliado e autorização de página. S5 = deploy + teste real federado + prova de referência e formula. Para cada S*: HEAD/git status, authorities, contratos, testes, positive+sibling+negative, evidence e SHAs; classificação PASS/FAIL/TEST_NOT_RUN/INCONCLUSIVE. Não promover PROPOSED a IMPLEMENTADO; evitar execução paralela de nova página enquanto E11 permanece INCONCLUSIVE.

---

## Reconciliacao R1 — contrato vigente (2026-10-27, fix/proc-0076-r1)

As 4 rotas existem conforme candidato (`/market-intelligence/{filters,summary,series,monthly-averages}`, `supplies.access`, S2S external-data-api). Ajustes de semantica do R1 sobre a proposta:

- **Freshness:** `meta.freshness` (objeto) substitui a heuristica antiga que marcava `stale` pela distancia hoje-ultima_observacao. Agora: `expected_cadence` (`monthly`|`business_daily`), `expected_latest_period`, `latest_observation_date`, `lag_periods`/`lag_days`, `last_successful_ingestion_at`, `evaluation_date`, `method`. Consulta historica completa **nao** e `stale`; feed atrasado vs ciclo de publicacao e. Ausencia de boletim PTAX em feriado/fds nao e falha.
- **Unidade/moeda:** `summary.last_quote.unit` reflete a moeda exibida (`BRL/metric ton` quando convertido; `USD/metric ton` nativo); `last_quote.native` preserva valor/moeda/unidade de origem e `last_quote.conversion` expõe `fx_kind`, `fx_rate`, `fx_reference_period`, `method`. `period_average.unit`, `series.unit`/`native_unit`, `monthly-averages.unit`/`native_unit` no envelope. Sem taxa sintetica: mes sem PTAX = `null` + `partial_reason=fx_missing`.
- **MFE:** KPI de ultima cotacao exibe `unit` corrigida; banner stale inclui evidencia temporal (ultima observacao vs periodo esperado); erros 401/403 tem mensagens neutras distintas; glossario/manual explicam stale por cadencia. `recharts` no plugin-ui via kit (`MultiTypeSeriesChart`), sem lib paralela.
- **Inalterado:** sem permission nova, sem calculo no MFE, zeros ficticios proibidos, granularidade day/month/year, URL/F5/back-forward, alternativa tabular acessivel, wireframe aprovado mantido.