# PROC-0076 — GPT Execution Brief e ledger de decisão

> **P0 DESIGN COMPLETE / IMPLEMENTATION NOT STARTED / TEST_NOT_RUN.**
> Data: 2026-10-26. Repositório roberiooliveiradev/delpi-central. Baseline inventariado main 270054a84243c0ee1aa60f06d1857be86f9095f2.
> Documentos irmãos:
> - [Arquitetura external-data-api, PostgreSQL e APIs internas](../shared-integrations/PROC-0076-EXTERNAL-MARKET-DATA-P0-ARCHITECTURE-AND-API-CONTRACTS-20261026.md)
> - [Contratos BFF, RQ/AC, wireframes desktop e mobile](./PROC-0076-MARKET-INTELLIGENCE-BFF-CONTRACTS-AND-WIREFRAMES-20261026.md)
> Contexto de produto: Transformômetro PROC-0076, GLPI #527.

## 1. DECISION LEDGER

| ID | Decisão | Estado |
|---|---|---|
| D01 | Reutilizar external-data-api (não criar serviço paralelo) | DECIDED_BY_PO + alinhado com HEAD |
| D02 | external-data-api é owner de ingestão, normalização e séries externas | TARGET; formalizar mudança do contrato stateless X0 |
| D03 | Usar postgres-plugins, **schema owner próprio** (nome external_data candidato), não supplies nem schema genérico | TARGET; role/migration e autorização infra pendentes |
| D04 | supplies-api expõe read-only dashboard via HTTP S2S, com Core AuthZ e sem acesso direto ao DB externo | TARGET |
| D05 | plugins/supplies mostra dashboard kit-first, sem cálculo de regra de mercado no client | TARGET |
| D06 | Metais e dólar conforme GLPI #527; nenhuma fonte confirmada ou scraping liberado | TO_INVENTORY / G-SOURCE-RIGHTS |
| D07 | FX, média e variação precisam de policy version e owner de negócio | TO_INVENTORY / G-SERIES |
| D08 | Não criar permission nova; vigente supplies.access e supplies.manage (ADR-009) | PROVEN |
| D09 | Sem page deploy enquanto E11 GATE-FEATURE inconclusivo, salvo rebaseline + autorização explícita | QUEUE BLOCK |
| D10 | CNPJ externo e enriquecimento de fornecedores precisam preservar contrato/testes | NON-REGRESSION |

### Observações de drift

README informa E11.S1–S9 executadas e GATE E11 INCONCLUSIVE; IMPLEMENTATION-PLAN ainda contém cabeçalho E10 em foco e recomenda não iniciar E11, embora o próprio corpo contenha atualização de E11. Registrar como **DOCUMENTATION_DRIFT / TO_RECONCILE**, não atualizar plano silenciosamente. ADR-009 e ADR-010 supersede/revisam trechos de RBAC/S2S nos documentos históricos. A external-data-api foi criada como **stateless** em X0/X1 e agora a intenção PO requer estado próprio de market data: isso é **CONTRACT_EVOLUTION_REQUIRED**, não autorização retroativa para desrespeitar X0.

## 2. BRIEF S1 — Source/storage/contract freeze (CURSOR, READ-FIRST)

