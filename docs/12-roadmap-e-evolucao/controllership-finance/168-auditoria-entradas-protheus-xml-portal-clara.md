# 168 — Auditoria de entradas (Protheus × XML de NF-e e CT-e) no Portal e na CLARA

| Campo | Valor |
|---|---|
| Status | **PLAN_DRAFT** |
| Data | 2026-11-13 |
| Decisor | owner do produto |
| Baseline | HEAD `08825074` (somente leitura) |
| Origem | skill `auditoria-entradas-nfe-protheus` + painel «Raio-X das Entradas» (artifact no claude.ai) |
| Anexo | [168-anexos/skill-auditoria-entradas-nfe-protheus](./168-anexos/skill-auditoria-entradas-nfe-protheus/) — cópia da skill (SKILL.md, `references/regras.md`, `scripts/*.py`), sem a cópia da SF4 |

Este documento consolida o plano. Ele é discutido no chat e atualizado aqui a cada decisão. Nada de runtime começa antes do gate da fase E1 (contrato).

---

## 1. Objetivo

Levar para o Portal Controladoria & Finanças e para a CLARA a auditoria mensal das notas de entrada: o confronto do que foi escriturado no Protheus (SF1, SD1, SF4, SFT) com o XML do fornecedor (NF-e e CT-e). O foco é o mesmo da skill: pegar, antes da contabilidade, os erros que ela devolve todo mês (CT-e com crédito indevido ou não tomado, CFOP, CST e origem, base de ICMS/IPI, chave de acesso, CNPJ do fornecedor, espécie, série e data, Simples e crédito presumido de SC).

Resultado esperado:

1. **Página «Auditoria de entradas»** no Portal: escolher o período (De/Até) e as filiais, executar a auditoria, acompanhar o resultado num dashboard (o conteúdo do Raio-X) e marcar ocorrências como resolvidas.
2. **CLARA**: ler o resultado, analisar («o que pede ação em outubro na matriz?»), executar a auditoria e marcar resolvido, ampliando só o catálogo das tools semânticas existentes.

## 2. Situação atual (AS-IS)

| Etapa | Como é hoje |
|---|---|
| Dados do Protheus | exportação manual de SF1, SD1 (e às vezes SFT) em xlsx; SF4 guardada dentro da skill, com aviso quando passa de 90 dias |
| XML | download manual do ZIP de NF-e e CT-e |
| Regras | `scripts/regras.py` da skill (≈ 60 KB); catálogo em `references/regras.md` |
| Saída | planilha `cruzamento_entradas_filial<FF>_<mmmAAAA>.xlsx` |
| Acompanhamento | painel Raio-X: lê a planilha, guarda o histórico **por pessoa**, compara com o mês anterior, marca «resolvido» só para quem marcou |

Limites do AS-IS: trabalho manual a cada mês; SF4 pode estar desatualizada; sem SFT o crédito fica «Depende da TES»; o status de resolvido não é compartilhado pela equipe; a CLARA não enxerga nada disso.

## 3. Decisões

| ID | Tema | Decisão | Status |
|---|---|---|---|
| D1 | Onde fica o motor de regras | **controllership-finance-api (BFF)**, em Clean Architecture: regras puras no domain, fontes por adapters HTTP (api-delpi e financial-api) | recomendação — confirmar |
| D2 | Entrada dos dados | **Automática**: período + filiais → a BFF busca Protheus (api-delpi) e XML (financial-api/Questor). Upload de arquivos só como alternativa se a listagem do Questor por período não for viável (ver E0) | recomendação — confirmar |
| D3 | Visual | conteúdo do Raio-X no **padrão visual do Portal** (`@delpi/plugin-ui`, claro/escuro); sem copiar o HTML | **DECIDIDO** (owner, 2026-11-13) |
| D4 | Permissões | **`controllership-finance.access`** para tudo desta funcionalidade: ver, executar/reexecutar e marcar resolvido. `manage` herda `access`. Nenhuma permission nova | **DECIDIDO** (owner, 2026-11-13) |
| D5 | Navegação | página própria **«Auditoria de entradas»**, com atalho a partir do Fechamento mensal (abre já com o mês da competência) | recomendação — confirmar |
| D6 | CLARA executa a auditoria | a CLARA tem acesso a todas as funcionalidades e audita as notas **num comando do usuário**; `entry_audit.run`, `resolve` e `reopen` são diretos (sem prepare/confirmação) | **DECIDIDO** (owner, 2026-11-13); execução direta proposta — confirmar |
| D8 | Recorte da análise | **período livre (De/Até)** escolhido pelo usuário, no lugar da competência fixa; filiais e tipos de documento como filtros da execução; os demais como filtros da análise | **DECIDIDO** (owner, 2026-11-13) |
| D9 | Componentes | dashboard com `@delpi/plugin-ui`; primitivos novos criados no plugin-ui e importados pelo Portal; o HTML do Raio-X não é copiado | **DECIDIDO** (owner, 2026-11-13) |
| D7 | Execução | assíncrona, por um worker dentro da BFF (padrão do job de notificações no `lifespan`), uma análise por período com uma execução por filial | recomendação — confirmar |

