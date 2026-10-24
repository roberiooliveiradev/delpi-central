# 80 — PROC-0072 | Registro vivo de investigação técnica do Ciclo 2 — Devin

> **Criado:** 23/10/2026. **Produto:** Portal Controladoria & Finanças / Central de Fechamento. **Natureza:** template operacional **DOCUMENTATION_ONLY**, destinado a preenchimento progressivo pelo Devin após GO de investigação específico. **Não é ordem de execução, nem aprovação de SQL, nem autorização de runtime.**

## 0. Instruções de uso e fonte de verdade

- **Este documento é o ponto de entrada e índice vivo** do Ciclo 2. O [doc 47](./47-t01-report-column-audit-tracker-v1.md) **continua sendo a authority dos seis gates G1–G6, R01–R15, denominadores e percentuais**. Não duplicar status de gate como segunda authority. Se houver evidência nova, registrar aqui e atualizar o doc 47 na mesma rodada, sem promover PASS por antecipação.
- O Ciclo 1 é `PO_ACCEPTED_WITH_RESIDUAL` conforme [doc 79](./79-ciclo1-aceite-formal-po.md). O [doc 78](./78-ciclo1-crosswalk-narracao-artefatos.md) cruza V01–V23 com os artefatos. [Docs 56](./56-proc0072-observacoes-guiadas-fechamento-custos.md) e [57](./57-proc0072-matriz-mestra-revalidacao-video-e-roadmap-inventarios.md) preservam a narração completa fornecida pelo PO; não solicitar nova narração.
- **Estado inicial:** `CYCLE_2_GO=NO`; `INVESTIGATION_NOT_STARTED`; `ERP_PARITY=TEST_NOT_RUN`. Inventários/probes prévios dos docs 47–49 não equivalem à execução deste ciclo.
- Identidade congelada: plugin `controllership-finance`, MFE `plugins/controllership-finance`, `/apps/controllership-finance`; BFF `controllership-finance-api`, `/apps/controllership-finance-api`; somente `controllership-finance.access` e `controllership-finance.manage`.
- TÉO/<GESTORA-PROC> = AS-IS/proveniência; GitHub HEAD = TARGET/contratos/código; Core = identidade/RBAC/effective permissions; api-delpi = owner de SQL e semântica TOTVS; strategic-indicators-api = indicadores. MFE comunica-se somente com BFF. Não compartilhar banco ou importar domain/application de outro contexto.
- **Regra de confidencialidade:** jamais versionar planilhas, PDFs, MP4, prints, linhas, valores, CPF/CNPJ, clientes, fornecedores, produtos, títulos, pedidos, credenciais, hashes de fontes privadas ou queries contendo identificadores reais. Apenas metadados genéricos, relações, lógica sanitizada, estados e referências técnicas aprovadas. Evidência operacional sensível fica sob custódia autorizada FORA do GitHub; registrar referência abstrata e acessos aprovados, sem endereço secreto ou token.
- **Edição concorrente:** revalidar HEAD e blob SHA do arquivo imediatamente antes de cada alteração. Preferir um commit pequeno por lote, sem sobrescrever resultados de outros agentes. Se divergência concorrente, parar, reconciliar e repetir o fetch; nunca force-push. Histórico é *append-only* nos registros de execução; correção cita registro anterior e motivo.
- Não marcar `PASS` por HTTP 200, schema encontrado, screenshot, nome de rotina ou teste isolado. `search miss != ausência`.

- **GATE TRANSVERSAL OBRIGATÓRIO — REUSO DE REGRAS E CONTRATOS EXISTENTES (R01–R15):** antes de nova investigação física, classificação de regra no doc 85, proposta de contrato/rota ou conclusão de ausência de capacidade, **pesquisar efetivamente no HEAD** os producers, consumers, serviços, endpoints, consultas, casos de uso e testes **já existentes** em (a) Suprimentos e suas APIs/portais, (b) api-delpi, (c) demais contextos Minha DELPI pertinentes; confrontar com as instruções oficiais, padrões de projeto em `docs/11-padroes-de-desenvolvimento/`, `.cursor` aplicáveis, ADRs/contratos canônicos e documentação vigente do processo. Começar por inventário direcionado do código e dos contratos — **não iniciar outro levantamento geral de regras nem duplicar implementação**. Busca sem resultado não prova inexistência: ampliar paths, símbolos, aliases e consumidores antes de declarar `TO_INVENTORY`.
- **Registro mínimo obrigatório da verificação de reuso, por item investigado:** indicar arquivos/símbolos e SHAs do HEAD consultados; owner/boundary; endpoint/contrato e consumers; fonte física e semântica quando existentes; testes; relação com Rxx e BR-Rxx (equivalente, parcial, divergente, não localizado); lacunas concretas e decisão aplicável. Referenciar regras existentes no **doc 85**, sem copiar ou criar catálogo paralelo. Quando a regra existente é canônica, avaliar reuso via contrato do respectivo owner; não mover SQL nem importar domain/application de outro contexto. Se houver escolha material de owner/contrato/semântica, retornar `DECISION_REQUIRED`; se autoridade já determinar resposta única, registrar a conclusão. Documentação isolada não prova runtime nem `CODE_DEPLOYED`.
- **Aplicação imediata R06/R07/CPV:** antes de chamar a medida CPV de indefinida ou propor nova fórmula, **localizar e confrontar o cálculo de CPV já apontado pelo PO como existente em Suprimentos e na API** com a regra de Protheus em api-delpi, seus consumidores e os movimentos do MATR910. Esta existência é **declaração do PO a verificar em HEAD**, não implementação já auditada nesta rodada. Manter separados (1) paridade das linhas/custos do Kardex e (2) semântica da medida CPV. As 11 linhas de custo de R06 ainda exigem verificação própria; não encerrar esse residual por analogia ao CPV. Não alterar gates por inserir esta diretriz.


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
| C2-01 | P0 | R03/R05/R08 | V11/V13/V17; RC-01/02 | 63/62/64/68 | MATR320 x P7 x H02 | <GESTORA-PROC> + ERP/api-delpi | D2 |
| C2-02 | P0 | R03 | V11; X03 | 63/68 | P7 integral x reduzido | Contabilidade + ERP/api-delpi | D2 |
| C2-03 | P0 | R06 | V12/V15; RC-04 | 61/67 | CPV Kardex 01 | Custos + ERP/api-delpi | D2 |
| C2-04 | P0 | R01/R02 | V07-V09; RC-09 | 69-75 | Baixas/compensações | Financeiro + ERP/api-delpi | D3 |
| C2-05 | P1 | R07 | V12/V14; RC-03 | 61/66 | Inventário 01/99 | Estoque + ERP/api-delpi | D2 |
| C2-06 | P1 | R09 | V05/V16; RC-05 | 65 | Faturamento x MOD | Custos + PCP + ERP/api-delpi | D4 |
| C2-07 | P1 | R12 | V01/V10 | 77 (Análise) | Custo médio e jobs | <GESTORA-PROC> + ERP/api-delpi | D4 |
| C2-08 | P1 | R10 | V20-V22; RC-06 | 77 (CC matriz) | Despesas e CC/SD1 | Controladoria + Contabilidade + ERP/api-delpi | D4 |
| C2-09 | P1 | R13/R14 + checklist | V18/V19 | 59/60 | Entregas e fontes externas | <GESTORA-PROC> + Contabilidade + PO | D4 |

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
- **Status de jobs/rotinas Protheus (Refaz Saldos, Acompanha Custos, MATR320 schedule) não é consultável via SQL** — depende do owner ERP / observação assistida. `DECISION_REQUIRED`/owner <GESTORA-PROC>+ERP.

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

---

## §19 — RODADA 7 (CF-C2-EXEC-006 continuação) — ELEGIBILIDADE SB9, DIVERGÊNCIAS E REGRA MOD — 2026-10-23

### 19.A — As 428 chaves sem linha SB9: elegibilidade demonstrada empiricamente

Decomposição das 428 chaves (filial 02, janela 20260831→20260930):

| Classe | n |
|---|---|
| Com snapshot anterior, **saldo zero, sem nenhum movimento** na janela | **402** |
| Somente movimento (sem snapshot anterior) | 26 |

- **Padrão empírico de elegibilidade — `PROVEN` no recorte:** 100% das chaves prior-zero sem snapshot não tiveram movimento; e das chaves prior-zero que receberam snapshot (2.814), 2.781 (98,8%) tiveram movimento SD3. Regra implícita observada: **saldo zero + sem movimento → sem snapshot novo**. As 33 exceções prior-zero→fim-sem-SD3 têm saldos não-zero no fim (provável movimento por perna SD1/SD2 não medida nesse recorte — `TO_INVENTORY` residual).
- Perfil das 428: concentradas no armazém 01, tipos PI(167)/PA(65)/II(36)/MO(26 sem SB2)/MC(27); 69 em armazéns 98/99/50 (MP). Todas com linha SB2 exceto as 26 de movimento.
- **Conclusão corrigida:** as 428 são diferença de cobertura do universo investigado com explicação de elegibilidade demonstrada — **não** incompletude do fechamento.

### 19.B — Divergências reconstrução×SB9: padrões identificados

Recontagem com as três pernas completas (join `F4_ESTOQUE='S'` em SD1/SD2 e `B9_FILIAL/B9_LOCAL` coerentes): **724** divergências de valor e **672** de quantidade (a contagem 523/290 da R6 usava formulação parcial — número corrente é o completo; a divergência em si não mudou de natureza).

| Padrão (valor) | n | Interpretação |
|---|---|---|
| `sb9_v == prior_v` exato ("congelado") | 224 | snapshot final repetiu o valor anterior — movimentos não refletidos |
| `sb9_v = 0` | 266 | snapshot zerado apesar de saldo/movimento calculado |
| demais | 234 | diferenças mistas |

- **Hipótese TM999 excluída — REJEITADA:** recomputar sem `D3_TM='999'` piora divergência (724→1.470) — TM999 (transferência/dev. poder 3) **está** refletida nos saldos SB9.
- Amostras mostram também o padrão `calc` incluindo pernas SD3 de armazéns 98/99 (CQ) que o SB9 parece não incorporar — nuance de escopo por armazém `TO_INVENTORY`.
- Causa das divergências permanece `INCONCLUSIVE` (fórmula×correção×escopo); código DEL100 não falsificado.

### 19.C — MOD: regra monetária identificada no acervo

`matr860.prx` (MATR860 "Análise de OP", fonte no acervo) prova a mecânica:
- Flag `ISMOD` = `B1_COD LIKE 'MOD%'` ou `B1_CCCUSTO<>' '` — **MOD é materializada como produto** (143 produtos `MOD*`, tipo `MO`, UM majoritária `HR`/`H` = horas).
- "Qtd./Custo Mão de Obra" = Σ `D3_QUANT`/`D3_CUSTO1` sobre requisições (`D3_CF='RE*'`/`'DE*'`) do produto-MOD contra a OP.
- Produção set/2026: 6.507 (f01) + 6.821 (f02) movimentos MOD `RE1`/`TM999` com **`D3_CUSTO1=0`** — as horas apropriadas não carregam custo no estoque.
- **Cadeia MOD consolidada:** SH6 aponta horas → requisição MOD em SD3 (quantidade=horas, custo=0, `D3_OP` vinculada à OP — matches em SH6 confirmados) → custo monetário apropriado **fora do estoque** (contábil/centro de custo — `CTT_CUSTO` é código de CC hierárquico, não rate). Fórmula monetária (rate×horas e lançamento contábil) permanece `TO_INVENTORY` → rotina de apuração contábil/PCP não localizada no acervo.

### 19.D — P7: inventário ampliado

- SX1 **não tem nenhum grupo `MATR4%`** — MATR460/P7 oficial não tem parâmetros registrados nesta base → produtor oficial provavelmente custom/job.
- Workfiles `TRB010` (12.799 linhas residuais @20111231: SD3/SD2/SD1, f01) e variantes `TRB*_SPMATA280`/`_36SP` confirmam uso histórico de TRB por rotinas de saldo — resíduo antigo, não prova de produtor atual.
- `MP7*` reafirmado ad-hoc; nenhuma paridade tentada (universo não comparável).

### 19.E — Pendências atualizadas

- `DLP06R01`: `BLOCKED` (owner TI) — sem novidades.
- Produtor linhas SB9: padrão de elegibilidade demonstrado, identidade do job `BLOCKED`.
- MOD monetário: rate/fórmula de apropriação `TO_INVENTORY`.
- Divergências reconstrução×SB9: `INCONCLUSIVE` — próximos passos: isolar perna dominante por amostra e armazéns 98/99.
- Doc 47: `NO_GATE_CHANGE`.

### 19.F — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R34 | 428 chaves | PROVEN (recorte): 402 saldo-zero+sem-mov; elegibilidade empírica | G4 fonte |
| C2-R35 | divergências | 224 congelado/266 zero/234 mista; TM999 rejeitada; INCONCLUSIVE causa | — |
| C2-R36 | MOD | PROVEN: MOD=produto SD3 RE1/999, horas, custo=0; monetário via apropriação fora estoque | G4 fonte |
| C2-R37 | P7 | SX1 sem MATR4%; TRB resíduo 2011; MP7 ad-hoc | — |

---

## §20 — RODADA 8 (CF-C2-EXEC-008) — CAUSA DAS DIVERGÊNCIAS E APROPRIAÇÃO MOD — 2026-10-23

### 20.A — Decomposição das divergências: origem isolada na perna SD3 — `PROVEN` (recorte) — *revisado pós-rework*

Crosstab divergentes×armazém×perna (filial 02, 0831→0930): **todas as 724 chaves divergentes de valor possuem movimentos somente em SD3** (`com_sd1=0`, `com_sd2=0` no universo divergente). **Delimitação:** isso prova apenas que a diferença reconstrução×SB9 se concentra em chaves cujos movimentos são SD3; **não** prova que SD1/SD2 estejam integralmente corretas (podem coincidir por não haver movimento) nem que o produtor SB9 omita SD1/SD2.

Distribuição por padrão×armazém (valor, categorias disjuntas — `congelado` = |sb9−prior|<0,001 com precedência; `sb9_zero` = sb9=0 e não-congelado; `misto` = demais; **total = 724**):

| Armazém | congelado | sb9_zero | misto | n |
|---|---|---|---|---|
| 01 | 135 | 27 | 219 | 381 |
| 98 (QUALIDADE) | 47 | — | 18 | 65 |
| 99 | 42 | 17 | 219 | 278 |
| **total** | **224** | **44** | **456** | **724** |

- Correção de transcrição: a versão inicial da tabela copiou `com_sd3`(20) como `n` em 01/sb9_zero (n real=27) — somava 717; reconciliado acima.
- Nota de sobreposição: `sb9_v=0` ocorre em 266 chaves divergentes no total — 222 dos "congelados" têm prior=0 (logo sb9=0), por isso a contagem por condição (266) supera a categoria disjunta (44).

**Atribuição por TM (`PROVEN` recorte):** para cada chave divergente, o delta calcula-se exatamente por uma perna ausente:
- **135 chaves: delta = contribuição TM010/`PR0`** (entrada de produção) — o SB9 não incorporou o valor de produção nessas chaves;
- **93 chaves: delta = contribuição TM999/`RE*`** (requisições/dev. poder de terceiros) — idem;
- demais: combinações parciais.

Interpretação hipotética (`INCONCLUSIVE`): o produtor real pode aplicar regras de TM/CF diferentes da reconstrução (ex.: produção valorizada por outra via, poder-de-terceiros com escopo próprio) — ou as chaves foram corrigidas antes/depois de movimentos específicos. Não demonstrado qual; DEL100 segue não falsificado.

### 20.B — Elegibilidade: 26 e 33 resolvidas

- **As 26 chaves "somente movimento" são TODAS produtos `MOD*` (tipo `MO`, armazém 01)** — evidência empírica **consistente com** não-estocabilidade de MOD (horas movimentam SD3 sem gerar saldo). Não é declaração de regra formal do produtor SB9, ainda não identificado. `PROVEN` (observação), não `PROVEN` (regra).
- **As 33 chaves prior-zero→snapshot-sem-SD3:** 32 têm perna em SD1/SD2 (consistente com "movimento→snapshot"); **1 residual** (`<PRODUTO-RESIDUAL-A>`@99, `v_fim=15,75`) sem nenhuma perna localizada na janela (`TO_INVENTORY` menor — possível perna não medida ou ajuste direto).

### 20.C — Armazéns especiais

`NNR010`: 98=`ARMAZÉM QUALIDADE`, 50=`ARMAZÉM 50 - REJEIT`, 99=`Armazém 99`. SB9 @0930 cobre 01/99/98/50/03/25/00 — **não há exclusão de CQ por armazém** no snapshot; as divergências em 98/99 seguem o mesmo padrão de perna SD3.

### 20.D — MOD monetária: cadeia e vias descartadas

- `D3_CUSTO1` dos produtos `MOD*` = **zero em 2022–2026 inteiro** — MOD nunca é valorizado no estoque, em nenhum período. `PROVEN`.
- Recursos SH1 (`H1_CCUSTO`) mapeiam CCs cujos códigos **espelham os códigos MOD** (`MOD325`↔CC `325`, `MOD310`↔`310`, `MOD030101`↔`030101`…) — produto MOD é a ponte hora→centro de custo. `PROVEN` (correspondência estrutural).
- **CT2 nos CCs de MOD — ausência delimitada:** zero lançamentos `CT2010` encontrados para os **filtros, período (set/2026) e centros de custo examinados** (`CT2_CCD`/`CT2_CCC` ∈ amostra de CCs MOD). Não descarta outras vias contábeis não investigadas (rateio CCT/CT5, rateio por item/empresa, apuração fora do período ou por outras dimensões). `TO_INVENTORY`.
- Fórmula monetária (rate×horas, veículo de apropriação) permanece `TO_INVENTORY` → possíveis vias não esgotadas: CT5/CCT rateio, apuração externa, ou custo absorvido no produto acabado via estrutura.

### 20.E — Produtor SB9: assinatura de inserção em janela comum

`I_N_S_D_T_` @20260930: as 3.117 linhas da filial 02 inseridas na janela `2026-10-02 17h`; as 4.812 da filial 01 em `2026-10-21 19h` — **assinatura de inserção em janela comum por filial**, consistente com processamento em lote; **não prova um único job** (podem coexistir múltiplos executores na mesma janela) nem identidade. Identidade do(s) produtor(es) segue `BLOCKED` (MATA330/SPs custom hipótese não provada).

### 20.F — P7 / residuais

- Produtor oficial P7: sem grupo SX1 `MATR4%`; TRB resíduo 2011; MP7 ad-hoc — nada novo a provar, status mantido.
- `DLP06R01`: `BLOCKED` owner TI. Financeiro R5 intacto.
- Doc 47: `NO_GATE_CHANGE`.

### 20.G — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R38 | divergências | PROVEN: divergentes só com perna SD3; 135Δ=TM010, 93Δ=TM999; tabela reconciliada (724) | G4 fonte |
| C2-R39 | 26/33 | PROVEN (observação): 26=MOD consistente com não-estocável; 32/33=perna SD1/SD2; 1 residual | G4 fonte |
| C2-R40 | armazéns | NNR decodificado; SB9 cobre CQ/REJEIT | — |
| C2-R41 | MOD | custo SD3 zero histórico; MOD↔CC espelhado; CT2 ausente nos CCs/filtros examinados | G4 fonte |
| C2-R42 | produtor | inserção em janela comum por filial — assinatura observada, job único não provado | — |

---

## §21 — RODADA 9 (CF-C2-EXEC-008 continuação) — REGRA SB9 = SNAPSHOT DE SB2 + MOD — 2026-10-23

### 21.A — Identidade SB9↔SB2 — `PROVEN` (recorte)

Teste em chaves `SB9@20260930` sem **nenhum** movimento posterior (SD3/SD1/SD2 após 09-30) — nessas, o SB2 atual equivale ao SB2 no fechamento:

| Comparação com SB2 atual | n | % de 1.643 |
|---|---|---|
| `B9_QINI == B2_QATU` | 1.593 | 96,9% |
| `B9_VINI1 == B2_VATU1` | 1.576 | 95,9% |
| `B9_CM1 == B2_CM1` | 1.164 | 70,8% |
| quantidade **e** valor iguais | **1.575** | **95,9%** |

**Conclusão:** `SB9` é **snapshot mensal do saldo físico SB2** (qtd × custo médio armazenado em `B9_CM1`, consistente em 2.925/3.117 linhas: `B9_VINI1 ≈ B9_QINI × B9_CM1`). As divergências reconstrução×SB9 refletem diferença entre a **fórmula de acúmulo (DEL100/SQL)** e o **roll-forward real do SB2** — não defeito do snapshot. Isto reenquadra §18–§20: o SB9 provê o fechamento oficial do saldo físico; a reconstrução por movimentos é aproximação (faltam pernas de SB2: ajustes, transferências poder-de-terceiros e outras origens fora de SD3/SD1/SD2).

### 21.B — Hipóteses testadas e rejeitadas

- **Retroatividade — REJEITADA:** 0 dos 26.726 movimentos SD3 da janela foi inserido após o batch (`I_N_S_D_T_` ≤ 02/10 17h); remover retroativos não fecha nenhuma das 724 (`dv_fecha_sem_retroativos=0`).
- **TM999 excluída — REJEITADA** (rodada 8).

### 21.C — Anatomia das 724 por regra de fechamento do valor

| Regra que fecha `sb9_v` | n | tb. c/ Δqtd |
|---|---|---|
| `sb9_v == prior_v` (congelado) | 224 | 224 |
| `sb9_v == sb9_qq × uc_prior` | 113 | 112 |
| `sb9_v == 0` | 44 | 43 |
| outra | 343 | 285 |

- Custo unitário armazenado (`B9_CM1`) das divergentes: **164 == CM anterior**; **332 == CM da reconstrução**; 4 zero. Quando CM coincide, o delta de valor = Δquantidade × CM — **a divergência primária é de quantidade** (620/672 com qtd divergente vs 55 com só valor divergente).
- Consistente com SB9=SB2: SB2 pode divergir da soma de movimentos por ajustes/pernas não medidas; CM recalculado em ~46% das divergentes.

### 21.D — MOD monetária: caminhos esgotados nesta base

