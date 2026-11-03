# 152 — Auditoria do conhecimento da CLARA, relatório a relatório (R01–R15)

**Data:** 03/11/2026 · **Base GitHub observada antes do registro:** `1e89b112f661b613ec673fb1a21f893cb59c8784` (HEAD remoto; git status local não acessível por este canal).
**Fonte efetivamente consultada:** ferramentas CLARA `get_context(topic=catalog)`, `knowledge(action=sources)` e `knowledge(action=search,query=R01..R15)`. **Corpus CLARA:** versão `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00`, publicada em 30/10/2026 11:16 -03, 2.186 itens, 88 fontes. Foram feitas pesquisas individuais para cada ID, com inspeção das respectivas seções de fichas. **Não foram executados aqui SQL completo, comparações exaustivas de producers nem consultas de dados de todos os R01–R15.** Este documento é triagem semântica da CLARA, não certificação de paridade oficial.

## Perguntas padronizadas da auditoria

Para cada relatório: (1) que problema resolve, momento do PROC-0072 e classificação REPORT/ERP_ROUTINE/DOCUMENT; (2) produtor oficial e origem canônica; (3) tabelas/joins/campos e grão; (4) filtros, datas, exclusões e parâmetros; (5) fórmulas, agregações e custo histórico; (6) exemplos reais, reconciliabilidade e divergências; (7) limitações/paridade/status; (8) citações verificáveis e versão da ficha comparada ao HEAD e contratos; (9) decisões/owners pendentes.

## Matriz por relatório: o que a CLARA efetivamente recuperou e o que melhorar

