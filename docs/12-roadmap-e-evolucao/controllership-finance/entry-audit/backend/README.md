# Entry audit · Back-end

| Campo | Valor |
|---|---|
| Status | **READY** — contrato fecha na T1 da [trilha](../track.md) |
| Plano | [../plan.md](../plan.md) |
| Serviços | `api-delpi` (Protheus, leitura) · `financial-api` (XML do Questor) · `controllership-finance-api` (BFF: motor, execução, persistência, rotas, MCP) |

## 1. Arquitetura

Ver o diagrama no [plano §4](../plan.md). Regras de fronteira: o MFE só fala com a BFF; a BFF fala com a api-delpi e a financial-api por HTTP; o SQL do Protheus fica na api-delpi; a busca de XML fica na financial-api; o motor de regras é domínio puro na BFF.

## 2. Decisões que afetam o back-end

D1 (motor na BFF), D2 (dados automáticos), D4 (tudo com `controllership-finance.access`), D6 (CLARA executa direto), D7 (worker na BFF), D8 (período livre). Status de cada uma no [plano §3](../plan.md).

## 3. Estrutura

### 3.1 Fluxo de uma auditoria

1. Alguém pede a auditoria: botão na página **ou** um comando à CLARA («audita as entradas de outubro»).
2. A BFF cria uma **análise** (`entry_audit_analysis`: período De/Até, tipos de documento, filiais) com uma **execução por filial** (`entry_audit_run`, status `queued`) e responde na hora com o identificador. Se já existe uma análise em andamento com os mesmos filtros de execução, devolve a mesma (idempotente).
3. Um **worker dentro da BFF** pega a execução. É o mesmo padrão do job de notificações que já roda no `lifespan` da BFF (`startup/notification_dispatch_job`).
4. O worker busca as fontes:
   - Protheus pela api-delpi: SF1, SD1, SF4, SFT e fornecedores (SA2) da filial no período informado (pela data de recebimento, como na exportação da SF1 hoje), só dos **tipos de documento** escolhidos;
   - XML pela financial-api: NF-e e CT-e da filial pela data de emissão, com folga antes do início do período para pegar notas emitidas antes e recebidas dentro dele, e os eventos de cancelamento. XML já baixado antes é reaproveitado do cache por chave de acesso, porque XML não muda.
5. O worker roda o **motor de regras** (domínio puro) e grava o resultado: notas casadas, ocorrências, notas sem par, CT-e, TES usadas.
6. O status de «resolvido» das ocorrências que continuam existindo é mantido pela **chave estável**.
7. A execução termina como `done` (ou `failed`, com o motivo). A página acompanha o andamento; a CLARA consulta o status e, ao terminar, apresenta o resultado.

### 3.2 api-delpi — leitura do Protheus (owner TOTVS)

Prefixo no padrão dos relatórios financeiros: `/financeiro/entry-audit`. Só leitura, paginado, sem regra fiscal (a regra fica no motor da BFF).

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /financeiro/entry-audit/documents` | `branch`, `received_from`, `received_to`, `species` (`SPED`, `CTE`), `page`, `page_size` | cabeçalhos SF1 + CNPJ/UF do fornecedor (SA2) |
| `GET /financeiro/entry-audit/items` | mesmos filtros | itens SD1 dos mesmos documentos |
| `GET /financeiro/entry-audit/fiscal-book` | mesmos filtros | itens do livro fiscal (SFT) dos mesmos documentos |
| `GET /financeiro/entry-audit/tes` | — | cadastro de TES (SF4) inteiro |
| `GET /financeiro/entry-audit/branches` | — | filiais com CNPJ e UF |

O inventário T0 (§4.2) mostra o que já existe e o que a T2 cria. Não há SQL pronto para este recorte.

### 3.3 financial-api — XML do Questor (owner)

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /invoices/received/export` | `branch`, `type` (`nfe` \| `cte`), `issued_from`, `issued_to`, `page`, `page_size` | lista com chave, número, série, emitente, emissão, valor, situação e os ids do provedor para baixar o XML |
| `GET /invoices/received/{id}/xml/original` | `branch`, `type` | XML original (já existe para CT-e e NFS-e; a NF-e usa `download_nfe_xml`) |