**TASK:** PROC76.S1 — External market sources + stateful contract freeze.
**GOAL:** tornar implementável a coleta e histórico sem inventar licença/fórmula, compatível com CNPJ já funcional.
**AUTHORITIES:** instruções oficiais, regras globais .cursor; plan-construction, plan-execution, test-and-commit quando houver execução, platform-architecture-boundaries, platform-data-persistence, platform-api-contracts-integration, platform-security-identity-authorization, http-integration-resilience; X0/X3; ADR-009/010.
**OWNER:** external-data-api para provider/persistência; source rights owner institucional/PO jurídico; supplies-api consumidor.
**CURRENT_STATE:** external-data-api Flask+HTTP+Redis limiter+S2S, stateless, GET /v1/cnpj/{cnpj}; postgres-plugins presente; nenhum market endpoint.
**RQ/AC:** RQ-76-01..09 e AC-76-01..09 dos documentos irmãos.
**EVIDENCE_REQUIRED:** licença explícita coleta/armazenamento/derivados/exibição; fonte FX oficial/homologada; metal, instrumento, quote_basis, currency, UM, closing/ref date/timezone; política average e missing days; schema owner e grants/role/migration runner; bench caso real, datasource error cases; CNPJ consumer regression. Abrir arquivos canônicos no HEAD; search miss != ausência.
**ALLOWED_SCOPE:** P0/S1 investigação, documentação/ADR, OpenAPI candidate → freeze somente com dados suficientes, design de schema e plano de migration; não ativar ingestion ou criar tabela sem gate.
**FORBIDDEN_SCOPE:** scraping não autorizado, mudança da rota CNPJ, token nos logs, acesso cross-context PostgreSQL, bypass S2S, novas permissions, página MFE, deploy.
**CONTRACTS:** alinhar endpoints internos listados no documento external-market-data; versionamento/operationId/error envelope; quota; retention; rollback.
**SECURITY:** S2S Keycloak individual, allowlist, issuer/aud validado, Core AuthZ no BFF, nenhum token no MFE; sem exposure external-data-api no gateway.
**TESTS:** fixtures licenciadas/dummies sem aparente dado real; contrato, auth, rate, validation, idempotência, migration em vazio/upgrade, regressão CNPJ.
**STOP_CONDITION:** fonte/FX/licença/schema owner não aprovados → STOP do produtor; registrar unresolved claramente. Mudança de premissa canônica → EXECUTION_DRIFT.

## 3. BRIEF S2 — external-data-api producer

**TASK:** PROC76.S2 — Market data ingestion and read models.
**GOAL:** implementar somente bounded context externo aprovado por S1. Sem alterar o contrato CNPJ.
**OWNER:** external-data-api.
**AUTHORITIES:** as regras do S1, migrations-immutable-checksum, http-integration-resilience, observability, plan-execution + test-and-commit.
**CURRENT_STATE:** S1 contract freeze aprovado é pré-condição obrigatória.
**EVIDENCE_REQUIRED:** migration+schema próprio, alterações compose/env sem segredo, provider adapter sob licença, job executável com dedup/lock/timezone, read API contract OpenAPI, restore/rollback strategy, CNPJ regression, S2S 401/403, provider 429/timeout, status stale, logs sem dados protegidos.
**ALLOWED_SCOPE:** producer, testes e documentação, scripts de deploy controlados; sem BFF/MFE em mesma fatia.
**FORBIDDEN_SCOPE:** cross-service DB, upstream interativo por consulta do usuário, PUT ERP, gravar em supplies, scraping não homologado.
**SECURITY:** S2S individual, rate limiter, no anonymous market refresh, logs redacted.
**ACCEPTANCE/TESTS:** contract positive/sibling/negative, migration vazio/upgrade, uniqueness/decimal, calendar gap, rate kind, retries/timeout, same run twice, forced failure, CNPJ unaffected.
**STOP_CONDITION:** sem S1 aprovado ou infra/provisionamento → não executar migration nem job em produção.

## 4. BRIEF S3 — supplies-api consumer