| ID | Natureza | Evidência de conhecimento CLARA encontrada | Lacuna ou revisão necessária | Triagem |
|---|---|---|---|---|
| R01 Baixas a pagar | Consulta financeira operacional / artefato FINR190 | BR-R01-001..011, população, estornos, valores, filial origem, SE5/SED e limites de equivalência | Conferir SQL/SE2/SE5 efetivo e catálogo versus paridade oficial; ficha ainda enfatiza emissão externa | VERIFY_RUNTIME |
| R02 Baixas a receber | Consulta financeira / DLP06R01 | Regras de valores, estornos, SE5×SE1×SED, diferenças entre pagar e receber | Fonte oficial ausente/parametrização geral incompleta; não apresentar paridade como fonte provada | SOURCE_GAP |
| R03 P7 | Snapshot de estoque; não rotina de execução | BR-R03-002..008, MATR989 em processo, estoque ex-99, recortes MP/PA/PI | Parâmetros oficiais, variante MATR460 e homologação por competência; identificar SQL atual | OFFICIAL_PARITY_PENDING |
| R04 Consumo por OP | Consulta operacional, NÃO equivalência MATR860 | **Ficha CLARA de 31/10 ainda afirma “não há operação Portal/CLARA”, “owner técnico nenhum”, “report_not_implemented”** | **STALE_EVIDENCE crítico:** produtor consumption-audit e BFF/CLARA/MFE publicados; atualizar ficha com SC2/SG1/SD4/SD3, distinção entre consumo auditado e MATR860, ordenação global G070, status administrativo C2_STATUS e ausência de centro escalar; confrontar regressão CLARA HTTP400 CF-UX-050 | P0_STALE |
| R05 Entradas e saídas | Consulta de movimentação | BR-R05-001..012, SD1/SD2/SD3/SB9, filtros, saldo inicial/final, TTAT as_of, reconciliação | Verificar SQL/versão atual, drift pós-emissão, paridade MATR320 não homologada | VERIFY_RUNTIME |
| R06 Kardex/CPV | Relatório MATR910 + medida gerencial distinta | Modelo UNION, filtros F4_ESTOQUE/D3_ESTORNO/ORIGLAN, SB9, TTAT, CalcEst, diferenciação CPV | Revisar custo as-of, parâmetros efetivos e código atual; homologação oficial segue distinta da reconstrução | VERIFY_RUNTIME |
| R07 Inventários | Recorte de ajustes do MATR910 | BR-R07-001..003, D3_DOC INVENT, entradas/saídas e reconciliação histórica 45/45 | Confrontar universo corrente (45 históricos vs contagem live diferente), filtros por filial/armazém; não inferir regressão só pelo total | RECONCILE |
| R08 Material em processo | Consulta MATR989 / H02 | BR-R08-001..006, SD3 RE*/DE*, OP ativa, saldo por par e armazém 99 | Conferir critérios de corte temporal, data de OP, valor as-of e paridade oficial | VERIFY_RUNTIME |
| R09 Faturamento × MOD | Consulta operacional DLP204 | Ficha possui BR-R09, expansão de PA, quantidades e fonte DLP204 | **STALE_EVIDENCE crítico:** ficha afirma “sem endpoint”, “CLARA não pode consultar”, “owner técnico nenhum”, “report_not_implemented”; já existe produtor/BFF/CLARA/MFE com operational_view, `source_missing` no custo SP e G042; atualizar com SHA/contratos e limites | P0_STALE |
| R10 Despesas por centro de custo | Consulta operacional/investigativa | 13 TES de exclusão, D1_DTDIGIT, MP fora, apuração ≠ investigação, divergência 12-vs-13 | Validar contra SQL atual e fechar semântica de classificação Direto/Ind/Adm e G6 | OWNER_RULE_PENDING |
| R11 NF a desconsiderar | Lista investigativa, sem exclusão automática | SD2/SF4, grupo 9035∩TES594, custo zero estrutural, não equivale erro | Decisão funcional E11a/E11b ainda aberta; não recomendar exclusão automática | OWNER_RULE_PENDING |
| R12 Estado de fechamento de custos | **ERP_ROUTINE** observada, Portal read-only | MATA320/MATA300/MATA330, B1_CUSTD, SB9/MV_ULMES, wizard e limites | Ficha `TARGET` e visão antiga; incorporar **novo design 151 / Gate 071** e ferramenta CLARA cost_closing_state, sem inferir execução/homologação | STALE_CONTEXT |
| R13 Extratos/aplicações | **DOCUMENT_EVIDENCE** externa | Origem externa, coleta Controladoria, DRE/Contabilidade; não há SQL TOTVS | Especificar inventário de instituições/tipos, checklist e upload P2/P5; não chamar relatório SQL bloqueado quando fluxo documental existe | DOC_CLASSIFICATION |
| R14 Importação/câmbio | **DOCUMENT_EVIDENCE** externa | Evidência de importação/câmbio/SWIFT/ACSI, origem externa | Aplicabilidade, owner e arquivo real, upload/competência; não criar produtor SQL | DOC_CLASSIFICATION |
| R15 Cutoff/virada | **ERP_ROUTINE / estado observado read-only** | MATA330/MATA280, SB9/MV_ULMES, timestamps e evidências de virada | Ficha `TARGET_ONLY` e sem referência suficiente à página read-only atual R12/R15; separar observação técnica de homologação e de execução | STALE_CONTEXT |

## Achados transversais fundamentados

1. **P0 documentação desatualizada:** R04 e R09 contradizem entregas registradas posteriormente a 31/10. Não remover cautela oficial MATR860 nem inventar SP DLP204 ao atualizar.
2. **R12/R15:** descrições de rotina do ERP devem explicar a página operacional read-only implementada, com semântica de evidência (3/5 não é fechamento 60% concluído). Atualizar para linguagem de negócio do doc 151 sem apagar rastreabilidade técnica.
3. **Separação essencial:** R13/R14 são documentos externos (P2/P5), não SQL; R12/R15 são rotinas/processos executados no TOTVS e visualização de estados, não relatórios financeiros a reimplementar.
4. **Conhecimento ≠ SQL do HEAD:** a busca CLARA retorna fontes e snippets; não foi provado que cada ficha reflita a query/joins do produtor em produção ou a versão deployed. Exigir revisão de código/produtor + testes antes de chamar regra `PROVEN_IN_RUNTIME`.
5. **R02, R03 e homologação oficial:** preservar estados `SOURCE_MISSING`/`PENDING` e evitar confundir reconstrução operacional com emissão oficial.
6. **Busca CLARA:** consultas excessivamente detalhadas combinadas com `report_id` retornaram `items:[]`, enquanto consultas simples `query="MATR910"`, `query="R04"` retornaram fontes. Resultado vazio **não** significa ausência de conhecimento; revisar lógica de busca/ranking e cobertura de perguntas sem inferir.
7. **Governança:** recomenda-se versão/publicação incremental das 15 fichas, com source SHA, owner, evidence class, último teste positivo, contrato produtor e data do corpus; usar GitHub como authority TARGET e TÉO como authority AS-IS.

