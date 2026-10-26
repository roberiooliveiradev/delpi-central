# PROC-0076 — Plano completo de execução autônoma para Devin

> **Status:** PLANNED / CODE_NOT_EXECUTED / DEPLOY_NOT_AUTHORIZED_BY_THIS_DOCUMENT
> **Data:** 2026-10-26 · **Repositório:** roberiooliveiradev/delpi-central
> **HEAD inspecionado:** main 7ac64f9732a0f20acf974b32712e9cd1e154842b. Revalidar em cada execução.
> **Base de negócio:** TÉO PROC-0076, GLPI #527, solicitação Joici Motta.
> **PR de documentação:** #111, branch docs/supplies-proc-0076-market-intelligence-p0-20261026
> **Companheiros:** [API externa/DB](../shared-integrations/PROC-0076-EXTERNAL-MARKET-DATA-P0-ARCHITECTURE-AND-API-CONTRACTS-20261026.md) · [BFF e wireframes desktop/mobile](./PROC-0076-MARKET-INTELLIGENCE-BFF-CONTRACTS-AND-WIREFRAMES-20261026.md)

## 0. MISSÃO E MODO DE EXECUÇÃO

**GOAL:** Entregar uma página nativa de Cotações de Metais e Câmbio no Portal Suprimentos, com dados externos autorizados, histórico persistente no PostgreSQL de plugins, APIs internas e BFF, dashboard de gráficos/médias/FX, experiência visual do Portal, rastreabilidade e aceites comprovados.

**TASK:** Seguir obrigatoriamente external-data-api → supplies-api → plugin-ui/MFE supplies → QA/runtime/docs. Devin deve agir com autonomia **sem microaprovações**, fazendo inspeção, implementação, testes, correções e commits necessários por etapa. Não parar por escolha local de implementação quando autoridade e contrato forem claros. Corrigir as falhas que descobrir e retestar antes de avançar. Preservar working tree e trabalho de terceiros. Não reescrever ADR/contrato para justificar diff.

**STOP-THE-LINE apenas na fatia afetada**, sem congelar trabalho independente: uso de dados sem licença/termos; secrets/acesso não disponíveis; conflito de owner/schema; alteração produtiva sem autorização; código invalida contrato; E11 ainda sem GATE-FEATURE para entrada na nova página. Continuar com modelos, fixtures claramente sintéticas, testes, contrato, documentação e componentes independentes, mas classificar FATIA BLOQUEADA quando necessário. Nunca simular consentimento, dado real, prova visual ou PASS.

### AUTHORITIES OBRIGATÓRIAS

1. docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md.
2. .cursor/rules globais: development-standards-index, evidence-driven-execution, centralized-rules-first, clean-code-architecture-guardrails, english-code-identifiers.
3. Especializadas: plan-construction, plan-execution, test-and-commit, platform-architecture-boundaries, platform-api-contracts-integration, platform-data-persistence, platform-security-identity-authorization, platform-frontend-mfe-experience, platform-quality-testing, platform-delivery-runtime-operations, feature-help-sync, contract-evolution-backward-compatibility, http-integration-resilience, plugin-mfe-page-excellence, mf-federation-patch-safety e migrations-immutable-checksum. Selecionar outras só pela responsabilidade.
4. ADR-009 e ADR-010, EXTERNAL-DATA-API-CONTRACT-FREEZE-X0, X3-RUNTIME-EVIDENCE-20261022; docs/12-roadmap-e-evolucao/supplies/README.md, IMPLEMENTATION-PLAN.md, API-ROUTES.md, WIREFRAMES.md; três documentos PROC-0076. Planos não superam contratos/HEAD.

### PRE-FLIGHT SEM NOVAS PERGUNTAS

- git fetch; registrar BASE HEAD, origin/main, git status; usar branch de execução separada do draft docs quando adequado e preservar diffs alheios.
- Ler implementação real em external-data-api/app, supplies-api/app, supplies-api/migrations, plugins/plugin-ui/src/components, plugins/supplies/src/{app,features,api,content}, infra/docker-compose.yml, testes e consumidores; procurar duplicação antes de criar arquivo.
- Estabelecer ledger RQ/AC abaixo, CURRENT/TARGET e owner de cada conceito, validar schemas e S2S. Não inferir ausência de busca negativa.
- Resolver drift documental: README atual aponta E11 executada com GATE-FEATURE INCONCLUSIVE (smoke federado autenticado); IMPLEMENTATION-PLAN tem cabeçalho histórico E10 em foco. A autorização deste pedido não substitui gate anterior. Buscar evidência mais recente; smoke autorizado pode resolver, senão conservar bloqueio de entrada na nova página.
- Registrar source rights / dataset layout / formula; se houver EXECUTION_DRIFT revalidar fatia, não adaptar código silenciosamente.

