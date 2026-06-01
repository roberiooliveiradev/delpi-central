# Playbook — Especialista SQL Avançado do Minha DELPI Chat IA

> **Status de implementação:** Fases 1–7 na camada **chat base** (inteligência). Execução/schema via API ficam no **agente** (actions).

Projeto: Minha DELPI Chat IA
Escopo: tornar o **chat comum** um especialista SQL de alto nível (elaborar, revisar, explicar, otimizar); o **agente** herda a skill e **executa** via actions (`POST /data/sql`, `/system/tables/*`).

---

## 1.1 Chat base vs agente (regra de arquitetura)

| Camada | Papel SQL |
|--------|-----------|
| **Chat base** | Intenção, modos, dialeto, segurança, revisão, performance, padrões (CTE/window), workspace, policy, chips de orientação, métricas |
| **Agente** | Actions permitidas: executar SQL, buscar schema, interpretar resultado real do banco |

O chat base **não chama API diretamente**. Sem agente/actions, responde com SQL em ```sql```, explicações e perguntas de esclarecimento. Com agente, o pipeline **planeja** prefetch/execução; as tools rodam só se `actionsEnabled` + `allowedActionIds`.

Serviços do playbook na base (`ChatAdvancedSqlSpecialistService`, advisors, métricas) orientam o LLM e o operador — **não substituem** actions do agente.

---

## 1. Objetivo

Transformar o chat comum em um especialista SQL de alto nível, capaz de ajudar o usuário a construir, validar, executar, explicar, otimizar e evoluir consultas SQL em diferentes bancos de dados e contextos.

O chat deve ir além de gerar SELECT simples.

Ele deve ser capaz de apoiar o usuário em tarefas como:

- montar consultas SQL do zero;
- entender uma necessidade de negócio e converter em SQL;
- explorar schema;
- descobrir tabelas e colunas;
- validar relações entre tabelas;
- construir joins complexos;
- montar CTEs;
- montar subqueries;
- montar agregações;
- montar consultas analíticas;
- usar window functions;
- aplicar filtros dinâmicos;
- trabalhar com datas;
- criar rankings;
- calcular percentuais;
- montar pivot/unpivot quando suportado;
- detectar duplicidade;
- otimizar consulta;
- explicar query existente;
- revisar SQL enviado pelo usuário;
- executar consulta quando houver ferramenta segura;
- interpretar resultados;
- sugerir próximas consultas;
- permitir adicionar/remover colunas;
- transformar resultado em tabela, gráfico, KPI ou relatório.

---

## 2. Princípio central

O chat deve agir como um analista SQL sênior.

Regra principal:

SQL avançado no chat = entender a pergunta + conhecer o schema + escolher o dialeto + construir consulta correta + validar segurança + otimizar + interpretar resultado.

---

## 3. O que significa ser especialista SQL

Um especialista SQL no chat deve conseguir:

1. Traduzir linguagem natural em consulta SQL.
2. Perguntar apenas o que for indispensável.
3. Inferir a intenção analítica do usuário.
4. Identificar tabelas candidatas.
5. Validar colunas reais.
6. Escolher o melhor tipo de join.
7. Evitar duplicidade indesejada.
8. Aplicar filtros corretos.
9. Trabalhar com agregações e granularidade.
10. Usar CTEs para clareza.
11. Usar window functions para análises avançadas.
12. Gerar consultas paginadas e performáticas.
13. Detectar riscos de performance.
14. Explicar a consulta em linguagem simples.
15. Interpretar os resultados.
16. Sugerir próximos passos.

---

## 4. Diferença entre SQL simples e SQL especialista

### SQL simples

Exemplo:

SELECT * FROM produtos;

Problemas:

- sem filtro;
- sem limite;
- sem escolha de colunas;
- sem contexto;
- sem performance;
- sem explicação;
- sem validação;
- sem análise.

---

### SQL especialista

Exemplo de comportamento esperado:

Usuário:

Quero saber os clientes que mais compraram nos últimos 6 meses, comparando com os 6 meses anteriores.

Chat deve:

1. Identificar que é análise comparativa por cliente.
2. Descobrir tabelas de clientes e vendas.
3. Validar campos de data e valor.
4. Criar períodos atual e anterior.
5. Agregar por cliente.
6. Calcular variação absoluta e percentual.
7. Ordenar por maior crescimento.
8. Retornar resultado.
9. Explicar o cálculo.
10. Sugerir gráfico de barras ou linha.

---

## 5. Arquitetura recomendada

Criar uma arquitetura modular para a skill SQL avançada.

Serviços sugeridos:

- SqlIntentClassifier
- SqlDialectResolver
- SqlSchemaDiscoveryService
- SqlSemanticSchemaMapper
- SqlRelationshipResolver
- SqlQueryPlanner
- SqlColumnSelectionService
- SqlFilterBuilder
- SqlJoinBuilder
- SqlAggregationBuilder
- SqlWindowFunctionBuilder
- SqlQueryComposer
- SqlSafetyValidator
- SqlPerformanceAdvisor
- SqlExecutionService
- SqlResultAnalyzer
- SqlRevisionService
- SqlExplainService
- SqlVisualizationAdvisor
- SqlMemoryWorkspaceService

---

## 6. Pipeline completo

Fluxo recomendado:

Mensagem do usuário
→ detectar intenção SQL
→ identificar objetivo analítico
→ identificar banco/dialeto
→ identificar tabelas candidatas
→ validar schema
→ resolver relações
→ planejar consulta
→ escolher colunas
→ montar filtros
→ montar joins
→ montar agregações
→ aplicar CTEs/window functions, se necessário
→ validar segurança
→ validar performance
→ executar ou apresentar SQL
→ analisar resultado
→ sugerir refinamentos

---

## 7. Modos de operação

### 7.1 Modo criação

Usuário quer criar uma consulta do zero.

Exemplo:

Monte uma consulta para listar vendas por cliente nos últimos 3 meses.

---

### 7.2 Modo revisão

Usuário cola uma SQL e quer saber se está correta.

O chat deve verificar:

- sintaxe;
- joins;
- filtros;
- agregações;
- risco de duplicidade;
- performance;
- segurança;
- legibilidade;
- compatibilidade com dialeto.

---

### 7.3 Modo explicação

Usuário quer entender uma query.

O chat deve explicar:

- objetivo;
- tabelas;
- joins;
- filtros;
- agrupamentos;
- cálculos;
- ordenação;
- resultado esperado.

---

### 7.4 Modo otimização

Usuário quer melhorar performance.

O chat deve analisar:

- uso de SELECT *;
- filtros sem índice;
- funções em colunas filtradas;
- joins sem chave;
- subqueries desnecessárias;
- ordenações caras;
- agrupamentos grandes;
- ausência de paginação;
- CTEs mal usadas;
- possibilidade de índice.

---

### 7.5 Modo execução

Usuário quer executar a consulta.

O chat deve:

- validar segurança;
- validar permissões;
- aplicar limite quando necessário;
- executar via ferramenta autorizada;
- retornar resultado;
- interpretar resultado.

---

### 7.6 Modo exploração de schema

Usuário quer descobrir tabelas, colunas e relações.

Exemplos:

- Quais tabelas têm informação de cliente?
- Procure coluna relacionada a data de emissão.
- Quais colunas existem nessa tabela?
- Como relacionar pedidos com clientes?

---

### 7.7 Modo edição incremental

Usuário altera uma query anterior.

Exemplos:

- Adicione a coluna cidade.
- Remova valor líquido.
- Agrupe por mês.
- Agora filtre só clientes ativos.
- Ordene por maior faturamento.
- Transforme em ranking.
- Faça comparação com ano anterior.

---

## 8. Detecção de intenção SQL

Ativar quando o usuário usar termos como:

- SQL;
- consulta;
- query;
- banco;
- tabela;
- coluna;
- schema;
- join;
- agrupar;
- filtrar;
- ordenar;
- contar;
- somar;
- média;
- ranking;
- variação;
- comparar períodos;
- executar consulta;
- trazer dados;
- otimizar query;
- explicar query;
- revisar SELECT.

---

## 9. Não ativar SQL quando

Não usar SQL quando:

- pedido é correção de texto comum;
- pedido é tradução;
- pedido é e-mail;
- pedido é resumo sem dados;
- existe uma API pronta melhor;
- é apenas pergunta conceitual simples;
- envolve alteração de dados sem autorização;
- envolve comando destrutivo;
- usuário pediu explicitamente para não executar;
- não há permissão para acessar dados.

---

## 10. Resolução de dialeto SQL

O chat deve identificar ou perguntar o dialeto quando necessário.

Dialetos possíveis:

- PostgreSQL;
- SQL Server / T-SQL;
- MySQL;
- MariaDB;
- SQLite;
- Oracle SQL;
- BigQuery SQL;
- Snowflake SQL;
- Redshift SQL;
- Databricks SQL;
- DuckDB;
- ANSI SQL genérico.

Se o usuário não informar o banco:

- usar dialeto padrão configurado no projeto;
- ou gerar SQL ANSI genérico;
- ou perguntar quando a sintaxe depender do banco.

Exemplo:

Para montar a query corretamente, preciso saber o banco: SQL Server, PostgreSQL, MySQL ou outro?

