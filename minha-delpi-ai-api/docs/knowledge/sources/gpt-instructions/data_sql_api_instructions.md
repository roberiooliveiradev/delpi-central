# 🧩 Guia de Uso da Rota `/data/sql`

## 📘 Descrição

A rota `/data/sql` permite a **execução controlada de SQL puro (T-SQL)**, enviadas em **formato JSON**, com **validação de segurança completa**,
Ela funciona como uma camada segura de leitura sobre o banco TOTVS Protheus (SQL Server), permitindo consultas avançadas sem expor DDL/DML ou risco de execução arbitrária, incluindo:

-   Verificação de **tabelas permitidas** (`allowed_tables.json`);
-   Bloqueio de **comandos DML e DDL** (`UPDATE`, `DELETE`, `DROP`, etc.);
-   Suporte a **CTEs e CTEs recursivas** (`WITH` e `WITH RECURSIVE`);
-   Compatibilidade com **SQL Server (T-SQL)**.

Principais capacidades

-   ✅ Execução de SELECTs simples ou múltiplos SELECTs
-   ✅ Suporte a DECLARE, SET e variáveis escalares
-   ✅ Suporte a CTEs (WITH), inclusive múltiplas CTEs
-   ✅ Suporte a comentários SQL (-- e /* ... */)
-   ✅ Validação de tabelas físicas via whitelist
-   ❌ Bloqueio total de DML, DDL, EXEC e transações

> ⚠️ Esta rota deve ser usada **apenas por agentes técnicos homologados** (nível de automação avançado).  
> O usuário humano nunca deve visualizar ou editar diretamente o SQL enviado.

---

## ⚙️ Método e Endpoint

| Método | Endpoint    | Autenticação         | Tipo de Body       |
| ------ | ----------- | -------------------- | ------------------ |
| `POST` | `/data/sql` | 🔐 Requer JWT válido | `application/json` |

---

## 🧱 Corpo da Requisição

O corpo deve conter o SQL dentro de um objeto JSON, conforme abaixo:

### ✅ Exemplo correto


```json
{
    "sql": "WITH hierarchy AS (SELECT B1_COD, B1_GRUPO, 0 AS LEVEL FROM SB1010 WHERE B1_GRUPO = '1008' UNION ALL SELECT p.B1_COD, p.B1_GRUPO, h.LEVEL + 1 FROM SB1010 p JOIN hierarchy h ON p.B1_GRUPO = h.B1_COD) SELECT * FROM hierarchy;"
}
```

### ❌ Exemplo incorreto

```sql
WITH hierarchy AS (
    SELECT B1_COD, B1_GRUPO, 0 AS LEVEL
    FROM SB1010
)
SELECT * FROM hierarchy;
```

> OBS: Remova qualquer comentário antes de executar o sql <br>

> A rota `/data/sql` **não aceita texto puro** (`text/plain`). <br>

> O corpo deve ser enviado como **JSON** (`Content-Type: application/json`).

---

## 🧰 Recursos e Validações

| Categoria                     | Comportamento                       |
| ----------------------------- | ---------------------------------------------------------------- |
| **Comandos permitidos**       | `DECLARE`, `SET`, `SELECT`, `WITH`  |
| **CTEs**                      | Suportadas (simples e múltiplas)    |
| **Múltiplos SELECTs**         | ✅ Permitidos na mesma requisição    |
| **Variáveis SQL**             | `DECLARE` e `SET` permitidos        |
| **Funções SQL**               | `SUM`, `COUNT`, `AVG`, `MIN`, `MAX`, `TRIM`, `UPPER`, `LOWER`, `CAST`, `CONVERT`, etc. |
| **Comentários SQL**           | Suportados (`--` e `/* ... */`)     |
| **Tabelas físicas**           | Validadas via `allowed_tables.json` |
| **CTEs na whitelist**         | ❌ Não exigidas                      |
| **DML / DDL**                 | ❌ Bloqueados                        |
| **EXEC / stored procedures**  | ❌ Bloqueados                        |
| **Transações (BEGIN/COMMIT)** | ❌ Bloqueadas                        |
| **GO / batches**              | ❌ Não suportados                    |


---

## 📈 Exemplo de Requisição

```bash
curl -X POST "https://api.transformamaisdelpi.com.br/data/sql" \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "DECLARE @G VARCHAR(10); SET @G = '\''1008'\''; SELECT TOP 3 * FROM SB1010 WHERE B1_GRUPO = @G;"
  }'
```

---

## ✅ Resposta de Sucesso

-   Consulta simples

```json
{
    "success": true,
    "sql": "WITH hierarchy AS (...) SELECT * FROM hierarchy;",
    "total": 37,
    "data": [
        { "B1_COD": "10080123", "B1_GRUPO": "1008", "LEVEL": 0 },
        { "B1_COD": "10080125", "B1_GRUPO": "10080123", "LEVEL": 1 }
    ]
}
```

-   Múltiplos SELECTs

```json
{
  "success": true,
  "results": [
    {
      "index": 1,
      "total": 3,
      "data": [ ... ]
    },
    {
      "index": 2,
      "total": 1,
      "data": [ ... ]
    }
  ]
}
```
---

## ❌ Resposta de Erro

### 🚫 Comando proibido

```json
{
    "success": false,
    "message": "Comando proibido detectado: UPDATE"
}
```

### 🚫 Tabela não permitida

```json
{
    "success": false,
    "message": "Tabela 'ZZ9999' não autorizada (fora da whitelist allowed_tables.json)."
}
```

### 🚫 SQL inválido

```json
{
  "success": false,
  "message": "Somente instruções DECLARE, SET, SELECT ou WITH são permitidas."
}
```

---

## 🧠 Boas Práticas

-   Sempre **finalize o SQL com `;`** (recomendado).
-   Declare todas as variáveis antes do WITH ou SELECT
-   Prefira CTEs para queries longas e legíveis
-   Use comentários para documentar regras de negócio
-   Use aliases claros (SB1, SH6, C)
-   Prefira `WITH` (sem `RECURSIVE`) quando estiver em ambiente SQL Server.
-   Utilize sempre **CTEs nomeadas claramente** (`WITH estoque_total AS (...)`).
-   Mantenha a lista de `allowed_tables.json` atualizada conforme o ambiente Protheus.

## 🔐 Limitações Importantes

-   Apenas leitura
-   Sem `INSERT`, `UPDATE`, `DELETE`
-   Sem `EXEC` ou `sp_*`
-   Sem `GO`
-   Sem controle automático de paginação
-   Não valida semântica de variáveis (erro vem do SQL Server)


---

## 🧱 Exemplo de uso interno pelo agente

### 🧠 Requisição automática (modo agente)

Quando o agente precisar consultar dados SQL puros:

1. Verificar se o comando é um `SELECT` válido.
2. Montar o JSON conforme o modelo abaixo:

    ```json
    { "sql": "SELECT TOP 3 * FROM SB1010 WHERE D_E_L_E_T_ = '';" }
    ```

3. Enviar o corpo JSON via `/data/sql` (Content-Type: application/json).
4. Retornar apenas o resultado (`data` e `total`) — **nunca o SQL completo**.
5. Caso o SQL seja rejeitado, relatar ao usuário:  
   _“Comando rejeitado por segurança SQL. Apenas SELECTs em tabelas permitidas são aceitos.”_

---

## 🔐 Limitações

-   Não executa `INSERT`, `UPDATE`, `DELETE` ou `ALTER`.
-   Não suporta `GO` (batch SQL Server).
-   Apenas uma instrução por requisição.
-   Não executa funções de sistema (`EXEC`, `sp_...`).

---

## 📗 Exemplos de solicitações

---

### 1. Usuário: **“Listar produtos programados para produzir hoje”**

#### 🎯 Objetivo

Listar os **produtos que possuem ordens de produção programadas para execução no dia**, considerando apenas **ordens ativas**, com **prioridade livre**, permitindo identificar rapidamente **o que está planejado para produzir hoje** por filial.

A consulta tem como finalidade:

- fornecer a **lista diária de produtos programados**;
- apoiar o **planejamento e acompanhamento do PCP**;
- garantir visibilidade do **plano de produção real do dia**;
- considerar apenas **produtos acabados válidos**.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_PRODUTO | Código do produto |
| C2_QUANT   | Quantidade planejada |
| C2_UM      | Unidade de medida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_DTINI   | Data de início da operação |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Requisições / Empenhos

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_TIPO    | Tipo do produto (PA) |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Operação programada para **hoje**  
  - `H8_DTINI = :DATA`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Apenas **produtos acabados**  
  - `B1_TIPO = 'PA'`

- Filial analisada  
  - `:FILIAL` (ex.: 01 ou 02)

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    OP.C2_PRODUTO        AS COD_PRODUTO,
    P.B1_DESC            AS DESCRICAO_PRODUTO,
    OP.C2_QUANT          AS QTD_PLANEJADA,
    OP.C2_UM             AS UNIDADE,
    OA.H8_DTINI          AS DATA_INICIO_OPERACAO
FROM SC2010 OP
LEFT JOIN SD4010 RE
    ON RE.D4_OP = OP.C2_OP
LEFT JOIN SH8010 OA
    ON OA.H8_OP    = RE.D4_OP
   AND OA.H8_OPER = RE.D4_OPERAC
LEFT JOIN SB1010 P
    ON P.B1_COD = OP.C2_PRODUTO
WHERE
        OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR  = '500'
    AND OA.H8_DTINI  = :DATA
    AND OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND OA.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_  = ''
    AND P.B1_TIPO = 'PA'
GROUP BY
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_UM,
    OA.H8_DTINI
ORDER BY
    OP.C2_PRODUTO ASC;
```

---

### 2. Usuário: **“Listar OPs (ordens de produção) finalizadas hoje”**

#### 🎯 Objetivo

Listar as **ordens de produção (OPs) finalizadas no dia**, considerando apenas **ordens ativas**, com **prioridade livre**, cuja **operação esteja programada para a data informada**.

A consulta tem como finalidade:

- identificar **produção efetivamente concluída no dia**;
- apoiar o **acompanhamento diário do PCP e da produção**;
- permitir análise por **Centro de Trabalho (CT)**;
- garantir que apenas **ordens válidas e encerradas** sejam consideradas.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_PRODUTO | Código do produto |
| C2_QUANT   | Quantidade planejada |
| C2_QUJE    | Quantidade produzida |
| C2_UM      | Unidade de medida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Empenhos de Componentes

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_DTINI   | Data de início da operação |
| H8_DTFIM   | Data de término da operação |
| H8_HRINI   | Hora de início |
| H8_HRFIM   | Hora de término |
| H8_CTRAB   | Centro de Trabalho |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Ordem **finalizada**  
  - `C2_QUANT = C2_QUJE`

- Operação programada para **hoje**  
  - `H8_DTINI = :DATA`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Filial analisada  
  - `:FILIAL` (ex.: 01 ou 02)

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    OP.C2_OP        AS COD_OP,
    OP.C2_PRODUTO   AS COD_PRODUTO,
    P.B1_DESC       AS DESCRICAO_PRODUTO,
    OP.C2_QUANT     AS QTD_OP,
    OP.C2_QUJE      AS QTD_PRODUZIDA,
    OP.C2_UM        AS UNIDADE,
    OA.H8_HRINI     AS HORA_INICIO,
    OA.H8_HRFIM     AS HORA_FIM,
    OA.H8_DTINI     AS DATA_INICIO,
    OA.H8_DTFIM     AS DATA_FIM,
    OA.H8_CTRAB     AS CT
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON RE.D4_OP = OP.C2_OP
INNER JOIN SB1010 P
    ON P.B1_COD = OP.C2_PRODUTO
INNER JOIN SH8010 OA
    ON OA.H8_OP    = RE.D4_OP
   AND OA.H8_OPER = RE.D4_OPERAC
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_  = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_QUANT   = OP.C2_QUJE
    AND OP.C2_PRIOR   = '500'
    AND OP.C2_FILIAL  = :FILIAL
    AND RE.D4_FILIAL  = :FILIAL
    AND OA.H8_FILIAL  = :FILIAL
    AND OA.H8_DTINI   = :DATA
GROUP BY
    OP.C2_OP,
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_QUJE,
    OP.C2_UM,
    OA.H8_HRINI,
    OA.H8_HRFIM,
    OA.H8_DTINI,
    OA.H8_DTFIM,
    OA.H8_CTRAB
ORDER BY
    OA.H8_HRINI ASC,
    OP.C2_OP   ASC;
```

