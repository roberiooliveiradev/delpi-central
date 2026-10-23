# 80 — PROC-0072 | Registro vivo de investigação técnica do Ciclo 2 — Devin

> **Criado:** 23/10/2026. **Produto:** Portal Controladoria & Finanças / Central de Fechamento. **Natureza:** template operacional **DOCUMENTATION_ONLY**, destinado a preenchimento progressivo pelo Devin após GO de investigação específico. **Não é ordem de execução, nem aprovação de SQL, nem autorização de runtime.**

## 0. Instruções de uso e fonte de verdade

- **Este documento é o ponto de entrada e índice vivo** do Ciclo 2. O [doc 47](./47-t01-report-column-audit-tracker-v1.md) **continua sendo a authority dos seis gates G1–G6, R01–R15, denominadores e percentuais**. Não duplicar status de gate como segunda authority. Se houver evidência nova, registrar aqui e atualizar o doc 47 na mesma rodada, sem promover PASS por antecipação.
- O Ciclo 1 é `PO_ACCEPTED_WITH_RESIDUAL` conforme [doc 79](./79-ciclo1-aceite-formal-po.md). O [doc 78](./78-ciclo1-crosswalk-narracao-artefatos.md) cruza V01–V23 com os artefatos. [Docs 56](./56-proc0072-observacoes-guiadas-fechamento-custos.md) e [57](./57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md) preservam a narração completa fornecida pelo PO; não solicitar nova narração.
- **Estado inicial:** `CYCLE_2_GO=NO`; `INVESTIGATION_NOT_STARTED`; `ERP_PARITY=TEST_NOT_RUN`. Inventários/probes prévios dos docs 47–49 não equivalem à execução deste ciclo.
- Identidade congelada: plugin `controllership-finance`, MFE `plugins/controllership-finance`, `/apps/controllership-finance`; BFF `controllership-finance-api`, `/apps/controllership-finance-api`; somente `controllership-finance.access` e `controllership-finance.manage`.
- TÉO/Joici = AS-IS/proveniência; GitHub HEAD = TARGET/contratos/código; Core = identidade/RBAC/effective permissions; api-delpi = owner de SQL e semântica TOTVS; strategic-indicators-api = indicadores. MFE comunica-se somente com BFF. Não compartilhar banco ou importar domain/application de outro contexto.
- **Regra de confidencialidade:** jamais versionar planilhas, PDFs, MP4, prints, linhas, valores, CPF/CNPJ, clientes, fornecedores, produtos, títulos, pedidos, credenciais, hashes de fontes privadas ou queries contendo identificadores reais. Apenas metadados genéricos, relações, lógica sanitizada, estados e referências técnicas aprovadas. Evidência operacional sensível fica sob custódia autorizada FORA do GitHub; registrar referência abstrata e acessos aprovados, sem endereço secreto ou token.
- **Edição concorrente:** revalidar HEAD e blob SHA do arquivo imediatamente antes de cada alteração. Preferir um commit pequeno por lote, sem sobrescrever resultados de outros agentes. Se divergência concorrente, parar, reconciliar e repetir o fetch; nunca force-push. Histórico é *append-only* nos registros de execução; correção cita registro anterior e motivo.
- Não marcar `PASS` por HTTP 200, schema encontrado, screenshot, nome de rotina ou teste isolado. `search miss != ausência`.

## 1. Controle de autorização e capacidades — preencher antes de qualquer consulta operacional

| Campo | Estado / preenchimento exigido |
|---|---|
| PO GO específico para Ciclo 2 | **D0-DOCUMENTARY_ONLY autorizado** pelo pedido `CF-C2-D0-001` (23/10/2026, texto do pedido em custódia do PO); GO de dados/consulta ao ERP continua **NO — PENDING** |
| Escopo autorizado | D0: leitura e inspeção documental do repositório (código, contratos, OpenAPI, configs não sensíveis, testes). Consultas de dados ao ERP: **não autorizadas** |
| Executor / identidade técnica | Devin (agente) — leitura de repositório. **Principal de API para D1 não provisionado**: TO_VERIFY (ver §11.D) |
| Repositório / branch / HEAD | `roberiooliveiradev/delpi-central` / `main` worktree `cf-stock-wt` @ `cda28e6b9fddfa47ac03dac77d21bf80e23b0d0f` (capturado em 23/10/2026) |
| `git status` do checkout | Limpo no início do lote D0; alterações preexistentes de outros worktrees não tocadas |
| Authorities carregadas | Instruções oficiais; `.cursor` aplicáveis (index, evidence-driven, boundaries, security, contracts, data-persistence); README do produto; docs 21/23/42/46/47/48/49/56/57/78/79; código físico api-delpi/BFF/shared-delpi_auth |
| Rotas tipadas autorizadas disponíveis | Inventariadas em §11.B: `/system/*` (metadados SX2/SX3/SIX/SX9), `/data/sql` (SQL read-only validada), rotas tipadas `financeiro/*`, `supplies/*`, produção, integrações. Nenhuma autorização de execução concedida por este documento |
| Rotas `/data/sql` e `/system` | Existência e guardrails comprovadas por código (§11.B). Execução: **NOT_AUTHORIZED** até GO explícito por lote; `/system` é candidata preferencial para D1 (metadados apenas) |
| Metadados SQL e consulta de dados | Capacidades distintas confirmadas: `/system` = dicionário físico; `/data/sql` = dados arbitrários SELECT-only. Aprovações separadas, menor privilégio primeiro |
| Grants e identidade efetiva | Authz = permissões efetivas resolvidas no Core `/me` por request (`shared/delpi_auth/middleware/fastapi_auth.py:103`). Quais principals detêm `api-delpi.system`/`api-delpi.data`: **TO_VERIFY** (requer Keycloak/Core, não disponível nesta sessão) |
| Limites operacionais | `/system`: paginação limitada via `LIMIT_QUERY` (tetos 20–200). `/data/sql`: sem teto de linhas observado no backend (`fetchall` em `base_repository.py:203`); projeção `BOUNDED_DYNAMIC_RESULTSET` existe na superfície DAVI; timeout: **TO_VERIFY** |
| Segurança da saída | Este registro contém apenas metadados técnicos e referências de código; nenhum valor operacional |
| Gate D0 | `EXECUTED_DOCUMENTARY` — ver registro D0-001 e §11. D1 permanece `PENDING_GO` |

**D0 — DoD:** inventário verificável das capacidades acessíveis ao executor, inclusive status de authn/authz, política de query, owners e limitações. **Não testar SQL arbitrária como maneira de descobrir permissões.** Em caso de dúvida de acesso, `DECISION_REQUIRED`; falha de autorização = STOP.

## 2. Ordem de investigação recomendada (não é GO)

| Lote | Dependência | Saída objetiva |
|---|---|---|
| D0 — READ/VERIFY API e permissões | GO de inventário apenas, owner e escopo | Manifesto das APIs, producer/consumer, controles e lacunas |
| D1 — metadados e bindings | D0 aprovado | Catálogo físico de tabelas/colunas/chaves/semântica, sem queries de negócio não autorizadas |
| D2 — estoques e custos | D1 e fontes validadas | Paridade de P7/MATR320/H02, Kardex, CPV, inventários |
| D3 — financeiro | D1 e autorização de dados financeiros | Paridade FINR e cinco saídas, compensação/baixa e logs |
| D4 — demais conferências e entregas | D1 e owners confirmados | MOD, custo médio, SD1, catálogos, evidências externas |
| D5 — revisão e homologação | D2–D4 executados ou bloqueados com justificativa | Exec report, resumo dos gaps, doc 47 atualizado e decisões para Ciclo 3 |

D1–D4 podem ser desdobrados sem apagar o histórico; o doc 47 controla R01–R15 e quaisquer filhos.

## 3. Matriz mestra — workstreams e rastreabilidade

| ID | Ordem | Tracker doc 47 | Narração / reconciliação doc 57 | Inventário Ciclo 1 | Questão principal | Owner validador candidato | Lote |
|---|---|---|---|---|---|---|---|
| C2-01 | P0 | R03/R05/R08 | V11/V13/V17; RC-01/02 | 63/62/64/68 | MATR320 x P7 x H02 | Joici + ERP/api-delpi | D2 |
| C2-02 | P0 | R03 | V11; X03 | 63/68 | P7 integral x reduzido | Contabilidade + ERP/api-delpi | D2 |
| C2-03 | P0 | R06 | V12/V15; RC-04 | 61/67 | CPV Kardex 01 | Custos + ERP/api-delpi | D2 |
| C2-04 | P0 | R01/R02 | V07-V09; RC-09 | 69-75 | Baixas/compensações | Financeiro + ERP/api-delpi | D3 |
| C2-05 | P1 | R07 | V12/V14; RC-03 | 61/66 | Inventário 01/99 | Estoque + ERP/api-delpi | D2 |
| C2-06 | P1 | R09 | V05/V16; RC-05 | 65 | Faturamento x MOD | Custos + PCP + ERP/api-delpi | D4 |
| C2-07 | P1 | R12 | V01/V10 | 77 (Análise) | Custo médio e jobs | Joici + ERP/api-delpi | D4 |
| C2-08 | P1 | R10 | V20-V22; RC-06 | 77 (CC matriz) | Despesas e CC/SD1 | Controladoria + Contabilidade + ERP/api-delpi | D4 |
| C2-09 | P1 | R13/R14 + checklist | V18/V19 | 59/60 | Entregas e fontes externas | Joici + Contabilidade + PO | D4 |

**Importante:** owner indicado é candidato para confirmação com a autoridade da área. O grupo `R13/R14` não significa equivalência entre fontes externas e checklist. Não remover R04, R11, R15 ou qualquer dos quinze itens do doc 47 por não estarem destacados nos nove workstreams: continuam no controle, exigem triagem/owner e, se necessário, desdobramento explícito de denominator/scope_change.

## 4. Ficha única obrigatória — copiar para cada workstream ou filho

A cada rodada, preencher **todos os campos**, inclusive os indisponíveis, usando `TO_INVENTORY`, `PENDING`, `TEST_NOT_RUN` ou `INCONCLUSIVE`; nunca deixar célula vazia interpretável como PASS.

```text
RECORD_ID: C2-xx / Rxx[.child] / iteration
RECORD_STATUS: PENDING
BASE_HEAD: <sha verificavel>
WORKTREE_STATUS: <clean / dirty / INCONCLUSIVE>
EXECUTOR_ID: <identidade autorizada>
RUN_DATE_UTC: <ISO-8601>
GO_REFERENCE_AND_SCOPE: <decisao PO, sha, owner API, capability; ou NO_GO>
SOURCE_DOCS: <56/57 Vxx, 78, inventario 59–77, 46/47, contratos>
PROCESS_STAGE_TEO: <node / versao / authority>
FUNCTIONAL_OWNER: <validado / candidato + evidencia>
TECHNICAL_OWNER: <repo/servico/time + evidencia>
REPORT_ID_NAME_VERSION: <impresso / candidato / TO_INVENTORY>
MENU_AND_PARAMETERS: <datas, empresa, filial, armazem, moeda, flags, cutoff, estado custeio>
POPULATION_AND_GRAIN: <evento, titulo, produto, OP, snapshot etc.; regra de deduplicacao>
SOURCE_KIND: ERP | EXTERNAL | MIXED | UNKNOWN
API_DISCOVERY: <metodo, path, OpenAPI/code link, commit, auth, scope, policy>
TABLES_AND_ALIASES: <aliases fisicos, origem de metadado, nao inferir nomes>
COLUMNS_AND_TYPES: <output -> physical column -> datatype -> nullability -> unit -> semantics>
KEYS_AND_CARDINALITY: <PK/candidata, FK/ponte, join e multiplicacao potencial>
FILTERS_AND_EXCLUSIONS: <D_E_L_E_T_, filial, data, cancelados, terceiros, compensacoes...>
BUSINESS_RULES: <formula, sinal, rounding, moeda, exclusoes e prova>
QUERY_OR_OPERATION_ID: <capability permitida, metodo, query template sanitizada e limite>
READ_EXECUTION: NOT_RUN | EXECUTED_AUTHORIZED | BLOCKED (sem dados privados)
PARITY_PROTOCOL: <artefato oficial, parametros comuns, denominador, tolerancia apenas se contratada>
PARITY_RESULT: TEST_NOT_RUN | PASS | FAIL | INCONCLUSIVE
PARITY_DIFFERENCE_CLASS: <population/filter/join/currency/sign/time/costing/other>
TEST_CASES: <positive, negative, boundary, partial, estorno, scope conforme relevante>
PRODUCER_CONTRACT_CONSUMER: <paths/shas, campo, impacto e tests; ou TO_INVENTORY>
SECURITY_PROOF: <escopo autorizado, authz efetiva, minimizacao, fail-closed>
EVIDENCE_REGISTER: <refs do GitHub somente sanitizadas; custodiante privado quando aplicavel>
G1_G6_STATUS_FROM_DOC47: <referencia apenas; NUNCA inventar PASS>
OPEN_QUESTIONS: <pergunta -> owner -> unblock action>
ASSUMPTIONS_INVALIDATED: <sim/nao; se sim EXECUTION_DRIFT>
REVIEW_VERDICT: INCONCLUSIVE
NEXT_BOUNDED_STEP: <exatamente uma proxima acao aprovada>
COMMIT_SHA: <sha realmente confirmado ou NONE>
```