Perguntar apenas se a diferença de dialeto afetar a consulta.

---

## 11. Diferenças de dialeto que o chat deve conhecer

### Limite de registros

SQL Server:

SELECT TOP 10 ...

PostgreSQL/MySQL/SQLite:

SELECT ...
LIMIT 10

Oracle:

FETCH FIRST 10 ROWS ONLY

---

### Datas

SQL Server:

DATEADD(month, -6, GETDATE())

PostgreSQL:

CURRENT_DATE - INTERVAL '6 months'

MySQL:

DATE_SUB(CURDATE(), INTERVAL 6 MONTH)

BigQuery:

DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)

---

### Concatenação

SQL Server:

CONCAT(a, b)

PostgreSQL:

a || b

MySQL:

CONCAT(a, b)

---

### Conversão de tipo

SQL Server:

CAST(valor AS DECIMAL(18,2))

PostgreSQL:

valor::numeric

ANSI:

CAST(valor AS DECIMAL(18,2))

---

### Tratamento de nulo

SQL Server:

ISNULL(campo, 0)

PostgreSQL/MySQL/Oracle:

COALESCE(campo, 0)

Preferir COALESCE quando possível.

---

## 12. Segurança

A skill SQL deve ser segura por padrão.

Permitir:

- SELECT;
- WITH;
- CTE;
- EXPLAIN, quando permitido;
- DECLARE/SET apenas se seguro e suportado;
- funções de agregação;
- window functions;
- subqueries de leitura.

Bloquear:

- INSERT;
- UPDATE;
- DELETE;
- DROP;
- ALTER;
- TRUNCATE;
- MERGE;
- CREATE;
- EXEC;
- CALL;
- GRANT;
- REVOKE;
- BEGIN TRAN;
- COMMIT;
- ROLLBACK;
- comandos administrativos;
- leitura de tabelas sensíveis sem permissão.

Resposta para bloqueio:

Essa operação foi bloqueada por segurança. Posso ajudar a montar uma consulta de leitura para analisar os dados, mas não executar alterações no banco.

---

## 13. Validador de segurança

Criar:

SqlSafetyValidator

Checklist:

[ ] A query é somente leitura?
[ ] Não contém comando destrutivo?
[ ] Não contém execução dinâmica perigosa?
[ ] Tabelas são permitidas?
[ ] Colunas são permitidas?
[ ] Há limite/paginação quando necessário?
[ ] Não expõe dados sensíveis sem permissão?
[ ] Não usa SELECT * em tabelas grandes?
[ ] Não contém múltiplos statements perigosos?
[ ] Não tenta burlar filtros de segurança?

---

## 14. Exploração de schema

O especialista deve conseguir explorar o schema.

Recursos esperados:

- listar tabelas;
- buscar tabela por nome;
- buscar tabela por descrição semântica;
- listar colunas;
- buscar coluna por nome;
- buscar coluna por significado;
- obter tipos de dados;
- identificar chaves primárias;
- identificar chaves estrangeiras;
- identificar índices;
- identificar cardinalidade;
- identificar relações prováveis;
- identificar campos de data;
- identificar campos numéricos;
- identificar campos categóricos;
- identificar colunas sensíveis.

---

## 15. Mapeamento semântico de schema

Criar:

SqlSemanticSchemaMapper

Objetivo:

Mapear linguagem do usuário para tabelas e colunas reais.

Exemplos:

| Usuário fala | Possíveis campos |
|---|---|
| cliente | customer_id, client_id, cod_cliente |
| nome do cliente | customer_name, nome_cliente |
| valor vendido | total_amount, sales_value, valor_total |
| data da venda | sale_date, emission_date, data_emissao |
| status | status, state, situation |
| vendedor | seller_id, sales_rep_id |
| produto | product_id, sku, item_code |
| quantidade | quantity, qty, qtd |
| margem | margin, profit_margin |
| cidade | city, municipio |

O mapeamento deve considerar:

- nome da coluna;
- descrição;
- tipo;
- tabela;
- relações;
- frequência de uso;
- exemplos do projeto;
- histórico da conversa.

---

## 16. Resolução de relações

Criar:

SqlRelationshipResolver

Deve identificar:

- joins por FK declarada;
- joins por convenção de nomes;
- joins já homologados;
- joins inferidos com baixa confiança;
- relação 1:1;
- relação 1:N;
- relação N:N;
- tabela ponte;
- risco de duplicidade.

Exemplo:

Pedidos → Clientes:

orders.customer_id = customers.id

Pedidos → Itens:

orders.id = order_items.order_id

Produtos → Itens:

products.id = order_items.product_id

---

## 17. Tipos de joins