**Listagem por data (T0, 2026-11-14).** A NF-e (`/cliente/nfe/listagem`) aceita `EmissionStart`/`EmissionEnd` em `dd/MM/yyyy` e devolve só dias dentro da janela. O mesmo par em ISO (`yyyy-MM-dd`) responde HTTP 500 HTML. O CT-e (`/cliente/cte/listagem`) aceita o par nos dois formatos e o total cai (sem filtro, milhares; com 01/11–12/11, 34 na filial 01). `iTotalDisplayRecords` da NF-e não é a cardinalidade: ecoa a janela de página (`start + página + 1`, ou o `iDisplayLength`). A financial-api conta percorrendo páginas até uma página curta. Não há fallback de upload. Detalhe no §4.

### 3.4 controllership-finance-api — rotas da BFF

Prefixo `/entry-audit`. Todas exigem `controllership-finance.access` (D4). A unidade de trabalho é a **análise**: um período (De/Até) escolhido pelo usuário, as filiais e os tipos de documento. Cada análise tem uma execução por filial e fica guardada para acompanhamento.

**Execução e histórico**

| Método e rota | Uso |
|---|---|
| `POST /entry-audit/analyses` | body `{date_from, date_to, document_types: ["nfe","cte"], branches: ["01","02"]}` (período livre: nenhuma data fixada pela BFF) → 202 com a análise criada (ou a que já está em andamento com os mesmos filtros) |
| `GET /entry-audit/analyses/options` | filiais permitidas (código, nome, UF, CNPJ) e tipos de documento (NF-e, CT-e) com o padrão |
| `GET /entry-audit/analyses` | histórico: filtros `date_from`, `date_to`, `branch`, `status`; paginação |
| `GET /entry-audit/analyses/{id}` | status, andamento por filial (etapa, documentos lidos, XML baixados), contagens, erro |
| `POST /entry-audit/analyses/{id}/rerun` | reexecuta com os mesmos filtros (ou só a filial que falhou: `{branches: ["02"]}`) |

**Dashboard** (todas aceitam os filtros da análise: `branch`, `severity`, `theme`, `supplier`, `tes`, `document_type`, `day`, `status`, `q`; o servidor calcula, o MFE não recalcula regra)

| Método e rota | Alimenta |
|---|---|
| `GET /entry-audit/analyses/{id}/summary` | os 4 KPIs, comparação com o período anterior de mesmo tamanho, conformidade (sem divergência, com divergência, sem par a resolver, sem par explicadas) |
| `GET /entry-audit/analyses/{id}/daily` | notas com divergência por dia, do período e do período anterior |
| `GET /entry-audit/analyses/{id}/breakdowns` | por severidade, por tema, top fornecedores (com % das notas com divergência) e TES com mais ocorrências |
| `GET /entry-audit/analyses/{id}/facets` | listas para os selects de filtro (fornecedores, temas, TES, severidades) com contagem |
| `GET /entry-audit/trend` | evolução entre análises: pendentes e altas por mês, filtros `branch`, `date_from`, `date_to` |

**Tabelas, detalhe e ações**

| Método e rota | Uso |
|---|---|
| `GET /entry-audit/analyses/{id}/occurrences` | aba Ocorrências; paginação e ordenação |
| `GET /entry-audit/analyses/{id}/occurrences/{key}` | detalhe: valores, por quê, o que fazer, regra citada, chave e links de DANFE/DACTE/XML, histórico de status |
| `GET /entry-audit/analyses/{id}/documents` | aba Notas casadas |
| `GET /entry-audit/analyses/{id}/unmatched` | aba Notas sem par |
| `GET /entry-audit/analyses/{id}/cte` | aba CT-e |
| `GET /entry-audit/analyses/{id}/tes` | aba TES usadas |
| `POST /entry-audit/occurrences/{key}/resolve` · `/reopen` | status compartilhado (quem e quando) |
| `POST /entry-audit/unmatched/{key}/resolve` · `/reopen` | idem para notas sem par |
| `GET /entry-audit/analyses/{id}/export` | planilha no layout atual da skill |

