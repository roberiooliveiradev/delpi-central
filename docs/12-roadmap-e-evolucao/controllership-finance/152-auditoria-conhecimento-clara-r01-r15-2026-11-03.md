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


## 9. GPT REVIEW independente — Gate 073 (03/11/2026)

**Commits verificados:** `main=5c5f58d5cf4cb91e401a842a5a0ece1356f51ce7`; commit funcional/documental `f11d1f9f644465e2f1be2213739b970faa0b3343` (cinco arquivos: `corpus_manifest.py`, fichas R09/R12/R15, `fichas/README.md`). `git status` local não inspecionado.

**Corpus live:** `knowledge(sources)` devolveu `664c61b3-38f3-469a-8019-a94db5c2c81f`, publicado 03/11/2026 10:40:21 -03, 2.252 itens / 88 fontes — `PASS` publicação.

**R09:** consulta `knowledge(search,query="R09")` recupera trecho de implementação vigente e interpretação reescrita, sem a antiga negativa presente de “não pode consultar — sem endpoint”. Histórico está rotulado como pretérito. `PASS` no caso pontual (não significa 105/105).

**REGRESSÃO CRÍTICA REPRODUZIDA EM GITHUB E CLARA — R12/R15:** arquivos `docs/.../fichas/R12-ficha.md` e `R15-ficha.md` contêm substituição textual global destrutiva de barras `/` pela sequência **` para rotinas (visão read-only)`**. Amostras literais no HEAD:
- R12 L1 título `Fechamento de custo  para rotinas (visão read-only) Reposição ...`; L3 data `31 para rotinas (visão read-only)10 para rotinas (visão read-only)2026`; L9 `Código para rotinas (visão read-only)nome`; L87 paths `GET para rotinas (visão read-only)financeiro...`.
- R15 L1 `Cutoff para rotinas (visão read-only) sacramentação...`; L3 data corrompida; L18 `R12 para rotinas (visão read-only)R15`; L78 divisores de campo corrompidos.
- A CLARA recupera esses mesmos títulos e fragmentos via `knowledge(search)`, logo `CORPUS_SEMANTIC_FAIL` além de `SOURCE_CORRUPTION`.
- A falha não foi eliminada pela alegada correção de heredoc e foi **commitada e publicada**. Provável classe de causa: substituição indiscriminada de separadores `/`; diagnóstico do comando específico não provado, não presumir além dos bytes constatados.

**Outros resíduos observados:** `knowledge(sources)` ainda descreve fonte `Ficha R04 — Consumo por OP (bloqueado)`, embora `corpus_manifest.py` na main já contenha `(visão operacional)`: atualizar metadados reais/registro de origem e checar cache/source registry; não presumir que atualização do manifest implica renomeação no catálogo já publicado. `knowledge(search,R12)` recupera blocos duplicados com título antigo/nova ficha no mesmo documento, e blocos obsoletos `report_not_implemented`; investigar se são seções ainda presentes, múltiplas versões indexadas ou ambos, não concluir automaticamente supersede perfeito. R15 recupera bloco antigo semelhante.

**Testes live independentes de Gate 073:** `knowledge(sources)`, `knowledge(search,R04/R09/R12/R15)` foram executados. O executor informou `105 perguntas TEST_NOT_RUN` e `read R04/R09/R12 TEST_NOT_RUN`. Não promover para PASS. Último teste positivo R04/R09/R12 foi realizado na revisão do Gate 072, não novamente nesta revisão.

### Decisão do GPT REVIEW
**`REWORK` obrigatório** para Gate 073: regressão de integridade textual nas fichas R12/R15 confirmada no HEAD e propagada ao corpus. A publicação física e melhoria R09 foram `PASS` pontual, mas a entrega não satisfaz correção e qualidade semântica R01–R15.

### Rework mínimo seguro antes de republicar

1. Restaurar R12/R15 de versão íntegra pre-G073 (por exemplo, comparar blob do commit base do Gate 073) e reaplicar **somente diffs mínimos semânticos**, sem substituição global de `/` e sem reescrever backticks/URLs/paths/datas.
2. Verificar line-by-line ou diff estrutural; procurar toda ocorrência de `para rotinas (visão read-only)` e outras corrupções em ambas as fichas. Tratar `0 hits` como condição necessária, não suficiente; conferir datas, URLs, links, markdown, contratos e conteúdo original preservado.
3. Adicionar teste de integridade das fontes e validação de mudanças indevidas em arquivos do corpus (paths intactos, headings, datas, code spans, URLs e hash/citation_locator); executar antes do commit e ingestão.
4. Corrigir metadados R04 no **registry efetivamente servido** por `knowledge(sources)`, não apenas no manifest de origem; demonstrar output live.
5. Investigar segmentação/recuperação duplicada R12/R15 (version/supersede) e preservar histórico com distinção temporal explícita. Republicar corpus somente após gates de integridade `PASS`.
6. Smoke pós-publicação via CLARA autenticada: `knowledge(search)` R04/R09/R12/R15 e perguntas negativas, `read` R04/R09/R12; 105 cenários de explicação R01–R15 seguem como `TEST_NOT_RUN` até executados.

**Sem necessidade de alteração de regras de negócio, SQL TOTVS, boundaries ou permissões a partir destes achados.** Prioridade de correção: **P0 integridade textual R12/R15**.


## 10. GPT REVIEW independente — Gate 074 (03/11/2026)

**HEAD GitHub observado:** `06998895d54b716ef0fbe37a3734b1ff15ee351f` (após execução relatada). Commit de reparo `3efc207992546a7a1500087b50a45a8eb73afa94` modificou somente `R12-ficha.md`, `R15-ficha.md`, `test_fichas_integrity.py`. `git status` local do ambiente Devin não verificável neste canal.

**Corpus live:** `knowledge(sources)` retornou versão `60b2b2d9-52d2-46d0-8ce7-28454f4d52ff`, publicada em 03/11/2026 10:47:26 BRT, 2.252 itens/88 fontes — `PASS` para publicação física.

**Integridade dos arquivos no HEAD:** R12/R15 em `main` não contêm `para rotinas (visão read-only)`, e datas/títulos/rotas `GET /financeiro/closing-state`, `R12/R15`, `MATA330/MATA280` estão legíveis. `PASS` no escopo literal verificado. Teste canônico novo `test_fichas_integrity.py` existe com 2 asserts test cases para splice e identificadores; execução `2/2` é **reportada pelo executor**, não reexecutada neste canal.

**FALHA DE SUPSERSEDE/RECUPERAÇÃO COMPROVADA:** `knowledge(search,query="R12",limit=70)` retornou simultaneamente segmentos da fonte `ficha-r12` com `source_version=d7bc370cee33` (versão corrompida G073) **e** `source_version=937a783ca24d` (versão corrigida G074). A versão antiga aparece no próprio `heading_path` e `excerpt`, p.ex. `31 para rotinas (visão read-only)10 para rotinas (visão read-only)2026` e `Código para rotinas (visão read-only)nome`. `knowledge(search,query="R15")` também retorna títulos e trechos corrompidos junto a versões corretas. Logo `knowledge(sources)` apontar hash novo **não comprova** supersede efetivo da coleção pesquisável.

**Metadados live não corrigidos:** `knowledge(sources)` ainda retorna `Ficha R04 — Consumo por OP (bloqueado)` e `Ficha R14 — Importação / câmbio (bloqueado)`, embora o `corpus_manifest.py` tenha nomes atuais no HEAD anterior. `FAIL` no requisito de atualização de registry/sources servido.

**Consultas operacionais executadas independentemente nesta revisão:** `read(report.production_order_consumption)` 2026-09 branch01 `PASS` total 1.243/25 items; 2026-10 branch01 `PASS` total 2.381/25; `read(report.billing_mod_breakdown)` 2026-09 branch01 `PASS` 299 anchors e 8 limitações; `read(report.cost_closing_state)` 2026-09 `PASS`, 4 limitações. Esses resultados validam operação do conector, não eliminam falha no corpus.

**105 verificações de conhecimento:** `TEST_NOT_RUN` (executor não executou e esta revisão amostrou busca pontual, não 105 perguntas).

### Veredito

**`REWORK`** para Gate 074: **fonte GitHub reparada e corpus republicado, mas ainda há dados da versão corrompida recuperáveis em produção, comprovados por `source_version` duplicado sob mesmo `source_id`.** O objetivo de integridade **end-to-end** não está atendido. **`ACCEPT_WITH_RESIDUAL` apenas para reparo dos arquivos-fonte + operação dos relatórios**, não para o corpus.

### Próximo rework mínimo, com gate de segurança

1. Inspecionar mecanismo atual de ingestão/upsert/versionamento, índices de busca e filtros de validade `source_id/source_version/corpus_version_id`; rastrear por que corpus novo mantém itens `source_version=d7bc370cee33` ativos no search de R12. Não apagar versões em lote sem inventário/rollback; confirmar comportamento intended de retenção histórica vs busca default.
2. Garantir que a busca default de conhecimento vigente exclua/tipifique explicitamente fontes superadas; manter histórico consultável somente em fluxo histórico governado, se já previsto em contrato. Mudança de semântica de retenção/retrieval exige owner approval conforme governança; sem decisão, retornar `DECISION_REQUIRED`.
3. Corrigir persistência e exposição dos nomes de fontes em `knowledge(sources)` para R04/R14 por mecanismo existente; provar antes/depois.
4. Publicar corpus controladamente e **chamar CLARA autenticada pós-publish**: `knowledge(search,R12/R15)` deve devolver 0 trechos corrompidos, version correta nos localizadores; `knowledge(sources)` títulos atuais; `read` R04/R09/R12 deve permanecer PASS.
5. Executar auditoria de recuperação progressiva R01–R15 (105 perguntas quando sessão disponível); nunca deduzir PASS de contagem de ingestão.

Sem evidência para alteração SQL/TOTVS/permissions. Categoria deste achado: `CORPUS_VERSION_DRIFT / STALE_EVIDENCE`, não problema de ficha GitHub.


## 11. GPT REVIEW independente — Gate 075 (03/11/2026)

**GitHub:** commit funcional `5f54491018ef4927749d608f23ef9f711e01d5a6` alterou apenas `corpus_ingestion.py`, `clara_knowledge_repository.py` e `test_corpus_stale_sweep.py`. O HEAD da main consultado durante a revisão foi `47a6ae201660f11c3aa49d66c052b45b3ec34306`, já posterior ao `3e9ec63d10` relatado pelo executor. Git status local e digest do container não verificados diretamente.