O chat deve escolher corretamente:

### INNER JOIN

Usar quando precisa apenas registros com correspondência nas duas tabelas.

### LEFT JOIN

Usar quando precisa manter registros da tabela principal mesmo sem correspondência.

### RIGHT JOIN

Evitar, preferir reescrever com LEFT JOIN.

### FULL OUTER JOIN

Usar para conciliação ou comparação entre bases.

### CROSS JOIN

Usar raramente, apenas quando intencional.

### SEMI JOIN / EXISTS

Usar para verificar existência sem duplicar linhas.

### ANTI JOIN / NOT EXISTS

Usar para encontrar registros sem correspondência.

---

## 18. Evitar duplicidade

O chat deve detectar risco de duplicidade em joins 1:N.

Exemplo:

Clientes x Pedidos x Itens pode multiplicar linhas.

Estratégias:

- agregar antes de fazer join;
- usar CTE por nível de granularidade;
- usar DISTINCT apenas quando fizer sentido;
- usar EXISTS para existência;
- separar consulta detalhada de consulta agregada.

Alerta recomendado:

Atenção: esse join pode multiplicar registros porque um cliente pode ter vários pedidos. Para evitar distorção, vou agregar os pedidos antes de juntar com clientes.

---

## 19. Granularidade

Antes de montar SQL, o chat deve identificar o nível de detalhe.

Exemplos:

- por cliente;
- por pedido;
- por item do pedido;
- por produto;
- por mês;
- por filial;
- por vendedor;
- por status.

Regra:

Não misturar campos de detalhe com agregações sem ajustar GROUP BY.

Pergunta quando necessário:

Você quer o resultado detalhado por nota/pedido ou resumido por cliente?

---

## 20. Seleção de colunas

O chat deve permitir:

- adicionar coluna;
- remover coluna;
- renomear coluna;
- reordenar coluna;
- ocultar coluna técnica;
- criar coluna calculada;
- trocar coluna equivalente;
- escolher colunas por categoria.

Exemplos:

- adicione cidade do cliente;
- remova ID interno;
- inclua mês;
- crie coluna de percentual;
- adicione ticket médio;
- traga só cliente, valor e data;
- tire colunas nulas.

---

## 21. Colunas calculadas

O especialista deve montar cálculos como:

- total = quantidade * preço;
- margem = receita - custo;
- margem percentual = margem / receita;
- ticket médio = valor total / número de pedidos;
- variação = atual - anterior;
- variação percentual = (atual - anterior) / anterior;
- participação = valor / total geral;
- idade = data atual - data nascimento;
- atraso = data entrega - data prevista;
- saldo = entradas - saídas.

Sempre tratar divisão por zero.

Exemplo:

CASE
  WHEN valor_anterior = 0 THEN NULL
  ELSE (valor_atual - valor_anterior) / valor_anterior
END AS variacao_percentual

---

## 22. Filtros

O chat deve montar filtros claros.

Tipos:

- igualdade;
- intervalo;
- lista;
- texto contém;
- começa com;
- data relativa;
- status;
- nulo/não nulo;
- faixa numérica;
- top N;
- exclusão.

Regras:

- filtros de data devem ser sargable quando possível;
- evitar função aplicada na coluna filtrada;
- preferir intervalo:
  campo_data >= início AND campo_data < fim

Evitar:

WHERE YEAR(data) = 2026

Preferir:

WHERE data >= '2026-01-01'
  AND data < '2027-01-01'

---

## 23. Datas e períodos

O chat deve entender:

- hoje;
- ontem;
- esta semana;
- semana passada;
- este mês;
- mês passado;
- últimos 7 dias;
- últimos 30 dias;
- trimestre atual;
- ano atual;
- ano passado;
- entre duas datas;
- mês fechado;
- acumulado do ano;
- últimos 12 meses.

Deve perguntar se houver ambiguidade:

Quando você diz “mês fechado”, deseja o último mês completo ou o mês atual até ontem?

---

## 24. Agregações

O especialista deve usar:

- COUNT;
- COUNT DISTINCT;
- SUM;
- AVG;
- MIN;
- MAX;
- MEDIAN, se suportado;
- percentis, se suportado;
- GROUP BY;
- HAVING.

Deve saber diferenciar:

- contar registros;
- contar entidades distintas;
- somar valores;
- média simples;
- média ponderada.

Exemplo:

Ticket médio:

SUM(valor_total) / COUNT(DISTINCT pedido_id)

Preço médio ponderado:

SUM(valor_total) / NULLIF(SUM(quantidade), 0)

---

## 25. Window functions

O especialista deve saber usar funções analíticas.

Exemplos:

- ROW_NUMBER;
- RANK;
- DENSE_RANK;
- LAG;
- LEAD;
- SUM() OVER;
- AVG() OVER;
- COUNT() OVER;
- FIRST_VALUE;
- LAST_VALUE;
- NTILE;
- PERCENT_RANK.

Usos:

- ranking por grupo;
- variação mês contra mês;
- acumulado;
- média móvel;
- deduplicação;
- selecionar último registro por entidade;
- top N por categoria;
- comparar linha atual com anterior.

Exemplo:

ROW_NUMBER() OVER (
  PARTITION BY cliente_id
  ORDER BY data_pedido DESC
) AS rn

---

## 26. CTEs

Usar CTEs para:

- organizar lógica;
- separar etapas;
- evitar subqueries difíceis;
- agregar antes de juntar;
- calcular períodos;
- deduplicar;
- melhorar legibilidade.

Exemplo de estrutura:

WITH vendas_base AS (...),
vendas_cliente AS (...),
ranking AS (...)
SELECT ...
FROM ranking
WHERE posicao <= 10;

---

## 27. Subqueries

Usar quando:

- filtro depende de outra consulta;
- existe/não existe relação;
- precisa calcular total global;
- precisa comparar com média geral.

Preferir EXISTS para existência:

WHERE EXISTS (
  SELECT 1
  FROM pedidos p
  WHERE p.cliente_id = c.id
)

Evitar IN com subquery grande quando EXISTS é melhor.

---

## 28. Pivots e relatórios cruzados

O chat deve conseguir montar relatórios como:

- vendas por mês em colunas;
- status por categoria;
- filial x mês;
- cliente x produto;
- ano atual x ano anterior.

Se o banco não suportar PIVOT, usar agregação condicional:

SUM(CASE WHEN mes = 1 THEN valor ELSE 0 END) AS jan

---

## 29. Comparação entre períodos

O chat deve montar:

- período atual;
- período anterior;
- variação absoluta;
- variação percentual;
- ranking por crescimento;
- ranking por queda.

Exemplo:

Usuário:

Compare vendas deste mês com mês passado por cliente.

Saída:

- cliente;
- valor atual;
- valor anterior;
- diferença;
- variação %.

---

## 30. Análise de coorte

Quando aplicável, o especialista pode ajudar com:

- clientes por mês de primeira compra;
- retenção;
- recompra;
- churn;
- tempo até recompra.

Deve avisar que precisa de:

- identificador do cliente;
- data do evento;
- métrica de atividade.

---

## 31. Deduplicação

O chat deve saber deduplicar por:

- último registro;
- maior valor;
- menor data;
- primeiro evento;
- status mais recente;
- combinação de chaves.

Exemplo:

Selecionar última compra por cliente:

ROW_NUMBER() OVER (
  PARTITION BY cliente_id
  ORDER BY data_compra DESC
) = 1

---

## 32. Controle de nulos

Sempre considerar nulos.

Usar:

- COALESCE;
- NULLIF;
- IS NULL;
- IS NOT NULL;
- CASE WHEN.

Exemplos:

COALESCE(valor, 0)

valor / NULLIF(total, 0)

---

## 33. CASE WHEN

Usar para:

- classificar status;
- criar faixas;
- traduzir códigos;
- criar flags;
- separar categorias.

Exemplo:

CASE
  WHEN valor >= 10000 THEN 'Alto'
  WHEN valor >= 1000 THEN 'Médio'
  ELSE 'Baixo'
END AS faixa_valor

---

## 34. Qualidade dos dados

O especialista deve detectar:

- nulos em campos importantes;
- duplicidades;
- registros órfãos;
- datas inválidas;
- valores negativos;
- valores zerados;
- status desconhecidos;
- categorias inconsistentes;
- chaves sem correspondência;
- outliers.

E sugerir consultas diagnósticas.

Exemplo:

Posso verificar se existem pedidos sem cliente relacionado.

---

## 35. Performance

O chat deve avaliar riscos de performance.

Problemas comuns:

- SELECT *;
- tabela grande sem filtro;
- ORDER BY sem necessidade;
- função na coluna do WHERE;
- LIKE '%texto%' em tabela grande;
- join sem chave;
- CTE materializada em alguns bancos;
- subquery correlacionada pesada;
- DISTINCT usado para mascarar duplicidade;
- OR excessivo;
- falta de índices;
- retorno muito grande.

---

## 36. Boas práticas de performance

Preferir:

- selecionar apenas colunas necessárias;
- aplicar filtros cedo;
- limitar resultados;
- agregar antes do join;
- usar EXISTS para existência;
- usar intervalo de datas sargable;
- evitar função em coluna filtrada;
- usar índices disponíveis;
- paginar;
- separar relatório pesado em etapas.

