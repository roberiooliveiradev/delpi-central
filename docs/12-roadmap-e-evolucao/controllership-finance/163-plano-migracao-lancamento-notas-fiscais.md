# 163 — PLANO: Migração do módulo Lançamento de Notas Fiscais (api-delpi → controllership-finance-api)

> Status: **F4 em andamento — HML parity + checagens PROD; runbook 164 DRAFT**
> Baseline F2b: HEAD `857b17ce03550eb6add765ad8176609c5a9de838` (`feat/lnf-migration-f2` / origem F3)
> F3 dark: `155e0cc4de`; F3-R: `287a534220`; resíduos F4 passo 0: `4bd9307b0e`
> Governança de git: **trabalho direto na `main`, sem branches** (decisão do owner — 2026-11-12)
> Natureza: **transferência de owner de runtime sem mudança de comportamento** (contrato, permissões e dados preservados)

---

## 1. Objetivo

Mover o módulo `lancamento_notas_fiscais` da `api-delpi` para a `controllership-finance-api` (BFF do Portal Controladoria & Finanças) e trocar a base URL do MFE `lancamento-notas-fiscais`, preservando integralmente:

- as **24 rotas** (path relativo, query, body, envelope, `error.code`, status HTTP, binários PDF/XML sem envelope);
- as **8 permissions** `lancamento-notas-fiscais.*` e a regra de filial atual;
- os **dados de produção** (schema `lancamento_notas_fiscais`) e os binários (volume `lancamento-notas-fiscais-danfe`);
- as **notificações** (`sourceApp=lancamento-notas-fiscais`, categorias `lancamento_notas_fiscais` e `lancamento_notas_fiscais_unmapped_products`);
- a conciliação sob demanda (`refresh` com cooldown 45 s; `run` com `manage`).

Fora de escopo: features novas, redesenho do MFE, correção de comportamento (gaps viram follow-up), CLARA (plano próprio após o corte).

## 2. Baseline AS-IS (F0 — PROVEN salvo indicação)