---

### 3. Usuário: **“Listar OPs programadas em aberto (não finalizadas) de hoje”**

#### 🎯 Objetivo

Listar as **ordens de produção (OPs) programadas para o dia** que **ainda não foram finalizadas**, considerando apenas **ordens ativas**, com **prioridade livre**, permitindo acompanhamento operacional diário por **Centro de Trabalho (CT)**.

A consulta tem como finalidade:

- identificar o **backlog real do dia**;
- acompanhar ordens **em execução ou pendentes**;
- apoiar o **controle de produção e PCP**;
- fornecer visão clara de **quantidade planejada, produzida e faltante**.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_PRODUTO | Código do produto |
| C2_QUANT   | Quantidade planejada |
| C2_QUJE    | Quantidade produzida |
| C2_UM      | Unidade de medida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Empenhos de Componentes

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_DTINI   | Data de início da operação |
| H8_HRINI   | Hora de início |
| H8_CTRAB   | Centro de Trabalho |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Ordem **em aberto** (não finalizada)  
  - `C2_QUANT > C2_QUJE`

- Operação programada para **hoje**  
  - `H8_DTINI = :DATA`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Filial analisada  
  - `:FILIAL` (ex.: 01 ou 02)

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 📐 Regra de cálculo da quantidade faltante

A quantidade faltante é calculada a partir da diferença entre o planejado e o produzido:

```text
(C2_QUANT - C2_QUJE)
```

A expressão é ajustada para preservar casas decimais conforme a unidade do produto.

---

#### 💾 Consulta

```sql
SELECT
    OP.C2_OP AS COD_OP,
    OP.C2_PRODUTO AS COD_PRODUTO,
    P.B1_DESC AS DESCRICAO_PRODUTO,
    OP.C2_QUANT AS QTD_OP,
    OP.C2_QUJE AS QTD_PRODUZIDA,
    (OP.C2_QUANT * 1000 - OP.C2_QUJE * 1000) / 1000 AS QTD_FALTANTE,
    OP.C2_UM AS UNIDADE,
    OA.H8_HRINI AS HORA_INICIO,
    OA.H8_DTINI AS DATA_INICIO,
    OA.H8_CTRAB AS CT
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON RE.D4_OP = OP.C2_OP
INNER JOIN SB1010 P
    ON P.B1_COD = OP.C2_PRODUTO
INNER JOIN SH8010 OA
    ON OA.H8_OP = RE.D4_OP
   AND OA.H8_OPER = RE.D4_OPERAC
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_  = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_QUANT  > OP.C2_QUJE
    AND OP.C2_PRIOR  = '500'
    AND OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OA.H8_DTINI  = :DATA
GROUP BY
    OP.C2_OP,
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_QUJE,
    OP.C2_UM,
    OA.H8_HRINI,
    OA.H8_DTINI,
    OA.H8_CTRAB
ORDER BY
    OA.H8_HRINI ASC,
    OP.C2_OP ASC;
```

---

### 4. Usuário: **“Liste as OPs distintas em aberto”**

#### 🎯 Objetivo

Listar as **ordens de produção (OPs) distintas que se encontram em aberto**, ou seja, **não finalizadas**, considerando apenas ordens **ativas**, **prioridade livre** e **com operação programada para a data informada**.

A consulta tem como finalidade:

- identificar rapidamente o **backlog real de produção**;
- apoiar o **controle operacional diário**;
- fornecer base para **priorização e acompanhamento** das OPs em execução;
- garantir que apenas ordens **válidas e ativas** sejam analisadas.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_QUANT   | Quantidade planejada |
| C2_QUJE    | Quantidade produzida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Empenhos / Consumo

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_DTINI   | Data de início da operação |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Ordem **em aberto** (não finalizada)  
  - `C2_QUANT > C2_QUJE`

- Seleção de OPs **distintas**  
  - `DISTINCT C2_OP`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Data de execução da operação  
  - `H8_DTINI = :DATA`

- Filial analisada  
  - `:FILIAL` (ex.: 01 ou 02)

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT DISTINCT
    OP.C2_OP AS COD_OP
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON OP.C2_OP = RE.D4_OP
INNER JOIN SH8010 OA
    ON RE.D4_OP     = OA.H8_OP
   AND RE.D4_OPERAC = OA.H8_OPER
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR = '500'
    AND OP.C2_QUANT > OP.C2_QUJE
    AND OA.H8_DTINI = :DATA
ORDER BY
    OP.C2_OP ASC;
```

---

### 5. Usuário: **“Agrupar as ordens por centro de trabalho (CT) e contar finalizadas e não finalizadas”**


#### 🎯 Objetivo

Apurar a **quantidade de ordens de produção finalizadas e não finalizadas**, **agrupadas por Centro de Trabalho (CT)**, permitindo uma visão clara do **status produtivo por recurso** em uma data específica.

A consulta tem como finalidade:

- monitorar o **andamento da produção por CT**;
- identificar **acúmulo de ordens não finalizadas**;
- apoiar decisões de **balanceamento de carga e priorização**;
- fornecer um **indicador consolidado** para gestão operacional.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_QUANT   | Quantidade planejada |
| C2_QUJE    | Quantidade produzida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Empenhos / Consumo

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_CTRAB   | Centro de Trabalho |
| H8_DTINI   | Data de início da operação |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Ordem **finalizada**  
  - `C2_QUANT = C2_QUJE`

- Ordem **não finalizada**  
  - `C2_QUANT > C2_QUJE`

- Agrupamento por **Centro de Trabalho**  
  - `H8_CTRAB`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Data de execução da operação  
  - `H8_DTINI = :DATA`

- Filiais analisadas  
  - `:FILIAL` (ex.: 01 ou 02)

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    OA.H8_CTRAB AS CT,
    COUNT(DISTINCT CASE 
        WHEN OP.C2_QUANT = OP.C2_QUJE THEN OP.C2_OP 
    END) AS OPS_FINALIZADAS,
    COUNT(DISTINCT CASE 
        WHEN OP.C2_QUANT > OP.C2_QUJE THEN OP.C2_OP 
    END) AS OPS_NAO_FINALIZADAS,
    COUNT(DISTINCT OP.C2_OP) AS TOTAL_OPS
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON OP.C2_OP = RE.D4_OP
INNER JOIN SH8010 OA
    ON RE.D4_OP     = OA.H8_OP
   AND RE.D4_OPERAC = OA.H8_OPER
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR = '500'
    AND OA.H8_DTINI = :DATA
GROUP BY
    OA.H8_CTRAB
ORDER BY
    OA.H8_CTRAB ASC;
```
---

### 6. Usuário: **“Identificar componentes sem empenho registrado (travamento de produção) para um CT específico”**


#### 🎯 Objetivo

Identificar **componentes associados a ordens de produção ativas** que **não possuem empenho registrado** (`D4_QUANT = 0`) em um **Centro de Trabalho (CT) específico**, caracterizando **travamento de produção**.

A consulta permite:

- detectar **bloqueios operacionais** causados por ausência de empenho;
- identificar **ordens liberadas que não conseguem consumir material**;
- apoiar ações imediatas de **PCP, almoxarifado e produção**;
- analisar situações por **filial, CT e data específica**.

---

#### 🧱 Tabelas envolvidas

##### SD4010 — Empenhos de Componentes

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_PRODUTO | Código do componente |
| D4_OPERAC  | Operação da OP |
| D4_QUANT   | Quantidade empenhada |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Ordem de produção |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_CTRAB   | Centro de Trabalho |
| H8_DTINI   | Data de início da operação |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Componentes **sem empenho registrado**  
  - `D4_QUANT = 0`

- Centro de Trabalho específico  
  - `H8_CTRAB = :CT`

- Data de execução da operação  
  - `H8_DTINI = :DATA`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Filial específica  
  - `:FILIAL`

- Considerar somente registros ativos  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    RE.D4_OP        AS COD_OP,
    RE.D4_PRODUTO   AS COD_PRODUTO,
    P.B1_DESC       AS DESCRICAO_PRODUTO,
    RE.D4_OPERAC    AS OPERACAO,
    RE.D4_QUANT     AS QTD_EMPENHO,
    OA.H8_CTRAB     AS CT
FROM SD4010 RE
INNER JOIN SC2010 OP
    ON OP.C2_OP = RE.D4_OP
INNER JOIN SB1010 P
    ON RE.D4_PRODUTO = P.B1_COD
INNER JOIN SH8010 OA
    ON RE.D4_OP      = OA.H8_OP
   AND RE.D4_OPERAC = OA.H8_OPER
WHERE
    RE.D_E_L_E_T_ = ''
    AND OP.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_  = ''
    AND OA.D_E_L_E_T_ = ''
    AND RE.D4_FILIAL = :FILIAL
    AND OP.C2_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR = '500'
    AND RE.D4_QUANT = 0
    AND OA.H8_CTRAB = :CT
    AND OA.H8_DTINI = :DATA
ORDER BY
    RE.D4_OP ASC;