---

## 37. Sugestão de índices

Quando o usuário pedir otimização, o chat pode sugerir índices conceituais.

Exemplo:

Para essa consulta, um índice em (cliente_id, data_pedido) pode ajudar, pois esses campos são usados em filtro e join.

Mas deve avisar:

A criação de índice deve ser avaliada por DBA, pois pode impactar escrita e armazenamento.

---

## 38. EXPLAIN / Plano de execução

Quando disponível, permitir:

- gerar EXPLAIN;
- interpretar plano;
- identificar scan;
- identificar join caro;
- identificar sort;
- identificar uso de índice;
- sugerir ajuste.

Não executar EXPLAIN se a ferramenta não permitir.

---

## 39. Resultado e inferência

Após executar, o chat deve:

- resumir quantos registros retornaram;
- informar filtros aplicados;
- indicar limitações;
- mostrar tabela;
- analisar padrões;
- identificar maiores/menores;
- detectar nulos;
- sugerir próximos passos;
- sugerir visualização.

Exemplo:

Análise:
- O cliente X aparece com maior faturamento.
- Os três primeiros clientes concentram 62% do total retornado.
- O resultado está limitado ao TOP 10.
- Posso gerar gráfico de barras ou comparar com o período anterior.

---

## 40. Visualização recomendada

| Resultado | Visualização |
|---|---|
| ranking | barra horizontal |
| dados temporais | linha |
| participação | rosca |
| indicador único | KPI |
| tabela detalhada | tabela |
| comparação | barras agrupadas |
| matriz | heatmap |
| hierarquia | árvore |
| pendências | checklist |
| relatório | lousa |

---

## 41. Resposta padrão após execução

Consulta executada com sucesso.

Resumo:
- Registros retornados: [n]
- Período: [período, se houver]
- Filtros aplicados: [filtros]
- Ordenação: [ordenação]
- Limite: [limite]
- Fonte: [fonte]
- Status da execução: sucesso

Resultado:

[tabela]

Análise:
- [insight 1]
- [insight 2]
- [limitação]

Próximos passos:
- Adicionar coluna
- Remover coluna
- Agrupar
- Ordenar
- Gerar gráfico
- Exportar
- Explicar SQL
- Colocar na lousa

---

## 42. Resposta padrão ao gerar SQL sem executar

Montei a consulta abaixo para o objetivo solicitado.

Objetivo:
[explicação]

SQL:
[query]

Observações:
- [limitação]
- [assunção]
- [risco de duplicidade, se houver]

Posso:
- executar;
- explicar;
- otimizar;
- adicionar colunas;
- adaptar para outro banco.

---

## 43. Edição incremental da query

O chat deve manter um workspace da consulta.

Estado recomendado:

{
  "sqlWorkspace": {
    "dialect": "postgresql",
    "objective": "ranking de vendas por cliente",
    "baseTables": ["orders", "customers"],
    "selectedColumns": [],
    "filters": [],
    "joins": [],
    "groupBy": [],
    "orderBy": [],
    "limit": 10,
    "lastSql": "",
    "lastResultSchema": [],
    "lastResultSummary": {}
  }
}

---

## 44. Ações incrementais suportadas

O usuário pode pedir:

- adicione coluna;
- remova coluna;
- troque filtro;
- mude período;
- adicione agrupamento;
- remova agrupamento;
- ordene diferente;
- mude TOP/LIMIT;
- traga totais;
- adicione percentual;
- compare com período anterior;
- gere CTE;
- transforme em subquery;
- otimize;
- explique;
- execute.

---

## 45. Exemplo de edição incremental

Usuário:

Liste vendas por cliente este mês.

Chat:

[monta e executa]

Usuário:

Adicione cidade.

Chat:

- verifica se cidade está na tabela de clientes;
- adiciona coluna;
- ajusta GROUP BY;
- executa novamente;
- explica alteração.

Resposta:

Adicionei a cidade do cliente e mantive o agrupamento por cliente. Como cidade é uma dimensão, ela também entrou no GROUP BY.

---

## 46. Tratamento de erro

### Coluna inexistente

A coluna solicitada não foi encontrada no schema validado.

Posso:
- buscar coluna equivalente;
- listar colunas da tabela;
- remover a coluna;
- ajustar a consulta.

---

### Tabela inexistente

Não encontrei essa tabela no schema disponível.

Posso:
- buscar por nome parecido;
- buscar por descrição;
- listar tabelas relacionadas;
- usar outra tabela.

---

### Join ambíguo

Existem múltiplas formas possíveis de relacionar essas tabelas.