**Publicação real:** CLARA `knowledge(sources)` retornou corpus `83dddfbe-7aeb-4a78-8cbe-570b6d6a8329`, publicado 03/11/2026 10:55:11 -03, 2.215 itens/88 fontes. `PASS` de leitura produtiva.

**Causa raiz confirmada por inspeção do código:** ingestão antes substituía segmentos coincidentes por locator/heading, mas não varria itens ainda `PUBLISHED` de headings removidas ou renomeadas. O novo `supersede_stale_items(source_id, keep_ids)` atualiza status dos itens não reconfirmados para `SUPERSEDED`, preservando histórico; `ingest_source` recolhe IDs atuais e chama sweep. O teste novo com FakeRepo prova chamada ao sweep e reporte de `stale_swept`; **não substitui testes SQL reais/concorrência/rollback por si só**. 2/2 da integridade de fichas e teste novo são resultados informados pelo executor, não reexecutados localmente pelo revisor.

**Teste MCP de recuperação vigente (independente):** `knowledge(search,query=R12/R15/R04/R09,limit=70)`, filtrados por `citation_locator.document` da respectiva ficha:
- R12: **5 itens da ficha**, exclusivamente `source_version=937a783ca24d`, **0** fragmentos de `d7bc370cee33` / splice.
- R15: **3 itens da ficha**, exclusivamente `source_version=8be9bacb3c5b`, **0** fragmentos corrompidos.
- R04: **2 itens da ficha**, exclusivamente `source_version=e9ea1ba60ebc`.
- R09: **4 itens da ficha**, exclusivamente `source_version=417222eaf0f7`, sem negativa presente de endpoint nos segmentos retornados.
O resultado comprova o cenário de busca real por IDs, não exaustividade de todas as expressões e tópicos.

**Metadados reais:** `knowledge(sources)` agora retorna `Ficha R04 — Consumo por OP (visão operacional)` e `Ficha R14 — Importação / câmbio (evidência documental externa)`. `PASS`.

**Consultas operacionais CLARA reais:**
- `read(report.production_order_consumption)` 2026-09 branch01: `success=true`, `total=1243`, 25 itens, `officiality=operational_view`, `officialParity=pending`.
- Mesmo relatório 2026-10 branch01: `success=true`, `total=2381`, 25 itens, `officialParity=pending`.
- `read(report.billing_mod_breakdown)` 2026-09 branch01: `success=true`, 299 âncoras, 8 limitações, `officiality=operational_view`, `officialParity=pending`.
- `read(report.cost_closing_state)` 2026-09: `success=true`, 4 limitações, `officiality=technical_markers`.

**Resultado:** `PASS` para objetivo P0 de versionamento vigente, integridade de fragmentos R12/R15 em busca real, metadata R04/R14 e regressões operacionais citadas. **Veredito Gate 075 = `ACCEPT_WITH_RESIDUAL`**.

**Resíduos explícitos:** (1) bateria de 105 perguntas R01–R15 `TEST_NOT_RUN`; (2) suite automatizada de cenários transacionais, rollback, publicação parcial, fontes vazias e concorrência não comprovada pelos testes novos apresentados; revisar antes de uma mudança maior; (3) smoke visual autenticado Portal não executado nesta revisão; (4) paridade oficial e decisões de owners permanecem pendentes conforme Documento 152. Não reabrir o incidente P0 sem evidência nova.


## 12. Auditoria exploratória de recuperação — 105 consultas R01–R15 (03/11/2026)

**Objetivo:** avançar a prova de qualidade da CLARA no corpus aceito no Gate 075. **Método real:** ferramenta MCP autenticada `knowledge(action="search",report_id=Rxx,query=tema,limit=12)` para todos os 15 relatórios × 7 temas `finalidade, tabelas, SQL, filtros, cálculo, paridade, limitações` = **105 chamadas executadas**. Critério de descoberta: presença da ficha canônica `fichas/Rxx-ficha.md` entre os doze primeiros resultados. Esse critério mede *recuperação*, não correção da resposta de um modelo conversacional, SQL parity, nem teste de `read` de cada relatório. Os temas não equivalem às sete perguntas contextuais adaptadas prometidas nos gates anteriores. Não chamar 105/105 de PASS semântico.

**Baseline:** GitHub main `a2c2020e310c8383f8533be2809622b3365e1f9f`; CLARA corpus `83dddfbe-7aeb-4a78-8cbe-570b6d6a8329`, 2.215 itens / 88 fontes.

| Item | Chamadas | Ficha canônica presente nos top-12 | Observação |
|---|---:|---:|---|
| R01 | 7 | 4 | Queries SQL/cálculo/paridade não trouxeram a ficha nos 12 primeiros |
| R02 | 7 | 3 | Busca genérica frequentemente prioriza docs 84/85/121 |
| R03 | 7 | 3 | Contratos transversais antecedem a ficha |
| R04 | 7 | 3 | Ficha não aparece em finalidade/tabelas/cálculo/paridade |
| R05 | 7 | 3 | Ficha ausente nas primeiras 12 em SQL/filtros/cálculo/paridade |
| R06 | 7 | 4 | Doc 122 e doc 85 competem com ficha |
| R07 | 7 | 3 | Mesmo motor documentado em contratos transversais |
| R08 | 7 | 4 | Ficha apareceu em SQL, não em cálculo |
| R09 | 7 | 2 | Ficha só apareceu em finalidade/limitações |
| R10 | 7 | 3 | Regras estão em docs amplos |
| R11 | 7 | 3 | Consulta genérica de SQL não prioriza ficha |
| R12 | 7 | 2 | Rotina/estado misturados a temas monetários genéricos |
| R13 | 7 | 4 | Documentos externos; perguntar SQL exige resposta “não aplicável” |
| R14 | 7 | 1 | Ficha só apareceu em finalidade |
| R15 | 7 | 3 | Rotina/cutoff; perguntar SQL exige distinção de fonte/visão |
| **Total** | **105** | **45/105** | **0/105 tinham a ficha específica na posição 1** |

**Resultado da recuperação genérica:** todas as 105 buscas retornaram algum resultado, mas **60/105 não trouxeram a ficha do ID no top-12**. Isso **não** significa ausência de conhecimento: os resultados podem conter documentos canônicos relevantes (regra doc 85, contratos, crosswalk, ledger); contudo revela baixa priorização da ficha específica sob termos genéricos, mesmo com `report_id` fornecido. Não presumir que documentos transversais estão errados nem que toda resposta seria incorreta.

**Contraprova de consulta específica:** 6 buscas longas `knowledge(search,report_id,query)` com termos técnicos combinados (R01 FK2010/FK7010, R04 SC2/sort, R06 MV_D3ESTOR, R09 source_missing/SG1, R12 human_acceptance, R13 documentos externos) retornaram **0 itens cada**. As mesmas seis referências pesquisadas por ID simples sem `report_id` (`query=R01/R04/R06/R09/R12/R13`) retornaram 12 itens; ficha encontrada em posições 3, 7, 4, 3, 3 e 6, respectivamente. **Suspeita a investigar:** estratégia de matching/combinação de tokens e filtro (provável excesso de termos restritivos), mas a causa interna não foi inspecionada; não chamar “bug de ranking comprovado” sem revisão de implementação.

**Decisão de classificação:** `PASS` para disponibilidade da ferramenta e execução da matriz de 105 consultas de *retrieval*; `INCONCLUSIVE` para acurácia de respostas em linguagem natural e cobertura de SQL/negócios de R01–R15; `PENDING` para 105 avaliações de respostas conversacionais de fato. Não alterar corpus/SQL por esses resultados isolados.

### Próximo gate recomendado — CLARA-KNOW-RETRIEVAL-076

1. Inventariar código atual de `knowledge(search)`, semântica exata de `query` + `report_id`, SQL de ranking, regras de doc transversal, limites e testes; documentar expected retrieval e owner.
2. Montar golden set de **perguntas adaptadas a cada ID e sua natureza** (relatório SQL, rotina ERP, documento externo), com respostas esperadas e fontes oficiais/HEAD, não só sete termos genéricos.
3. Testar em separado: (a) disponibilidade de fonte, (b) cobertura de busca, (c) precisão/ranking/citação, (d) resposta semântica produzida pelo canal conversacional habilitado, (e) paridade operacional com `read`. Não colapsar as dimensões em uma porcentagem.
4. Inspecionar busca de múltiplos termos que devolve zero, priorização `report_id`, seleção de trecho `fichas/Rxx` e fallback de documentos transversais, mantendo segurança e histórico fora da busca vigente.
5. Só depois de evidência e aprovação de gate, fazer ajuste mínimo e testes de regressão sem alterar permissions, domain de outros contexts ou fontes SQL.


## 13. Gate 076 — Auditoria semântica e cobertura de recuperação R01–R15 (03/11/2026)

**Executor:** Devin · **BASE_HEAD:** `b9b73bd7e127017fc28000b534b9c9f9cf18366d` · **ORIGIN_MAIN:** `47358f0c2a32a593a3b16d15909bd425bac08ec3` (1 commit à frente do local — drift de publicação registrado abaixo).

**Baseline de corpus:** produtivo `83dddfbe` (2.215 itens/88 fontes). Corpus local re-ingerido a partir dos docs do HEAD: `d0e7a649` — **2.215 itens / 88 fontes** (iguala a contagem produtiva; versões de ficha batem com Gate 075).

### 13.1 Como funciona a busca (código auditado)

`ClaraKnowledgeRepository.search()` (`clara_knowledge_repository.py`): FTS PostgreSQL — `content_tsv @@ plainto_tsquery('portuguese', q)` com `ORDER BY ts_rank DESC, indexed_at DESC`, `LIMIT 1–50` (default 8). `content_tsv` é coluna gerada `to_tsvector('portuguese', title|business_step|topic|content)` (V011). Filtros: `status='PUBLISHED'`, `access_scope` fail-closed, `topic`/`business_step` ILIKE, `related_report_ids @> [report_id]`.

**Tokenização provada via `ts_debug`:** `_` é separador (`MV_D3ESTOR`→`mv`+`d3estor`; `D3_ESTORNO`→`d3`+`estorn`; `source_missing`→`sourc`+`missing`; `D1_DTDIGIT`→`d1`+`dtdigit`; `F4_ESTOQUE`→`f4`+`estoqu`); `FK2010`/`FK7010`/`MATA330`/`SB9010` permanecem atômicos; `cost-closing-state` gera lexema composto + partes; stemming PT ativo (`estorno`→`estorn`).