- `D3_CC` existe mas só **10/6.821** linhas MOD o têm preenchido — CC não viaja no SD3.
- `CT5010` (pares CCD/CCC de rateio): 194 linhas, todas vazias. `CTH010` (classe valor): 0 linhas.
- `CT3010.CT3_CUSTO`: só 9 linhas, todas de **2008** — lançamento por CC desuso.
- `CT2010` nos CCs de MOD set/2026: zero (delimitado, rodada 8).
- **Síntese:** apropriação monetária MOD **não ocorre** nas tabelas contábeis/CC desta base — consistente com absorção no custo do produto (CM via MATA330) ou apuração externa/planilha. `TO_INVENTORY` com vias documentadas esgotadas → owner ERP/Controladoria.

### 21.E — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R43 | SB9×SB2 | PROVEN (recorte): 96% identidade sem mov. posterior → SB9=snapshot SB2 | G4 fonte |
| C2-R44 | retroatividade | REJEITADA: 0 mov. pós-batch | — |
| C2-R45 | 724 decompostas | 224 cong/113 qtd×uc_prior/44 zero/343 outra; CM: 332=calc, 164=prior | — |
| C2-R46 | MOD vias | esgotadas nesta base (D3_CC, CT5, CTH, CT3, CT2) → TO_INVENTORY | — |
| C2-R47 | — | `NO_GATE_CHANGE` | — |

---

## §22 — RODADA 10 (CF-C2-EXEC-010) — VALIDAÇÃO SB9×SB2, PRODUTOR E PROVENIÊNCIA MOD — 2026-10-23

### 22.A — Classificação das 68 exceções SB9×SB2

População: 1.643 chaves `SB9@20260930` (filial 02) sem nenhum movimento posterior SD3/SD1/SD2; 68 divergem do SB2 atual (tolerância: `ABS(Δqtd)>0,0001` / `ABS(Δvalor)>0,01` — nenhum caso é mero arredondamento).

| Classe | n |
|---|---|
| somente quantidade (`B9_QINI≠B2_QATU`, `VINI1=VATU1`) | 1 |
| somente valor | 18 |
| quantidade **e** valor | 49 |
| **total** | **68** |

- **Sem estorno/deleção pós-fechamento:** zero linhas SD3 com `D3_ESTORNO='S'` ou `R_E_C_D_E_L_` para as 68 chaves → a mudança do SB2 não é explicada por movimentação posterior capturável → ajuste direto/recálculo por pernas fora de SD3/SD1/SD2 (consistente com a ressalva de §21.A).
- Padrão recorrente (§22.F): mesma assinatura no fechamento anterior.

### 22.B — `B9_CM1 ≠ B2_CM1` — interpretação temporal

Na população sem movimento posterior:

| Perfil CM | n |
|---|---|
| `B9_CM1 == B2_CM1` | 1.164 |
| diferença pequena | 140 |
| diferença grande | 339 |

- **303/339** casos de diferença grande têm quantidade e valor idênticos → `B2_CM1` foi **atualizado após o fechamento** sem alterar o saldo físico → evidência de recálculo de custo médio posterior ao snapshot (MATA330 em janela separada ou reexecução).
- Conclusão delimitada: `B9_CM1` e `B2_CM1` **não** representam o mesmo instante nem obrigatoriamente o mesmo cálculo — `B9_CM1` fixa o CM no fechamento; `B2_CM1` é o CM corrente, mutável por recálculos. Não equiparar.

### 22.C — Reconciliação DEL100 × SB2/SB9 — fórmula corrigida pelo fonte

Releitura do `DEL100.PRW` corrigiu o mapeamento das pernas usado nas reconstruções anteriores (§18–§21):

| Perna | Fonte (linha) | Correto | Mapeamento anterior |
|---|---|---|---|
| SD1 data | L110 | `D1_DTDIGIT` | `D1_EMISSAO` |
| SD1 valor | L114 | `D1_CUSTO` | `D1_TOTAL` |
| SD2 valor | L127 | `D2_TOTAL` | `D2_CUSTO1` |
| SD3 | L94–101 | `D3_EMISSAO`, `D3_CUSTO1`, `D3_ESTORNO<>'S'`, TM<500 entra/≥500 sai | igual |

Rerun com a fórmula fiel (filial 02, janela `20260831→20260930`, chaves com SB9 atual): **421 chaves divergentes** — contra 724 sob o mapeamento aproximado. As contagens de §19–§21 permanecem como evidência histórica **com a limitação registrada**: foram produzidas sob mapeamento de campos menos fiel ao fonte; as classificações derivadas (diferença ≠ defeito) não se alteram.

Confronto das 421 com o SB2 **atual**:

| Comparação | n |
|---|---|
| `B2_QATU ==` quantidade reconstruída | 110/421 |
| `B2_VATU1 ==` valor reconstruído | 1/421 |
| subconjunto congelado (`sb9_v == prior_v`) | 111 |
| — dos quais `B2 ==` reconstrução | **0** |

Leitura: existem **três estados com trajetórias distintas** — reconstrução por movimentos, snapshot SB9 e saldo corrente SB2. Em 111 chaves "congeladas", nem snapshot nem saldo corrente seguem a reconstrução → o roll-forward do SB2 incorpora pernas/austes que a fórmula movimento-a-movimento não mede. Divergência DEL100×SB9 **não é defeito**; igualdade SB9×SB2 no recorte (§21.A) **não valida** o algoritmo de formação do saldo.

### 22.D — Produtor SB9: três planos separados

1. **Correspondência de dados — `PROVEN` (recorte):** SB9 ≅ SB2 no fechamento (§21.A); recorrente (§22.F).
2. **Rotina disponível no acervo — `PARCIAL`:** `MA330OK.PRW` (39 linhas) é o **ponto de entrada padrão chamado ao final do MATA330** (recálculo do custo médio). Corpo: `EXEC STP_DELPI_OP_TERCEIRO_<emp>` com `@DATADE` (L18–21) e `EXEC STP_PROTHEUS_DELPI_AJUSTA_OP` para filiais **01 e 02** com `@ANOMES` (L25–36) → hooks DELPI estão acoplados ao ciclo do MATA330. **Não** há escrita direta em SB9 neste fonte. O MATA330 padrão (que fecha custo médio e grava SB9) não consta do acervo → identidade do produtor segue `BLOCKED` (código/owner TI).
3. **Execução observada — `INCONCLUSIVE`:** inserção em janela comum por filial (§20.E) é assinatura compatível com job de fechamento, não prova de job. As SPs referenciadas (`STP_DELPI_OP_TERCEIRO_01`, `STP_PROTHEUS_DELPI_AJUSTA_OP`) estão **ausentes** das bases acessíveis (`DELPI`, `DELPI_TST01`, `DELPI_TST_WS`, `IntranetDelpiDev`) → provavelmente em outra base/servidor ou removidas → execução `BLOCKED` (owner TI/ERP).

### 22.E — MOD monetária: proveniência `PROVEN`

Fluxo funcional localizado (Controladoria/PCP): `vw_Apontamentos_Eficiencia` expõe por apontamento OP, produto, `TEMPO_MAO_OBRA_OP`, `TEMPO_REAL_HORAS`, `CENTRO_CUSTO_RECURSO`, `PRODUTO_MOD`, `VALOR_MOD_HORA`, `RESULTADO_MOD`, `LUCRO_MOD`, `PREJUIZO_MOD`; `DLP34R01.PRW` consome `VW_PROTHEUS_CUSTO_ANALITIC_*`/`VW_PROTHEUS_CUSTO_SINT_*` (cadeia de custos); `vw_fin_despesas_centro_custo` mapeia despesas por CC.

**Fonte do rate — `PROVEN` (população completa):**

```sql
-- VALOR_MOD_HORA == SBZ010.BZ_CUSTD por filial
SELECT v.FILIAL, v.PRODUTO_MOD, v.VALOR_MOD_HORA, z.BZ_CUSTD
FROM (SELECT FILIAL, PRODUTO_MOD, VALOR_MOD_HORA
      FROM vw_Apontamentos_Eficiencia
      WHERE DATA_PRODUCAO >= '2026-01-01' GROUP BY 1,2,3) v
LEFT JOIN SBZ010 z ON z.BZ_COD=v.PRODUTO_MOD AND z.BZ_FILIAL=v.FILIAL AND z.D_E_L_E_T_=''
-- f01: 30/30 MATCH | f02: MATCH exceto MOD312/314/316/317 (rate NULL na view E sem linha SBZ — consistente)
```

- `BZ_CUSTD` = **custo padrão por filial** (complemento SBZ). `B1_CUSTD` diverge (MOD320: `B1`=32,83 vs rate 84,02) → o rate é **por filial**, não o custo padrão global.
- Rate **cadastral/estático**: MOD20101 = 88,34 desde 2006 — mantido manualmente, não derivado de rateio contábil → explica a ausência nas tabelas CT* (§21.D).
- `PRODUTO_MOD ↔ CENTRO_CUSTO_RECURSO` espelhados (MOD352↔352) — consistente com §20.D.
- Regra monetária (estrutural): `RESULTADO_MOD = horas_apontadas × BZ_CUSTD(MOD,filial)`; `LUCRO_MOD`/`PREJUIZO_MOD` decompõem o resultado (tempo padrão vs real valorizado). Set/2026: f01 2.661h → resultado R$5.919,08; f02 3.232h → R$56.000,57.
- **Boundary:** definições das views são criptografadas (`definition=None`) → fórmula interna exata de lucro/prejuízo e joins internos `TO_INVENTORY` (exige owner com acesso à DDL). Tabelas CT* esgotadas em rodadas anteriores não são o veículo — a apropriação é **operacional via custo padrão SBZ**, não contábil.

### 22.F — Recorrência do padrão snapshot

Fechamento anterior (`20260831`, filial 02): 1.359 chaves sem movimento posterior; `B9_QINI == B2_QATU` em 1.307 (96,2%); quantidade e valor iguais em 1.302 (95,8%) → o padrão SB9=snapshot SB2 se repete entre fechamentos (`PROVEN` recorrente no recorte).

### 22.G — Residuais

- `DLP06R01` (receber): `BLOCKED` — fonte ausente do acervo.
- P7/MATR460: produtor e parâmetros não comprovados; MP7/TRB não são proxy — `TO_INVENTORY`.
- Produtor SB9: identidade `BLOCKED`; hook MA330OK comprovado em fonte, execução não observada.
- Doc 47: **`NO_GATE_CHANGE`** — nenhum critério de promoção demonstrado nesta rodada.

### 22.H — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R48 | 68 exceções | 1 qtd / 18 valor / 49 ambos; 0 estorno/deleção pós-fechamento | — |
| C2-R49 | CM1 | 303/339 CM-diff com qtd+valor iguais → recálculo posterior; B9_CM1≠B2_CM1 temporalmente | — |
| C2-R50 | DEL100 fiel | campos corrigidos (D1_DTDIGIT/D1_CUSTO/D2_TOTAL); 421 divergentes; B2 fecha só 110 qtd/1 valor; 111 congeladas sem B2=recon | — |
| C2-R51 | produtor | MA330OK = PE pós-MATA330 → STPs f01/f02 (fonte); SPs ausentes nas bases acessíveis; execução BLOCKED | G4 fonte |
| C2-R52 | MOD rate | PROVEN: `VALOR_MOD_HORA == BZ_CUSTD` 100% dos pares 2026; estático desde 2006; boundary view criptografada | G4 fonte |
| C2-R53 | recorrência | 20260831: 95,8% qtd+valor == SB2 → snapshot recorrente | G4 fonte |
| C2-R54 | — | `NO_GATE_CHANGE` | — |

---

## §23 — RODADA 11 (CF-C2-EXEC-011) — EXECUTION_DRIFT DEL100 + HOMOLOGAÇÃO FÓRMULA MOD — 2026-10-23

### 23.A — `EXECUTION_DRIFT` declarado — reconstrução DEL100×SB9

As contagens de divergência das Rodadas 7–9 (724 valor / 672 quantidade) e todas as classificações derivadas (categorias §21.C, atribuição por TM §20.A) foram produzidas por consultas **com mapeamento de campos diferente do `DEL100.PRW`**. Os scripts das rodadas eram temporários e foram removidos; a reprodução exata do binário da consulta R7 não é possível. Registrado como `EXECUTION_DRIFT` da trilha §18–§21 — **evidência histórica preservada, conclusões dependentes reclassificadas abaixo**.

Divergências documentadas do mapeamento anterior vs fonte (`DEL100.PRW` L94–128):

| Perna | Fonte (vigente) | Mapeamento aproximado (R7–R9) |
|---|---|---|
| SD1 data | `D1_DTDIGIT` (L110) | `D1_EMISSAO` |
| SD1 valor | `D1_CUSTO` (L114) | `D1_TOTAL` |
| SD2 valor | `D2_TOTAL` (L127) | `D2_CUSTO1` |
| SD3 | `D3_EMISSAO`, `D3_CUSTO1`, `D3_ESTORNO<>'S'`, TM<500 entra | igual |

### 23.B — Matriz de variantes: o que move a contagem (f02, 0831→0930, chaves com SB9 atual)

| Variante | Cobertura | qtd-div | valor-div |
|---|---|---|---|
| **FIEL** (DTDIGIT+CUSTO/TOTAL) | prior∪mov, prior NULL excluído | 242 | **421** |
| V1: EMISSAO+TOTAL/CUSTO1 | idem | 341 | 482 |
| V2: EMISSAO+CUSTO/CUSTO1 | idem | 341 | 415 |
| V4: EMISSAO+TOTAL/TOTAL | idem | 341 | 649 |
| FIEL + prior NULL→0 | idem | 285 | 524 |
| FIEL + cobertura inclui cur-only (recon=0) | ∪cur | 290 | 529 |
| FIEL sem F4 nas duas pernas | ∪cur | 368 | 606 |
| FIEL janela `>=0831` | prior∪mov | 449 | 611 |

Leitura da decomposição 724→421:
- **Campo SD1 data** (`D1_DTDIGIT` vs `D1_EMISSAO`): ±~100 chaves de quantidade e dezenas de valor.
- **Campos de valor** (`D1_CUSTO`/`D1_TOTAL`, `D2_TOTAL`/`D2_CUSTO1`): efeito dominante no valor — `D1_TOTAL` sozinho adiciona ~130 divergentes.
- **Cobertura** (incluir chaves cur-only com recon=0): +59 keys.
- **F4/estorno/janela**: estorno nulo neste recorte; janela ampliada e ausência de F4 elevam contagens (não reproduzem 724 sozinhos).
- Os números **R6 (523/290) são aproximadamente reproduzidos** por `FIEL + cobertura ∪cur` (529/290) — consistente com a R6 ter cobertura ampliada. O par **724/672 da R7 não foi byte-reproduzido** em nenhuma das 12 variantes — exige diferença estrutural não recuperável do script removido. Ambos os pares ficam `STALE_EVIDENCE`.

**Reprodução vigente:** fórmula fiel ao fonte, `prior∪mov`, prior NULL excluído → **3.058 chaves, 421 divergentes de valor, 242 de quantidade** (com cobertura ∪cur: 530/529/290).

### 23.C — Reclassificação das conclusões dependentes das 724

| Item | R7–R9 (STALE) | R11 vigente (421) |
|---|---|---|
| congelado (`sb9_v==prior_v`) | 224 | 111 |
| `sb9_v==0` | 44 | 152 |
| `sb9_v==qtd×CM_prior` | 113 | 192 |
| Δ==contribuição TM010 | **135** | **0** |
| Δ==contribuição TM999 | 93 | 22 |
| presença TM nas divergentes | — | TM999:249, TM010:158, TM499:52, TM502:8, TM503:1 |

- A **atribuição TM010/TM999 de §20.A está SUPERADA** — era artefato do mapeamento aproximado (o delta "exato" casava com a fórmula errada). Com a fórmula fiel, nenhuma divergência fecha integralmente por TM010 e só 22 por TM999.
- A observação "divergentes só com perna SD3" mantém-se como **padrão de presença** (não prova de omissão do produtor).
- Reafirmam-se inalteradas: as 26 chaves MOD (não-estocáveis), elegibilidade saldo-zero+sem-movimento, SB9=snapshot SB2 (96%), retroatividade rejeitada, 68 exceções — nenhuma depende das 724.

### 23.D — MOD monetária: homologação numérica `PROVEN`

População: 85.904 apontamentos 2026 com `VALOR_MOD_HORA` não-nulo.

| Fórmula | Match | Status |
|---|---|---|
| `TEMPO_GANHO_PERDIDO_HORAS = TEMPO_PREVISTO_HORAS − TEMPO_REAL_HORAS` | 85.904/85.904 | **PROVEN** |
| `RESULTADO_MOD = TEMPO_GANHO_PERDIDO_HORAS × VALOR_MOD_HORA` | 85.904/85.904 | **PROVEN** |
| `LUCRO_MOD = MAX(RESULTADO_MOD, 0)` | 85.904/85.904 | **PROVEN** |
| `PREJUIZO_MOD = MAX(−RESULTADO_MOD, 0)` | 85.904/85.904 | **PROVEN** |
| `VALOR_MOD_HORA == SBZ010.BZ_CUSTD` (filial×produto) | f01 33/33; f02 34/38 | **PROVEN** |
| candidatas rejeitadas | `real×rate` 12.009; `padrão×rate` 11.680; `estimado−real` 12.819 | REJEITADAS |

**Correção à fórmula registrada em §22.E:** `RESULTADO_MOD` **não é** "horas apontadas × rate" — é o **delta de eficiência valorizado**: `(TEMPO_PREVISTO − TEMPO_REAL) × BZ_CUSTD`, com lucro/prejuízo como decomposição por sinal. A redação de §22.E fica corrigida por esta seção (append-only, sem apagar).

Cardinalidade: **1 rate por filial×produto** (zero produtos com >1 `VALOR_MOD_HORA`). Exceções: 4 produtos f02 (`MOD312/314/316/317`) com rate NULL na view **e** sem linha SBZ na filial — comportamento consistente do LEFT JOIN, não defeito. Semântica dos campos: `BZ_CUSTD` = valor-hora cadastral (custo padrão por filial); `TEMPO_PREVISTO_HORAS` = horas previstas (≈ estimado proporcional + ~0,08h); `TEMPO_REAL_HORAS` = horas apontadas; `RESULTADO_MOD` = resultado financeiro da eficiência; `LUCRO`/`PREJUÍZO` = decomposição por sinal.

### 23.E — Manutenção de `BZ_CUSTD` — `PROVEN` (auditoria TTAT_LOG)

`SBZ010_TTAT_LOG` registra **todas** as alterações de `BZ_CUSTD` com usuário/programa/data:

| Programa | n alterações BZ_CUSTD | Natureza |
|---|---|---|
| MATA320 | 71.789 | atualização massiva de custo (recálculo) |
| MATA010 | 945 | cadastro manual de produto |
| CRMA110 | 272 | integração CRM |
| **MATA019** | **71 (todas MOD, f01)** | **atualização de custo standard** |

- **Para produtos MOD**: 79 alterações em 2026 — 71 via `MATA019` (ex.: 08/10/2026 11:42–11:49, usuária JOICI, regravou em massa: MOD20101 77,61→88,34; MOD352 44,17→45,81; MOD393 0→79,87) + 8 via `MATA010`.
- **Correção à afirmação §22.E ("estático desde 2006"):** FALSA. A view retorna **o rate corrente do SBZ aplicado retroativamente** a todos os apontamentos históricos — MOD20101 mostra 88,34 em linhas de 2006 porque a view junta o `BZ_CUSTD` atual (gravado em 08/10/2026), não o rate vigente na data do apontamento. Implicação: `RESULTADO_MOD`/`LUCRO`/`PREJUÍZO` históricos são **revalorizados** a cada atualização de `BZ_CUSTD` — a view não é point-in-time.
- Rates MOD são, portanto, **custo padrão mantido por rotina de atualização (MATA019) + ajustes manuais**, revisados periodicamente — não derivados de rateio contábil nem imutáveis.

### 23.F — Boundary registrado

Definições das views (`vw_Apontamentos_Eficiencia`, `VW_PROTHEUS_CUSTO_*`) são criptografadas (`definition=None`) → produtor SQL interno não inspecionável; o que está `PROVEN` é o **contrato empírico** (colunas, fórmulas e fonte do rate). Extração da DDL: owner SQL/DBA.

### 23.G — Residuais

- `DLP06R01` `BLOCKED`; P7 `TO_INVENTORY`; produtor SB9 `BLOCKED` — inalterados.
- Doc 47: **`NO_GATE_CHANGE`**.
- Fórmula interna `TEMPO_PREVISTO_HORAS` (origem do +0,08h sobre o estimado) `TO_INVENTORY` menor.

### 23.H — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R55 | drift | EXECUTION_DRIFT declarado; 724 não byte-reproduzido (12 variantes); vigente=421/242 | — |
| C2-R56 | reclassificação | TM010 135→0; TM999 93→22; congelado 224→111; STALE_EVIDENCE §20.A/§21.C | — |
| C2-R57 | MOD fórmula | PROVEN 100%: GANHO=PREV−REAL; RES=GANHO×rate; LUCRO/PREJUIZO=split sinal; rate=BZ_CUSTD | G4 fonte |
| C2-R58 | BZ_CUSTD manutenção | PROVEN: MATA019/MATA010 atualizam; view usa rate corrente retroativo; corrige §22.E | G4 fonte |
| C2-R59 | — | `NO_GATE_CHANGE` | — |

---

## §24 — RODADA 12 (CF-C2-EXEC-012) — HISTÓRICO MOD, QUERY VIGENTE E RESIDUAIS — 2026-10-23

### 24.A — Completude temporal do `SBZ010_TTAT_LOG`

| Âmbito | n | desde | até |
|---|---|---|---|
| todo o log | 558.069 | **2026-04-27** | 2026-10-23 |
| `BZ_CUSTD` | 73.102 | 2026-04-27 | 2026-10-23 |

**Limitação estrutural `PROVEN`:** a auditoria TTAT cobre apenas **~6 meses** (ativada em 27/04/2026). Não é fonte histórica completa — rates anteriores a abril/2026 são irreconstruíveis por esta via. Para histórico de rates MOD é utilizável **só a partir de 27/04/2026**.

### 24.B — Trilha de rates MOD (cruzamento log × view)

79 alterações `BZ_CUSTD` em produtos MOD no período coberto:

| Evento | Programa | Data | Escopo |
|---|---|---|---|
| criação de rates | MATA010 | jul/2026 | MOD22401–22405 (I) |
| **revalorização massiva f02** | MATA019 | 07/10/2026 15:31 | MOD213/214/215/220/230/310… (38,35→41,73; 75,09→84,00) |
| **revalorização massiva f01** | MATA019 | 08/10/2026 11:39–11:49 | ~30 MODs (MOD20101 77,61→88,34; MOD352 44,17→45,81; MOD223 115,21→127,50) |
| produtos sem log | — | — | ~80 linhas MOD com `BZ_CUSTD=0`/data inclusão antiga — rate nunca definido |

A view **sempre aplica o `BZ_CUSTD` corrente**: apontamentos de set/2026 exibem o rate gravado em out/2026 (prova: MOD20101 exibe 88,34 em linhas de 2006, mas o log mostra 77,61→88,34 apenas em 08/10/2026).

### 24.C — Demonstração quantitativa: rate da competência vs corrente

Set/2026, MOD352 f01 (rate 44,17→45,81 em 08/10): `Σ RESULTADO` view = **−178,97**; recalculado com rate da competência = **−173,38** (Δ −5,59 em 1.697 apontamentos).

Total set/2026, produtos com rate alterado em out/2026:

| Filial | MODs | resultado view (rate atual) | resultado rate competência | Δ |
|---|---|---|---|---|
| 01 | 28 | +5.918,90 | +5.429,18 | **+489,72 (~9%)** |
| 02 | 21 | −32.694,32 | −30.228,79 | **−2.465,53 (~8%)** |

→ **Impacto material**: cada revalorização de `BZ_CUSTD` reescreve ~8–9% do resultado MOD do mês corrente e de **todo** o histórico exibido pela view.

### 24.D — Separação dos três planos + opções para o owner

| Plano | Estado |
|---|---|
| fórmula matemática | `PROVEN`: `RESULTADO = (TEMPO_PREVISTO − TEMPO_REAL) × rate`; LUCRO/PREJUÍZO = split por sinal (§23.D) |
| implementação da view | `BLOCKED` DDL criptografada; contrato empírico = join com `BZ_CUSTD` **corrente** (não point-in-time) |
| política de congelamento | **inexistente no observado**: indicadores são recalculados ao vivo; nenhuma snapshot de rate/resultado encontrada |

Opções para decisão do owner (não implementado):

1. **Histórico original (rate da competência):** exige rate vigente por data — reconstruível só desde 27/04/2026 via TTAT_LOG, ou nova tabela de histórico de rates. Corrige comparabilidade temporal; quebra paridade com a view oficial enquanto ela usar rate corrente.
2. **Recalculado corrente (status quo da view):** resultados sempre revalorizados ao custo atual; consistente com a view existente; distorte série histórica.
3. **Ambos lado a lado:** preserva as duas leituras; exige a mesma fonte de rate-por-data do item 1.

### 24.E — Query vigente sanitizada (DEL100×SB9) — reproduzível

```sql
/* f02, janela 20260831->20260930, chaves prior|movimento com SB9 atual
   resultado vigente: total=3058, qtd-div=242, valor-div=421 */
WITH prior AS (
  SELECT B9_COD, B9_LOCAL, B9_QINI q0, B9_VINI1 v0
  FROM SB9010 WHERE B9_DATA='20260831' AND B9_FILIAL='02' AND D_E_L_E_T_=''
), cur AS (
  SELECT B9_COD, B9_LOCAL, B9_QINI q1, B9_VINI1 v1
  FROM SB9010 WHERE B9_DATA='20260930' AND B9_FILIAL='02' AND D_E_L_E_T_=''
), mv3 AS (
  SELECT D3_COD cod, D3_LOCAL loc,
    SUM(CASE WHEN D3_TM<'500' THEN D3_QUANT ELSE -D3_QUANT END) dq,
    SUM(CASE WHEN D3_TM<'500' THEN D3_CUSTO1 ELSE -D3_CUSTO1 END) dv
  FROM SD3010 WHERE D3_FILIAL='02' AND D3_EMISSAO>'20260831' AND D3_EMISSAO<='20260930'
   AND D3_ESTORNO<>'S' AND D_E_L_E_T_='' GROUP BY D3_COD, D3_LOCAL
), mv1 AS (
  SELECT D1_COD cod, D1_LOCAL loc, SUM(D1_QUANT) dq, SUM(D1_CUSTO) dv
  FROM SD1010 WHERE D1_FILIAL='02' AND D1_DTDIGIT>'20260831' AND D1_DTDIGIT<='20260930'
   AND D_E_L_E_T_='' AND EXISTS (SELECT 1 FROM SF4010 WHERE F4_CODIGO=D1_TES AND F4_ESTOQUE='S' AND SF4010.D_E_L_E_T_='')
  GROUP BY D1_COD, D1_LOCAL
), mv2 AS (
  SELECT D2_COD cod, D2_LOCAL loc, SUM(D2_QUANT) dq, SUM(D2_TOTAL) dv
  FROM SD2010 WHERE D2_FILIAL='02' AND D2_EMISSAO>'20260831' AND D2_EMISSAO<='20260930'
   AND D_E_L_E_T_='' AND EXISTS (SELECT 1 FROM SF4010 WHERE F4_CODIGO=D2_TES AND F4_ESTOQUE='S' AND SF4010.D_E_L_E_T_='')
  GROUP BY D2_COD, D2_LOCAL
), rec AS (
  SELECT x.cod, x.loc,
    MAX(x.q0)+COALESCE(SUM(x.dq3),0)+COALESCE(SUM(x.dq1),0)-COALESCE(SUM(x.dq2),0) rq,
    MAX(x.v0)+COALESCE(SUM(x.dv3),0)+COALESCE(SUM(x.dv1),0)-COALESCE(SUM(x.dv2),0) rv
  FROM (
    SELECT B9_COD cod, B9_LOCAL loc, q0, v0, 0.0 dq3, 0.0 dv3, 0.0 dq1, 0.0 dv1, 0.0 dq2, 0.0 dv2 FROM prior
    UNION ALL SELECT cod,loc,NULL,NULL,dq,dv,NULL,NULL,NULL,NULL FROM mv3
    UNION ALL SELECT cod,loc,NULL,NULL,NULL,NULL,dq,dv,NULL,NULL FROM mv1
    UNION ALL SELECT cod,loc,NULL,NULL,NULL,NULL,NULL,NULL,dq,dv FROM mv2
  ) x GROUP BY x.cod, x.loc
)
SELECT COUNT(*),
  SUM(CASE WHEN ABS(c.q1-r.rq)>0.0001 THEN 1 ELSE 0 END) dq_div,
  SUM(CASE WHEN ABS(c.v1-r.rv)>0.01 THEN 1 ELSE 0 END) dv_div
FROM rec r JOIN cur c ON c.B9_COD=r.cod AND c.B9_LOCAL=r.loc;
```

Marcação formal: **todas as conclusões derivadas de 724/672 estão `STALE_EVIDENCE`** (§19.C, §20.A atribuição TM, §21.C categorias); a referência vigente é 421/242 + reclassificação §23.C. Não repetidos: testes já descartados (TM999-excluída, retroatividade, 12 variantes).

### 24.F — Residuais: separação SQL-investigável vs owner

| Item | Estado | Caminho |
|---|---|---|
| `DLP06R01` (receber) | `BLOCKED` | fonte ausente do acervo → owner TI (pedido de fonte) |
| P7/MATR460 | `TO_INVENTORY` | sem grupo SX1 MATR4%; MP7/TRB não-proxy; fonte oficial não consta do acervo → owner TI |
| produtor SB9 | `BLOCKED` | **esgotado o investigável por SQL read-only**: triggers em SB2/SB9 = só `*_STAMP`/`SB2010_SCHEDULE_MRP` (MRP, definição criptografada); zero SPs `STP_*`/`DELPI*` na base; `msdb.dbo.sysjobs` **permissão negada** → jobs SQL Agent e DDL de views/triggers exigem owner DBA; MATA330/hook = evidência de fonte (§22.D) |
| definição views custo/eficiência | `BLOCKED` | DDL criptografada → owner DBA |

### 24.G — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R60 | log TTAT | cobre só ≥27/04/2026 — não é histórico completo | — |
| C2-R61 | trilha MOD | 79 alterações: mass-updates MATA019 f02 07/10 + f01 08/10; MATA010 criações | — |
| C2-R62 | impacto | set/2026: f01 +489,72 (~9%), f02 −2.465,53 (~8%) — revalorização material | G4 fonte |
| C2-R63 | opções | 3 opções owner (original/recalculado/ambos); política de congelamento inexistente | — |
| C2-R64 | query vigente | sanitizada no §24.E; 724/672 → STALE_EVIDENCE formal | — |
| C2-R65 | residuais | SQL-investigável esgotado; msdb/DDL/proc = owner DBA/TI | — |
| C2-R66 | — | `NO_GATE_CHANGE` | — |

---

## §25 — RODADA 13 (CF-C2-EXEC-013) — CONSOLIDAÇÃO E FECHAMENTO DE RESIDUAIS — 2026-10-23

### 25.A — Validação pontual da query §24.E (TES/SF4 e reprodução)

**Lookup TES/SF4 — `PROVEN` fiel à semântica `xFilial`:** `SF4010` é compartilhada — todas as 458 linhas têm `F4_FILIAL=' '` e **nenhum** `F4_CODIGO` duplicado por filial ou com `F4_ESTOQUE` divergente. Logo `DbSeek(xFilial("SF4")+TES)` resolve no registro global único — o `EXISTS` sem filtro de filial da query publicada **equivale exatamente** ao comportamento AdvPL. Todos os 39 TES usados na janela resolvem a registro único.

**Reprodução independente:** a query §24.E foi executada em duas sessões distintas com resultado idêntico — **3.058 chaves / 242 quantidade / 421 valor** — reproduzível e versionada.

### 25.B — Consolidação MOD

| Evidência | Estado |
|---|---|
| `VALOR_MOD_HORA == SBZ010.BZ_CUSTD` (filial×produto, 1:1) | `PROVEN` (f01 33/33; f02 34/38 + 4 sem-SBZ consistentes) |
| `RESULTADO = (PREVISTO−REAL)×rate`; `LUCRO/PREJUÍZO` = split sinal | `PROVEN` 85.904/85.904 |
| View aplica rate **corrente** retroativamente | `PROVEN` (MOD20101: 88,34 em 2006 vs log 77,61→88,34 em 08/10/2026) |
| Cobertura do histórico | `LIMITADO`: TTAT_LOG inicia 27/04/2026 — **reconstrói só pós-abril**; rates anteriores irreconstruíveis |
| Cadastro inicial de rates MOD | ~80 produtos sem log e `BZ_CUSTD=0` — nunca precificados |

### 25.C — Quadro de decisão para a Controladoria (não implementado)

| Opção | Proveniência exigida | Imutabilidade | Limitações |
|---|---|---|---|
| **A. Histórico homologado** (rate da competência) | rate vigente por data — TTAT_LOG (≥abr/26) ou nova tabela histórica | snapshot de resultado por competência gravado no fechamento | pré-abr/26 irreconstruível; diverge da view oficial enquanto ela usar rate corrente; exige manutenção de tabela/política nova |
| **B. Recalculado corrente** (status quo) | `BZ_CUSTD` atual (já provado) | nenhuma — revaloriza a cada MATA019/MATA010 | distorce série histórica ±8–9%/revalorização; paridade plena com a view existente |
| **C. Ambos** | as duas fontes acima | snapshot da opção A + leitura viva da B | maior superfície de explicação/UX; depende de A |

Requisitos para qualquer decisão: fonte de rate-por-data com owner (Controladoria/Custos), política de congelamento no fechamento mensal, e homologação do valor-base set/2026 (f01 +5.918,90 / f02 −32.694,32 pela ótica corrente).

### 25.D — Evidências objetivas a solicitar aos owners

| # | Owner | Evidência solicitada | Desbloqueia |
|---|---|---|---|
| E1 | TI/ERP | fonte `DLP06R01` (ou confirmação de rotina produtora das 657 baixas receber) | produtor receber |
| E2 | TI/ERP | produtor e parâmetros do P7/MATR460 oficial (rotina, SX1/SX6, exports) | R03 G1–G4 |
| E3 | DBA | definição (DDL) de `vw_Apontamentos_Eficiencia`, `VW_PROTHEUS_CUSTO_*`, `vw_fin_despesas_centro_custo` | implementação MOD, bindings G4 |
| E4 | DBA | lista de jobs SQL Agent (`msdb.dbo.sysjobs`) e código das SPs `STP_DELPI_OP_TERCEIRO_*`/`STP_PROTHEUS_DELPI_AJUSTA_OP` | execução do fechamento SB9 |
| E5 | TI/ERP | confirmação da rotina/schedule que grava SB9 (MATA330+custom?) e log de execução out/2026 | produtor SB9 |
| E6 | Controladoria | decisão 25.C (A/B/C) + homologação do valor-base MOD set/2026 → **atualizado 23/10: opção C aprovada** (`81-decisao-e6`, `e68ae2d63129`); restam E6-D1..D6 + homologação + AC-E6 | política de congelamento |

### 25.E — Cruzamento residuais × gates Doc 47

| Gate item | Nossa evidência relacionada | O que falta para o gate |
|---|---|---|
| **R03** P7/Bloco H | SB9=snapshot SB2 (96%), elegibilidade, 68 exceções | produtor oficial + parâmetros (E2); G1–G4 `PENDING` |
| **R04** Consumo/OP | `matr860` decodificado (MOD via SD3, `B1_COD LIKE 'MOD%'`/`B1_CCCUSTO`) | bindings homologados + amostra oficial (G4/G5) |
| **R09** Faturamento×MOD | produtor `DLP204.prw` `SOURCE_AVAILABLE` + modelo 99,4% (rodada 24, §43); fórmula+rate `PROVEN` | SP `STP_DELPI_FORMA_PRECO_*`/RPO/parâmetros + 27 tempos + divisor (E9); DDL da view (E3); aceite (G6) — G4 PASS, G5 `INCONCLUSIVE` |
| **R12** Refaz Saldos | `DEL100` decodificado + query vigente 421/242 | vínculo rotina-oficial↔relatório; execução observada — **errata r27: rotina do vídeo = MATA300, não DEL100 (§46)** |
| **R15** Cutoff/SB9 | snapshot recorrente, janela comum, MA330OK hook | execução do job (E4/E5) + aceite |

**`NO_GATE_CHANGE`**: toda evidência acima é candidata a G4/G5, mas gates exigem referência de artefato/SHA, homologação e aceite — nenhum critério completo nesta rodada.

### 25.F — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R67 | SF4 lookup | PROVEN: compartilhada (458 linhas filial=' '), EXISTS ≡ xFilial | G4 fonte |
| C2-R68 | reprodução | 3.058/421/242 confirmado em 2 execuções independentes | G4 fonte |
| C2-R69 | quadro decisão | A/B/C com requisitos e limitações; valor-base set/26 | — |
| C2-R70 | owner asks | E1–E6 objetivas para TI/DBA/Controladoria | — |
| C2-R71 | cross-map | R03/R04/R09/R12/R15 mapeados; `NO_GATE_CHANGE` | — |

---

## §26 — HANDOFF (CF-C2-HANDOFF-001) — PACOTE DE EVIDÊNCIAS PARA OWNERS — 2026-10-23

Pacote consolidado em `82-ciclo2-handoff-pacote-evidencias-owners.md` (renumerado de `81-` em 2026-10-23, resolvendo colisão com o documento de decisão): E1–E6 organizados por responsável (TI/ERP, DBA, Controladoria) com evidência atual, lacuna, fonte esperada, impacto, critério de aceite e protocolo de classificação de respostas (`SOURCE_AVAILABLE`/`CODE_DEPLOYED`/`EXECUTION_OBSERVED`/`FUNCTIONAL_ACCEPTANCE`). Referência vigente 3.058/421/242; `EXECUTION_DRIFT`/`STALE_EVIDENCE` preservados.

**E6 — atualização de estado (2026-10-23):** opção **C — Ambos** aprovada como direção de produto (`APPROVED / PRODUCT_DIRECTION_ONLY`), registrada em `81-decisao-e6-historico-monetario-mod-opcao-c.md` (`e68ae2d63129`). `IMPLEMENTATION_AUTHORIZED = NO` — não autoriza contratos, runtime, jobs, view ou UI. Pendências remanescentes: detalhamentos E6-D1..D6, homologação dos valores-base set/2026 e validação dos critérios AC-E6-01..10 (ver doc 82 §2.3). Doc 47: `NO_GATE_CHANGE`.

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R72 | handoff | doc 81 criado; E1–E6 por owner; protocolo de resposta | — |


---

## §27 — FULL EVIDENCE RECONCILIATION (CF-C2-FULL-EVIDENCE-RECONCILIATION-001) — 2026-10-23

Processamento integral da pasta `fechamento` do PO (20 arquivos) + vídeo 54:44 (frames por detecção de cena + full-res). **Crosswalk completo: `83-ciclo2-crosswalk-evidencias-r01-r15.md`.** Sem SQL novo — reconciliação documental/audiovisual/técnica.

### 27.A — Resoluções principais

| Achado | Evidência | Efeito |
|---|---|---|
| `DLP06R01` = layout `.prt` do relatório de baixas | `Pagos por dt.pdf` e `Recebidos.pdf` header `SIGA/DLP06R01.prt/v.12`; `Pagos por nat.pdf` = `nat.prt` | E1 respondido: produtor = **FINR190** ("Relação de Baixas DLP" menu vídeo 13:00 + roster), `.PRX` no acervo |
| P7 = "Registro de Inventário Modelo P7" | vídeo 35:00/37:00 duas emissões preview; `Estoque.pdf` (completo, 3.946.431,87) + `Resumo Estoque.pdf` (escopo MP/PA/PI, 2.976.967,56); roster MATR460; SPEDFISCAL→Bloco H | E2 estreitado: falta parâmetros por emissão, confirmação variante, binding SB9 |
| Execução do fechamento | vídeo 14:47: wizard "Acompanha Custo → Novo fechamento de custo" 4 etapas, JOICI/Matriz | E5 estreitado: falta provar passo que grava SB9 (B9_I_N_S_D_T_ f02=02/10 f01=21/10 ≠ execução 30/09) |
| Fechamento é iterativo | totais P7: 3.776.994,69 (15:06) → ~2.756.1xx (15:08) → 3.946.431,87/2.976.967,56 (PDFs 19:19) | `as_of`/versão obrigatórios (AC-E6) |
| EDAPP gera exports SD1/SD2 | vídeo 47:00 (`SCAGPOU0.XML`); `CC matriz.xlsb` (`SCAGQGA0.XML`) = SD1 + CC; `NF a desconsiderar.xlsb` = SD2 | R10/R11 G4 |
| Roster oficial de rotinas | `Contabilidade liberações.xlsx` | G3 de R05(MATR320), R06/R07(MATR910), R08(MATR989), R09(DLP204), R10/R11(EDAPP), R01/R02(FINR190), R03(MATR460) |

### 27.B — Gates (doc 47 §11): 38 novos PASS

`COLETA = 40/60 = 66,7%` · `AUDITORIA = 40/90 = 44,4%` · concluídos 0/15. G4 só R01/R02 (fonte+SQL inspecionado) e R10/R11 (export = própria tabela). G5/G6 não promovidos.

### 27.C — Status por item

R05 VALIDADO (rotina+artefato); R01/R02/R03/R06–R12/R15 PARCIAL; R04/R13/R14 BLOQUEADO (R04 sem artefato de consumo-OP; R13 externalidade confirmada por checklist; R14 sem evidência).

### 27.D — Registro

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R73 | pasta PO | 20 arquivos inventariados; vídeo mapeado (timeline §3 doc 83) | — |
| C2-R74 | DLP06R01 | resolvido: .prt FINR190 | E1 |
| C2-R75 | P7 | artefatos + rotina observada; escopo MP/PA/PI confirmado em uso real | E2 |
| C2-R76 | fechamento | execução observada 14:47; wizard 4 etapas | R15/R12 |
| C2-R77 | EDAPP | SD1/SD2 exports provados | R10/R11 |
| C2-R78 | doc 47 | +38 gates; 66,7% coleta / 44,4% auditoria | §11 |

Preservados: `EXECUTION_DRIFT`/`STALE_EVIDENCE` (724/672); DEL100 vigente 3.058/421/242; MOD decisão C (doc 81) sem implementação.


---

## §28 — REWORK DE GATES (revisão §27) — 2026-10-23

Revisão dos G4 promovidos na §27 contra a definição canônica do doc 47 (G4 = bindings físicos: tabelas, colunas, joins, filtros). **Errata da §27:**

### 28.A — Correções

| Item | §27 dizia | Correção |
|---|---|---|
| R02 G4 | PASS (FINR190 + DLP06R01.prt) | **PENDING** — §17.D deste próprio documento provou que o artefato (657) não segue o WHERE do FINR190 (649/690). Produtor = `DLP06R01` **custom, fonte ausente do acervo**. O `DLP06R01.prt` do PDF é o *layout* compartilhado, não o produtor. Binding provado só em nível de fonte de dados (`SE5 'R'×SE1`=657); coluna→campo e filtros do relatório são desconhecidos |
| R01 G4 | PASS | **mantido** — binding explícito: `FINR190_DLP.PRX` (commit `0df96daafe`, blob `92bcae1c`) mapeia TRCell→`E5_*`/SED; WHERE reproduz população oficial 948 + motivo 5/5 (§17.B/C). Residual fora do G4: versão RPO + paridade monetária (G5) |
| R10/R11 G4 | PASS | **mantido** — prova adicional: linha 0 dos exports = literal `SD1`/`SD2` e headers = títulos SX3 `D1_*`/`D2_*`; export EDAPP = dump monotabela, sem join; filtro = consulta do usuário |
| R05 | "VALIDADO" | **PARCIAL** — rotina `MATR320` + artefato `.prt` identificados (G1–G3); G4–G6 abertos |
| R15 | execução observada | **preservado sem identidade de produtor** — wizard executado 30/09 14:47, mas `B9_I_N_S_D_T_` (f02 02/10, f01 21/10) diverge; qual passo grava SB9 segue não provado |

### 28.B — Métricas corrigidas (doc 47 §11.1)

37 gates novos (não 38): `COLETA = 39/60 = 65,0%` · `AUDITORIA = 39/90 = 43,3%` · concluídos 0/15.

### 28.C — Efeito no handoff (doc 82 E1)

E1 dividido: **pagar** = FINR190 provado (residual: versão RPO + paridade monetária); **receber** = fonte do `DLP06R01` custom segue pendente com TI/ERP.