A **chave estável** de uma ocorrência não depende do período: filial + chave de acesso do documento + ocorrência + campo + item. Assim, a mesma ocorrência que aparece em duas análises com períodos sobrepostos mostra o mesmo status de resolvida.

Envelope, erros e `meta` iguais aos das outras rotas da BFF. Os DANFE/DACTE/XML usam as rotas que o LNF já expõe na BFF.

### 3.5 Organização do código na BFF (Clean Architecture)

| Camada | Pasta | Conteúdo |
|---|---|---|
| domain | `domain/entry_audit/` | modelos (documento, item, livro, TES, XML NF-e/CT-e, ocorrência, severidade, tema); casamento SF1×XML (inclusive troca de chave) e SD1×itens; regras separadas por grupo (cabeçalho, itens, coerência, Simples/presumido SC, CT-e, chave/espécie/fornecedor, livro fiscal, sem par, «não apontado»); motor que junta tudo |
| application | `application/entry_audit/` | executar, consultar, resolver/reabrir, exportar; portas (`ProtheusEntriesPort`, `FiscalXmlPort`, `EntryAuditRepository`) |
| infrastructure | `infrastructure/entry_audit/` | gateway api-delpi, gateway financial-api, leitura dos XML (porte de `leitura.py`), repositório Postgres, cache de XML, exportação xlsx (porte de `relatorio.py`) |
| interface | `interface/http/routes/entry_audit/` · `interface/mcp/` | rotas HTTP; entradas da CLARA no catálogo semântico |
| startup | `startup/entry_audit_worker.py` | worker no `lifespan`; ao subir, devolve para a fila as execuções que estavam rodando quando o processo parou |

### 3.6 Persistência

Migration `V023` no schema `controllership_finance`, com as tabelas da seção 7 e mais `entry_audit_xml_cache` (chave de acesso, modelo, XML compactado, data da busca).

### 3.7 CLARA — «audita todas as notas» num comando

| Pedido do usuário | O que a CLARA faz |
|---|---|
| «Audita as entradas de outubro» | `execute entry_audit.run {date_from: 2026-10-01, date_to: 2026-10-31, branches: todas}` → recebe a análise; consulta `read entry_audit.analysis` até terminar; chama `analyze entry_audit_findings`; responde no formato da skill: o que pede ação, o que corrigir, o que não tem impacto |
| «Me explica o dashboard» | `read entry_audit.summary` + `breakdowns` + `daily` → explica os KPIs, a conformidade, os temas e os fornecedores que concentram ocorrências, e compara com o período anterior |
| «O que melhorou desde setembro?» | `read entry_audit.trend` + `analyze entry_audit_findings` → evolução e sugestão de direcionamento (por exemplo, cadastrar fornecedor no Configurador de Tributos, corrigir uma TES) |
| «O que ainda está pendente na matriz?» | `read entry_audit.occurrences {branch: 01, status: pending}` da última análise |
| «Por que essa CT-e deu alta?» | `read` da ocorrência + `knowledge` com a regra citada |
| «Marca a NF 123 da WEG como resolvida» | `execute entry_audit.resolve` |

A execução é **direta**, sem prepare/confirmação: não altera dado de negócio (só cria o resultado da auditoria), é idempotente por período e filiais e o owner quer que a CLARA faça o trabalho num comando só (D6). Resolver e reabrir também são diretos. Catálogo completo da CLARA em [../mcp/README.md](../mcp/README.md).

### 3.8 Filtros da execução e configuração

Os filtros que o usuário informa são os **dois que ele usa hoje**: o **período** (De/Até, livre — a BFF não fixa nem sugere datas), aplicado na data de recebimento como na exportação da SF1, e os **tipos de documento**, que hoje ele filtra no Excel. A filial vem da escolha de filiais (a skill roda uma filial por vez).