### Registro de execução (append-only; repetir por rodada)

| Run ID | Lote / item | Base HEAD | GO ref | Ação READ autorizada | Nova evidência sanitizada | G1–G6 impactados | Bloqueio/owner | Commit/SHAs | Veredito |
|---|---|---|---|---|---|---|---|---|---|
| D0-001 | D0 | `cda28e6b9f` | CF-C2-D0-001 (documentary GO apenas) | EXECUTED_DOC_ONLY — inventário de rotas/authz/guardrails por código; nenhuma chamada ao ERP | Manifesto §11.B; cobertura §11.C; plano D1 §11.E | NONE — `NO_GATE_CHANGE` | Principal de execução D1 não provisionado (owner: Core/Keycloak + PO) | commit deste registro | EXECUTED_DOCUMENTARY |

## 5. Questões verificáveis e critérios por workstream

### C2-01 — MATR320 x P7 x H02 (P0)
- Confirmar versões/rotinas e mapeamento físico de cada saída, parâmetros idênticos, população, saldos de abertura/fechamento, processo, terceiros e custeio.
- Validar relação de reconciliação **sem adotar a igualdade por hipótese**; observar regra P3 já aprovada de `DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02` e `PARIDADE_OK` somente em R$ 0,00, com ±R$ 0,01 divergente; não declarar PASS se as três medidas não são oficiais e comparáveis.
- AC: protocolo reproduzível, totais categorizados, explicações de diferenças e owner; caso contrário `INCONCLUSIVE`.

### C2-02 — P7 completo x reduzido (P0)
- Identificar motivo das diferenças de matéria-prima, versões, parâmetros, custo, layout H, filiais e terceiros. Não equiparar R03 operacional ao P7 oficial.
- AC: dois outputs oficiais sob recorte comprovado, equivalência ou divergência explicada formalmente.

### C2-03 — CPV/Kardex (P0)
- Validar armazém 01, códigos fiscais completos, terceiros, sinais e coluna de custo; inventariar consumers atuais (inclusive indicador/CPV).
- AC: valor oficial explicado por população e fórmula homologada, sem usar planilha como norma.

### C2-04 — baixas financeiras (P0)
- Contrastar fontes 69–75 e doc 48 com produtor FINR190/customização efetiva, `FK1/FK2/FK7/SE1/SE2/FKB` quando autorizados; respeitar cardinalidade, branch nullable, natureza, motivo, estorno, compensação e baixa parcial.
- AC: comparação PDF/XLSB/ERP por data/natureza/motivo, incluindo logs de inconsistências; sem inferir movimento bancário de baixa nem replicar título como evento.
- Auditar effective permissions e isolamentos de scope com owners; nenhum endpoint novo.

### C2-05 — inventário 01/99 (P1)
- Revalidar inventário `INVENT`, TES `999/499`, movimentos `RE0/DE0` observados, cobertura por armazém, multiplicações e sinal.
- AC: cálculo e população por armazém, sem dupla contagem, conferidos com relatório oficial.

### C2-06 — faturamento x MOD (P1)
- Provar origem de componentes de MOD, quantidade, horas teóricas e apontadas, custo unitário e total; testar retornos/devoluções e filiais.
- AC: semântica de previsto/realizado formalmente aprovada, com paridade por unidade/competência.

### C2-07 — custo médio e jobs (P1)
- Identificar parâmetros/estado do Acompanha Custos e custo de reposição, status reais de jobs, consequência do Refaz Saldos e filtro de variações.
- AC: algoritmo/versão e pontos de leitura seguros demonstrados; **nenhum comando mutante**.

### C2-08 — centro de custo SD1 (P1)
- Verificar fonte SD1, tipos de entrada, exclusões MP/terceiros, cadastro de CC, conta contábil, diferenças entre direto/indireto/administrativo, exceções e vigência.
- AC: regras revisadas pela Contabilidade com casos limítrofes; não codificar prefixos como verdade.

### C2-09 — entregas por competência (P1)
- Relacionar checklist P2, catálogo P6 e pacote P5 com fonte/produtor por item, escopo de unidade ativa, destinatário e aprovação humana via Core.
- AC: rastreabilidade de obrigações, arquivos e owners sem interpretar verde `Enviar` como enviado/aceito; não criar página ou permission.

## 6. Critério de passagem e protocolo de paridade

1. G1 propósito/etapa: evidência rastreável ao TÉO, documentos e owner.
2. G2 saída/layout: campos, filtros, totais, agrupamento e versão demonstrados.
3. G3 tipo e owner: ERP/externa/mista confirmado; não deduzir pela rotina candidata.
4. G4 bindings técnicos ou contrato externo: tabelas, colunas, chaves, regras e consumidor confirmados.
5. G5 teste read-only reproduzível e paridade: mesma população, período, filial, moeda, custeio, fórmulas, exceções, logs e diferenças. `TEST_NOT_RUN` quando não houve teste autorizado.
6. G6 aceite funcional formal: owner humano revisa resultado; executor não autoaprova.

**Progressos e percentuais** são calculados **somente no doc 47**, com denominator e source SHA. `PASS` de G1–G4 não implica G5 ou G6; contagem de linhas não equivale a paridade de totais.

## 7. Segurança, limites de consultas e paradas obrigatórias

- Inventariar SQL/system por leitura de documentação e código; usar **apenas** operações READ existentes, autorizadas, limitadas e auditadas por owner. `POST` pode ser read-only no contrato, mas método HTTP não prova imutabilidade: inspecionar implementação.
- Negar ou interromper operações com DDL/DML, stored procedures mutantes, `EXEC`, grants, deploy, migration, export massivo, bypass de authz e manipulação de fechamento/compensações.
- Exigir escopo de empresa/filial autorizado, limites de datas e linhas, timeout, redução de campos sensíveis, rate limit, usuário técnico auditável; authn != authz.
- Divergência entre contrato e realidade ou hipótese refutada: `EXECUTION_DRIFT`, preservar a evidência e parar subgrafo afetado.
- Falta de owner, credencial, rota, escopo, definição monetária ou permissão: `INCONCLUSIVE`/`DECISION_REQUIRED`, nunca fallback para SQL irrestrita.
- Duas tentativas sem evidência nova: documentar bloqueio, owner e próximo desbloqueio; não repetir busca cega.
- Sem autorização formal do PO para **cada lote** aplicável, preencher apenas inventário documental ou aguardar GO; não executar consultas.
- Não alterar contratos R01/R02/R03 (docs 48/49), permissões, domínio ou runtime como subproduto do inventário.

## 8. Contrato de entrega para revisão GPT

Em cada entrega Devin deve produzir: **FACTS / EVIDENCE / GAPS / DRIFT / DECISION_REQUIRED / TESTS / SECURITY / COVERAGE / SHAS / NEXT_BOUNDED_STEP**. Incluir RQ/AC ou IDs de investigação, tabelas/campos confirmados, argumentos de paridade, owners e todos os não-testados.