Preservados: `EXECUTION_DRIFT`/`STALE_EVIDENCE` (724/672); DEL100 vigente 3.058/421/242; E6 opção C (doc 81) sem implementação; G5/G6 não promovidos.

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R79 | rework G4 | R02 G4→PENDING (§17.D); R01/R10/R11 mantidos com binding explícito; R05 reclassificado | §11.1 doc 47 |

---

## §29 — Paridade monetária row-level dos relatórios de baixas (CF-C2-PARITY-001, 2026-10-23)

Rodada de reconciliação monetária (SELECT-only, canal autorizado `docker exec -i delpi-api-delpi python -` → `connection_pool`; `db_datareader`). Comparação linha-a-linha entre artefatos oficiais e SE5/SE1/SE2, competência 09/2026, eixo `E5_DATA`. Detalhe integral sanitizado: **doc 84**.

### 29.A — Descoberta: contagens reais dos artefatos

`pagos 09 26.xlsb` = **948 linhas de dados** (não 974 — a contagem anterior incluía rodapés/resumos); `Recebidos.xlsb` = **657** (não 686). Ambos batem com as populações oficiais.

### 29.B — R01 (pagar) — paridade row-level completa

- WHERE do `FINR190_DLP.PRX` reproduzido **fielmente** pela primeira vez: chave do par de estorno = FILIAL+PREFIXO+NUMERO+PARCELA+TIPO+CLIFOR+LOJA+SEQ+BANCO+AGENCIA+CONTA+MOVCX (linhas ~1107–1120 do fonte), sem data/valor — gera **948 exatos** (a reprodução anterior com chave aproximada dava 937).
- Multiset de chaves: **948/948 idêntico** ao artefato.
- `Total Baixado` = `E5_VALOR`: **0 divergências** por registro; Jur/Multa = `E5_VLJUROS+E5_VLMULTA` 244,07; Correção = `E5_VLCORRE` −39.365,10; Descontos = `E5_VLDESCO+VLDECRE` 0,01 — todos exatos.
- `Valor Original`: `E2_VALOR` em 942/948; 5 INV aglutinados → VO = `E5_VALOR`; 1 NF → VO = soma do grupo (NF + 4× `TX UNIAO` = 1.029,52). Regra 100% explicada.
- Resumos impressos exatos: Baixados = Σ`E5_VALOR` não-CMP/FAT; Compens. = lado `CP` dos pares CMP; Bx.Fatura = FAT. `Orig` = `E5_FILORIG` (532×01 + 416×02).
- PDF = xlsb − "log de inconsistências": ΔTB 387.629,64 e ΔTB 40.431,46 (receber) = **totais impressos no próprio PDF** — relação exata; identidade do subconjunto = residual (FK6-VA = 0 em todas as linhas; regra não reproduzida por agregação).
- **G5 → PASS** (doc 47 §11.2). `EXECUTION_DRIFT` da rodada 4 (950≠948) agora explicado: era a chave do par de estorno.

### 29.C — R02 (receber) — paridade row-level completa do artefato

- População: **649 chaves com título idênticas** + **8 movimentos `PA` sem título** (`E5_ORIGEM='FINA750'`, histórico "Valor pago s/ Titulo") = 657.
- 8 linhas de **decomposição** (`MT`/`JR`/`DC` + 1 `VL` duplicado) excluídas pelo produtor — seus valores já estão dentro do `E5_VALOR` da baixa `VL` (juros 4,94+multa 11,42 = 16,36 = componente do 587,70).
- Universo SE5'R' = 746 (657 com título + 89 sem título de vários tipos FOL/COF/NDF/vazio); artefato inclui só `PA`/`FINA750` — regra de inclusão do sem-título parcialmente identificada (3 `PA`/`DEB` excluídos).
- `Total Baixado` = `E5_VALOR` exato; `Valor Original` = `E1_VALOR` **649/649**; Jur/Multa 44,16 exato; resumos idênticos à regra do pagar; ΣVO residual **R$1,00** (1 linha) — **retificado em §30: erro de soma na consolidação, Δ real = R$0,00 e VO das 8 linhas `PA` provado = provisão `'P'` espelhada**.
- Coluna `Orig` preenchida só nas linhas sem título (= `E5_FILORIG`); linhas com título exibem vazio (SE1 compartilhada) — semântica distinta do pagar, coerente com produtor distinto.
- **G5 → PASS** (paridade do artefato × banco demonstrada); **G4 permanece PENDING** (fonte `DLP06R01` ausente — regra geral dos filtros não provada).

### 29.D — R03/R05 — paridade parcial

- R03: `Material em processo.xlsb` = EM PROCESSO do P7 completo **exato** (355.240,51; MP 354.938,50 · PI 254,44); PA/PI EM ESTOQUE = MATR320 exato; EM ESTOQUE total e escopo MP/PA/PI não reproduzidos por recorte SB9×armazém (Δ ≥ −8.182,43). G5 PENDING.
- R05: SB9@30/09 f01 × Saldo Atual MATR320 por tipo — **9/10 exatos**; residual MP **+8.631,73** não explicado. G5 PENDING.
- R10: SD1 set/2026 f01 (657 linhas/1.218.399,30 por `D1_EMISSAO`) ≠ artefato EDAPP (353 linhas/169.704,12) — filtro da consulta do operador não documentado.

### 29.E — Efeito e preservações

| Run | Item | Resultado | Gate |
|---|---|---|---|
| C2-R80 | paridade R01 | 948/948 + TB/VO/componentes/resumos exatos | **G5 PASS** |
| C2-R81 | paridade R02 | 649+8 reconciliados + TB/VO exatos | **G5 PASS** (G4 PENDING) |
| C2-R82 | paridade R03/R05 | parcial — EM PROC + PA/PI exatos; MP residual | G5 PENDING |

Métricas: `COLETA = 39/60 = 65,0%` (inalterado) · `AUDITORIA = 41/90 = 45,6%` · concluídos 0/15. Preservados: E6 opção C, `EXECUTION_DRIFT`/`STALE_EVIDENCE` DEL100 (724/672 → vigente 3.058/421/242), §17/§21/§27/§28 intactos, G6 não promovido (exige aceite humano).

---

## §30 — Errata e rework de paridade R02 (CF-C2-PARITY-001 — 2ª rodada, 2026-10-23)

Revisão pontual solicitada após o commit `57a7587901`. Escopo: divergência de
R$1,00 no ΣVO do receber + separação entre registros reproduzidos e hipóteses.

### 30.A — Errata: o "residual de R$1,00" era erro de soma, não divergência

Ao reprocessar a consolidação do §29.C, a soma dos VOs das 8 linhas `PA`
sem título é **15.836,71** (o registro anterior digitou 15.837,71 na
consolidação manual — erro de transcrição, não dos dados). Reconstrução:
`ΣE1_VALOR(649) = 5.285.696,59` + `ΣVO sem título = 15.836,71` =
**5.301.533,30 = ΣVO do artefato — Δ R$0,00, exato**. Nenhuma linha tem
diferença de centavos.

### 30.B — Regra de VO do sem-título provada: provisão `'P'` espelhada

Cada movimento `PA`/`FINA750` do receber (`'R'`) possui na própria SE5 um
espelho `'P'` de provisão (origem `MATA121`/`FINA050`, motivo NOR, mesmo
numero/clifor). **VO impresso = valor da provisão `'P'`** — 8/8 exato:

- numero <MOV-PROV-A>: provisão 1.571,60 = recebimentos 877,00+119,96 +
  compensação 'P' 574,64 (fluxo fecha integralmente);
- idem <MOV-PROV-B> (286,08), <MOV-PROV-C> (830,78), <MOV-PROV-D> (749,20), <MOV-PROV-E> (29,89),
  <MOV-PROV-F> (56,06), <MOV-PROV-G> (10.741,50 — provisão `FINA050`).

### 30.C — Os 3 sem-título excluídos, identificados por linha lógica

`<RECEBIMENTO-SEM-TITULO-A>` 118,27 `FINA090` f01 · `<RECEBIMENTO-SEM-TITULO-B>` 1.000,00 `FINA090` f01 ·
`<RECEBIMENTO-SEM-TITULO-C>` 1.537,00 `FINA750` f02 — todos `PA`/`DEB` sem SE1, confirmados na
SE5 e **ausentes do artefato**. A regra geral que inclui 8 e exclui estes 3
(e a que suprime as 8 linhas de decomposição) segue **hipótese não
demonstrada** — dependente do fonte `DLP06R01` (E1, TI/ERP).

### 30.D — Estado após rework

- **Reproduzidos integralmente (R02):** 657/657 linhas — população, chaves,
  TB, VO (incl. provisão espelhada), componentes, resumos, PDF−xlsb.
- **R01:** paridade do artefato integral (948/948 no XLSB); subconjunto do
  log de inconsistências do PDF reconstruído **em agregado** (total impresso),
  **não linha-a-linha** — residual mantido.
- **R02 G5: PASS mantido** — Δ monetário = R$0,00; pendências remanescentes
  são de identidade de regra (G4), não de paridade. G4 PENDING, G6 PENDING.
- Métricas inalteradas: `COLETA 39/60` · `AUDITORIA 41/90` · concluídos 0/15.

---

## §31 — CF-C2-STOCK-PARITY-001: fonte MATR320 localizado + reconciliação completa de colunas + mecanismo da divergência MP (2026-10-23)

Rodada de investigação READ-only. Dois achados estruturais: (1) o fonte
oficial do relatório está no acervo documental; (2) a divergência de
R$8.631,73 e os gaps das colunas Compras/EntPT decorrem de **eventos
retificadores posteriores à emissão**, reconstruíveis por RECNO e por
log de auditoria.

### 31.A — Fonte e arquitetura da emissão