Os parâmetros que na skill eram argumentos fixos — TES do crédito presumido de SC (`004`) e final do CFOP de frete (`352`) — viram **configuração da BFF** (variáveis de ambiente com esses padrões), fora da tela e fora do pedido. Cada análise grava a versão da configuração usada.

**Tipo de documento (decisão do owner, 2026-11-13):** hoje a SF1 é filtrada pela **Espécie do documento** (`F1_ESPECIE`) em **SPED** e **CTE**, e o Questor é exportado em **NF-e** e **CT-e**. Na Delpi, SPED = NF-e (55) e CTE = CT-e (57) nos dois sistemas. A BFF traduz o filtro único «NF-e / CT-e» em `species=SPED,CTE` na api-delpi e em `type=nfe,cte` na financial-api. Outras espécies (NFS, CF…) ficam fora. O tipo de nota (`F1_TIPO`: N, C…) não é filtrado.

### 3.9 O que a amostra real mostrou (12/11/2026, Matriz) e o que a plataforma faz melhor

Amostra enviada pelo owner: SF1 e SD1 exportadas do Protheus (Genéricos) e dois ZIPs do Questor; a skill foi rodada sobre ela para servir de referência. Os dados ficam fora deste repositório (ele é público); só os números entram aqui.

| Item | Amostra |
|---|---|
| Recorte da SF1 | **um dia**: recebimento 12/11/2026 (SD1 com a mesma data de digitação); 10 notas, 13 itens |
| Espécies na SF1 exportada | SPED 4 · CTE 3 · NFS 2 · CF 1 (no uso normal, o usuário filtra SPED e CTE); tipos de nota N 7 · C 3 |
| Recorte do Questor | **um dia**: emissão 11/11/2026, destinatário = CNPJ da Matriz; 15 NF-e (inclui 1 transferência da Filial) e 1 CT-e |
| Resultado da skill | 2 NF-e casadas · 0 CT-e casados · **14 só no XML** (Média) · **5 só no SF1** (Info, emitidas antes de 11/11) · 3 ocorrências Média (origem da mercadoria) · «não apontado»: 5 ICMS em TES sem crédito, 3 CST 090 |
| Tamanho | ~10 notas por dia na Matriz: volume pequeno; desempenho não é risco |

**O que isso ensina.** Na skill, a SF1 é recortada pela data de **recebimento** e o XML pela data de **emissão**, em downloads separados. Quase tudo vira «sem par» por diferença de datas, e não por erro: das 16 notas do Questor, 14 ainda não tinham sido lançadas no dia (várias delas estavam na fila do Lançamento de Notas Fiscais no dia seguinte), e 5 notas da SF1 foram emitidas antes do dia baixado.

A plataforma resolve isso sem mudar as regras:

1. **XML pela chave.** Para cada nota da SF1 com chave, a BFF busca o XML **pela chave** no Questor (a financial-api já baixa por identificador; a listagem atual filtra por número, CNPJ e valor). «Só no SF1 por período» deixa de existir: só sobra o que de fato não tem XML.
2. **Listagem por emissão só para achar o que não foi lançado.** A listagem do Questor no período (com folga antes do início) serve para encontrar XML sem lançamento.
3. **Cruzamento com o Lançamento de Notas Fiscais.** O LNF está na mesma BFF. Uma nota «só no XML» que tem solicitação aberta no LNF (aguardando, em atendimento ou com pendência) recebe a situação **«Em lançamento (LNF)»**, com o status e o link da solicitação, em vez de «não escriturada». Sem solicitação e emitida há mais de N dias, continua Média.
4. **CT-e pelo tomador.** O CT-e do download pode ter outro destinatário; a regra do tomador da skill (empresa tomadora → deve ser escriturado) continua valendo.

Essas três mudanças (1–3) alteram as contagens de «sem par» em relação à skill. No teste de paridade (E2), elas são comparadas à parte: o motor com os mesmos insumos da skill tem de dar o mesmo resultado; as melhorias são uma camada a mais, documentada.

## 4. Dados necessários (inventário T0, 2026-11-14)