**TASK:** PROC76.S3 — Market intelligence BFF composition.
**GOAL:** servir apenas os quatro recursos BFF do documento de wireframes; sem manipular DB external_data.
**OWNER:** supplies-api Flask.
**CURRENT_STATE:** producer S2 autenticado disponível e com contrato versionado; caso contrário PENDING.
**RQ/AC:** RQ-76-01..09, AC correspondentes.
**AUTHORITIES:** instructions, .cursor, ADR-009/010, API-ROUTES.md, external-market-data P0, MFE clients existentes.
**CONTRACTS:** /market-intelligence/filters, summary, series, monthly-averages como candidatos; confirmar OpenAPI final.
**SECURITY:** JWT só identidade, Core effective supplies.access, fail-closed; técnica S2S upstream, 403 de usuário só por AuthZ Core; sem nova permission ou branch artificial.
**ALLOWED_SCOPE:** gateway S2S, use cases aggregation, DTO, routes e teste.
**FORBIDDEN_SCOPE:** scraping/requests externa direta, banco de outro contexto, lógica domínio em view, nova migration supplies, UI.
**ACCEPTANCE:** reproducible series/averages/FX with policy_version; stale/partial/no_data; 401/403/422/429/502/503/504 mapped; robust limits; positive+sibling+negative.
**STOP_CONDITION:** não implementar antes de S2 contract READY e política FX homologada.

## 5. BRIEF S4 — MFE dashboard

**TASK:** PROC76.S4 — Uma página nativa em plugins/supplies.
**GOAL:** dashboard conforme wireframes sem integração externa direta.
**OWNER:** plugins/supplies.
**AUTHORITIES:** feature-help-sync, frontend/MFE rules, plugin-ui, ADR-009, README, BFF S3, manifest.
**CURRENT_STATE:** S3 pronto, gate E11 reconciliado, autorização de nova página registrada.
**ALLOWED_SCOPE:** feature market-intelligence, BFF clients, route/manifest somente após gate; Help e testes.
**FORBIDDEN_SCOPE:** nova permission, cálculo negócio do câmbio, estilo global fora .dashboard-supplies-portal, lib de gráfico se kit atende, MFE → external-data-api, outras páginas.
**SECURITY:** UI faz UX; supplies-api autoriza.
**ACCEPTANCE:** loading/empty/partial/error/403/404/stale, URL/F5, dark/light, desktop/mobile, teclado/foco, tabelas acessíveis, fonte e metodologia, tests/build/smoke federado.
**STOP_CONDITION:** página anterior GATE aberto ou BFF sem contrato e AuthZ; NÃO promover baseado apenas no roadmap.

## 6. BRIEF S5 — runtime/acceptance

**TASK:** PROC76.S5 — Deploy+GATE.
**GOAL:** comprovar ponta a ponta com fonte legalmente utilizada, dados históricos persistidos, médias e fx auditáveis.
**EVIDENCE_REQUIRED:** source SHA/digest, migration checksum/backup, real approved sample with time/price/unit/FX provenance, authorized/nonauthorized users, S2S, no direct API, mobile/light/dark, URL/F5, Help sync, rollback, CNPJ no-regression.
**OUTCOME:** PASS/FAIL/PENDING/INCONCLUSIVE/TEST_NOT_RUN por evidência; sem PASS inferido.
**STOP_CONDITION:** sem smoke autenticado ou licença → INCONCLUSIVE, não declarar fechamento.

## 7. Execution Report obrigatório por fatia

BASE HEAD; ORIGIN MAIN; FINAL HEAD; git status; status; FACTS PROVEN; TO_INVENTORY; EXECUTION_DRIFT; files inspected/changed; owner/contract impact; security checks; RQ/AC coverage; tests and TEST_NOT_RUN; postconditions/outcome; residual search; unresolved; next bounded step.

Este documento é handoff e planejamento. Não altera a fila E11, não implementa rotas nem dá autorização para deploy.

---

## Reconciliacao R1 — decisoes adicionais (2026-10-27, fix/proc-0076-r1)