O GPT emite só `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Após review, correções e aprovação, registrar commit e atualizar README de maneira limitada. Nenhum PASS ou GO é inferido de documento, API HTTP 200, teste verde isolado ou ausência de resultados na busca.

## 9. Critério de fechamento do Ciclo 2

- Todas as famílias R01–R15 e filhos necessários tiveram disposição formal `PASS` ou bloqueio qualificado com owner, causa e plano; denominadores íntegros no doc 47.
- Questões dos nove workstreams receberam evidência rastreável, incluindo diferenças e regras que permanecem não homologadas.
- G5 e G6 só recebem PASS com prova técnica e aceite humano. Não encerrar como paridade plena se houver casos `TEST_NOT_RUN`.
- Contratos para Ciclo 3 são **propostas**, sem implementação; decisões materiais abertas seguem `DECISION_REQUIRED`.
- PO autoriza expressamente o próximo gate, separadamente. Este doc é instrumento de preenchimento, não GO.

## 10. Próxima ação — limitada

**D0 documental executado (ver §11).** Aguardar revisão do GPT Arquiteto e GO expresso do PO para o **lote D1** (metadados físicos via rotas `/system`, sequência e restrições em §11.E). Nenhuma chamada ao ERP foi ou será feita sem esse GO.

## 11. D0 — Inventário técnico de capacidades (CF-C2-D0-001, 23/10/2026)

Base: `cda28e6b9fddfa47ac03dac77d21bf80e23b0d0f`, worktree limpo, somente leitura de código/contratos/config não sensível. Nenhuma chamada HTTP ao ERP executada.

### 11.A — Modelo de autenticação/autorização (comprovado em código)

| Camada | Mecanismo | Evidência |
|---|---|---|
| AuthN usuário | JWT Keycloak (JWKS, issuer+audience obrigatórios, fail-closed sem config) | `shared/delpi_auth/jwt_validator.py` |
| AuthZ efetiva | Core `/me` é a fonte primária, mas `load_user_rbac` emprega cache normal (TTL padrão 60s) e pode reutilizar dado stale (TTL padrão 900s) em falhas de consulta; `force_refresh` ignora caches e não aceita stale. Caminho de fallback por claims e marcação `rbac_unavailable` devem ser avaliados distintamente. **Não** equivale a reconsulta obrigatória do Core a cada request. | `shared/delpi_auth/middleware/fastapi_auth.py:26-29,84-103,103-162,184-272` |
| Enforcement rota | `require_any_permission(...)` usa permissões do contexto e trata `is_superadmin` antes do teste. Quando `rbac_unavailable` é verdadeiro **e falta permissão**, `_deny_missing_permission` eleva `Service Unavailable`; mapear resposta HTTP pelo middleware, sem afirmar fail-closed absoluto para todos os cenários de stale cache. Requer prova por teste para rota/principal. | `shared/delpi_auth/authorization.py`; `shared/delpi_auth/middleware/fastapi_auth.py` |
| S2S individual (ADR-010) | Guardas S2S e token delegado aparecem implementados para rotas específicas; validade de assinatura, audience, client allowlist, scope e obrigatoriedade de Bearer devem ser atestadas por testes de contrato/negação e configuração efetiva. Não inferir cobertura global de todos os endpoints. | `api-delpi/app/interface/http/s2s_service_access.py`; rotas financeiras e testes aplicáveis a inventariar |
| Superfícies públicas | Somente `/public/*`, `/.well-known/oauth-protected-resource`, `/gpt-actions/v1/openapi.json` | `api-delpi/app/middleware/auth_middleware.py:24-64` |
| MCP | `/mcp` exige OAuth de usuário (modelo A); identidade de máquina proibida | `auth_middleware.py:77-93`, `main.py:375` |

### 11.B — Manifesto de capacidades (api-delpi @ HEAD acima)

**Capacidades de metadados — `/system` (leitura de dicionário Protheus, tipadas):**

| Rota | Fonte física | AuthZ | Tipo | Disponibilidade |
|---|---|---|---|---|
| `GET /system/tables/search` | SX2 | `api-delpi.system` | READ | IMPLEMENTED; allowlisted p/ DAVI (`search_tables_by_description`) |
| `GET /system/tables/{t}` | SX2 | `api-delpi.system` | READ | IMPLEMENTED; allowlisted (`get_protheus_table`) |
| `GET /system/tables/{t}/columns` | SX3 | `api-delpi.system` | READ | IMPLEMENTED; allowlisted (`list_protheus_table_columns`) |
| `GET /system/tables/{t}/indexes` | SIX | `api-delpi.system` | READ | IMPLEMENTED |
| `GET /system/tables/{t}/relations` | SX9 | `api-delpi.system` | READ | IMPLEMENTED |
| `GET /system/tables/{t}/schema` | SX2+SX3+SIX+SX9 composto | `api-delpi.system` | READ | IMPLEMENTED |
| `GET /system/tables/{t}/columns/search` e `GET /system/columns/search` | SX3 | `api-delpi.system` | READ | IMPLEMENTED; 2ª allowlisted |

Fonte: `api-delpi/app/interface/http/routes/system_routes.py:69-290`; mount `main.py:379`. Paginação limitada (`LIMIT_QUERY`, tetos 20–200). Ideal para D1 — responde o essencial de G4 **sem tocar dados de negócio**.

**Capacidade SQL bruta — `/data`:**

| Rota | Guardrails | AuthZ | Tipo | Disponibilidade |
|---|---|---|---|---|
| `POST /data/sql` (`execute_sql_raw`) | Validador SQL estrutural e configuração de bypass de allowlist reportados no D0; seu comportamento efetivo, indireções e negativas devem ser demonstrados por testes. O caminho de repositório reporta `fetchall` sem teto de linhas comprovado neste review; auditoria e timeout pendentes. **Não** presumir SELECT-only como garantia integral sem testes e hardening. | `api-delpi.data` (grant efetivo não verificado) | SELECT-like / SECURITY_REVIEW_REQUIRED, não autorizado neste ciclo | IMPLEMENTED (código) / runtime não verificado; DAVI tem superfície declarada `BOUNDED_DYNAMIC_RESULTSET`, que não prova limite da rota de backend |

Fonte: `data_routes.py:23-93`, `sql_validator.py`, `run_sql_use_case.py`, `base_repository.py:188-215`, `app/content/davi_external_read_allowlist.json` (95 ops; única com `canonicalSqlRoute` = `execute_readonly_sql`). Auditoria por usuário e timeout/statement cap: **TO_VERIFY**.

**Rotas tipadas de negócio relevantes aos workstreams (todas READ/GET salvo indicação):**

| Rota(s) | Fonte TOTVS | AuthZ | Workstream |
|---|---|---|---|
| `GET /financeiro/settlements/payables` `/receivables` `/summary` | FK2/FK1 (eventos), FK7 (ponte), SE2/SE1 (títulos), SED (natureza) | S2S estrito: client `controllership-finance-api` + scope `settlements.read` + Bearer usuário delegado | C2-04 |
| `GET /financeiro/stock-inventory` | SB9010 snapshot `B9_DATA`=fim do período (`B9_QINI`, `B9_VINI1`) | S2S estrito scope `stock-inventory.read` | C2-01, C2-02 |
| `GET /supplies/stock-value` | SB9010 fechamento oficial + fallback estimado (resolução `officialClosure` vs `estimated`) | `KPI_SUPPLIES_ACCESS` ou S2S supplies-BFF | C2-01, C2-02, C2-05 |
| `GET /supplies/cpv`, `/supplies/inventory-turnover` | TOTVS (ver repositórios supplies) | `KPI_SUPPLIES_ACCESS` ou S2S supplies-BFF | C2-03 |
| `GET /financeiro/despesas-centro-custo/*` (6 rotas) | view `dbo.vw_fin_despesas_centro_custo` — **linhagem SD1 atrás da view: TO_VERIFY** | `financeiro-centro-custo.*` (Core /me) | C2-08 |
| `GET /financeiro/inadimplencia/*` (5+ rotas) | títulos de recebimento (SE1 e correlatas — detalhe TO_VERIFY) | `financeiro-inadimplencia.*` | C2-04 (adjacente) |
| `GET /stock-balances`, `non-moving-stock`, `inventory-accuracy`, `third-party-materials` | SB2 e correlatas | permissões por domínio (Core /me) | C2-05 |
| Família produção: `unproductive-hours`, `machine-load`, `pcp-orders`, `production-order-sets`, `production-appointments`, `eficiencia-fabril` | SH*/SC*/SD2 conforme repositório | permissões por domínio | C2-06, C2-07 |
| `GET /integrations/protheus/status` | Protheus REST (status) | `PROTHEUS_INTEGRATION_READ_PERMISSIONS` | auxiliar C2-04/08 (proveniência) |
| `POST/PUT /integrations/protheus/supplier*` | Protheus REST **WRITE** | idem | **FORA DE ESCOPO D1** — mutante |
| `GET /integrations/operations/{id}`, `.../events` | tracking de integração | conforme rota | auxiliar auditoria |
| Observabilidade `/system/{sql-health,console-*,observability-snapshot,caller-stats,connection-pools,query-cache/stats,openapi-diff,envelope-contracts,smoke-definitions}` | telemetria interna | `api-delpi.system`/`api-delpi-console.view`/`api-delpi.access` | suporte D1/D5; POSTs de alerta podem disparar webhook → **efeito indireto, não usar em D1** |

**BFF `controllership-finance-api`** (única fronteira do MFE): `GET /closing/financial-settlements`, `/closing/financial-settlements/summary`, `/closing/stock-inventory`, `/viewer-context`, `/health`. AuthZ `controllership-finance.access` via Core; upstream = S2S próprio (`X-Delpi-Service-Authorization`) + Bearer do usuário delegado (`infrastructure/api_delpi_gateway.py`). **Não expõe `/system` nem `/data/sql`** — D1 exige ou principal direto na api-delpi, ou novas rotas tipadas no BFF (DECISION_REQUIRED).

**`strategic-indicators-api`**: rotas de indicadores/integrações existem (`si_app/interface/http/routes/*`); detalhamento **TO_INVENTORY** sob demanda (consumers de CPV/MOD — C2-03, C2-06).

### 11.C — Cobertura dos workstreams (capacidade × necessidade)

| WS | Capacidade candidata | Cobre sem SQL bruta? | Lacuna / dependência |
|---|---|---|---|
| C2-01 MATR320×P7×H02 | `/system` (bindings candidatos SB9/SB2/SD3…) + `/supplies/stock-value` + `/financeiro/stock-inventory` | Capacidade de consultar dicionário implementada; bindings necessários **não verificados**. Dados/paridade: não autorizados | Job/parâmetros do fechamento não são expostos por API — owner Protheus |
| C2-02 P7 integral×reduzido | idem + contrato R03 (`officialP7:false` preservado) | Metadados: sim. Dois outputs oficiais: fora da API (artefatos/custódia PO) | comparação documental, não SQL |
| C2-03 CPV/Kardex 01 | `/supplies/cpv` + `/system` (SD3/SB2 bindings) | Parcial — regra de coluna de custo exige binding físico via `/system` | confirmar grain da rota CPV |
| C2-04 Baixas | `/financeiro/settlements/*` (S2S) + `/system` (FK1/FK2/FK7/SE1/SE2/FKB/SED) | Metadados: sim. Paridade FINR190/logs: depende de artefatos oficiais | owner Financeiro + proveniência FINR |
| C2-05 Inventário 01/99 | `stock_balances`, `inventory_accuracy`, `/system` (SB2/SB8/SD3, TES 999/499, RE0/DE0) | Metadados: sim | TES/movimentos exigem verificação de dados — GO |
| C2-06 Faturamento×MOD | rotas produção + `/system` (SH6/SH1/SD2/SD3) | Metadados: sim | semântica previsto/realizado: owner Custos/PCP |
| C2-07 Custo médio/jobs | `/system` (B2_CM1 e correlatas) + código `stock_value_*` | Metadados: sim | **status de jobs Protheus não é API** — DECISION_REQUIRED (observação assistida) |
| C2-08 CC/SD1 | `/financeiro/despesas-centro-custo/*` + `/system` (SD1/CTT) | Parcial — fonte real atrás de view customizada | mapear linhagem da `vw_fin_despesas_centro_custo` |
| C2-09 Entregas/fontes externas | Core (aprovação humana) + doc 47/checklist | Fonte ERP por `/system` não aplicável como critério universal; documentação e contrato externo requerem owner | sem dependência obrigatória de SQL |

### 11.D — Gaps e decisões pendentes

- **Principal de execução para D1**: nenhuma identidade de auditoria provisionada. Opções: (a) usuário existente com grant `api-delpi.system` no Core; (b) client S2S novo com escopo dedicado `metadata.read` (exigiria contrato novo — não há rota S2S para `/system` hoje); (c) execução assistida pelo owner. **DECISION_REQUIRED** — recomendação: (a) menor privilégio, menor mudança de código.
- `/data/sql`: **SECURITY_REVIEW_REQUIRED** — bypass de allowlist ligado por padrão e ausência de teto de linhas no backend; para D1 preferir `/system` (responde G4 sem dados). SQL bruta só com GO nominal + teto `TOP` explícito + auditoria confirmada.
- Grants efetivos de `api-delpi.system`/`api-delpi.data`: **TO_VERIFY** (Keycloak/Core, fora da sessão).
- Timeout/statement cap e auditoria por usuário em `/data/sql`: **TO_VERIFY**.
- Linhagem SD1 da view `vw_fin_despesas_centro_custo`: **TO_VERIFY** (D1 via `/system` não resolve views customizadas; pode exigir `INFORMATION_SCHEMA`/fonte TOTVS — ponto de GO).
- `strategic-indicators-api` e consumers de indicadores CPV/MOD: **TO_INVENTORY** se C2-03/C2-06 exigirem.
- **Revisão GPT D0** detectou imprecisão material da frase `Core /me por request` diante de cache normal/stale; correção documental registrada, sem alegar que o runtime esteja defeituoso. **NO_GATE_CHANGE** no doc 47.

### 11.E — Proposta delimitada do D1 (PENDING_GO)

1. **Escopo**: somente metadados físicos — nomes de tabela, colunas, tipos, chaves, índices, relações SX9 — para o conjunto de aliases por workstream (SB9, SB1, SB2, SD3, FK1/FK2/FK7, SE1/SE2, SED, FKB, SD1, CTT, SH1/SH6, RE0/DE0, SIX, SX* conforme ledger).
2. **Sequência mínima**: `GET /system/tables/search` por alias → `GET /system/tables/{t}/schema` por tabela confirmada → `/relations` e `/indexes` quando o schema composto não bastar. Sem SELECT de dados.
3. **Restrições**: sem datas/valores de negócio na resposta registrada; saída sanitizada (metadados apenas); volume ≤ ~60 chamadas; principal único auditável; horário acordado.
4. **Evidência esperada**: mapa físico por workstream preenchendo `TABLES_AND_ALIASES`, `COLUMNS_AND_TYPES`, `KEYS_AND_CARDINALITY` das fichas §4; divergências doc×físico → `EXECUTION_DRIFT`.
5. **Critérios de parada**: permissão ausente (`403`), tabela não catalogada, necessidade de dados (→ volta ao PO), qualquer ambiguidade de escopo.
6. **Não coberto por capacidades atuais**: parâmetros de jobs/rotinas Protheus (MATR320, Refaz Saldos, Acompanha Custos), artefatos oficiais, linhagem de views customizadas — exigem owner humano ou GO específico.
7. **Owners necessários**: PO (GO), owner api-delpi (confirmação de uso `/system`), admin Core/Keycloak (grant do principal).


### 11.F — GPT rework documental D0 (23/10/2026)

**Motivo:** revisão da precisão de authz/cache, cobertura `/system` e garantias SQL/S2S. Rework exclusivamente documental; nenhum teste ou chamada ao ERP.