Leitura somente. Protheus: `SX3010` e `SF1010`/`SFT010`/`SF4010`/`SYS_COMPANY` no banco `DELPI`, o mesmo que a api-delpi de HML e a local usam. Questor: container `delpi-financial-api` de PROD (token configurado, filiais 01 e 02). A financial-api de HML não está no ar; a chamada real foi em PROD, sem token, CNPJ, chave ou valor no log. Classificação: `PROVEN` salvo onde está `TO_INVENTORY`.

### 4.1 Coluna da skill × campo × tabela

Títulos conferidos em `SX3010` (`D_E_L_E_T_ = ' '`). `leitura.py` não lê nome físico: lê o cabeçalho da planilha e o XML. O motor da BFF consome os campos físicos abaixo, não o apelido da planilha.

**SF1 → `SF1010`**

| Coluna da skill | Campo | Título SX3 |
|---|---|---|
| Filial | `F1_FILIAL` | Filial |
| Numero | `F1_DOC` | Numero |
| Serie | `F1_SERIE` | Serie |
| Fornecedor | `F1_FORNECE` | Fornecedor |
| Loja | `F1_LOJA` | Loja |
| Nome Forn. | `A2_NOME` | Razao Social |
| Estado | `A2_EST` | Estado |
| CNPJ (coluna opcional) | `A2_CGC` | CNPJ/CPF |
| Chave NFe | `F1_CHVNFE` | Chave NFe |
| DT Emissao | `F1_EMISSAO` | DT Emissao |
| Dt. Receb. | `F1_RECBMTO` | Dt. Receb. |
| Espec.Docum. | `F1_ESPECIE` | Espec.Docum. |
| Tipo da Nota | `F1_TIPO` | Tipo da Nota |
| Form. Prop. | `F1_FORMUL` | Form. Prop. |
| Vlr.Frete | `F1_FRETE` | Vlr.Frete |
| Vlr.Despesas | `F1_DESPESA` | Vlr.Despesas |
| Base p/ICMS | `F1_BASEICM` | Base p/ICMS |
| Vlr.ICMS | `F1_VALICM` | Vlr.ICMS |
| Base p/IPI | `F1_BASEIPI` | Base p/IPI |
| Vlr.IPI | `F1_VALIPI` | Vlr.IPI |
| Vlr.Mercad | `F1_VALMERC` | Vlr.Mercad |
| Vlr.Bruto | `F1_VALBRUT` | Vlr.Bruto |
| Descontos | `F1_DESCONT` | Descontos |
| Base ICM Sol | `F1_BRICMS` | Base ICM Sol |
| ICMS Solid. | `F1_ICMSRET` | ICMS Solid. |
| Vlr.Seguro | `F1_SEGURO` | Vlr.Seguro |

`Nome Forn.` não existe no SX3. A skill espera esse cabeçalho; a fonte é `SA2010.A2_NOME`.

**SD1 → `SD1010`**

| Coluna da skill | Campo | Título SX3 |
|---|---|---|
| Filial | `D1_FILIAL` | Filial |
| Documento | `D1_DOC` | Documento |
| Serie | `D1_SERIE` | Serie |
| Forn/Cliente | `D1_FORNECE` | Forn/Cliente |
| Loja | `D1_LOJA` | Loja |
| Item NF | `D1_ITEM` | Item NF |
| Produto | `D1_COD` | Produto |
| Cod. Fiscal | `D1_CF` | Cod. Fiscal |
| Sit.Tribut. | `D1_CLASFIS` | Sit.Tribut. |
| Tipo Entrada | `D1_TES` | Tipo Entrada |
| Quantidade | `D1_QUANT` | Quantidade |
| Vlr.Unitario | `D1_VUNIT` | Vlr.Unitario |
| Vlr.Total | `D1_TOTAL` | Vlr.Total |
| Base Icms | `D1_BASEICM` | Base Icms |
| Aliq. ICMS | `D1_PICM` | Aliq. ICMS |
| Vlr.ICMS | `D1_VALICM` | Vlr.ICMS |
| Vlr.Base IPI | `D1_BASEIPI` | Vlr.Base IPI |
| Aliq. IPI | `D1_IPI` | Aliq. IPI |
| Vlr.IPI | `D1_VALIPI` | Vlr.IPI |
| ICMS Solid. | `D1_ICMSRET` | ICMS Solid. |
| Desconto | `D1_VALDESC` | Desconto |