```
---

### 7. Usuário: **“Identificar ordens finalizadas sem consumo de componentes”**

#### 🎯 Objetivo

Identificar **ordens de produção finalizadas** que **não apresentaram consumo de componentes**, caracterizando uma **inconsistência produtiva ou de apontamento**, uma vez que houve produção concluída sem baixa de material.

A consulta permite:

- detectar **falhas de apontamento ou empenho**;
- identificar **ordens encerradas indevidamente**;
- apoiar auditorias de **produção, estoque e custos**;
- isolar casos por **CT, filial e data específica**.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna      | Descrição |
|------------|-----------|
| C2_OP      | Número da ordem de produção |
| C2_PRODUTO | Código do produto produzido |
| C2_QUANT   | Quantidade planejada |
| C2_QUJE    | Quantidade efetivamente produzida |
| C2_PRIOR   | Prioridade da OP |
| C2_FILIAL  | Filial da OP |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SD4010 — Empenhos / Consumo de Componentes

| Coluna      | Descrição |
|------------|-----------|
| D4_OP      | Ordem de produção |
| D4_OPERAC  | Operação da OP |
| D4_COD     | Código do componente |
| D4_QUANT   | Quantidade consumida |
| D4_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH8010 — Operações Alocadas

| Coluna      | Descrição |
|------------|-----------|
| H8_OP      | Ordem de produção |
| H8_OPER    | Operação |
| H8_CTRAB   | Centro de Trabalho |
| H8_DTINI   | Data de início da operação |
| H8_FILIAL  | Filial |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Ordem de produção **finalizada**  
  - `C2_QUANT = C2_QUJE`

- **Sem consumo de componentes**  
  - `SUM(D4_QUANT) = 0`

- Centro de Trabalho específico  
  - `H8_CTRAB = :CT`

- Data de execução da operação  
  - `H8_DTINI = :DATA`

- Apenas OPs com prioridade **Livre**  
  - `C2_PRIOR = '500'`

- Filial específica  
  - `C2_FILIAL = :FILIAL`

- Considerar somente registros ativos  
  - `SC2010.D_E_L_E_T_ = ''`  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SH8010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    OP.C2_OP        AS COD_OP,
    OP.C2_PRODUTO   AS COD_PRODUTO,
    P.B1_DESC       AS DESCRICAO_PRODUTO,
    OP.C2_QUANT     AS QTD_PLANEJADA,
    OP.C2_QUJE      AS QTD_PRODUZIDA,
    RE.D4_COD       AS COD_COMPONENTE,
    RE.D4_OPERAC    AS OPERACAO,
    SUM(RE.D4_QUANT) AS QTD_EMPENHO,
    OA.H8_CTRAB     AS CT
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON OP.C2_OP = RE.D4_OP
INNER JOIN SB1010 P
    ON OP.C2_PRODUTO = P.B1_COD
INNER JOIN SH8010 OA
    ON RE.D4_OP      = OA.H8_OP
   AND RE.D4_OPERAC = OA.H8_OPER
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_  = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR = '500'
    AND OA.H8_DTINI = :DATA
    AND OA.H8_CTRAB = :CT
    AND OP.C2_QUANT = OP.C2_QUJE
GROUP BY
    OP.C2_OP,
    OP.C2_PRODUTO,
    P.B1_DESC,
    OP.C2_QUANT,
    OP.C2_QUJE,
    RE.D4_COD,
    RE.D4_OPERAC,
    OA.H8_CTRAB
HAVING
    SUM(RE.D4_QUANT) = 0
ORDER BY
    OP.C2_OP ASC;
```

---

### 8. Usuário: **"Média de tempo por CT (H8_HRINI → H8_HRFIM)"**

#### 🧱 Tabelas envolvidas

-   SC2010 — Ordens de Produção
-   SD4010 — Empenhos
-   SH8010 — Operações

#### ⚙️ Condições aplicadas

-   Apenas ordens finalizadas (C2_QUANT = C2_QUJE)
-   Agrupar por H8_CTRAB
-   C2_PRIOR = 500
-   Filial = 01
-   H8_DTINI = hoje
-   H8_HRFIM IS NOT NULL
-   H8_HRINI IS NOT NULL
-   Registros ativos

#### 💾 Consulta

```sql
SELECT
    OA.H8_CTRAB AS CT,
    CAST(
        AVG(
            (
                (CAST(LEFT(REPLACE(OA.H8_HRFIM, ':', ''), 2) AS INT) * 60 +
                 CAST(RIGHT(REPLACE(OA.H8_HRFIM, ':', ''), 2) AS INT)
                )
              -
                (CAST(LEFT(REPLACE(OA.H8_HRINI, ':', ''), 2) AS INT) * 60 +
                 CAST(RIGHT(REPLACE(OA.H8_HRINI, ':', ''), 2) AS INT)
                )
            ) / 60.0
        ) AS FLOAT
    ) AS TEMPO_MEDIO_HORAS
FROM SC2010 OP
INNER JOIN SD4010 RE
    ON OP.C2_OP = RE.D4_OP
INNER JOIN SH8010 OA
    ON RE.D4_OP      = OA.H8_OP
   AND RE.D4_OPERAC = OA.H8_OPER
WHERE
    OP.D_E_L_E_T_ = ''
    AND RE.D_E_L_E_T_ = ''
    AND OA.D_E_L_E_T_ = ''
    AND OP.C2_FILIAL = :FILIAL
    AND RE.D4_FILIAL = :FILIAL
    AND OA.H8_FILIAL = :FILIAL
    AND OP.C2_PRIOR = '500'
    AND OA.H8_DTINI = :DATA
    AND OA.H8_DTFIM = :DATA
    AND OA.H8_HRINI IS NOT NULL
    AND OA.H8_HRFIM IS NOT NULL
    AND OP.C2_QUANT = OP.C2_QUJE
GROUP BY
    OA.H8_CTRAB
ORDER BY
    OA.H8_CTRAB ASC;

```

> Atenção: as colunas de horas no TOTVS são no formato texto HH:MM por isso é necessário usar o CAST

---

### 9. Usuário: **“Estoque total por filial/local, Grupo 1008 – Descrição TERM. BANDEIRA”**


#### 🎯 Objetivo

Apurar o **estoque total disponível** de produtos do **grupo 1008 (terminais)** cuja **descrição contenha o texto “TERM. BANDEIRA”**, com os resultados **agrupados por filial e local de estoque**.

A consulta tem como finalidade:

- fornecer uma **visão consolidada de estoque físico**;
- permitir análise por **filial e local**;
- apoiar decisões de **produção, abastecimento e balanceamento de estoque**;
- garantir que apenas **produtos válidos e ativos** sejam considerados.

---

#### 🧱 Tabelas envolvidas

##### SB2010 — Estoque por Produto / Local

| Coluna      | Descrição |
|------------|-----------|
| B2_FILIAL  | Filial do estoque |
| B2_LOCAL   | Local de armazenagem |
| B2_COD     | Código do produto |
| B2_QATU    | Quantidade atual em estoque |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_GRUPO   | Grupo do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Considerar somente **produtos ativos**  
  - `SB1010.D_E_L_E_T_ = ''`

- Considerar somente **saldos de estoque ativos**  
  - `SB2010.D_E_L_E_T_ = ''`

- Filtrar produtos do **grupo 1008 (terminais)**  
  - `SB1010.B1_GRUPO = '1008'`

- Filtrar descrição contendo **TERM. BANDEIRA**  
  - `SB1010.B1_DESC LIKE '%TERM. BANDEIRA%'`

- Consolidação de estoque por:  
  - Filial (`B2_FILIAL`)  
  - Local (`B2_LOCAL`)  
  - Produto (`B2_COD`)

---

#### 💾 Consulta

```sql
WITH estoque_total AS (
    SELECT
        E.B2_FILIAL,
        E.B2_LOCAL,
        E.B2_COD,
        SUM(E.B2_QATU) AS QT
    FROM SB2010 E
    WHERE
        E.D_E_L_E_T_ = ''
    GROUP BY
        E.B2_FILIAL,
        E.B2_LOCAL,
        E.B2_COD
)
SELECT
    T.B2_FILIAL,
    T.B2_LOCAL,
    P.B1_COD,
    P.B1_DESC,
    T.QT
FROM SB1010 P
INNER JOIN estoque_total T
    ON P.B1_COD = T.B2_COD
WHERE
    P.D_E_L_E_T_ = ''
    AND P.B1_GRUPO = '1008'
    AND P.B1_DESC LIKE '%TERM. BANDEIRA%'
ORDER BY
    P.B1_COD ASC;
```
---

### 10. Usuário: **“Buscar produtos do grupo 1050 com descrição contendo COMP e unidade diferente de peça”**

---

#### 🎯 Objetivo

Identificar **produtos cadastrados no grupo 1050** cuja **descrição contenha o termo “COMP”** e cuja **unidade de medida seja diferente de peça (PC)**.

A consulta tem como finalidade:

- detectar **inconsistências de cadastro** de unidade de medida;
- apoiar **saneamento e padronização** do cadastro de produtos;
- permitir análise objetiva de itens do grupo 1050 que **não seguem o padrão esperado de unidade**.

---

#### 🧱 Tabelas envolvidas

##### SB1010 — Cadastro de Produtos

> Fonte única necessária para a consulta.

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código interno do produto |
| B1_DESC    | Descrição do produto |
| B1_GRUPO   | Grupo do produto |
| B1_UM      | Unidade de medida |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Grupo do produto igual a **1050**  
  - `B1_GRUPO = '1050'`

- Descrição do produto contendo o texto **COMP**  
  - `B1_DESC LIKE '%COMP%'`

- Unidade de medida diferente de **peça (PC)**  
  - `B1_UM <> 'PC'`

- Considerar somente registros ativos  
  - `SB1010.D_E_L_E_T_ = ''`

---

#### 💾 Consulta

```sql
SELECT
    B1_COD   AS COD_PRODUTO,
    B1_DESC  AS DESCRICAO_PRODUTO,
    B1_GRUPO AS GRUPO,
    B1_UM    AS UNIDADE
FROM SB1010
WHERE
        D_E_L_E_T_ = ''
    AND B1_GRUPO = '1050'
    AND B1_DESC LIKE '%COMP%'
    AND B1_UM <> 'PC'
ORDER BY
    B1_COD;
```
---

### 11. Usuário: **"Encontrar produtos com partnumbers duplicados para um fornecedor"**

#### 🎯 Objetivo

Identificar produtos DELPI distintos que compartilham o mesmo **partnumber do fornecedor**, caracterizando duplicidade no relacionamento Produto × Fornecedor.

---

#### 🧱 Tabelas envolvidas

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código interno do produto DELPI |
| B1_DESC    | Descrição do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica do registro |

##### SA5010 — Relacionamento Produto × Fornecedor

| Coluna      | Descrição |
|------------|-----------|
| A5_PRODUTO | Código do produto DELPI |
| A5_FORNECE | Código do fornecedor |
| A5_NOMEFOR | Nome do fornecedor |
| A5_CODPRF  | Partnumber do produto no fornecedor |
| D_E_L_E_T_ | Indicador de exclusão lógica do registro |

---

#### ⚙️ Condições aplicadas

- Fornecedor específico (`A5_FORNECE = '001499'`)
- Considera somente registros ativos  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SA5010.D_E_L_E_T_ = ''`
- Identificação de partnumbers duplicados  
  - Mesmo `A5_CODPRF` associado a mais de um produto DELPI

---

#### 💾 Consulta

```sql
SELECT
    P.B1_COD     AS COD_PRODUTO,
    P.B1_DESC    AS DESCRICAO_PRODUTO,
    F.A5_FORNECE AS COD_FORNECEDOR,
    F.A5_NOMEFOR AS NOME_FORNECEDOR,
    F.A5_CODPRF  AS PARTNUMBER
FROM SB1010 P
INNER JOIN SA5010 F
    ON F.A5_PRODUTO = P.B1_COD
WHERE
        F.A5_FORNECE =  '001499'
    AND F.D_E_L_E_T_ = ''
    AND P.D_E_L_E_T_ = ''
    AND F.A5_CODPRF IN (
        SELECT
            A5_CODPRF
        FROM SA5010
        WHERE
                A5_FORNECE =  '001499'
            AND D_E_L_E_T_ = ''
        GROUP BY
            A5_CODPRF
        HAVING COUNT(*) > 1
    )
ORDER BY
    F.A5_CODPRF,
    P.B1_COD;
