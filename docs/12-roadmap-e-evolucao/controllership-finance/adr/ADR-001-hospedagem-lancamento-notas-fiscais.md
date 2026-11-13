# ADR-001 — Hospedagem do módulo Lançamento de Notas Fiscais na controllership-finance-api

| Campo | Valor |
|-------|--------|
| Status | **ACCEPTED** (2026-11-12, decisor: owner do produto) |
| Data | 2026-11-12 |
| Contexto | Portal Controladoria & Finanças — hospedagem do módulo `lancamento_notas_fiscais` |
| Relacionados | [Doc 163 v2](../163-plano-migracao-lancamento-notas-fiscais.md) |
| Implementação | `IMPLEMENTATION_AUTHORIZED=NO` |

Não havia série de ADR neste produto. Este arquivo abre a série em `docs/12-roadmap-e-evolucao/controllership-finance/adr/`.

---

## Contexto

O inventário F0 da migração do módulo Lançamento de Notas Fiscais (`api-delpi` → `controllership-finance-api`) foi aceito com residual (`ACCEPT_WITH_RESIDUAL`). A baseline desse inventário é o HEAD `1bee257518d092925525ce54f67bc9c5ece6094a` (`main`). A revisão F1, somente documentação, fechou no HEAD `631a3273d6317ba62b315ef0ab1a52bcf89e88a2` (`main`). Entre esses dois SHAs não há diff no módulo, nas migrations do plugin, na BFF, no gateway nem no MFE `lancamento-notas-fiscais`.

O módulo hoje expõe 24 rotas em `/lancamento-notas-fiscais`, autoriza oito permissions `lancamento-notas-fiscais.*`, persiste o schema `lancamento_notas_fiscais` no `postgres-plugins` e consulta o Protheus e a `financial-api`. O plano v2 trava a transferência de owner de runtime sem mudança de comportamento. As decisões abaixo são as do doc 163.

## Decisão

| # | Decisão | Origem |
|---|---|---|
| D1 | A BFF autoriza pelas permissions `lancamento-notas-fiscais.*` lidas no Core `/me`. Não exige `controllership-finance.access`. O módulo hospedado preserva o app e as permissions de origem. | Usuário, 2026-11-12 |
| D2 | Transferência de posse do schema `lancamento_notas_fiscais`, sem mover dados. A BFF passa a ser a única dona (conexão e runner, com V001–V014 como baseline byte a byte). A api-delpi deixa de conectar e de migrar esse schema no mesmo deploy. | Usuário, 2026-11-12 |
| D3 | O SQL Protheus usado pelo módulo vai junto para a BFF (SF1, SA5/SB1 e cópia das consultas SA2/SC7). | Usuário, 2026-11-12, contra a recomendação de manter o SQL na api-delpi |
| D4 | Corte direto. No deploy do corte as rotas saem da api-delpi, o MFE troca a base, e os catálogos do chat e da TV são regenerados. Sem janela em que as duas bases respondam. | Usuário, 2026-11-12 |
| D5 | O responder local do módulo na BFF reproduz o envelope da api-delpi (`dataVersion`, `entity`, `shape`, `error.code`) e a negação `{detail}`. O envelope global da BFF não muda. | Authority do contrato 1:1 |
| D6 | A BFF chama a `financial-api` diretamente no contrato `/invoices/received…`, com credencial de serviço própria. | Authority do owner do dado |
| D7 | A regra de filial atual permanece, inclusive nas rotas que hoje não filtram filial. Gap de filial vira follow-up. | Authority de não mudar comportamento |
| D8 | O bypass de service token como superadmin não é portado, salvo se o residual F1 provar um consumer de serviço em runtime. | Recomendação do plano v2, a confirmar em F1 |

F1 não provou um consumer dedicado das rotas LNF com token de serviço. D8 permanece como escrita no plano. O residual dessa confirmação está nas consequências e no desvio (a) operacional do middleware herdado.

## Desvios conscientes

### (a) Permissions de outro app autorizadas na BFF

O freeze documental do portal diz que as permissions são somente `controllership-finance.access` e `controllership-finance.manage` (`README.md:89`). D1 abre uma exceção, válida apenas para o módulo hospedado: a BFF aceita `lancamento-notas-fiscais.*` sem exigir `controllership-finance.access`.

O mesmo README já está em drift com o runtime. A BFF já reconhece `controllership-finance.access.dre` (`controllership_finance_app/interface/http/authz.py:23-26`). Corrigir esse texto do README é follow-up separado e não faz parte desta hospedagem.

### (b) SQL Protheus dentro da BFF

A fronteira vigente atribui SQL TOTVS à api-delpi. D3 coloca na BFF o SQL do módulo (SF1+SA1+SA2 e SA5+SB1) e uma cópia das consultas compartilhadas que ele usa: SA2 em `TotvsSupplierRepository` e SC7 em `open_purchase_orders_sql` (`safety_stock_sql.py:392`). A duplicação SC7/SA2 permanece como residual; a paridade com a função canônica é teste de F3/F4, não uma terceira cópia.

### (c) Corte direto, sem janela de compatibilidade

D4 não mantém as rotas antigas em paralelo. O rollback até a limpeza (F6) é redeploy da versão anterior, no mesmo schema e sem alteração de DDL.

## Consequências