- `docs/13-fontes-totvs-protheus/04. Estoque/MATR320/matr320.prx` =
  relatório padrão TOTVS `MATR320` (TReport "Resumo das Entradas e
  Saidas"). Caminho primário: **stored procedure `MAT056`** via
  `TCSPExec` (GetSPName("MAT056","22"), VerIDProc `'002'`); o SQL do
  fonte só roda como fallback quando a SP não existe.
- `Dmatr320.prx` = customização Delpi `DLPR320` (User Function renomeada,
  lógica idêntica **exceto** `nEntrTerc`/`nSaiTerc` comentados — colunas
  de poder de terceiros zeradas).
- Evidência da variante efetivamente emitida: o PDF oficial traz
  `Entrada/Saída Poder Terceiros` **não zeradas** (MP: 319.258,140 /
  36.806,805) → a emissão seguiu o caminho **padrão (SP MAT056)**,
  não `DLPR320`. Regras do fonte padrão valem como AS-IS.
- Parâmetros do pergunte `MTR320`: armazém de/até (mv_par01/02), tipo
  de/até (03/04), produto de/até (05/06), **emissão de/até (07/08)**,
  moeda (09), **saldo a considerar: Atual/Fechamento/CalcEst (10)**,
  MOD sim/não (11), OPs SIGAMNT (12). Constantes internas:
  `MV_LOCPROC` (armazém processo, padrão `'99'`) e `MV_CQ` (qualidade,
  padrão `'98'`).

### 31.B — Regras canônicas de coluna (fonte, linhas 402–761)

Filtros físicos por tabela:

- `SD1`: join SF4 `F4_ESTOQUE='S'` · `D1_DTDIGIT` ∈ [par07,par08] ·
  `D1_ORIGLAN<>'LF'` · `D1_LOCAL` ∈ [par01,par02] · valor = `D1_CUSTO`
  (moeda 1; `D1_CUSTO<n>` p/ moeda n).
- `SD2`: idem com `D2_EMISSAO` ∈ período · `D2_ORIGLAN<>'LF'` ·
  valor = `D2_CUSTO1`.
- `SD3`: `D3_EMISSAO` ∈ período · `D3_LOCAL` range ·
  `D3_ESTORNO<>'S'` (MV_D3ESTOR='N') · valor = `D3_CUSTO1` com sinal
  **negativo quando `D3_TM > '500'`** (TM é saída).
- Classificação SD1/SD2 por `SF4.F4_PODER3` + `D1_TIPO`/`D2_TIPO`:
  poder3='N' → Compras/Vendas (ou DevVendas/DevComprs se TIPO='D');
  poder3≠'N' → EntPT/SaiPT.
- Classificação SD3 por `D3_CF`/`D3_OP`: `CF` iniciando 'PR' →
  Produção; `CF ∈ {RE4,DE4}` → Transferências; `OP` vazio ∧
  `CF[3]≠'3'` → Movimentações Internas; `OP` preenchido → Requisições
  p/ Produção; demais → Transf. p/ Processo (`nReqOutr`, acumulado
  também em `nReqProc` sob regra `lLocProc`).
- `nSaldoAtu` = Σ `B2_VATU<moeda>` (par10=1) ou `B2_VFIM<moeda>` (2)
  ou `CalcEst` (3) sobre SB2 nos armazéns do range.
- **`nSalant` é derivado**: `SaldoAtu − Σ colunas de movimento`
  (não é saldo inicial cadastrado — texto do próprio fonte).

### 31.C — Reconciliação coluna a coluna — linha MP (filial 01, 09/2026)

Valores impressos × origem física (SELECT-only; custos em moeda 1):

| Coluna | Impresso | Origem física | Δ |
|---|---|---|---|
| Saldo Inicial | 3.315.659,021 | derivado (SA − movimentos); = ΣSB9@0831 exato | 0 |
| Compras | 642.670,88 | SD1 poder3=N/est=S/tipo≠'D' DTDIGIT-Set **+ itens 001 do doc `<NF-RETIF-A>` ainda vivos** (548.652,07 + 94.018,81) | **0** |
| Movimentações Internas | −40.957,818 | SD3 OP-vazio, CF[3]≠'3' (INV DE0/RE0 net + DE6/RE6 net + RE0-503) a custos de emissão; por custo atual −40.958,297 | ~0,48 residual de precisão (TTAT_COLD) |
| Requisições p/ Produção | −666.114,374 | SD3 OP-preenchido não-PR (RE2+RE9+RE0-999-220) a custos de emissão (TTAT_COLD) | **0** |
| Transferências | 0,000 | SD3 CF∈{RE4,DE4} espelhadas (±259.794,011) | 0 |
| Produção | 0,000 | sem CF 'PR*' em MP | 0 |
| Vendas | 164.330,717 | SD2 poder3=N/est=S/tipo≠'D' `D2_CUSTO1` (TES 614/5101 + 590/6151) | **0** |
| Transf. p/ Processo | 940.599,335 | SD3 CF[3]='3' OP-vazio (RE3) a custos de emissão — **coluna memo fora da equação do saldo** | **0** |
| Devolução de Vendas | 264,681 | SD1 poder3=N/est=S/tipo='D' (TES 168/CFOP 1949) | **0** |
| Devolução de Compras | 4.732,694 | SD2 poder3=N/est=S/tipo='D' (CFOP 6201, TES 530/561) | **0** |
| Entrada Poder Terceiros | 319.258,140 | SD1 poder3≠'N'/est=S `D1_CUSTO` DTDIGIT-Set **sem os itens 085 do doc `<NF-RETIF-A>`** (422.860,14 − 103.602,00) | **0** |
| Saída Poder Terceiros | 36.806,805 | SD2 poder3≠'N'/est=S `D2_CUSTO1` (TES 524 × CFOP x903) | **0** |
| Saldo Atual | 3.364.910,314 | medida de saldo no estado de custo da emissão (01/10 16:16) | vs SB9@21/10: +8.631,73 (ver 31.D) |

Equação da linha MP (verificada ao centavo):
`SA = SI + Compras + MovInt + Requisições + Transf + Produção − Vendas
+ DevV − DevC + EntPT − SaiPT` — TransfProc fora da soma (memo).

### 31.D — Mecanismo unificado: retificação retroativa pós-emissão

Doc `<NF-RETIF-A>` (sanitizado; NF série 1, emissão 18/09,
digitação 22/09): cada item existe em **par espelhado** —

- `TES 001` **deletado** (`D_E_L_E_T_='*'`, RECNO 286517–286520,
  custo 94.018,81 — itens MP);
- `TES 085` **vivo** (RECNO 288137–288140, custo 103.602,00).

Os RECNOs 288137–288140 estão num bloco cujos vizinhos têm
`D1_DTDIGIT` = 20–21/10/2026 → **os itens 085 foram inseridos em
~20–21/10 com datas retroativas** (mesma onda do rebuild SB9 de
21/10 19:13 e do insert do doc `<NF-RETIF-B>`-085 em RECNO contíguo). Na emissão
(01/10 16:16) os itens eram 001/compra → explica **simultaneamente**:

- Compras impresso 642.670,88 = 548.652,07 + 94.018,81 (Δ 0,00);
- EntPT impresso 319.258,14 = 422.860,14 − 103.602,00 (Δ 0,00).

Demais linhas SD1 deletadas na janela (duplicatas `<DOC-DUPLICADO-A>`,
`<DOC-DUPLICADO-B>`, `<DOC-DUPLICADO-C>` etc., sanitizadas) são housekeeping anterior à emissão —
caso contrário os matches centesimais não fechariam.

### 31.E — Decomposição da divergência MP (SA impresso × SB9 atual)

`SB9@21/10 (B9_VINI1) = 3.373.542,05` vs `SA impresso = 3.364.910,31`
→ **+8.631,73**. Componentes demonstrados:

1. **Repricing da retificação** — os 4 itens do doc `<NF-RETIF-A>`
   trocaram custo 94.018,81 → 103.602,00 (**Δ +9.583,19**); dois dos
   produtos (`<PRODUTO-CUSTO-A>`, `<PRODUTO-CUSTO-B>`, sanitizados) constam no topo do relatório de
   variação de CM (`Analise.xlsx`) — o repricing integrou a
   revalorização do estoque.
2. **Recálculo de custo médio pós-emissão** — `MATA330` e rotinas
   correlatas regravaram `D3_CUSTO1`/`D2_CUSTO1` (25.995 updates no
   TTAT); reversão com `TTAT_COLD` reproduz os valores de emissão
   (matches exatos em RE3 e Requisições). A variação agregada por
   produto (`Analise.xlsx`, ΣQfinal×ΔCM ≈ +10,7k) é consistente em
   ordem de grandeza.
3. **Movimentos retroativos INVENT** (digitação ≤30/09, insert
   01/10 ~19h): líquido apenas **−24,95**.
4. **Residual** ≈ −950 (interações de repricing por produto/armazém e
   precisão do COLD) — INCONCLUSIVE no centavo.

Classificação: **DIFERENÇA EXPLICADA** (não paridade): os dois números
medem estados de custo distintos — SA@emissão (16:16, pré-retificação)
vs snapshot SB9 reconstruído em 21/10. A coluna `Saldo Atual` do
MATR320 é reproduzível **no estado de custo da emissão**, não no
estado atual.

### 31.F — Estado e preservações

- Nenhuma mutação de dados; todas as consultas SELECT.
- `EXECUTION_DRIFT`, `STALE_EVIDENCE`, `NO_GATE_CHANGE` preservados.
- Regras codificadas em doc 85 §5 (BR-R05-003…010); matriz de paridade
  em doc 84 §4; crosswalk doc 83.
- G5 para R05 permanece **PENDING** até paridade `as_of` centesimal
  demonstrada nas três medidas (E/S × P7 × H02) — SA depende de
  snapshot/versionamento explícito.

### 31.G — Frente B parcial: evidências estruturais do MATR460/P7

O fonte `matr460.prx` **não** consta no acervo (código padrão TOTVS, como a
SP MAT056). Evidências indiretas encontradas:

- `A460UNIT.prw` (hook Delpi no acervo): recebe `dDataFech`, `cLocOrig`
  (parâmetro `MV_ALMTERC`), `cArqTemp` e ajusta `TOTAL/VALOR_UNIT/QUANTIDADE`
  por produto — executa `UPDATE MP7GDA SET VALOR += workfile.TOTAL`. Confirma
  MATR460 = rotina do "Modelo P7" (tabelas `MP7*`).
- Banco contém arquivos de trabalho P7 persistidos:
  `MP7GDA` (PRODUTO/VALOR — ajuste do hook), `MP7_01_01`, `MP7_01_02`,
  `MP7_05_01`, `MP7_052019`, `MP7F01_202402`, `MP7F02_202402` — esquema
  `PRODUTO, ARMAZEM, DATAFECHAMENTO, NOMEARQ, TIPOMOV, QUANTIDADE, TOTAL`.
- `TIPOMOV` observado: **`aSalAtu`** (linhas de saldo por produto+armazém+
  data-fechamento), **`QtCus`** (linhas quantidade×custo), **`aDadosCF9`**
  (dados do registro fiscal de inventário — livro CF9). Dados persistem só
  até ~04/2024 — nada da competência 09/2026 (arquivo é recriado por
  emissão).
- Aritmética dos artefatos (doc 84 §3 + esta rodada):
  `EM ESTOQUE 3.591.191,36 + EM PROCESSO 355.240,51 = 3.946.431,87`
  = **TOTAL geral do `Estoque.pdf` ao centavo** → o P7 completo =
  EM ESTOQUE + EM PROCESSO, e EM PROCESSO = MATR989 (355.240,51 exato).
- `EM ESTOQUE total 3.591.191,36` vs `SA total MATR320 3.884.464,44`:
  Δ −293.273,08 ≈ estoque no armazém 99/LOCPROC (MP loc-99 = 293.674,80) —
  **hipótese forte não provada**: P7 EM ESTOQUE exclui armazém de
  processo (MV_LOCPROC=99), consistente com a existência de `MV_ALMTERC`
  no hook e com a seção EM PROCESSO separada. Confirmação depende dos
  parâmetros de emissão (E2) ou do fonte da SP.

### 31.H — Conciliação tripla E/S × P7 × H02 — comparabilidade

- `MATR320` mede **movimentação do período por tipo** (fluxo) com Saldo
  Atual como medida de estado à data de referência.
- `P7/MATR460` mede **posição de inventário** (EM ESTOQUE + EM PROCESSO)
  à data-fechamento, provavelmente por produto/armazém (`aSalAtu`).
- `H02/Bloco H` é o **registro fiscal do inventário** (SPED) — escopo
  fiscal/legal, distinto do operacional.
- As três medidas **não são diretamente confrontáveis** sem: (i)
  parâmetros de emissão do P7 (tipos/armazém/terceiros — E2);
  (ii) alinhamento de data-base e escopo; (iii) identidade da medida
  H02 no recorte. A equação canônica `DIVERGÊNCIA = E/S − P7 − H02`
  continua **não aplicável ao recorte atual** — pendência legítima, não
  falha de reconciliação. Requisito TARGET derivado: o portal deve
  expor cada medida com seu `as_of` e escopo, sem forçar igualdade.

---

## §32 — ERRATA DE SANITIZAÇÃO (CF-C2-HISTORICAL-SANITIZATION-001, 2026-10-23 — corrigida; data original registrada por engano como 05/11/2026)

Auditoria de confidencialidade retroativa sobre os docs do processo
PROC-0072 (Ciclo 1 e Ciclo 2 nesta pasta). Substituição de identificadores
operacionais por **aliases estáveis**; nenhuma regra, total, fórmula,
conclusão ou classificação foi alterada. O mapeamento original↔alias fica
sob custódia do owner, **fora do repositório**.

### Categorias sanitizadas

| Categoria | Aliases | Abrangência |
|---|---|---|
| Movimentos sem título excluídos do receber | `<RECEBIMENTO-SEM-TITULO-A..C>` | docs 47/80/84/85 |
| Movimentos sem título com provisão espelhada | `<MOV-PROV-A..G>` | docs 80/84/85 |
| NF de grupo (exemplo VO por soma de grupo) | `<NF-GRUPO-A>` | doc 84 |
| Título exemplo da baixa VL composta | `<TITULO-VL-A>` | doc 84 |
| Produto residual snapshot sem SD3 | `<PRODUTO-RESIDUAL-A>` | doc 80 |
| Produto da linha final H_ histórica | `<PRODUTO-H-A>` | doc 46 |
| Produtos citados como amostra no vídeo | `<PRODUTO-EXEMPLO-A/B>` | docs 56/57 |
| Produtos do repricing da retificação | `<PRODUTO-CUSTO-A/B>` | doc 80 (renomeado de `<prod-A/B>`) |
| Docs SD1 duplicados (housekeeping) | `<DOC-DUPLICADO-A..C>` | doc 80 (renomeado de `<dup-A..C>`) |
| Pessoa física (gestora do processo) | `<GESTORA-PROC>` | 23 docs — 132 ocorrências |
| Produtos divergentes SB9×MATR989 | `<PRODUTO-WIP-A..D>` | docs 80 §41/§42, 85 §8, 84 §5.2 |
| PAs âncora/seriais/residuais do Fat×MOD | `<PA-ÂNCORA-*>`, `<PA-SERIAL-*>`, `<PA-RESIDUAL-R09-*>` | docs 80 §43, 85 §9, 84 §5.3 |
| Produto exemplo da hipótese QTNP (R03) | `<PRODUTO-QTNP-A>` | doc 80 §35 (sanitizado rodada 24) |
| Produtos de benefícios saúde/odonto excluídos do R10 | `<PRODUTO-BENEFICIO-*>` | docs 80 §44, 82 E10 |

Os aliases `<NF-RETIF-A>`/`<NF-RETIF-B>` da rodada anterior foram
mantidos — mesmo objeto real = mesmo alias em todos os documentos.

### Preservado por decisão classificada (risco baixo, necessidade técnica)

- `R_E_C_N_O_`/RECNOs: posições físicas de linha — necessárias à prova de
  timing da onda retificadora; sem utilidade fora de acesso direto ao DB.
- Códigos de centro de custo (`02/03/05/0401/0404/0405/0504/030101`),
  prefixos `MOD*`, TES/CFOP: códigos técnicos necessários às regras.
- Nomes de tabelas/colunas/rotinas/fontes, `MP7_*`, `H_*`, `SCGN*`,
  nome do arquivo de vídeo, SHAs/commits/blobs/UUIDs/job-ids, datas,
  totais e resíduos de paridade.

### Histórico Git

Os valores originais permanecem em commits anteriores (a sanitização
altera somente o HEAD). Classificação: identificadores operacionais de
documentos fiscais/títulos/produtos + 1 nome de pessoa — exposição de
baixa severidade em repositório privado; **nenhuma credencial, segredo
ou dado financeiro de contraparte identificado**. Contenção adicional
(reescrita de histórico) fica registrada como `DECISION_REQUIRED` para o
owner de segurança — não executada nesta rodada.

---

## §33 — RODADA 15 (CF-C2-STOCK-RULES-CONSOLIDATION-002) — FECHAMENTO R05 + BINDING P7 LOCPROC — 2026-10-23

Continuação de §31 (R05/MATR320) e §31.G (R03/P7). SELECT-only
via `delpi-api-delpi` (mesma autorização READ da rodada anterior).

### A. Residual MovInt R$0,48 — RESOLVIDO (Δ 0,000)

O residual de ~R$0,48 em Movimentações Internas (§31.B) era **artefato
de reconstrução**: a reversão `TTAT_COLD` foi aplicada em excesso.
Com corte estrito em `TTAT_DTIME > 2026-10-01 16:16:27` (timestamp de
emissão), apenas 8 updates pós-emissão existem no grupo MovInt
(par espelhado doc `<DOC-MOVINT-A>` + 6 linhas `INVENT` repriced por
`MATA330`). Reversão correta:

- MovInt emissão = **−40.957,818** = impresso **exato** (Δ 0,000).
- Linhas INVENT foram inseridas 16:02–16:14 de 01/10 (antes da
  emissão) — `A340INVPRO`/RPC; repricing pós-emissão mínimo (+0,018
  líquido no grupo).
- Linhas deletadas/estornadas do grupo são **pares espelhados**
  (DE↔RE mesmo doc/valor) → líquido zero; não explicavam residual.
- `D3_DTLANC` vazio em **todas** as 1.050 linhas do grupo → não é
  discriminante.
- `SP MAT056` não existe como objeto legível no banco (`sys.procedures`
  vazio) — execução interna Protheus; lógica `.prx` segue como espelho.

**Regra derivada:** reconstrução `as_of` via TTAT exige corte por
`TTAT_DTIME > timestamp_de_emissão` — reverter updates anteriores
introduz erro artificial.

### B. Ponte quantitativa R$8.631,73 — DECOMPOSIÇÃO COMPLETA

Modelo por produto (MP, filial 01, todos os armazéns):

```
V_emissão_p = B9_VINI1@0831_p + SD1_p(DTDIGIT-set, ESTOQUE=S)
              − SD2_p(EMISSAO-set, CUSTO1@emissão)
              + SD3_p(signed, CUSTO1@emissão, exclui TransfProc-RE3)
residual_p  = B9_VINI1@0930_p − V_emissão_p
```

Nota de modelo: `TransfProc` (CF `RE3`, armazém de origem, sem DE par)
é excluído porque o valor **permanece no estoque da filial**
(armazém 99) — consistente com a coluna memo do relatório.

**Σ residual = +8.631,741** vs Δ oficial +8.631,731 — **superseded por
§34:** a diferença de −0,010 não é arredondamento: é a revalorização
pós-emissão da linha RE0 RECNO `4817031` (60,760→60,770, `MATA330`
21/10 08:01) + ruído ±0,001–0,002 de outros 4 produtos com TTAT
própria; com `CAST(... AS DECIMAL(30,9))` a ponte fecha **exato**
(+8.631,731 = Δ oficial). Decomposição por produto — **apenas 5**:

| Produto (alias) | Residual | Mecanismo evidenciado (TTAT) |
|---|---:|---|
| `<PRODUTO-CUSTO-A>` | +5.270,252 | repricing onda retificadora: inserts RPC 01-02/10 + `MATA241`/`MATA330` |
| `<PRODUTO-CUSTO-B>` | +3.190,169 | `MATA330` 21/10 07:59-08:00 regravou `D3_CUSTO1` ~+7% (8.602→9.274 etc.) |
| `<PRODUTO-REVAL-A>` | +148,000 | repricing custo pós-emissão (RPC/`MATA460A`) |
| `<PRODUTO-REVAL-B>` | +23,292 | idem |
| `<PRODUTO-REVAL-C>` | +0,028 | `INVENT` repriced (259.473→259.501) |

Os dois produtos da retificação concentram +8.460,42 (98%); os demais
+171,32 são micro-revalorizações do mesmo recálculo de custo médio.
**A divergência é integralmente drift de estado de custo** entre a
emissão (01/10 16:16) e o rebuild SB9 (21/10 ~19:13) — não é erro de
relatório nem medida divergente.

Agregados conferem o estado de emissão ao centavo:
ΣSD1 962.193,70 = Compras+EntPT+DevV · ΣSD2 205.870,22 =
Vendas+SaiPT+DevC · ΣSD3(ex-RE3) −707.072,19 = Requis+MovInt.

### C. A3 — reconciliação expandida: 10 tipos × 13 colunas

Reprodução das regras `matr320.prx` para **todos os tipos** (EM, GG,
II, MC, MH, MP, MS, MX, PA, PI) no estado de emissão:

| Resultado | Cobertura |
|---|---|
| 12 colunas de fluxo | **120/120 exatas** (\|Δ\| < 0,01) — inclui MP |
| Saldo Atual | **9/10 exatos**; único Δ = MP +8.631,73 (decomposto em B) |

Conclusão: as regras de classificação SD1/SD2/SD3 são **gerais**
(valem para todos os tipos), não específicas de MP. PA `Produção`
só fecha com reversão COLD — confirma que MATA330 regravou custos
de produção após a emissão.

### D. R03/P7 — binding EM ESTOQUE ↔ armazém de processo — `PROVEN`

Hipótese §31.G (P7 EM ESTOQUE exclui `MV_LOCPROC='99'`) **demonstrada
centesimalmente**:

```
B9_VINI1@0831[loc99]  =   215.673,929
+ RE3 in (TransfProc) =   940.599,335   (débita loc 01, credita processo)
+ SD3 loc99 líquido   =  −863.000,176   (RE2/RE9/RE4 saídas − DE0/DE4)
= V_emissão loc99     =   293.273,088
SA_emissão (impresso) − loc99_emissão
= 3.884.464,444 − 293.273,084 = 3.591.191,36 = EM ESTOQUE P7 ✓
```

Δ residual 0,004 (float). Interpretação funcional:

- `EM ESTOQUE` P7 = **saldo físico excluindo o armazém de processo**
  (`MV_LOCPROC='99'`), medido no `as_of` da emissão.
- `EM PROCESSO` P7 = **MATR989** (saldo alocado a OPs) — medida
  distinta do estoque físico de loc 99 (355.240,51 ≠ 293.273,08);
  ambos "material em processo" sob óticas diferentes (OP-alocado vs
  armazém-físico). **Não confundir as duas medidas.**
- `SA MATR320` (3.884.464,44) inclui loc99; `VINI1@0930` atual de
  loc99 = 293.722,38 (drift +449,30 da mesma onda de repricing).
- Emissão `Resumo Estoque.pdf` (MP/PA/PI; EM ESTOQUE 2.699.026,36 +
  EM PROC 277.941,20) tem `as_of`/parâmetros **diferentes** — não
  reconciliável com o snapshot; `PENDING` parâmetros (E2).

Cadeia física consolidada: `MATR460 → workfile MP7* (+ hook A460UNIT
ajustes MP7GDA) → saldo físico ex-99 (SB9-like no as_of) + MATR989 →
relatório`. Parâmetros efetivos por emissão e fonte `matr460.prx`
permanecem `PENDING` (E2) — o binding de **totalização** está provado,
o binding de **parametrização** não.

### E. Conciliação tripla E/S × P7 × H02 — incompatível no recorte

O relato operacional (doc 03) registra a conferência
`E/S 3.890.247,18 − P7 3.776.994,69 − H02 64.591,71 = 48.660,78`
("resíduo"). As três parcelas pertencem a **emissões e medidas
diferentes**: E/S do relato ≠ artefato MATR320 (3.884.464,44; Δ
5.782,74 — outra emissão/estado); P7 do relato = emissão iterativa
30/09 (não a final); `H02` = medida não identificada (`TO_INVENTORY`
— provável total do bloco H02 do registro de inventário, escopo
fiscal, não saldo contábil). A soma `E/S−P7−H02` só converge para
0,00 se as três parcelas compartilharem `as_of`, escopo de armazém/
tipo e base de custo — condição **não satisfeita** nos dados
disponíveis. "Insumos 266.321,45" do relato = SA tipo II do MATR320
(exato) — indica que a conferência operacional já usa SA por tipo,
não o total geral.

**Requisito TARGET consolidado:** a conciliação exige que cada medida
carregue `as_of`, `escopo` (tipos/armazéns) e `base_de_custo`
explícitos; comparar totais de emissões distintas produz "resíduo"
estrutural, não divergência real.

### F. Temporalidade consolidada (B4)

| Instante | Evento |
|---|---|
| 30/09 ~14:47 | emissões iterativas P7 (vídeo) — totais variam |
| 01/10 16:01 | `MATA330` recálculo CM (updates `D3_CUSTO1`) |
| 01/10 16:02–16:14 | inserts `INVENT` (A340INVPRO) |
| 01/10 16:16:27 | emissão MATR320 (`as_of` das colunas) |
| 01/10 ~16:58 | `Material em processo.xlsb` (MATR989 → EM PROCESSO P7) |
| 20–21/10 | onda retificadora: reclass `001→085` (NF-RETIF-A), inserts retroativos |
| 21/10 07:59–08:00 | `MATA330` repricing +7% nos produtos da retificação |
| 21/10 ~19:13 | rebuild SB9 f01 (`VINI1@0930` gravado) |
| (verificação) 23/10 | ponte por produto: Δ +8.631,73 = revalorização de 5 produtos |

`as_of` distintos: colunas MATR320 = 01/10 16:16; P7 EM ESTOQUE =
mesmo estado (SA − loc99 provado); EM PROCESSO = estado MATR989
~16:58; SB9@0930 = 21/10. Classificação: competência 09/2026,
`as_of` por parcela, versão de processamento por execução.

### G. Execução, autorização e classificação

- **GO utilizado:** decisão PO §12 (23/10/2026) —
  `D1-D4_READ_DISCOVERY=AUTHORIZED_WITH_VERIFIED_READ_ONLY_PRINCIPAL`;
  principal confirmado somente-leitura. Nenhuma consulta nova fora do
  GO; nenhum pedido de permissão adicional.
- **SQL executado (SELECT-only):** agregações SD1×SF4
  (`F4_ESTOQUE='S'`, `D1_DTDIGIT`), SD2×SF4 (`D2_EMISSAO`), SD3 por
  `D3_CF`/`D3_OP`/`D3_TM`/`D3_ESTORNO`/`D3_LOCAL`/`D3_LOCALIZ` com
  reversão `TTAT_COLD` cortada em `TTAT_DTIME > 2026-10-01 16:16:27`;
  SB9 `B9_VINI1` por produto/armazém @0831/@0930; TTAT por RECNO
  (`TTAT_FIELD`, `TTAT_OPERATI`, `TTAT_PROGRAM`, `TTAT_DTIME`).
- **READ-only confirmado:** zero DML/DDL; `sys.procedures` consultado
  apenas para constatar ausência de `MAT056` legível.
- **Scripts de investigação:** temporários no worktree
  (`scripts_tmp_bridge_a2.py`, `scripts_tmp_types_a3.py`,
  `scripts_tmp_b3_loc99.py`) — não versionados; fórmulas e resultados
  consolidados nesta seção e no doc 85.
- **Classificações aplicadas:** `PROVEN` (binding de totalização P7,
  MovInt Δ0,000, 120/120 colunas, ponte MP por produto); `PENDING`
  (parametrização P7 por emissão, fonte `matr460.prx`, emissão
  resumida, medida H02 — E2/E5); `TARGET` (exposição de `as_of`/
  escopo/base_de_custo por medida). Nenhum requisito material
  descartado; nenhum gate promovido além do demonstrado.

---

## §34 — RODADA 16 (CF-C2-STOCK-G5-REWORK-001) — VERIFICAÇÃO G5: PARIDADE AO CENTAVO — 2026-10-23

Revisão do commit `df4d7caa5d`: promoção de G5 exigia demonstrar (i) a
paridade efetiva do Saldo Atual oficial na emissão e (ii) a origem do
centavo entre +8.631,741 (ponte) e +8.631,731 (delta oficial).

### A. Precisão dos campos e ordem de agregação

- `B9_VINI1`, `B9_QINI`, `D1_CUSTO`, `D2_CUSTO1`, `D3_CUSTO1` =
  **float(53)** (INFORMATION_SCHEMA) — representação binária, não
  decimal; o relatório imprime 3 casas.
- Reprodução exata: `CAST(B9_VINI1 AS DECIMAL(30,9))` **por linha,
  antes do SUM** (agregação em float acumulou erro binário e produziu
  o falso −0,010 da rodada 15). Custos de movimento via
  `Decimal(str(v))` + reversão `TTAT_COLD` por RECNO.

### B. Reprodução das 130 células oficiais — Δ 0,000

Recalculadas 10 tipos × 13 colunas em estado de emissão
(`D1_DTDIGIT`/`D2_EMISSAO`/`D3_EMISSAO` set/2026, SF4 `F4_ESTOQUE=S`,
`D3_ESTORNO<>S`, RE3 memo fora da equação, custos ao `as_of`
01/10 16:16:27 via TTAT):

| Medida | Resultado |
|---|---|
| 120 células de fluxo (12 × 10 tipos) | **Δ = 0,000 em todas** |
| Saldo Atual por equação de fluxo (10 tipos) | **Δ = 0,000 em todos** — inclui MP: `V_emissão = 3.364.910,314` = SA impresso |
| SA × snapshot SB9@0930 (referência, não célula oficial) | 8/10 Δ = 0,000; PI Δ = −0,001; MP Δ = +8.631,731 (decomposto em C) |

### C. Origem exata do centavo — ponte fecha Δ = 0,000

Com agregação decimal: `Σ residual_p = +8.631,731` = delta oficial
(`VINI1@0930_MP − SA_impresso`) — **discrepância 0,000**.

| Parcela | Valor | Evidência |
|---|---:|---|
| 5 produtos revalorização (ondas RPC/`MATA241`/`MATA330` 20-21/10) | +8.631,741 | TTAT por RECNO (§33.B) |
| `<PRODUTO-REVAL-D>` — linha RE0 RECNO `4817031` `D3_CUSTO1` 60,760→**60,770** por `MATA330` 21/10 08:01:26 | **−0,010** | `SD3010_TTAT_LOG` (U) |
| 4 produtos (`<PRODUTO-AJUSTE-A..D>`) micro-ajustes TTAT pós-emissão | +0,002 / −0,002 / −0,001 / +0,001 = **0,000** | TTAT próprias |
| **Total** | **+8.631,731** | = Δ oficial, exato |

Balancete do produto `<PRODUTO-REVAL-D>` (prova linha-a-linha):
loc01 `962,449 − RE3 425,608 = 536,841` ✓ · loc99 `192,617 + RE3
425,608 − req 192,620 = 425,605` ✓ — o −0,010 é o custo de
requisição regravado em +0,010 após a emissão, absorvido no rebuild
SB9 de 21/10.

### D. Corolário — binding P7 loc99 também é exato

O Δ 0,004 de §33.D era **arredondamento de impressão** do EM ESTOQUE
(2 casas), não drift: `loc99_emissão = 293.273,088` exato →
`EM ESTOQUE = 3.884.464,444 − 293.273,088 = 3.591.191,356`, que
imprime `3.591.191,36`. O binding `EM ESTOQUE = saldo ex-loc99 no
as_of` é **exato na precisão impressa** — resta `PENDING` apenas a
parametrização/produtor (E2), não a aritmética.

### E. Decisão e escopo

- **130/130 células oficiais reproduzidas no `as_of` de emissão com
  Δ = 0,000** → **R05 G5 PASS mantido** (G4 PASS inalterado; G6
  PENDING — aceite funcional).
- A divergência SA × snapshot posterior é drift temporal **fechado ao
  centavo** (não residual): +8.631,741 revalorização − 0,010 linha
  RE0 + 0,000 micro-ajustes.
- Classificações: `PROVEN` (130/130 células, ponte MP ao centavo,
  origem do centavo); escopo = emissão MATR320 01–30/09/2026 filial
  01 apenas. SQL: SELECT-only, GO §12.

## §35 — RODADA 17 (CF-C2-P7-PARAMETERS-PARITY-001) — DECOMPOSIÇÃO DA EMISSÃO RESUMIDA P7 — 2026-10-23

Escopo: somente resíduos de R03 (P7/MATR460). SQL SELECT-only via
`delpi-api-delpi` (GO §12). Nenhuma reabertura de R05/R01/R02; nenhuma
mudança de gate nesta rodada.

### A. Estrutura das emissões — fatos observados

- `Estoque.pdf` = **FOLHA 000.101** de um "REGISTRO DE INVENTÁRIO"
  (MATRIZ, `ESTOQUES EXISTENTES EM: 30/09/2026`) — resumo com **10
  classificações fiscais** em EM ESTOQUE (3.591.191,36) + EM PROCESSO
  (355.240,51) → TOTAL GERAL **3.946.431,87**.
- `Resumo Estoque.pdf` = **FOLHA 000.074** de uma emissão **distinta**,
  mesmo layout e mesma data-base — resumo com **apenas MP/PA/PI**
  (EM ESTOQUE 2.699.026,36 + EM PROCESSO 277.941,20) →
  **2.976.967,56**.
- Fato decisivo: **PA e PI são idênticos nas duas folhas**
  (EM ESTOQUE 190.511,24 / 24.528,60; EM PROCESSO PI 254,44) → ambas
  usam a **mesma base temporal e o mesmo estado de custo**. A
  divergência é exclusiva de MP: `EM ESTOQUE −587.698,28`;
  `EM PROCESSO −77.251,73`.
- Vídeo (frames 35:00–38:00): abas simultâneas
  "Registro de Inventário Módulo P7" (≥3), preview intermediário
  30/09 15:06 (TOTAL 3.776.994,69), MATR320 14:53 anterior, preview
  15:08 já no escopo MP/PA/PI (MP EM ESTOQUE ≈2.483.070 — consistente
  com estado parcial de gravação do fechamento).

### B. Produtor — confirmado vs pendente

- **Confirmado:** rotina de menu "Registro de Inventário Modelo P7" →
  `MATR460`; grupo de parâmetros **SX1 `MTR460` (25 perguntas)**
  extraído integralmente (doc 85 BR-R03-008). Não existe grupo
  `MTR460A`; `MTA460` pertence a faturamento; `MTR470` é livro de
  movimentações (outra rotina).
- Cadeia de execução candidata confirmada estruturalmente:
  `MATR460 → MP7_*(workfiles) → MP7GDA (agregação produto) → A460UNIT
  (hook custom) → relatório`. `MP7_*` retêm competências só até
  ~04/2024 — a da emissão não sobrevive (`MP7GDA` remanescente:
  78 produtos ≠0, Σ 539.330,11).
- **Pendente:** fonte `matr460.prx`/RPO compilado — não inferido
  `CODE_DEPLOYED`. Semântica exata do parâmetro `02 Saldo em
  Poder 3º ?` (Sim/Não/De Terceiros/Em Terceiros) não demonstrável
  sem fonte.
- SX6 vigente: `MV_LOCPROC='99'`, `MV_CQ='98'`, `MV_CQREJEI='50'`,
  `MV_ALMTERC` vazio.

### C. Hipóteses testadas e descartadas (com evidência)

| Hipótese para Δ MP EM ESTOQUE (−587.698,28) | Resultado |
|---|---|
| Filtro de armazém | MP ex-99 = 3.071.684,80; nenhum subconjunto de armazéns = alvo (loc01 sozinho = 3.008.095,45) — **descartada** |
| `as_of` temporal (qualquer cutoff 01/09–01/10) | varredura não atinge 2.483.986,52; PA/PI idênticos contradizem — **descartada** |
| Faixa/prefixo de produto | nenhuma partição por prefixo = 587.698,28; PA(7xxx)/PI(alfanumérico) não formam range único — **descartada** |
| Produtos sem movimento em setembro | 1.273.803 ≠ alvo — **descartada** |
| Exclusão poder3 por **quantidade** (QTNP×custo, SB6×custo) | 731.759 / 681.078 / 670.628 — **descartada** |
| Emissão intermediária (SB9 regravado progressivamente) | reconstrução por prefixo de código não fecha; PA/PI idênticos contradizem — **descartada** |

### D. Melhor modelo — exclusão por conjunto de produtos poder3

- **MP EM ESTOQUE:** excluir do universo ex-99 os produtos com
  `QTNP@emissão>0` (B2_QTNP corrente revertido por movimentos
  `F4_PODER3='R'/'D'` inseridos após 01/10 16:16:27) →
  **587.621,85** vs alvo 587.698,28 — **residual 76,43** (0,013 %).
  Nenhum produto fora do conjunto vale 76,43 (subset-sum ambíguo:
  centenas de combinações; ex.: `<PRODUTO-QTNP-A>`=71,21 SB6-R aberto sem QTNP).
- **MP EM PROCESSO:** mesma família — soma MATR989 dos produtos
  `QTNP@emissão>0` = **79.194,35** vs alvo 77.251,73 —
  **residual +1.942,62**. Composição: tipo '' 64.388,66 + RE9
  12.410,84 + RE2 2.394,85 + RE1/RE0 0. Nenhuma partição por
  `TIPO RE/DE`, OP poder3 (SC2 `C2_OPTERCE`/`C2_STTERCE` só PI/PA) ou
  produto-fronteira fecha o centavo.
- Direção dos residuais: estoque precisa **+76,43** de exclusão
  (resumo exclui mais), processo precisa **−1.942,62** (resumo
  exclui menos) — incompatível com simples mudança de `as_of` do
  conjunto QTNP; sugere diferença de **medida** (posição poder3 por
  movimento, workfile `aDadosCF9`, ou estado QTNP de outro instante).
- **Classificação:** `PROVEN` — o resumo aplica regra de exclusão de
  material poder-de-terceiros sobre MP (direção e magnitude provadas;
  MTR460 param 02 existe e é a regra candidata). `PENDING` —
  população exata (QTNP vs SB6 vs workfile), instante do conjunto e
  mecanismo de escopo de tipos (MTR460 não tem parâmetro de tipo;
  possível multi-seleção de tipos na UI ou variante custom).

### E. Matriz de parâmetros (observado × inferido × ausente)

| Parâmetro | P7 completo (folha 101) | P7 resumo MP/PA/PI (folha 74) | Fonte |
|---|---|---|---|
| Rotina | Reg. Inventário Modelo P7 (MATR460) | idem (mesmo layout/data-base) | PDFs, vídeo |
| Data de Fechamento | 30/09/2026 | 30/09/2026 | cabeçalho |
| Filial | 01 MATRIZ | 01 MATRIZ | cabeçalho |
| Tipos de produto | todos (10 classificações) | MP/PA/PI | resumos |
| `Saldo em Poder 3º ?` | incluído (provado: total bate ex-99 integral) | excluído ≈QTNP@emissão (99,987 %; Δ76,43) | reconstrução |
| `Saldo em Processo ?` | Sim | Sim | seções EM PROCESSO |
| Lista Custo | Médio (PA/PI = B2_CM1 exato) | idem | valores idênticos |
| Timestamp execução | ~01/10 16:16 (binding custo) | desconhecido (folha 74 < 101 ≠ ordem) | binding/vídeo |
| Demais parâmetros MTR460 | ausentes nos artefatos | ausentes | — |
| Estado de homologação | aceito como referência | não homologado — pendente E2 | — |

### F. Timeline P7 (competência 09/2026)

`30/09 ~14:47` início fechamento (wizard custo) → `14:53` MATR320
(SA MP 3.370.493,537) → `15:06` P7 preview total (3.776.994,69) →
`15:08` P7 escopo MP/PA/PI (estado parcial) → `01/10 16:15:58`
MATR989 "Material em processo" → `01/10 ~16:16` P7 completo oficial
+ MATR320 oficial → `02/10` movimentos poder3 (rec +138.885 u /
dev −152.921 u) → `21/10 19:13` regravação integral SB9@0930.

### G. Decisão de gate

- **R03 G4: PENDING (parcial PROVEN)** — bindings físicos e
  totalização do completo demonstrados; parâmetros efetivos por
  emissão só parcialmente demonstrados (escopo de tipos e regra
  poder3 sem prova centavo nem fonte).
- **R03 G5: PENDING** — resumo não reproduzido ao centavo
  (Δ estoque 76,43 / Δ processo 1.942,62); sem linhas de produto da
  emissão resumida nem fonte do produtor, a população exata é
  ambígua por subset-sum.
- R03 G6 PENDING (aceite Controladoria). R05 G4/G5 PASS preservados.
- `NO_GATE_CHANGE`. Residual mínimo p/ owner: (1) parâmetros da
  emissão resumida (print das perguntas ou log mv_par); (2) linhas
  de produto da folha 74 (PDF completo da emissão resumida);
  (3) fonte/RPO do MATR460 implantado (semântica poder3 + escopo
  de tipos).

## §36 — ERRATA (CF-C2-P7-E2-HANDOFF-001) — CLASSIFICAÇÃO DE BR-R03-007 — 2026-10-23

Correção de classificação sobre §35.D — **nenhum fato foi alterado**;
apenas a fronteira entre fato e hipótese:

- `PROVEN` (fatos observados, doc 85 BR-R03-007): a emissão resumida
  apresenta somente MP/PA/PI; as diferenças entre as duas emissões
  concentram-se exclusivamente em MP; existe o parâmetro SX1 `MTR460`
  pergunta 02 `Saldo em Poder 3º ?` (Sim/Não/De Terceiros/Em
  Terceiros).
- `PENDING` (não demonstrado): qual opção foi selecionada em cada
  emissão; se essa opção explica a exclusão observada; a população
  exata de produtos/valores; a semântica interna do MATR460
  compilado.
- O modelo `QTNP@emissão` (estoque 587.621,85 → Δ **76,43**;
  processo 79.194,35 → Δ **+1.942,62**) permanece como **hipótese
  empiricamente sustentada** — melhor ajuste entre as candidatas,
  mas **não é regra oficial** e não deve ser lido como prova de que
  o parâmetro poder3 foi o mecanismo utilizado. O texto de §35.D que
  sugeria "o resumo aplica regra de exclusão poder3" fica supersedido
  por esta classificação.
- Consequência: R03 G4/G5 permanecem `PENDING`; encerramento
  condicionado ao pacote E2.1/E2.2/E2.3 do doc 82 §2.1 (parâmetros
  efetivos, linhas de produto da folha 74 e produtor implantado).

## §37 — RODADA 19 (CF-C2-KARDEX-CPV-INVENT-PARITY-001) — RECONSTRUÇÃO FÍSICA DO KARDEX MATR910 — 2026-10-23

### §37.A — Preparação e GO

- HEAD `303104af38` (sincronizado com `origin/main`, fast-forward a partir
  de `146170360d`). `IMPLEMENTATION_AUTHORIZED=NO`; somente SELECT via
  `delpi-api-delpi`; artefatos originais lidos via Excel COM (XLSB → CSV
  temporário, fora do Git).
- Artefatos: `cpv 09 26 matriz.xlsb` (R06, emissão 01/10/2026 16:58) e
  `Invent.xlsb` (R07), ambos já custodiados — não requisitados ao PO.

### §37.B — Inventário estrutural dos XLSB (Frente A)

- `cpv 09 26 matriz.xlsb`: 1 aba "01-02 - Kardex Fisico-Financei",
  **14.382 linhas × 16 col** = **1.544 blocos de produto** + **9.357
  linhas de movimento** + ~379 cabeçalhos repetidos + 1.544 linhas de
  "segunda UM" + linhas de posição IPI/endereço. **0 blocos sem
  movimento** — as 14.382 linhas NÃO são movimentos.
- `Invent.xlsb`: 1 aba `Planilha2`, **50 linhas × 12 col** = **45
  movimentos efetivos** `INVENT` + linhas em branco/agregação. Totais:
  entradas 2.348,108 / R$185.103 · saídas 30.808,206 · líquido
  **−28.460,098**.
- Competência: todos os movimentos em 09/2026; escopo efetivo **filial
  02 / loc 01** (R06) e loc 01+99 (R07).

### §37.C — R06: produtor e modelo físico (Frentes B/C/D)

- **Produtor `PROVEN`:** rotina "Kardex" ≡ **MATR910**; fonte
  `matr910_dlp.prx` no acervo (`SOURCE_AVAILABLE`; `CODE_DEPLOYED`
  pendente — E7). Comportamento observado 100% compatível com o fonte.
- **Modelo:** UNION SD1+SD2+SD3 por produto (join SB1; SD1/SD2 join SF4
  `F4_ESTOQUE='S'`), filtros `D3_ESTORNO<>'S'`, `D*_ORIGLAN<>'LF'`,
  `D*_LOCAL=mv_par08`, `D1_REMITO=''`, ranges SB1 (produto/tipo/grupo).
- **Competência por tabela:** SD1=`D1_DTDIGIT`, SD2=`D2_EMISSAO`,
  SD3=`D3_EMISSAO` — provado por contagens e por casos digitação≠emissão.
- **Ordenação:** data + `*_NUMSEQ` — 1.971/1.971 grupos mesma-data
  consistentes com `D3_NUMSEQ` (mv_par16=Digitação).
- **REF:** `F-`+`D1_FORNECE` (260/260), `P-`+`D2_PEDIDO` (594/594),
  `OP`+`D3_OP` (6.060/6.060), `CC`+`D3_CC` (~2.443).
- **Custos:** `D1_CUSTO`/`D2_CUSTO1`/`D3_CUSTO1` moeda 1 **as_of da
  emissão** — 9.346/9.357 (99,88%) com vínculo (corrente ou `TTAT_OLD`
  de revalorização pós-emissão). Identidade linha-a-linha verificada por
  blocos.
- **Saldos:** inicial = `CalcEst` ≡ `B9_QINI`/`B9_VINI1` @2026-08-31
  (1.544/1.544 exato); cadeia contínua até o saldo impresso
  (1.544/1.544). Sinais negativos ficam na coluna do movimento
  (devolução SD2 → entrada negativa; estorno-compra SD1 → saída
  negativa).
- **População:** só produtos com ≥1 movimento elegível; 26 `MOD*` tipo
  `MO` fora (sem SB9); 1.426 produtos SB9 sem movimento elegível fora
  (1.023 com saldo≠0) — relatório de movimento, não de posição.
- **CPV (`AS-IS`):** saídas agregadas ≠ CPV — misturam requisições de
  produção (RE1/RE3 dominantes), vendas NF (5101/6101/7101), devoluções,
  transferências e INVENT. Sem escopo de medida, nenhum total do relatório
  é igualável ao CPV — `DECISION_REQUIRED` para a medida.

### §37.D — R07: inventários (Frente E)

- `Invent.xlsb` = mesmo MATR910 filtrado a `D3_DOC='INVENT'`, TES
  999/RE0 (saída) e 499/DE0 (entrada), filial 02 loc 01+99.
- **45/45 linhas vinculadas ao SD3** — 35 match direto + 10 via
  `TTAT_OLD` de `D3_CUSTO1` (revalorização pós-emissão; ex.: 1.330,650
  impresso vs 1.331,299 corrente). Sem misses residuais de população no
  escopo observado.

### §37.E — Temporalidade (Frente F)

- Linha do tempo: emissão kardex 01/10 **16:58** → recálculo MATA330
  ~17:5x (TTAT `D3_CUSTO1` em massa) → regravação SB9@0930 em 21/10.
- Custos impressos = `as_of` de emissão; ~1.981 linhas divergentes do
  custo corrente resolvem via `TTAT_OLD`.
- Saldo final kardex vs SB9 corrente: **354 produtos divergem só em
  valor** (Δqtd=0 em todos) — 227 < R$1, 127 ≥ R$1 — drift de
  revalorização posterior, `STALE_EVIDENCE` na comparação corrente, não
  defeito do relatório (cadeia interna 100% consistente).

### §37.F — Paridade (Frente G)

- Identidade de linha: 9.357/9.357 (R06) e 45/45 (R07) verificado por
  blocos; custos 99,88% direto+TTAT; saldos iniciais 100%; ordenação
  100%; REF 100%. Matriz detalhada no doc 84 §5.1.
- Hipóteses descartadas com evidência: filial 01 (população não bate),
  data única de emissão para SD1 (digitação provada), saldo por recálculo
  inverso (batimento exato com `B9`@0831), inclusão de estornos (pares
  ausentes com linha limpa presente).

### §37.G — Gates

- **R06: G4 PASS, G5 PASS** — origem física, filtros, joins, ordenação,
  custos `as_of` e cadeia de saldo demonstrados + paridade linha-a-linha
  reproduzível (residual temporal classificado, não erro).
- **R07: G4 PASS, G5 PASS** — 45/45 ajustes INVENT vinculados, semântica
  TES/CF/saldo provada, totais reconciliados.
- **G6: PENDING** (aceite funcional Controladoria). R01–R05 inalterados.
- Métricas: `COLETA 42/60 = 70,0%` · `AUDITORIA 47/90 = 52,2%`.

## §38 — ERRATA/REFINAMENTO (CF-C2-KARDEX-R06-G5-REWORK-001) — AS 11 LINHAS — 2026-10-23

Correção de precisão sobre §37.C/§37.F — **nenhum fato econômico muda**;
apenas o denominador do vínculo de custo:

- A métrica "9.346/9.357 (99,88%)" provinha do **roteamento estrito** da
  reconciliação inicial (entrada-NF→SD1, saída-NF→SD2). As 11 linhas
  remanescentes eram `NO_KEY` de roteamento — não divergência de custo.
- **4 linhas `entrada−` (NEG-E-01..04):** origem física **SD2**,
  `TIPONF='D'` — devolução de compra (TES 561/530, CF 6201/5201). O
  MATR910 imprime `QUANTIDADE×−1`/`CUSTO×−1` na coluna **entradas**
  quando `MV_LISTDEV` ativo — função `zMTR910Dev` no fonte
  (dbSeek `SF2` + `TIPONF='D'`). Efeito: `aSalAtu −= QUANTIDADE`
  (devolução sai do estoque). Custo = `D2_CUSTO1` corrente **exato**.
- **7 linhas `saída−` (NEG-S-01..07):** origem física **SD1**,
  `TIPONF='D'` — devolução de venda (TES 120, CF 2201). Impressas como
  negativos na coluna **saídas** (dbSeek `SF1` + `TIPONF='D'`). Efeito:
  `aSalAtu += QUANTIDADE` (mercadoria retorna). Custo = `D1_CUSTO`
  corrente **exato**.
- As 11 linhas pertencem a 11 blocos distintos; efeito nos saldos coberto
  pela cadeia já verificada (1.544/1.544) — a conferência do custo
  individual não depende da consistência do saldo.
- **Estado final da paridade de custo R06: 9.357/9.357 (100%)** =
  7.376 `CUR` direto + 1.981 `TTAT_OLD` (revalorização pós-emissão).
  Zero diferença sem explicação.
- Decisão: **R06 G5 PASS mantido** (reinforcing evidence, não relaxamento);
  R07 G4/G5 inalterados; G6 PENDING. Métricas inalteradas
  (42/60 · 47/90).

## §39 — CPV EXISTING RULE VERIFY (CF-C2-CPV-EXISTING-RULE-VERIFY-001) — 2026-10-23

Rodada READ/VERIFY/DOCUMENTATION_ONLY (HEAD `e9bba94e54`) — gate
transversal §0 aplicado a R06: o PO informou que o CPV já existe na
plataforma; a verificação confirmou.

**Cadeia rastreável (consumer → producer):**

- `plugins/dashboard-supplies/src/pages/CpvPage.tsx` — tela "CPV —
  Custo de produto vendido" (cards CPV total, CPV/ROL, movimentos;
  gráficos por CFOP/TES/top produtos/documentos); fetch via
  `suppliesApi.ts` → `GET /apps/api-delpi/supplies/cpv`.