## Backlog de correção proposto — sem implementação autorizada nesta auditoria

- **CLARA-KNOW-001 (P0):** corrigir fichas R04 e R09 e republicar corpus; validar consulta/resposta de conhecimento, owner e SHA.
- **CLARA-KNOW-002 (P1):** atualizar fichas R12/R15 e distinguir rotina TOTVS de visão de acompanhamento read-only atual; documentar limitações de estado e aprovação humana.
- **CLARA-KNOW-003 (P1):** matriz source-to-SQL-to-contract para R01–R11, com grão, filtros, fórmulas, colunas, datas, costs as_of, joins, producers/consumers, teste e SHA; executar auditoria um a um no HEAD antes de afirmar paridade.
- **CLARA-KNOW-004 (P1):** fechar cobertura documental R13/R14 (instituições, aplicabilidade, owner, fluxo P2/P5), sem tratar como relatórios TOTVS.
- **CLARA-KNOW-005 (P1):** testar qualidade do mecanismo de busca CLARA, fonte, ranking e citações; distinguir miss real vs consulta restritiva.
- **CLARA-KNOW-006 (P1):** regressão da CLARA R04 HTTP400 (CF-UX-050) é problema operacional separado; o corpus não conserta gateway/contrato e não deve mascará-lo.

**Status final deste documento:** `AUDIT_INVENTORY_COMPLETE` das fichas CLARA para os 15 IDs; `INCONCLUSIVE` para garantia de conhecimento de SQL real em todos os produtores; sem alteracão de código ou runtime. Próximo gate deve fechar matriz fonte→SQL→contrato por relatório e atualizar corpus com provas.


## 6. Segunda passagem — confronto direto com SQL e contratos no HEAD (03/11/2026)

**Alcance e evidência:** leitura direta de arquivos `main` via GitHub; SQL verificado em `api-delpi` para R04, R05, R06/R07; use case e BFF para R04/R09; cliente MFE R04; fichas GitHub R04/R06/R09/R12. Além disso, CLARA `knowledge(search)` foi consultada individualmente R01–R15 com seleção de até 40 itens por ID, e `read(report.production_order_consumption)` e `read(report.billing_mod_breakdown)` foram chamados neste gate. **Não foi executada query SQL diretamente no banco.** Branch GitHub `main`; HEAD GitHub foi conferido via search commits. `git status` local de um runner não foi obtido. O trecho abaixo é `CODE_PROVEN` para condições SQL literais, `CLARA_PROVEN` para respostas do connector, e `PENDING` para paridade/execução em produção não comprovadas.

### R04 — Consumo por OP: produtor real versus ficha CLARA