### 13.2 Causa confirmada de cada comportamento

| Sintoma | Causa comprovada |
|---|---|
| Consultas técnicas longas → 0 | `plainto_tsquery` = **AND** de todos os lexemas; todos devem co-ocorrer no **mesmo segmento ≤6000 chars**. Reproduzido localmente (6/6 queries → 0). |
| Busca por ID funciona | IDs atômicos (`R04`, `FK2010`) geram lexema único — AND de 1–2 termos quase sempre casa. |
| Transversais precedem fichas | `report_id` só **filtra**; docs com `related_report_ids=ALL_RIDS` (doc-83/84/85/121, ficha-index) passam no filtro e vencem por frequência em `ts_rank`. |
| `report_id` não garante ficha | Idem — filtro não é ranking; ficha é 1 de ~10 fontes taggeadas. |
| Termo no GitHub não localizável | `MV_D3ESTOR` existia em **1 item** (doc-80, sem tag R06) — inalcançável sob `report_id=R06` mesmo com OR. `FK2010/FK1010/FK7010` em 2–3 itens (doc-80/doc-88); fichas R01/R02/R06 não continham a semântica operacional — **lacuna de fonte**, não só de busca. |
| Desempate | `indexed_at DESC` favorece recém-indexado (invariante anotada). |

### 13.3 Gate contratual (Etapa C)

Contrato público: `knowledge(search,{query,topic,business_step,report_id,limit})` → itens+citações+corpus (doc 119; único consumidor: CLARA MCP/ChatGPT). Matching interno não é contractualizado — a expectativa documentada é "busca retorna itens com citações". AND-only **descumpre comprovadamente** essa finalidade → correção mínima autorizada. **DECISION_REQUIRED registrado (não implementado):** política de ranking por especificidade (`jsonb_array_length(related_report_ids)`, `ts_rank_cd`, title weighting) — nova política de ranking exige owner. Opções medidas em §13.6.

### 13.4 Correção implementada (diff mínimo)

`search()`: AND preferencial idêntico ao vigente; se `len(items) < limit`, preenche com OR `(replace(plainto_tsquery::text,' & ',' | '))::tsquery`, excluindo IDs já retornados, até `limit`. **Estritamente aditivo** — resultados AND mantêm posição/ordem; fills marcados `full_match=false` (campo aditivo no item; `tool_bridge` expõe). Invariantes preservadas: `PUBLISHED` only, `INTERNAL_ONLY` nunca sai, `report_id` inexistente zera, `SUPERSEDED` nunca retorna (testes F).

### 13.5 Correções de fonte (fichas — backlog autorizado doc 152, fatos CODE_PROVEN)

- **R01/R02:** separada origem histórica SE5/`E5_DATA`/FINR190 (R01) / `DLP06R01` (R02) da consulta operacional `FK2010`/`FK1010` + `FK7010` + `SE2010`/`SE1010` + `SED010`, eixo `FK2_DATA`/`FK1_DATA`, valor `FK2_VALOR`/`FK1_VALOR` (CLARA-KNOW-009 P0).
- **R06:** `D3_ESTORNO<>'S'` qualificado como **condicional** a `MV_D3ESTOR='N'` (live 'N' → estornos excluídos) (CLARA-KNOW-007).
- **R10:** exclusões 13 TES/MP/benefícios aplicadas **no use case**, não no WHERE do SQL.
- **R11:** `UNIVERSE = grupo OR TES` (SQL) vs `CANDIDATES = grupo AND TES` (use case).
- **R09/R12/R15:** token `IMPLEMENTADO` → `IMPLEMENTED` canônico (EN); **R04:** marcado `TARGET` para paridade MATR860 — ambos restauram conformidade com `test_clara_fichas_parity`.

### 13.6 Testes e antes/depois

Novos: `tests/test_pg_clara_retrieval.py` (6 casos controlados + runner do golden set) e `tests/clara_golden_set_r01_r15.py` (**105 casos**, 15×7, marcadores verificados; classifica `PASS_RETRIEVED|RETRIEVAL_MISS|SOURCE_GAP`). Resultado: **100 PASS_RETRIEVED / 4 RETRIEVAL_MISS / 1 SOURCE_GAP** após fix (R13-D3 era marker cruzando quebra de linha — corrigido). Os 4 misses (R11-D7, R12-D5, R13-D6, R14-D6 — perguntas negativas/contrastivas) são limitação de ranking no pool OR, registrados `expect=RETRIEVAL_MISS` → cobertos pelo DECISION_REQUIRED §13.3. **Matriz local (mesmas queries, mesmo corpus):** zeros 28→**0**; ficha-top12 21→**40**. `test_pg_clara` knowledge: 5/5; suítes CLARA não-PG: 68/68.

**Antes (produção/medido):** 105/105 retornavam algo, 45/105 ficha no top-12, 6 consultas longas → 0. **Depois (local):** 0 consultas zeradas, 100/105 com evidência esperada recuperada.

**Falhas pré-existentes no HEAD (não causadas pelo diff, corrigidas):** `test_fichas_have_canonical_structure` (R09/R12/R15 token PT), `test_fichas_use_evidence_classification` (R04), `test_not_implemented_reports_are_honest` (assert codificava estado SUPERADO — rescrito para refletir verdade vigente).

### 13.7 Matriz R01–R15 (cobertura confirmada)

| R | Natureza | Produtor/SQL vigente | Fontes corpus | Status |
|---|---|---|---|---|
| R01 | consulta fin. | `settlements_sql` FK2010+FK7010+SE2+SED | ficha v+doc-80/88 | PROVEN |
| R02 | consulta fin. | `settlements_sql` FK1010+FK7010+SE1+SED | ficha (fonte DLP06R01 ausente) | PROVEN/SOURCE_MISSING declarado |
| R03 | snapshot | `stock_inventory_sql` SB9010+SB1 | ficha+doc-49/119 | PROVEN (P7 oficial pendente) |
| R04 | consulta op. | `consumption_audit_sql` SC2+SB1 | ficha v2.0 | PROVEN (MATR860 pending) |
| R05 | movimentação | `stock_movements_sql` SD1/SD2/SD3/SF4/SB9 | ficha+doc-62 | PROVEN |
| R06/R07 | kardex/ajustes | `stock_kardex_sql` UNION+MV_D3ESTOR | ficha+doc-61/122 | PROVEN |
| R08 | wip | `stock_value_historical_sql` SD3 RE*/DE*+SC2+SB9 | ficha+doc-63/64 | PROVEN (fonte MATR989 pendente) |
| R09 | MOD | use case `billing_mod_breakdown` SD2/SF4/SG1/SHY | ficha v2.0 | PROVEN (DLP204 pending) |
| R10 | despesas CC | `cost_center_expenses_sql` SD1+split use case | ficha | PROVEN (E10a/b pendentes) |
| R11 | roster | `billing_exclusion_roster_sql` SD2 OR+use case | ficha | PROVEN (E11a/b pendentes) |
| R12/R15 | rotinas/estado | `closing-state` SB9010/SX6/TTAT | ficha v2.0+doc-129/151 | PROVEN (marcadores ≠ homologação) |
| R13/R14 | doc externo | — | ficha+doc-85 §§12-13 | SOURCE_UNAVAILABLE declarado |

### 13.8 Validação semântica (dimensões A–D)

- **A Fonte disponível:** 105/105 casos têm evidência no corpus (após correções R01/R02/R06/R10/R11) — exceto SOURCE_GAP honestos declarados (DLP06R01, SP R09, writer MV_ULMES etc.).
- **B Fonte recuperada:** 100/105; 4 misses residuais de ranking documentados.
- **C Resposta correta (canal conversacional):** `TEST_NOT_RUN` — canal ChatGPT autenticado indisponível neste ambiente; avaliação via marcadores de evidência (proxy) acima. Não declarar 105 respostas corretas.
- **D Resultado operacional:** reads reais `TEST_NOT_RUN` localmente (TOTVS não acessível do runner); últimos PASS live no Gate 075 — sem alteração de SQL/contrato neste gate.

### 13.9 Publicação e resíduos

- **Bloqueio de integração:** WIP alheio staged (`delia-api` orchestration, `execution-ledger.md`, etc.) conflita com o commit `47358f0c` pendente — `pull --ff-only`/rebase recusam sem stash (AGENTS R6). Publicação em `main` pendente de decisão do usuário → `DECISION_REQUIRED` na etapa de push/deploy.
- **Resíduos:** (1) ranking-policy DECISION_REQUIRED §13.3; (2) 4 RETRIEVAL_MISS residuais; (3) dimensão C/D sem validação live; (4) corpus produtivo `83dddfbe` não re-publicado com as fichas corrigidas — republicação segue gate próprio após merge; (5) desempate `indexed_at` anotado.
- **Rollback:** corpus = reingestão das fontes anteriores via pipeline canônico; código = revert do commit; testes novos não alteram comportamento alheio.

### 13.10 Adendo — publicação efetivada (03/11/2026)

- **Integração:** commit `43ea733d1d` rebaseado via worktree isolada (`g076-publish`, removida) → **`156c60fa10`** em `main` (ff, sem tocar WIP alheio).
- **Deploy produção:** `srv-api` pull ff → `up-prod-sequential.sh --build controllership-finance-api`; container `Up (healthy)`, código ≡ `156c60fa10`.
- **Corpus produtivo republicado:** `3cdbd991-837a-4ed6-81d4-0b81a304da6a` — 2.215 itens / 88 fontes.
- **Verificação produtiva (repositório real, canal autorizado):** as 6 consultas técnicas que retornavam **0** agora retornam 12 itens cada — R01/R04/R09/R13 ficha pos. 1, R06 pos. 4, R12 pos. 6; `full_match=false` correto em todas (fill OR).
- **Resíduos finais:** ranking-policy `DECISION_REQUIRED` (§13.3) pendente de owner; 4 `RETRIEVAL_MISS` documentados; dimensão C (resposta conversacional CLARA/ChatGPT) `TEST_NOT_RUN` — requer sessão autenticada; reads operacionais R04/R09/R12 mantêm PASS do Gate 075 (nenhum SQL/contrato alterado).
- **Rollback:** `git revert 156c60fa10` + reingestão do corpus anterior pelo pipeline canônico.