`D1_DESC` (título `Desc.Item`) é percentual. O número «Desconto» da skill é `D1_VALDESC`.

**SF4 → `SF4010`**

| Coluna da skill | Campo | Título SX3 |
|---|---|---|
| Cod. do Tipo | `F4_CODIGO` | Cod. do Tipo |
| Txt Padrao | `F4_TEXTO` | Txt Padrao |
| Calcula ICMS | `F4_ICM` | Calcula ICMS |
| Cred. ICMS ? | `F4_CREDICM` | Cred. ICMS ? |
| L.Fisc. ICMS | `F4_LFICM` | L.Fisc. ICMS |
| Calcula IPI? | `F4_IPI` | Calcula IPI? |
| Credita IPI? | `F4_CREDIPI` | Credita IPI? |
| L.Fiscal IPI | `F4_LFIPI` | L.Fiscal IPI |
| Mat.Consumo | `F4_CONSUMO` | Mat.Consumo |

**SFT → `SFT010`.** A skill casa apelidos de planilha (`SFT_COLS` em `regras.py`). Vários títulos reais do SX3 não estão nessa lista (`Cli/Forn.`, `Codigo loja`, `Código Item`, `Vlr Isen ICM`, `Vlr Out ICMS`, `Data Cancel`). A api-delpi lê a coluna física. Período do livro: `FT_ENTRADA` (Data Entrada), que a skill não lista.

| Papel | Campo | Título SX3 |
|---|---|---|
| Filial | `FT_FILIAL` | Filial |
| Tipo de movimento | `FT_TIPOMOV` | Tipo Mov. |
| Documento | `FT_NFISCAL` | Doc. Fiscal |
| Série | `FT_SERIE` | Série NF |
| Fornecedor | `FT_CLIEFOR` | Cli/Forn. |
| Loja | `FT_LOJA` | Codigo loja |
| Item | `FT_ITEM` | Código Item |
| Chave | `FT_CHVNFE` | Chave Nfe |
| ICMS creditado | `FT_VALICM` | Valor ICMS |
| ICMS outras | `FT_OUTRICM` | Vlr Out ICMS |
| ICMS isentas | `FT_ISENICM` | Vlr Isen ICM |
| IPI creditado | `FT_VALIPI` | Valor IPI |
| Cancelamento | `FT_DTCANC` | Data Cancel |
| Data de entrada | `FT_ENTRADA` | Data Entrada |

**Empresa → `SYS_COMPANY`** (não está no SX3). `M0_CODFIL` 01 UF `SC`; 02 UF `ES`; CNPJ com 14 dígitos. Há várias empresas no mesmo código de filial (`M0_CODIGO` 01, 03, 04, 05 na filial 01; 01 e 04 na filial 02), todas com a marca no nome. As tabelas `*010` são a empresa `01`. A rota `branches` filtra `M0_CODIGO = '01'`.

### 4.2 SQL já existente na api-delpi

Não há consulta que devolva o recorte da auditoria. Reaproveita-se o padrão (`WITH (NOLOCK)`, `D_E_L_E_T_ = ' '`, filial, join SF1 por filial+documento+série+fornecedor+loja):

| Tabela | O que já existe | O que a T2 cria |
|---|---|---|
| SF1 | `purchase_freight_sql.py` lê chave, espécie, bruto, mercadorias e emissão de um documento já conhecido | listagem por `F1_RECBMTO` + `F1_ESPECIE` |
| SD1 | recebimento de compra, kardex, preço — sem CST/CFOP/TES fiscais da auditoria | itens dos mesmos documentos |
| SF4 | `F4_CODIGO` / `F4_DUPLIC` em faturamento e CPV | cadastro inteiro com crédito e livro |
| SFT | nenhuma ocorrência de `SFT010` no código | livro por documento/item |
| SA2 | `totvs_supplier_repository.py` (`A2_COD`, `A2_LOJA`, `A2_CGC`, `A2_EST`, `A2_NOME`) | join no documento, não uma busca solta |
| Filiais | `SYS_COMPANY` em propostas comerciais (`M0_CODFIL`, `M0_CGC`) | `branches` da empresa `01` |