**Contradição comprovada e alta prioridade:**
- `fichas/R04-ficha.md` (e resultado da CLARA, corpus 30/10) ainda afirma que não existe operação Portal/CLARA, produtor técnico ou regra registrável. `STALE_EVIDENCE` frente à implementação atual.
- **Fonte real da listagem:** `api-delpi/app/infrastructure/persistence/totvs/production_repositories/consumption_audit_sql.py`. Grão **uma OP** (`SC2010 OP` com `SB1010 P` para descrição; paginação `OFFSET/FETCH`); BFF `production_order_consumption_routes.py` preserva `officiality=operational_view`, `officialParity=pending`. Detalhe reutiliza diversas fontes (SC2/SD4/SD3/SH6/HZA/SH8/SG2/SG1/SB1).
- **Campos listados:** `C2_FILIAL`, `C2_OP`, `C2_NUM`, `C2_ITEM`, `C2_SEQUEN`, `C2_PRODUTO`, `B1_DESC`, `C2_UM`, `C2_QUANT`, `C2_QUJE`, `C2_STATUS`, `C2_TPOP`, `C2_EMISSAO`, `C2_DATPRI`, `C2_DATPRF`, `C2_DATRF`.
- **Datas reais:** `emission=C2_EMISSAO`; `finished=C2_DATRF`; `appointment` seleciona OP via `EXISTS SH6010.H6_DTAPONT` dentro do período; datas planejadas `C2_DATPRI/DATPRF` não são filtros `date_type`.
- **Filtros SQL:** filial obrigatória e deleção lógica; `search` por `C2_OP/C2_NUM`; `product` por código/descrição; `status=C2_STATUS`; `work_center`/`operation` por `EXISTS SH8010` (multiplicidade SH8, **não** coluna escalar na listagem). LIKE com escape de curinga e parâmetros bindados.
- **Ordenação global atual:** allowlist `production_order,product_code,product_description,status,date`; `date` usa a data escolhida por `date_type` (appointment ordena pelo `MIN(H6_DTAPONT)`); direção asc/desc; desempate por OP asc. **Sem sort:** ordem legada `C2_EMISSAO DESC,C2_OP ASC`; `sort_direction` sem `sort_by` é inválido. Valor externo não é interpolado no SQL.
- **Serviço já existe:** `GET /supplies/consumption-audit/orders` com S2S `consumption-audit.read` e clients `supplies-api`, `controllership-finance-api`; BFF `GET /closing/competences/{period}/production-order-consumption`, client MFE `productionOrderConsumptionApi.ts` normaliza snake_case.
- **Runtime nesta auditoria:** CLARA `read(report.production_order_consumption)` `period=2026-09,branch=01` → **HTTP 400 “Parâmetros inválidos.”** (`FAIL`, reproduzido). Não declarar operacionalmente restabelecido; CF-UX-050 permanece aberto. A comparação documental não prova causa do 400.
- **Limite de conhecimento:** contrato `consumption-audit` não implica paridade oficial `MATR860`; equivalência permanece `pending`. Descrever a semântica administrativa `C2_STATUS` separada do progresso da OP.

**Ação concreta:** reescrever seção `identificação/fonte/regras/operação` da ficha R04 com código/SQL/owner e marcação de oficialidade, depois republicar corpus; criar teste de pergunta CLARA que rejeite “não implementado” e não confunda sort, período e progressão.

### R09 — Faturamento × MOD: motor atual versus ficha recuperada

- No corpus CLARA (30/10), ficha ainda diz: “CLARA não pode consultar dados — sem endpoint”, “report_not_implemented” e “owner técnico nenhum”, embora `fichas/R09-ficha.md` no GitHub **já possua apêndices** de implementação G049/G051. **Defasagem de publicação/indexação do corpus**, distinta da manutenção de arquivo-fonte.
- O use case do HEAD `api-delpi/app/application/use_cases/financeiro_billing_mod_breakdown/get_billing_mod_breakdown_use_case.py` seleciona âncoras de PA faturado via SD2/SF4 `F4_DUPLIC='S'`, expande componentes diretos SG1 por nível, propaga quantidades, associa operações/recursos e emite custo tipado `source_missing` quando a taxa dependente de SP não existe. Não substituir taxa ausente por zero.
- O mesmo código executa `_build_branch_anchors` para pré-carregar arestas/ operações por filial e expõe `officialParity=pending`.
- **Teste live independente neste gate:** `CLARA read(report.billing_mod_breakdown)` `period=2026-09,branch=01` → **PASS**; `anchors=299`, `limitations=8`. Portanto **a afirmação do corpus “sem endpoint” é falsificada por consulta positiva real**, mas paridade DLP204 oficial continua `pending`.
- **Ação:** republicar ficha R09 vigente com identificação do contrato e regra `source_missing`, atualizar resumo de capacidade e teste live positivo sem congelar números históricos como invariantes.

### R05 — Entradas e saídas: SQL diretamente verificado