1. **Core RBAC:** `load_user_rbac` consulta `Core /me` quando necessário, usando cache normal de 60 segundos e fallback stale até 900 segundos pelos valores padrão (`fastapi_auth.py:26-29,103-162`). `force_refresh=True` ignora os caches e desativa fallback stale. `rbac_unavailable` não pode ser descrito como consequência de toda falha do Core: houve caminhos de cache e fallback distintos, cuja execução por rota depende de testes de negação. Não alegar reconsulta ao Core em toda request.
2. **Cobertura:** todas as nove frentes receberam rotas *candidatas* no manifesto D0; não houve chamadas reais às rotas `/system`, conferência de dados físicos nem demonstração de que todos os bindings existem. `G4 = NO_GATE_CHANGE` até evidência direta e owner.
3. **`/data/sql`:** manter `SECURITY_REVIEW_REQUIRED` e `NOT_AUTHORIZED`; bypass reportado de allowlist e ausência observada de row cap impedem considerá-la apta para D1. A proteção estrutural SELECT-like deve ser testada antes de constituir garantia de segurança; a bounded projection DAVI não prova teto no backend.
4. **S2S:** guardas presentes no código para rotas financeiras, mas efetividade de configuração, negative paths, grants e token delegado dependem de testes específicos e owner; não se deve generalizar para toda a API.
5. **Rastreabilidade:** Doc 47 preservado com `NO_GATE_CHANGE`. Os dados de autenticação vêm do código no HEAD observado; nenhum HTTP/ERP ou permission grant foi testado. D1 permanece `PENDING_GO`, com principal/owner e escopo por aprovar.

**Revisão:** correções documentais efetuadas; nenhum sinal de implementação autorizada. `D0_EXECUTION=DOCUMENTARY_ONLY`; `G4_PARITY=TEST_NOT_RUN`; `D1=NO_GO`.


## 12. Decisão do PO — GO de execução READ-only do Ciclo 2 (23/10/2026)

**Decisão expressa do PO nesta conversa:** "vamos fazer apenas consultas select o usuário do banco é somene leitura. vamos partir para execução, ficar limitando o devin só vai nos atrapalhar". Esta seção é a autoridade mais recente sobre o **GO operacional READ-only** e prevalece sobre marcas anteriores de `D1=NO_GO` ou `CYCLE_2_GO=NO` **somente para investigação SELECT/read-only nos nove workstreams**, sem reclassificar provas antigas.

**Estado atualizado:** `CYCLE_2_READ_INVESTIGATION=PO_APPROVED`; `D1-D4_READ_DISCOVERY=AUTHORIZED_WITH_VERIFIED_READ_ONLY_PRINCIPAL`; `WRITE_OR_RUNTIME_IMPLEMENTATION=NOT_AUTHORIZED`. D0 está fechado documentalmente com residuais. O PO afirma que o usuário do banco é somente leitura; **os grants efetivos do principal ainda precisam ser constatados pelo executor**, sem expor credenciais. Se a autenticação/autorização requerida pela API não estiver disponível, registrar bloqueio; não contornar proteções nem solicitar novas permissões por conta própria.

### 12.A — Diretriz de execução

- Devin pode investigar em sequência **D1, D2, D3 e D4** sem pedir um novo aceite para cada tabela ou chamada de leitura, dentro deste escopo; revisar e publicar evidências progressivamente. Não exigir número fixo de chamadas nem obrigar que todo dicionário SX2/SX3 esteja completo antes dos SELECTs necessários.
- Permitidos: leitura de metadados via `/system`, consultas tipadas GET de dados operacionais, e `SELECT`/CTEs read-only via `/data/sql` ou ação canônica autorizada, respeitando autenticação/escopo disponíveis e conta de BD sem privilégios de escrita. Escolher a superfície com menor complexidade que entregue prova.
- Antes da primeira consulta: capturar HEAD/status; verificar pelo canal legítimo os privilégios e a identidade de consulta efetivamente utilizados, documentação da rota, e que consulta read-only não chama rotina/procedure mutante. Não executar DDL, DML, EXEC/procedures, transações com escrita, nem contornar autenticação. Preferir tabelas/colunas explícitas e filtros de competência/filial; segmentar grandes conjuntos e usar limites ou agregados quando fizer sentido para proteger performance **sem impor um teto arbitrário que invalide a conciliação**.
- A afirmação do PO sobre conta read-only é uma premissa operacional, não comprovação independente. Se o principal efetivo tiver escrita, query endpoint permitir efeitos colaterais não conhecidos, ou observabilidade indicar carga excessiva, **STOP** e registrar owner/alternativa segura; não tentar explorar.
- Não publicar no GitHub dados brutos, valores financeiros confidenciais, identificadores pessoais, segredos ou tokens. Guardar outputs sensíveis em meio autorizado, documentando somente a existência, parâmetros sanitizados, regra, divergência, status e identificador de evidência permitido.
- Nenhuma nova API, BFF, tela, permission, migration, alteração de código produtivo, agendamento de job, alteração do Protheus ou deploy. O contrato R01/R02/R03 não muda por este GO.
- A execução do ciclo deve atualizar este registro vivo, doc 47 quando G1-G6 forem efetivamente demonstrados, e produzir Execution Report por workstream/rodada; sem esperar retorno a este chat para cada SELECT.

### 12.B — Gate mínimo não burocrático

1. Confirmar identidade técnica e autorização funcional existente para READ e conta de banco sem grants mutantes. **Sem novos grants pelo Devin.**
2. Executar apenas operações de leitura sem efeitos colaterais e com escopo corporativo permitido; manter filtros/volume proporcionais.
3. Para cada workstream, identificar fontes/chaves/fórmulas, montar SELECT reproduzível, comparar com artefato oficial e registrar diferença ou `INCONCLUSIVE`.
4. Atualizar docs 80 e 47 preservando o histórico; entregar SHAs e pendências.
5. Quando faltar autorização/capacidade, separar o bloqueio específico e continuar outros workstreams permitidos. Não bloquear todo o ciclo por uma lacuna isolada.

**Paridade e homologação:** este GO autoriza *investigar*, não presumir equivalência, passar G5/G6 sem prova ou declarar fechamento final. Revisão GPT e aceite funcional humano continuam necessários para conclusão.

## 13. Execução C2 — rodada 1 (23/10/2026, base `0a85ed4e95`)

**Canal de execução:** SELECTs read-only executados no host de produção via `docker exec -i delpi-api-delpi python -`, usando `app.infrastructure.providers.totvs.connection_pool` (mesma config da api-delpi). Nenhuma credencial copiada/registrada; nenhum dado operacional sensível publicado — apenas contagens, distribuições e vereditos de paridade.

**Gate 12.B.1 — PROVEN:** principal efetivo = conta de domínio nomeada (`SUSER_SNAME`), `db_datareader=1`, `db_datawriter=0`, `db_owner=0`, `HAS_PERMS_BY_NAME(...,'INSERT')=0`, `UPDATE` negado em SB1010, `SELECT` permitido. Premissa do PO ("conta somente leitura") **constatada por grants efetivos**, não só por afirmação.

### 13.A — Cobertura física das tabelas candidatas (metadados)

Existem com dados: SB1010 (~55k), SB2010 (~77k), SB9010 (~2,28M), SD3010 (~4,69M), SB5010 (~105k), SD7010 (~6,6k), SD9010 (~35k), FK1010 (~109k), FK2010 (~128k), FK7010 (~394k), SE1010 (~118k), SE2010 (~128k), SED010 (174), FKB010 (92), SE5010 (~310k), FK5010 (~239k), FK6010 (~3,2k), SB7010 (~46k), SD2010 (~499k), SF2010 (~235k), SH6010 (~474k), SH1010 (154), SC2010 (~923k), SG2010 (~128k), SG1010 (~197k), SD1010 (~282k), SF1010 (~105k), CTT010 (252; 182 ativos), CT1010 (~1,4k), SX2010/SX3010/SIX010/SX9010, SA1010/SA2010, SYS_USR, SBZ010. **Ausente:** DE0010. **Vazias:** RE0010, SB8010, SBJ010, SBK010, SDC010 (inventário por endereço/blocks/não-usados).

### 13.B — C2-01/C2-02 — estoque P7 (SB9)

- **Snapshots mensais completos**: `B9_DATA` tem snapshots fim-de-mês para as duas filiais, **2025-01 → 2026-09** (18 meses), com ~4,3–4,8k linhas/filial 01 e ~2,7–3,3k/filial 02 por data. Snapshot 2026-09-30 existe nas duas filiais.
- **`EXECUTION_DRIFT` resolvido (timing)**: o smoke de produção de 21-22/10 reportou `source_missing` para filial 01 em 09/2026; hoje SB9 tem 4.812 linhas em filial 01 nessa data → o fechamento de setembro da filial 01 foi gerado após o smoke. O semântico `source_missing` estava correto no momento da execução.
- **Paridade do contrato R03 — PROVEN (contra o próprio contrato)**: `SUM(B9_VINI1)` em 2026-09-30, filial 02, escopo `all_products` = **10.576.487,84** — idêntico ao `historicalTotal` do smoke registrado (10.576.487,839), centavo a centavo. Escopo `mp_pi_pa` = `B1_TIPO IN ('MP','PI','PA')` confirmado (`constantes.py:13`); contribuição mp_pi_pa = 94,6% do valor da filial 02.
- **Join SB9→SB1**: cobertura 100% (nenhum grupo `<no-sb1>` na distribuição de tipos da filial 01).
- Distribuição `B1_TIPO` filial 01 em 09/2026: MP 2.599, PA 802, II 704, PI 464, MC 83, MH 51, MS 37, EM 29, GG 21, MX 13, AI 7, SV 1, OI 1 — tipos não-MP/PI/PA somam 947 itens (escopo `all_products` os inclui legitimamente).
- Colunas confirmadas: `B9_QINI`, `B9_VINI1`, `B9_VINI2`, `B9_CM1` (custo médio no snapshot — insumo para C2-07), `B9_DATA`, `B9_FILIAL`, `B9_LOCAL`.
- **Paridade com MATR460 oficial: `TEST_NOT_RUN`** — exige artefato oficial (não disponível no canal DB).

### 13.C — C2-04 — baixas financeiras (FK1/FK2)

- **Grão do produtor confirmado = evento** (FKx), não título: SE2 títulos com `E2_BAIXA` em 09/2026 = 846; relatório oficial = 948 linhas; FK2 eventos = 978. Relatório oficial é event-level.
- **FK2 é fonte completa**: **0 títulos SE2 baixados em 09/2026 sem evento FK2** (retro-check via ponte FK7 `FK7_PREFIX/FK7_NUM/FK7_PARCEL/FK7_FILTIT` — colunas reais confirmadas: `FK7_FILIAL, FK7_IDDOC, FK7_ALIAS, FK7_FILTIT, FK7_PREFIX, FK7_NUM, FK7_PARCEL, FK7_TIPO, FK7_CLIFOR, FK7_LOJA, FK7_IDPAI`).
- **Ponte FK7→SE2**: 975/978 eventos (99,7%) têm alias `SE2`; apenas 3 eventos DEB sem ponte FK7 (prováveis baixas sem título vinculado).
- **Distribuição por motivo (FK2_MOTBX, 09/2026)**: DEB=673, CMP=190, FAT=83, DAC=26, NOR=6 (total 978) vs oficial (doc 73): DEB=600, CMP=186, FAT=83, NOR=65, DAC=14 (total 948). **FAT exato (83=83)**; deltas DEB +73, CMP +4, DAC +12, NOR −59, total +30 — `INCONCLUSIVE` com classes candidatas: população (origens), definição de data (FK2_DATA vs data de digitação/disponibilização), exclusões por motivo/origem.
- **`FK2_ORIGEM` (09/2026)**: FINA090=597, FINA750=274, FINA290=83, MATA103=24 — quatro rotinas produtoras; FINA750/MATA103 são candidatas a explicar parte do delta (rotinas não-baixa-manual).
- **`FK2_LA`**: N=882, vazio=93, S=3 — eventos marcados (S) e sem marcação existem; possível filtro do relatório sobre esse campo.
- `FK2_DTDIGI` fora do mês em 0 eventos → **data retroativa descartada** como causa do delta.
- SE5 (bancário) descartado como produtor: 139.890 NOR + 92.861 DEB no mês — grão/escopo muito maiores que o relatório.
- Recebimento (FK1, 09/2026): NOR=634, CMP=40, DAC=2 (676 eventos) — para confronto futuro com a aba de recebidos do artefato oficial.
- **Matriz origem×motivo (09/2026)**: FINA090→DEB 597; FINA290→FAT 83; FINA750→CMP 180, DEB 76, DAC 12, NOR 6; MATA103→DAC 14, CMP 10.
- **Hipótese de reconciliação H-948-A**: `978 − MATA103(24) − NOR(6) = 948` — **bate o total oficial exatamente**. Porém a distribuição por motivo não fecha (FK2 DEB=673 vs oficial 600) → os rótulos de motivo do relatório provavelmente derivam de outro campo (ou a amostra do doc 73 não cobre o universo). Status: **INCONCLUSIVE**, hipótese forte a validar com o artefato/owner FINR190.
- **Recebimento (FK1, 09/2026)**: origem×motivo = FINA110→NOR 557, FINA715→NOR 46, FINA740→NOR 31/CMP 40/DAC 2 (total 676 vs oficial 657 — delta +19, mesma classe de divergência de população). Produtor oficial é o relatório custom `DLP06R01` (doc 74), não FINR190 — registrar para o mapeamento de producer em G3.
- Status: bindings da **fonte de dados** = PROVEN; bindings do **relatório** (campos→colunas, filtros exatos do FINR190/`_F190C`) = PENDING (precisa do owner da customização ou do artefato com filtros).