Autorização das rotas `/financeiro/*` que a BFF consome: JWT do usuário em `Authorization` mais `X-Delpi-Service-Authorization` (client-credentials da BFF). Gateway: `controllership-finance-api/.../infrastructure/api_delpi_gateway.py`.

### 4.3 Questor / financial-api

| Pergunta | Evidência |
|---|---|
| A listagem de NF-e filtra data? | Sim, `EmissionStart`/`EmissionEnd` em `dd/MM/yyyy`. Em 12/11/2026 a página só teve esse dia (filial 01: 10 linhas; filial 02: 20). ISO nesse par devolve HTTP 500. Sem data, a primeira página traz vários dias e `iTotalDisplayRecords` não é a contagem real. |
| Filtra destinatário? | Não há parâmetro de destinatário. A sessão é da empresa (`QuestorCompanyRegistry`, filiais `01` e `02`). Os dois dias acima diferem, então as sessões não se misturam. |
| Como listar CT-e recebido? | `GET /cliente/cte/listagem` com `Entry=0`, ordenado por `DhEmi`. O adapter já envia `EmissionStart`/`EmissionEnd` vazios (`questor_cte_adapter.py`). Preenchidos, o total da filial 01 cai de 3760 para 34 no intervalo 01/11–12/11, em BR e em ISO. |
| Como achar o XML pela chave? | A chave tem CNPJ do emitente nas posições 7–20, modelo 21–22, série 23–25 e número 26–34 (`fiscal_access_key.py`). NF-e: `NfeNumber` (+ `IssuerFederalRegistration`) devolve a linha cuja chave é a pedida; o XML sai por `XmlFilename` + `Id` em `/cliente/transferenciaArquivo/download`. Não há filtro de chave na listagem de NF-e. CT-e: o parâmetro `KeyCte` existe no adapter e vai vazio; a T3 prova o preenchimento. |
| Sessão da filial 02? | `PROVEN` em PROD: company id configurado e a listagem de 12/11 devolve conjunto diferente da filial 01. Em HML o container `delpi-hml-financial-api` não existe. |

O `ReceivedInvoiceQuery` vigente ainda não tem período. A T3 acrescenta `issued_from`/`issued_to` e a busca por chave. D2 permanece automática.

### 4.4 LNF — solicitação aberta

A solicitação (`invoice_posting_requests`) não guarda a chave. A chave está só no DANFE anexado (`invoice_posting_danfe_attachments.access_key`, `V008`). A chave fiscal da solicitação é filial + fornecedor + loja + número (`document_match_key`) + série (`uq_lnf_requests_active_fiscal_key`).

Aberta = `pending`, `in_progress` ou `blocked` (`NON_TERMINAL_STATUSES` em `fiscal_normalization.py`). `list_requests` já filtra número, fornecedor e status; não filtra chave. Para a D11 a BFF consulta, na ordem: chave no anexo do DANFE; senão número + fornecedor (+ série, se houver). Sem anexo, a chave sozinha não acha a solicitação. Somente leitura.

### 4.5 Padrões da BFF que a trilha reutiliza

| Peça | Onde | Próximo uso |
|---|---|---|
| Job no `lifespan` | `main.py` cria a task de `run_closing_notification_dispatch_loop` e cancela no shutdown | `startup/entry_audit_worker.py` no mesmo ponto, atrás de `ENTRY_AUDIT_ENABLED` |
| Migrations | `migrations_runner.py` aplica `migrations/V###__*.sql` com checksum. Última: `V022`. | `V023` |
| Catálogo semântico | `interface/mcp/server.py`: seis tools; capacidade nova é `(entity, action)` em `semantic_bridge.py` | entradas `entry_audit.*` na T7, sem tool nova |
| Corpus | `corpus_manifest.py`, `access_scope=PORTAL_ACCESS` | fichas AE no domínio `controllership` |
| Instruções | `interface/mcp/branding.py` | bloco da auditoria na T7 |
| Testes MCP | `tests/test_clara_catalog_schema_callable.py`, `test_clara_direct_execution.py`, `test_clara_corpus_parity.py` | mesmos padrões na T7 |

