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
