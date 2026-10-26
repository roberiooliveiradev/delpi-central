# PROC-0076.P0 — External Market Data: arquitetura, persistência e contratos candidatos

> **Estado: PROPOSED / DESIGN-ONLY / NOT IMPLEMENTED / NOT DEPLOY AUTHORIZATION**
> **Data editorial:** 2026-10-26
> **Base de inventário:** main 270054a84243c0ee1aa60f06d1857be86f9095f2. Revalidar HEAD/working tree antes da execução.
> **Demanda:** Transformômetro PROC-0076 (processo 8877c932-0f04-45ba-a24c-0265fdb4c186), instância d4762c9d-cfa3-4140-9f83-53114d96f4cb, GLPI #527.
> **Relacionados:** EXTERNAL-DATA-API-CONTRACT-FREEZE-X0.md, EXTERNAL-DATA-API-MVP-ARCHITECTURE.md, X3-RUNTIME-EVIDENCE-20261022.md, ADR-009, ADR-010, regras .cursor, documentação de Suprimentos.
> **Escopo:** PROPOSTA de expansão do contexto externo; não substitui o freeze X0 de CNPJ, nem prova licença de cotações ou implantação.

## 1. Decisão de arquitetura e evidências

O Product Owner solicitou reutilizar external-data-api para aquisição, normalização e histórico de cotações, armazenamento no PostgreSQL dos plugins e exposição pelo BFF supplies-api. A autorização aqui é de **documentação e planejamento**; as etapas de código/deploy continuam sob gates por owner e por página.

### PROVEN no HEAD examinado

- external-data-api é Flask, interna, sem rota pública no nginx, com GET /health e GET /v1/cnpj/{cnpj}, decorador S2S via delpi_auth, allowlist supplies-api, provider BrasilAPI, rate limiter consumer/cnpj/global e testes.
- external-data-api é **stateless hoje**; requirements/settings não incluem cliente PostgreSQL; X0 congelou CNPJ sem persistência. Portanto, persistência de séries históricas exige mudança explícita de contrato/infra e migration própria.
- supplies-api possui consumer HTTP+S2S ExternalDataApiCompanyRegistryProvider para CNPJ. Cabeçalhos: X-Delpi-Service-Authorization com client-credentials. Não enviar token de usuário.
- infra/docker-compose.yml tem postgres-plugins (Postgres 15, base PLUGINS_DB_NAME); supplies-api usa schema supplies em V001. Não usar schema/tabelas supplies como repositório de mercado.
- Portal usa o catálogo vigente supplies.access e supplies.manage (ADR-009); não criar permissions por mercado/rota.
- Transformômetro PROC-0076 registra instância em fase planejado, sem baseline/revisões/diagrama/evidência vinculada. GLPI #527 solicita dia/mês/ano, dólar/real convertido e médias mensais; menciona Shockmetais/LME e planilha X:\COMPRAS\Comodites cotações\LME\2026. Isso não comprova licença, endpoint ou fórmula.

### Gaps materiais e STOP

- SOURCE_RIGHTS: verificar fonte/credencial/contrato, direito de coleta automatizada, conservação histórica, derivados e apresentação interna. Shockmetais é referência informada, **não** endpoint de API homologado; não fazer scraping até aprovação formal.
- SERIES_SEMANTICS: bolsa/provedor, metal, código/série, praça, modalidade de preço (cash/contrato/prazo), unidade física, moeda de origem, fechamento/timezone, feriados, revisões e dia de observação.
- FX_SEMANTICS: fonte USD/BRL, taxa/horário de referência, PTAX vs comercial vs outro critério, pareamento por data, valores ausentes e fórmula oficial. Não converter automaticamente sem homologação.
- STORAGE_INFRA: confirmar conectividade/autorização do external-data-api ao postgres-plugins, role isolada, schema, migration runner, backup, retenção e políticas operacionais.
- QUEUE_GATE: README atual sinaliza E11 em foco com smoke autenticado pendente. Contratos externos podem evoluir em fatia backend separada somente após aprovação; **não** antecipar nova página MFE enquanto gate de página não for reconciliado.

## 2. CURRENT → TARGET

~~~text
CURRENT:
supplies MFE → supplies-api → external-data-api GET /v1/cnpj/{cnpj}
                                        → BrasilAPI