## 4. Arquitetura (TARGET)

```
Protheus (SF1/SD1/SF4/SFT) ──► api-delpi (SQL canônico TOTVS, só leitura)
                                         │ HTTP
Questor (XML NF-e/CT-e) ──► financial-api ─┤
                                         ▼
     controllership-finance-api
       domain:       motor de regras (porte de regras.py), sem framework/HTTP/DB
       application:  executar auditoria (período, filiais), reexecutar, resolver/reabrir
       adapters:     api-delpi (entradas e TES), financial-api (XML), Postgres (resultado)
                 │                                   │
     MFE controllership-finance              CLARA (read / analyze / execute)
     «Auditoria de entradas»
```

Regras de fronteira (instruções do projeto):

- O MFE só fala com a BFF. A BFF fala com a api-delpi e a financial-api por HTTP; nunca acessa o banco do Protheus nem o banco vizinho.
- O SQL do Protheus fica na api-delpi (owner canônico TOTVS). A busca de XML fica na financial-api (owner do Questor).
- O motor de regras é domínio puro: recebe documentos normalizados (cabeçalho, itens, livro, TES, XML) e devolve ocorrências. Isso permite o teste de paridade com a skill sem rede.

## 4A. Estrutura do back-end (TARGET — revisar na E1)

### 4A.1 Fluxo de uma auditoria

1. Alguém pede a auditoria: botão na página **ou** um comando à CLARA («audita as entradas de outubro»).
2. A BFF cria uma **análise** (`entry_audit_analysis`: período, data de referência, filiais, tipos de documento, parâmetros) com uma **execução por filial** (`entry_audit_run`, status `queued`) e responde na hora com o identificador. Se já existe uma análise em andamento com os mesmos filtros de execução, devolve a mesma (idempotente).
3. Um **worker dentro da BFF** pega a execução. É o mesmo padrão do job de notificações que já roda no `lifespan` da BFF (`startup/notification_dispatch_job`).
4. O worker busca as fontes:
   - Protheus pela api-delpi: SF1, SD1, SF4, SFT e fornecedores (SA2) da filial no período (data de referência: recebimento, como a SF1 da skill);
   - XML pela financial-api: NF-e e CT-e da filial pela data de emissão, com folga antes do início do período para pegar notas emitidas antes e recebidas dentro dele, e os eventos de cancelamento. XML já baixado antes é reaproveitado do cache por chave de acesso, porque XML não muda.
5. O worker roda o **motor de regras** (domínio puro) e grava o resultado: notas casadas, ocorrências, notas sem par, CT-e, TES usadas.
6. O status de «resolvido» das ocorrências que continuam existindo é mantido pela **chave estável**.
7. A execução termina como `done` (ou `failed`, com o motivo). A página acompanha o andamento; a CLARA consulta o status e, ao terminar, apresenta o resultado.

### 4A.2 api-delpi — leitura do Protheus (owner TOTVS)