### 13.D — C2-05 — inventário/movimentos (SD3)

- SD3 filial 01 em 09/2026: **TM 999 = 19.893** (dominante), 010=1.941, 502=1.037, **499=547**, 503=226, 102=3.
- TES (SF4): 010=E "Devolução de cliente", 102=E "Rem ativo", 502=S "Venda de mercadorias", 503=S "Venda s/ ICMS". TES 999/499 não encontradas na filial consultada (custom ou por filial — TO_VERIFY).
- Prefixos de documento em TM 999/499: `220`=~19,9k, `INV`=258, `SK2`/`SK3`=98, `246`=26 — **sem `RE0`/`DE0`**; a referência da narração "RE0/DE0" provavelmente designa outra identificação (TO_INVENTORY com o PO/owner estoque; RE0010 existe mas vazia).
- TM 999+499 compartilham os mesmos documentos (ex.: `SK2`=65 em cada TM) → pares entrada/saída do mesmo movimento — confirmar regra de deduplicação antes de somar.
- **Eixo armazém 01/99 confirmado** (C2-05 "inventário 01/99"): SD3 09/2026 filial 01 — TM 999: loc `01`=11.242, `99`=8.543, `98`=103; TM 499: `01`=432, `99`=111. Docs `INV*` (ajuste de inventário): 113+79 no loc 01, 45+21 no loc 99.
- **Perfil de armazéns no SB9 2026-09-30**: filial 01 → locais 01 (3.945), 99 (753), 98 (101), 25, 50, ` 0`, 03; filial 02 → 01 (2.640), 99 (336), 98 (76), 50, 03, 00, 25. Base para os resumos por armazém do R03.

### 13.E — C2-06 — faturamento × MOD

- SD2 (itens NF saída) 09/2026: filial 01=1.791, filial 02=598 linhas.
- SH6 apontamentos 2026 (H6_DATAINI): filial 01=44.670, filial 02=62.085. Colunas úteis confirmadas: `H6_OP`, `H6_PRODUTO`, `H6_OPERAC`, `H6_RECURSO`, `H6_DATAINI/H6_HORAINI/H6_DATAFIN/H6_HORAFIN`, `H6_QTDPROD`, `H6_TEMPO`, `H6_LOCAL`, `H6_TIPO`, `H6_STATUS`.
- SH1 recursos (154 linhas): `H1_CODIGO`, `H1_MAOOBRA`, `H1_CCUSTO`, `H1_GCCUSTO`, `H1_MODFAT` — elos para custo de MOD por recurso.
- Cadeia candidata MOD: SH6.H6_TEMPO × taxa do recurso (SH1) → MOD apontado; faturado via SD2. Fórmula oficial e denominação previsto/realizado = owner Custos/PCP (narração V05/V16).

### 13.F — C2-07 — custo médio / jobs

- `B2_CM1` populado: 21.130 produtos ≠0 na filial 01, 9.445 na filial 02 → custo médio corrente disponível em SB2; `B9_CM1` também presente no snapshot mensal (comparável histórico×corrente).
- Parâmetro `MV_320SLD='1'` encontrado em SX6 (relacionado ao comportamento de saldo do MATR320 — registrar para C2-01).
- **Status de jobs/rotinas Protheus (Refaz Saldos, Acompanha Custos, MATR320 schedule) não é consultável via SQL** — depende do owner ERP / observação assistida. `DECISION_REQUIRED`/owner Joici+ERP.

### 13.G — C2-08 — centro de custo / SD1

- View `vw_fin_despesas_centro_custo`: 26 colunas (`filial, data_emissao, centro_custo_*, documento, serie, pedido, produto_*, valor_total, conta_contabil, rateio, tes, cfop, tipo_documento, tipo_produto_lancamento, recno_sd1`).
- **Linhagem SD1 = PROVEN**: amostra `recno_sd1` → `SD1010.R_E_C_N_O_` casou 3/3; `dm_sql_referenced_entities` vazio e `definition` NULL (metadados restritos/encriptados) — prova por join, não por texto.
- CTT010: 182 centros de custo ativos.
- Regras de classificação direto/indireto/administrativo e vigência = owner Contabilidade (doc §5 C2-08).

### 13.H — C2-09 — entregas/fontes externas

- Natureza documental (checklist P2, catálogo P6, pacote P5) — sem dependência de query nesta rodada. Pendente de trilha de aprovação via Core por item.

### 13.I — Registro desta rodada (append-only)

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R01 | Gate 12.B.1 | grants efetivos do principal | PROVEN read-only (datareader only) | — |
| C2-R02 | 13.A | existência física 45 tabelas | 38 presentes c/ dados; DE0 ausente; RE0/SB8/SBJ/SBK/SDC vazias | — |
| C2-R03 | C2-01/02 | cobertura SB9 + paridade contrato | 18 meses × 2 filiais; total all_products filial02 09/2026 bate smoke ao centavo | suporta G4 R03 (bindings); G5 oficial segue TEST_NOT_RUN |
| C2-R04 | C2-04 | grão, ponte, motivos, origens | evento FK2 completo (0 órfãos SE2); delta 978 vs 948 = INCONCLUSIVE com causas candidatas | suporta G4 parcial R01/R02 |
| C2-R05 | C2-05 | perfil SD3 + TES | TM 999/499 identificados; RE0/DE0 não são docs SD3 | TO_INVENTORY owner estoque |
| C2-R06 | C2-06/07/08 | SH6/SH1/SD2/B2_CM1/view | fontes confirmadas; linhagem SD1 da view provada por join | G4 parcial C2-08 |
| C2-R07 | — | doc 47 | `NO_GATE_CHANGE`: evidência prova fonte/grão, não binding no nível do relatório oficial (exige artefato/owner) | — |

### 13.J — Pendências identificadas nesta rodada

1. **Delta FK2 978↔948**: hipótese líder `978 − MATA103 − NOR = 948` (total exato); distribuição por motivo diverge → validar com artefato/owner FINR190 se exclusões são por origem/motivo/campo derivado.
2. TES 999/499: confirmar descrição/filial da TES (owner estoque).
3. "RE0/DE0" da narração: esclarecer com PO o que designam (não são tabelas nem prefixos SD3 observados).
4. Linhagem completa da view despesas (definição restrita): pedir DDL ao owner DB ou validar cobertura SD1 por período.
5. Paridade MATR460/H02/FINR190: depende de artefatos oficiais fora do banco.
6. Sequência de snapshot SB9 por filial: confirmar calendário de fechamento por filial (por que 01 fechou depois de 02 em 09/2026 — relevante para o semântico `source_missing`/`incomplete` do R03).

---

## 14. CICLO 2 — Execução Rodada 2 (CF-C2-EXEC-002) — evidências

> Autorização: continuação após `ACCEPT_WITH_RESIDUAL` da rodada 1. Mesmo canal (`docker exec` → pyodbc no container `delpi-api-delpi`, credenciais read-only já provisionadas), mesmo principal (`db_datareader` apenas). Somente SELECT/agregações `NOLOCK`. Nenhuma escrita, procedure, DDL ou alteração de runtime.

### 14.A — C2-01/C2-02 — cronologia do snapshot SB9 (filial 01)

- **PROVEN**: `SB9010.I_N_S_D_T_` (timestamp de inserção) mostra geração assíncrona por filial:
  - `B9_DATA=20260831`: filial 01 inserida **18/09 19:03** vs filial 02 **01/10 20:44**.
  - `B9_DATA=20260930`: filial 01 inserida **21/10 19:13** vs filial 02 **02/10 17:58** — defasagem de **19 dias**.
- Interpretação: o `source_missing`/`incomplete` observado no smoke reflete o **calendário real de fechamento por filial** (job executado por filial em datas distintas), não defeito de leitura. O job/processo upstream que gera o SB9 **não é exposto via SQL** — owner ERP (`Refaz Saldos`/`Acompanha Custos` ou schedule equivalente) segue `TO_INVENTORY` para proveniência do job.
- Consequência semântica para o R03: `source_missing` por filial é estado esperado durante a janela de fechamento; o timestamp de inserção do snapshot (`I_N_S_D_T_`) está disponível para exibição/telemetria futura se o contrato evoluir.

### 14.B — C2-04 — baixas a pagar: delta 978 × 948 (reprodução de filtros)

**Dimensão filial — PROVEN:**
- `FK2_FILIAL` é vazio em 100% dos eventos; `SE2.E2_FILIAL` é vazio em 100% dos títulos baixados em 09/2026 (846/846) — **títulos são centralizados sem filial**.
- A dimensão de filial efetiva é `FK2_FILORI` (filial de origem do evento): **filial 01 = 543 eventos, filial 02 = 435 eventos** (09/2026).
- Join FK2→FK7→SE2 corrigido e validado: `FK7_CHAVE` é chave delimitada `FILTIT|PREFIX|NUM|PARCEL|TIPO|CLIFOR|LOJA`; join pelos campos individuais `FK7_PREFIX/NUM/PARCEL/TIPO/CLIFOR/LOJA` → `E2_PREFIXO/NUM/PARCELA/TIPO/FORNECE/LOJA` cobre **975/978** eventos (99,7%). `FK7_ALIAS`='SE2' (pagar) / 'SE1' (receber) em 100% — ponte canônica confirmada.
- `E2_MOTIVO` é vazio em 100% dos títulos → o motivo só existe no grão do evento (`FK2_MOTBX`) ou em fonte ainda não identificada do relatório.

**Eixo de competência — três datas testadas (população ago–out/2026):**

| Eixo | Eventos em 09/2026 |
|---|---|
| `FK2_DATA` | 978 |
| `FK2_DTDIGI` | 980 |
| `E2_BAIXA` do título | 1.007 |

- Nenhum eixo reproduz 948; **competência por data não explica o delta**.

**Distribuição por tipo de documento (`FK2_TPDOC`, 09/2026):** VL=641, BA=198, CP=94, ES=45.
**Subconjuntos disjuntos que somam exatamente o delta 30:** `ORIGEM='MATA103'` (24) ⊕ `MOTBX='NOR'` (6) = 30 → `978 − 30 = 948` (aritmeticamente exato, interseção verificada = 0). Porém **o motivo oficial do artefato (NOR=65) diverge de `FK2_MOTBX` (NOR=6)** — se a exclusão fosse por `MOTBX='NOR'`, o artefato não poderia conter 65 NOR. Conclusão: **a coluna "motivo" do relatório não é `FK2_MOTBX`** (ou é mapeada/derivada) e a coincidência de total pode ser espúria. Status: **INCONCLUSIVE** — exige fonte do FINR190/layout ou artefato com parâmetros.

### 14.C — C2-04 — baixas a receber: delta 676 × 657 (`DLP06R01`)

- Eixos de competência (pop ago–out): `FK1_DATA`=676, `FK1_DTDIGI`=678, `E1_BAIXA`=671 — nenhum reproduz 657.
- Tipos de evento `FK1_TPDOC`: VL=633, ES=17, BA=14, CP=12.
- Tipos de título vinculado (`E1_TIPO` via FK7, alias 'SE1', cobertura 676/676): **NF=655, NCC=11, RA=9, BOL=1**. O artefato oficial lista `PA` entre os tipos — **nenhum evento FK1 de 09/2026 vincula título `PA`** → divergência de universo a investigar (ou o artefato cobre período/filtro diferente).
- **Subconjunto disjunto exato**: `TPDOC='ES'` (17) ⊕ `MOTBX='DAC'` (2) = 19 → `676 − 19 = 657` (interseção = 0). Candidato semanticamente plausível: `ES` = estorno excluído do relatório + `DAC` fora da relação de baixas. A distribuição por motivo do artefato não permite confirmar — **INCONCLUSIVE** até parâmetros do `DLP06R01`.
- `FK1_FILORI` também é a dimensão de filial: 01 = 359, 02 = 317 eventos.