external-data-api: HTTP/S2S + limiter, sem PostgreSQL.

TARGET — somente após SOURCE_RIGHTS + P0 freeze + infra/migration:
provedor autorizado (metais + FX)
       ↓ coleta agendada, sem UI token
external-data-api (provider adapters + validação + harmonização)
       ↓ transaction / idempotent upsert
postgres-plugins / schema externo de owner exclusivo (CANDIDATO: external_data)
       ↑ consultas históricas bounded, read-only e S2S
external-data-api GET /v1/market-data/*
       ↑ client HTTP interno
supplies-api (Core effective AuthZ, composição e adaptação para dashboard)
       ↑ BFF REST
plugins/supplies / market-intelligence (UX pura)
~~~

Uma instalação física compartilhada de Postgres **não** implica compartilhamento lógico de tabelas. O schema external_data é nome CANDIDATO: decisão de infraestrutura/migration owner antes do primeiro CREATE SCHEMA. Não usar schema genérico de outro plugin nem acessar dados de outros contextos.

## 3. Ownership invariável

| Conceito | Owner | Nunca fazer |
|---|---|---|
| Provedores internet, extração, normalização, catalogação técnica, histórico de cotações, origem, status de coleta | external-data-api | Salvar em supplies ou colocar crawler no BFF |
| Disponibilidade da fonte/licença, semântica de mercado derivada e governança de retenção | Owner institucional a nomear + external-data-api executa contrato aprovado | Inferir que página pública concede licença |
| Experiência de Suprimentos, filtros UX, summary e comportamento 403/404 | supplies-api + MFE, respectivamente | MFE consultar API externa ou Postgres |
| Identity/SSO e service credentials | Keycloak | Credenciais no browser/Git/log |
| Effective permissions | Core API; supplies-api avalia fail-closed | JWT claim como autoridade final |
| SQL/ERP TOTVS | api-delpi | Copiar TOTVS ao external_data |
| Metadata do PROC-0076 e GLPI #527 | TÉO/Helpdesk | Tratar como schema de produto ou prova de runtime |

## 4. Persistência proposta, isolada do CNPJ

**Candidato:** schema external_data dentro de postgres-plugins, exclusivo do serviço externo. Se um contrato institucional já definir outro schema/role, STOP e reconciliar antes do commit. Não persistir histórico na tabela de fornecedores nem copiar dados de TOTVS.

| Tabela candidata | Chaves e campos de desenho | Invariantes |
|---|---|---|
| external_data.market_data_sources | source_id PK, provider_id, source_kind, attribution, license_reference, license_reviewed_at, allowed_use_scope, active, created_at | Nunca confundir cadastro local de fonte com licença efetivamente aprovada |
| external_data.metal_instruments | instrument_id PK, metal_code, instrument_code, market, quotation_basis, native_currency, unit_code, source_id FK, active | Mesmo metal com base/contrato/UM diferente é série diferente |
| external_data.metal_quote_observations | observation_id PK, instrument_id FK, observation_date, native_price NUMERIC, native_currency, unit_code, quote_basis, source_id, source_record_key (quando disponível), retrieved_at, revised_at, quality_status | Idempotência por identidade econômica+data+fonte; sem float para monetários; valor positivo ou condição explicitamente homologada |
| external_data.fx_rate_observations | fx_id PK, pair_code, rate_kind, reference_date, value NUMERIC, source_id, retrieved_at, revised_at, quality_status | PTAX, spot e outras referências não podem compartilhar chave sem rate_kind |
| external_data.market_data_ingestion_runs | run_id PK, provider_id, feed, started_at, finished_at, outcome, counts, safe_error_code, correlation_id, version | Sem raw payload protegido, tokens ou dados pessoais; trilha operacional sem falsa afirmação de cobertura |

*Campos e nomes são TARGET, não DDL aprovado.* A migration deve definir CHECK/UNIQUE/FK/índices reais após validar feed: índices candidatos por instrument_id+observation_date DESC e pair_code+rate_kind+reference_date DESC; transaction e upsert atômicos; backup e upgrade testados. Nenhuma migration existente pode ser reescrita. Documentar checksum e política de deploy.

**Médias mensais:** calcular sobre observações elegíveis, retornar count de observações válidas, range coberto e policy_version; não materializar tabela de médias sem evidência de performance. Média de valores USD convertidos por data pode diferir de média USD × média FX: regra fica em aberto até homologação, jamais inferida. Um mês com dias ausentes não é mês completo por default.

## 5. Ingestão de dados — desenho proposto

1. Scheduler/worker do serviço (ou job de infraestrutura explicitamente autorizado) dispara feed somente para fonte habilitada e licenciada; **sem endpoint anônimo POST refresh**.
2. Acquire lock/concurrency control para evitar corridas; aplicar limites por provedor/consumer e política do contrato externo.
3. Fetch com timeout finito, circuit/error handling, ETag/Last-Modified quando suportado. Respeitar 403, 429, Retry-After, robots/termos quando aplicáveis; nunca contornar bloqueios.
4. Validar JSON/HTML conforme adapter aprovado (preferência explícita por API/arquivo contratado). Preservar provenance mínima permitida, recusar unidade/moeda/data não reconhecidas.
5. Normalizar com precision decimal, validadores de instrumento, timezones, duplicatas, revisões e outliers marcados para revisão em vez de corrigidos silenciosamente.
6. Gravar observações idempotentes e registrar ingestion_run por transação coerente; erro parcial não marca o lote inteiro como sucesso.
7. Consultas REST retornam exclusivamente histórico persistido/validado, **sem chamar internet no request do usuário**. A UI explicita última atualização e stale/partial.
8. Desativar feed por config se licença expirar/for contestada; manter retenção/exibição coerente com direitos da fonte. Sem fallback silencioso para site alternativo.

## 6. Contratos EXTERNAL API candidatos — interna, S2S

Todos os paths abaixo são **PLANNED / NÃO EXISTEM**. Devem passar por contract freeze, OpenAPI versionado, operationIds estáveis, testes e compatibilidade de CNPJ antes da implementação.

| Method | Path (candidato) | operationId proposto | Função |
|---|---|---|---|
| GET | /v1/market-data/catalog | listMarketDataCatalogV1 | instrument_code/metal, nome, native_currency, unit, quote_basis, source_id, capability/coverage |
| GET | /v1/market-data/metals/observations | listMetalObservationsV1 | Datas/preços normalizados em moeda de origem; consulta histórica limitada |
| GET | /v1/market-data/fx/observations | listFxObservationsV1 | Séries FX persistidas por pair+rate_kind |
| GET | /v1/market-data/ingestion-status | getMarketDataIngestionStatusV1 | Estado técnico, última tentativa/sucesso e frescor por feed; S2S operator/consumer policy a congelar |

Parâmetros para metals/observations:
- instrument_code: obrigatório, código do catálogo; não aceitar símbolo arbitrário do cliente.
- date_from/date_to: datas ISO YYYY-MM-DD, obrigatórios; janela máxima candidata 366 dias por request; histórico longo paginado/chunk por ano.
- cursor (opcional) e limit (default alvo 100, max alvo 500) com ordenação por data e chave estável.
- quote_basis não é parâmetro livre caso faça parte da identidade do instrumento.
- source e unit: metadados retornados, não selecionáveis arbitrariamente sem correspondência contratual.

Parâmetros FX:
- pair=USD/BRL (único inicialmente), rate_kind do catálogo homologado, date_from/date_to/cursor/limit.
- Taxa histórica deve corresponder à data oficial de referência; lacunas retornam null/absence sem forward-fill implícito.

DTO EXTERNO — observação individual proposta:

~~~json
{
  "instrument_code": "METAL_CODE_AND_QUOTE_BASIS_APPROVED",
  "observation_date": "2026-10-23",
  "price": "1234.5678",
  "currency": "USD",
  "unit": "UNIT_FROM_SOURCE",
  "quote_basis": "BASIS_FROM_SOURCE",
  "quality": "validated",
  "source": {
    "source_id": "SOURCE_FROM_APPROVED_CATALOG",
    "provider_id": "PROVIDER_APPROVED",
    "retrieved_at": "2026-10-23T19:00:00Z",
    "reference_date": "2026-10-23",
    "license_reference": "NON_SECRET_REFERENCE",
    "schema_version": "v1"
  }
}
~~~

**O exemplo ilustra tipos, não cotações reais nem um feed já contratado.** Paginação global candidata: {items, page_info:{next_cursor,has_more}, meta:{as_of,data_status,source_ids,coverage}}. Para seriado vazio: items=[] e data_status=no_data, não números zero fictícios.

Status de erros candidato (verificar família padrão existente): 400 INVALID_QUERY, 401 unauthorized, 403 forbidden, 404 UNKNOWN_INSTRUMENT, 422 UNSUPPORTED_SERIES, 429 RATE_LIMITED + Retry-After, 502 UPSTREAM_INVALID_RESPONSE (ingestão), 503 PROVIDER_UNAVAILABLE / STORAGE_UNAVAILABLE / SOURCE_NOT_LICENSED, 504 UPSTREAM_TIMEOUT. **Nunca** devolver 403 interno S2S como 403 de negócio para o usuário final na supplies-api. GET históricos devem funcionar com upstream temporariamente fora, marcados stale, desde que licença permita distribuição do histórico.

Autenticação: X-Delpi-Service-Authorization (client-credentials), audience external-data-api e allowlist supplies-api; mesma proteção S2S individual do CNPJ, mas nenhuma ampliação automática de permission de todos consumidores. JWT de usuário nunca encaminhado. Erros e logs não revelam credencial/provider tokens/raw payload.

## 7. Contract readiness e segurança de fonte

| Gate | Critério | Estado 2026-10-26 |
|---|---|---|
| G-SOURCE-RIGHTS | Permissão documental explícita para coleta, histórico, derivação USD/BRL, apresentação interna e retenção | TO_INVENTORY / BLOQUEIA INGESTÃO |
| G-SERIES | Catálogo, UM, quote_basis, paridade de metal, timezone e FX definidos por responsável de negócio | TO_INVENTORY |
| G-DATA-OWNER | Novo schema/role/migrations aprovados, migração sob external-data-api, sem acesso cross-context | TARGET / TO_INVENTORY |
| G-EXTERNAL-CONTRACT | OpenAPI/DTO/erros/limites/versionamento congelados, CNPJ intacto | PLANNED |
| G-BFF-CONTRACT | Consumidor supplies-api e fórmulas homologadas, sem cálculo no MFE | PLANNED |
| G-TEST | Migrations vazio/upgrade, retries/quota, idempotência, duplicatas, fontes ruins, S2S+401/403, restore/cancel/stale | TEST_NOT_RUN |
| G-RUNTIME | Job e DB autorizados, deploy interno, amostra real rastreada, observabilidade, rollback | INCONCLUSIVE |

Dados históricos externos **não** são dados próprios TOTVS do Portal. A decisão nova evolui o limite stateless definido em X0; não apagar o histórico de freeze X0: produzir ADR/contract change aditivo na primeira etapa de execução.

## 8. Plano bounded por owner

- **PROC76.P0 (este documento):** inventário/contratos/wireframes. Sem código, tabela, job, scraping ou deploy.
- **PROC76.S1 — Fonte + regra + storage freeze:** responsável institucional aprova licença, instrumento, FX, médias, retenção e PostgreSQL role/schema; Cursor verifica migrações existentes/CI, constrói contrato OpenAPI final e ADR aditivo. STOP enquanto faltar fonte.
- **PROC76.S2 — external-data-api:** migration schema owner, persistence adapters, fonte licenciada, coleta agendada e endpoints read-only; testes positivos/sibling/negativos, upgrade, idempotência, quotas, rollover de dias e runtime interno. Sem tocar CNPJ funcional além de testes de regressão.
- **PROC76.S3 — supplies-api:** gateway HTTP S2S, serviço read-model, filtros/status, AuthZ efetiva Core, contratos BFF para dashboard, testes 200/empty/401/403/422/429/502/503/504 e dados stale.
- **PROC76.S4 — MFE:** somente após GATE da página em foco reconciliado e autorização explícita; rota proposta /apps/supplies/market-intelligence, gráficos/tabela/médias, filtro/URL, Help, responsividade, foco e tema.
- **PROC76.S5 — prova/aceite:** deploy sequencial, smokes internos e federados autenticados, paridade de 3+ datas com fonte legalmente utilizável, teste de média/FX e validação de Joici; evidência SHA/rollback. GATE-FEATURE não é PASS por build isolado.

### Matriz de rastreabilidade

| Requirement | Proof/AC | Etapa |
|---|---|---|
| RQ-76-01 consulta de metais | catálogo unit/basis/source consistente, um metal com data/valor rastreável | S1/S2 |
| RQ-76-02 histórico dia/mês/ano | janela, paginação, cobertura e ordem estáveis | S2/S3/S4 |
| RQ-76-03 USD/BRL | FX correto por data/tipo ou unavailable explícito | S1/S2/S3 |
| RQ-76-04 médias mensais | política homologada, contagem amostral e teste determinístico | S1/S2/S3 |
| RQ-76-05 rastreabilidade | fonte, UTC da coleta, referência e versão no DTO/UI | S2/S3/S4 |
| RQ-76-06 frescor e erros | stale/partial/no_data/downtime sem false success | S2/S3/S4 |
| RQ-76-07 UX completa | URL/F5, charts+table, Help, acessibilidade, mobile/tema, smoke | S4/S5 |
| RQ-76-08 segurança e CNPJ | Core permissions, S2S, nenhum MFE direto, regressão CNPJ | S2/S3/S5 |
| RQ-76-09 persistência própria | migration segura, isolation, backup, índices, unicidade | S1/S2/S5 |

## 9. Handoff / stop conditions

Cursor deve reportar BASE HEAD, FINAL HEAD, git status, facts PROVEN, TO_INVENTORY, EXPERIMENTS, EXECUTION_DRIFT, arquivos inspecionados/alterados, impacto contratual, testes, postconditions, residual search e NEXT BOUNDED STEP. Não inventar dado numérico de metal/câmbio para simular conexão com fonte real. Ausência de autorização de fonte/DB/schema ou quebra da fila E11 → **STOP-THE-LINE** no subgrafo impactado. Este documento é DRAFT de contrato, nunca evidência de funcionalidade implementada.

---

## Reconciliacao R1 — IMPLEMENTADO (2026-10-27, fix/proc-0076-r1)

Este documento era PROPOSED/DESIGN-ONLY. A implementacao existe em `main` (`e1c7974327` + fixes `660ddd3983`, `fecb855107`) e foi corrigida no rework R1 (`3b13494c69`, `ebe1f54ee4`, `4f81f9c233`, `313c5469da`). Divergencias/confirmacoes vs a proposta:

- **Schema:** `external_data` e **constante canonica fixa** em `Settings.EXTERNAL_DATA_SCHEMA` — nao configuravel por env (isolar por nome de schema quebraria o ledger `schema_migrations` vs DDL real). Isolamento de ambientes e por `PLUGINS_DB_*` (database/host).
- **Migrations:** V001 (schema+tabelas), V002 (catalogo licenciado: `bcb-ptax` ODbL-1.0, `world-bank-pink-sheet` CC BY 4.0, 6 metais), **V003** (proveniencia LME das series Pink Sheet + escopo `no_redistribution_pending_lme_review` — a CC BY 4.0 do WB nao cobre dados de terceiros; uso interno preservado, redistribuicao externa exige decisao formal). Checksum sha256 + imutabilidade + advisory lock multi-worker; falha de migration = **boot degradado** (CNPJ continua), nao derruba o processo.
- **Rotas implementadas:** `/v1/market-data/{catalog,metals/observations,fx/observations,ingestion-status}` — S2S obrigatorio, so historico persistido, janelas bounded (<=366d FX diario / <=3660d metais mensal), `limit`<=500.
- **Provedores:** PTAX BCB OData (`CotacaoDolarPeriodo`) + Pink Sheet XLSX (aba "Monthly Prices", 6 metais USD/mt). LME direto/Shockmetais fora do catalogo (sem licenca).
- **PTAX em producao:** HTTP 403 (WAF BCB no egress) — registrado como `EXTERNAL_DATA_PROVIDER_UNAVAILABLE` em `ingestion_runs`, sem dados ficticios; feed permanece OFF ate solucao operacional. Nao e bug de codigo.
- **Testes:** suite inclui PostgreSQL real em banco descartavel (`EXTERNAL_DATA_TEST_PG_*`) — antes TEST_NOT_RUN; cobre migrations, checksum, advisory lock, NUMERIC, unicidade/FK, idempotencia e boot degradado.
- **Residual:** `GATE-FEATURE` nao e escopo deste doc; ver IMPLEMENTATION-PLAN supplies. Feed flags OFF; E11 nao reconciliado.