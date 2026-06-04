# Playbook DELPI — PA Produzido, Inspeção Final e Expedição

## 1. Objetivo

Este playbook define como saber se um produto acabado já foi finalizado e está liberado para expedição.

A regra operacional validada é:

```text
Depois que o PA é apontado no CT de inspeção final, ele já vai para expedição.
```

Portanto, para saber quanto de um PA está na expedição, não devemos olhar intermediários.

Devemos olhar somente:

```text
PA apontado no CT de INSPEÇÃO FINAL.
```

---

## 2. Regra-mãe

```text
Quantidade de PA em expedição =
SUM(H6_QTDPROD) dos apontamentos do PA no CT de INSPEÇÃO FINAL.
```

Perda na inspeção:

```text
Quantidade perdida na inspeção =
SUM(H6_QTDPERD) dos apontamentos do PA no CT de INSPEÇÃO FINAL.
```

---

## 3. Importante: somente PA entra na expedição

Intermediários `PI` continuam sendo parte da produção.

Eles não devem ser considerados como expedição.

Filtro obrigatório:

```sql
AND SB1.B1_TIPO = 'PA'
```

---

## 4. Tabelas usadas

### 4.1 SH6010 — Apontamento de produção

Tabela principal para saber o que foi realmente apontado.

Campos importantes:

| Campo | Uso |
|---|---|
| `H6_FILIAL` | Filial do apontamento |
| `H6_OP` | Ordem de produção apontada |
| `H6_PRODUTO` | Produto apontado |
| `H6_OPERAC` | Operação apontada |
| `H6_RECURSO` | Recurso apontado |
| `H6_QTDPROD` | Quantidade boa produzida |
| `H6_QTDPERD` | Quantidade perdida |
| `H6_DATAINI` | Data inicial |
| `H6_HORAINI` | Hora inicial |
| `H6_DATAFIN` | Data final |
| `H6_HORAFIN` | Hora final |
| `H6_DTAPONT` | Data do apontamento |
| `D_E_L_E_T_` | Exclusão lógica |

---

### 4.2 SH1010 — Recursos

Usada para descobrir a qual centro de trabalho pertence o recurso apontado.

Campos importantes:

| Campo | Uso |
|---|---|
| `H1_FILIAL` | Filial |
| `H1_CODIGO` | Código do recurso |
| `H1_DESCRI` | Nome do recurso |
| `H1_CTRAB` | Centro de trabalho do recurso |
| `D_E_L_E_T_` | Exclusão lógica |

Relação principal:

```sql
SH1.H1_FILIAL = H6.H6_FILIAL
SH1.H1_CODIGO = H6.H6_RECURSO
```

---

### 4.3 SHB010 — Centros de Trabalho

Usada para identificar quais CTs são de inspeção final.

Campos importantes:

| Campo | Uso |
|---|---|
| `HB_FILIAL` | Filial |
| `HB_COD` | Código do centro de trabalho |
| `HB_NOME` | Nome do centro de trabalho |
| `HB_CC` | Centro de custo |
| `HB_LOCAL` | Armazém vinculado, quando existir |
| `D_E_L_E_T_` | Exclusão lógica |

Filtro para localizar CT de inspeção final:

```sql
UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
```

---

### 4.4 SB1010 — Cadastro de produtos

Usada para garantir que o produto analisado é PA.

Campos importantes:

| Campo | Uso |
|---|---|
| `B1_COD` | Código do produto |
| `B1_DESC` | Descrição |
| `B1_TIPO` | Tipo do produto |
| `B1_UM` | Unidade |
| `D_E_L_E_T_` | Exclusão lógica |

Filtro obrigatório:

```sql
SB1.B1_TIPO = 'PA'
```

---

## 5. CTs de inspeção final confirmados

Consulta realizada na `SHB010` confirmou:

| Filial | CT | Nome CT | Centro de custo |
|---|---|---|---|
| `01` | `CT-70` | `INSPEÇÃO FINAL` | `349` |
| `02` | `CT-99` | `INSPECAO FINAL` | `399` |

Portanto:

```text
Filial 01 → CT-70 → INSPEÇÃO FINAL
Filial 02 → CT-99 → INSPECAO FINAL
```

---

## 6. Como interpretar expedição

### 6.1 PA apontado no CT de inspeção final com quantidade boa

Se o PA teve apontamento no CT de inspeção final e `H6_QTDPROD > 0`:

```text
PA finalizado e liberado para expedição.
```

### 6.2 PA apontado no CT de inspeção final com perda

Se o PA teve apontamento no CT de inspeção final, mas `H6_QTDPROD = 0` e `H6_QTDPERD > 0`:

```text
PA passou pela inspeção, mas não gerou quantidade boa para expedição.
```

### 6.3 PA sem apontamento no CT de inspeção final

Se não existe apontamento do PA no CT de inspeção final:

```text
PA ainda não está finalizado para expedição pela regra validada.
```

---

## 7. Query — Descobrir CTs de inspeção final por filial

```sql
SELECT
    HB_FILIAL AS FILIAL,
    HB_COD AS CT,
    HB_NOME AS NOME_CT,
    HB_CC AS CENTRO_CUSTO,
    HB_LOCAL AS ARMAZEM_CONSUMO
FROM SHB010 WITH (NOLOCK)
WHERE
    D_E_L_E_T_ = ''
    AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
ORDER BY
    HB_FILIAL,
    HB_COD;
```

Resultado validado:

| Filial | CT | Nome |
|---|---|---|
| `01` | `CT-70` | `INSPEÇÃO FINAL` |
| `02` | `CT-99` | `INSPECAO FINAL` |

---

## 8. Query — Quanto de um PA está na expedição por período

Esta é a query principal.

Ela retorna a quantidade finalizada para expedição de um PA específico, considerando apenas apontamentos no CT de inspeção final.

Trocar:

```sql
SET @PRODUTO = '90260951';
SET @DATA_INI = '20260604';
SET @DATA_FIM = '20260605';
```

Observação:

Usar intervalo fechado-aberto:

```sql
H6_DTAPONT >= @DATA_INI
H6_DTAPONT < @DATA_FIM
```

Query:

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @DATA_INI VARCHAR(8);
DECLARE @DATA_FIM VARCHAR(8);

SET @PRODUTO = '90260951';
SET @DATA_INI = '20260604';
SET @DATA_FIM = '20260605';

WITH CTS_INSPECAO AS (
    SELECT
        HB_FILIAL AS FILIAL,
        HB_COD AS CT_INSPECAO,
        HB_NOME AS NOME_CT_INSPECAO
    FROM SHB010 WITH (NOLOCK)
    WHERE
        D_E_L_E_T_ = ''
        AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
),