### 14.D — C2-05 — "RE0/DE0": ausência comprovada no SD3

- Varredura em **toda a história** do SD3 (não apenas 09/2026): **zero** `D3_TM` alfabéticos (alfabeto completo = 010, 011, 015, 020, 100–105, 200/201, 499, 501–504, 600/601, 999) e **zero** prefixos `RE*`/`DE*` em `D3_DOC` (dominância numérica + `INV*` 37.698 + outros 5.899).
- `RE0010` existe como tabela física mas está **vazia**; `DE0010` não existe. Não é search-miss: o espaço de códigos foi enumerado exaustivamente.
- Interpretação revisada: "RE0/DE0" provavelmente designa **tipos de documento/movimento em outro módulo ou convenção da narração** (ex.: requisição/devolução no módulo de estoque/custos), não registros SD3. `TO_INVENTORY` com o owner estoque/PO — registrar como premissa da narração a confirmar, não como ausência do conceito.

### 14.E — C2-08 — linhagem view→SD1 ampliada (escala total)

- **PROVEN em escala total**: 156.808 linhas da `vw_fin_despesas_centro_custo` → **100% com `recno_sd1` preenchido e casado em `SD1010.R_E_C_N_O_` (0 órfãs, 0 nulos)** em todos os agrupamentos temporais varridos.
- `tipo_documento` da view: N=120.236, C=36.308, D=237, I=25, P=2 (semântica dos códigos = owner Contabilidade).
- **Permanece inacessível**: texto DDL da view (`sys.sql_modules.definition` = NULL — `WITH ENCRYPTION` ou restrição de metadados) e `sys.dm_sql_referenced_entities` vazio → os filtros internos (joins adicionais, exclusões, origem CTT/SA1/SA2) só são inferíveis pelas colunas expostas. `BLOCKED` por privilégio de metadados — owner DBA para DDL oficial.
- Implicação G4: binding view→SD1 demonstrado empiricamente; binding campo-a-campo interno da view permanece `PENDING`.

### 14.F — Registro desta rodada (append-only)

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R08 | C2-01/02 | `I_N_S_D_T_` SB9 por data/filial | PROVEN: filial 01 gera ~19 dias após filial 02 (set/2026: 21/10 vs 02/10) | suporta semântico `source_missing` do R03 |
| C2-R09 | C2-04 | join FK7→SE2 corrigido + `FK2_FILORI` | PROVEN: filial do evento = `FK2_FILORI` (01:543/02:435); títulos SE2 centralizados (filial vazia); ponte cobre 975/978 | bindings R01/R02 |
| C2-R10 | C2-04 | eixos de competência + TPDOC + subconjuntos do delta | 948 reproduzível por `−MATA103 −NOR` (disjunto) mas motivo oficial diverge → INCONCLUSIVE | G5 segue TEST_NOT_RUN |
| C2-R11 | C2-04 | recebíveis: eixos + TPDOC + `E1_TIPO` | 657 reproduzível por `−ES −DAC` (disjunto); títulos PA ausentes do universo FK1 → INCONCLUSIVE | G5 segue TEST_NOT_RUN |
| C2-R12 | C2-05 | enumeração exaustiva `D3_TM`/`D3_DOC` | PROVEN: RE0/DE0 inexistem no SD3 em toda a história | premissa da narração → PO/owner estoque |
| C2-R13 | C2-08 | view→SD1 por `recno_sd1` em escala | PROVEN: 156.808/156.808 linhas com linhagem (0 órfãs) | binding fonte G4 |
| C2-R14 | — | doc 47 | `NO_GATE_CHANGE`: bindings de fonte/grão provados; bindings de relatório e paridade oficial seguem pendentes de artefatos/parâmetros | — |

### 14.G — Pendências desta rodada

1. **Fonte do motivo oficial** (FINR190/`DLP06R01`): `E2_MOTIVO` vazio e `FK2_MOTBX`≠rótulos do artefato → identificar campo/rotina que rotula DEB/CMP/FAT/NOR/DAC no relatório. Owner: responsável pela customização/financeiro.
2. **Filtros efetivos dos relatórios**: testar com artefato exportado com parâmetros (competência, filial, tipos, exclusões); os deltas têm subconjuntos exatos mas divergem em motivo → não aceitar igualdade de total.
3. **"RE0/DE0"**: confirmar com PO/estoque a que conceito se referem na narração (não são TM nem prefixo de doc no SD3; `RE0010` vazia).
4. **DDL da view** de despesas: solicitar ao DBA (definição encriptada/restrita para o principal read-only).
5. **Proveniência do job SB9**: não exposta via SQL; confirmar com ERP a rotina e o calendário por filial.

---

## 15. CICLO 2 — Execução Rodada 3 (CF-C2-EXEC-003) — produtores e paridade

> Mesmo canal autorizado (SELECT-only via `docker exec` → pyodbc, principal `db_datareader`). Foco: origem técnica do FINR190/`DLP06R01`, fonte dos rótulos de motivo, confronto de universo/filtros pagar×receber, semântica `I_N_S_D_T_`.

### 15.A — Origem dos rótulos DEB/CMP/FAT/NOR/DAC — PROVEN

- Os códigos são **siglas do cadastro `F7G010` (motivos de baixa)**: `DEB`='DEBITO CC', `NOR`='NORMAL' (ambos `F7G_MOVBCO='S'` — movimento bancário), `CMP`='COMPENSA', `DAC`='DACAO', `FAT`='FATURAS'. F7G010 tem 20 siglas ativas, 1 linha cada.
- A coluna do relatório **NÃO é `FK2_MOTBX`** (evento) nem `E2_MOTIVO` (título, vazio em 100%): é **`SE5010.E5_MOTBX`** — motivo de baixa do **movimento bancário**, referenciando F7G. Isso resolve a divergência `FK2_MOTBX` NOR=6 vs artefato NOR=65.
- Coerência externa: o substituto oficial FINSV010 declara exatamente as tabelas `SE1, SE2, SED, F7G, FK1, FK2, FK5, FKA` (doc 46/TOTVS) — o elo SE5↔F7G encontrado na base é consistente com a família declarada.

### 15.B — C2-04 pagar — universo do relatório 948: PROVEN (grão)

- SE5 'P' em 09/2026: 1.126 linhas brutas. Restringindo a linhas **com título SE2 vinculado** (join `E5_PREFIXO+NUMERO+PARCELA+TIPO+CLIFOR+LOJA` → `E2_*`): **996 linhas / 877 títulos**.
- `E5_FILIAL` é vazio em 100% — movimento bancário também centralizado; filial do relatório segue `FK2_FILORI` (evento) ou dimensão equivalente.
- **`DISTINCT (título, E5_DATA, E5_MOTBX)` = 948 — total oficial reproduzido exatamente.** Grão do relatório = baixa por título × dia × motivo (o SE5 fragmenta baixas em múltiplas linhas por composição bancária; o relatório consolida).
- Distribuição por `E5_MOTBX` no universo consolidado: **NOR=65 e FAT=83 batem o artefato exatamente**; DEB=618 (vs 600), CMP=163 (vs 186), DAC=19 (vs 14). Divergência residual ±48 em 3 motivos — a coluna "motivo" do artefato pode derivar de reclassificação adicional (ou a tabulação da amostra no doc 73 leu coluna correlata). `INCONCLUSIVE` no nível motivo; `PROVEN` no nível total+grão.
- Eixos de data descartados: `FK2_DATA`, `FK2_DTDIGI`, `E2_BAIXA`, `E5_DATA` puro, `E5_DATA=E2_BAIXA` — nenhum reproduz 948 isoladamente.

### 15.C — C2-04 receber — universo do relatório 657: PROVEN (row-level)

- SE5 'R' em 09/2026 com título SE1 vinculado (mesmo join por `E1_*`): **657 linhas = total oficial exato**, sem dedup (dedup por (título,data,motivo) daria 649 — logo o relatório de receber é **row-level**, grão movimento).
- Distribuição: NOR=641 (VL=633, JR=3, MT=3, RA=1, DC=1), CMP=14 (BA/CP), DAC=2 (BA). Tipos de título: NF=655, NCC=11, RA=9, BOL=1 — título `PA` ausente no universo (residual vs lista do artefato).
- Produtores provavelmente **diferentes por lado**: pagar ≈ FINR190/derivado (grão consolidado título×dia×motivo), receber ≈ `DLP06R01` custom (grão movimento) — consistente com doc 46 (FINR190/`_F190C` para ambos no relato, DLP06R01 associado ao recebível pelo artefato). Nome/versão/fonte dos programas: `TO_INVENTORY` (código proprietário não acessível via SQL).

### 15.D — Filial, competência e filtros — síntese validada

| Dimensão | Pagar | Receber |
|---|---|---|
| Universo físico | SE5 'P' + SE2 | SE5 'R' + SE1 |
| Grão relatório | DISTINCT (título, data, motivo) = 948 | linha de movimento = 657 |
| Competência | `E5_DATA` no mês | `E5_DATA` no mês |
| Filial | não está em SE5/SE2 (vazia) → `FK2_FILORI` | idem → `FK1_FILORI` |
| Motivo | `E5_MOTBX` → F7G | `E5_MOTBX` → F7G |
| Tipo título | via FK7→SE2 | via FK7→SE1 |

### 15.E — `I_N_S_D_T_` e disponibilidade R03

- `I_N_S_D_T_` = timestamp de **inserção física** da linha SB9 pelo job de fechamento (proven na §14.A). Relação com o R03: a fonte fica disponível no endpoint assim que inserida — o `source_missing` reflete exclusivamente o atraso do job por filial. **Proveniência do job (rotina/schedule) permanece `TO_INVENTORY`** — não exposta via SQL; owner ERP.
- Cobertura view→SD1 (§14.E) preservada: 156.808/156.808 — sem revalidação necessária nesta rodada.

### 15.Bloqueios — Bloqueios desta rodada

- Código-fonte dos relatórios FINR190, `_F190C` e `DLP06R01` (proprietário/custom): não acessível via SQL — `BLOCKED`, owner TI/customização.
- Parâmetros efetivos de execução (tela de parâmetros): não persistidos em tabela acessível — `TO_INVENTORY` com operador/artefato exportado.
- DDL da view de despesas: segue `BLOCKED` (encriptada) — DBA.
- Divergência residual de motivos pagar (DEB/CMP/DAC ±48): exige inspeção da lógica de exibição do relatório ou artefato completo com filtros — `DECISION_REQUIRED` para próxima rodada.

### 15.G — Registro desta rodada (append-only)

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R15 | motivo | F7G010 + `E5_MOTBX` | PROVEN: rótulos são siglas F7G via motivo do movimento SE5 | resolve dúvida G4 de coluna |
| C2-R16 | C2-04 pagar | universo SE5↔SE2 + dedup | PROVEN: `DISTINCT(título,data,motivo)`=948 exato; NOR/FAT exatos; DEB/CMP/DAC divergem → INCONCLUSIVE motivo | suporta G5 parcial |
| C2-R17 | C2-04 receber | universo SE5↔SE1 | PROVEN: 657 row-level exato | suporta G5 parcial |
| C2-R18 | — | doc 47 | `NO_GATE_CHANGE`: falta binding campo→coluna do relatório e artefato oficial de comparação | — |

---

## 16. CICLO 2 — Execução Rodada 4 (CF-C2-EXEC-004) — paridade por registro

> Mesmo canal read-only autorizado. Objetivo: testar se o universo SE5 reproduz funcionalmente os relatórios oficiais — não aceitar coincidência de contagem como equivalência.

### 16.A — Parâmetros oficiais descobertos no dicionário SX1 — PROVEN