## 1. MODELO DE DADOS E FONTES — CAMINHO EXECUTÁVEL

**CURRENT PROVEN:** external-data-api é Flask, S2S client_credentials Keycloak, interna e sem Postgres; GET /v1/cnpj/{cnpj} existe com BrasilAPI, rate limiter Redis. supplies-api já tem gateway HTTP/S2S para CNPJ; postgres-plugins (PG15) existe. O schema supplies é estado próprio do BFF e não deve armazenar cotações externas.

**TARGET:** external-data-api será owner de aquisição, normalização, storage e séries; proposta de schema dedicado external_data no mesmo servidor postgres-plugins, com role/grants/runner próprios após confirmar infra. supplies-api consumirá **somente HTTP/S2S**. MFE consumirá **somente supplies-api**. Não existe transferência de ownership de SQL TOTVS.

### Fontes candidatas e decisão autônoma por capacidade

- **USD/BRL oficial:** API PTAX do Banco Central, dataset diário https://dadosabertos.bcb.gov.br/dataset/dolar-americano-usd-todos-os-boletins-diarios ; OData https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao . O catálogo lista licença ODbL. Devin deve identificar série de **fechamento/venda**, sua data de referência e obrigação de atribuição; não substituir por horário aleatório de boletim.
- **Metais mensais:** Banco Mundial Pink Sheet https://www.worldbank.org/en/research/commodity-markets , planilha mensal XLS; termos de datasets https://www.worldbank.org/ext/en/legal/terms-conditions/datasets . Licença CC BY 4.0 é default, porém dados de terceiros podem ter restrições específicas. Verificar metadados/licença série por série **antes de habilitar coleta ou exibição**. Candidatos: cobre, alumínio, zinco, níquel, chumbo e estanho conforme série realmente publicada.
- **Metais diários LME/Shockmetais:** GLPI refere https://shockmetais.com.br/lme e arquivo em rede; **não há contrato API ou licença comprovados**. Não fazer scraping nem usar feed alternativo não autorizado. Só habilitar daily-metal após fonte formalmente licenciada.
- Fonte não liberada permanece DISABLED no catálogo; implementar adapter/teste com fixture sintética identificada e continuar fatias independentes; **não declarar LIVE_DATA_PASS**.

### Cobertura e fórmula inicial (PROPOSED, sujeita a homologação de negócio)

- Pink Sheet tem série mensal já agregada; cada linha é valor publicado para o mês, não uma cotação de cada dia. Mês é exibido como referência média mensal publicada; **não fabricar observações diárias**.
- BCB: FX venda/fechamento em dias válidos. FX médio mensal = média aritmética das observações diárias oficiais válidas, com valid_count/coverage. Feriado sem boletim não equivale a zero.
- BRL mensal indicativo = valor USD mensal da série metálica × média mensal da PTAX venda do mesmo mês. Label obrigatório: “Conversão indicativa: referência mensal do metal × média mensal PTAX venda”. Não alegar preço de compra TOTVS ou média de conversões diárias.
- Variação do período: (último valor válido / primeiro valor válido - 1) × 100, se início não-zero e ao menos duas referências distintas. Anual: média aritmética de meses válidos, label “média dos meses observados” com n/12 e parcialidade, não média diária.
- Métodos devem possuir method_version, query/data-source metadata e fixture de verificação Decimal; se houver autoridade conflitante, congelar fórmula problemática e continuar série USD original.
- Na UI: metais permitem month/year até existir daily-metal licenciado; painel de câmbio pode day/month/year; filtros disponíveis vêm do catálogo BFF. UX nunca mascara mensal como diário.

## 2. TRILHA ATÔMICA DO DEVIN

~~~text
D0 PRE-FLIGHT + RIGHTS/SERIES CONTRACT
   ↓ proof