- **D-R1-01 (freshness):** `data_status` separa (a) completude do periodo consultado de (b) atraso do feed vs cadencia de publicacao. `stale` = fonte atrasada; historico antigo completo = `ok`. Datas congeladas nos testes.
- **D-R1-02 (unidade):** valor convertido carrega unidade convertida (`BRL/metric ton`); origem preservada em `native`/`conversion`. Nunca misturar `ptax_closing_buy`/`sell` — `fx_kind` e explicito por request e auditavel.
- **D-R1-03 (schema):** `external_data` fixo (constante); migrations V001/V002 intocadas em producao; V003 aditiva para proveniencia LME.
- **D-R1-04 (licenca):** CC BY 4.0 WB nao cobre series de terceiros (LME subjacente). Escopo da fonte registra `no_redistribution_pending_lme_review`; exibicao interna com atribuicao mantida, redistribuicao pendente de decisao formal.
- **D-R1-05 (PTAX):** 403 WAF no egress de prod e impedimento operacional, nao bug; feed OFF, ingestao registra falha verificavel. Nenhuma tentativa de bypass autorizada.
- **D-R1-06 (navegacao):** pagina deep-linkavel fora do hub/palette ate E11 reconciliado — mantido.

## Reconciliacao R1.1 — decisoes adicionais (2026-10-27, fix/proc-0076-r1)

- **D-R1.1-01 (seguranca de testes PG):** `tests/pg_disposable_guard.py` — guarda fail-closed centralizada exigida antes de qualquer SQL mutante em teste: flag explicita + host loopback/allow-remote + dbname com `test` + prova no engine (sentinela ou schema vazio). Sem prova de isolamento, nenhuma migration/DROP roda.
- **D-R1.1-02 (completude x frescor):** `data_status` = qualidade da consulta apenas (`ok|partial|no_data`); atraso do feed vive exclusivamente em `meta.freshness.status`. Ausencia total de PTAX com metal disponivel = `partial`+`fx_missing`, nunca `no_data`. Semantica identica nos 3 endpoints; MFE deriva banner de `freshness.status==="delayed"`.
- **D-R1.1-03 (direitos LME):** evidencia oficial (WB datasets ToU + LME licensing) mostra que `internal_display` tambem nao e uso comprovado — V004 aditiva refina escopo para `internal_display_pending_lme_review`. `SOURCE_RIGHTS=INCONCLUSIVE`; decisao institucional pendente; feed permanece OFF; historico preservado.
- **D-R1.1-04 (gates mantidos):** E11/GATE-FEATURE INCONCLUSIVE; PTAX 403 operacional sem bypass; feeds OFF; V003/V004 so aplicam em prod no proximo deploy autorizado; sem smoke federado nesta execucao.

## Reconciliacao R1.2 — seguranca, quarentena e governanca (2026-10-27, fix/proc-0076-r1)