- `supplies-api` `SuppliesDelpiReads.get_cpv` (`supplies_delpi_reads.py`,
  `top_limit=15`) → `/supplies/cpv`; consumido por
  `OverviewCompositionService` como KPI-CPV (`cpv_percentage`) e por
  `strategic_indicators_gateway` (`"KPI-CPV"→"supplies-cpv"`).
- api-delpi `GET /supplies/cpv` (`supplies_router.py:89`, op
  `get_supplies_cpv`, auth `require_any_permission_or_supplies_bff(
  KPI_SUPPLIES_ACCESS)`) → `build_get_cpv_use_case`.
- `GetCPVUseCase` (`use_cases/supplies/get_cpv_use_case.py`) — compõe
  `CpvQueryRepositoryPort` (summary/by_cfop/by_tm/top_products/
  top_documents) + `FinancialQueryRepositoryPort.get_rol`; deriva
  `cpv_percentage = cpv_total/rol*100`, custo médio por movimento e por
  unidade.
- `CpvQueryRepository` (`totvs/supplies_repositories/
  cpv_query_repository.py`) — docstring "CPV alinhado ao relatório
  Kardex" (realinhamento deliberado no commit `4bd217a3ae`):
  `FROM SD2010 D2 WHERE D2.D_E_L_E_T_='' [AND D2_FILIAL=?]
  AND D2_EMISSAO BETWEEN ? AND ? AND D2_CF IN (cfops)`;
  medida `SUM(D2_CUSTO1)` / `SUM(D2_QUANT)`; CFOPs default
  `KARDEX_DEFAULT_CFOPS = (5101, 5124, 6101, 6124)` — campo `cfops`
  existe no DTO `GetCPVRequest` mas **não é exposto** pela rota.
- ROL (mesmo use case): `financial_repository.get_rol` — SD2 vendas
  elegíveis (`D2_TIPO<>'D'`, `F4_DUPLIC='S'` + exceções MI/CF 5927/
  5911-6911 filial 01) menos devoluções de venda SD1
  (`CommercialRolReturnSql.sales_return_predicate`).
- Chat/DAVI: `SUPPLIES_CPV` agent_route (`openapi_agent_metadata.py:668`,
  "Indicador CPV agregado por filial e período (SD2010, SUM(D2_CUSTO1),
  CFOPs Kardex)") — rota registrada no `route_contract_registry` e
  coberta por testes de contrato/registro/meta (`test_route_contract_*
  registry*`, `test_davi_*`, `test_envelope_consumer_compat`).

**Confronto CPV implementado × R06/MATR910:**

| Dimensão | Kardex MATR910 (R06) | CPV `GET /supplies/cpv` |
|---|---|---|
| Fonte | UNION SD1+SD2+SD3 | **somente SD2** |
| População | todo movimento `F4_ESTOQUE='S'` | só `D2_CF ∈ (5101,5124,6101,6124)` |
| Período | D1_DTDIGIT/D2_EMISSAO/D3_EMISSAO | `D2_EMISSAO` |
| Custo | `D*_CUSTO*` as_of emissão | `D2_CUSTO1` **corrente** |
| Filtros extra | `D3_ESTORNO<>'S'`, `ORIGLAN<>'LF'`, `D*_LOCAL`, `D1_REMITO=''` | nenhum |
| Granularidade | linha a linha por produto | agregado + cortes CFOP/TES/top-N |

- Devoluções de compra (SD2 `TIPONF='D'`, CF 5201/6201 — as 4 linhas
  NEG-E de §38) **fora** do CPV (CFOPs não pertencem ao conjunto);
  devoluções de venda são SD1 — fora de SD2, não entram no numerador;
  no ROL as devoluções de venda SD1 são subtraídas do denominador.
- Conclusão de semântica: o CPV implementado mede **custo das saídas de
  venda por NF**, subset das saídas do kardex — a afirmação §37.C
  ("saídas agregadas ≠ CPV") se mantém e agora tem a medida canônica
  identificada.

**Lacunas verificadas (`REUSE_PARTIAL` para evidência de fechamento):**

1. `D2_CUSTO1` corrente ≠ `as_of` — revalorização MATA330 pós-fechamento
   altera o valor reportado (mesma natureza do `STALE_EVIDENCE` do
   saldo final §37.E); evidência mensal imutável exige custo `as_of`
   (TTAT) ou snapshot persistido.
2. Branch único opcional; sem consolidado multi-unidade explícito.
3. CFOPs fixos no contrato HTTP (DTO tem `cfops`, rota não expõe).
4. Sem recorte por produto/tipo/armazém na resposta (só agregados e
   top-N) — insuficiente para drill-down de evidência por item.
5. Cobertura de teste = contrato/registro de rota; sem teste unitário
   dedicado do SQL do repositório (diferente de outros repos SD2).