```
---

### 12. Usuário: **“Buscar a última NF válida de um produto, excluindo transportadoras.”**

#### 🎯 Objetivo

Identificar a **última Nota Fiscal de Entrada válida** de um produto DELPI específico, garantindo que:

- o fornecedor seja **real (não transportadora)**;
- fornecedores internos previamente mapeados sejam **explicitamente excluídos**;
- apenas **registros ativos** sejam considerados;
- o resultado represente **a NF mais recente**, considerando critérios cronológicos consistentes.

O objetivo é obter **um único registro confiável por produto**, representando a última compra válida.

---

#### 🧱 Tabelas envolvidas

##### SD1010 — Itens de Notas Fiscais de Entrada

| Coluna        | Descrição |
|--------------|-----------|
| D1_FILIAL    | Filial de lançamento da NF |
| D1_COD       | Código do produto |
| D1_DOC       | Número da Nota Fiscal |
| D1_EMISSAO   | Data de emissão da NF |
| D1_DTDIGIT   | Data de digitação da NF |
| D1_FORNECE   | Código do fornecedor |
| D1_LOJA      | Loja do fornecedor |
| D_E_L_E_T_   | Indicador de exclusão lógica |

---

##### SA2010 — Cadastro de Fornecedores

| Coluna      | Descrição |
|------------|-----------|
| A2_COD     | Código do fornecedor |
| A2_LOJA    | Loja do fornecedor |
| A2_NOME    | Nome do fornecedor |
| A2_CGC     | CNPJ do fornecedor |
| A2_EST     | UF do fornecedor |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SA5010 — Relacionamento Produto × Fornecedor

| Coluna      | Descrição |
|------------|-----------|
| A5_PRODUTO | Código do produto DELPI |
| A5_FORNECE | Código do fornecedor |
| A5_LOJA    | Loja do fornecedor |
| A5_CODPRF  | Partnumber do produto no fornecedor |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Produto específico analisado  
  - `SD1010.D1_COD = '10080001'`

- Considerar somente registros ativos  
  - `SD1010.D_E_L_E_T_ = ''`  
  - `SA2010.D_E_L_E_T_ = ''`  
  - `SA5010.D_E_L_E_T_ = ''`

- Exclusão de fornecedores internos específicos  
  - `D1_FORNECE <> '000019'`  
  - `D1_FORNECE <> '001149'`

- Exclusão de transportadoras  
  - Fornecedor cujo nome contenha “TRANSP” é descartado  
  - `UPPER(SA2010.A2_NOME) NOT LIKE '%TRANSP%'`

- Determinação da última NF válida por produto  
  - Critério de ordenação hierárquico:
    1. Data de emissão (`D1_EMISSAO`)
    2. Data de digitação (`D1_DTDIGIT`)
    3. Número da NF (`D1_DOC`)
  - Uso de `ROW_NUMBER()` particionado por produto
  - Seleção apenas do registro mais recente (`RN = 1`)

---

#### 💾 Consulta

```sql
WITH ULTIMA_NF_PRODUTO AS (
    SELECT
        SD1.D1_FILIAL        AS FILIAL,
        SD1.D1_COD           AS COD_MATERIA_PRIMA,
        A5.A5_CODPRF         AS PARTNUMBER,
        SD1.D1_DOC           AS NF_NUMERO,
        SD1.D1_EMISSAO       AS DATA_EMISSAO,
        SD1.D1_DTDIGIT       AS DATA_DIGITACAO,
        SD1.D1_FORNECE       AS FORNECEDOR_CODIGO,
        SD1.D1_LOJA          AS FORNECEDOR_LOJA,
        SA2.A2_NOME          AS FORNECEDOR_NOME,
        SA2.A2_CGC           AS FORNECEDOR_CNPJ,
        SA2.A2_EST           AS FORNECEDOR_UF,
        ROW_NUMBER() OVER (
            PARTITION BY SD1.D1_COD
            ORDER BY
                SD1.D1_EMISSAO DESC,
                SD1.D1_DTDIGIT DESC,
                SD1.D1_DOC DESC
        ) AS RN
    FROM SD1010 SD1
    INNER JOIN SA2010 SA2
        ON SA2.A2_COD  = SD1.D1_FORNECE
       AND SA2.A2_LOJA = SD1.D1_LOJA
       AND SA2.D_E_L_E_T_ = ''
    LEFT JOIN SA5010 A5
        ON A5.A5_PRODUTO = SD1.D1_COD
       AND A5.A5_FORNECE = SD1.D1_FORNECE
       AND A5.A5_LOJA    = SD1.D1_LOJA
       AND A5.D_E_L_E_T_ = ''
    WHERE
            SD1.D_E_L_E_T_ = ''
        AND SD1.D1_COD = '10080001'
        AND SD1.D1_FORNECE <> '000019'
        AND SD1.D1_FORNECE <> '001149'
        AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
)
SELECT
    FILIAL,
    COD_MATERIA_PRIMA,
    PARTNUMBER,
    NF_NUMERO,
    DATA_EMISSAO,
    DATA_DIGITACAO,
    FORNECEDOR_CODIGO,
    FORNECEDOR_LOJA,
    FORNECEDOR_NOME,
    FORNECEDOR_CNPJ,
    FORNECEDOR_UF
FROM ULTIMA_NF_PRODUTO
WHERE RN = 1
ORDER BY COD_MATERIA_PRIMA;
```
---

### 13. Usuário: **“Identificar a quantidade consumida de terminais por CT, agrupada por filial”**

#### 🎯 Objetivo

Identificar a **quantidade efetivamente consumida de terminais (grupo 1008)** em um **Centro de Trabalho (CT) específico**, considerando **apenas produção real comprovada**, com os resultados **agrupados por filial**, dentro de um **período definido**.

A consulta garante que:

- o consumo apurado é **real**, não apenas planejado;
- o CT é validado por **apontamento efetivo de produção**;
- as quantidades **não são infladas** por múltiplos apontamentos;
- os resultados são **comparáveis entre filiais**.

---

#### 🧱 Tabelas envolvidas

##### SD4010 — Empenhos / Consumo de Materiais

| Coluna        | Descrição |
|--------------|-----------|
| D4_FILIAL    | Filial da ordem de produção |
| D4_OP        | Número da OP |
| D4_OPERAC    | Operação da OP |
| D4_COD       | Código do material consumido |
| D4_QTDEORI   | Quantidade originalmente empenhada |
| D4_QUANT     | Quantidade efetivamente baixada |
| D_E_L_E_T_   | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_GRUPO   | Grupo do produto |
| B1_UM      | Unidade de medida |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SH6010 — Apontamentos de Produção

| Coluna        | Descrição |
|--------------|-----------|
| H6_FILIAL    | Filial do apontamento |
| H6_OP        | Ordem de produção |
| H6_OPERAC   | Operação apontada |
| H6_RECURSO  | Recurso / Centro de Trabalho |
| H6_TIPO     | Tipo de apontamento (P = Produção) |
| H6_DATAINI  | Data de início da execução |
| D_E_L_E_T_  | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Considerar apenas **terminais**  
  - `SB1010.B1_GRUPO = '1008'`

- Validar apenas **produção real**  
  - `SH6010.H6_TIPO = 'P'`

- Centro de Trabalho específico  
  - `SH6010.H6_RECURSO = 'CT-53'`

- Período de execução real  
  - `SH6010.H6_DATAINI BETWEEN '20250101' AND '20251231'`

- Agrupamento por filial  
  - `SD4010.D4_FILIAL`

- Considerar somente registros ativos  
  - `SD4010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`  
  - `SH6010.D_E_L_E_T_ = ''`

- Validação de execução real por operação  
  - Uso de `EXISTS (SH6010)` para garantir que **cada linha da SD4010 só é considerada se a operação teve produção real no CT e no período informado**

---

#### 📐 Regra de cálculo da quantidade consumida

A quantidade consumida é calculada **exclusivamente a partir da SD4010**, utilizando o critério:

```text
D4_QTDEORI - D4_QUANT
```

Somente valores positivos são considerados, evitando consumo inflado ou registros inconsistentes.

---

#### 💾 Consulta

```sql
SELECT
    SD4.D4_FILIAL        AS FILIAL,
    SD4.D4_COD           AS COD_MATERIAL,
    SB1.B1_DESC          AS DESC_MATERIAL,
    SB1.B1_UM            AS UNIDADE,
    'CT-53'              AS CT,
    SUM(
        CASE
            WHEN SD4.D4_QTDEORI > SD4.D4_QUANT
            THEN SD4.D4_QTDEORI - SD4.D4_QUANT
            ELSE 0
        END
    ) AS QTD_CONSUMIDA
FROM SD4010 SD4
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = SD4.D4_COD
WHERE
    SD4.D_E_L_E_T_ = ''
    AND SB1.D_E_L_E_T_ = ''
    AND SB1.B1_GRUPO = '1008'

    AND EXISTS (
        SELECT 1
        FROM SH6010 SH6
        WHERE
            SH6.D_E_L_E_T_ = ''
            AND SH6.H6_TIPO = 'P'
            AND SH6.H6_FILIAL = SD4.D4_FILIAL
            AND SH6.H6_OP     = SD4.D4_OP
            AND SH6.H6_OPERAC = SD4.D4_OPERAC
            AND SH6.H6_RECURSO = 'CT-53'
            AND SH6.H6_DATAINI BETWEEN '20250101' AND '20251231'
    )
GROUP BY
    SD4.D4_FILIAL,
    SD4.D4_COD,
    SB1.B1_DESC,
    SB1.B1_UM
ORDER BY
    SD4.D4_FILIAL,
    SD4.D4_COD;
```

### 14. Usuário: **“Tempo médio real de consumo de uma matéria prima para o CT-xx (CT específico, sem duplicidade de tempo)”**

---

#### 🎯 Objetivo

Calcular, para cada **matéria prima**, o **tempo médio real de consumo por unidade**, utilizando **dados reais de produção**, considerando:

- apenas **apontamentos de produção válidos** (`H6_TIPO = 'P'`);
- um **Centro de Trabalho (CT) específico**;
- uma **faixa de datas definida**;
- a **quantidade real consumida** de cada matéria prima;
- a **eliminação de duplicidade de tempo**, consolidando todos os apontamentos pertencentes à mesma **OP + operação**.

O resultado é um indicador **ponderado pelo volume real produzido**, tecnicamente consistente, adequado para análise de desempenho produtivo e engenharia de tempos.

---

#### 🧱 Tabelas envolvidas

##### SH6010 — Apontamentos de Produção

| Coluna        | Descrição |
|--------------|-----------|
| H6_FILIAL    | Filial do apontamento |
| H6_OP        | Ordem de produção |
| H6_OPERAC   | Operação da OP |
| H6_RECURSO  | Recurso / Centro de Trabalho |
| H6_TIPO     | Tipo de apontamento (P = Produção) |
| H6_DATAINI  | Data de início da execução |
| H6_DATAFIN  | Data de término da execução |
| H6_HORAINI  | Hora de início |
| H6_HORAFIN  | Hora de término |
| D_E_L_E_T_  | Indicador de exclusão lógica |

---

##### SD4010 — Consumo de Materiais

| Coluna        | Descrição |
|--------------|-----------|
| D4_FILIAL    | Filial da OP |
| D4_OP        | Ordem de produção |
| D4_OPERAC   | Operação da OP |
| D4_COD       | Código do material consumido |
| D4_QTDEORI  | Quantidade originalmente empenhada |
| D4_QUANT    | Quantidade efetivamente baixada |
| D_E_L_E_T_  | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_GRUPO   | Grupo do produto |
| B1_UM      | Unidade de medida |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- **SH6010 — Apontamentos de Produção**
  - Somente registros ativos: `D_E_L_E_T_ = ''`
  - Apenas produção real: `H6_TIPO = 'P'`
  - Centro de Trabalho específico: `H6_RECURSO = :CT`
  - Período de execução real: `H6_DATAINI BETWEEN :DATA_INICIO AND :DATA_FIM`
  - Apontamentos completos:
    - `H6_DATAFIN IS NOT NULL`
    - `H6_HORAINI <> ''`
    - `H6_HORAFIN <> ''`
  - **Consolidação do tempo** por:
    - Filial
    - OP
    - Operação
    - CT

- **SD4010 — Consumo de Terminais**
  - Somente registros ativos: `D_E_L_E_T_ = ''`
  - Quantidade real consumida calculada como:
    - `D4_QTDEORI - D4_QUANT` (quando positiva)
  - Agrupamento por:
    - Filial
    - OP
    - Operação
    - Código do material

- **SB1010 — Cadastro de Produto**
  - Somente registros ativos: `D_E_L_E_T_ = ''`
  - Apenas terminais: `B1_GRUPO = :GRUPO`

---

#### 🧮 Equações envolvidas

- **⏱️ Tempo total consolidado por OP + operação**

Para cada OP \(i\) e operação \(j\):

\[
T_{i,j} = \sum (DataHoraFim_{i,j} - DataHoraInicio_{i,j})
\]

> A soma elimina duplicidades causadas por múltiplos apontamentos na SH6010.

---

- **📦 Quantidade real consumida da matéria prima**

Para cada matéria prima \(t\), OP \(i\) e operação \(j\):

\[
Q_{i,j,t} = \sum
\begin{cases}
D4\_QTDEORI - D4\_QUANT, & \text{se } D4\_QTDEORI > D4\_QUANT \\
0, & \text{caso contrário}
\end{cases}
\]

---

#### ⏱️ Tempo médio real por materia prima (ponderado)

Para cada materia prima \(t\):

\[
\boxed{
TempoMédio_t = \frac{\sum T_{i,j}}{\sum Q_{i,j,t}}
}
\]

- Unidade: **segundos por peça**
- Tempo **ponderado pelo volume real consumido**
- Não se trata de média simples por OP

---

#### 💾 Consulta

```sql
DECLARE @CT VARCHAR(20);
DECLARE @GRUPO VARCHAR(20);
DECLARE @DATA_INICIO VARCHAR(20);
DECLARE @DATA_FIM VARCHAR(20);