APONTAMENTO_PA_INSPECAO AS (
    SELECT
        H6.H6_FILIAL AS FILIAL,
        H6.H6_PRODUTO AS PRODUTO,
        SB1.B1_DESC AS DESCRICAO,
        SB1.B1_TIPO AS TIPO,
        SB1.B1_UM AS UNIDADE,

        H6.H6_OP AS OP,
        H6.H6_OPERAC AS OPERACAO,
        H6.H6_RECURSO AS RECURSO,

        SH1.H1_DESCRI AS NOME_RECURSO,
        SH1.H1_CTRAB AS CT,
        CT.NOME_CT_INSPECAO,

        SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_FINALIZADA_EXPEDICAO,
        SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_INSPECAO,
        COUNT(*) AS TOTAL_APONTAMENTOS,

        MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO,
        MIN(H6.H6_HORAINI) AS PRIMEIRA_HORA,
        MAX(H6.H6_DATAFIN) AS ULTIMO_FIM,
        MAX(H6.H6_HORAFIN) AS ULTIMA_HORA,
        MAX(H6.H6_DTAPONT) AS ULTIMO_APONTAMENTO
    FROM SH6010 H6 WITH (NOLOCK)
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = H6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
       AND SB1.B1_TIPO = 'PA'
    INNER JOIN SH1010 SH1 WITH (NOLOCK)
        ON SH1.H1_FILIAL = H6.H6_FILIAL
       AND SH1.H1_CODIGO = H6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ''
    INNER JOIN CTS_INSPECAO CT
        ON CT.FILIAL = H6.H6_FILIAL
       AND CT.CT_INSPECAO = SH1.H1_CTRAB
    WHERE
        H6.D_E_L_E_T_ = ''
        AND H6.H6_PRODUTO = @PRODUTO
        AND H6.H6_DTAPONT >= @DATA_INI
        AND H6.H6_DTAPONT < @DATA_FIM
    GROUP BY
        H6.H6_FILIAL,
        H6.H6_PRODUTO,
        SB1.B1_DESC,
        SB1.B1_TIPO,
        SB1.B1_UM,
        H6.H6_OP,
        H6.H6_OPERAC,
        H6.H6_RECURSO,
        SH1.H1_DESCRI,
        SH1.H1_CTRAB,
        CT.NOME_CT_INSPECAO
)

SELECT
    FILIAL,
    PRODUTO,
    DESCRICAO,
    TIPO,
    UNIDADE,
    OP,
    OPERACAO,
    RECURSO,
    NOME_RECURSO,
    CT,
    NOME_CT_INSPECAO,
    CAST(QTD_FINALIZADA_EXPEDICAO AS VARCHAR(50)) AS QTD_FINALIZADA_EXPEDICAO,
    CAST(QTD_PERDIDA_INSPECAO AS VARCHAR(50)) AS QTD_PERDIDA_INSPECAO,
    TOTAL_APONTAMENTOS,
    PRIMEIRO_INICIO,
    PRIMEIRA_HORA,
    ULTIMO_FIM,
    ULTIMA_HORA,
    ULTIMO_APONTAMENTO
FROM APONTAMENTO_PA_INSPECAO
ORDER BY
    FILIAL,
    OP,
    OPERACAO,
    RECURSO;
```

---

## 9. Query — Ranking de PAs finalizados para expedição em uma data

Esta query lista PAs finalizados na inspeção final, em todas as filiais, dentro do período informado.

```sql
DECLARE @DATA_INI VARCHAR(8);
DECLARE @DATA_FIM VARCHAR(8);

SET @DATA_INI = '20260604';
SET @DATA_FIM = '20260605';

WITH CTS_INSPECAO AS (
    SELECT
        HB_FILIAL AS FILIAL,
        HB_COD AS CT_INSPECAO,
        HB_NOME AS NOME_CT_INSPECAO
    FROM SHB010 WITH (NOLOCK)
    WHERE
        D_E_L_E_T_ = ''
        AND UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
),