- **FINR190 (grupo `FIN190`)**: 42 parâmetros documentados em `SX1010`, incluindo `Da/Até data de baixa` (01–02), `Do/Até Banco` (03–04), `Da/Até Filial Origem` (33–34 — **confirma `FILORI`/`E5_FILORIG` como eixo de filial**) e **`42: "Cons. Bx. por mov. bancaria ?"`** — confirma oficialmente que o relatório considera baixas por **movimento bancário (SE5)**.
- **DLP06R01**: nenhum grupo SX1 correspondente (`DLP06*`/`%6R0%` ausentes — há DLP001–035 e DLP05R01/02, DLP10R03, DLP34R01, DLP73R01). Parâmetros da customização não persistidos no dicionário → `BLOCKED`, owner TI.
- **Preenchimentos efetivos** usados na geração dos artefatos do Ciclo 1 não são recuperáveis via SQL (SX1 guarda definições, não a última execução) — `BLOCKED`.

### 16.B — Pagar: reconstrução funcional do universo 948 — PROVEN (estrutura), residual ±2

Pipeline reproduzido com evidências de campo:

1. `SE5010`, `E5_RECPAG='P'`, `E5_DATA` em 09/2026 → 1.126 movimentos.
2. Join ao título SE2 (chave `PREFIXO+NUMERO+PARCELA+TIPO+FORNECE+LOJA`, many→1, sem fan-out) → **996 com título / 130 sem título** (DH=84, TR=30, PA=8, ES=7, VL=1 — movimentos bancários avulsos, corretamente fora da relação de baixas).
3. `E5_DTCANBX=''` (baixa não cancelada) → **957**; todos os 39 cancelados vinculados têm cancelamento no próprio mês.
4. `E5_TIPODOC ∈ {VL, BA, CP, PA}` → **950** (exclui CM/ES/DC/MT residuais).

Distribuição por `E5_MOTBX`×`E5_TIPODOC` no conjunto resultante vs artefato oficial:

| Motivo oficial | Artefato | Reconstruído | Δ |
|---|---|---|---|
| DEB | 600 | 600 (VL) | **0** |
| CMP | 186 | 188 (BA94+CP94) | −2 |
| FAT | 83 | 83 (BA) | **0** |
| NOR | 65 | 65 (PA) | **0** |
| DAC | 14 | 14 (BA) | **0** |
| **Total** | **948** | **950** | **−2** |

- **4 de 5 motivos reproduzem exatamente** (DEB, FAT, NOR, DAC) e o total diverge por 2 eventos CMP. O `DISTINCT(título,data,motivo)=948` da rodada 3 era **coincidência aritmética** — corrigido: o mecanismo real é exclusão de cancelados + filtro de tipos de documento, não deduplicação (dedup sobre ativos daria 924).
- Residual CMP−2: não encontrado flag discriminante (`E5_TIPOLAN`/`E5_SITUACA`/`E5_LA` uniformes). Hipóteses não testáveis sem artefato: filtro de banco (params 03–04), linhas geradas após a data de emissão do artefato, ou regra interna do programa. `INCONCLUSIVE` ±2, `TO_INVENTORY`.
- `E5_TABORI` registra a origem do movimento: `FK2`=931, `FK5`=65 — **todos os NOR (65) vieram de FK5** (baixa por movimentação bancária direta, não por baixa de título). Isso fecha a semântica NOR='NORMAL' vs evento FK2.
- `E5_FILORIG` está preenchido no SE5 (01=563 / 02=433) — eixo de filial disponível também no movimento bancário.

### 16.C — Receber: universo 657 — PROVEN (row-level)

- SE5 'R' × SE1 em 09/2026 = **657 linhas exatas**, grão movimento (inclui 1 linha com `E5_DTCANBX` preenchido — DLP06R01 aparentemente não filtra cancelamento, ou o artefato antecede o cancelamento).
- Os 8 movimentos que diferenciam 657 linhas de 649 combinações distintas: **4 grupos (título,dia,motivo) com 2 linhas de `E5_TIPODOC` diferentes** (ex.: VL+JR do mesmo título no mesmo dia) — linhas funcionalmente distintas (juros/encargos vs valor principal), não duplicatas. Confirma grão **row-level** para o produtor de receber.
- Assimetria de grão P (título×dia×tipo consolidado) vs R (movimento) é consistente com produtores distintos: FINR190/`_F190C` × `DLP06R01`.

### 16.D — Baixas parciais e cardinalidade — PROVEN

- Join SE5→SE2: cada movimento casa ≤1 título (0 fan-out; 130 movimentos sem título = avulsos).
- 53 títulos pagos com ≥2 movimentos ativos no mês (máx. 14) → baixas parciais existem no grão de movimento; o relatório por linha de movimento as representa nativamente.
- Tratamento de estorno: `E5_DTCANBX` (data de cancelamento da baixa) — preenchido em 41 movimentos P de 09/2026, todos cancelados no próprio mês.

### 16.E — Correção de precisão sobre SB9/`I_N_S_D_T_`

- Refinando §14.A: `I_N_S_D_T_` prova o **timestamp de inserção física** da linha no banco — não prova qual rotina/job a inseriu nem sua hora de agendamento. A defasagem de 19 dias da filial 01 é fato; a **causalidade** (job específico, schedule ou gatilho manual) permanece hipótese/TO_INVENTORY. Nenhuma conclusão da rodada 2 é invalidada; apenas o escopo da prova é delimitado.

### 16.F — Confronto monetário — BLOCKED

- Artefatos do Ciclo 1 são sanitizados sem totais monetários → comparação de `ΣE5_VALOR`/componentes (juros, desconto, abatimento) não é executável. `BLOCKED` até artefato com totais ou autorização para amostra.

### 16.G — Registro desta rodada (append-only)

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R19 | produtor | SX1 `FIN190` + `E5_TABORI` | PROVEN: relatório usa movimento bancário (param 42), filial origem (params 33–34); origem FK2/FK5 nos dados | G3/G4 parcial |
| C2-R20 | pagar | pipeline SE5→SE2 + DTCANBX + tipodoc | PROVEN estrutura: 950 vs 948, 4/5 motivos exatos; residual CMP−2 sem flag discriminante | G5 parcial |
| C2-R21 | receber | SE5→SE1 row-level | PROVEN: 657 exato; 8 surplus = linhas distintas por tipodoc | G5 parcial |
| C2-R22 | — | doc 47 | `NO_GATE_CHANGE`: confronto monetário bloqueado (artefatos sem totais); G5 exige linha-a-linha com artefato | — |

## §17 — RODADA 5 (CF-C2-EXEC-005) — CRUZAMENTO FONTES TOTVS × SQL — 2026-10-23

Base do cruzamento: `docs/13-fontes-totvs-protheus/` (acervo DELPI versionado em `0df96daafe`) × produção via `delpi-api-delpi` (conta read-only). **Caveat permanente:** fonte disponibilizado ≠ versão compilada no RPO de produção.

### 17.A — Fontes localizados no acervo — PROVEN

| Alvo | Achado | Status |
|---|---|---|
| FINR190 | `06. Financeiro/FINR190/FINR190_DLP.PRX` (2.580 linhas, custom DELPI do padrão) | **PROVEN — lido** |
| FINR130 | `finr130_dlp.prx` + `FINR130D.PRX` — é relação de **títulos SE1** (emissão/vencimento), não baixas | Lido — não é o produtor do artefato |
| MATR320 | `04. Estoque/MATR320/Dmatr320.prx` — relatório "Resumo de entradas e saídas" (não job SB9) | Lido |
| MATA330 hook | `04. Estoque/MA330OK.PRW` — ponto de entrada do Refaz Saldos; dispara `EXEC STP_DELPI_OP_TERCEIRO_01` e `STP_PROTHEUS_DELPI_AJUSTA_OP` (filiais 01/02) | **PROVEN — evidência de job** |
| DLP06R01 | **ausente do acervo** (grep em todo o pacote) | `BLOCKED` → owner TI |
| MATR460 (P7) | **ausente do acervo** | `BLOCKED` |

### 17.B — FINR190_DLP: regra oficial de seleção — PROVEN (código)

`INSERT INTO NEWSE5` (linhas ~1040–1170) + `Fr190TstCond` (564–628) definem o universo oficial:

```
SE5.D_E_L_E_T_=' '
AND E5_RECPAG='P'                                   -- lado pagar (MV_PAR11=2)
AND E5_DATA BETWEEN par01 AND par02                 -- competência
AND E5_MOTBX<>'DSD' AND E5_MOVCX<>'S'
AND E5_SITUACA NOT IN ('C','E','X')
AND NOT EXISTS (par de estorno E5_TIPODOC='ES', E5_ORIGEM<>'FINA100', mesma chave)
AND E5_HISTOR NOT LIKE '%Baixa Automatica / Lote%'  -- STR0077
AND E5_TIPODOC NOT IN ('DC','D2','JR','J2','TL','MT','M2','CM','C2','ES','E2'[, 'CB' p/ R])
+ E5_DTCANBX vazio (cancelamento — via Fr190MovCan/TstCond quando PAR16=1)
+ ranges parâmetros: banco 03–04, natureza 05–06, clifor 07–08, dtdigit 09–10,
  lote 20–21, loja 22–23, prefixo 26–27, filial origem 33–34 (E5_FILORIG)
```

Células do relatório são `SE5.E5_*` diretamente (E5_MOTBX, E5_DATA, E5_FILORIG etc.) — **grão row-level de movimento bancário**, sem dedup por título.

### 17.C — Reprodução SQL do WHERE oficial — PARIDADE ESTRUTURAL pagar — PROVEN (população + motivo + regra candidata)

Aplicado o WHERE do código (+ vínculo a título SE2 ativo) sobre produção, 09/2026:

| Motivo | Artefato oficial | WHERE oficial reproduzido | Δ |
|---|---|---|---|
| DEB | 600 | 600 | **0** |
| CMP | 186 | **186** | **0** |
| FAT | 83 | 83 | **0** |
| NOR | 65 | 65 | **0** |
| DAC | 14 | 14 | **0** |
| **Total** | **948** | **948** | **0** |

**5/5 motivos exatos + total exato + grão exato.** O residual CMP−2 da rodada 4 está **resolvido**: exatamente 2 linhas CMP possuem par de estorno `E5_TIPODOC='ES'` na mesma chave (probe `cmp_es_pair`=2; demais cláusulas isoladas=0). A exclusão `NOT EXISTS estorno-ES` era a regra faltante.

**Classificação desta paridade (delimitada):** demonstrada a paridade de **população** (948 linhas), **distribuição por motivo** (5/5 exatos) e **regra candidata do fonte** (WHERE do `FINR190_DLP` reproduz fielmente o artefato). **Não demonstrada**: paridade monetária por coluna/linha, paridade por registro (identidade de cada linha vs artefato — artefato sanitizado sem payload) e comprovação de que o fonte do acervo é a versão efetivamente compilada no RPO de produção.

Sem vínculo de título o WHERE oficial produz 1.059 linhas (111 com motivo em branco = movimentos manuais/avulsos) — o artefato conta apenas baixas com título, ou o operador filtrou motivo≠blank.

### 17.D — Receber — produtor confirmado como NÃO-FINR190 — PROVEN

- WHERE oficial 'R' (+ `CB` na lista de exclusão): **690** sem vínculo; **649** com vínculo SE1 — nenhum bate 657.
- População do artefato (657) = SE5 'R' × SE1 **sem** as exclusões do FINR190 (inclui linhas JR×3, MT×3, VL×1, DC×1 que o relatório padrão removeria + 1 cancelada).
- Distribuição `E5_TIPO` das 657: NF=648, NCC=6, RA=2, BOL=1 — coerente com artefato.
- Conclusão: produtor de receber é custom simples (grão movimento, filtros mínimos) — consistente com `DLP06R01`, cujo fonte **não está no acervo** → identidade do produtor `BLOCKED` (owner TI).

### 17.E — Outros achados de código

- `MV_PAGANT='F'` e `MV_CPNEG` ausente no SX6 → filtro PAR24 de CMP-antecipação inerte nesta instalação (não era a regra do residual).
- `E5_SITUACA` das 39 canceladas: ''(33)/'C'(6) → cancelamento é efetivamente `E5_DTCANBX`, não situação.
- Tabelas custom `MP7*` existem no banco (`MP7_01_01`, `MP7_052019`, `MP7F01_202402`…) — candidatas a staging de P7; `TO_INVENTORY` para rodada dedicada.
- SPs `STP_DELPI_OP_TERCEIRO_01`/`STP_PROTHEUS_DELPI_AJUSTA_OP` não localizadas no DB DELPI (outra base ou removidas) — código das SPs `BLOCKED`.
- `Dmatr320`/`finr130_dlp` são customizações de relatórios operacionais (sem relação com SB9/P7).