Você prefere relacionar por:
- cliente;
- pedido;
- produto;
- filial;
- chave composta?

---

### Resultado grande demais

O resultado ficou grande demais.

Posso:
- aplicar limite;
- paginar;
- agrupar;
- filtrar por período;
- retornar apenas resumo.

---

### Query lenta

A consulta parece pesada.

Sugestões:
- reduzir período;
- selecionar menos colunas;
- aplicar filtros antes;
- agregar antes do join;
- verificar índices;
- executar versão resumida.

---

## 47. Explicação da query

Quando o usuário pedir “explique”, responder:

## Objetivo

Essa consulta busca...

## Tabelas usadas

- tabela A: papel
- tabela B: papel

## Relações

- A.id = B.a_id

## Filtros

- período...
- status...

## Agregações

- soma...
- contagem...

## Ordenação

- maior valor primeiro...

## Cuidados

- risco de duplicidade...
- limitação...

---

## 48. Revisão de query colada pelo usuário

Checklist:

[ ] Sintaxe parece correta?
[ ] Dialeto está claro?
[ ] SELECT * é necessário?
[ ] Joins estão corretos?
[ ] Filtros estão no lugar certo?
[ ] Datas estão eficientes?
[ ] GROUP BY está coerente?
[ ] HAVING está correto?
[ ] ORDER BY é necessário?
[ ] Há risco de duplicidade?
[ ] Há risco de performance?
[ ] Há comandos proibidos?
[ ] Há forma mais simples?

---

## 49. Geração de SQL complexo

O especialista deve ser capaz de criar:

- CTEs encadeadas;
- subqueries;
- joins múltiplos;
- agregações condicionais;
- ranking por grupo;
- comparação período atual x anterior;
- acumulado no ano;
- média móvel;
- top N por categoria;
- deduplicação por linha mais recente;
- detecção de registros órfãos;
- análise de coorte;
- análise ABC;
- pivot por mês;
- cálculos de SLA;
- funil de conversão;
- retenção;
- churn;
- gap analysis.

---

## 50. Exemplos de SQL avançado que deve suportar

### Top N por grupo

Usar ROW_NUMBER ou RANK.

### Comparação mês contra mês

Usar agregação por mês + LAG.

### Participação percentual

Usar SUM(valor) / SUM(SUM(valor)) OVER ().

### Acumulado

Usar SUM(valor) OVER (ORDER BY data).

### Último registro por entidade

Usar ROW_NUMBER PARTITION BY entidade ORDER BY data DESC.

### Registros sem correspondência

Usar LEFT JOIN + IS NULL ou NOT EXISTS.

### Média móvel

Usar AVG(valor) OVER (ORDER BY data ROWS BETWEEN 2 PRECEDING AND CURRENT ROW).

---

## 51. Prompt interno recomendado

Você é um especialista SQL sênior do Minha DELPI Chat IA.

Sua função é ajudar o usuário a construir, revisar, explicar, otimizar, executar e interpretar consultas SQL.

Regras obrigatórias:

1. Entenda a intenção antes de gerar SQL.
2. Identifique o dialeto SQL ou use padrão configurado.
3. Valide schema antes de usar tabelas/colunas não conhecidas.
4. Não invente tabela, coluna, relação ou regra de cálculo.
5. Prefira APIs prontas quando forem mais seguras que SQL.
6. Gere SQL somente leitura por padrão.
7. Bloqueie comandos destrutivos ou administrativos.
8. Evite SELECT * em tabelas grandes.
9. Use filtros e limites seguros.
10. Escolha joins considerando granularidade e duplicidade.
11. Use CTEs para consultas complexas.
12. Use window functions quando forem a melhor solução.
13. Trate nulos e divisão por zero.
14. Explique limitações e assunções.
15. Após executar, interprete os resultados.
16. Sugira próximos passos úteis.
17. Permita adicionar/remover colunas mantendo a query atual.
18. Em erro, explique e ofereça recuperação.
19. Diferencie certeza de indício.
20. Não atribua causa raiz sem dados suficientes.

---

## 52. Testes de regressão

Criar:

test_advanced_sql_specialist.py

Casos mínimos:

| Caso | Entrada | Esperado |
|---|---|---|
| SQL1 | criar SELECT simples | query segura |
| SQL2 | usuário não informa banco | pergunta ou usa padrão |
| SQL3 | adicionar coluna | ajusta SELECT/GROUP BY |
| SQL4 | remover coluna | mantém filtro |
| SQL5 | comparar períodos | cria CTEs |
| SQL6 | ranking por grupo | usa window function |
| SQL7 | top N por categoria | usa ROW_NUMBER/RANK |
| SQL8 | último registro | usa ROW_NUMBER |
| SQL9 | variação percentual | trata divisão por zero |
| SQL10 | join 1:N | alerta duplicidade |
| SQL11 | comando DELETE | bloqueia |
| SQL12 | SELECT * grande | sugere colunas |
| SQL13 | coluna inexistente | valida schema |
| SQL14 | resultado vazio | sugere recuperação |
| SQL15 | query lenta | sugere otimização |
| SQL16 | explicar SQL | explica partes |
| SQL17 | revisar SQL | aponta riscos |
| SQL18 | executar SQL | valida e executa |
| SQL19 | inferir resultado | gera análise |
| SQL20 | gerar gráfico | escolhe visualização |

---

## 53. Métricas

Medir:

- consultas SQL geradas;
- consultas SQL executadas;
- consultas bloqueadas;
- revisões de SQL;
- explicações de SQL;
- otimizações sugeridas;
- erros de schema;
- erros de execução;
- uso de CTE;
- uso de window function;
- edição incremental;
- colunas adicionadas/removidas;
- resultados interpretados;
- feedback de acerto;
- feedback de erro;
- tempo médio de execução;
- queries lentas;
- consultas convertidas em gráfico/lousa.

---

## 54. Feedback específico

Adicionar motivos:

- SQL incorreto;
- tabela errada;
- coluna errada;
- join errado;
- filtro errado;
- agrupamento errado;
- resultado duplicado;
- performance ruim;
- não entendeu intenção;
- não explicou query;
- não interpretou resultado;
- inferência sem base;
- faltou próxima ação;
- deveria ter perguntado;
- perguntou demais;
- deveria ter usado API;
- deveria ter usado SQL.

---

## 55. Roadmap de implementação

### Fase 1 — Skill SQL segura

- Detectar intenção SQL.
- Gerar SELECT seguro.
- Bloquear comandos perigosos.
- Aplicar limite.
- Explicar consulta.

### Fase 2 — Schema inteligente

- Explorar tabelas.
- Explorar colunas.
- Mapear termos do usuário.
- Resolver relações.
- Validar colunas.

### Fase 3 — SQL avançado

- CTEs.
- Window functions.
- Comparação de períodos.
- Rankings.
- Deduplicação.
- Percentuais.
- Pivots.

### Fase 4 — Workspace interativo

- Memória da query.
- Adicionar/remover colunas.
- Alterar filtros.
- Agrupar.
- Ordenar.
- Mostrar SQL.

### Fase 5 — Execução e análise

- Executar via ferramenta segura.
- Interpretar resultados.
- Detectar anomalias.
- Sugerir próximos passos.
- Gerar gráficos.

### Fase 6 — Otimização

- Performance advisor.
- EXPLAIN.
- Sugestão de índices.
- Diagnóstico de duplicidade.
- Refatoração.

### Fase 7 — Observabilidade

- Métricas.
- Feedback.
- Testes.
- Dashboard de qualidade.

---

## 56. Anti-padrões

Evitar:

1. Gerar SELECT * sem necessidade.
2. Inventar tabela.
3. Inventar coluna.
4. Ignorar dialeto.
5. Ignorar granularidade.
6. Usar DISTINCT para esconder join errado.
7. Misturar agregação com detalhe sem critério.
8. Não tratar divisão por zero.
9. Não tratar nulos.
10. Não limitar consulta ampla.
11. Executar comando destrutivo.
12. Afirmar causa sem dados.
13. Ignorar resultado vazio.
14. Não explicar erro.
15. Não sugerir próximo passo.
16. Não permitir edição incremental.
17. Usar SQL quando API pronta é melhor.
18. Otimizar sem entender objetivo.
19. Confundir filtro WHERE e HAVING.
20. Usar função em coluna de data no WHERE sem necessidade.

---

## 57. Resultado esperado

Depois da implementação, o chat deve ser capaz de atuar como um especialista SQL universal.

Ele deve:

- montar SQL simples e complexo;
- adaptar ao dialeto do banco;
- validar schema;
- construir joins corretos;
- evitar duplicidade;
- montar CTEs;
- usar window functions;
- criar rankings;
- comparar períodos;
- calcular percentuais;
- explicar queries;
- revisar queries;
- otimizar queries;
- executar com segurança;
- interpretar resultados;
- sugerir gráficos e próximos passos;
- permitir edição incremental.

---

## 58. Resumo executivo

A skill SQL atual não deve ser apenas um gerador simples de SELECT.

Ela deve evoluir para um copiloto SQL avançado, capaz de entender dados, schema, dialeto, intenção, performance e resultado.

Regra final:

Um especialista SQL não entrega apenas query. Ele entrega uma análise confiável, segura e evolutiva.