APONTAMENTO_PA_INSPECAO AS (
    SELECT
        H6.H6_FILIAL AS FILIAL,
        H6.H6_PRODUTO AS PRODUTO,
        SB1.B1_DESC AS DESCRICAO,
        SB1.B1_TIPO AS TIPO,
        SB1.B1_UM AS UNIDADE,

        H6.H6_OP AS OP,
        H6.H6_OPERAC AS OPERACAO,
        H6.H6_RECURSO AS RECURSO,

        SH1.H1_DESCRI AS NOME_RECURSO,
        SH1.H1_CTRAB AS CT,
        CT.NOME_CT_INSPECAO,

        SUM(CAST(H6.H6_QTDPROD AS FLOAT)) AS QTD_FINALIZADA_EXPEDICAO,
        SUM(CAST(H6.H6_QTDPERD AS FLOAT)) AS QTD_PERDIDA_INSPECAO,
        COUNT(*) AS TOTAL_APONTAMENTOS,

        MIN(H6.H6_DATAINI) AS PRIMEIRO_INICIO,
        MIN(H6.H6_HORAINI) AS PRIMEIRA_HORA,
        MAX(H6.H6_DATAFIN) AS ULTIMO_FIM,
        MAX(H6.H6_HORAFIN) AS ULTIMA_HORA,
        MAX(H6.H6_DTAPONT) AS ULTIMO_APONTAMENTO
    FROM SH6010 H6 WITH (NOLOCK)
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = H6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ''
       AND SB1.B1_TIPO = 'PA'
    INNER JOIN SH1010 SH1 WITH (NOLOCK)
        ON SH1.H1_FILIAL = H6.H6_FILIAL
       AND SH1.H1_CODIGO = H6.H6_RECURSO
       AND SH1.D_E_L_E_T_ = ''
    INNER JOIN CTS_INSPECAO CT
        ON CT.FILIAL = H6.H6_FILIAL
       AND CT.CT_INSPECAO = SH1.H1_CTRAB
    WHERE
        H6.D_E_L_E_T_ = ''
        AND H6.H6_DTAPONT >= @DATA_INI
        AND H6.H6_DTAPONT < @DATA_FIM
    GROUP BY
        H6.H6_FILIAL,
        H6.H6_PRODUTO,
        SB1.B1_DESC,
        SB1.B1_TIPO,
        SB1.B1_UM,
        H6.H6_OP,
        H6.H6_OPERAC,
        H6.H6_RECURSO,
        SH1.H1_DESCRI,
        SH1.H1_CTRAB,
        CT.NOME_CT_INSPECAO
)

SELECT TOP 20
    FILIAL,
    PRODUTO,
    DESCRICAO,
    UNIDADE,
    OP,
    OPERACAO,
    RECURSO,
    NOME_RECURSO,
    CT,
    NOME_CT_INSPECAO,
    CAST(QTD_FINALIZADA_EXPEDICAO AS VARCHAR(50)) AS QTD_FINALIZADA_EXPEDICAO,
    CAST(QTD_PERDIDA_INSPECAO AS VARCHAR(50)) AS QTD_PERDIDA_INSPECAO,
    TOTAL_APONTAMENTOS,
    PRIMEIRO_INICIO,
    PRIMEIRA_HORA,
    ULTIMO_FIM,
    ULTIMA_HORA,
    ULTIMO_APONTAMENTO
FROM APONTAMENTO_PA_INSPECAO
ORDER BY
    QTD_FINALIZADA_EXPEDICAO DESC,
    QTD_PERDIDA_INSPECAO DESC,
    PRODUTO,
    OP;
```

---

## 10. Resultado validado — 20260604

Teste executado para a data:

```text
20260604
```

A query retornou PAs apontados no CT de inspeção final.

Top exemplos:

| Filial | PA | Descrição | OP | CT | Qtd. finalizada expedição | Perda inspeção |
|---|---|---|---|---|---:|---:|
| `01` | `90300080` | CHICOTE DE LIGACAO | `24463901001` | `CT-70` | 1 | 0 |
| `02` | `90262126` | CHICOTE DE LIGAÇAO | `10429001001` | `CT-99` | 0.6 | 0 |
| `01` | `90262401` | CHICOTE DE LIGAÇAO | `24514601001` | `CT-70` | 0.5 | 0 |
| `01` | `90264227` | CHICOTE TRR-ITCC-0039 | `24524701001` | `CT-70` | 0.5 | 0 |
| `01` | `90310075` | TAMPA UCW | `24517001001` | `CT-70` | 0.5 | 0 |
| `02` | `90262982` | CHICOTE DE LIGAÇÃO | `10478001001` | `CT-99` | 0.4 | 0 |

---

## 11. Resultado validado — PA com perda na inspeção

Produto testado:

```text
90260951 — CHICOTE DE LIGACAO
Data: 20260604
Filial: 01
CT: CT-70 — INSPEÇÃO FINAL
```

Resultado:

| OP | Operação | CT | Qtd. finalizada expedição | Qtd. perdida inspeção |
|---|---|---|---:|---:|
| `24531901001` | `06` | `CT-70` | 0 | 0.003 |
| `24556901001` | `06` | `CT-70` | 0 | 0.010 |
| `24557001001` | `06` | `CT-70` | 0 | 0.010 |

Conclusão:

```text
O PA 90260951 passou pela inspeção final em 20260604, mas não gerou quantidade boa para expedição.
A quantidade apontada no CT-70 foi perda de inspeção.
```

---

## 12. Diferença entre produção e expedição

### Produção iniciada

Pode ser qualquer apontamento produtivo do PA ou PI.

Base:

```text
SH6010
```

Inclui:

```text
PA e PI
```

### Expedição do PA

É somente apontamento do PA no CT de inspeção final.

Base:

```text
SH6010 + SH1010 + SHB010
```

Inclui somente:

```text
PA
```

Não inclui:

```text
PI
MP
```

---

## 13. Como responder quando perguntarem “quanto está na expedição?”

Modelo:

```text
Para o PA [produto], no período [data inicial] a [data final]:

Qtd. finalizada para expedição: [SUM H6_QTDPROD no CT inspeção final]
Qtd. perdida na inspeção: [SUM H6_QTDPERD no CT inspeção final]
Filial: [filial]
CT de inspeção final: [CT] — [nome]
OPs consideradas: [lista]
```

Exemplo:

```text
Para o PA 90300080 em 20260604:
Qtd. finalizada para expedição: 1 MI
Perda na inspeção: 0
Filial: 01
CT: CT-70 — INSPEÇÃO FINAL
OP: 24463901001
```

---

## 14. Alertas importantes

### 14.1 Não usar intermediários para expedição

PI pode ser produzido, mas não representa produto em expedição.

```text
Expedição é somente PA.
```

### 14.2 Não usar apenas estoque

O saldo em estoque pode ajudar, mas a regra operacional validada foi:

```text
PA apontado na inspeção final já vai para expedição.
```

Então a evidência primária é:

```text
Apontamento no CT de inspeção final.
```

### 14.3 Quantidade perdida não entra na expedição

Se `H6_QTDPERD > 0`, isso representa perda/reprovação na inspeção.

Não somar perda como expedição.

```text
Expedição = H6_QTDPROD
Perda = H6_QTDPERD
```

### 14.4 Usar CT oficial da filial

Não fixar apenas `CT-70`.

A filial 02 usa outro CT.

Regra dinâmica:

```sql
UPPER(HB_NOME) LIKE '%INSPE%FINAL%'
```

Assim a query encontra:

```text
Filial 01 → CT-70
Filial 02 → CT-99
```

---

## 15. Checklist técnico

Antes de concluir que um PA está na expedição:

- [ ] Produto é `PA` na `SB1010`;
- [ ] Existe apontamento na `SH6010`;
- [ ] Recurso do apontamento existe na `SH1010`;
- [ ] Recurso aponta para CT em `H1_CTRAB`;
- [ ] CT está cadastrado na `SHB010`;
- [ ] Nome do CT contém `INSPEÇÃO FINAL` ou `INSPECAO FINAL`;
- [ ] Somar apenas `H6_QTDPROD`;
- [ ] Separar `H6_QTDPERD` como perda;
- [ ] Não considerar PI;
- [ ] Filtrar `D_E_L_E_T_ = ''` em todas as tabelas;
- [ ] Usar período com intervalo fechado-aberto.

---

## 16. Resumo final

```text
Para saber quanto de um PA está na expedição, consulte os apontamentos reais da SH6010 do produto tipo PA, una com SH1010 para descobrir o CT do recurso, una com SHB010 para garantir que o CT é INSPEÇÃO FINAL, e some H6_QTDPROD. Intermediários não entram nessa conta.
```