- **D-R1.2-00 (reconciliacao do merge antecipado):** o PR #112 foi mesclado ao `main` em `17e13ce99ce29fbd3eef22b1a2cb10db13df647b` (pais `c7a4b155d0` + `2937147b67`) **antes** do aceite da R1.1. Portanto `main` contem a implementacao R1 + o estado previo da guarda (auto-claim) e do `data_status`; R1.1 (`6160df1e7f`, `631b501130`, `ae38870fda`) e R1.2 existem **somente** na branch `fix/proc-0076-r1` → PR #113. O merge nao representa aceite de runtime, deploy (nenhum), migrations em prod (V003/V004 nao aplicadas), licenciamento (LME INCONCLUSIVE) nem fechamento do GATE-FEATURE (E11 aberto).
- **D-R1.2-01 (guarda PG — prova independente):** a sentinela deixou de ser auto-criada pela guarda. `tests/provision_pg_test_db.py` (provisionador, fora da guarda) cria o banco dedicado `external_data_test_<rand>` e grava `provisioned_by='pg_provision'` + `token` aleatorio + `dbname` em `public.delpi_disposable_db_guard`; a guarda **somente verifica**: flag `DISPOSABLE` + host + dbname + `EXTERNAL_DATA_TEST_PG_TOKEN` casa com a linha do provisionador no banco conectado. Flag sozinha, nome `*_test`, schema vazio e sentinela pre-existente/estrangeira sao bloqueados antes de SQL mutante.
- **D-R1.2-02 (politica de uso por operacao):** `app/domain/usage_policy.py` — concessao exige valor exato no `allowed_use_scope`; `*_pending_*`, `unknown`, ausencia ou fonte inativa = negado. Operacoes: `collect`, `store`, `derive`, `internal_display`, `redistribute`. `redistribute` nao tem nenhum consumidor interno — qualquer uso externo e rejeitado por default.
- **D-R1.2-03 (quarentena de leitura no owner):** queries de catalogo/observacoes verificam `internal_display` no produtor e lancam `UseNotApprovedError` → HTTP 403 `EXTERNAL_DATA_USE_NOT_APPROVED`. Catalogo expoe `display_allowed` por fonte sem vazar preco. Consulta direta por `instrument_code`/periodo nao contorna — a verificacao e por fonte, antes de qualquer leitura. Historico permanece fisicamente preservado.
- **D-R1.2-04 (ingestao fail-closed):** `collect`+`store` devem estar concedidos explicitamente; feed habilitado por env nao basta. Fonte inativa/ausente/sem grants → `EXTERNAL_DATA_SOURCE_NOT_LICENSED` antes de qualquer fetch/upsert.
- **D-R1.2-05 (contrato BFF):** `EXTERNAL_DATA_USE_NOT_APPROVED` → **503 `source_use_not_approved`** (erro dedicado, nunca 403 de autorizacao de usuario). `/filters` propaga `selectable:false` (derivado de `display_allowed` do produtor); o MFE filtra opcoes nao-selecionaveis, nao envia queries para elas e exibe estado neutro sem dados antigos/inventados. Help/manual/glossario sincronizados.
- **D-R1.2-06 (gates mantidos):** identicos a D-R1.1-04 — feeds OFF, sem deploy, sem migrations prod, E11/GATE/LME INCONCLUSIVE, sem bypass WAF.

## Reconciliacao R1.3 — readiness do contrato de direitos + default-deny (2026-10-27, fix/proc-0076-r1)

- **D-R1.3-01 (vulnerabilidade fechada):** a quarentena dependia da V004 aplicada, mas o boot degradado (necessario para manter o CNPJ) permitia servir mercado sobre catalogo V002/V003 com `internal_display` legado. `app/infrastructure/persistence/market_contract_readiness.py` prova por invocacao: ledger legivel + revisao **V004** presente + checksum igual ao arquivo canonico + tabela/coluna do catalogo presentes. Falha = `EXTERNAL_DATA_CONTRACT_NOT_READY` (503) antes de qualquer leitura — sem cache, nunca retem autorizacao.
- **D-R1.3-02 (cobertura dos read paths):** `check_market_contract_ready` chamado em `get_catalog`, `list_metal_observations`, `list_fx_observations`, `get_ingestion_status` e no job `ingest_market_data` antes de qualquer escrita. Sem bypass por `instrument_code`, periodo ou paginacao; falha nunca vira lista vazia nem `data_status=ok`.
- **D-R1.3-03 (default-deny nos consumidores):** BFF `selectable = display_allowed is True` (ausente/null/invalido = nao-selecionavel; `default_instrument` nunca aponta bloqueado); MFE `selectable === true` apenas; catalogo sem selecionaveis exibe estado neutro de indisponibilidade, nunca empty-state enganoso nem dados antigos.
- **D-R1.3-04 (contrato BFF):** `EXTERNAL_DATA_CONTRACT_NOT_READY` → **503 `contract_not_ready`** — indisponibilidade tecnica distinta de `source_use_not_approved` (decisao de licenca em contrato pronto) e de 401/403 de usuario (Core `supplies.access`).
- **D-R1.3-05 (cenarios comprovados em PG real):** V001–V003 → deny em todas as rotas; V004 aplicada → ready, metais LME negados, FX liberado; checksum adulterado → deny; engine ilegivel → deny. Prova em banco descartavel provisionado (guarda R1.2).
- **D-R1.3-06 (gates mantidos):** identicos a D-R1.2-06.