Prefixo no padrão dos relatórios financeiros: `/financeiro/entry-audit`. Só leitura, paginado, sem regra fiscal (a regra fica no motor da BFF).

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /financeiro/entry-audit/documents` | `branch`, `received_from`, `received_to`, `page`, `page_size` | cabeçalhos SF1 + CNPJ/UF do fornecedor (SA2) |
| `GET /financeiro/entry-audit/items` | mesmos filtros | itens SD1 dos mesmos documentos |
| `GET /financeiro/entry-audit/fiscal-book` | mesmos filtros | itens do livro fiscal (SFT) dos mesmos documentos |
| `GET /financeiro/entry-audit/tes` | — | cadastro de TES (SF4) inteiro |
| `GET /financeiro/entry-audit/branches` | — | filiais com CNPJ e UF |

A E0 confirma se já existe SQL reaproveitável para algum destes (há consultas de SF1/SD1 em compras e estoque).

### 4A.3 financial-api — XML do Questor (owner)

| Método e rota | Parâmetros | Retorna |
|---|---|---|
| `GET /invoices/received/export` | `branch`, `type` (`nfe` \| `cte`), `issued_from`, `issued_to`, `page`, `page_size` | lista com chave, número, série, emitente, emissão, valor, situação e os ids do provedor para baixar o XML |
| `GET /invoices/received/{id}/xml/original` | `branch`, `type` | XML original (já existe para CT-e e NFS-e; a NF-e usa `download_nfe_xml`) |

**Lacuna:** a listagem atual do Questor (`/cliente/nfe/listagem`) não recebe data. Ela vem ordenada por emissão (`orderGroup=Emission`) e só com entradas (`Entry=True`). A E0 prova se aceita filtro de data; se não aceitar, a financial-api pagina pela emissão e para quando passar do início do período. A entrada automática continua viável nos dois casos.

### 4A.4 controllership-finance-api — rotas da BFF

Prefixo `/entry-audit`. Todas exigem `controllership-finance.access` (D4). A unidade de trabalho é a **análise**: um período (De/Até) escolhido pelo usuário, as filiais e os tipos de documento. Cada análise tem uma execução por filial e fica guardada para acompanhamento.

**Execução e histórico**

| Método e rota | Uso |
|---|---|
| `POST /entry-audit/analyses` | body `{date_from, date_to, date_basis: "received", branches: ["01","02"], document_types: ["nfe","cte"], params: {presumed_credit_tes: "004", freight_cfop_suffix: "352"}}` → 202 com a análise criada (ou a que já está em andamento com os mesmos filtros) |
| `GET /entry-audit/analyses/options` | filiais permitidas (código, nome, UF) e padrões dos parâmetros avançados |
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

### 4A.5 Organização do código na BFF (Clean Architecture)

| Camada | Pasta | Conteúdo |
|---|---|---|
| domain | `domain/entry_audit/` | modelos (documento, item, livro, TES, XML NF-e/CT-e, ocorrência, severidade, tema); casamento SF1×XML (inclusive troca de chave) e SD1×itens; regras separadas por grupo (cabeçalho, itens, coerência, Simples/presumido SC, CT-e, chave/espécie/fornecedor, livro fiscal, sem par, «não apontado»); motor que junta tudo |
| application | `application/entry_audit/` | executar, consultar, resolver/reabrir, exportar; portas (`ProtheusEntriesPort`, `FiscalXmlPort`, `EntryAuditRepository`) |
| infrastructure | `infrastructure/entry_audit/` | gateway api-delpi, gateway financial-api, leitura dos XML (porte de `leitura.py`), repositório Postgres, cache de XML, exportação xlsx (porte de `relatorio.py`) |
| interface | `interface/http/routes/entry_audit/` · `interface/mcp/` | rotas HTTP; entradas da CLARA no catálogo semântico |
| startup | `startup/entry_audit_worker.py` | worker no `lifespan`; ao subir, devolve para a fila as execuções que estavam rodando quando o processo parou |

### 4A.6 Persistência

Migration `V023` no schema `controllership_finance`, com as tabelas da seção 7 e mais `entry_audit_xml_cache` (chave de acesso, modelo, XML compactado, data da busca).

### 4A.7 CLARA — «audita todas as notas» num comando

| Pedido do usuário | O que a CLARA faz |
|---|---|
| «Audita as entradas de outubro» | `execute entry_audit.run {date_from: 2026-10-01, date_to: 2026-10-31, branches: todas}` → recebe a análise; consulta `read entry_audit.analysis` até terminar; chama `analyze entry_audit_findings`; responde no formato da skill: o que pede ação, o que corrigir, o que não tem impacto |
| «Me explica o dashboard» | `read entry_audit.summary` + `breakdowns` + `daily` → explica os KPIs, a conformidade, os temas e os fornecedores que concentram ocorrências, e compara com o período anterior |
| «O que melhorou desde setembro?» | `read entry_audit.trend` + `analyze entry_audit_findings` → evolução e sugestão de direcionamento (por exemplo, cadastrar fornecedor no Configurador de Tributos, corrigir uma TES) |
| «O que ainda está pendente na matriz?» | `read entry_audit.occurrences {branch: 01, status: pending}` da última análise |
| «Por que essa CT-e deu alta?» | `read` da ocorrência + `knowledge` com a regra citada |
| «Marca a NF 123 da WEG como resolvida» | `execute entry_audit.resolve` |

A execução é **direta**, sem prepare/confirmação: não altera dado de negócio (só cria o resultado da auditoria), é idempotente por período e filiais e o owner quer que a CLARA faça o trabalho num comando só (D6). Resolver e reabrir também são diretos.

## 5. Ganhos em relação à skill

| Hoje | Com a plataforma |
|---|---|
| SF4 copiada na skill | SF4 lida ao vivo a cada execução |
| SFT quase nunca vem; muito «Depende da TES» | SFT lida ao vivo; o livro fiscal decide o crédito |
| ZIP de XML baixado à mão | XML buscado no Questor pela financial-api |
| Resolvido por pessoa, no navegador | Resolvido compartilhado, com quem resolveu e quando, preservado entre reexecuções |
| CLARA sem acesso | CLARA lê, analisa, executa e resolve |

## 6. Dados necessários (a confirmar na E0)

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

## 7. Persistência (TARGET, schema `controllership_finance`)

| Tabela | Conteúdo |
|---|---|
| `entry_audit_analysis` | período (De/Até), data de referência, filiais, tipos de documento, parâmetros, status agregado, quem pediu (usuário ou CLARA em nome do usuário), datas |
| `entry_audit_run` | uma por filial da análise: status (`queued`/`running`/`done`/`failed`), etapa e andamento, contagens, versão do motor, hash das fontes, erro |
| `entry_audit_document` | notas casadas (cabeçalho comparado), situação |
| `entry_audit_occurrence` | ocorrência: chave estável, severidade, tema, ocorrência, NF, fornecedor, item, campo, valor Protheus, valor XML, diferença, TES, por quê, ação sugerida, regra |
| `entry_audit_unmatched` | notas só no XML / só no SF1, com motivo e situação |
| `entry_audit_cte` | comparativo dos CT-e |
| `entry_audit_tes_used` | TES usadas na análise, com a configuração da SF4 |
| `entry_audit_status` | resolvido/reaberto por **chave estável** (independente do período), quem e quando |
| `entry_audit_xml_cache` | XML por chave de acesso (compactado), data da busca |

Uma reexecução substitui o resultado da filial, e o status de resolvido continua valendo pela chave estável.

## 8. Dashboard «Auditoria de entradas» (wireframes)

Wireframes completos: [168-anexos/wireframes-auditoria-entradas.html](./168-anexos/wireframes-auditoria-entradas.html). Detalhamento por página (dimensionamento, componentes e props, dados, estados): [168-paginas/](./168-paginas/00-indice-e-convencoes.md) — [01 Entrada e execução](./168-paginas/01-pagina-entrada-e-execucao.md), [02 Dashboard da análise](./168-paginas/02-pagina-dashboard-da-analise.md), [03 Detalhe da ocorrência](./168-paginas/03-pagina-detalhe-da-ocorrencia.md), [04 Componentes novos e evoluções do plugin-ui](./168-paginas/04-componentes-plugin-ui-novos-e-evolucoes.md). Família visual **analítica** do padrão dos Portais: PageHero → filtros → KPIs → gráficos → tabelas. O conteúdo vem do painel Raio-X; o HTML dele não é copiado.

```text
TopBar do Portal
PageHero compact ─ título, período, última execução, fontes   [Exportar] [Executar / Reexecutar]
└─ FilterBar
   ├─ Filtros da execução: Período (preset + De/Até), Data de referência, Filiais, Documentos, Parâmetros avançados
   └─ Filtros da análise: Severidade, Tema, Fornecedor, TES, Status, Limpar   (na URL; não reexecutam)