- Fonte: `api-delpi/app/infrastructure/persistence/totvs/financeiro_stock_movements/stock_movements_sql.py` (`CODE_PROVEN`).
- SD1: `D1_DTDIGIT`, `D1_ORIGLAN<>'LF'`, TES SF4 exigindo `F4_ESTOQUE='S'`; SD2: `D2_EMISSAO`, `D2_ORIGLAN<>'LF'`, TES estoque; SD3: `D3_ESTORNO<>'S'`, custo `D3_CUSTO1` assinado conforme direção. Produto/categoria `SB1.B1_TIPO`; universo de saldos `SB9`.
- **Comparação ficha:** BR-R05-002..012 descreve as famílias e reconstrução TTAT `as_of` sem contradição conclusiva nesta leitura. Mas ainda falta auditar cada predicado de TES, sinal, intervalo e join e comparar com dados reais; **não declarar SQL 100% equivalente só por correspondência de fontes**.

### R06/R07 — um motor, dois recortes; condicionais que a CLARA deve explicar

- Fonte: `api-delpi/app/infrastructure/persistence/totvs/financeiro_stock_kardex/stock_kardex_sql.py` + use case `financeiro_stock_kardex/get_stock_kardex_use_case.py` + `stock_kardex_router.py`.
- Kardex: UNION SD1/SD2/SD3; SD1/SD2 via SF4 com restrições `F4_ESTOQUE='S'`; `D1_REMITO=''`; exclui `D1_ORIGLAN='LF'`/`D2_ORIGLAN='LF'`; SB9 define saldo anterior por grão; TTAT históricos de custo em logs SD2/SD3 com custo as-of; movimentos separados do CPV gerencial.
- **Nuance relevante que a ficha simplifica:** exclusão `D3_ESTORNO='S'` no SQL do Kardex é **condicional ao parâmetro `MV_D3ESTOR='N'`**. A ficha BR-R06-002 descreve o filtro como regra incondicional. Não afirmar que isso necessariamente altera resultados; é **potencial divergência de explicação** a validar com parâmetros produtivos e owner.
- R07: o próprio router expõe leitura dedicada inventory-adjustments; o mesmo SQL acrescenta `D3_DOC='INVENT'` para o recorte. Não inventar motor separado. `fichas/R07-ficha.md` descreve 45/45 linhas históricas — não confundir com quantidade viva de todos os filtros/filiais.
- **Ação:** revisar ficha R06 BR-R06-002 para explicitar `MV_D3ESTOR`, separar custo as-of por tabela e CPV, revisar ficha R07 com os parâmetros históricos da amostra versus consulta viva; a paridade oficial por competência permanece pendente.

### R12/R15 — documentação publicada versus CLARA e tela

- `fichas/R12-ficha.md` atual no GitHub já descreve `GET /financeiro/closing-state` → BFF `/closing/competences/{period}/cost-closing-state` → MFE/CLARA `read(report.cost_closing_state)`, com cautela `technical_markers`.
- O corpus CLARA ainda recupera segmentos `TARGET` de 31/10 e não incorpora integralmente o design aprovado Doc 151, executado Gate 071. **Atualizar publicação do corpus** com a versão GitHub atual, garantindo que `3/5` evidências não sejam explicadas como 60% de rotina executada.
- R15 continua processo de virada no TOTVS (`MATA330/MATA280`) e estado técnico observado; nenhuma leitura equivale execução/homologação.

### Veredicto de evidência desta passagem

| Escopo | Resultado |
|---|---|
| R04 SQL + filtro + sort + BFF + MFE | `PROVEN` em código, CLARA runtime `FAIL` HTTP400 |
| R09 use case + consulta CLARA real | `PROVEN` / `PASS`; conhecimento indexado `STALE_EVIDENCE` |
| R05 SQL vs regra CLARA | Famílias confirmadas; paridade completa `INCONCLUSIVE` |
| R06/R07 SQL vs ficha | Fontes confirmadas; divergência de **descrição condicional** `MV_D3ESTOR` precisa validação |
| R12/R15 ficha do GitHub versus CLARA | Desatualização do corpus e design recente `PROVEN`; homologação `PENDING` |
| R01/R02/R03/R08/R10/R11 SQL literal completo | `TO_INVENTORY` neste gate (documentação consultada, SQL linha a linha não revisado) |
| R13/R14 | Documentos externos, não relatórios SQL TOTVS |