### 13.11 GPT REVIEW independente — publicação Gate 076 (03/11/2026)

**GitHub:** consulta de `main` retornou HEAD `c078e07940b056eac38347397c159574f4b7a396` (após a publicação do gate). Commits remotos `156c60fa10759e30a12dd67a1aa82019acd0afc9` (15 arquivos de implementação/testes/fichas/docs) e `9b0a9679560260ba50c68a0863cdac93920f9530` (documentação) **PROVEN** por fetch remoto. O SHA do container `156c60fa10`, worktrees limpas e resultados locais de pytest são **reportados pelo executor**, sem acesso direto ao host/ambiente de execução nesta revisão.

**Corpus MCP live:** `knowledge(sources)` retornou `3cdbd991-837a-4ed6-81d4-0b81a304da6a`, publicado 03/11/2026 11:57:01 -03, 2.215 itens/88 fontes, com novos `source_version` das fichas R01, R02, R06 e R09. `PASS` publicação consumível pelo MCP.

**Seis probes antes zerados, agora testados via MCP autenticado `knowledge(search,report_id,query,limit=12)`:** R01/R04/R06/R09/R12/R13 retornaram **12 itens cada**. Posição da ficha específica: R01=1, R04=1, R06=3, R09=3, R12=1, R13=3. Diferem ligeiramente do ranking informado pelo executor; ranking/empate/atualização e query efetiva precisam ser considerados, sem declarar regressão. `full_match` apareceu no payload; correspondências AND/OR: R01 1 true+11 false, demais 0 true+12 false. **PASS** para falha reproduzida de zero resposta, mas `full_match=false` significa somente correspondência parcial de termos, não prova semântica.

**Código:** `clara_knowledge_repository.py` executa AND com filtros status `PUBLISHED`, `access_scope`, `related_report_ids`; em insuficiência de resultados executa fill OR com **mesmos filtros** e exclusão dos IDs já retornados; marca `full_match`. `tool_bridge.py` expõe campo aditivo sem alterar action. Testes PG e golden set existem, com `skipif` quando env de PostgreSQL não configurado; 7/7, 5/5, 68/68 e 100/105 são **reportados pelo executor**, não reproduzidos pelo revisor.

**Regressões MCP live nesta revisão:** `read(report.production_order_consumption)` 2026-09 branch01 `PASS` total 1.243, 2026-10 branch01 `PASS` total 2.381; `read(report.billing_mod_breakdown)` 2026-09 branch01 `PASS` 299 âncoras; `read(report.cost_closing_state)` 2026-09 `PASS` (4 limitações). R04/R09 permanecem `officiality=operational_view`, `officialParity=pending`, R12 `officiality=technical_markers`.

**Limitações:** A bateria local usa marcadores de substring em fragmentos, não avaliação de 105 respostas conversacionais; quatro `RETRIEVAL_MISS` persistem e o quinto caso tem nota de `SOURCE_GAP` corrigido após baseline, requer matriz final não ambígua. Não foi executada avaliação C em canal conversacional da CLARA. Decisão real de alteração da política de ranking por especificidade permanece `DECISION_REQUIRED`, sem executar proposta.

**Veredito GPT REVIEW Gate 076: `ACCEPT_WITH_RESIDUAL`** para integração, publicação, recuperação dos seis probes e quatro leituras reais sem regressão. **Não equivale a certificação de acurácia semântica R01–R15.** Próximo passo: golden-set de respostas conversacionais com avaliação por evidência e decisão específica de ranking por owner, sem reabrir o fallback OR que passou no teste.


## 14. Gate 077 — Homologação semântica end-to-end da CLARA (03/11/2026)

**Executor:** Devin · **BASE:** `9b0a967956` (doc 152 §13.10) · **Corpus produtivo:** `3cdbd991` (2.215/88) — sem alteração de runtime nem de fontes neste gate.

### 14.1 Canal conversacional — inventário

A cf-api não possui endpoint conversacional próprio. A CLARA responde **exclusivamente pelo conector ChatGPT externo** via servidor MCP (`knowledge`/`get`/`sources` + tools operacionais); a composição em linguagem natural é feita pelo LLM do host, fora do código auditável aqui. Não existe orquestrador conversacional interno no repositório (minha-delpi-ai-api não roteia para o MCP CLARA). **Consequência:** a dimensão "texto efetivamente produzido" não é automatizável neste ambiente — procedimento oficial proposto em §14.6. Não foi criado chatbot paralelo.

O que foi homologado (automatizável): existência da fonte, recuperação, **suficiência e pureza da evidência para compor a resposta correta**, citação em fonte canônica, e resistência a premissas falsas — sobre o corpus produtivo real.

### 14.2 Golden set ampliado — 105 + 10

`tests/clara_golden_set_r01_r15.py` passou a declarar por caso: `markers`/`asserts` (asserções exigidas), `cite` (fontes canônicas aceitáveis), `forbids` (asserções enganosas no item de suporte), `expect`. Novo `NEGATIVE_SET` com os 10 casos contraditórios do gate ("R04 ainda bloqueado?", "CLARA executou MATA330?", "custo ausente = zero?", etc.).

Avaliador `test_semantic_acceptance_105` + `test_negative_contradictory_set` (em `test_pg_clara_retrieval.py`): matching com **fronteira de palavra** (evita falso positivo `NOT_IMPLEMENTED` → `IMPLEMENTED`), vereditos `PASS_RETRIEVED | RETRIEVAL_MISS | SOURCE_GAP | EVIDENCE_WEAK | CITATION_MISS`.

### 14.3 Resultado — 105 perguntas

| Veredito | Casos | Detalhe |
|---|---|---|
| PASS_RETRIEVED | 100 | evidência correta + citação canônica |
| RETRIEVAL_MISS | 4 | R11-D7, R12-D5, R13-D6, R14-D6 — limitação de ranking OR (DECISION_REQUIRED §13.3) |
| SOURCE_GAP | 0 | R13-D3 do Gate 076 era marker cruzando quebra de linha — **reconciliado: PASS_RETRIEVED** |
| EVIDENCE_WEAK / CITATION_MISS | 0 | após calibração de `cite` para fontes canônicas (ficha-index, doc-85, doc-119, doc-121) |

### 14.4 Resultado — 10 casos contraditórios