SET @CT = 'CT-33A';
SET @GRUPO = '1007';
SET @DATA_INICIO = '20250101';
SET @DATA_FIM = '20251231';

WITH SH6_CONSOLIDADO AS (
    SELECT
        H6_FILIAL,
        H6_OP,
        H6_OPERAC,
        H6_RECURSO,
        -- Tempo TOTAL por OP + operação (elimina duplicidade)
        SUM(
            DATEDIFF(
                SECOND,
                CAST(CONVERT(char(8), H6_DATAINI, 112) + ' ' + H6_HORAINI AS datetime),
                CAST(CONVERT(char(8), H6_DATAFIN, 112) + ' ' + H6_HORAFIN AS datetime)
            )
        ) AS TEMPO_OP_SEG
    FROM SH6010
    WHERE
        D_E_L_E_T_ = ''
        AND H6_TIPO = 'P'
        AND H6_RECURSO = @CT
        AND H6_DATAINI BETWEEN @DATA_INICIO AND @DATA_FIM
        AND H6_DATAFIN IS NOT NULL
        AND H6_HORAINI <> ''
        AND H6_HORAFIN <> ''
    GROUP BY
        H6_FILIAL,
        H6_OP,
        H6_OPERAC,
        H6_RECURSO
),

CONSUMO AS (
    SELECT
        SD4.D4_FILIAL,
        SD4.D4_OP,
        SD4.D4_OPERAC,
        SD4.D4_COD,
        -- Quantidade REAL consumida
        SUM(
            CASE
                WHEN SD4.D4_QTDEORI > SD4.D4_QUANT
                THEN SD4.D4_QTDEORI - SD4.D4_QUANT
                ELSE 0
            END
        ) AS QTD_CONSUMIDA
    FROM SD4010 SD4
    WHERE
        SD4.D_E_L_E_T_ = ''
    GROUP BY
        SD4.D4_FILIAL,
        SD4.D4_OP,
        SD4.D4_OPERAC,
        SD4.D4_COD
)
SELECT
    SH6.H6_FILIAL AS FILIAL,
    SB1.B1_COD   AS CODIGO,
    SB1.B1_DESC  AS DESCRICAO,
    SB1.B1_UM    AS UNIDADE,
    SH6.H6_RECURSO AS CT,
    -- Quantidade total REAL no período / CT
    SUM(C.QTD_CONSUMIDA) AS QTD_TOTAL_MP,
    -- Tempo total REAL (sem duplicidade)
    SUM(SH6.TEMPO_OP_SEG) AS TEMPO_TOTAL_SEG,
    -- Tempo médio REAL por peça (ponderado)
    SUM(SH6.TEMPO_OP_SEG) * 1.0
    / NULLIF(SUM(C.QTD_CONSUMIDA), 0)
    AS TEMPO_MEDIO_SEG_POR_PECA
FROM SH6_CONSOLIDADO SH6
INNER JOIN CONSUMO C
    ON C.D4_FILIAL = SH6.H6_FILIAL
   AND C.D4_OP     = SH6.H6_OP
   AND C.D4_OPERAC = SH6.H6_OPERAC
INNER JOIN SB1010 SB1
    ON SB1.B1_COD   = C.D4_COD
   AND SB1.B1_GRUPO = @GRUPO
   AND SB1.D_E_L_E_T_ = ''
WHERE
    C.QTD_CONSUMIDA > 0
GROUP BY
    SH6.H6_FILIAL,
    SB1.B1_COD,
    SB1.B1_DESC,
    SB1.B1_UM,
    SH6.H6_RECURSO
ORDER BY
    SH6.H6_FILIAL,
    SB1.B1_COD,
    TEMPO_MEDIO_SEG_POR_PECA;
```

---

### 15. Usuário: **"Buscar produtos com descrição duplicada (Matéria-Prima)."**

#### 🎯 Objetivo

Identificar **produtos do tipo Matéria-Prima (MP)** cadastrados no
Protheus que compartilham **a mesma descrição (`B1_DESC`)**,
caracterizando **duplicidade de cadastro**, garantindo que:

-   apenas **produtos ativos** sejam considerados;
-   o escopo seja **restrito a MP**;
-   a duplicidade seja determinada **exclusivamente pela descrição
    textual**;
-   todos os **códigos envolvidos** em cada descrição duplicada sejam
    retornados;
-   seja possível **quantificar o grau de duplicidade** por descrição.

O objetivo é **detectar inconsistências de cadastro**, apoiar
**saneamento de dados** e **prevenir riscos operacionais**.

---

#### 🧱 Tabelas envolvidas

##### SB1010 --- Cadastro de Produtos

  Coluna          | Descrição
  --------------- | ----------------------
  B1_COD          | Código do produto
  B1_DESC         | Descrição do produto
  B1_TIPO         | Tipo do produto
  D_E\_L_E\_T\_   | Exclusão lógica

---

#### ⚙️ Condições aplicadas

-   Somente produtos ativos
    -   `D_E_L_E_T_ = ''`
-   Somente Matéria-Prima
    -   `B1_TIPO = 'MP'`
-   Identificação de duplicidade
    -   Agrupamento por `B1_DESC`
    -   `HAVING COUNT(*) > 1`

---

#### 💾 Consulta

``` sql
WITH descricoes_duplicadas AS (
    SELECT
        B1_DESC,
        COUNT(*) AS QTD
    FROM SB1010
    WHERE
        D_E_L_E_T_ = ''
        AND B1_TIPO = 'MP'
    GROUP BY
        B1_DESC
    HAVING COUNT(*) > 1
)
SELECT
    P.B1_COD   AS COD_PRODUTO,
    P.B1_DESC  AS DESCRICAO,
    D.QTD      AS QTD_PRODUTOS_COM_MESMA_DESCRICAO
FROM SB1010 P
INNER JOIN descricoes_duplicadas D
    ON D.B1_DESC = P.B1_DESC
WHERE
    P.D_E_L_E_T_ = ''
    AND P.B1_TIPO = 'MP'
ORDER BY
    D.QTD DESC,
    P.B1_DESC,
    P.B1_COD;
```

---

### 16. Usuário: **"Itens de pedidos de venda em aberto — aberto físico × comercial × faturável (com insights)."**

#### 🎯 Objetivo

Identificar e analisar a **carteira de pedidos de venda**
no Protheus, classificando cada item conforme o **tipo real de abertura**
(**físico, comercial ou faturável**), garantindo que:

- apenas **itens de pedido ativos** sejam considerados;
- somente **itens com saldo em aberto** (quantidade vendida maior que entregue)
  sejam retornados;
- **bloqueios no item** sejam respeitados;
- os pedidos sejam classificados de forma **determinística e auditável**;
- seja possível **identificar pedidos bloqueados por falta de liberação**;
- sejam gerados **insights operacionais e financeiros**, como:
  - valor financeiro exposto;
  - status logístico do pedido (alinhado ao Power BI);
  - identificação de pedidos bloqueados por liberação.

O objetivo é **eliminar ambiguidades sobre “pedido em aberto”**,
permitindo separar claramente **problemas comerciais, produtivos e fiscais**,
e fornecer uma **base sólida para tomada de decisão e automação via API**.

---

#### 🧱 Tabelas envolvidas

##### SC6010 — Itens do Pedido de Venda

| Coluna          | Descrição                         |
| --------------- | --------------------------------- |
| C6\_FILIAL      | Filial do item                    |
| C6\_NUM         | Número do pedido                  |
| C6\_PRODUTO     | Código do produto                 |
| C6\_QTDVEN      | Quantidade vendida                |
| C6\_QTDENT      | Quantidade entregue               |
| C6\_PRCVEN      | Preço unitário de venda           |
| C6\_BLOQUEI     | Bloqueio comercial do item        |
| C6\_BLQ         | Bloqueio logístico/fiscal do item |
| D\_E\_L\_E\_T\_ | Exclusão lógica                   |

---

##### SC5010 — Cabeçalho do Pedido de Venda

| Coluna          | Descrição                         |
| --------------- | --------------------------------- |
| C5\_FILIAL      | Filial do pedido                  |
| C5\_NUM         | Número do pedido                  |
| C5\_EMISSAO     | Data de emissão                   |
| C5\_CLIENTE     | Código do cliente                 |
| C5\_LOJACLI     | Loja do cliente                   |
| C5\_LIBEROK     | Indica se o pedido está liberado  |
| C5\_BLQ         | Bloqueio no pedido                |
| C5\_STATUS      | Status do pedido (ex.: cancelado) |
| C5\_NOTA        | Número da nota fiscal             |
| D\_E\_L\_E\_T\_ | Exclusão lógica                   |

---

##### SB1010 — Cadastro de Produtos

| Coluna          | Descrição            |
| --------------- | -------------------- |
| B1\_COD         | Código do produto    |
| B1\_DESC        | Descrição do produto |
| D\_E\_L\_E\_T\_ | Exclusão lógica      |

---

##### SA1010 — Cadastro de Clientes

| Coluna          | Descrição         |
| --------------- | ----------------- |
| A1\_COD         | Código do cliente |
| A1\_LOJA        | Loja do cliente   |
| A1\_NOME        | Nome do cliente   |
| D\_E\_L\_E\_T\_ | Exclusão lógica   |

---

#### ⚙️ Condições aplicadas

- Somente itens ativos — `SC6010.D_E_L_E_T_ = ''`
- Somente pedidos ativos — `SC5010.D_E_L_E_T_ = ''`
- Somente produtos ativos — `SB1010.D_E_L_E_T_ = ''`
- Somente clientes ativos — `SA1010.D_E_L_E_T_ = ''`
- Somente itens com **saldo em aberto** — `(C6_QTDVEN - C6_QTDENT) > 0`
- Exclusão de itens bloqueados — `C6_BLOQUEI / C6_BLQ`

---

#### 🧠 Regras de classificação do tipo de aberto

- **Aberto físico**
  - Existe saldo em aberto (`C6_QTDVEN > C6_QTDENT`)
  - Pedido **não liberado** ou com restrições comerciais
  - Representa pendência **quantitativa**, não necessariamente atendível

- **Aberto comercial**
  - Existe saldo em aberto
  - Pedido **liberado** (`C5_LIBEROK = 'S'`)
  - Pedido **não cancelado** (`C5_STATUS <> 'C'`)
  - Pode ainda não estar apto a faturar

- **Aberto faturável**
  - Existe saldo em aberto
  - Pedido liberado
  - Pedido não cancelado
  - Pedido **sem nota fiscal gerada** (`C5_NOTA IS NULL OR = ''`)
  - Representa **fila real de faturamento****

---

#### 🧭 Regras de classificação do status do pedido (alinhado ao Power BI)

O **status do pedido** é determinado **exclusivamente no nível do item (SC6010)**,
com base na **quantidade entregue** e na **data prometida de entrega (`C6_ENTREG`)**,
replicando exatamente a lógica utilizada no Power BI.

- **Concluído**
  - `C6_QTDENT >= C6_QTDVEN`

- **Parcialmente Entregue**
  - `C6_QTDENT > 0` e `C6_QTDENT < C6_QTDVEN`

- **Sem Data**
  - `C6_QTDENT < C6_QTDVEN`
  - `C6_ENTREG IS NULL` ou `C6_ENTREG = '00000000'`

- **Entrega prevista hoje**
  - `C6_QTDENT < C6_QTDVEN`
  - Data de entrega = data atual

- **Atrasado**
  - `C6_QTDENT < C6_QTDVEN`
  - Data de entrega < data atual

- **Entrega próximos 7 dias**
  - `C6_QTDENT < C6_QTDVEN`
  - Data de entrega > data atual e ≤ data atual + 7 dias

- **Entrega futura**
  - `C6_QTDENT < C6_QTDVEN`
  - Data de entrega > data atual + 7 dias


---

#### 💾 Consulta

```sql
-- Página desejada
DECLARE @Page INT = 1;        
-- Registros por página
DECLARE @PageSize INT = 100; 

