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
<<<<<<< HEAD
=======

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
>>>>>>> origin/main