**Decisão:** BR-R06-010 reclassificado `PROVEN` (implementação e
semântica identificadas) + **`REUSE_PARTIAL`**; `DECISION_REQUIRED`
restrito à questão material real: custo `as_of`/snapshot vs custo
corrente para a medida de fechamento — owner a decidir. Nenhum código,
endpoint ou contrato foi criado ou alterado nesta rodada.
Gates/métricas inalterados (42/60 · 47/90).

## §40 — DIREÇÃO PO: CPV MENSAL VIVO E CORREÇÕES RETROATIVAS — 2026-10-23

- **Decisão expressa do PO (`PRODUCT_DIRECTION_APPROVED`, documentação apenas):** CPV é apurado por **competência mensal**. Quando um erro de janeiro é descoberto em outubro, a correção ocorre no registro de janeiro e, após recálculo Protheus autorizado, consultas posteriores a janeiro mostram o **valor corrente atualizado**. A data da descoberta não transfere a competência.
- **AS-IS:** doc 56 Registro 08; doc 57 V15 (CFOPs 5101/5124/6101/6124, terceiros, Saídas Custo) e RC-04. **TARGET existente:** §39, doc 85 BR-R06-010: `GET /supplies/cpv`, `D2_EMISSAO` e `D2_CUSTO1` corrente.
- **Errata §39:** mutabilidade após MATA330 **não é lacuna nem `DECISION_REQUIRED` para a leitura corrente de CPV**. Não exigir `as_of` ou snapshot para essa consulta. `REUSE_PARTIAL` pode persistir por motivos distintos (granularidade/filtros/testes).
- **Rastreabilidade distinta:** identificar valores/evidências de homologação anteriormente realizados quando existirem, sem substituir o CPV vivo ou afirmar persistência/snapshot implementados. E6=C é decisão específica de histórico monetário MOD, não solução automaticamente aplicável ao CPV.
- **Sem novo GO:** nenhuma operação SQL, job, contrato, código ou runtime autorizada; R06/R07 G4/G5 PASS e G6 PENDING; 42/60, 47/90. Próxima rodada: sequência vigente docs 47/80, com verificação transversal §0.


## §41 — R08 MATR989 · Material em Processo — paridade física completa (rodada 22 — 2026-10-23)

Artefato oficial `Material em processo.xlsb` (aba única `01-01 - Saldo em
Processo (Ana` — variante **analítica** do MATR989, roster oficial;
`matr989.prx` **ausente do acervo** → `SOURCE_MISSING`, mesma classe
DLP06R01). Dt.Ref 01/10/2026 · Hora 16:15:58 · Emissão 01/10/2026 ·
57.359 linhas × 8 colunas: `CODIGO, DESCRICAO, UM, LOCAL, ORDEM PRODUCAO,
TIPO RE/DE, QTDE EM PROCESSO, VALOR EM PROCESSO`. Consultas SELECT-only
no `as_of` da emissão; zero DDL/DML; zero runtime.

### A. Estrutura do artefato — dois blocos

| Bloco | Linhas efetivas | Total | Fonte física provada |
|---|---|---|---|
| Com `ORDEM PRODUCAO` | **1.501** (650 pares produto×OP; 164 produtos; 444 OPs; 93 chaves prod×OP×tipo duplicadas por doc distinto) | **R$61.967,42** | linhas `SD3010` `D3_CF IN (RE0,RE1,RE2,RE9)` |
| Sem OP | 573 produtos ≠ 0 (+ ~54.600 linhas catálogo qtde/valor=0 e 141 `MOD*`) | **R$293.273,09** | `SB9010` `B9_DATA=20260930` `B9_LOCAL=99` |
| **Total** | | **R$355.240,51** | = EM PROCESSO do P7 completo (exato) |

Linhas sem OP com qtde/valor zero = catálogo de apresentação (não entram
no total nem na população).

### B. Grão — linha física SD3, não documento

1.501 linhas impressas = 1.501 linhas `SD3010` `RE*` elegíveis (join
prod+op+cf+doc+local); **um único** `D3_DOC` tem 2 linhas SD3 e o artefato
imprime 2 — grão = linha de movimento. Quantidade = `D3_QUANT`; valor =
`D3_CUSTO1` (custo do movimento a moeda 1, do instante do movimento —
ex. 9,16/u = `B2_CM1` da época).

### C. Regra de seleção — OP aberta no instante da emissão

Saldo por par = Σ`RE*` − Σ`DE*` com `D3_EMISSAO ≤ 20260930` (corte de
competência — `RE*` de 01/10 na mesma OP **não** aparecem). O par é
impresso **somente se a OP estiver aberta na data de referência**:

| Grupo | Resultado | Discriminador |
|---|---|---|
| 650 pares impressas | 100% exato qtde+valor | 0 têm `PR0` (apontamento de produção, SD3 `D3_CF LIKE 'PR%'`) da OP; PR0 só a partir de 02/10 ou nenhum |
| 36 OPs excluídas testadas | 33/33 | primeiro `PR0` em **01/10** (dia da emissão — produziram no Dt.Ref) |
| 3 OPs excluídas | 3/3 | `C2_QUJE=0` e `C2_DATRF` preenchido — encerradas/canceladas sem nunca produzir |
| 15 pares filial 02 | excluídos | artefato é filial 01 |

Conclusão: `RE*` entra no relatório se a OP está viva (sem `PR0` e sem
`C2_DATRF`) **no momento em que o relatório roda** — não basta "ter saldo
de requisições". Estado corrente de SC2 (`QUJE>0`, `DATRF`) já reflete
produções de outubro; a reprodução `as_of` usou `PR0` como proxy físico do
fechamento da OP — 118 OPs impressas não têm nenhum `PR0`; 325 produziram
só em outubro.

Fronteira registrada: a seleção distingue `as_of`-dia (01/10) — dentro do
dia, `PR0` antes/depois das 16:15 não é observável por data. `C2_QUJE=0`
na emissão ≡ sem `PR0` até 01/10 (consistência SC2↔SD3 nos 444 OPs
impressos: todos existem em SC2).

### D. Bloco sem OP — SB9 loc 99 no fechamento

| Checagem | Resultado |
|---|---|
| Produtos SB9 `B9_DATA=20260930` loc 99 com saldo ≠ 0 vs artefato sem-OP | **569 exatos** (q+valor) |
| Divergentes | 4: `<PRODUTO-WIP-A>` ΔR$449,16 e `<PRODUTO-WIP-B>` Δ0,144 (revalorização `B9_VINI1` pós-emissão — drift `STALE_EVIDENCE`, mesma classe R05/R06); `<PRODUTO-WIP-C>` Δ0,01; `<PRODUTO-WIP-D>` Δ−0,001 (resíduo de centavo) — aliases §42.D |
| SB9 ≠ 0 ausente do artefato | 0 |

Exemplo: produto 180/u — SB9@0930 loc99 = 180 × 9,16 = 1.648,80 = linha
impressa exata.

### E. Confronto com P7 (BR-R03-003 → provado nos dois sentidos)

Decomposição dos R$355.240,51:

| Componente | Valor | Natureza |
|---|---|---|
| SB9 loc 99 (sem OP) | 293.273,09 | estoque físico do armazém de processo |
| `RE0` | 588,50 | requisições de OP aberta (loc 99) |
| `RE1` loc **01** | 254,44 | material de OP em almoxarifado — **= fatia PI do EM PROCESSO** (doc 80 §33.D previa 254,44) |
| `RE2` | 48.713,64 | requisições de OP aberta (loc 99) |
| `RE9` | 12.410,85 | requisições de OP aberta (loc 99) |
| **Σ** | **355.240,51** | **= EM PROCESSO P7 exato, Δ 0,00** |

`EM PROCESSO` **não é** o saldo do armazém 99: é estoque-em-processo
físico (293.273,09) **+** material alocado a OPs abertas (61.967,42).
Distinção material para a Central de Fechamento — o armazém 99 sozinho
subestima EM PROCESSO em ~17%.

R03 **não** é promovido por associação: EM PROCESSO do P7 = total MATR989
agora `PROVEN` nos dois sentidos (o P7 completo soma exatamente o artefato
R08); produtor/parâmetros do P7 seguem pendentes (E2).

### F. Hipóteses descartadas

- ~~net de movimentos do mês~~ — 2.726 pares com movimento em setembro e
  saldo >0 ausentes do artefato (OPs já produzidas/encerradas).
- ~~escopo por `C2_DATRF`~~ — 453 pares impressas têm `C2_DATRF` populado
  (encerramento registrado em outubro, OP viva na emissão).
- ~~grão documento~~ — provado linha SD3 (1.501 = 1.501).
- ~~SDC/alocação~~ — SDC não governou a população; SC2+SD3 bastam.
- ~~MOD com valor~~ — 141 linhas `MOD*` todas qtde/valor 0 (linhas de
  catálogo); MOD não entra no bloco com OP — horas MOD são outro artefato
  (R09).
- ~~filial 02~~ — 15 pares (prod,OP) com movimento f02 e net>0 excluídos.

### G. Reuso existente verificado (gate transversal §0)

| Cadeia | Veredito |
|---|---|
| `stock_value_historical_sql.py` (api-delpi) — SB9@data + ponte SD3 | **canônico** p/ bloco sem-OP e saldos `as_of` |
| `_fetch_wip_proxy_rows` → `em_processo_proxy_value` = `SUM(SB2.B2_VATU1)` loc `('50','98','99')` | **parcial** — cobre só o bloco físico corrente (~293k), não o alocado a OP (61.967,42) nem `as_of` |
| `ops_abertas_sql.py` — `C2_QUANT>C2_QUJE AND C2_DATRF=''` | predicado adjacente; MATR989 exige `QUJE=0` (sem `PR0`) — semântica distinta |
| Serviço de saldo RE−DE por OP | **inexistente** — lacuna real (`TARGET` doc 85 BR-R08-009) |

### H. Gates

`G4` producer+variante (MATR989 analítico, roster+título da aba), bindings
(SD3/SB9/SC2), chaves, filtros e transformações demonstrados → **PASS**;
`G5` reconciliação linha-a-linha 1.501/1.501 + 569/573 (4 explicados) +
população 650/650 + total P7 exato → **PASS**; `G6` homologação humana →
`PENDING`. Residual: fonte `matr989.prx`/RPO (classe E7) + semântica
intra-dia do corte + neteo `DE*` não exercido nesta competência.

## §42 — ERRATA R08 (CF-C2-R08-MATR989-PARITY-REWORK-001 — 2026-10-23)

Errata/complemento do §41. Nenhuma conclusão de fundo muda; quatro pontos
de rigor corrigidos/reforçados.

### A. Reconciliação do centavo (Frente A)

Os componentes publicados no §41.E foram arredondados a 2 decimais —
soma 355.240,**52** ≠ total 355.240,51. Com a **precisão original de 3
decimais** do artefato, a decomposição fecha exata:

| Componente | Precisão original |
|---|---|
| SB9 loc 99 (sem OP) | 293.273,088 |
| `RE0` | 588,500 |
| `RE1` loc 01 | 254,437 |
| `RE2` | 48.713,642 |
| `RE9` | 12.410,845 |
| **Σ** | **355.240,512** → exibido 355.240,51 |

O relatório soma em precisão cheia e arredonda o total para exibição;
somar componentes já arredondados produz o artefato de +0,01. Regra:
**linhas em 3 decimais; grupo e total = Σ sem arredondar, exibição a 2
decimais** (half-up). `PROVEN` (total = P7).

### B. Quatro diferenças SB9 — classificação com evidência (Frente B)

Todas as **753 linhas** `SB9010` f01@0930 loc99 foram (re)inseridas em
**21/10/2026 19:13:41** (`I_N_S_D_T_` = `S_T_A_M_P_`, verificado em
todas) — 20 dias após a emissão do relatório (01/10 16:15). Portanto o
artefato **não leu a SB9 atual**: o bloco sem-OP reflete a posição do
armazém 99 **no instante da emissão**; a SB9@0930 vigente é uma
regravação posterior do fechamento. `SB9010_TTAT_LOG`/`SB2010_TTAT_LOG`
estão **vazios** para esses RECNOs — sem auditoria por campo; a classe
temporal se apoia no timestamp universal de regravação + direção do drift
de custo médio, não em hipótese.

| Alias | Impresso (q/valor; cm implícito) | SB9 atual (valor; cm) | Δ (imp−atual) | Classe |
|---|---|---|---|---|
| `<PRODUTO-WIP-A>` | 2.000 / 16.517,702 (8,258851) | 16.966,861 (8,4834); SB2 loc99 corrente q=0, cm 8,6479 | −449,159 | `TEMPORAL` — revalorização de CM entre emissão e regravação (drift continua no SB2) |
| `<PRODUTO-WIP-B>` | 314,31 / 90,947 (0,289354) | 91,091 (0,2898); SB2 cm corrente 0,2879 | −0,144 | `TEMPORAL` — revalorização centesimal de CM |
| `<PRODUTO-WIP-C>` | 1.982 / 425,615 (0,214740) | 425,605 (0,2147); SB2 corrente 425,620 | +0,010 | `TEMPORAL`/arredondamento — micro-ajuste de CM na regravação |
| `<PRODUTO-WIP-D>` | 0 / −0,001 | 0 / 0 | −0,001 | arredondamento — resíduo de centavo zerado na regravação |

Efeito no total: ΣΔ = **+449,294**; SB9@0930 loc99 corrente soma
**293.722,382** vs 293.273,088 impresso — diferença **integralmente
decomposta** pelos 4 produtos (paridade no `as_of` da emissão preservada;
drift pós-emissão, mesma classe R05/R06).

### C. Produtor e escopo — reclassificação de rigor (Frente C)

- Produtor = MATR989 variante analítica **inferido** por roster oficial +
  título da aba (`PRODUCER_INFERRED_BY_ARTIFACT`); `matr989.prx` ausente
  (`SOURCE_MISSING`); versão compilada não identificada. **Errata §41:**
  a expressão "`CODE_DEPLOYED` via artefato" é retirada — relatório
  emitido prova `EXECUTION_OBSERVED`, não identidade do código.
- Seleção por OP aberta: reproduzida na **granularidade de dia**
  (`as_of`-dia 01/10 — sem `PR0` e sem `C2_DATRF` naquela data). A
  semântica **intradia** (PR0 de 01/10 antes/depois das 16:15) não é
  observável por data e permanece pendente (E8).
- Neteo `DE*`: **inferência estrutural** — nenhum par impresso contém
  `DE*` nesta competência; não generalizado além da população testada
  (T-R08-06 segue `candidato`).

### D. Sanitização (Frente D)

Códigos reais dos 4 produtos divergentes substituídos por aliases
estáveis `<PRODUTO-WIP-A..D>` (mapeamento sob custódia do owner, fora do
repositório). Os originais constaram no commit `f5c50f7c04` —
**exposição registrada** para avaliação do owner de segurança; histórico
Git não reescrito por decisão do PO (§32).

### E. Gates e métricas (Frente E)

G4/G5 sustentados: critério G4 = bindings físicos+seleção+filtros
demonstrados (produtor inferido por artefato é suficiente — fonte é
residual E8, precedente R06/R07); G5 = reconciliação reproduzível +
residuais explicados. Métricas corrigidas: `COLETA = 43/60 = 71,7%`;
`AUDITORIA = 49/90 = 54,4%`; `RELATORIOS_CONCLUIDOS = 0/15`; R03 não
promovido; R08 G6 `PENDING`.
## §43 — R09 · Faturamento × MOD — modelo físico do DLP204 (rodada 24)

Escopo: `Fat x MOD.xlsb` (abas `1-Fl01`/`2-Fl02`, 4.476 linhas de detalhe).
Resultado: produtor confirmado **com fonte** + modelo físico reconstruído
a 99,4%; SP interna e pontos de borda → E9. Gates: **G4 PASS · G5
INCONCLUSIVE · G6 PENDING**.

### A. Produtor, variante e parâmetros — `PROVEN`

- `DLP204.prw` **no acervo** (`docs/13-fontes-totvs-protheus/06.
  Financeiro/DLP204.prw`, Gabriel, 2019) — `SOURCE_AVAILABLE`;
  `EXECUTION_OBSERVED` pelo artefato; `CODE_DEPLOYED` não declarado
  (RPO não vinculado — E9).
- Emissor `FWMSEXCEL`: aba `FlNN`/tabela `Estrutura Filial NN` por
  filial; linha `Total Produto ---->` existe só na sessão Excel
  interativa (não persistida no XLSB).
- SX1 `DLP204`: par01/02 datas, par03/04 produto, par05/06 grupo,
  par07/08 tipo, par09 roteiro (default `01`), par10 filiais, par11
  "Exibir MP?". Artefato: competência **set/2026** (reproduzida), ambas
  filiais, par11=**Não** (sem linhas `03/05/07`).

### B. Seleção e propagação — `PROVEN` (4.476/4.476)

- PA-âncora = `SB1` na faixa de parâmetros **e** ∃ `SD2` da filial no
  período com TES `F4_DUPLIC='S'` (WHERE literal do fonte — mesma
  regra canônica de vendas). Fonte não filtra `D2_TIPO`; as 7 NFs tipo
  `D` de set/2026 com TES duplic-S são de MPs fora do escopo —
  `UNEXERCISED` (teste T-R09-07 candidato).
- `Seq Comp` = `COMP` da SP = nível da expansão SG1 (`02` PA, `04`
  componente, `06` subcomponente) — conferido por distância
  estrutural (0/1/2).
- `Qtd Fat.` = `QTDFAT` da SP = faturamento do PA-âncora; `QTDFAT=0` →
  fallback = quantidade do chamador (`aModPar[4]`) — explica seriais
  herdando a quantidade do pai faturado.

### C. Expansão PA→MOD — `SOURCE_MISSING` (SP) / mecanismo `PROVEN` (99,4%)

- Motor = `EXEC STP_DELPI_FORMA_PRECO_<emp> (prod, fil, roteiro, dataDe,
  dataAte, nivel, pa_ancora)` → retorna `PA, COMP, B1_COD, B1_DESC,
  QTDFAT, B1_UM, G2_TEMPAD, CUSTO_UNIT, CUSTO_TOTAL, CUSTOPROD, HORAS`.
  **Procedure ausente de todos os bancos acessíveis** (legado 2019) —
  internos inferidos por artefato → E9 (sem inventar lógica).
- MOD = recurso da operação do **roteiro congelado da OP** (`SHY010`,
  `HY_OP`=`C2_NUM`+`C2_ITEM`+`C2_SEQUEN` — OPs de desdobramento têm
  item-pai + seriais como sequências) ou do roteiro cadastral `SG2010`
  (fallback), via ponte `SH1010.H1_CCUSTO` → `MOD<cc>` — **mesma ponte
  §22** que alimenta a `vw_Apontamentos_Eficiencia` (`SHB010.HB_CC`
  concordante exceto CT-01C f02 → `MOD345`, onde SH1 prevalece).
- `Quantidade` = `HY_TEMPAD` (nome `G2_TEMPAD` no contrato da SP):
  **4.311 linhas via SHY + 138 via SG2 = 4.449/4.476 (99,4%)**. As
  "revisões de roteiro" da investigação preliminar eram `HY_TEMPAD`
  histórico ≠ `G2_TEMPAD` corrente (`STALE_EVIDENCE` do cadastro).
  Fator `÷2`/÷`C2_QUANT` em itens de desdobramento (par de seriais) —
  semântica do divisor `PENDING` (E9). **27 linhas residuais** (tempos
  zerados / roteiro de OP não localizado — ex.: `<PA-RESIDUAL-R09-*>`).

### D. Custos e fórmulas — `PROVEN`

- `Horas = Qtd Fat. × Quantidade`; `Custo Total = Horas × Custo Unit`
  — identidade aritmética 4.476/4.476.
- `Custo Unitario` = `SBZ010.BZ_CUSTD` (filial,MOD) **vigente na
  emissão** — cadeia `SBZ010_TTAT_LOG` com cutoff ~06-07/10/2026
  (anterior às revalorizações `MATA019` 07-08/10, §23): **4.469/4.469**
  linhas com rate conferem; **7 linhas** MOD sem registro SBZ na filial
  (ausência de cadastro ≠ zero — E6).
- `UM` = `B1_UM` do MOD (`HR`/`H`/`PC`); `Custo Produto` = `CUSTOPROD`
  = 0 em todas as linhas (semântica não exercida — `PENDING` menor).
- Totais derivados do artefato: f01 ΣCusto=164.985,66 / ΣHoras=2.472,58;
  f02 ΣCusto=579.268,58 / ΣHoras=7.089,40. Sem subtotais persistidos.

### E. Reuso transversal (gate §0)

- Predicado `F4_DUPLIC='S'` = mesma regra canônica de vendas
  (`REUSE_CONFIRMED` de predicado).
- `vw_Apontamentos_Eficiencia` = `REUSE_PARTIAL`: mesmo mapa CT→MOD e
  mesmo domínio de rate, mas semântica divergente (horas reais/
  previstas + rate corrente retroativo §23.E **vs** tempo padrão do
  roteiro × faturamento × rate `as_of`) — não transplantar fórmula.
- Nenhum serviço Minha DELPI implementa a cadeia — `TARGET` doc 85 §15.

### F. Residuais → E9 (owner TI/ERP, doc 82)

SP `STP_DELPI_FORMA_PRECO_*` (fonte/RPO), versão compilada do DLP204,
parâmetros efetivos da emissão (par03..11), regra de seleção de OP por
PA dentro da SP, semântica do divisor `÷2` em desdobramento, 27 linhas
de tempo sem roteiro localizado, 7 MODs sem SBZ (cadastro ou exceção?),
semântica de `CUSTOPROD`. `D2_TIPO='D'` não exercido.

### G. Gates e confidencialidade

`G1–G3` mantidos; **`G4 PASS`** — produtor com fonte + bindings físicos
(seleção 100%, expansão 99,4%, rate 100% das linhas com SBZ)
demonstrados; **`G5 INCONCLUSIVE`** — paridade monetária/quantitativa
alta mas não integral no grão linha (27 tempos + divisor + regra de
seleção de OP na SP pendentes — sem promover por agregado); `G6
PENDING`. Códigos de produto substituídos por aliases
(`<PA-ÂNCORA-*>`, `<PA-SERIAL-*>`, `<PA-RESIDUAL-R09-*>`) — mapeamento
sob custódia do owner fora do repositório. Códigos MOD (`MOD###`)
mantidos por convenção §22 (cadastro de rates, não identificam item
comercial).

## §44 — R10 · Notas por Centro de Custo — seleção EDAPP reconstruída e paridade (rodada 25 — 2026-10-23)