DECLARE @Offset INT = (@Page - 1) * @PageSize;

SELECT
    C6.C6_FILIAL        AS FILIAL,
    C6.C6_NUM           AS PEDIDO,
    C5.C5_EMISSAO       AS DATA_EMISSAO,
    C6.C6_PRODUTO       AS PRODUTO,
    SB1.B1_DESC         AS DESCRICAO_PRODUTO,

    SA1.A1_COD          AS COD_CLIENTE,
    SA1.A1_LOJA         AS LOJA_CLIENTE,
    SA1.A1_NOME         AS CLIENTE,

    C6.C6_QTDVEN        AS QTD_VENDIDA,
    C6.C6_QTDENT        AS QTD_ENTREGUE,
    (C6.C6_QTDVEN - C6.C6_QTDENT) AS SALDO_ABERTO,

     -- SB2010 / Armazém 01
    ISNULL(SB2.B2_QATU, 0) AS ESTOQUE_ATUAL,  

    C6.C6_PRUNIT        AS PRECO_UNITARIO,    
    (C6.C6_QTDVEN - C6.C6_QTDENT) * C6.C6_PRUNIT AS VALOR_ABERTO,

    CASE
        WHEN C6.C6_ENTREG IS NULL OR C6.C6_ENTREG = '00000000'
            THEN NULL
        ELSE CONVERT(
            DATE,
            STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-')
        )
    END AS DATA_ENTREGA,

    CASE
        WHEN C6.C6_QTDENT >= C6.C6_QTDVEN THEN 'Concluído'
        WHEN C6.C6_QTDENT > 0
         AND C6.C6_QTDENT < C6.C6_QTDVEN THEN 'Parcialmente Entregue'
        WHEN C6.C6_QTDENT < C6.C6_QTDVEN
         AND (C6.C6_ENTREG IS NULL OR C6.C6_ENTREG = '00000000') THEN 'Sem Data'
        WHEN C6.C6_QTDENT < C6.C6_QTDVEN
         AND CONVERT(DATE, STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-'))
             = CAST(GETDATE() AS DATE) THEN 'Entrega prevista hoje'
        WHEN C6.C6_QTDENT < C6.C6_QTDVEN
         AND CONVERT(DATE, STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-'))
             < CAST(GETDATE() AS DATE) THEN 'Atrasado'
        WHEN C6.C6_QTDENT < C6.C6_QTDVEN
         AND CONVERT(DATE, STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-'))
             > CAST(GETDATE() AS DATE)
         AND CONVERT(DATE, STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-'))
             <= DATEADD(DAY, 7, CAST(GETDATE() AS DATE))
             THEN 'Entrega próximos 7 dias'
        WHEN C6.C6_QTDENT < C6.C6_QTDVEN
         AND CONVERT(DATE, STUFF(STUFF(C6.C6_ENTREG, 5, 0, '-'), 8, 0, '-'))
             > DATEADD(DAY, 7, CAST(GETDATE() AS DATE))
             THEN 'Entrega futura'
        ELSE 'Outro'
    END AS STATUS_PEDIDO,

    CASE
        WHEN C5.C5_LIBEROK = 'S'
         AND (C5.C5_BLQ IS NULL OR C5.C5_BLQ = '')
         AND (C5.C5_STATUS IS NULL OR C5.C5_STATUS <> 'C')
         AND (C5.C5_NOTA IS NULL OR C5.C5_NOTA = '')
            THEN 'ABERTO FATURAVEL'
        WHEN C5.C5_LIBEROK = 'S'
         AND (C5.C5_BLQ IS NULL OR C5.C5_BLQ = '')
         AND (C5.C5_STATUS IS NULL OR C5.C5_STATUS <> 'C')
            THEN 'ABERTO COMERCIAL'
        ELSE 'ABERTO FISICO'
    END AS TIPO_ABERTO,

    CASE
        WHEN C5.C5_LIBEROK IS NULL OR C5.C5_LIBEROK <> 'S'
            THEN 'BLOQUEADO POR LIBERACAO'
        ELSE 'LIBERADO'
    END AS STATUS_LIBERACAO

FROM SC6010 C6

INNER JOIN SC5010 C5
    ON C5.C5_FILIAL = C6.C6_FILIAL
   AND C5.C5_NUM    = C6.C6_NUM
   AND C5.D_E_L_E_T_ = ''

INNER JOIN SB1010 SB1
    ON SB1.B1_COD = C6.C6_PRODUTO
   AND SB1.D_E_L_E_T_ = ''

INNER JOIN SA1010 SA1
    ON SA1.A1_COD   = C5.C5_CLIENTE
   AND SA1.A1_LOJA  = C5.C5_LOJACLI
   AND SA1.D_E_L_E_T_ = ''

LEFT JOIN SB2010 SB2
    ON SB2.B2_COD    = C6.C6_PRODUTO
   AND SB2.B2_FILIAL = C6.C6_FILIAL
   AND SB2.B2_LOCAL  = '01'
   AND SB2.D_E_L_E_T_ = ''

WHERE
    C6.D_E_L_E_T_ = ''
    AND (C6.C6_QTDVEN - C6.C6_QTDENT) > 0
    AND (C6.C6_BLOQUEI IS NULL OR C6.C6_BLOQUEI = '')
    AND (C6.C6_BLQ IS NULL OR C6.C6_BLQ = '')

ORDER BY
    TIPO_ABERTO DESC,
    STATUS_PEDIDO,
    VALOR_ABERTO DESC

OFFSET @Offset ROWS
FETCH NEXT @PageSize ROWS ONLY;
```

### 17. Usuário: **"Comparação de tempo planejado × tempo real de ordens de produção (com setup, hora-mil e quantidade em milheiro)."**

#### 🎯 Objetivo

Identificar e analisar o **desempenho real das ordens de produção (OPs)** no Protheus,
comparando o **tempo planejado** (derivado do roteiro de operações)
com o **tempo real executado**, garantindo que:

- apenas **OPs ativas e finalizadas** sejam consideradas;
- o **tempo planejado** seja calculado de forma **determinística**, considerando:
  - **setup em horas** (uma única vez por operação);
  - **tempo padrão em hora-mil (HM)**;
  - **quantidade da OP expressa em milheiro**;
- o **tempo real** seja apurado a partir de **data + hora reais de início e fim**;
- o cálculo seja **auditável, reproduzível e alinhado ao PCP**;
- seja possível **identificar desvios de eficiência produtiva**, classificando as OPs em:
  - dentro do esperado;
  - atenção;
  - estouro de tempo.

O objetivo é **eliminar ambiguidades no cálculo de tempo produtivo**,
permitindo comparar **planejamento × execução real**,
identificar gargalos operacionais
e fornecer uma **base sólida para análise de eficiência, custos e melhoria contínua**.

---

#### 🧱 Tabelas envolvidas

##### SC2010 — Ordens de Produção

| Coluna | Descrição |
|------|----------|
| C2_FILIAL | Filial da OP |
| C2_OP | Número da ordem de produção |
| C2_PRODUTO | Código do produto |
| C2_QUANT | Quantidade planejada (**em milheiro**) |
| C2_QUJE | Quantidade produzida (em milheiro) |
| D_E_L_E_T_ | Exclusão lógica |

---

##### SD4010 — Requisições da Ordem de Produção

| Coluna | Descrição |
|------|----------|
| D4_FILIAL | Filial da requisição |
| D4_OP | Número da OP |
| D4_OPERAC | Código da operação |
| D_E_L_E_T_ | Exclusão lógica |

---

##### SG2010 — Roteiro de Operações

| Coluna | Descrição | Unidade |
|------|----------|--------|
| G2_FILIAL | Filial do roteiro | — |
| G2_PRODUTO | Código do produto | — |
| G2_OPERAC | Operação do roteiro | — |
| G2_SETUP | Tempo de setup | **Horas** |
| G2_TEMPAD | Tempo padrão | **Hora-mil** |
| D_E_L_E_T_ | Exclusão lógica | — |

---

##### SH8010 — Apontamento de Operações

| Coluna | Descrição |
|------|----------|
| H8_FILIAL | Filial do apontamento |
| H8_OP | Ordem de produção |
| H8_OPER | Operação |
| H8_DTINI | Data de início da operação |
| H8_HRINI | Hora de início da operação |
| H8_DTFIM | Data de fim da operação |
| H8_HRFIM | Hora de fim da operação |
| D_E_L_E_T_ | Exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Somente OPs ativas — `SC2010.D_E_L_E_T_ = ''`
- Somente requisições ativas — `SD4010.D_E_L_E_T_ = ''`
- Somente operações ativas — `SG2010.D_E_L_E_T_ = ''`
- Somente apontamentos ativos — `SH8010.D_E_L_E_T_ = ''`
- Somente OPs **finalizadas** — `C2_QUANT = C2_QUJE`
- Somente OPs com início na data analisada — `H8_DTINI = @DATA`
- Respeito estrito à **filial em todas as tabelas**

---

#### 🧠 Regras de cálculo do tempo planejado

##### Setup

- Origem: `SG2010.G2_SETUP`
- Unidade: **horas**
- Regra: considerado **uma única vez por operação**, sem multiplicação por quantidade

```
Setup_total (h) = Σ G2_SETUP
```

##### Tempo padrão (hora-mil)

- Origem: `SG2010.G2_TEMPAD`
- Unidade: **hora-mil (HM)**
- Quantidade da OP: `SC2010.C2_QUANT` (**em milheiro**)

```
Tempo_padrão (h) = G2_TEMPAD × C2_QUANT
```

##### Tempo planejado total

```
Tempo_planejado (h) = Setup_total + Tempo_padrão
```

---

#### ⏱️ Regras de cálculo do tempo real

```
Tempo_real (h) = DATEDIFF(MINUTE, DTINI+HRINI, DTFIM+HRFIM) / 60
```

---

#### 🧭 Regras de classificação do desempenho da OP

- **OK** → Tempo real ≤ tempo planejado
- **ATENÇÃO** → Tempo real ≤ tempo planejado × 1,10
- **ESTOURO** → Tempo real > tempo planejado × 1,10

---

#### 💾 Consulta

```sql
DECLARE @FILIAL VARCHAR(2) = '01';
DECLARE @DATA   DATE       = '2026-02-09';

WITH TEMPO_REAL AS (
    SELECT
        OP.C2_OP,
        CAST(
            SUM(
                DATEDIFF(
                    MINUTE,
                    CAST(OA.H8_DTINI AS DATETIME) + CAST(OA.H8_HRINI AS DATETIME),
                    CAST(OA.H8_DTFIM AS DATETIME) + CAST(OA.H8_HRFIM AS DATETIME)
                )
            ) / 60.0
        AS FLOAT) AS TEMPO_REAL_HORAS
    FROM SC2010 OP
    INNER JOIN SD4010 RE
        ON RE.D4_OP     = OP.C2_OP
       AND RE.D4_FILIAL = OP.C2_FILIAL
    INNER JOIN SH8010 OA
        ON OA.H8_OP      = RE.D4_OP
       AND OA.H8_OPER   = RE.D4_OPERAC
       AND OA.H8_FILIAL = OP.C2_FILIAL
    WHERE
            OP.C2_FILIAL = @FILIAL
        AND OA.H8_DTINI = @DATA
        AND OP.C2_QUANT = OP.C2_QUJE
        AND OP.D_E_L_E_T_ = ''
        AND RE.D_E_L_E_T_ = ''
        AND OA.D_E_L_E_T_ = ''
    GROUP BY
        OP.C2_OP
),

TEMPO_PLANEJADO AS (
    SELECT
        OP.C2_OP,
        OP.C2_PRODUTO,
        CAST(OP.C2_QUANT AS FLOAT)               AS QTD_MILHEIRO,
        CAST(OP.C2_QUANT * 1000 AS FLOAT)        AS QTD_UNIDADES,
        CAST(SUM(SG.G2_SETUP) AS FLOAT)          AS SETUP_HORAS,
        CAST(SUM(SG.G2_TEMPAD * OP.C2_QUANT) AS FLOAT)
                                                AS TEMPO_PADRAO_HORAS
    FROM SC2010 OP
    INNER JOIN SD4010 RE
        ON RE.D4_OP     = OP.C2_OP
       AND RE.D4_FILIAL = OP.C2_FILIAL
    INNER JOIN SG2010 SG
        ON SG.G2_FILIAL  = OP.C2_FILIAL
       AND SG.G2_PRODUTO = OP.C2_PRODUTO
       AND SG.G2_OPERAC  = RE.D4_OPERAC
    WHERE
            OP.C2_FILIAL = @FILIAL
        AND OP.C2_QUANT  = OP.C2_QUJE
        AND OP.D_E_L_E_T_ = ''
        AND RE.D_E_L_E_T_ = ''
        AND SG.D_E_L_E_T_ = ''
    GROUP BY
        OP.C2_OP,
        OP.C2_PRODUTO,
        OP.C2_QUANT
)

SELECT
    P.C2_OP,
    P.C2_PRODUTO,
    P.QTD_MILHEIRO,
    P.QTD_UNIDADES,
    P.SETUP_HORAS,
    P.TEMPO_PADRAO_HORAS,
    CAST(
        P.SETUP_HORAS + P.TEMPO_PADRAO_HORAS
    AS FLOAT)                                   AS TEMPO_PLANEJADO_HORAS,
    R.TEMPO_REAL_HORAS,
    CAST(
        R.TEMPO_REAL_HORAS -
        (P.SETUP_HORAS + P.TEMPO_PADRAO_HORAS)
    AS FLOAT)                                   AS DESVIO_HORAS,
    CASE
        WHEN R.TEMPO_REAL_HORAS <= (P.SETUP_HORAS + P.TEMPO_PADRAO_HORAS)
            THEN 'OK'
        WHEN R.TEMPO_REAL_HORAS <= (P.SETUP_HORAS + P.TEMPO_PADRAO_HORAS) * 1.10
            THEN 'ATENCAO'
        ELSE 'ESTOURO'
    END AS STATUS
FROM TEMPO_PLANEJADO P
INNER JOIN TEMPO_REAL R
    ON R.C2_OP = P.C2_OP
ORDER BY
    DESVIO_HORAS DESC;

```


### 18. Usuário: **"Quantidade consumida real do item 10080063 por produto do grupo 9030 no mês atual."**

#### 🎯 Objetivo

Identificar e documentar o **consumo real** do item **10080063** na base Protheus,
considerando apenas os **produtos acabados do grupo 9030**,
com apuração **por produto** dentro do **mês atual**.

O objetivo é garantir que o cálculo utilize a lógica correta da tabela **SD4010**,
eliminando a ambiguidade entre:

- **quantidade originalmente empenhada**;
- **saldo ainda não consumido**;
- **consumo real efetivo da matéria-prima**.

A consulta foi construída para responder com precisão:

- quais produtos do grupo **9030** consumiram o item **10080063**;
- quanto cada produto consumiu no período analisado;
- qual a lógica correta de cálculo do consumo real na **SD4**;
- como evitar interpretações incorretas usando apenas `D4_QTDEORI`.

---

#### 🧱 Tabelas envolvidas

##### SD4010 — Requisições da Ordem de Produção

| Coluna | Descrição |
|------|----------|
| D4_FILIAL | Filial da requisição |
| D4_COD | Código do item requisitado |
| D4_PRODUTO | Produto pai da requisição |
| D4_DATA | Data do empenho |
| D4_QTDEORI | Quantidade originalmente empenhada |
| D4_QUANT | Saldo da quantidade empenhada |
| D_E_L_E_T_ | Exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna | Descrição |
|------|----------|
| B1_COD | Código do produto |
| B1_DESC | Descrição do produto |
| B1_GRUPO | Grupo de estoque |
| D_E_L_E_T_ | Exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Somente registros ativos da SD4 — `SD4010.D_E_L_E_T_ = ''`
- Somente registros ativos da SB1 — `SB1010.D_E_L_E_T_ = ''`
- Somente o item analisado — `SD4010.D4_COD = '10080063'`
- Somente produtos do grupo **9030** — `SB1010.B1_GRUPO = '9030'`
- Somente registros do **mês atual**
- Somente consumo real positivo no resultado final

No caso validado em conversa, o mês atual foi tratado como:

- início: `20260301`
- fim: `20260331`

---

#### 🧠 Regra de cálculo do consumo real

##### Quantidade originalmente empenhada

- Origem: `SD4010.D4_QTDEORI`
- Significado: quantidade inicialmente reservada/empenhada para a OP
- **Não representa sozinha o consumo real**

##### Saldo da quantidade empenhada

- Origem: `SD4010.D4_QUANT`
- Significado: quantidade que ainda permanece como saldo do empenho
- Deve ser abatida da quantidade originalmente empenhada

##### Consumo real

A validação do schema e dos exemplos mostrou que a lógica correta é:

```sql
CASE
    WHEN D4_QTDEORI > D4_QUANT
    THEN D4_QTDEORI - D4_QUANT
    ELSE 0
END
```

Isso significa:

```text
Consumo real = Quantidade empenhada originalmente - Saldo ainda não consumido
```

---

#### ✅ Validação da lógica aplicada

Durante a validação da tabela **SD4010**, foi confirmado que:

- `D4_QTDEORI` = **Quantidade Empenhada**
- `D4_QUANT` = **Saldo da Quantidade Empenhada**

Portanto:

- usar apenas `D4_QTDEORI` pode superestimar consumo em cenários onde ainda exista saldo;
- o cálculo auditável e correto para consumo real é **`D4_QTDEORI - D4_QUANT`**;
- quando `D4_QUANT = 0`, o consumo real coincide com a quantidade empenhada original;
- quando existe saldo, o consumo real deve ser reduzido proporcionalmente.

---

#### 📦 Resultado esperado

A consulta retorna, para cada produto do grupo **9030**:

- código do produto pai;
- descrição do produto;
- quantidade consumida real do item **10080063** no mês atual.

Isso permite:

- medir o consumo real da matéria-prima por produto;
- comparar consumo entre itens do grupo 9030;
- alimentar análises de consumo, custo e rastreabilidade.

---

#### 💾 Consulta

```sql
SELECT
    SD4.D4_PRODUTO AS COD_PRODUTO,
    SB1.B1_DESC    AS DESC_PRODUTO,
    SUM(
        CASE
            WHEN SD4.D4_QTDEORI > SD4.D4_QUANT
            THEN SD4.D4_QTDEORI - SD4.D4_QUANT
            ELSE 0
        END
    ) AS QTD_CONSUMIDA
FROM SD4010 SD4
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = SD4.D4_PRODUTO
   AND SB1.D_E_L_E_T_ = ''
WHERE SD4.D_E_L_E_T_ = ''
  AND SD4.D4_COD = '10080063'
  AND SB1.B1_GRUPO = '9030'
  AND SD4.D4_DATA >= '20260301'
  AND SD4.D4_DATA <= '20260331'
GROUP BY
    SD4.D4_PRODUTO,
    SB1.B1_DESC
HAVING SUM(
        CASE
            WHEN SD4.D4_QTDEORI > SD4.D4_QUANT
            THEN SD4.D4_QTDEORI - SD4.D4_QUANT
            ELSE 0
        END
    ) > 0
ORDER BY QTD_CONSUMIDA DESC, SD4.D4_PRODUTO;
```

---

#### 📊 Resultado obtido no caso validado

| Código do produto | Descrição do produto | Quantidade consumida |
|------|----------|----------|
| 90300007 | CHICOTE DE LIGACAO - ROHS | 702.0 |
| 90300053 | CHICOTE DE LIGACAO - ROHS | 216.0 |
| 90300014 | CHICOTE DE LIGACAO - ROHS | 162.0 |
| 90300078 | RESISTOR ESTRELA 3W 25KVA 100K | 162.0 |
| 90300061 | RESISTOR RDC 3W 120K - ROHS | 150.0 |
| 90300064 | CHICOTE DE LIGACAO- 3W - ROHS | 150.0 |
| 90300073 | RESISTOR ESTRELA 3W 82K | 81.0 |
| 90300076 | RESISTOR ESTRELA 3W 25KVA 62K | 81.0 |
| 90300077 | RESISTOR ESTRELA 3W 25KVA 82K | 81.0 |

---

#### 🧭 Conclusão técnica

A documentação e a validação prática demonstram que a forma correta de medir o consumo real do item **10080063** na **SD4010** é:

- **não** usar `D4_QTDEORI` isoladamente;
- usar o cálculo **`D4_QTDEORI - D4_QUANT`**;
- filtrar os produtos do grupo desejado na **SB1010**;
- consolidar o resultado por produto pai (`D4_PRODUTO`).

Essa abordagem torna o cálculo:

- **determinístico**;
- **auditável**;
- **reproduzível**;
- aderente ao comportamento real do empenho e consumo da matéria-prima no Protheus.

### 19. Usuário: **“Listar os produtos mais comprados”**

#### 🎯 Objetivo

Listar os **produtos mais comprados em um período**, considerando os **itens das notas fiscais de entrada**, com possibilidade de análise por **filial**, permitindo identificar:

- os produtos com maior **quantidade comprada**;
- os produtos com maior **valor total comprado**;
- a **quantidade de notas fiscais** em que cada item apareceu;
- a **última data de compra** dentro do período analisado.

A consulta tem como finalidade:

- apoiar análises de **compras e suprimentos**;
- identificar itens de **maior giro de entrada**;
- apoiar negociações com fornecedores;
- dar visibilidade dos itens com maior peso no processo de compra.

---

#### 🧱 Tabelas envolvidas

##### SD1010 — Itens de Nota Fiscal de Entrada

| Coluna      | Descrição |
|------------|-----------|
| D1_FILIAL  | Filial |
| D1_COD     | Código do produto |
| D1_DOC     | Número da nota fiscal |
| D1_QUANT   | Quantidade comprada |
| D1_TOTAL   | Valor total do item |
| D1_EMISSAO | Data de emissão da nota |
| D1_FORNECE | Código do fornecedor |
| D1_LOJA    | Loja do fornecedor |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_TIPO    | Tipo do produto |
| B1_GRUPO   | Grupo do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SA2010 — Cadastro de Fornecedores *(opcional para filtros de fornecedor)*

| Coluna      | Descrição |
|------------|-----------|
| A2_COD     | Código do fornecedor |
| A2_LOJA    | Loja do fornecedor |
| A2_NOME    | Nome do fornecedor |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Período analisado  
  - `D1_EMISSAO >= :DATA_INICIO`  
  - `D1_EMISSAO < :DATA_FIM`

- Considerar somente registros ativos  
  - `SD1010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`

- Quando necessário, permitir corte por filial  
  - `D1_FILIAL = :FILIAL`

- Quando necessário, permitir exclusão de fornecedores específicos ou transportadoras via `SA2010`

---

#### 💾 Consulta

```sql
SELECT TOP 50
    SD1.D1_FILIAL                                   AS FILIAL,
    SD1.D1_COD                                      AS COD_PRODUTO,
    SB1.B1_DESC                                     AS DESCRICAO_PRODUTO,
    COUNT(DISTINCT SD1.D1_DOC)                      AS QTDE_NFS,
    SUM(SD1.D1_QUANT)                               AS QTD_TOTAL_COMPRADA,
    SUM(SD1.D1_TOTAL)                               AS VALOR_TOTAL_COMPRADO,
    MAX(SD1.D1_EMISSAO)                             AS ULTIMA_COMPRA
FROM SD1010 SD1
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = SD1.D1_COD
WHERE
    SD1.D_E_L_E_T_ = ''
    AND SB1.D_E_L_E_T_ = ''
    AND SD1.D1_EMISSAO >= :DATA_INICIO
    AND SD1.D1_EMISSAO < :DATA_FIM
GROUP BY
    SD1.D1_FILIAL,
    SD1.D1_COD,
    SB1.B1_DESC
ORDER BY
    SUM(SD1.D1_QUANT) DESC,
    SUM(SD1.D1_TOTAL) DESC,
    SD1.D1_COD ASC;
```

---

#### 🧠 Regras de interpretação

- **Tabela principal de compras:** `SD1010`
- **Descrição do produto:** `SB1010`
- **Quantidade comprada:** `SUM(D1_QUANT)`
- **Valor total comprado:** `SUM(D1_TOTAL)`
- **Quantidade de notas:** `COUNT(DISTINCT D1_DOC)`
- **Última compra no período:** `MAX(D1_EMISSAO)`

---

#### 🔁 Variação com filtro de fornecedor

Use esta versão quando a análise precisar:

- excluir fornecedores internos;
- desconsiderar transportadoras;
- filtrar compras válidas por fornecedor.

```sql
SELECT TOP 50
    SD1.D1_FILIAL                                   AS FILIAL,
    SD1.D1_COD                                      AS COD_PRODUTO,
    SB1.B1_DESC                                     AS DESCRICAO_PRODUTO,
    COUNT(DISTINCT SD1.D1_DOC)                      AS QTDE_NFS,
    SUM(SD1.D1_QUANT)                               AS QTD_TOTAL_COMPRADA,
    SUM(SD1.D1_TOTAL)                               AS VALOR_TOTAL_COMPRADO,
    MAX(SD1.D1_EMISSAO)                             AS ULTIMA_COMPRA
FROM SD1010 SD1
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = SD1.D1_COD
INNER JOIN SA2010 SA2
    ON SA2.A2_COD  = SD1.D1_FORNECE
   AND SA2.A2_LOJA = SD1.D1_LOJA
WHERE
    SD1.D_E_L_E_T_ = ''
    AND SB1.D_E_L_E_T_ = ''
    AND SA2.D_E_L_E_T_ = ''
    AND SD1.D1_EMISSAO >= :DATA_INICIO
    AND SD1.D1_EMISSAO < :DATA_FIM
    AND UPPER(SA2.A2_NOME) NOT LIKE '%TRANSP%'
GROUP BY
    SD1.D1_FILIAL,
    SD1.D1_COD,
    SB1.B1_DESC
ORDER BY
    SUM(SD1.D1_QUANT) DESC,
    SUM(SD1.D1_TOTAL) DESC,
    SD1.D1_COD ASC;
```

---

#### ✅ Resultado esperado

A consulta deve retornar, para cada produto comprado no período:

- filial;
- código do produto;
- descrição;
- quantidade de notas fiscais;
- quantidade total comprada;
- valor total comprado;
- data da última compra.

---

#### 📌 Observações

- Quando o usuário pedir **“os mais comprados”**, o critério principal deve ser **quantidade comprada** (`SUM(D1_QUANT)`).
- Quando o usuário pedir **“os que mais geraram valor de compra”**, o critério principal pode ser **valor total** (`SUM(D1_TOTAL)`).
- Quando o usuário pedir **por filial**, manter `D1_FILIAL` no `SELECT` e no `GROUP BY`.
- Quando o usuário pedir **geral**, remover `D1_FILIAL` do agrupamento.
- Quando o usuário pedir **Top N**, aplicar `TOP N` no `SELECT`.

---

### 20. Usuário: **“Listar os refugos de matéria-prima no período”**

#### 🎯 Objetivo

Listar os **registros de refugo/perda de matéria-prima** no Protheus dentro de um **período definido**, com rastreabilidade por:

- filial;
- data da perda;
- ordem de produção (OP);
- operação;
- matéria-prima perdida;
- quantidade perdida;
- motivo da perda;
- recurso / centro de trabalho;
- vínculo com movimentação de estoque.

A consulta tem como finalidade:

- identificar as **matérias-primas que geraram refugo**;
- apoiar análises de **perda produtiva e desperdício**;
- rastrear perdas por **OP, operação e recurso**;
- fornecer base auditável para indicadores de **refugo e sucata**.

---

#### 🧱 Tabelas envolvidas

##### SBC010 — Perda por OP

| Coluna      | Descrição |
|------------|-----------|
| BC_FILIAL  | Filial |
| BC_DATA    | Data da perda |
| BC_OP      | Ordem de produção |
| BC_OPERAC  | Operação |
| BC_PRODUTO | Produto perdido |
| BC_TIPO    | Tipo da perda (`R` = Refugo, `S` = Scrap) |
| BC_QUANT   | Quantidade da perda |
| BC_MOTIVO  | Motivo da perda |
| BC_RECURSO | Recurso / CT |
| BC_SEQSD3  | Sequência da movimentação SD3 |
| BC_IDENSH6 | Identificação vinculada ao SH6 |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

##### SB1010 — Cadastro de Produtos

| Coluna      | Descrição |
|------------|-----------|
| B1_COD     | Código do produto |
| B1_DESC    | Descrição do produto |
| B1_TIPO    | Tipo do produto |
| D_E_L_E_T_ | Indicador de exclusão lógica |

---

#### ⚙️ Condições aplicadas

- Período analisado  
  - `BC_DATA >= :DATA_INICIO`  
  - `BC_DATA < :DATA_FIM`

- Considerar somente registros ativos  
  - `SBC010.D_E_L_E_T_ = ''`  
  - `SB1010.D_E_L_E_T_ = ''`

- Considerar somente **matéria-prima**  
  - `SB1010.B1_TIPO = 'MP'`

- Considerar somente perdas classificadas como **refugo ou scrap**  
  - `BC_TIPO IN ('R','S')`

---

#### 💾 Consulta

```sql
SELECT TOP 50
    BC.BC_FILIAL                               AS FILIAL,
    BC.BC_DATA                                 AS DATA_PERDA,
    BC.BC_OP                                   AS OP,
    BC.BC_OPERAC                               AS OPERACAO,
    BC.BC_PRODUTO                              AS COD_MATERIA_PRIMA,
    SB1.B1_DESC                                AS DESCRICAO_MATERIA_PRIMA,
    BC.BC_TIPO                                 AS TIPO_PERDA,
    BC.BC_QUANT                                AS QTD_PERDA,
    BC.BC_MOTIVO                               AS MOTIVO_PERDA,
    BC.BC_RECURSO                              AS RECURSO,
    BC.BC_SEQSD3                               AS SEQ_SD3,
    BC.BC_IDENSH6                              AS ID_SH6
FROM SBC010 BC
INNER JOIN SB1010 SB1
    ON SB1.B1_COD = BC.BC_PRODUTO
WHERE
    BC.D_E_L_E_T_ = ''
    AND SB1.D_E_L_E_T_ = ''
    AND BC.BC_DATA >= :DATA_INICIO
    AND BC.BC_DATA < :DATA_FIM
    AND SB1.B1_TIPO = 'MP'
    AND BC.BC_TIPO IN ('R','S')
ORDER BY
    BC.BC_QUANT DESC,
    BC.BC_DATA DESC,
    BC.BC_PRODUTO ASC;
```

---

#### 🧠 Regras de interpretação

- **Tabela principal de refugo/perda:** `SBC010`
- **Produto perdido:** `BC_PRODUTO`
- **Descrição da matéria-prima:** `SB1010.B1_DESC`
- **Quantidade perdida:** `BC_QUANT`
- **Tipo da perda:**
  - `R = Refugo`
  - `S = Scrap`
- **Data da perda:** `BC_DATA`
- **Motivo da perda:** `BC_MOTIVO`
- **Recurso / CT:** `BC_RECURSO`
- **Rastreabilidade da movimentação:** `BC_SEQSD3`

---

#### ✅ Resultado esperado

A consulta deve retornar, para cada registro de perda no período:

- filial;
- data da perda;
- OP;
- operação;
- código da matéria-prima;
- descrição da matéria-prima;
- tipo da perda;
- quantidade perdida;
- motivo da perda;
- recurso;
- sequência da movimentação;
- vínculo com SH6, quando existir.

---

#### 📌 Observações

- Quando o usuário pedir **“refugos”**, priorizar `BC_TIPO = 'R'`.
- Quando o usuário pedir **“scrap”**, priorizar `BC_TIPO = 'S'`.
- Quando o usuário pedir **“perdas”**, manter `BC_TIPO IN ('R','S')`.
- Quando o usuário pedir **Top N**, aplicar `TOP N` no `SELECT`.
- Quando o usuário pedir **agrupado por matéria-prima**, consolidar com `SUM(BC_QUANT)` e `GROUP BY BC_PRODUTO, B1_DESC`.

---