ScopeChipBar ─ filtros ativos removíveis
KPIs ×4 ─ Valor conferido · Notas sem divergência · Ocorrências pendentes · Diferença nas altas (com Δ vs período anterior)
Linha: Notas com divergência por dia (período × anterior)   |   Conformidade (medidor + legenda clicável)
Linha: Top 8 fornecedores                                    |   Ocorrências por tema (rosca + lista)
Linha: Por severidade | TES com mais ocorrências | Evolução entre análises
SectionCard ─ abas: Ocorrências | Notas casadas | Notas sem par | CT-e | TES usadas
   └─ Pendentes / Resolvidas / Todas · busca · colunas · tabela com Resolver/Reabrir · progresso · paginação
Pergunte à CLARA ─ sugestões prontas
Detalhe da ocorrência ─ painel lateral: valores, por quê, o que fazer, regra, documentos, Resolver
```

Estados: primeiro acesso (sem análise, com «Análises anteriores»), execução em andamento (etapas e progresso por filial), falha parcial (uma filial falhou, a outra concluiu), vazio por filtro. Mobile: KPIs em 2 colunas, gráficos empilhados, filtros num painel, tabela em cards.

Filtros vindos da skill e do painel: período (no lugar da competência fixa), filiais (matriz/filial, consolidado), severidade, tema, fornecedor, dia (clique no gráfico), status (pendente/resolvida), busca, mais tipo de documento e TES. Os parâmetros da skill (`--tes-presumido 004`, `--cfop-frete 352`) ficam em «Parâmetros avançados» com o padrão preenchido. `--cnpj`, `--uf` e `--filial` deixam de existir para o usuário: vêm do cadastro das filiais.

### 8.1 Componentes do `@delpi/plugin-ui`

Regra: componente novo nasce no `@delpi/plugin-ui`, genérico (sem «auditoria» no nome nem na API), e é importado pelo MFE. Evoluções são aditivas, com os padrões atuais preservados e testes de caracterização antes da mudança.

| Bloco | Componente | Situação | O que falta |
|---|---|---|---|
| Cabeçalho | `PageHero` (compact) | existe | — |
| Período | **`PeriodRangeFilter`** = `QuickPeriodSelector` + `DateField` ×2 | **novo** | composto genérico: preset + De/Até + rótulo da data de referência |
| Filtros | `FilterBar`, `FiltersRow`, `FilterSelectField`, `MultiSelectField`, `ClearFiltersButton` | existe | — |
| Filtros ativos | `ScopeChipBar` | evoluir | `onRemove` por chip e «Limpar tudo» |
| KPIs | `MetricKpiCard` + `TrendDelta` | existe | — |
| Por dia | `ChartCard` + `ComparativeAreaChart` | evoluir | `onPointSelect` e `selectedName` (clique no dia) |
| Conformidade | `SemicircleProgressGauge` | evoluir | legenda clicável |
| Top fornecedores / TES | `HorizontalValueBars` | evoluir | `tone` por item e item selecionado |
| Por tema | **`DistributionDonut`** (sobre `ChartSeriesPie`) | **novo** | rosca + lista com contagem/% e seleção |
| Severidade | `HorizontalValueBars` | evoluir | mesma evolução (tom e seleção), para filtrar por clique |
| Evolução | `LineSeriesChart` | existe | — |
| Abas e status | `UnderlineNav`, `SegmentToggle` | existe | — |
| Tabelas | `DataTableSection`, `StatusBadge`, `TablePaginationNav`, `DataRecordCard` (mobile) | existe | — |
| Resolver na linha | **`ResolutionStatusCell`** | **novo** | Resolver / «✓ data» / Reabrir, acessível, com estado de envio |
| Progresso resolvido | `ProgressSummaryBar` | existe | — |
| Execução | `StateBanner`, `ProgressTracker`, `InlineLoadingProgress` | existe | — |
| Detalhe | `DrawerShell`, `DetailCard`, `HelpTooltip` | existe | — |
| Vazio | `EmptyGuidance` | existe | — |

## 9. CLARA (só catálogo; sem tools novas)

| Tool | Entrada | Uso |
|---|---|---|
| `read` | `entry_audit.analysis` | análises (histórico) e o status/andamento de uma análise |
| `read` | `entry_audit.summary` / `entry_audit.daily` / `entry_audit.breakdowns` / `entry_audit.trend` | os mesmos números do dashboard, para a CLARA explicar o painel |
| `read` | `entry_audit.occurrences` | ocorrências com filtros (severidade, tema, fornecedor, status) |
| `read` | `entry_audit.unmatched` | notas sem par |
| `analyze` | `analysis_type=entry_audit_findings` | FACT/RECOMMENDATION agrupado por causa (TES, cadastro, fornecedor), no formato «o que pede ação / corrigir / sem impacto» da skill, com direcionamentos e comparação com análises anteriores |
| `execute` | `entry_audit.run` | executar/reexecutar a auditoria de um período (uma filial ou todas), **direto** (D6) |
| `execute` | `entry_audit.resolve` / `entry_audit.reopen` | marcar status (direto, baixo impacto) |
| `knowledge` | domínio Controladoria | catálogo de regras (`references/regras.md`) como conhecimento citável |

Gate de todas as entradas: `controllership-finance.access` (D4).

## 10. Fases

Regra de trabalho: teste de comportamento em HML; passou tudo, vai para PROD. Funcionalidade entra desligada por flag e é ligada depois do ensaio HML.

| Fase | Entrega | Saída |
|---|---|---|
| E0 | Inventário somente leitura: SQL existente na api-delpi para SF1/SD1/SF4/SFT/SA2; capacidade do Questor de listar por período e destinatário; CNPJ/UF das filiais; volume mensal por filial | lacuna do Questor resolvida ou D2 revista |
| E1 | Contrato: endpoints novos (api-delpi, financial-api, BFF), schema, catálogo CLARA, rotas do MFE | doc 168 com contrato `ACCEPTED` |
| E2 | Motor de regras no domain da BFF + **teste de paridade** com a skill sobre arquivos reais de um mês | paridade PASS |
| E3 | Fontes: endpoints de leitura na api-delpi; listagem por período na financial-api | testes de contrato PASS |
| E4 | Execução, persistência, reexecução com status preservado, exportação xlsx | testes PASS |
| E5 | Página no MFE + Ajuda | testes e build PASS |
| E6 | CLARA: catálogo, analyze, conhecimento | testes PASS |
| E7 | Ensaio HML com período real (outubro/2026, filiais 01 e 02) → PROD | paridade em HML + publicação |

## 11. Critério central de aceite: paridade

Para a mesma filial e período, com os mesmos dados de entrada, o motor da BFF produz **as mesmas ocorrências** que a skill: mesma nota, item, ocorrência, campo e severidade, e os mesmos valores (tolerância de R$ 0,05).

Diferenças só são aceitas quando explicadas pela fonte ao vivo e documentadas, por exemplo: SF4 mais nova que a cópia da skill; SFT presente decidindo um «Depende da TES».

## 12. Riscos

| Risco | Mitigação |
|---|---|
| Questor sem listagem por período | E0 prova; alternativa de upload (D2) |
| Volume (centenas de XML por mês) e tempo de execução | execução assíncrona com andamento; cache de XML por chave |
| Mapeamento da SFT nunca validado com dado real (aviso da própria skill) | E0/E2 com SFT real da Delpi |
| Regras da empresa («não apontado») se perderem no porte | paridade E2 inclui o bloco «Não apontado» do Resumo |
| Repositório público | o anexo traz só regras e scripts; a cópia da SF4 (cadastro de TES) não foi versionada |

## 13. Fora do escopo

Lançar ou corrigir notas no Protheus; alterar TES ou cadastro de fornecedor; substituir a contabilidade. A auditoria aponta e explica; a correção continua no ERP.

## 14. Registro

| Data | Evento |
|---|---|
| 2026-11-13 | Plano criado. D4 decidida pelo owner (tudo com `controllership-finance.access`). D1, D2, D3 e D5 com recomendação, aguardando confirmação. Skill anexada como referência para o porte. |
| 2026-11-13 | Detalhamento das páginas em `168-paginas/` (00 a 04): dimensionamento, componentes do plugin-ui com props, dados e estados; especificação dos 3 primitivos novos e das 4 evoluções aditivas (inclui `ComparativeAreaChart` com clique no dia). Rota nova `GET /entry-audit/analyses/options`. |
| 2026-11-13 | Dashboard: período livre (D8), plugin-ui com primitivos novos no kit (D9), D3 decidida. Rotas da BFF refeitas em torno da análise por período (§4A.4) e rotas do dashboard; persistência ajustada (§7); wireframes (§8 e anexo HTML); CLARA explica o dashboard e sugere direcionamentos. |
| 2026-11-13 | Estrutura do back-end (§4A): rotas da api-delpi, da financial-api e da BFF; organização em camadas; worker; cache de XML; CLARA executando a auditoria num comando (D6). Visual da página fica para a próxima rodada. Planejamento em tabela à parte (`planejamento-auditoria-entradas.xlsx`). |