D1 EXTERNAL-DATA-API
  D1.1 schema + migration/DB role
  D1.2 providers adapters PTAX/Pink Sheet
  D1.3 ingestion job, idempotency, freshness
  D1.4 internal GET /v1/market-data/*
  D1.5 producer integration/tests
   ↓ proof
D2 SUPPLIES-API
  D2.1 S2S gateway
  D2.2 business read-model/derived-methods
  D2.3 BFF GET /market-intelligence/*
  D2.4 Core AuthZ/tests/OpenAPI
   ↓ proof, E11 gate
D3 PLUGIN-UI + PLUGINS/SUPPLIES
  D3.1 inventory/reuse generic kit
  D3.2 feature/route/dashboard/URL
  D3.3 HELP, responsive, A11y, tests
   ↓ proof
D4 E2E + DEPLOY CONDITIONS + DOCUMENT + FINAL REPORT
~~~

**Gate de cada fatia é local e automático:** ao demonstrar sua postcondition via testes/contrato, continuar para seguinte READY. Se fatia bloqueada, realizar apenas próximos subtrabalhos independentes e manter dependências INCONCLUSIVE, sem postcondition falsa.

### D0 — Fonte, owner e contratos

**Propósito:** nenhuma implementação baseada em suposições. Fazer inventário do schema/role postgres-plugins, migrations runner e deploy; verificar dados e licença; identificar APIs/config de CNPJ e comparar contratos X0/ADR. Checar direito de ingestão, retenção, derivados, display interno, atribuição, cache, export, terceiros e date/price basis. Definir catálogo de instrumentos, unidade/moeda/qualidade/periodicidade. Documentar licenças/termos em decisão versionada. Definir OpenAPI candidato e origem do scheduler. Revalidar gate E11.

**Aceite D0:** registro PROVEN/TO_INVENTORY por fonte e por contrato; schema owner confirmado ou schema candidato claramente condicionado; cálculo/UM identificados e histórico CNPJ preservado; E11 gate com evidência ou INCONCLUSIVE. Não alterar infraestrutura produtiva.

### D1 — external-data-api: producer, storage, fontes e rotas

**Propósito:** serviço externo passa a armazenar séries autorizadas e servi-las sob S2S sem alterar GET /v1/cnpj/{cnpj}.

**D1.1 Persistência/migration**
- Modelar schema owner candidato external_data no postgres-plugins com role exclusivo, sem acesso direto supplies-api; migrações novas imutáveis (nunca editar migration aplicada), runner checksum versionado e configuração env secrets.
- Propor e implementar conforme freeze tabelas: external_data.market_data_sources (licença/atribuição/status), external_data.metal_instruments (metal+instrument_code+quotation_basis+native_unit+currency+source), external_data.metal_quote_observations (instrument_id+period_start+granularity+price NUMERIC+source+quality+retrieved/revised), external_data.fx_rate_observations (pair+rate_kind+reference_date+value NUMERIC+source+timestamp/quality), external_data.market_data_ingestion_runs (run/feed/times/status/counts/safe error/correlation). Normalizar valores e origem, sem raw XLS/HTML persistido por padrão.
- UNIQUE/fingerprint de identidade econômica: instrumentos não se mesclam por unidade ou modalidade; observação unique (instrument,period_start,granularity,source); FX unique (pair,rate_kind,date,source); FKs, CHECK, índices por instrumento/data e FX/date; revisions/last fetched registrados sem sobrescrever histórico silenciosamente.
- Testar schema vazio, upgrade, FK/unique, concorrência, transação, rollback, idempotência, restart, backup/restore. Não usar float para preço/câmbio; usar Decimal no domínio + NUMERIC no banco. Não rodar migration produtiva sem autorização específica de owner/infra.

**D1.2 Adapters provedores**
- Reusar infraestrutura de HTTP config, erros e rate limit onde é contrato técnico comum; criar ports próprios de mercado e provider adapters independentes por feed (PTAX e WB, mais disabled default). Não importar domínio do CNPJ nem adicionar seleção de URL arbitrária.
- PTAX: datasource OData por período, data/timezone, boletim fechamento/venda, paginação, validação JSON e taxas; distinguir sem observação de indisponibilidade.
- WB: import mensal XLS por URL oficial da página catálogo; verificar MIME/tamanho/estrutura e planilha Description; parser defensivo para codificação/colunas/revisões/mês ausente; registrar metadata e não relabelar cotação como LME diária.
- Host allowlist, timeout finito, quota, Retry-After 429, no retry em 403 legal/denial, respeito a termos, logs sem payload bruto/secrets, fail-closed em provider disabled.

**D1.3 Job agendado**
- Job interno do serviço ou scheduler infra existente, idempotente e singleton/lock. FX diário; WB mensal após divulgação, conforme fonte. Backfill bounded e incremental, possibilidade de correções retroativas, retry controlado, checkpoints/recovery. Não envolver HTTP externo dentro de transação DB. Falha parcial preserva último dataset bom e run.status PARTIAL/FAIL com contagens reais; não apagar dados autorizados por erro de rede.
- Não dar endpoint público para UI executar coleta. Status read-only S2S por feed; datestamp da última tentativa, última carga bem-sucedida, lag e source availability.

**D1.4 API interna — paths TARGET até freeze**
- GET /v1/market-data/catalog — instrumentos ativos, UM, basis, source, granularities, cobertura.
- GET /v1/market-data/metals/observations — instrument_code, from/to, cursor/limit bounded e ordenação estável; preço native e provenance.
- GET /v1/market-data/fx/observations — USD/BRL+rate_kind+range, paginação, valores oficiais.
- GET /v1/market-data/ingestion-status — last_success, state, lag, safe error e dataset revision.
- S2S Keycloak via X-Delpi-Service-Authorization, issuer/JWKS/audience, allowlist supplies-api, nenhuma rota nginx do serviço externo. Nenhum JWT de usuário repassado. OpenAPI versionado, operationId estável e único; DTO decimal com precisão (string serializada), source_id, provider_id, currency, unit, basis, period, retrieved_at, quality, schema/method version.
- Contratos de erros compatíveis: 400 bad query, 401/403 S2S, 404 unknown instrument, 422 unsupported date/granularity, 429 + Retry-After, 502 invalid provider response, 503 source/storage unavailable, 504 timeout. 200 sem dados só com payload empty e data_status=no_data explícito. O GET histórico consulta banco do serviço, **não a internet a cada acesso do usuário**.

**D1.5 Testes/aceite**
- Testes de parser e schema source, moeda, dia/mês/ano, daily FX/monthly metal, idempotência replay, concorrência, provedor 403/429/5xx, timeout, MIME/colunas XLS inválidos, provider disabled, multi-source mismatch, unique/FK/upgrades.
- Auth S2S positive/sibling/negative: token válido e allowlist, spoof/sem token, aud errada, 401/403, upstream zero calls before auth, rate limiting; todos os testes CNPJ existentes continuam PASS.
- **Postcondition:** S2S consulta histórico persistido do schema owner e CNPJ não regrediu. Sem licença/provider live, registrar D1_CODE_PASS e LIVE_SOURCE_INCONCLUSIVE — nunca dizer “metais reais integrados”.

### D2 — supplies-api: gateway e BFF

**Propósito:** fornecer uma única interface ao MFE, com AuthZ efetiva e cálculo/versionamento controlados.

1. Inspecionar external_data_company_registry_provider.py e shared delpi_auth para reutilizar padrão S2S; criar gateway de mercado independente, timeout/error typed, sem alterar adapter CNPJ.
2. Criar use cases de catálogo/filters, summary, séries e médias, com domínio mínimo e cálculos Decimal versionados, conversão mensal explicitamente indicativa, coverage e data_status fresh/stale/partial/no_data. Não duplicar persistência no schema supplies e não acessar internet diretamente.
3. Rotas candidatas no Flask em /apps/supplies-api:
   - GET /market-intelligence/filters
   - GET /market-intelligence/summary
   - GET /market-intelligence/series
   - GET /market-intelligence/monthly-averages
4. Validar instrument_code, date_from/to ISO, currency USD|BRL, granularity disponível, fx_kind e limites/paginação; não montar query ilimitada nem multiplicar chamadas sem bound. BFF mapeia erros técnicos do S2S com estados apropriados; 401/403 de backend S2S **não** é 403 do usuário.
5. Resolver effective permissions na Core. O catálogo atual ADR-009 é somente supplies.access (consulta) e supplies.manage (admin independente), sem grants por metal, filial, gráfico ou CRUD. Com Core unavailable, fail-closed; não confiar em JWT claims para autorizar. Dados de mercado globais não recebem filtro fake 01/02, salvo business restriction formalmente provada.
6. Envelope REST/DTO e OpenAPI devem seguir os contracts atuais da supplies-api, com source/date/unit/method, last ingest e qualidade. Correlation-id propagado. Contratos backward-compatible.
7. Unit + gateway + HTTP tests para positive (metal USD), sibling (outro metal ou somente FX), negative (range/metal inválido, vazio, FX faltante, denom zero), Core deny/unavailable, S2S deny, timeout 429/502/503/504, regressão de suppliers/CNPJ.
8. **Postcondition D2:** rotas novas atendem HTTP read-model correto, autorizadas e com testes de conversão reais ou fixture marcadas. Não mudar status documental PLANNED→IMPLEMENTADO até existir evidência em código e teste.

### D3 — plugin-ui e MFE plugins/supplies

**Propósito:** página com qualidade visual equivalente às demais, kit-first, sem lógica financeira no cliente e sem novo design system. Entrar na nova página somente quando GATE-FEATURE anterior da fila estiver fechado e a autorização de página reconciliada. Se E11 INCONCLUSIVE persistir, preparar kit/docs/fixtures independentes e não ativar nova rota/deploy como se a feature estivesse liberada.

**D3.1 Reutilização de componentes COMPROVADOS no HEAD**
- Fonte: plugins/plugin-ui/src/components/charts/LineSeriesChart.tsx, ConfigurableSeriesChart.tsx, ChartViewShell.tsx, MultiTypeSeriesChart.tsx, StableResponsiveContainer.tsx (exports via charts/index.ts e @delpi/plugin-ui/index).
- Wrappers no MFE: plugins/supplies/src/app/suppliesUi.ts contém SuppliesPageHero, SuppliesPagePath, SuppliesFilterBarShell, SuppliesSelectField, SuppliesDateField, SuppliesSegmentToggle, SuppliesSectionCard, SuppliesLoadingCard, SuppliesEmptyState, SuppliesStateBanner, SuppliesDataTable, SuppliesCompactPagination, SuppliesChartGranularityToggle.
- Padrões visuais/funcionais: features/overview/OverviewOtdSeriesChart.tsx, features/analytics/OtdAnalyticsPage.tsx, features/safety-stock/SafetyStockPage.tsx e query.ts.
- Importar de @delpi/plugin-ui/index por Module Federation; **não** duplicar componentes em supplies, instalar chart library paralela ou copiar código do kit. Composição local é permitida, componente genérico compartilhável ausente deve ser adicionado ao plugin-ui com API aditiva, teste próprio e regressão de outros consumidores. Não tocar CSS global; manter .dashboard-supplies-portal e tokens do kit.
- Para gráfico usar kit line/series + view shell, table fallback acessível; formatar números no MFE somente para exibição, toda média/conversão vem do BFF.

**D3.2 Página e roteamento**
- Estrutura candidata: plugins/supplies/src/features/market-intelligence/{MarketIntelligencePage.tsx,MarketFilters.tsx,MarketSeriesChart.tsx,MarketAveragesTable.tsx,api.ts,types.ts,query.ts,content.ts,tests}.
- Integração apenas por client existente plugins/supplies/src/api/httpClient, AbortController para mudança rápida de filtros, race guard contra resposta antiga.
- Após gate, mapear view e path em pluginRoutes.ts, App.tsx, conteúdo de navegação e supplies.manifest.json schemaVersion 1.0.0, rota /apps/supplies/market-intelligence; usar supplies.access já existente, não criar permission ou rota v2. URL query allowlist instrument/currency/granularity/from/to, suporta F5/back-forward e deep links; estados 403/404 distintos.
- Compor PageHero + breadcrumb + subtítulo; linha de metadados de fonte/last refresh, filtros por série, USD/BRL, período e agregação suportada; quatro cards; gráfico de linha com tooltip acessível; tabela paginada de histórico/médias. Matching de design com Overview/OTD/Estoque.
- Cards: última cotação (referência e unidade), média (n/coverage), variação (duas datas-base), câmbio (tipo e referência). Quando null, mostrar — e justificativa; nunca zero falso ou moeda ilegítima.

**WIREFRAME DESKTOP — implementar exatamente este layout com kit**
~~~text
Início › Visão geral › Inteligência de Mercado                              [? Ajuda]
COTAÇÕES DE METAIS E CÂMBIO
Fonte: X  | Referência: data | Última coleta: data/hora | [stale se aplicável]
[Série / metal ▼] [USD | BRL] [Diário | Mensal | Anual (suportados)] [De] [Até]

[ÚLTIMA COTAÇÃO]     [MÉDIA PERÍODO]      [VARIAÇÃO]        [DÓLAR REF.]
Valor, moeda, UM     Contagem/cobertura   Datas comparadas  Taxa/tipo/data

EVOLUÇÃO HISTÓRICA
[LineSeriesChart / ConfigurableSeriesChart, with legend, accessible tooltip]
[Alternativa tabular dos mesmos pontos]

HISTÓRICO E MÉDIAS
Período | Valor | Moeda/UM | Amostras | Cobertura | Fonte | Status
[Paginação quando necessário]
[Metodologia e Fonte / Como interpretar os valores / Atribuição]
~~~

**WIREFRAME MOBILE**
~~~text
< Inteligência de Mercado [?]
Fonte / atualização / status
Série [cobre v]
USD | BRL
Granularidade [Mês v]
De [____] Até [____]
Última cotação [card]
Média [card]
Variação [card]
Dólar referência [card]
EVOLUÇÃO [chart responsivo + Ver como tabela]
HISTÓRICO [cards expansíveis sem scroll horizontal do portal]
Fonte e metodologia [?]
~~~

**D3.3 UX, Ajuda e testes**
- Estados initial/loading, success, empty/no_data, partial FX, stale, 401, 403, 404, 422, 429/Retry-After, 502/503/504 e retry somente de leitura. Não renderizar spinner infinito, não exibir demo como dado real. Granularidades não suportadas ficam desabilitadas/ocultas com texto explicativo.
- Claro/escuro, mobile/desktop, aria labels, contraste, foco/teclado e tabela alternativa a tooltip. Sem layout quebrado ou min-width arbitrário.
- Sincronizar plugins/supplies/src/content/userManualContent.ts, tooltips, glossário, FAQ, Quero→onde e docs na mesma entrega. Definir cotação mensal publicada, PTAX, taxa câmbio, conversão indicativa, último dado, cobertura, fonte, atraso, benchmark vs preço fornecedor/TOTVS.
- Rodar typecheck/build, lint, suites plugin-ui se alterado, Vitest da feature para data parsing, filtros/URL/F5, race guard, stale/partial/error e states 403/404, mobile/theming e keyboard. Smoke federado autenticado quando liberado; build isolado ≠ PASS runtime.
- **Postcondition D3:** página está roteada e renderiza BFF real com identidade visual nativa e Help, todos os AC de UX com prova. Se gate anterior bloqueia ativação, reportar D3_BLOCKED_BY_QUEUE, sem exibir link de página implementada.

### D4 — Integração, runtime e documentação final

**Propósito:** provar o objetivo original e fechar evidência sem false positives.

**Testes cruzados:**
- Fonte autorizada metal mensal + dois períodos distintos, outra série metal (sibling), USD/BRL PTAX em datas reais e lacuna. Comprovar fórmulas Decimal e version por fixture determinística separada do código.
- Ingestão repetida não duplica; atualização retroativa versionada; erro parcial preserva histórico bom; GET não chama internet; source stale explicita defasagem; mês faltante não vira zero.
- S2S 401/403 e Core effective 401/403/503; invalid dates/granularity, 429, 502, 503/504; CNPJ e Suppliers regressão verde.
- MFE deep link F5, filtros, chart/table, mobile, dark/light, keyboard, Help. Smoke federado autenticado com conta autorizada e conta negativa; se não há browser/conta, VISUAL_AUTHENTICATED=INCONCLUSIVE, nunca PASS.
- SQL migration vazio/upgrade/uniques/backup; live source sample com data, currency, UM, source, revised_at, attribution, FX e method. Não afirmar paridade com LME diário sem feed.

**Operação/deploy:**
- Documentar env sem secrets, S2S allowlist/audience, schema grants, scheduler configuração e rate limits; health não consulta provedor remoto. Feature/feed disabled por padrão até source rights e migração aprovados. Aplicar migração em homologação autorizada, com backup e rollback/rollforward; produção **somente com aprovação operacional específica** e gate anterior.
- Deploy sequencial (producer + DB → BFF → MFE), SHA/digest de cada serviço, smoke local/interno/federado e evidência de rollback. Kill-switch feed e UI sem drop schema e sem tocar CNPJ.
- Monitor last_successful_ingestion, lag por feed, 429/errors, count inserted/updated/skipped, monitoramento seguro sem secrets ou raw payload. Planos de retenção e atribuição auditáveis.

**Docs finais:**
- OpenAPI real das duas APIs, external-data-api/docs/README.md, shared-integrations, supplies/API-ROUTES.md e wireframes, README/IMPLEMENTATION-PLAN apenas linhas ativas afetadas, Ajuda in-app, ADR de mudança stateless→stateful, migration README/runbook, source rights register.
- Fases com commits separados por owner, PR revisável, diff adversarial, testes/exit codes e outcome. Não fazer auto-merge se algum gate material estiver FAIL/INCONCLUSIVE.

## 3. MATRIZ RQ/AC E PROVAS DE ACEITE

| RQ | Aceite observável | Owner/etapa | Teste |
|---|---|---|---|
| RQ-76-01 catálogo | Série/metais existem com fonte, basis, unidade, período; negar código livre | D1→D3 | Catalog contract e UI |
| RQ-76-02 granularidade | Metais monthly/year, daily só se autorizado; FX day/month/year; datas/URL/F5 | D1→D3 | Range, URL, widget |
| RQ-76-03 USD/BRL | Valor indicativo BRL requer FX no mês e método versionado; null sem FX | D1/D2 | Decimal + partial |
| RQ-76-04 médias | Mensal publicado, FX mensal calculado, yearly n/12; zero não substitui ausência | D1/D2 | Math fixtures |
| RQ-76-05 proveniência | Fonte, licença/atribuição, datas de observação/coleta, currency, unit, quote_basis, status | D1→D3 | DTO + tooltip |
| RQ-76-06 histórico | Persistência em schema owner com migration segura e reprocessamento idempotente | D1 | DB integration |
| RQ-76-07 boundary | GET external S2S; BFF Core; MFE somente BFF; sem SELECT de DB vizinho | D1→D3 | Integration architecture |
| RQ-76-08 AuthZ | supplies.access efetiva; JWT não é authority, sem permission nova; negative fail-closed | D1/D2/D3 | 401/403/503 |
| RQ-76-09 dashboard | Hero/filtros/cards/charts/tabela do kit, dados reais ou estado sem dados | D3 | Structural + visual |
| RQ-76-10 experiência | Mobile, claro/escuro, foco, tabela acessível, URL/F5 e Help sincronizada | D3/D4 | UI smoke/test |
| RQ-76-11 regressão | CNPJ, Supplier 360, auth e outros módulos inalterados | Todas | Suites/diff |
| RQ-76-12 runtime | Source rights, migrações, deploy, smoke auth, SHAs/digests, rollback | D4 | Runtime gate |

### Matriz de fluxo e anti-regressão

| Superfície | P0 | Casos negativos/irmãos |
|---|---|---|
| Provider FX BCB | IN | finais semana, boletim inesperado, 429, 5xx |
| Provider metal monthly WB | IN se rights | mês ausente, unidade alterada, layout diferente, revisões |
| Source metal diário LME | FORA até licença | sem scraping e sem síntese de valores diários |
| Storage PostgreSQL owner | IN | duplicate, concurrency, atomic rollback, upgrade |
| external-data-api S2S | IN | allowlist/audience, range inválido, ausência fonte |
| supplies-api BFF | IN | Core 503, deny, invalid FX, stale/partial |
| Portal MFE + Help | IN quando E11 gate | F5, mobile, theme, keyboard, empty, 403 |
| CNPJ/fornecedores existentes | REGRESSÃO OBRIGATÓRIA | não alterar contrato |
| Forecast/export/alertas | FORA | não apresentar botão inerte |

## 4. CRITÉRIOS DE SEQUÊNCIA, GATES E OUTCOME

~~~text
D0: HEAD/owners/contracts/source rights inventoried
 → D1 producer code + DB migration tests + real source evidence when permitted
 → D2 BFF S2S contract + Core auth + numerical/partial tests
 → E11 GATE-FEATURE closed/reconciled
 → D3 kit-first page + route + Help + UX tests
 → D4 authenticated federated smoke + data/method/source proof + rollback

SOURCE_RIGHTS=PASS
DATA_OWNER/MIGRATIONS=PASS
EXTERNAL_API_AND_JOB=PASS
BFF_CORE_AUTHZ=PASS
E11_PRIOR_PAGE_GATE=CLOSED
MFE_HELP_UX=PASS
INTEGRATION_RUNTIME_AUTH_SMOKE=PASS
→ PROC76 GATE-FEATURE=PASS

Qualquer condição ausente: FAIL/INCONCLUSIVE/TEST_NOT_RUN,
nunca PROMOTED/PASS inventado. Continuação automática das fatias
independentes desbloqueadas é permitida e desejada.
~~~

**Decisão GPT sobre relatório:** ACCEPT, ACCEPT_WITH_RESIDUAL, REWORK, EXECUTION_DRIFT ou INCONCLUSIVE com evidência e alcance explícitos. Não declarar produto concluído ao terminar só backend ou build da UI.

### Comandos de referência (ajustar ao package/venv real)

~~~bash
git fetch origin
git rev-parse HEAD
git rev-parse origin/main
git status --short

cd external-data-api
pytest -q tests/
cd ../supplies-api
pytest -q tests/
cd ../plugins/plugin-ui
npm run test -- --run
npm run build
cd ../supplies
npm run test
npm run build
npm run lint
~~~

Registrar contagens/exit code/ambiente; não disfarçar teste não executado. Teste PostgreSQL/migrations, browser e runtime exigem ambientes e autorizações reais. Documentar smoke quando aplicável e verificar resultado perceptível original.

## 5. BRIEF FINAL PARA DEVIN (COLAR NO AGENTE)

**TASK:** PROC-0076 — End-to-end Market Intelligence execution.
**GOAL:** Construir external-data-api (coleta + histórico PostgreSQL plugin), depois supplies-api (gateway S2S + BFF/AuthZ) e depois plugin-ui + página nativa /apps/supplies/market-intelligence com Help.
**RQ/AC:** RQ-76-01 a RQ-76-12 da seção 3; aceite é resultado observável, não teste unitário isolado.
**AUTHORITIES:** instruções oficiais, .cursor globais/especializadas, ADR-009/010 e contratos/código HEAD.
**OWNER:** external-data-api owns market data; supplies-api owns BFF/usuario; plugin-ui owns reusable design primitives; supplies MFE owns composition. Keycloak identity, Core effective grants.
**CURRENT_STATE:** external-data-api tem CNPJ via BrasilAPI stateless; supplies-api o consome via S2S; plugin-ui possui charts e wrappers; E11 gate anterior precisa revalidação.
**EVIDENCE_REQUIRED:** HEAD/status, source licence and semantics, migrations checksums, OpenAPI, HTTP tests, Core/S2S AuthZ, fixed-calculation fixtures, kit reuse, Help, runtime positive/sibling/negative, SHA/digest, rollback.
**ALLOWED_SCOPE:** menor diff correto em external-data-api, Postgres schema owner (após infra approval), supplies-api, plugin-ui quando generic gap comprovado, plugins/supplies, Help/docs/tests; seguir D0→D4.
**FORBIDDEN_SCOPE:** novo microserviço, scraping LME/Shockmetais não licenciado, inventar dados, direct MFE→external-data, cross-context DB, nova permission, TOTVS writes, deploy sem gates, alteração de feature alheia.
**CONTRACTS:** quatro rotas internas /v1/market-data/* e quatro BFF /market-intelligence/* do P0, sujeitas a freeze sem drift; preservação GET /v1/cnpj/{cnpj}.
**SECURITY:** Core effective supplies.access fail-closed, S2S Keycloak individual, secrets somente env segura, no raw payload logs.
**ACCEPTANCE:** dados e datas reais homologados, dashboard kit-first e fonte/metodologia, states completos, URLs/F5, build/test, smoke federado autenticado ou INCONCLUSIVE explícito.
**TESTS:** suite external-data, supplies-api, plugin-ui/supplies, PostgreSQL migration, contract, integration, negative, browser visual, CNPJ regression.
**STOP_CONDITION:** somente bloqueio material; continuar fatias independentes; não false PASS. Não pedir microdecisões.
**REPORT:** BASE HEAD; ORIGIN MAIN; FINAL HEAD; GIT STATUS; STATUS; FACTS PROVEN; TO_INVENTORY; EXECUTION_DRIFT; FILES INSPECTED/CHANGED; CONTRACT IMPACT; SECURITY CHECKS; SOURCE RIGHTS; RQ/AC COVERAGE; TESTS; RESIDUAL SEARCH; POSTCONDITION/OUTCOME; UNRESOLVED; NEXT STEP.

**Ordem inexorável:** READ → VERIFY → CLASSIFY → DECIDE → IMPLEMENT MINIMAL DIFF → TEST → VERIFY OUTCOME → RESIDUAL SEARCH → DOCUMENT → REPORT. Não parar a cada etapa técnica, não saltar um gate real.