### 4.6 Volume (banco `DELPI`, recebimento em `F1_RECBMTO`, 2026)

Notas por mês e filial, espécies da auditoria. Novembro vai até 14/11.

| Mês | 01 SPED | 01 CTE | 02 SPED | 02 CTE |
|---|---:|---:|---:|---:|
| 01 | 154 | 40 | 128 | 44 |
| 02 | 177 | 44 | 154 | 48 |
| 03 | 196 | 54 | 224 | 118 |
| 04 | 175 | 58 | 185 | 59 |
| 05 | 192 | 60 | 155 | 53 |
| 06 | 167 | 57 | 192 | 63 |
| 07 | 160 | 55 | 202 | 66 |
| 08 | 216 | 73 | 204 | 67 |
| 09 | 218 | 50 | 176 | 39 |
| 10 | 227 | 59 | 224 | 97 |
| 11 (até 14) | 132 | 45 | 93 | 45 |

Um dia, 12/11/2026: filial 01 = 12 SPED + 7 CTE (+ 2 NFS + 1 CF, fora da auditoria); filial 02 = 19 SPED + 0 CTE (+ 4 NFS + 2 CF). A amostra do owner (10 notas na matriz) é um recorte manual, menor que a `SF1010` do dia. A paridade compara o mesmo conjunto de entrada, não essa contagem bruta.

Livro em novembro (`FT_TIPOMOV = 'E'`, `FT_ENTRADA`): 480 linhas na filial 01 e 532 na 02. SF4 com filial vazia ou `01`: 458 cadastros. Volume de um mês cabe numa execução assíncrona.

### 4.7 Adaptações em relação ao texto anterior

| Premissa antiga | Evidência | Adaptação |
|---|---|---|
| Listagem do Questor não recebe data; senão, upload | Data em `dd/MM/yyyy` funciona na NF-e e no CT-e | D2 segue automática. Sem upload. |
| `iTotal*` da listagem é a contagem | Na NF-e o total ecoa a página | T3 conta as linhas, página a página |
| Apelidos da SFT na skill cobrem a Delpi | Títulos SX3 divergem | Contrato usa a coluna física |
| Uma linha de `SYS_COMPANY` por filial | Várias empresas por `M0_CODFIL` | `branches` usa `M0_CODIGO = '01'` |


## 5. Persistência (TARGET, schema `controllership_finance`)

| Tabela | Conteúdo |
|---|---|
| `entry_audit_analysis` | período (De/Até), tipos de documento, filiais, versão da configuração usada, status agregado, quem pediu (usuário ou CLARA em nome do usuário), datas |
| `entry_audit_run` | uma por filial da análise: status (`queued`/`running`/`done`/`failed`), etapa e andamento, contagens, versão do motor, hash das fontes, erro |
| `entry_audit_document` | notas casadas (cabeçalho comparado), situação |
| `entry_audit_occurrence` | ocorrência: chave estável, severidade, tema, ocorrência, NF, fornecedor, item, campo, valor Protheus, valor XML, diferença, TES, por quê, ação sugerida, regra |
| `entry_audit_unmatched` | notas só no XML / só no SF1, com motivo e situação |
| `entry_audit_cte` | comparativo dos CT-e |
| `entry_audit_tes_used` | TES usadas na análise, com a configuração da SF4 |
| `entry_audit_status` | resolvido/reaberto por **chave estável** (independente do período), quem e quando |
| `entry_audit_xml_cache` | XML por chave de acesso (compactado), data da busca |

Uma reexecução substitui o resultado da filial, e o status de resolvido continua valendo pela chave estável.