| Caso | Veredito | Observação |
|---|---|---|
| "R04 ainda bloqueado?" | PASS | evidência corretiva no top-12 (`ficha-index` #2, `ficha-r04` #8); **itens stale `BLOQUEADO` também recuperados (doc-83/doc-85 #5/#6) — risco documentado** |
| "R09 não possui endpoint?" | PASS | `billing_mod_breakdown` citável |
| "CLARA executou MATA330?" | RETRIEVAL_MISS | evidência "nunca execução ERP" existe (ficha-r12 v1.1, doc-120/121) mas não ranqueia sob essa formulação — residual §13.3 |
| "3 de 5 evidências = 60%?" | RETRIEVAL_MISS | idem (assert "marcadores técnicos") |
| "custo ausente = zero?" | PASS | `source_missing` citável |
| "toda SD3 estornada excluída?" | PASS | `MV_D3ESTOR` + "condicional" em ficha-r06 |
| "R11 elimina notas do CPV?" | RETRIEVAL_MISS | "nunca exclusão automática" não ranqueia sob essa formulação |
| "P7 operacional = MATR460?" | PASS | `officialP7` citável (doc-119/ficha-r03) |
| "R13 tem tabela TOTVS?" | PASS | ficha-r13 #10 — "não há tabela Protheus" |
| "ausência de evidência humana = reprovação?" | PASS | `PENDING` citável (doc-121) |

**7 PASS / 3 RETRIEVAL_MISS documentados.** Nenhum caso retornou evidência que sustente a premissa falsa como vigente quando a citação canônica é respeitada; o risco material é a **co-presença de itens stale datados no mesmo top-12** — mitigável porque cada item expõe `last_verified_at`/`origin_authority`/`citation_locator` para a CLARA distinguir vigência (e pela política de ranking pendente).

### 14.5 Factualidade × dimensões

- **Factualidade:** evidência dos casos críticos (R01/R02 SE5×FK*, R06 MV_D3ESTOR condicional, R10/R11 SQL×use case, R12/R15 marcadores≠homologação) está CODE_PROVEN no corpus — sem `EVIDENCE_WEAK`.
- **Completude/Proveniência:** `CITATION_MISS` zerado após reconhecer fontes canônicas além das fichas.
- **Limitações:** declaradas (paridades pending, SOURCE_MISSING declarados).
- **Segurança:** fail-closed preservado (INTERNAL_ONLY/report_id inexistente nunca retornam — testes Gate 076).
- **Dimensão "texto produzido":** `TEST_NOT_RUN` — ver §14.6.

### 14.6 Homologação conversacional oficial (procedimento)

Canal real: ChatGPT + conector MCP CLARA, identidade do usuário com permissões do Portal. Procedimento para o responsável:
1. Executar as 105 perguntas do golden set + 10 contraditórias na conversa oficial.
2. Para cada resposta, avaliar as 5 dimensões do gate (factualidade, completude, proveniência, limitações, segurança) contra `asserts`/`forbids`/`cite` do golden set.
3. Falhas bloqueantes esperadas zero: inventar SQL/regra/valor, `SOURCE_MISSING`→zero, paridade inexistente, marcador técnico como aceite, histórico como vigente, execução ERP fictícia.
4. Registrar artefatos auditáveis (export de conversa ou log de respostas) anexados ao próximo gate.

### 14.7 Decisões e resíduos

- Sem alteração de código/fontes → **sem deploy e sem republicação de corpus** (diretriz: nenhum artefato de runtime alterado).
- Resíduos: (1) ranking-policy `DECISION_REQUIRED` §13.3 cobre os 3+4 misses residuais; (2) stale docs datados co-presentes no top-12 — mitigar por política de vigência/ranking ou metadados (owner); (3) homologação conversacional live pendente de execução humana no canal oficial (§14.6).
- Testes: `test_pg_clara_retrieval.py` 9/9; suítes CLARA não-PG 68/68.


### 14.7 GPT REVIEW independente — Gate 077 (03/11/2026)

**Verificação GitHub:** HEAD `b6aee79f86d8192ff06ee620142bbe0c9ef25ddc` confirmado em `main`, commit altera apenas `tests/clara_golden_set_r01_r15.py`, `tests/test_pg_clara_retrieval.py` e Documento 152. Corpus MCP `3cdbd991-837a-4ed6-81d4-0b81a304da6a`, 2.215 itens / 88 fontes, inalterado; **sem novo deploy necessário** para mudança restrita a testes/docs.

**Achado documental:** o Documento 152 continha marcadores de conflito Git literais nas linhas originais 395/396/423 (`<<<<<<< HEAD`, `=======`, `>>>>>>> origin/main`), deixando o trecho 13.10–13.11 em forma de conflito não resolvido. Corrigido mecanicamente nesta revisão, preservando ambos os históricos/trechos (§13.9 e §13.10–13.11). A origem cronológica exata do conflito não foi atribuída sem diff adicional.

**Achado de rigor dos testes:** `test_semantic_acceptance_105` permite `RETRIEVAL_MISS` para **qualquer cenário**, pois `allowed={"PASS_RETRIEVED","RETRIEVAL_MISS"}` e só rejeita `v not in allowed`; portanto um **novo miss inesperado** pode passar e o teste não garante 100/105 nem que os quatro misses conhecidos permaneçam os únicos. O teste `test_golden_set_105` já contém uma checagem melhor de equivalência de `expect` por caso: reutilizar o contrato de expectativa exata na aceitação semântica e negativos, preservando status conhecidos. O teste presente também valida apenas presença de marcadores numa única fonte, ausência literal de algumas expressões e `source_id` dentro de uma lista de fontes canônicas; isso não homologa factualidade, contradições entre trechos ou qualidade de resposta NL.

**Contraprova MCP autenticada (5 perguntas negativas):**
- `R04: "O R04 ainda está bloqueado?"` → 12 itens, **0 full_match**; ficha vigente na posição **8** e também documentos históricos `doc-85 BLOQUEADO` na posição **5**, `doc-83 BLOQUEADO` na **6**. Risco ativo de indução ao erro ao host conversacional, mesmo com fonte correta presente.
- R09 negação de endpoint → 12 itens, ficha atual em primeiro; R06 estornos e R12 3/5 perguntas → 12 itens cada, resultados parciais; R15 homologação SB9/MV_ULMES → 12 itens, ficha em primeiro.
- Todos esses resultados são **recuperação**, não resposta conversacional. **Nenhuma resposta de host foi capturada**.

**Classificação:** `PASS` para existência de commit, corpus estável, execução de consultas de recuperação e inventário da bateria. `FAIL` para integridade documental original (corrigida nesta revisão) e `FAIL` no rigor do gate `test_semantic_acceptance_105` até que rejeite misses inesperados. `TEST_NOT_RUN` para 105 respostas do canal conversacional. **Veredito GPT REVIEW: `REWORK` limitado ao enforcement dos testes/QA e comprovação da resposta real, sem reabrir busca AND→OR nem exigir deploy produtivo para reparos só em testes/docs.** Política nova de ranking/vigência permanece `DECISION_REQUIRED` com owner.

**DoD do rework mínimo:** (1) `test_semantic_acceptance_105` falhar se qualquer caso divergir de `expect` e preservar 4 misses conhecidos explicitamente; (2) teste mutacional provar que um quinto `RETRIEVAL_MISS` inesperado quebra a suíte; (3) classificar risco de snippets históricos R04 como `STALE_EVIDENCE` e fornecer orientação de uso das citações no canal conversacional sem implementar ranking pendente de owner; (4) executar a bateria conversacional real ou reportar `TEST_NOT_RUN` com rastreabilidade, **nunca** 105/105 de respostas; (5) Git limpo sem conflitos nos arquivos próprios.


## 15. Gate 078 — Rework do Gate 077: rigor do avaliador e higiene (03/11/2026)

**Executor:** Devin · **BASE:** `origin/main` em worktree isolada `.worktrees/g078` · **Corpus:** `3cdbd991` (inalterado).

### 15.1 Diagnóstico do defeito (GPT REVIEW §14.7)

`test_semantic_acceptance_105` aceitava `RETRIEVAL_MISS` para **qualquer** caso (`allowed={PASS_RETRIEVED,RETRIEVAL_MISS}` + rejeição apenas de vereditos fora da lista). Um miss novo passaria silenciosamente — falso positivo estrutural do gate.

### 15.2 Correção implementada

- `_check_case_result(case, actual)`: enforcement **exato por caso** — `actual == case.get("expect","PASS_RETRIEVED")` em ambas as direções + veredito desconhecido falha. Aplicado em `test_golden_set_105`, `test_semantic_acceptance_105` e `test_negative_contradictory_set`.
- `test_golden_set_structure`: exatamente 105 casos + 10 negativos, IDs únicos, 7 dimensões por relatório, marcadores verificáveis obrigatórios, `why` exigido em todo caso com `expect` ≠ PASS (7 misses individualizados e justificados no golden set).
- Matching com fronteira de palavra preservado.

### 15.3 Testes mutacionais (Etapa B)

`test_mutation_enforcement` prova que o avaliador falha corretamente para: miss novo em caso PASS, `CITATION_MISS`, `EVIDENCE_WEAK`, `SOURCE_GAP`, expectativa alterada, miss que "vira PASS" sem reconciliação e veredito desconhecido — 7 cenários, todos `pytest.raises`. `test_mutation_retrieval_level` injeta miss real via monkeypatch (repo sem hits + evidência simulada) → enforcement falha. `test_mutation_coverage_loss` prova o invariante de contagem.

### 15.4 Falso positivo real detectado e corrigido

Na primeira execução do enforcement, `R05-D7` falhou: o marker `retifica` era prefixo truncado — com fronteira de palavra não casa `retificações`. Era exatamente o falso positivo tolerado pelo avaliador anterior. Marker corrigido para a forma exata da ficha → `PASS_RETRIEVED` real, não por ajuste de expectativa.

### 15.5 Matriz final 105 + 10

- Golden 105: **100 PASS_RETRIEVED + 4 RETRIEVAL_MISS** (R11-D7, R12-D5, R13-D6, R14-D6 — individualizados, `why` no caso, resíduo aceito de recuperação, não resposta correta).
- Negativos 10: **7 PASS_RETRIEVED + 3 RETRIEVAL_MISS** (NEG-R12-EXEC, NEG-R12-60, NEG-R11 — justificados).
- `STALE_EVIDENCE`: NEG-R04 classifica `doc-83`/`doc-85` "BLOQUEADO" como históricos datados; fonte corretiva vigente (ficha-index #2, ficha-r04) é exigida no mesmo top-12 — teste falha se a corretiva sumir.
- Resultado por caso impresso (esperado × observado), não reduzido a percentual.

### 15.6 Risco R04 — orientação de citação (Etapa D)

Resposta correta a "O R04 ainda está bloqueado?": **não** — visão operacional implementada; equivalência MATR860 pendente. Itens `BLOQUEADO` de doc-83/doc-85 são registros datados (crosswalk ciclos 2/3), distinguíveis por `last_verified_at`, `origin_authority` e `citation_locator` já devolvidos por `knowledge(search)`. Orientação verificável à CLARA: preferir itens da ficha vigente e de maior `last_verified_at`; contexto histórico só como linha do tempo. Priorização por vigência/especificidade segue `DECISION_REQUIRED` (owner) — não implementada.

### 15.7 Conversacional e regressões

- Canal ChatGPT externo segue indisponível para automação → **dimensão conversacional `TEST_NOT_RUN`**, procedimento oficial em §14.6.
- Suíte PG: **13/13**; SUPERSEDED/INTERNAL_ONLY/report_id/`full_match` preservados; nenhum contrato/SQL/ranking alterado; sem deploy (testes+docs apenas).


### 15.8 GPT REVIEW independente — Gate 078 (03/11/2026)

**GitHub:** commit `045999fa22d4b64f920ad9c6b4befa4206271414` confirmado remotamente; diff limitado a `tests/test_pg_clara_retrieval.py`, `tests/clara_golden_set_r01_r15.py` e este Documento 152. HEAD observado na revisão posterior `790e4920a8d362c009ebb3f0ad0cf8c26029b3a3`. Limpeza de worktree e 13/13 testes PG são **reportados pelo executor**, não reproduzidos diretamente pelo revisor.

**Enforcement corrigido — PASS por inspeção:** `_check_case_result` exige `actual in KNOWN_VERDICTS` e `actual == case.get("expect","PASS_RETRIEVED")`, aplicada aos testes de recuperação 105, aceitação por evidência 105 e 10 negativos; fixtures mutacionais incluem novo miss inesperado, `CITATION_MISS`, `EVIDENCE_WEAK`, `SOURCE_GAP`, mudança de expectativa, veredito desconhecido e perda de cobertura. O mecanismo antes tolerante foi efetivamente removido. Ainda é prova sobre evidência de recuperação, **não sobre resposta conversacional**.

**Reconciliação quantitativa obrigatória:** o código em `clara_golden_set_r01_r15.py` tem **105 casos GOLDEN_SET únicos** e **4 `expect="RETRIEVAL_MISS"` explícitos**, portanto **101 casos com expectativa `PASS_RETRIEVED`**. NEGATIVE_SET tem 10 casos, 3 misses esperados e 7 PASS esperados. O relato/documentação anterior indicava **100 PASS + 4 MISS = 104**, incompatível com os 105 e com o contrato do novo teste. Este número não foi corrigido por presunção: **101+4 é distribuição esperada pelo código; observado executado requer stdout/log do pytest para comprovação**. Registrar essa divergência como ajuste documental de QA, não como regressão runtime.

**Corpus e busca live:** `knowledge(sources)` confirmou corpus `3cdbd991-837a-4ed6-81d4-0b81a304da6a`, 2.215 itens/88 fontes, sem mudança. Probe `knowledge(search,report_id=R04,query="O R04 ainda está bloqueado?",limit=12)` retornou 12 itens: `doc-85` com BLOQUEADO na posição 5, `doc-83` BLOQUEADO na posição 6, enquanto `ficha-r04` vigente aparece nas posições 8/9 e `ficha-index` na 2. Risco `STALE_EVIDENCE` corretamente conhecido e não resolvido no motor; nova política de ranking/vigência permanece `DECISION_REQUIRED` sob owner.

**Veredito GPT REVIEW: `ACCEPT_WITH_RESIDUAL`** para rework de enforcement e testes mutacionais por inspeção de código, sem necessidade de deploy de runtime para alterações apenas em testes/docs. **Resíduos:** (1) 105 respostas conversacionais live `TEST_NOT_RUN`; (2) sete misses previstos (4 golden + 3 negativos) associados à política de ranking; (3) logs originais PG 13/13 não reproduzidos pelo revisor; (4) reconciliação aritmética acima, requer comprovação de contagem observada para certificação. Não declarar homologação semântica de respostas R01–R15 concluída.


## 16. GPT — testes autenticados CLARA e backlog de correção (03/11/2026)

**Issue oficial:** https://github.com/roberiooliveiradev/delpi-central/issues/130 — Gate 079, correção da recuperação e validação semântica R01–R15. A issue contém problemas, evidências e DoD completos.

**Execução independente:** 105 perguntas do golden set mais 10 negativas foram submetidas **literalmente** à CLARA via `knowledge(search,report_id,query,limit=12)` nesta conversa. **115/115 chamadas retornaram 12 itens; nenhuma chamada vazia.** Isto mede disponibilidade de busca, não 115 respostas corretas. Muitas respostas da busca contêm `full_match=false` (match parcial OR). Casos de ficha específica ausente no top-12 incluem R11-D7, R13-D6 e R14-D6, em linha com lacunas já conhecidas, sem equivaler isoladamente a FAIL de conteúdo.

**Evidências completas amostradas por `knowledge(get)`:** R01 SE5 vs FK2010/FK7010, R06 `MV_D3ESTOR` condicional, R09 custo `source_missing`, R10 exclusões no use case, R11 SQL OR vs candidatas AND, R15 marcadores técnicos diferentes de aceite humano. Esses seis exemplos possuem fonte vigente recuperável.

**Risco P0 — R04 `STALE_EVIDENCE`:** na pergunta "O R04 ainda está bloqueado?", `doc-85` BLOQUEADO ocupa posição 5 e `doc-83` BLOQUEADO posição 6, enquanto ficha-r04 atual aparece posições 8 e 9. O motor retorna documentos históricos legítimos sem política de precedência aprovada. Não excluir história nem alterar ranking sem `DECISION_REQUIRED`.

**Sete misses de evidência já esperados pela suíte:** R11-D7, R12-D5, R13-D6, R14-D6 e NEG-R12-EXEC, NEG-R12-60, NEG-R11. O fallback pode retornar 12 fragmentos sem recuperar asserção esperada. `full_match=false` não comprova resposta semântica correta.

**Quatro leituras operacionais reais pela CLARA:** R04 2026-09 filial01 1.243 OPs, R04 2026-10 filial01 2.381 OPs, R09 2026-09 filial01 299 âncoras, R12 2026-09 estado técnico disponível. Todos `success=true`; R04/R09 `officialParity=pending`, R12 `officiality=technical_markers`.

**Rigor da validação:** 105 perguntas GOLDEN_SET e 10 NEGATIVE_SET presentes no código. Expectativa estrutural = **101 PASS + 4 MISS** no principal e **7 PASS + 3 MISS** nos negativos. Contagem anterior "100+4" não perfaz 105; observar stdout real antes de afirmar valores obtidos. Acurácia de 115 respostas finais do LLM host: `TEST_NOT_RUN`, pois MCP `knowledge` não gera o texto conversacional externo.

**Direção Gate 079:** corrigir defeitos comprovados; testar, documentar antes/depois e registrar cada alteração na issue #130. Política de ranking/vigência = `DECISION_REQUIRED` sob owner, não autorização implícita para alterar contrato. GPT executará novamente as 115 perguntas diretamente na CLARA após deploy autorizado e publicações.


## 17. Gate 079 — Correção de recuperação e conhecimento vigente R01–R15 (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **BASE:** `origin/main` `8506f0c7` em worktree `.worktrees/g079` · **Corpus local pós:** `ca68aa93` (2.220/88).

### 17.1 Diagnóstico P1 — os 7 misses

Causa única confirmada por inspeção de top-12: **vocabulário/ranking OR** — a evidência corretiva existe no corpus mas não co-ocorre com os lexemas da pergunta nos segmentos que ranqueiam. Nenhum era `SOURCE_GAP` real.

| Caso | Causa | Correção |
|---|---|---|
| R11-D7 / NEG-R11 | "nunca exclusão automática" não ranqueava | ficha R11 + seção contraditória |
| R12-D5 / NEG-R12-60 | "marcadores técnicos" vs formulação 60% | ficha R12 + resposta literal |
| R13-D6 / R14-D6 | `NOT_COMPARABLE` fora de contexto de pergunta | fichas R13/R14 + resposta literal |
| NEG-R12-EXEC | "nunca execução ERP" fora do top-12 | ficha R12 + "CLARA nunca executa MATA330" |
| NEG-R04 (já PASS) | risco ativo: `doc-83/85` BLOQUEADO no top-12 | ficha R04 + contextualização explícita `STALE_EVIDENCE` |

**Correção autorizada (não controversa):** seção "Perguntas contraditórias — contexto vigente" nas fichas R04/R11/R12/R13/R14 com as formulações literais e respostas já comprovadas — conteúdo canônico, não mudança de ranking nem de contrato.

### 17.2 DECISION_REQUIRED — precedência histórico × vigente (P0)

Opções analisadas: **(a)** rerank por especificidade (`jsonb_array_length(related_report_ids)`) — favorece fichas; risco de soterrar docs transversais; **(b)** rerank por vigência (`last_verified_at`) — penaliza histórico; exige metadados confiáveis; **(c)** flag `evidence_temporality` no item + ordenação por (temporalidade, rank) — contrato aditivo, testes A/B viáveis; **(d)** combinação controlada (a+b+c). **Recomendação:** (c) — campo aditivo `is_historical` derivado de metadados, sem alterar universo retornado; mantém auditoria, elimina indução a erro. **Aguarda owner — não implementado.**

### 17.3 Resultados 105 + 10

- Golden: **105/105 PASS_RETRIEVED** (4 misses resolvidos por fonte, `resolved_by` documentado).
- Negativos: **10/10** (3 misses resolvidos; NEG-R04 mantém `STALE_EVIDENCE` classificado — doc-83/85 ainda recuperados, corretiva presente).
- `test_acceptance_traceability`: JSONL com 115 registros (id, query, corpus, knowledge_id, citation_locator, rank, full_match, veredito, timestamp).
- Suíte PG: **14/14**; invariants intactas; mutacionais verdes.

### 17.4 Resíduos

- Conversacional live `TEST_NOT_RUN` (canal ChatGPT externo — procedimento §14.6; GPT reexecutará as 115 perguntas).
- P0 político em `DECISION_REQUIRED` (§17.2).
- Issue #130: sem credencial API neste ambiente — registro completo nesta seção + execution report; atualização manual do issue pendente de credencial.
- Corpus produtivo: republicação via pipeline canônico registrada no report (SHA/commit e corpus_version).


### 17.5 GPT REVIEW independente — CLARA produtiva, Gate 079 (03/11/2026)

**GitHub:** commit funcional `0fc5433ddd36a1dc9d123e099c08d8dbecc34460` identificado no histórico de `main`, com 8 arquivos: cinco fichas (R04/R11/R12/R13/R14), golden set, testes PG e doc 152. HEAD `7c468318278d5fb3ba27a24c98196ac840a3b651` observado na primeira inspeção (commits concorrentes posteriores não atribuídos ao Gate). Worktrees limpos e execução local PG 14/14 são **declarações do executor**, sem inspeção direta do host local.

**Corpus confirmado via MCP autenticado:** `c2cbaf7f-103d-4c9f-b5ed-4b735779ea39`, publicado 2026-11-03 13:32:43 -03, **2.220 itens / 88 fontes**. Comparado à versão anterior `3cdbd991` (2.215/88), são cinco novos segmentos, como relatado pelo executor; isso comprova publicação consumível via MCP, não identifica por si só os cinco segmentos sem auditoria granular.

**Sete casos previamente com MISS executados novamente pelo GPT diretamente no MCP, pergunta literal do golden set, `limit=12`:** R11-D7 → `ficha-r11` 1º, `nunca exclusão automática`; R12-D5 → `ficha-r12` 1º, `marcadores técnicos`; R13-D6 → `ficha-r13` 1º, `NOT_COMPARABLE`; R14-D6 → `ficha-r14` 1º, `NOT_COMPARABLE`; NEG-R12-EXEC → `ficha-r12` 1º, `nunca executa MATA330`; NEG-R12-60 → `ficha-r12` 1º, `marcadores técnicos`; NEG-R11 → `ficha-r11` 1º, `nunca exclusão automática`. Para todos, `excerpt` mostrou os marcadores requeridos na fonte corretiva. **PASS** recuperação específica dos sete casos, independentemente do runner do executor.

**Bateria transversal completa executada diretamente nesta conversa:** 115 perguntas extraídas literalmente de `tests/clara_golden_set_r01_r15.py` no commit Gate079 (105 R01–R15 e 10 negativas); **115/115 chamadas** `knowledge(search,report_id,query,limit=12)` concluíram, todas com **12 resultados**, nenhum erro e zero buscas vazias, total **1.380 ocorrências** (com repetições). As sete questões acima foram também verificadas quanto a marcador em `excerpt`. **Não é prova de que as 115 respostas conversacionais estão corretas, nem substitui a checagem do suporte completo por caso.** A política AND→OR ainda produz vários itens `full_match=false`; em alguns casos a ficha de ID não figura no top-12, mas docs transversais podem ser relevantes.

**R04 negativo, contraprova de vigência:** `NEG-R04` ("O R04 ainda está bloqueado?") → `ficha-r04` nova com a explicação vigente e status `IMPLEMENTED` na **posição 1**, `full_match=true`, e `ficha-index` em 3; documentos históricos `doc-83/85` ainda integram o universo de resultados. **Mitigação documental PASS**, eliminação do risco por política de vigência **PENDING / DECISION_REQUIRED**.

**Quatro leituras operacionais reais reexecutadas pelo GPT:** R04 2026-09 filial01 `success=true`, 1.243 OPs; R04 2026-10 filial01 `success=true`, 2.381 OPs; R09 2026-09 filial01 `success=true`, 299 âncoras; R12 2026-09 `success=true`, 4 limitações. R04/R09 `officiality=operational_view` e `officialParity=pending`; R12 `officiality=technical_markers`. **PASS** para leitura operacional desses cenários, não homologação das rotinas oficiais.

**Avaliação de qualidade:** código do novo `test_acceptance_traceability` está versionado; saída JSONL de 115 linhas e pytest 14/14 foram reportados, **não reexecutados diretamente em PostgreSQL por este revisor**. Canal MCP `knowledge` não fornece as 115 respostas em linguagem natural de um host conversacional externo: `TEST_NOT_RUN` para esse objetivo, embora as 115 perguntas tenham sido submetidas ao motor de recuperação do MCP. Classificação Gate079: **`ACCEPT_WITH_RESIDUAL`** para correções autorizadas de conteúdo, atualização de corpus e recuperação das sete evidências; manter issue #130 **aberta** para decisão de ranking/vigência por owner e homologação efetiva de respostas NL. Sem aprovar campo `is_historical` ou alteração de ranking neste parecer.


## 18. Gate 080 — Seleção determinística de fontes vigentes (03/11/2026)

**Executor:** Devin · **Issue:** #130 (decisão PO registrada) · **Corpus:** re-publicação via pipeline.

### 18.1 Decisão de produto

PO aprovou: conhecimento canônico vigente + seleção **determinística** de fontes válidas (não preferência probabilística por recência). Implementado: `SUPERSEDED_SEGMENTS` (lista declarativa em `corpus_manifest.py`) — segmentos que afirmam estado comprovadamente superado são marcados `SUPERSEDED` na ingestão. Permanecem no GitHub e no banco para auditoria; nunca concorrem como autoridade vigente. Sem mudança de ranking/contrato/escopo.

### 18.2 Segmentos marcados

- `doc-83` — "R04 — Consumo por OP — **BLOQUEADO (sem artefato novo)**" (R04 está `IMPLEMENTED` — consumption-audit).
- `doc-85` — "§4 — R04 · Consumo por OP — `BLOQUEADO`" (idem).

Estados ainda verdadeiros preservados: doc-83/doc-85 "R13/R14 BLOQUEADO" (fonte externa — segue vigente), doc-80 histórico, todo o catálogo BR de doc-85 (citado pelas fichas).

### 18.3 Dados dinâmicos (inventário)

Consultas financeiras usam produtores oficiais vigentes: `production_order_consumption` (R04), `billing_mod_breakdown` (R09), `cost_closing_state` (R12/R15), settlements/stock/cost-center/billing-roster (R01–R11) — sempre com competência+filial+permissões; `officialParity` declarada. Nenhum número documental estático substitui dado operacional.

### 18.4 Testes

`test_superseded_state_segments`: query "O R04 ainda está bloqueado?" → zero itens `BLOQUEADO` retornados + ficha vigente presente; 2 segmentos SUPERSEDED; ≥3 segmentos R13/R14 BLOQUEADO permanecem PUBLISHED. Suíte PG: **15/15**. Mutações/enforcement/invariants preservadas.

### 18.5 Resíduos

- Conversacional live `TEST_NOT_RUN` (canal externo; GPT reexecuta).
- Política futura de `is_historical` granular por item (não fonte/segmento) segue `DECISION_REQUIRED` se demandada.
- Issue #130: sem credencial API — registro nesta seção.


## 19. Gate 080-RW01 — Zero exposição de conteúdo superado (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Adendo PO:** filtro no backend antes de qualquer entrega ao modelo; não via prompt/reranking.

### 19.1 Defeito reproduzido e inventário

GPT reproduziu: query `R04 está BLOQUEADO?` (sem `report_id`) retornava `doc-80` "27.C — Status por item" (pos. 2, `PUBLISHED`) afirmando `R04/R13/R14 BLOQUEADO` — R04 superado, R13/R14 vigentes no mesmo segmento. Inventário por conteúdo encontrou **16 segmentos** afirmando estados superados de R04/R09/R12/R15 (todos `IMPLEMENTED`): doc-80 ×2, doc-83 ×2, doc-85 ×2, doc-86 ×2, doc-113, doc-118 ×2, doc-120, doc-121, doc-124, doc-23 ×3, ficha-index (linha GATE A). Preservados por ainda verdadeiros: doc-80 "16.F BLOCKED" (artefato sanitizado), doc-112 "R01–R15 sem competência" (DR-C2), R13/R14 BLOQUEADO em doc-83/85.

### 19.2 Correção determinística — `STALE_SEGMENT_FIXES`

`corpus_manifest.py` declara dois modos por segmento (match por `title_contains`):
- **`drop`** (6): segmento inteiramente datado — sai da ingestão; item antigo vira `SUPERSEDED` pelo sweep por locator.
- **`fix`** (10): segmento misto — `fix_lines` reescreve **apenas** as linhas superadas; conteúdo corrigido volta pelo mesmo `citation_locator` → versão antiga `SUPERSEDED`, trilha de auditoria íntegra; marcador "Afirmação de estado superado corrigida na ingestão (Gate 080-RW01)" anexado.

Fonte canônica corrigida diretamente: `fichas/README.md` linha R04 (`NOT_IMPLEMENTED` → `IMPLEMENTADO` + capability). **Backend fail-closed:** `get_item` agora filtra `status='PUBLISHED'` — `knowledge(get)` de item superado → `KnowledgeNotFound`. Sem mudança de contrato/schema/ranking/permissão; histórico íntegro em GitHub + linhas SUPERSEDED.

### 19.3 Verificação

- Corpus local `19231723` (2.214/88): `state_fixed` = doc-80×2, doc-83×2, doc-85×2, doc-86×2, doc-113, doc-118×2, doc-120, doc-121, doc-124, doc-23×3; 73 itens SUPERSEDED na trilha.
- Query `R04 está BLOQUEADO?` **sem** filtro: `doc-80 27.C` agora afirma `R13/R14 BLOQUEADO; R04 implementado` — zero claim superado no top-12; `ficha-r04` pos. 1.
- `get()` no id superado → `KnowledgeNotFound`.
- `test_superseded_state_segments` reescrito: invariante de 12 padrões superados ausentes de TODO `PUBLISHED`, conteúdo corrigido presente, `get()` fail-closed, R13/R14 preservados. Suíte PG: **15/15**.

### 19.4 Resíduos

- Conversacional live `TEST_NOT_RUN`; issue #130 sem credencial API neste ambiente (registro aqui + report).
- Novos docs futuros com afirmações datadas exigem entrada declarativa no manifest — processo, não heurística.


## 20. Gate 081 — Auditoria integral do corpus CLARA (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Escopo:** 100% dos 2.214 itens PUBLISHED (não amostragem/top-12).

### 20.1 Método e cobertura

Scanner programático sobre os 2.214 itens (`/tmp/g081_audit.py` — detecção de afirmações de estado para R01–R15 + claims de handler/contrato/capability). **27 itens flagados → 100% revisados individualmente.** Caminhos de contexto auditados: `search`, `get`, `list_sources`, `list_top_items` — todos filtram `PUBLISHED`; `get_item` fail-closed desde G080-RW01.

### 20.2 Classificação dos 27 flagados

| Classe | Qtd | Itens |
|---|---|---|
| CURRENT_VERIFIED (já corrigidos/vigentes) | 10 | doc-80 27.C/48.1 fixados, doc-83/85/86/113/118/120/124 fixados, doc-112 DR-C2, ficha-r04/ficha-r09 |
| HISTORICAL_ONLY (narrativa datada legítima) | 7 | doc-00 ciclos 2/3, doc-113 §29.22/25.2, doc-117 ANL, doc-118 B, doc-119 11.7 |
| STALE_CONFIRMED → drop (7) | 7 | doc-121 stage-03, doc-23 G060/STAGE-03/REWORK-008, doc-85 publicação, doc-88 C3-D01/C3-D06 |
| STALE_CONFIRMED → fix_lines (1) | 1 | doc-86 §9 (lista bloqueados) |
| STALE_CONFIRMED → fonte corrigida (2) | 2 | README.md ×3 linhas, fichas/README.md R04 (RW01) |

### 20.3 Correções aplicadas

- **13 drops + 11 fix_lines** declarados em `STALE_SEGMENT_FIXES` (auditoria acrescentou 7 drops + 1 fix ao RW01).
- `README.md` e `fichas/README.md` corrigidos na fonte (docs canônicos vigentes).
- Teste: 19 padrões superados → zero em `PUBLISHED`; conteúdo corrigido presente; get() fail-closed; R13/R14 preservados. **Suíte 15/15**.
- Corpus local `5c48899a` (2.207 PUBLISHED / 86 SUPERSEDED — trilha íntegra).

### 20.4 Ressalva honesta

Classificação por regras determinísticas + revisão humana dos flagados — cobre afirmações de estado de relatórios/handlers/contratos; não exaure julgamento semântico de 2.214 itens (dados financeiros estáticos datados permanecem como evidência histórica legítima, nunca apresentados como vigentes pelas fichas). Novos docs datados exigem nova entrada no manifest.


## 21. Gate 082 — Certificação semântica integral (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Corpus auditado:** `1fd4c8b0` (2.207 itens / 88 fontes) — 100% inspecionado item a item via `tests/clara_semantic_audit.py` (reexecutável; inventário JSONL por item com classificação + justificativa).

### 21.1 Resultado da classificação (2.207 itens, reconciliado)

| Classe | Qtd | Composição |
|---|---|---|
| NOT_APPLICABLE | 2.045 | sem afirmação operacional sujeita a atualidade (regras, SQL, metadados, proveniência) |
| UNVERIFIED | 117 | valores monetários estáticos datados — evidência histórica legítima, nunca apresentada como vigente nas fichas |
| HISTORICAL_ONLY | 16 | narrativa datada com claims antigos em contexto temporal explícito |
| CURRENT_VERIFIED | 13 | segmentos corrigidos/negações verificadas contra a matriz vigente |
| REVIEW → resolvidos | 16 | **todos confirmados como ainda verdadeiros ou datados** (detalhe §21.2) |
| STALE_CONFIRMED | **0** | nenhum novo superado após revisão item a item dos flagados |

### 21.2 Revisão manual dos 16 REVIEW

Todos verificados contra a verdade vigente: `doc-80` (15.B/17.A/17.D/19.E/20.F/22.G/23.G/24.F) — `BLOCKED` refere **fonte `DLP06R01` ausente do acervo (E1, ainda vigente)** e investigações datadas; `doc-83 §2`/`doc-83 R13/R14`/`doc-85 §12/§13` — R13/R14 `BLOQUEADO` ainda verdadeiros (fontes externas); `doc-100` "Estado honesto" — "nenhuma paridade oficial homologada" (G6=0/15, vigente); `doc-112 32.6` — DR-C2 sem competência, vigente; `doc-118 B` — referências RQ-ANL. **Nenhuma afirmação de estado falsa encontrada.**

### 21.3 Caminhos de contexto — re-verificados

`search`, `get` (fail-closed `PUBLISHED`), `list_sources`, `list_top_items` — todos filtram `PUBLISHED`; acesso por `knowledge_id` SUPERSEDED → `KnowledgeNotFound`; `INTERNAL_ONLY` nunca no escopo `PORTAL_ACCESS`. Sem cache/caminho paralelo identificado.

### 21.4 Testes e residuos

- Suíte PG: **15/15** (19 padrões superados → zero PUBLISHED; golden 105 + negativos 10 + mutacionais + invariantes).
- Homologação conversacional: **`TEST_NOT_RUN`** — canal ChatGPT externo não automatizável; protocolo §14.6 disponível para o canal oficial.
- Ressalva: classificação é regra determinística + revisão humana dos flagados — 2.045 NOT_APPLICABLE não carregam claims de estado; julgamento semântico fino é procedimento do próximo GPT REVIEW. **Não declarado "zero stale absoluto"** — declarado: zero superado **identificado** na auditoria integral.


## 22. Gate 082-RW01 — Auditoria semântica por afirmação (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Corpus:** `5c48899a` local (2.207/88 — mesmo conjunto do produtivo `1fd4c8b0`). Resposta ao REWORK do GPT: a classificação regex é substituída por auditoria **claim-level** — `clara_semantic_audit.py` agora extrai 13.416 afirmações tipadas dos 2.207 itens, confronta cada afirmação operacional com a tabela de verdade vigente (matriz GATE A, capabilities do bridge, G6=0/15, ausências E1/E8/E9 ainda verdadeiras) e registra a cadeia afirmação→autoridade→evidência→conclusão→ação por linha.

### 22.1 Resultado (2.207 itens, reconciliado)

| Classe | Qtd | Composição |
|---|---|---|
| HISTORICAL_ONLY | 1.569 | afirmações temporalmente ancoradas (registros/evidências datadas) — confrontadas com a verdade, nenhuma superada sem decisão |
| NOT_APPLICABLE | 578 | regra/contrato/mecânica/plano — justificativa cita o conteúdo inspecionado (perfil estrutural) |
| CURRENT_VERIFIED | 60 | afirmações de estado corrente consistentes com a autoridade vigente |
| STALE_CONFIRMED/MIXED/CONFLICT/UNVERIFIED/REVIEW | **0** | fila zerada com decisão individual registrada |

### 22.2 Reexame dos 2.045 NOT_APPLICABLE

Todos reexaminados statement a statement: 1.486 continham afirmações invisíveis à regex (datadas, mecânicas, regras, plano) e **34 continham afirmações de estado corrente** — verificadas contra autoridade → CURRENT_VERIFIED. Os 117 UNVERIFIED (valores datados): 85 HISTORICAL_ONLY (competência explícita), 19 CURRENT_VERIFIED, 13 NOT_APPLICABLE (regra de paridade ilustrada). Os 45 restantes revalidados claim a claim.

### 22.3 Afirmações de bloqueio — verificação adversarial

16 claims contêm R04/R09/R12/R15 + predicado de bloqueio: todas decididas individualmente — linhas corrigidas G080-RW01 (doc-80 27.C/48.1), registros datados (doc-00/23/86/100), prerequisito DR-C2, spec de enum, negação (ficha-r04). **Nenhuma afirmação superada nova encontrada; nenhuma passou sem confronto.** Duas divergências datadas mantidas como histórico foram anotadas para o GPT (doc-100 "R01–R15 sem contrato", doc-118 "18 tools/52 fontes/1.298 itens").

### 22.4 Artefatos versionados

`docs/12-roadmap-e-evolucao/controllership-finance/evidence-g082rw/` — `g082rw-items.jsonl` (inventário inicial×final+justificativa), `g082rw-claims.jsonl` (matriz por afirmação, 15 campos do brief), `g082rw-divergences.jsonl`, `g082rw-coverage.md` (método, contagens, reconciliação, caminhos de contexto, testes).

### 22.5 Caminhos de contexto e testes

- Live: `get(SUPERSEDED)` → `KnowledgeNotFound`; `search "R04 bloqueado"` com e sem `report_id` → ficha-r04 no topo, zero claim superado; `list_sources` 88 fontes sem INTERNAL_ONLY; `get_context` projeta só metadados do corpus.
- `pytest tests/test_pg_clara_retrieval.py` (efêmero + reingestão): **15/15 PASS** — golden 105, negativos 10, guardas SUPERSEDED/INTERNAL/report_id.
- Sem mudança de corpus/runtime/contrato → `DEPLOY_NOT_APPLICABLE`. Homologação conversacional: **`TEST_NOT_RUN`** (canal ChatGPT externo; protocolo §14.6).

## 23. Gate 082-RW02 — Evidência verificável por revisor independente (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Corpus local:** `84e92712` (2.207/88 — republicado com fix_lines D1/D2). Resposta ao REWORK do RW01: revisão manual verdadeira, confronto de mecanismos, matriz de divergências e prova adversarial.

### 23.1 Revisão manual verdadeira

`MANUAL_VERDICTS` (regras por fonte com `match="."`) removido. Regras determinísticas passaram a `CURATED_RULES` rotuladas `automático`; decisões humanas vivem em `evidence-g082rw/g082rw-manual-decisions.json` — **22 decisões individuais** vinculadas por `knowledge_id` + `claim_hash`, com autoridade, evidência e justificativa por afirmação. Sem evidência individual → `UNVERIFIED`/`PENDING`.

### 23.2 Contratos e mecanismos confrontados

`_verify_mechanism` distingue regra normativa (A) de afirmação de comportamento implementado (B): `CAPABILITY_MAP`/`PRODUCER_MAP`/`CANON_FACTS`/`_CAP_TOKENS` verificáveis no HEAD. Mecânicas AS-IS de proveniência TO_INVENTORY sem verificação externa → `UNVERIFIED` honesto (não mascarado).

### 23.3 Divergências D1/D2 — registradas e tratadas

- **D1** doc-100 «R01–R15 sem contrato (PENDING_CONTRACT)» — `fix_lines`: linha reescrita com marcação temporal + estado vigente; original SUPERSEDED.
- **D2** doc-118 «MCP 18 tools / 52 fontes / 1.298 itens» — `fix_lines` idem.
Ambas no `DIVERGENCE_REGISTRY` emitido em `g082rw-divergences.jsonl` com risco/decisão/evidência. Corpus local `84e92712` e **corpus produtivo `9b2f318f`** (2.207/88) publicados via `corpus_ingestion --publish` (actor `clara-g082rw02`), após deploy do serviço. Smoke produtivo: `get(SUPERSEDED)`→KnowledgeNotFound; `search «R04 bloqueado»`→ficha-r04 topo; `sources`→88/0 INTERNAL. Resíduo declarado: menções datadas a `PENDING_CONTRACT`/`18 tools` permanecem em registros de pauta/evidência datados (HISTORICAL_ONLY) — candidatas a segregação futura se o PO estender a política a qualquer ocorrência textual.

### 23.4 Teste adversarial — 16/16

`tests/test_clara_semantic_audit_adversarial.py` — fixtures isoladas, expectativas declaradas. O teste reproduziu 3 defeitos reais do auditor, corrigidos: `no` (preposição) lido como negação; "não possui" ausente do predicado de bloqueio; claims `mechanism` sem surface-token sem confronto.

### 23.5 Contagens finais (corpus `84e92712`)

88 CURRENT_VERIFIED · 1.310 HISTORICAL_ONLY · 238 NOT_APPLICABLE · **571 UNVERIFIED (PENDING)** — 1.341 claims sem autoridade conclusiva, declarados, não homologados. Zero STALE_CONFIRMED/REVIEW/MIXED residuais. `pytest tests/test_pg_clara_retrieval.py`: **15/15**; adversarial: **16/16**. Homologação conversacional: **TEST_NOT_RUN**.

## 24. Gate 083 — Eliminação de resíduos (03/11/2026)

**Executor:** Devin · **Issue:** #130 · **Corpus:** `5782708a` local (2.208/88 — republicado; produtivo `59bedb57`→`PENDING` (republicação com resíduos finais)). Objetivos G083-A/B/C contra os resíduos do `ACCEPT_WITH_RESIDUAL` do G082-RW02.

### 24.1 G083-A — Pendências semânticas

1.341 afirmações `UNVERIFIED` reconciliadas em `g083-claim-authority-matrix.jsonl` com natureza/autoridade/disposição individual: **806 NOT_APPLICABLE** (spec/contrato aprovado), **346 VALID_HISTORICAL** (evidência AS-IS TO_INVENTORY), **189 PENDING_AUTHORITY** (declaradas como pendências — não PASS). 29 decisões individuais hash-keyed em `g083-manual-decisions.json`.

### 24.2 G083-B — Histórico superado segregado

Varredura integral do corpus (não só top-hits): 22 correções (`g083-corrections.jsonl`) — D1/D2 do RW02 + 20 `fix_lines` G083 anotando afirmações datadas superadas (`PENDING_CONTRACT` de relatórios já implementados, `18 tools`, `52 fontes`, bloqueios datados R04/R03) em doc-00/86/88/90/100/111/117/119/121/122. Originais em SUPERSEDED (141 itens). Padrões `stale_patterns` Gates 080/081 + G083: **0 ocorrências PUBLISHED**.

### 24.3 G083-C — Homologação conversacional

**TEST_NOT_RUN** — canal oficial ChatGPT/CLARA indisponível neste ambiente; protocolo executável em `g083-conversational-115.md` e §14.6 (105 golden + 10 negativos).

### 24.4 Evidências e testes

`evidence-g083/`: residual-inventory, claim-authority-matrix, historical-exposure, corrections, retrieval-validation, tests, conversational-115, coverage. Testes: auditoria claim-level (0 REVIEW/STALE), adversarial **16/16**, suíte PG **15/15** (golden 105 + 10 negativos + invariantes SUPERSEDED/escopo). Artefatos intermediários descobertos pelo próprio teste de invariante (doc-121 `report_not_implemented`, variante doc-86, índice doc-00) corrigidos e revalidados.