**Prioridade seguinte:** `CLARA-KNOW-001` correção R04/R09; `CLARA-KNOW-007` verificar e ajustar a descrição R06 da condição `MV_D3ESTOR`; `CLARA-KNOW-008` republicar R12/R15 e registrar SHA/versão de corpus. Não mudar SQL por discrepância documental sem evidência. Este gate é **DOCUMENTATION_ONLY**.


## 7. Terceira passagem — SQL literal R01/R02/R03/R10/R11 (03/11/2026)

**Escopo:** leitura direta dos arquivos SQL `financeiro_settlements/settlements_sql.py`, `financeiro_stock_inventory/stock_inventory_sql.py`, `financeiro_cost_center_expenses/cost_center_expenses_sql.py`, `financeiro_billing_exclusion_roster/billing_exclusion_roster_sql.py`, com comparação às fichas R01/R02/R03/R10/R11 disponíveis na CLARA. Sem execução de queries live aqui.

### R01/R02 — distinção crítica entre artefato histórico SE5 e consulta operacional atual

- **Fonte do SQL ativo:** `api-delpi/app/infrastructure/persistence/totvs/financeiro_settlements/settlements_sql.py` e não simplesmente a tabela `SE5`. O builder usa eventos de baixa `FK2010` (pagar) / `FK1010` (receber), join de títulos via `FK7010` (`FK7_IDDOC`, `FK7_ALIAS='SE2'|'SE1'`), títulos `SE2010`/`SE1010` e naturezas `SED010`.
- O valor de evento é `FK2_VALOR`/`FK1_VALOR`, não valor total original do título `E2_VALOR`/`E1_VALOR`; competência usa `FK2_DATA`/`FK1_DATA`, não presumir `E5_DATA` como eixo da API operacional. `LEFT JOIN` e `OUTER APPLY TOP 1` preservam baixa sem título/natureza ligados e informam qualidade do vínculo.
- A CLARA recupera fichas R01/R02 com `SE5×SE2/SE1×SED`, `E5_DATA`, descrição da **emissão documental histórica** e também o termo “consulta operacional” — documentação pode induzir usuário a explicar o cálculo atual a partir da fonte errada.
- **Classificação:** `KNOWLEDGE_BOUNDARY_MISMATCH`, não `SQL_BUG`. Separar na resposta da CLARA: (a) relatório histórico / layout custom comprovado, (b) consulta operacional atual `FK1/FK2+FK7+SE1/SE2+SED`, (c) paridade com emissão oficial **não homologada**. Atualizar fichas e respostas com dois blocos explícitos, fonte/versão distintos. **Prioridade P0** (erro de orientação sobre tabelas).

### R03 — snapshot P7

- **SQL verificado:** `financeiro_stock_inventory/stock_inventory_sql.py` lê `SB9010` no encerramento do mês com `SB1010`, por filial × armazém × produto. O cabeçalho SQL distingue o snapshot exato de estimadores de saldo pela última SB9 + SD3.
- **Ficha CLARA:** descreve emissão histórica MATR460 e composição P7, inclusive bloco “em processo” do MATR989. Isso não prova que a consulta de snapshot R03 seja uma emissão oficial MATR460. Explicar separadamente o motor operacional do Portal (`SB9` exata) e os conceitos do relatório oficial; composição e limites devem ser verificados contra o use case (não inteiramente nesta passagem).

### R10 — seleção operacional na aplicação, não filtro SQL pré-aplicado

- **SQL verificado:** `financeiro_cost_center_expenses/cost_center_expenses_sql.py` traz linhas `SD1010` por `D1_DTDIGIT`, com dimensões `SB1010`, `SA2010` e `CTT010` (`OUTER APPLY TOP 1` por filial/CC). A query **não aplica o conjunto de exclusões 13 TES / MP / benefícios no WHERE**; devolve os atributos para classificação no use case `calculation` versus `investigation`.
- A ficha CLARA sabe os 13 TES, exclusão MP e distinção apuração/investigação. Aperfeiçoar a explicação dizendo **qual etapa executa a regra**, evitando a afirmação falsa de que o SQL já elimina os documentos excluídos. Não muda a decisão humana Direto/Indireto/Adm pendente.