| Item | Valor | Evidência |
|---|---|---|
| Router | prefixo `/lancamento-notas-fiscais`, 24 rotas | `lancamento_notas_fiscais_router.py:82-85`, `:262-1236`; `main.py:395` |
| Gateway | `/apps/api-delpi/` → api-delpi | `gateway/nginx.conf:917-920` |
| Envelope sucesso | `api_delpi_success`: `success, message, data, error, meta{dataVersion=2026-07, operationId, entity, shape, pagination}` | `route_response_helpers.py:13-48`, `response_meta_builder.py:7-27`, `route_contract_registry.py:1341-1412` |
| Negação AuthZ | `{detail: Forbidden|Unauthorized|Authorization service unavailable}` (fora do envelope) | `fastapi_auth.py:170-181` |
| AuthZ | `require_permission`/`require_any_permission` com effective permissions do Core `/me`; filial por `branch_access_error` | router + `lancamento_notas_fiscais_branch_access.py:22-60` |
| Conjuntos | READ = access, create, view, view.filial-01/02, process, manage; `review-unmapped-products` à parte | `api_delpi_permissions.py:97-106`, `:638-662` |
| Filial não aplicada | suppliers, received-invoices/*, unmapped-products, reconciliation/run, reconciliation/refresh | tabela F0 |
| Service token | token interno de serviço entra como superadmin | `fastapi_auth.py:208-223` |
| Persistência | schema `lancamento_notas_fiscais` em `postgres-plugins`, V001–V014, runner `api-delpi/scripts/run_plugins_migrations.py` | `api-delpi/migrations/plugins/lancamento-notas-fiscais/` |
| Binários | `LNF_DANFE_UPLOAD_DIR` → `${DELPI_DATA_HOST_DIR}/lancamento-notas-fiscais-danfe` | `infra/docker-compose.yml:1590`, `:1652` |
| Protheus (do módulo) | SF1+SA1+SA2 (`totvs_invoice_posting_sf1_sql.py`), SA5+SB1 (`supplier_product_mapping_sql.py`) | F0 |
| Protheus (canônico compartilhado) | SA2 `TotvsSupplierRepository`; SC7 `open_purchase_orders_sql` (`safety_stock_sql.py:392`) | F0 |
| Documentos recebidos | `financial-api` `/invoices/received…` com `API_DELPI_INTERNAL_SERVICE_TOKEN` | `financial_received_invoice_gateway.py:43-70` |
| Jobs | nenhum; conciliação HTTP sob demanda | F0 |
| Notificações | POST `{CORE_API_BASE_URL}/integrations/notifications` | `lnf_portal_notification_service.py:20-50`, `:305-318` |
| MFE | ponto único `API_BASE` em `invoicePostingApi.ts:20`; `/core-api/me` fica | F0 |
| Permissions no Core de **produção** | presentes (usuário real recebeu as 8 no catálogo efetivo da CLARA em 2026-11-12) | OBSERVED (prod) |
| Dados em produção | existem (fila filial 01 com solicitações reais em 2026-11-12) | OBSERVED (prod); contagens exatas TO_INVENTORY |

## 3. Decisões

| # | Tema | Decisão | Origem |
|---|---|---|---|
| D1 | Permissions | BFF autoriza pelas `lancamento-notas-fiscais.*` (via Core `/me`). **Não** exige `controllership-finance.access`. ADR registra a exceção: módulo hospedado preserva app/permissions de origem. | Usuário |
| D2 | Banco | **Transferência de posse do schema**, sem mover dados. BFF passa a ser a única dona de `lancamento_notas_fiscais` (conexão + runner com V001–V014 como baseline byte a byte). api-delpi deixa de conectar/migrar no mesmo deploy. | Usuário |
| D3 | Protheus | **SQL vai junto para a BFF** (SF1, SA5/SB1 e cópia das consultas SA2/SC7 usadas pelo módulo). Desvio consciente da regra "api-delpi = SQL TOTVS", registrado no ADR com residual de duplicação SC7/SA2. | Usuário (contra recomendação) |
| D4 | Rotas antigas | **Corte direto**: no deploy do corte, rotas saem da api-delpi, MFE troca a base, catálogos do chat e da TV são regenerados. | Usuário |
| D5 | Envelope | Responder **local ao módulo** na BFF reproduzindo exatamente o envelope da api-delpi (`dataVersion`, `entity`, `shape`, `error.code`) e a negação `{detail}`. Envelope global da BFF não muda. | Authority (contrato 1:1) |
| D6 | Financial-api | BFF chama a financial-api diretamente com credencial de serviço própria (mesmo contrato `/invoices/received…`). | Authority (owner do dado) |
| D7 | Filial | Preservar exatamente a regra atual, inclusive rotas sem filtro de filial. Gaps viram follow-up. | Authority (sem mudança de comportamento) |
| D8 | Service token superadmin | **Não** portar o bypass, salvo se F1 provar consumer de serviço em runtime. | Recomendação — confirmar em F1 |

## 4. Invariantes

1. Contrato 1:1 nas 24 rotas — garantido por suíte de contrato rodando **antes** contra a api-delpi e **depois** contra a BFF.
2. Mesmos usuários com o mesmo acesso, por rota e por filial.
3. **Zero alteração de schema durante a migração**: V001–V014 copiadas byte a byte; nenhuma V015 até o corte estabilizar. Isso garante rollback por redeploy.
4. Um único escritor do schema em qualquer momento (sem dual-write).
5. Notificações com o mesmo `sourceApp`/categorias, sem duplicidade.
6. Nada em produção antes do gate de corte.

## 5. Fases

| Fase | Entrega | Gate |
|---|---|---|
| **F0** Inventário | relatório + este plano | ACCEPT_WITH_RESIDUAL (feito) |
| **F1** Docs + residual | plano v2 no repo, ADR, respostas F1-R1…R7 | ACCEPT |
| **F2** Contrato congelado | suíte de contrato + matriz AuthZ (24 rotas × permissions × filial) rodando contra a api-delpi; golden samples sucesso/erro/PDF/XML | baseline PASS |
| **F3** Implementação BFF (dark) | bounded context `invoice_posting` na BFF (domain/application/infrastructure/interface), responder local, helper AuthZ LNF, runner do schema com baseline, adapters Protheus/financial-api/Core notifications, mount do volume, envs | suíte F2 PASS contra a BFF; testes unit/adapters; rotas não expostas no gateway |
| **F4** Paridade em homologação | mesmo dataset, mesma suíte nas duas bases; diff de respostas | diff = 0 (exceto voláteis documentados) |
| **F5** Corte (deploy único) | gateway, BFF dona do schema, api-delpi sem módulo, MFE `API_BASE`, catálogos chat/TV regenerados, envs | smoke federado filial-01/02 por perfil PASS; notificações PASS; contagem por status igual antes/depois |
| **F6** Limpeza | remoção do código morto na api-delpi, docs atualizados | residual search limpo |
| **F7** CLARA | plano próprio | — |

## 6. DoD do corte

- 24/24 rotas com paridade; PDFs/XML idênticos (hash).
- Matriz AuthZ igual ao AS-IS (positivo, negativo, filial irmã), incluindo `view.filial-01` sem acesso à 02 e `BRANCH_REQUIRED` quando aplicável.
- Duplicidade continua 409 `invoice_posting_request.duplicate` com `existing_request_id`.
- `refresh` com cooldown 45 s e `invoice_posting_reconciliation.busy` preservados.
- Notificações de bloqueio, resolução, menção e produtos sem código chegando uma vez.
- Contagem por status e por tabela igual antes/depois.

## 7. Rollback

Até F6: redeploy da versão anterior (api-delpi com módulo + MFE com base antiga + gateway antigo). Como o schema não muda e é o mesmo banco, os dados gravados pela BFF ficam válidos para a api-delpi.

## 8. Riscos

| Risco | Mitigação |
|---|---|
| BFF sem acesso ao `postgres-plugins` ou ao Protheus | F1-R1/R2 antes de F3 |
| Ledger de migrations diferente entre runners → checksum | F1-R3; baseline sem reexecução |
| Consumer não mapeado quebra no corte direto | F1-R4 (chat/TV runtime e principal) + logs de acesso das rotas por 7 dias antes de F5 |
| Duplicação de SQL SC7/SA2 | residual registrado no ADR; teste de paridade com a função canônica |
| Envelope divergente | responder local + suíte F2 |
| Notificação duplicada no corte | produtor antigo removido no mesmo deploy |

## 9. Resultado F1 e decisões complementares

### Resultado F1 (HEAD 631a3273d6317ba62b315ef0ab1a52bcf89e88a2) e decisões complementares — 2026-11-12

**Revisão:** F1 ACCEPT_WITH_RESIDUAL. ADR-001 ACCEPTED pelo owner. F2 autorizado (somente testes). Runtime NÃO autorizado.

| Item | Achado F1 (PROVEN) | Decisão / regra |
|---|---|---|
| R1 Banco | BFF já conecta no mesmo `postgres-plugins/plugins_hub` (`infra/docker-compose.yml:2966-2974`, `:2996`). Dev não declara `PLUGINS_DB_*` nem `depends_on` (`docker-compose.dev.yml:3199-3200`, `:3248-3252`). | D2 mantida sem nova rede/credencial. Ajuste do compose dev entra em F3. |
| R2 Protheus | BFF sem pyodbc/ODBC/`TOTVS_DB_*`; api-delpi usa `msodbcsql18`, pool e `READ UNCOMMITTED` (`connection_pool.py:21-65`). | D3 mantida: F3 replica driver, envs, pool e isolamento na BFF. |
| R3 Ledger | Runner de plugins grava `"{schema}".schema_migrations` (`version VARCHAR 'V001'`, `id UUID`); runner da BFF grava `controllership_finance.schema_migrations` (`version INT`), versões 1–14 já ocupadas pelo fechamento. Mesmo SHA-256. | **Regra R3:** BFF ganha runner dedicado ao schema `lancamento_notas_fiscais`, lendo o ledger existente no formato atual. V001–V014 byte a byte, sem reexecução. Até o corte o runner é **verify-only** (não aplica). No corte a api-delpi deixa de migrar esse schema. Proibido colocar os arquivos LNF na sequência do fechamento. |
| R6 Erros | api-delpi: `error{code, recoverable}`, 422 "Parâmetros inválidos"/`VALIDATION_ERROR`, 500 de rota `INTERNAL_ERROR`, `HTTPException` 500 → `HTTP_ERROR`, exceção não tratada → `{detail:"Internal Server Error"}`, AuthZ `{detail}`. BFF `fail()` sem `error.code`. | **D5 reforçada:** tratamento de erro próprio das rotas LNF (por prefixo de path), reproduzindo todos esses formatos. Handlers globais da BFF não se aplicam ao módulo. |
| R7 Financial-api | Só aceita `API_DELPI_INTERNAL_SERVICE_TOKEN` em `/invoices/received`, principal `internal_invoice_reader` (`auth_middleware.py:20`, `:40-63`). | **D6 corrigida:** a BFF reutiliza o mesmo token, mesmo header `X-Delpi-Service-Token` e mesmo principal restrito. Não existe "credencial própria". |
| R5 Service token | Nenhum caller dedicado. O middleware compartilhado da BFF também promove o token a superadmin (`auth_middleware.py:90`). | **D8 mantida com trava explícita:** rotas LNF na BFF exigem `principal_type == "user"`; token de serviço é recusado. Diferença registrada como KNOWN_DIVERGENCE_D8 na suíte de contrato. |
| R4 Chat/TV | Catálogos `tv_data_routes.json` e contratos do chat são gerados do OpenAPI da api-delpi; TV chama GET via service token; vínculo de painel e authMode do provider do chat estão só em runtime. | **D9 (nova):** com o corte direto, chat e TV perdem as operações LNF na regeneração. Antes do corte (F4), verificar em produção painéis da TV com operationIds LNF e o provider do chat. Uso zero → aceita a perda. Uso > 0 → DECISION_REQUIRED ao owner. |
| R8 Testes | Todos os testes LNF importam `app.*` da api-delpi. | F2 cria suíte **caixa-preta HTTP** parametrizada por URL base; os testes unitários existentes migram com o código em F3. |
| Docs | README do portal (`README.md:89`) ainda diz "só access/manage", runtime já tem `controllership-finance.access.dre`. | Follow-up documental fora deste plano. |