Sub-task: `CF-C2-R10-CENTRO-CUSTO-SD1-PARITY-001`. Artefato `CC
matriz.xlsb`. READ-only (`delpi-api-delpi`, `db_datareader`); zero
DML/DDL; runtime não autorizado.

### A. Artefato e grão

Aba `SCAGQGA0.XML`; linha 0 literal `SD1`; headers = títulos SX3
`D1_*`. **353 linhas efetivas**, todas filial `01`, **139 documentos**,
46 centros de custo distintos, Σ `Vlr.Total` = **R$ 169.704,12**.
Grão = **item SD1** (linha física de NF de entrada). Coluna sem título
entre `C Custo` e `C Contabil` contém a classificação
`Direto`/`Indireto`/`Adm` (ver §F).

### B. Binding físico (353/353 — `PROVEN`)

Chave de vínculo `(D1_DOC, D1_ITEM, D1_COD, D1_TOTAL)` une cada linha
do artefato a **exatamente um** RECNO SD1 — sem ambiguidade, sem linha
não localizada. Mapeamento de colunas: `Vlr.Total`=`D1_TOTAL`,
`Vlr.Unitario`=`D1_VUNIT`, `Quantidade`=`D1_QUANT`, `Tipo Produto`=
`D1_TP` (tipo gravado na linha; diverge de `B1_TIPO` corrente em
casos observados), `Tipo Entrada`=`D1_TES`, `Cod. Fiscal`=`D1_CF`,
`C Custo`=`D1_CC`, `DT Digitacao`=`D1_DTDIGIT`, `Forn/Cliente`=
`D1_FORNECE`, `Loja`=`D1_LOJA`, `No do Pedido`=`D1_PEDIDO`,
`Armazem`=`D1_LOCAL`. `Vlr.Total` nem sempre = `D1_QUANT`×`D1_VUNIT`
(segunda UM/conversão/arredondamento Protheus) — a medida monetária
autoritativa é `D1_TOTAL`, não a fórmula.

### C. Seleção real — procedimento do operador (owner) × reprodução física

Universo `SD1010` `D1_FILIAL='01'` `D_E_L_E_T_<>'*'`:
`D1_DTDIGIT ∈ set/2026` → **686 linhas** (eixo digitação, não
emissão — 80 linhas incluídas têm `D1_EMISSAO` fora de setembro, mín
2026-08-03; universo por `D1_EMISSAO` seria 659).

O procedimento relatado pelo owner (doc 56 Registro 17, 44:28–47:48 —
`OWNER_REPORTED_VIA_PO`) reproduz fisicamente **100%** do artefato:

| Passo (owner) | Regra física | Linhas | Status |
|---|---|---|---|
| filtro data de digitação no mês | `D1_DTDIGIT` 2026-09-01..30 | 686→base | `PROVEN` |
| excluir "12 tipos de entrada" | `D1_TES ∉` conjunto | −303 → 383 | `PROVEN` (lista → §C.1) |
| ordenar por produto, excluir MP | `D1_TP<>'MP'` | −24 → 359 | `PROVEN` 302/302 |
| coparticipação plano saúde fora | benefícios GG sem CC | −6 → **353** | `PROVEN` 6/6 |

Soma residual zero: 303+24+6 = 333 = 686−353. Total exato nos dois
lados do corte.

### C.1 Lista de tipos de entrada — narrada × observada

Narrada (transcrição PO, 2/3 dígitos): `01,02,03,04,030,040,083,080,
085,120,204,318` — mapeia para `001,020?,003,040?,030,040,080,083,
085,120,204,318` (11 distintos; `02`/`04` ambíguos). **Observada
(13 TES, zero falso-positivo/negativo):** `001,003,016,020,030,040,
080,083,085,120,159,204,318` = COMPRAS MP (001/003), CONTA ORDEM
(016), ENERGIA (020), COMUNICAÇÃO (030), TRANSPORTE (040), ENTRADA
IND./VASILHAME (080/083/085), DEVOL. VENDAS (120), REMESSA INDUSTR.
(159), TRANSF. MP (204), IMPORTAÇÃO (318). `016` e `159` estão
fora da lista narrada — ambos `F4_DUPLIC='N'` (não geram duplicata;
coerente com análise de despesas) — confirmação da lista exata → E10.

Hipótese descartada: `F4_ESTOQUE` não discrimina (TES `S` dentro e
fora; `N` dentro e fora). MP é excluído por `D1_TP` da linha, não por
`B1_TIPO` — consistente com o owner ter ordenado a **coluna exportada**.

### D. Benefícios excluídos (as 6 linhas residuais)

TES `046`, `D1_TP='GG'`, **sem CC**, produtos do grupo de benefícios
(plano de saúde/odontológico — aliases `<PRODUTO-BENEFICIO-*>`,
mapeamento sob custódia do owner): R$ 6.990,44 excluídos. Casa com a
regra relatada "parcela do colaborador fora, sem CC" — não extrapolar
para toda despesa de plano (distinção colaborador×empresa → E10).

### E. Reuso transversal (gate §0)

`GET /financeiro/despesas-centro-custo/*` (api-delpi, plugin
`financeiro-centro-custo`, `vw_fin_despesas_centro_custo`): **mesmo
domínio**, seleção **diferente** — view usa `data_emissao`=
`D1_EMISSAO` + exige `D1_CC<>''` + não exclui MP/TES (448 linhas
set/26 f01, Σ R$ 545.580,00; cobre 269/353 do artefato; as 84 faltantes
= 80 do eixo digitação + 4 sem-CC; view acrescenta 179 incl. 128 MP).
Classificação **`REUSE_PARTIAL`** — módulo reutilizável como domínio/
contrato de despesas por CC, **não** como reprodutor da seleção
oficial (consulta distinta `despesas-cc-official-scope` se homologada).
DDL da view não visível a `db_datareader` (SQL 15197) — predicados
internos documentados como limitação, sem afirmação de regra oculta.

### F. Classificação Direto/Indireto/Adm — manual pós-exportação (`AS-IS`)

A coluna sem título **não existe em SD1 nem CTT** (testados
`CTT_CLASSE/TIPO/TIPO00/TIPO01/TIPO2` — sem campo análogo). Correlação
semântica por CC: `Direto` = CCs de máquina/produção (275, 223, 393 —
mesmos CCs dos `MOD###` de R09) + insumos sem CC marcados manualmente;
`Indireto` = CCs de apoio (0301–0504); `Adm` = CCs administrativos
(01xx–02xx, 0501). 2 entradas `direto` minúsculas = edição humana.
Owner confirma: classificação escrita manualmente na planilha, usando
CC como indício. Subtotais derivados: Adm 99.297,81 · Indireto
38.554,82 · Direto 31.851,49 (Σ = 169.704,12). `TARGET` exige fonte
de classe homologada — não inferir por prefixo de CC.

### G. Temporalidade

Nenhuma divergência linha×linha detectada (353/353 exatas) — o SD1
corrente **não divergiu** da exportação; nada a classificar como
`STALE_EVIDENCE`. Correções retroativas em SD1 são raras e não
afetaram esta competência.

### H. Gates, sanitização e residuais

`G1–G4` mantidos; **G5 `PASS`** — população 353/353 reconciliada no
grão item, seleção reproduzida integralmente e corroborada pelo
procedimento relatado do owner, medida monetária exata; `G6 PENDING`
(aceite Controladoria). Residuais → **E10** (Controladoria/operadora):
lista exata de tipos de entrada excluídos (narrada 12 vs observada 13
— `016`/`159` + ambiguidade `02`/`04`), consulta/filtro salvo EDAPP ou
data-hora da sessão, confirmação da regra de benefícios (parcela
colaborador×empresa) e da fonte da classificação Direto/Ind/Adm.
Aliases: `<PRODUTO-BENEFICIO-*>` (produtos saúde/odonto), docs/
fornecedores individuais não publicados; TES/CFOP/CC/totais mantidos
como evidência técnica.

## §45 — R11 · NF a Desconsiderar / CPV Zero — seleção e causa física (rodada 26 — 2026-10-23)

Sub-task: `CF-C2-R11-NF-DESCONSIDERAR-SD2-PARITY-001`. Artefato `NF a
desconsiderar.xlsb`. READ-only (`delpi-api-delpi`, `db_datareader`);
zero DML/DDL/recálculo; runtime não autorizado; fórmula do CPV canônico
intocada.

### A. Artefato e grão

Aba `Planilha2`; linha 0 literal `SD2`; headers = títulos SX3 `D2_*`
(184 colunas exportadas — sem `Emissao`, `Cliente`, `Serie`, `Custo`).
**11 linhas efetivas**, filial 01, **11 documentos distintos**,
Σ `Vlr.Total` = **R$ 97.462,71**. Grão = item SD2. Errata doc 47
§11.1: a coluna `Tipo Saida` (594) é `D2_TES` — `D2_TIPO`='N' nas
linhas (não `D2_TIPO` como anotado).

### B. Binding físico (11/11 — `PROVEN`)

Chave `(D2_DOC, D2_ITEM, D2_COD, D2_TOTAL)` une cada linha a exatamente
um RECNO SD2 — sem ambiguidade, sem não-localizadas. `Vlr.Unitario`=
`D2_PRCVEN`, `Grupo`=`D2_GRUPO`, `C Contabil`=`D2_CONTA`, `MD5`/`Campo
UUID` = auditoria Protheus.

### C. Seleção real — identidade de conjunto (`PROVEN`)

Universo `SD2010` `D2_FILIAL='01'` `D_E_L_E_T_<>'*'` `D2_EMISSAO`∈
[20260901..20260930]: `D2_GRUPO='9035'` → **11 linhas** =
**exatamente o artefato** (mesmo conjunto, não só mesma cardinalidade).
`D2_TES='594'` produz o mesmo conjunto — em set/2026 a equivalência é
bidirecional (todo 594 é 9035 e vice-versa). All-time: 9035 aparece
com TES 511/505/610/… — o predicado "9035" **não** é atemporal; é a
interseção observada na competência. Qual eixo o operador usou (grupo
× TES) é indistinguível pelo artefato → E11.

Hipóteses descartadas: `D2_CUSTO1=0` como predicado (91 linhas no mês —
artefato é subconjunto 9035/594); documento como unidade (seleção é por
item — docs com 2 itens contribuem só o item 594); `D2_TIPO` (todas 'N').

### D. CPV zero — causa estrutural (`PROVEN` via SF4 + TTAT)

As 11 linhas têm `D2_CUSTO1=0` **desde a criação**: `SD2010_TTAT_LOG`
registra insert `MATA460A` na data da emissão com `COLD`=`CNEW`=0.000 e
zero alterações posteriores — não é custo faltante, correção pendente
nem drift (`STALE_EVIDENCE` não se aplica). Causa física:
`SF4.F4_ESTOQUE='N'` para TES 594 "VENDA DE PRODUCAO DO
ESTABELECIMENTO" — TES sem baixa de estoque não gera custo de saída;
`F4_DUPLIC='S'` mantém a duplicata/receita.

### E. Semântica do conjunto — industrialização para terceiros

Produtos grupo 9035 = itens de serviço/insumo de industrialização
("INDUSTR./RESINAGEM/INSUMOS UTILIZADOS", `D2_TP`='PA'). **8 das 11
NFs casam dois itens**: item 01 = produto físico `9026*` com TES **510**
"INDUSTRIALIZACAO EFET. P/ OUTRA EMPRESA" (`F4_ESTOQUE='S'`, custo>0,
CFOP 5124) + item 02 = faturamento da industrialização com TES 594
(custo 0, CFOP 5101); 3 NFs só têm o item 594. Clientes = empresas
terceiras (não intercompany) — industrialização efetuada para outra
empresa, faturada sem baixa de estoque próprio.

### F. Reuso transversal (gate §0)

`GET /supplies/cpv` (`GetCPVUseCase`/`CpvQueryRepository` —
`SUM(D2_CUSTO1)`, CFOPs 5101/5124/6101/6124, `D2_EMISSAO`): as 11
linhas (CFOP 5101) **contribuem R$0,00 ao CPV** — inclusão no conjunto
não altera o custo; a receita integra faturamento/ROL. `REUSE_PARTIAL`
— coerente com o artefato, sem contradição; o "desconsiderar" é camada
de conferência manual, não predicado da API. Regra kardex
`F4_ESTOQUE='S'` (R06) = `REUSE_CONFIRMED` por predicado: explica a
ausência destas linhas no MATR910. Decisão PO §40 preservada: CPV
vivo/corrente — nada a corrigir aqui.

### G. Gates, sanitização e residuais

`G1–G4` mantidos; **G5 `PASS`** — população 11/11 por identidade de
conjunto, medidas exatas (Σ 97.462,71; valores por linha), custo zero
explicado estruturalmente; `G6 PENDING`. Residual → **E11**
(Controladoria): qual apuração recebe o "desconsiderar" (numerador
CPV, denominador ROL, conferência DRE/faturamento — roster diz "à
desconsiderar do faturamento"); se a seleção é regra por TES/grupo ou
exceção por documento; eixo efetivo do filtro EDAPP (grupo vs TES).
Doc 67 (ciclo 1) NFEX-01/05 respondidos fisicamente; NFEX-01
(finalidade) permanece owner. Aliases: clientes/produtos individuais
não publicados; grupo 9035, TES, CFOP, totais = evidência técnica.

---

## §46 — R12: sequência operacional de fechamento de custos (rodada 27)

`CF-C2-R12-COST-CLOSING-PROCESS-VERIFY-001` — READ → VERIFY VIDEO →
INSPECT CODE → CROSS-CHECK → DOCUMENT → REPORT. Vídeo oficial MP4
**reinspecionado diretamente** (frames extraídos nos timestamps-chave;
inspeção direta, não apenas documental). Read-only; zero DML/DDL/recálculo.

### A. Linha do tempo observada (vídeo → wall-clock)

Reunião iniciada ~14:31 (nome do arquivo). Wall-clock ≈ tempo de vídeo
+ ~14:27 (offset do início da gravação).

| vídeo | etapa | tela/rotina | resultado visível | classificação |
|---|---|---|---|---|
| 01:55–02:08 | consulta | `Acompanha Custos` → lista `Fechamentos` | histórico com status (Concluído/Cancelado/Análise e revisão), filial, datas; botão `Reabertura de estoque`; modal "Novo fechamento" explica reprocessamento do CM | `EXECUTION_OBSERVED` (navegação) |
| 02:18–02:40 | parametrização | etapa 1 `Predefinição de cálculo` | último fechamento 31/08/2026; data 30/09/2026; método `Diária`; `Filial corrente`; regra visível: fechamento só em data posterior ao último | `EXECUTION_OBSERVED` |
| ~03:09–04:00 | execução | `Custo de Reposicao` → `Recalculo` → Perguntas | parâmetros íntegros (BR-R12-001); descrição declara escrita em `B1_CUSTD` | `EXECUTION_OBSERVED` |
| 04:36 | parametrização | `Refaz Saldos` (grupo SX1 `MTA300`) | `Ate Armazem`=ZZ, `Zera saldo MOD`=Recalcular, `Zera CM MOD`=Recalcular | `EXECUTION_OBSERVED` |
| ~05:34 | narração | `Refaz por DIT terceiros` | apenas citada — não executada nem exportada | relato — `PENDING` |
| 06:04–06:46 | execução/validação | `Recálculo dos Saldos` → `Log de processamento das STORED PROCEDURES` | threads `c300P0101xx - Ok` (≥6 visíveis); sem export | `EXECUTION_OBSERVED` (log); efeito no dado `PENDING_EVIDENCE` |
| ~14:47 | execução | wizard etapa 2 `Cálculo de custo` 100% | níveis validados, arquivo de trabalho, transferências entre filiais, movimentações — todos concluídos; controles Cancelar/Refazer/Próximo; menção EventViewer | `EXECUTION_OBSERVED` |
| 16:40–36:10 | conferência | etapa 3 `Análise e revisão` | grade "1991 produtos", status por moeda, CM ini/fin, Variação%, Exportar | `EXECUTION_OBSERVED` |
| — | homologação | etapa 4 `Fechamento` | **não exibida no vídeo** | lacuna registrada |

### B. Rotinas — identidade física

- **Custo de Reposição = `MATA320`** — grupo SX1 `MTA320` reproduz 1:1 os
  16 parâmetros da tela. **Efeito provado:** `SB1010_TTAT_LOG` →
  `TTAT_PROGRAM='MATA320'`, `TTAT_FIELD='B1_CUSTD'`, `TTAT_USER='JOICI'`:
  **13.201 writes 30/09 14:36–14:56** (1ª execução, produtos até MP) +
  **1.532 writes 15:09–15:14** (2ª execução, PA/PI); **+15.972 writes
  01/10 16:03–17:48** (reexecuções pós-demo). Cadeia vídeo→rotina→campo→
  escrita completa — a rotina grava `SB1.B1_CUSTD`.
- **Refaz Saldos = `MATA300`** — grupo SX1 `MTA300` (8 perguntas) 1:1 com
  a tela (incl. `Zera o saldo de produtos MOD?`); log exibe threads de SP
  `c300P*` com `- Ok`. **Sem rastro TTAT** em campos `B2_*`/SB9 (campos
  de saldo/custo não auditados) → efeito físico direto não consultável:
  `PENDING_EVIDENCE`.
- **Acompanha Custos** — wizard web sobre motor MATA330 customizado
  (doc 56 Reg.14); etapas 1–3 observadas; etapa 4 não exibida.
- **`DEL100.PRW`** — custom do acervo, **distinto do Refaz do vídeo**:
  auditoria/correção sequencial SB9 (`RecLock` em `B9_VINI1`/`B9_QINI` no
  modo alteração; log-only no modo auditoria). Binding anterior
  "Refaz=DEL100" = **errata corrigida**.
- **`MA330OK.PRW`** — PE pós-MATA330: `STP_DELPI_OP_TERCEIRO_<emp>`
  (`@DATADE`) + `STP_PROTHEUS_DELPI_AJUSTA_OP` f01/f02 (`@ANOMES`) +
  EventViewer (coerente com a menção na tela do wizard). SPs ausentes nas
  bases acessíveis; `sysjobs` sem permissão → `SOURCE_AVAILABLE`,
  execução `PENDING` (E4).

### C. Persistência provada (competência 09/2026)

- `MV_ULMES` = `20260930` em **f01 e f02** — marcador de último
  fechamento avançado para setembro.
- `SB9`@30/09: rajada única por filial — f02 02/10 17:58:01–03 (3.117
  linhas), f01 21/10 19:13:40–42 (4.812 linhas). Writer efetivo
  `PENDING` (E5) — divergência temporal preservada (reexecução/"Refazer
  cálculo"/etapa distinta/rotina separada — sem byte-proof).

### D. `Analise.xlsx` ↔ etapa 3 ↔ SB9

- Estrutura 1:1 com a grade do wizard; export = 1.994 linhas de dados,
  filial 01, armazéns 01/99/98/25/50; "1991 produtos" na tela vs 1.994
  linhas (Δ de contagem registrado — `PENDING` menor).
- **CM final ≡ `B9_CM1`@30/09 em 1.966/1.994 (98,6%)**; 22 sem SB9 =
  pseudo-produtos `MOD*` com custo 0 (estrutural — sem snapshot de
  saldo); 6 deltas = drift temporal cálculo-da-demo (30/09) × gravação
  f01 (21/10). CM inicial ≡ `B9_CM1`@31/08 em 1.689 linhas (283 chaves
  sem snapshot de agosto).
- `Status moeda` = sinal da Variação% em 1.994/1.994 (Positivo/Negativo/
  Neutro).
- SB2 corrente **não** é a fonte do artefato (amostra 10/25) — o CM final
  é o do fechamento, não o saldo vivo.

### E. Erratas corrigidas

1. `Tempo Setup?` = **`Som Tempo Propo`** (frame 03:20); doc 56 dizia
   "Sem Tempo Proprio" — corrigido por adendo rastreável.
2. `Calcular os Custos Por?` = **`Ult Cust Compra`** na 1ª execução
   (MC→MP) e **`Estrutura`** na 2ª (PA→PI) — o registro anterior do
   catálogo documentava apenas o valor da 2ª execução (doc 56 Reg.02).
3. `Refaz Saldos` do vídeo = **MATA300** (binding SX1 `MTA300`), não
   DEL100.

### F. Reuso (gate §0)

`B1_CUSTD` lido como `standard_cost` nos product repositories —
`REUSE_CONFIRMED` (leitura). SB9 lido por `stock_value_official_closure_sql`
/`stock_value_historical_sql` — `REUSE_CONFIRMED` (snapshot de
fechamento). `GET /supplies/cpv` — `REUSE_PARTIAL` (custo corrente).
Nenhum contrato de status/orquestração de fechamento existe —
`TARGET` futuro; nada criado nesta rodada.

### G. Gates

- **G4 `PASS`** (antes `PENDING`): rotinas bound (MTA320/MTA300 via SX1
  1:1 + `TTAT_PROGRAM`), parâmetros íntegros, efeito MATA320→`B1_CUSTD`
  provado em dados, artefato da etapa 3 reconciliado com SB9, DEL100
  desambiguado.
- **G5 `INCONCLUSIVE`** (antes `TEST_NOT_RUN`): MATA320 verificado
  ponta-a-ponta; mas a cadeia fechamento→SB9 não tem writer identificado,
  MATA300 não deixa rastro físico auditável do efeito, a etapa 4 do
  wizard não foi exibida e a execução do vídeo é **demonstração** —
  paridade do artefato 98,6% com Δ explicado (drift temporal + `MOD*`).
- G6 `PENDING` — aceite Controladoria.
- Métricas: auditoria 52→**53/90 (58,9%)**; coleta 44/60 inalterada.

### H. Residuais

- **E5** (TI/ERP/DBA): writer efetivo do SB9 nas rajadas 02/10 e 21/10;
  vínculo etapa-4-do-wizard↔gravação.
- **E4** (DBA): SPs `STP_DELPI_OP_TERCEIRO_*`/`STP_PROTHEUS_DELPI_*` e
  jobs — ausentes/inacessíveis; existência física e origem.
- **E12** (Controladoria/TI-ERP): sequência oficial e checkpoints
  obrigatórios; identidade formal da rotina "Refaz por DIT terceiros";
  confirmação dos efeitos do MATA300 (`Recalcular` MOD); papel do
  `MV_ULMES` como evidência de fechamento concluído.
