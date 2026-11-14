# Entry audit · Back-end

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** (contrato fecha na E1) |
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

A E0 confirma se já existe SQL reaproveitável para algum destes (há consultas de SF1/SD1 em compras e estoque).

### 3.3 financial-api — XML do Questor (owner)

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /invoices/received/export` | `branch`, `type` (`nfe` \| `cte`), `issued_from`, `issued_to`, `page`, `page_size` | lista com chave, número, série, emitente, emissão, valor, situação e os ids do provedor para baixar o XML |
| `GET /invoices/received/{id}/xml/original` | `branch`, `type` | XML original (já existe para CT-e e NFS-e; a NF-e usa `download_nfe_xml`) |

**Lacuna:** a listagem atual do Questor (`/cliente/nfe/listagem`) não recebe data. Ela vem ordenada por emissão (`orderGroup=Emission`) e só com entradas (`Entry=True`). A E0 prova se aceita filtro de data; se não aceitar, a financial-api pagina pela emissão e para quando passar do início do período. A entrada automática continua viável nos dois casos.

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

## 4. Dados necessários (a confirmar na E0)

| Fonte | Campos usados pelo motor (ver `scripts/regras.py`) | Owner |
|---|---|---|
| SF1 | filial, documento, série, fornecedor/loja, espécie, chave, emissão, recebimento, valores (bruto, mercadorias, ICMS, base, IPI, ST, frete, despesa, desconto) | api-delpi |
| SD1 | item, produto, CFOP, CST/`D1_CLASFIS`, TES, quantidade, total, ICMS/base/alíquota, IPI/base, ICMS ST, desconto | api-delpi |
| SF4 | código, crédito ICMS, livro ICMS, crédito IPI, livro IPI, material de consumo, cálculo de ICMS/IPI | api-delpi |
| SFT | documento, série, fornecedor/loja, item, valor ICMS/IPI creditado | api-delpi |
| SA2 | CNPJ e UF do fornecedor por código/loja | api-delpi |
| XML NF-e e CT-e | todos os documentos do período por CNPJ destinatário/tomador, com eventos de cancelamento | financial-api |
| Empresa | CNPJ e UF de cada filial (01, 02) | a inventariar |

**Lacuna conhecida:** a listagem atual de notas recebidas da financial-api (`ReceivedInvoiceQuery`) filtra por número, CNPJ do fornecedor e valor, **não por período**. A E0 precisa provar se o Questor permite listar por data de emissão/recebimento e CNPJ do destinatário. Se não permitir, D2 cai para upload do ZIP.


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