- A suíte de contrato precisa passar na api-delpi antes do corte e na BFF depois, nas 24 rotas, inclusive PDF/XML sem envelope.
- V001–V014 permanecem byte a byte. Nenhuma V015 entra antes de o corte estabilizar.
- O runner atual da BFF grava versões inteiras em `controllership_finance.schema_migrations` (`migrations_runner.py:57-62`). O ledger do módulo é `lancamento_notas_fiscais.schema_migrations`, com versão `VARCHAR` no formato `V001` (`run_plugins_migrations.py:92-98`). O algoritmo de checksum é o mesmo (SHA-256 dos bytes), o ledger não é. Assumir V001–V014 exige um runner do schema do módulo que só confere o ledger existente e não reexecuta SQL, fora da sequência inteira do fechamento.
- A BFF já conecta no mesmo `postgres-plugins` / `plugins_hub` das demais APIs de plugin (`docker-compose.yml:2966-2974` e `2996`). Não há instância nova. O que falta para o schema do módulo é o runner próprio, não uma rede ou um usuário novos.
- A BFF não tem driver ODBC nem variáveis `TOTVS_DB_*`. D3 exige replicar o pool da api-delpi (`connection_pool.py:32-65`).
- A `financial-api` só aceita `API_DELPI_INTERNAL_SERVICE_TOKEN` em `/invoices/received` (`auth_middleware.py:20`, `:56-63`). Não há segunda credencial. A “credencial própria” de D6 ainda não existe nesse serviço; F3 precisa reutilizar o token compartilhado ou estender a financial-api. Isso fica fora de F1.
- D8 não fica de graça. Fora do MCP, a BFF já delega ao `jwt_middleware` compartilhado (`auth_middleware.py:90`), e esse middleware promove o token interno a superadmin (`fastapi_auth.py:208-217`). O compose da BFF carrega `env_file: .env` (`docker-compose.yml:2926-2927`), e o exemplo de produção declara `API_DELPI_INTERNAL_SERVICE_TOKEN`. Cumprir D8 exige um portão explícito nas rotas hospedadas. F1 não achou caller dedicado do módulo; achou o caminho genérico da TV, que anexa o mesmo header em todo GET (`shared/delpi_api_client/client.py:51`). Painel publicado usando operationId LNF não está no Git (`TO_INVENTORY`).
- Nada desta ADR autoriza implementação, migration, compose, nginx, manifesto ou permission.

## Alternativas rejeitadas

| Alternativa | Motivo |
|---|---|
| Exigir `controllership-finance.access` além das permissions de origem | O usuário decidiu D1: o módulo hospedado preserva o app de origem |
| Manter o SQL Protheus só na api-delpi e a BFF chamar por HTTP | O usuário decidiu D3 contra essa recomendação |
| Janela com as rotas antigas e as novas no ar | O usuário decidiu D4, corte direto |
| Copiar V001–V014 para a pasta de migrations do fechamento | As versões inteiras 1–14 já são o fechamento; o checksum abortaria ou o DDL correria no ledger errado |
| Mover os dados para outro schema ou outra instância | D2 é posse do schema, sem mover dados |

## Referências

- Plano: [163-plano-migracao-lancamento-notas-fiscais.md](../163-plano-migracao-lancamento-notas-fiscais.md)
- Freeze de permissions (texto a corrigir à parte): `README.md` deste produto, linha das permissions `access` e `manage`
- Runner atual da BFF: `controllership-finance-api/controllership_finance_app/infrastructure/persistence/migrations_runner.py`
- Runner do schema de plugins: `api-delpi/scripts/run_plugins_migrations.py`
- Middleware compartilhado: `shared/delpi_auth/middleware/fastapi_auth.py`

## Adendo F1

### Resultado F1 (HEAD 631a3273d6317ba62b315ef0ab1a52bcf89e88a2) e decisões complementares — 2026-11-12

**Revisão:** F1 ACCEPT_WITH_RESIDUAL. ADR-001 ACCEPTED pelo owner. F2 autorizado (somente testes). Runtime NÃO autorizado.

## Adendo F5a — Risco D9 e logs 7 dias aceitos pelo owner — 2026-11-12

O owner **aceitou o risco** de seguir a preparação dark / corte sem verificação prévia de:

1. **D9 (Chat/TV):** painéis TV e provider do chat com operationIds LNF (uso > 0 ou = 0 não foi inventariado em PROD nesta janela);
2. **Logs de 7 dias** dos callers das rotas LNF (item F4 2e).

Registro: risco aceito pelo owner em **2026-11-12**. Mitigação residual permanece no runbook 164 (rollback por flags + regeneração de catálogos no corte F5b).

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

---

## Adendo F7-R4 (2026-11-13) — CLARA aceita usuários só-LNF

**Decisão do owner:** a porta de entrada da CLARA (MCP) não exige mais somente `controllership-finance.access`. Usuário humano com qualquer `lancamento-notas-fiscais.*` efetiva entra na CLARA; gates por entrada de catálogo e a BFF (JWT do usuário) continuam sendo a autoridade de cada ação.

- Rotas HTTP do Portal/fechamento: inalteradas (`authorized_user` = CF.access).
- D8 (service principal proibido nas rotas LNF / MCP humano): inalterado.
- Knowledge: escopos `controllership` e `lancamento-notas-fiscais` separados por permissão efetiva.