### 17.F — Registro desta rodada

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R23 | fontes | inventário acervo vs alvos | PROVEN: FINR190_DLP/FINR130/MATR320 lidos; DLP06R01 e MATR460 ausentes | G4 fonte |
| C2-R24 | pagar | WHERE oficial reproduzido em SQL | **PROVEN estrutural: 948 exato, 5/5 motivos, grão row-level, regra candidata do fonte**; CMP−2 explicado por par estorno-ES; monetário/por-registro/versão-RPO pendentes | G5 estrutural |
| C2-R25 | receber | mesma reprodução lado R | PROVEN: artefato não segue filtros FINR190 (649/690≠657); produtor custom não-arquivado | G5 parcial |
| C2-R26 | SB9 job | MA330OK hook | PROVEN indireto: PE pós-MATA330 existe e chama SPs; causalidade do job segue hipótese | — |
| C2-R27 | — | doc 47 | `NO_GATE_CHANGE` parcial: paridade de **população+distribuição+regra** provada para pagar, mas artefato oficial continua sem totais monetários/linhas → confronto linha-a-linha pendente | — |

### 17.G — Continuação rodada 5 (pós-ajuste documental) — MP7*, DEL100 e demais residuais

- **Tabelas `MP7*` = exports manuais de P7**, não rotina produtora: `PRODUTO/ARMAZEM/DATAFECHAMENTO/NOMEARQ/TIPOMOV/QUANTIDADE/TOTAL`, criadas 2020–2024 (ex.: `MP7_05_01`=1.223 linhas @20231231; `MP7F01_202402`=712k linhas 2021–2024 filial 01; `MP7_052019` layout distinto CODIGO/QTD/VLR). `MP7_01_01`/`MP7_01_02` vazias.
- **Teste de paridade MP7×SB9 @20231231 — `INCONCLUSIVE`**: só 155/1.223 linhas de `MP7_05_01` casam por produto×armazém com `SB9010.B9_DATA='20231231'` filial 01; totais divergem (q 5,56M vs 4,84M; v 2,29M vs 3,32M). Não prova nem refuta P7≡SB9 — escopo/filtros da exportação são desconhecidos (não há parâmetros nem rotina associada). Registrado como export ad-hoc, `TO_INVENTORY`.
- **`DEL100.PRW` decodifica a semântica do SB9 — PROVEN (código)**: rotina custom "Recalculando Fechamentos" que valida `B9_VINI1`/`B9_QINI` recomputando: saldo do fechamento anterior + SD3 do período (`D3_TM<'500'` entrada / `≥'500'` saída, ignorando `D3_ESTORNO='S'`) + SD1 (`F4_ESTOQUE='S'`) − SD2. Compara com SB9 na data fim e, com `lAlterar`, **corrige via RecLock** — evidencia que snapshots SB9 podem ser corrigidos retroativamente. Criação da linha SB9 não acontece aqui (ausência apenas gera log tipo "3") — produtor das linhas segue apontando para MATA330/rotina standard.
- **`MA330OK.PRW`**: ponto de entrada pós-MATA330 que executa `STP_DELPI_OP_TERCEIRO_01` e `STP_PROTHEUS_DELPI_AJUSTA_OP` (filiais 01/02) — confirma que o Refaz Saldos roda com hooks DELPI; as SPs não existem no DB DELPI (outra base/removidas) → código `BLOCKED`.
- **`DLP06R01` continua ausente**: `DLP06F01/02/03`, `FA750BRW` (botões de borderô PIX) e `DLPXFIN1` (wrapper FINA717) são helpers não relacionados a relatório de baixas. Produtor do artefato de receber permanece `BLOCKED` → owner TI (ou confirmar se é o FINR190 padrão executado com parâmetros mínimos — ver nota).
- **Nota metodológica receber**: a população 657 = SE5 'R'×SE1 cru também é reproduzível pelo FINR190 se os parâmetros de exclusão estivessem desligados — porém o FINR190 sempre aplica `E5_TIPODOC NOT IN (...)` fixo no código, então o conjunto fixo torna DLP06R01/outro executor a explicação mais plausível. `INCONCLUSIVE` até fonte/parâmetros.
- **SH6 (MOD)**: consumidores custom identificados no acervo (`10. PCP`: `PApPosAp`, `matr895`, `DLP10G03`, `MA680INC`, `MT685LOK`, `MT680VAL`, `MOBILE/PAPGETOP`) — cadeia MOD tem candidatos de relatório custom para rodada dedicada. `TO_INVENTORY`.
- **FINR150**: `finr150_dlp.prx` presente no acervo (cheques) — não relacionado aos artefatos do ciclo.

---

## §18 — RODADA 6 (CF-C2-EXEC-006) — ESTOQUES, CUSTOS E MOD — 2026-10-23

Cruzamento fontes DELPI (`docs/13-fontes-totvs-protheus/`) × SQL read-only × artefatos. Sem alteração de runtime/dados.

### 18.A — DEL100 × SB9: fórmula, granularidade e correção — PROVEN (código) / divergência de dados

**Parâmetros (TPergunta `DEL100`, grupo SX1 com 48 entradas registrado):** Data Fechamento, De/Ate Produto, De/Ate Local (default 01–99), Modo Execução (1=Alteração, 2=Somente Log).

**Janela:** valida `B9_DATA=par01` existente e deriva `dDataIni` = data do snapshot **anterior** (índice 2 do SB9) — encadeamento de fechamentos.

**Granularidade:** produto × armazém, por filial (`xFilial` em cada área).

**Fórmula recomputada (linhas 84–145):**
```
calc = B9_VINI1/B9_QINI @dDataIni
     + SD3 (D3_ESTORNO<>'S'; D3_TM<'500' entra / D3_TM>='500' sai; eixo D3_EMISSAO; D3_CUSTO1/D3_QUANT)
     + SD1 (TES com F4_ESTOQUE='S'; eixo D1_DTDIGIT; D1_CUSTO/D1_QUANT)
     − SD2 (TES com F4_ESTOQUE='S'; eixo D2_EMISSAO; D2_TOTAL/D2_QUANT)
```
Compara com SB9 @dDataFim; com modo Alteração **corrige via `RecLock`** (`B9_VINI1`, `B9_QINI`). Ausência de linha SB9 no fim gera log tipo "3" — **não cria** snapshot.

**Capacidade vs execução:** a capacidade de correção retroativa existe no código; execução efetiva **não é observável via SQL** (sem trilha de execução). `TO_INVENTORY` → owner ERP.

**Validação SQL da fórmula (filial 02, 20260831→20260930) — `INCONCLUSIVE`/divergente:**
- 3.545 chaves produto×armazém no universo investigado; **428 sem linha SB9 no fechamento** — diferença de cobertura do universo investigado (elegibilidade dessas chaves para snapshot **não demonstrada**; podem não ser elegíveis — Rodada 7 investiga);
- 523 linhas com diferença de valor (>R$1; Σ|Δ|=4,98M) e 290 com diferença de quantidade (Σ|Δ|=9,08M) **entre a reconstrução SQL e o SB9 observado** — diferença registrada sem conclusão causal: não demonstrado se decorre de nuance da fórmula (TES, custo de retorno, filial SF4), de correção posterior, ou da reconstrução SQL;
- Não concluído que DEL100 seja aproximada/errada nem que seja a regra do produtor SB9 — ambas as hipóteses abertas (`INCONCLUSIVE`).

### 18.B — MATR320/MATA330/P7: produtores e consumidores

- **`Dmatr320.prx`** (custom de MATR320, "Resumo das entradas e saídas"): seção `{"SB1","SD1","SD2","SD3"}` — lê **SD3 por `D3_EMISSAO`** (filtros `D3_ESTORNO<>'S'`, TES/serviço) — relatório de movimentação do período, **não consome nem produz SB9**.
- SX1: sem grupo MATR320; existem `MATA317` (6 params), `MATR325` (4) e **`DEL100` (48)**. MATR460 (P7) não tem grupo SX1 no acervo nem fonte.
- `MA330OK` (PE do MATA330) segue como única evidência de processo upstream de fechamento (dispara SPs custom por filial); criador das linhas SB9 **não comprovado**.

### 18.C — MP7*: origem e granularidade — PROVEN ad-hoc

- `NOMEARQ` = nomes de spool (`SCGN000xxx`) e `TIPOMOV` = nomes de **variáveis internas** (`aSalAtu`, `QtCus`, `aDadosCF9`) → são **dumps de arrays de execução**, não exports curados do relatório P7 oficial.
- Coberturas heterogêneas por arquivo (datas 2021–2024, 1–40 datas, armazéns variáveis) → universos **não comparáveis** a SB9 sem os parâmetros da exportação. Paridade MP7×SB9 permanece `INCONCLUSIVE`; decisão: **não usar MP7 como proxy do P7 oficial**.

### 18.D — Faturamento × MOD: consumidores SH6 e cadeia de custo

- **`matr895`** (Real × Previsto, fonte TOTVS no acervo): seção sobre `SH6+SC2+SB1+SH1+SH4+SG2`; join OP via `SUBSTR(H6_OP)` em `C2_NUM/C2_ITEM/C2_SEQUEN`; divisor de tempo padrão `SH1.H1_MAOOBRA`; células `HoraPrev`/`HoraReal`, `H6_QTDPROD`/`H6_QTDPERD`.
- **`DLP10G03` (custom)**: calcula eficiência `=(G2_TEMPAD×H6_QTDPROD + setup)/H6_TEMPO×100` e **grava `H6_ZEFICI`** (campo custom) — campo preenchido em 308.865/457.954 linhas SH6 (67%); o preenchimento prova que **algum** produtor grava o campo, **não** que esta versão específica do `DLP10G03` executou em produção (fonte ≠ RPO compilado).
- **`PApPosAp`**: ponto de entrada que normaliza `H6_OP`/desdobramento de OP.
- **Custo MOD — associação comprovada no recorte consultado**: `SH1` não tem custo monetário (`H1_MAOOBRA`, `H1_CCUSTO`, `H1_GCCUSTO`, `H1_MODFAT`); `SH4.H4_CUSTOH` existe mas está **zerado** nas 529 ferramentas consultadas. Cobertura SH6→SH1 em 09/2026: **100%** dos 13.886 apontamentos com recurso válido e `H1_CCUSTO` preenchido → associação SH6→recurso→centro de custo **comprovada no recorte**; generalização para a regra monetária de rateio MOD permanece `TO_INVENTORY` (fórmula rate × horas não demonstrada).
- Escala: SH6 = 457.954 apontamentos; set/2026 = 13.886 (55 recursos, 1.688 produtos).

### 18.E — Recebíveis: DLP06R01 — pendência mantida

Sem novas evidências no acervo; produtor permanece `BLOCKED` → owner TI. Nenhuma consulta repetida.

### 18.F — Registro desta rodada

| Run | Item | Ação | Resultado | Gate |
|---|---|---|---|---|
| C2-R28 | DEL100 | leitura integral + SX1 | PROVEN: fórmula, granularidade, correção RecLock; capacidade≠execução | G4 fonte |
| C2-R29 | SB9 fórmula | recompute SQL f02 0831→0930 | DIVERGENTE: 428 chaves sem linha fim (elegibilidade não demonstrada); 523 Δvalor / 290 Δqtd reconstrução×SB9 — causa aberta | — |
| C2-R30 | MATR320 | leitura Dmatr320 | PROVEN: consome SD3+SB1 (mov. período); não produz SB9 | — |
| C2-R31 | MP7* | perfil NOMEARQ/TIPOMOV | PROVEN: dumps de arrays de execução, não P7 oficial | — |
| C2-R32 | MOD | matr895/DLP10G03/PApPosAp + links SH6 | PROVEN (recorte): associação SH6→H1_CCUSTO 100%; H4_CUSTOH zerado; H6_ZEFICI preenchido (produtor não identificado) | G4 fonte |
| C2-R33 | — | doc 47 | `NO_GATE_CHANGE` | — |