### R11 — SQL de universo OR e classificação investigativa no use case

- **SQL verificado:** `financeiro_billing_exclusion_roster/billing_exclusion_roster_sql.py` lê `SD2010` no eixo `D2_EMISSAO` com predicado de **universo** `D2_GRUPO = grupo-alvo OR D2_TES = TES-alvo`; `SF4010` via `OUTER APPLY TOP 1`, `SB1` e `SA1` via LEFT. Document siblings de mesmo `filial+doc+série` têm métricas correlacionadas.
- A ficha CLARA descreve o conjunto de **candidatas** como `9035∩594` (interseção). **Não é contradição necessariamente:** SQL inclui também linhas relacionadas fora do critério para investigação; a **classificação de candidatas/out_of_criteria é responsabilidade do use case**, não do SQL. Explicar claramente: `UNIVERSE = grupo OR TES`; `CANDIDATES = grupo AND TES`; não confundir “encontrado para investigação” com “deve excluir NF”.
- **Classificação:** `KNOWLEDGE_EXPLANATION_GAP`, não defeito SQL provado. Sem mudança de regra sem autorização do owner.

### Consolidação das novas ações

- **CLARA-KNOW-009 (P0):** R01/R02 — separar semântica de relatório histórico SE5 do **SQL operacional FK2010/FK1010+FK7**; perguntas “qual tabela?”, “qual data?”, “qual valor?” devem retornar a fonte da visão explicitamente indicada.
- **CLARA-KNOW-010 (P1):** R10/R11 — explicar corretamente distinção entre `SELECT do universo` e `classificação no use case`, com dois exemplos de linha candidata/fora de critério.
- **CLARA-KNOW-011 (P1):** R03 — explicitar motor de snapshot SB9010 versus P7 oficial e não declarar equivalência sem homologação.
- **R08:** producer SQL literal ainda `TO_INVENTORY` nesta passagem; documentação do domínio recuperada, não extrapolar.
- **Status:** `CODE_PROVEN` em cinco arquivos SQL e diferenças de explicação; `INCONCLUSIVE` para paridade de produção ou resultado de todos os predicados downstream. `DOCUMENTATION_ONLY`.


## 8. GPT REVIEW independente do Gate 072 (03/11/2026, ~10:31 BRT)

**GitHub `main` conferida:** `99e892807715feebcb8d52e91205274c0d4cd68b`; implementação `e83fc8341195e918e89e6f58d51e15b65fc855b8`, documentação `d2fdead52acbdf81c89a00436fb97d4486a174b2` / `99e8928077...`. Commit de código modificou rota BFF R04, `tool_bridge.py` e fichas R04/R09/R12/R15, não os 15 arquivos de fichas. Git status local e SHA de containers não foram verificados diretamente.

**Corpus realmente observado na CLARA conectada:** `497ec9af-00d4-4e07-9b64-b96fcc97f3c5`, publicado `2026-11-03 10:29:04-03`, **2.230 itens / 88 fontes** — `PASS` em existência/versão, não em qualidade semântica de todas as respostas.

### Testes live executados no GPT REVIEW

| Verificação | Resultado | Evidência factual |
|---|---|---|
| `read(report.production_order_consumption)` 2026-09, branch 01 | **PASS** | `success=true`, total **1.243**, 25 linhas na página padrão; primeira OP `24841701001` |
| `read(report.production_order_consumption)` 2026-10, branch 01 | **PASS** | `success=true`, total **2.381**, 25 linhas; primeira OP `24905301001` |
| `read(report.billing_mod_breakdown)` 2026-09, branch 01 | **PASS** | `success=true`, **299 âncoras**, 8 limitações |
| `read(report.cost_closing_state)` 2026-09 | **PASS** | `success=true`, quatro limitações |
| `knowledge(search,query='R04')` | **PASS parcial** | nova ficha `R04-ficha.md` identifica produtor api-delpi, BFF, rota e `IMPLEMENTADO`, preservando MATR860 `pending` |
| `knowledge(search,query='R09')` | **FAIL semântico** | **mesma ficha R09 atual** retorna seção “Interpretação” com `não pode consultar dados — sem endpoint` e `report_not_implemented`, embora seção “Identificação” diga `IMPLEMENTADO` e read real passe. Busca também retorna bloco de publicação antigo `PENDING_CONTRACT/EXTERNAL`, versão 1.0/31-10 |
| `knowledge(search,query='R12')` | **Inconsistência histórica recuperável** | seção `Identificação` diz `IMPLEMENTADO` e seção “Atualização v1.1” cita CLARA live, mas cabeçalho inicial ainda diz corpus antigo `5bebf07f` e `sem contrato operacional`; legenda `report_not_implemented` aparece em interpretação histórica |
| `knowledge(search,query='R15')` | **Inconsistência histórica recuperável** | seção “Identificação” diz `IMPLEMENTADO`, mas título de versão 1.0 cita publicação antiga `5bebf07f` e `sem contrato operacional`; `fichas/README.md` também permanece na versão anterior |

**Causa documentada:** a edição do Gate 072 atualizou linhas de `Implementação`, mas preservou no mesmo documento indexado blocos antigos com afirmações presentes formuladas no presente (“não pode consultar”, “hoje report_not_implemented”), sem marcação estruturada inequívoca de HISTÓRICO OBSOLETO. A ingestão incorporou esses blocos; nova versão publicada **não os tornou inacessíveis**. Não é prova de falha no parser ou no ranking, mas é prova de **contradição na base de recuperação**. Os nomes de fontes do corpus ainda incluem, por exemplo, “Ficha R04 — Consumo por OP (bloqueado)”, mesmo com corpo atualizado, exigindo revisar títulos/manifests se esses títulos forem mostrados aos usuários.

### Veredito por objetivo

- **Incidente P0 CF-UX-050 (CLARA R04 HTTP 400): `PASS` na consulta real positiva em duas competências.** Código no HEAD adiciona `isinstance(value,str)` antes de encaminhar os params do R04, coerente com hipótese de `Query` default leak; correção causal isolada depende de testes de requisição, mas outcome agora comprovado.
- **Corpus publicado: `PASS`** para versão, data, volume e disponibilidade.
- **R04 explicação: `PASS parcial`** (identificação atualizada; não comprova bateria de perguntas).
- **R09 explicação: `FAIL`**: corpus contradiz consulta real na seção “Interpretação”; **precisa de rework documental/publicação**.
- **R12/R15 explicação: `FAIL parcial/STALE_EVIDENCE`** em trechos históricos que ainda podem ser recuperados sem qualificação.
- **105 perguntas R01–R15: `TEST_NOT_RUN`**; para correção de conhecimento integral, não declarar 15/15 PASS. Demais fichas não atualizadas conforme relatório Devin e matriz doc 152.

**Veredito de conjunto do Gate 072: `REWORK` para o objetivo de conhecimento correto R01–R15; `ACCEPT_WITH_RESIDUAL` apenas para a correção operacional do R04 + publicação física do corpus.**

**Rework mínimo sugerido:** (1) revisar ficha R09 por inteiro, reescrevendo interpretações presentes falsas e referências históricas, não apenas a linha Implementação; (2) retirar ambiguidades semelhantes do texto ativo R12/R15, preservando eventos históricos somente em seção rotulada “Histórico, não estado atual”; (3) atualizar índice/manifests/títulos de fontes; (4) republicar corpus pela rotina canônica; (5) **retestar knowledge search** para termos negativos (`não pode consultar`, `sem endpoint`, `report_not_implemented`) com report_id e por query, verificando atribuição temporal e referências; (6) executar bateria de perguntas progressiva ao longo de R01–R15 com prova source→SQL→contrato, sem modificar SQL/segurança por aparente drift semântico.

**Segurança e paridade:** nenhuma alteração de SQL/TOTVS/permissions requerida pelo achado. R04 MATR860 e R09 DLP204 continuam `officialParity=pending`. Validação Portal visual autenticada ainda `TEST_NOT_RUN` nesta revisão.
