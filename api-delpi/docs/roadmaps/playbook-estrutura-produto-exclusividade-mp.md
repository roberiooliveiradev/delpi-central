# Playbook DELPI — Estrutura de Produto, BOM Multinível e Matérias-Primas Exclusivas

## 1. Objetivo

Este playbook consolida o conhecimento validado durante os testes de consulta de estrutura de produto no Protheus DELPI.

Ele cobre:

- Consulta da estrutura completa de um produto;
- Abertura multinível da BOM;
- Tratamento de intermediários;
- Filtro correto de vigência;
- Comparação com a rota oficial `/products/{code}/structure`;
- Identificação de matérias-primas exclusivas;
- Exclusão de produtos de teste/amostra iniciados por `8000` e `8001`.

---

## 2. Tabelas principais

### 2.1 SG1010 — Estrutura do produto

A tabela principal da estrutura/BOM é:

- `SG1010`

Campos principais:

| Campo | Significado |
|---|---|
| `G1_COD` | Produto pai |
| `G1_COMP` | Componente filho |
| `G1_QUANT` | Quantidade do componente na estrutura |
| `G1_INI` | Data inicial de vigência |
| `G1_FIM` | Data final de vigência |
| `D_E_L_E_T_` | Exclusão lógica |

---

### 2.2 SB1010 — Cadastro de produtos

A tabela de cadastro do produto é:

- `SB1010`

Campos principais:

| Campo | Significado |
|---|---|
| `B1_COD` | Código do produto |
| `B1_DESC` | Descrição |
| `B1_TIPO` | Tipo do produto |
| `B1_UM` | Unidade de medida |
| `B1_GRUPO` | Grupo do produto |
| `D_E_L_E_T_` | Exclusão lógica |

Tipos importantes:

| Tipo | Significado |
|---|---|
| `PA` | Produto acabado |
| `PI` | Produto intermediário |
| `MP` | Matéria-prima |

---

## 3. Regra essencial de vigência

A rota oficial de estrutura considera somente componentes vigentes.

Nos testes, a SQL sem filtro de vigência retornou itens históricos/vencidos.

Para reproduzir a rota `/products/{code}/structure`, usar:

```sql
AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
```

Também pode ser usado filtro completo de intervalo:

```sql
AND (G1.G1_INI = '' OR G1.G1_INI <= CONVERT(CHAR(8), GETDATE(), 112))
AND (G1.G1_FIM = '' OR G1.G1_FIM >= CONVERT(CHAR(8), GETDATE(), 112))
```

Porém, a lógica observada na rota usa principalmente:

```sql
G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
```

---

## 4. Query base — Estrutura completa multinível

Esta query abre a estrutura completa de um produto, incluindo intermediários e matérias-primas.

Trocar apenas:

```sql
SET @PRODUTO = '90260149';
```

por outro código.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90260149';
SET @MAX_DEPTH = 50;

WITH recursive_bom AS (
    SELECT 
        G1_COD   AS parent_code,
        G1_COMP  AS component_code,
        G1_QUANT AS quantity,
        1        AS bom_level
    FROM SG1010 WITH (NOLOCK)
    WHERE D_E_L_E_T_ = ''
      AND G1_COD = @PRODUTO
      AND G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT 
        c.G1_COD,
        c.G1_COMP,
        c.G1_QUANT,
        p.bom_level + 1
    FROM SG1010 c WITH (NOLOCK)
    INNER JOIN recursive_bom p
        ON p.component_code = c.G1_COD
    WHERE c.D_E_L_E_T_ = ''
      AND p.bom_level < @MAX_DEPTH
      AND c.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
)

SELECT 
    rb.bom_level AS NIVEL,

    rb.parent_code AS PRODUTO_PAI,
    parent.B1_DESC AS DESC_PRODUTO_PAI,
    parent.B1_TIPO AS TIPO_PRODUTO_PAI,
    parent.B1_UM   AS UNIDADE_PRODUTO_PAI,

    rb.component_code AS COMPONENTE,
    comp.B1_DESC      AS DESC_COMPONENTE,
    comp.B1_TIPO      AS TIPO_COMPONENTE,
    comp.B1_UM        AS UNIDADE_COMPONENTE,

    rb.quantity AS QTD_POR
FROM recursive_bom rb
LEFT JOIN SB1010 parent WITH (NOLOCK)
    ON parent.B1_COD = rb.parent_code
   AND parent.D_E_L_E_T_ = ''
LEFT JOIN SB1010 comp WITH (NOLOCK)
    ON comp.B1_COD = rb.component_code
   AND comp.D_E_L_E_T_ = ''
ORDER BY
    rb.bom_level,
    rb.parent_code,
    rb.component_code
OPTION (MAXRECURSION 0);
```

---

## 5. Validação feita com o produto 90260149

Produto testado:

```text
90260149 — CHICOTE EPR SINGELO 235MM
```

Resultado observado:

- SQL sem filtro de vigência: 42 registros;
- Rota `/products/90260149/structure`: 24 registros;
- SQL com filtro de vigência: 24 registros.

Conclusão:

A rota oficial retorna somente estrutura vigente.

Itens vencidos aparecem na SQL se não houver filtro por `G1_FIM`.

---

## 6. Conceito de matéria-prima exclusiva

Uma matéria-prima é considerada exclusiva quando:

```text
Ela aparece em estruturas vigentes de apenas 1 produto acabado válido.
```

A análise deve considerar:

- Estrutura multinível;
- Intermediários dentro do PA;
- MPs escondidas dentro de PIs;
- Somente registros ativos;
- Somente estruturas vigentes;
- Somente PAs reais de produção.

---

## 7. Regra para ignorar PAs de teste/amostra

Produtos acabados cujo código começa com `8000` ou `8001` devem ser ignorados.

Eles são considerados amostras ou testes e não representam produtos normais de produção.

Filtro obrigatório:

```sql
AND PA.B1_COD NOT LIKE '8000%'
AND PA.B1_COD NOT LIKE '8001%'
```

---

## 8. Query — Listar 5 matérias-primas exclusivas e seus PAs

Esta query encontra 5 MPs exclusivas, desconsiderando PAs `8000%` e `8001%`.

```sql
WITH ESTRUTURA_PA AS (
    SELECT
        PA.B1_COD       AS PA_RAIZ,
        PA.B1_DESC      AS DESC_PA_RAIZ,
        PA.B1_UM        AS UNIDADE_PA,
        G1.G1_COD       AS PRODUTO_PAI,
        G1.G1_COMP      AS COMPONENTE,
        1               AS NIVEL
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN SB1010 PA WITH (NOLOCK)
        ON PA.B1_COD = G1.G1_COD
       AND PA.D_E_L_E_T_ = ''
       AND PA.B1_TIPO = 'PA'
       AND PA.B1_COD NOT LIKE '8000%'
       AND PA.B1_COD NOT LIKE '8001%'
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        EP.PA_RAIZ,
        EP.DESC_PA_RAIZ,
        EP.UNIDADE_PA,
        G1.G1_COD,
        G1.G1_COMP,
        EP.NIVEL + 1
    FROM ESTRUTURA_PA EP
    INNER JOIN SG1010 G1 WITH (NOLOCK)
        ON G1.G1_COD = EP.COMPONENTE
       AND G1.D_E_L_E_T_ = ''
       AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
    WHERE
        EP.NIVEL < 50
),

MP_POR_PA AS (
    SELECT DISTINCT
        EP.COMPONENTE AS COD_MP,
        MP.B1_DESC    AS DESC_MP,
        MP.B1_UM      AS UNIDADE_MP,
        MP.B1_GRUPO   AS GRUPO_MP,
        EP.PA_RAIZ,
        EP.DESC_PA_RAIZ,
        EP.UNIDADE_PA
    FROM ESTRUTURA_PA EP
    INNER JOIN SB1010 MP WITH (NOLOCK)
        ON MP.B1_COD = EP.COMPONENTE
       AND MP.D_E_L_E_T_ = ''
       AND MP.B1_TIPO = 'MP'
),

MP_EXCLUSIVA AS (
    SELECT
        COD_MP
    FROM MP_POR_PA
    GROUP BY
        COD_MP
    HAVING
        COUNT(DISTINCT PA_RAIZ) = 1
)

SELECT TOP 5
    M.COD_MP,
    M.DESC_MP,
    M.UNIDADE_MP,
    M.GRUPO_MP,
    M.PA_RAIZ AS COD_PA,
    M.DESC_PA_RAIZ AS DESC_PA,
    M.UNIDADE_PA,
    'SIM' AS MP_EXCLUSIVA
FROM MP_POR_PA M
INNER JOIN MP_EXCLUSIVA E
    ON E.COD_MP = M.COD_MP
ORDER BY
    M.COD_MP,
    M.PA_RAIZ
OPTION (MAXRECURSION 0);
```

---

## 9. Resultado validado da query de exclusivas

Após excluir PAs `8000%` e `8001%`, a consulta retornou exemplos como:

| MP | PA |
|---|---|
| `10010001` | `90290024` |
| `10010002` | `90290057` |
| `10010004` | `90310010` |
| `10010032` | `90261255` |
| `10010065` | `90262888` |

Exemplo importante:

```text
MP 10010032 apareceu como exclusiva do PA 90261255.
```

---

## 10. Query — Estrutura de um produto mostrando exclusividade das MPs

Esta é a query principal para consultar a estrutura de um produto e marcar se cada matéria-prima é exclusiva.

Ela:

- Abre a estrutura vigente do produto;
- Considera intermediários;
- Calcula quantidade acumulada;
- Marca `MP_EXCLUSIVA = SIM/NAO`;
- Conta em quantos PAs válidos a MP aparece;
- Desconsidera PAs `8000%` e `8001%`.

Trocar:

```sql
SET @PRODUTO = '90261255';
```

pelo produto desejado.

```sql
DECLARE @PRODUTO VARCHAR(30);
DECLARE @MAX_DEPTH INT;

SET @PRODUTO = '90261255';
SET @MAX_DEPTH = 50;

WITH ESTRUTURA_PRODUTO AS (
    SELECT
        G1.G1_COD   AS PRODUTO_PAI,
        G1.G1_COMP  AS COMPONENTE,
        G1.G1_QUANT AS QTD_POR,
        CAST(G1.G1_QUANT AS FLOAT) AS QTD_ACUMULADA,
        1           AS NIVEL,
        CAST(G1.G1_COD + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS CAMINHO
    FROM SG1010 G1 WITH (NOLOCK)
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_COD = @PRODUTO
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        G1.G1_COD,
        G1.G1_COMP,
        G1.G1_QUANT,
        CAST(EP.QTD_ACUMULADA * CAST(G1.G1_QUANT AS FLOAT) AS FLOAT) AS QTD_ACUMULADA,
        EP.NIVEL + 1,
        CAST(EP.CAMINHO + ' > ' + G1.G1_COMP AS VARCHAR(MAX)) AS CAMINHO
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN ESTRUTURA_PRODUTO EP
        ON EP.COMPONENTE = G1.G1_COD
    WHERE
        G1.D_E_L_E_T_ = ''
        AND EP.NIVEL < @MAX_DEPTH
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
),

MATERIAS_PRIMAS_DO_PRODUTO AS (
    SELECT DISTINCT
        EP.COMPONENTE AS COD_MP
    FROM ESTRUTURA_PRODUTO EP
    INNER JOIN SB1010 SB1 WITH (NOLOCK)
        ON SB1.B1_COD = EP.COMPONENTE
       AND SB1.D_E_L_E_T_ = ''
    WHERE
        SB1.B1_TIPO = 'MP'
),

TODAS_ESTRUTURAS_VALIDAS AS (
    SELECT
        PA.B1_COD  AS PA_RAIZ,
        PA.B1_DESC AS DESC_PA_RAIZ,
        G1.G1_COD  AS PRODUTO_PAI,
        G1.G1_COMP AS COMPONENTE,
        1          AS NIVEL
    FROM SG1010 G1 WITH (NOLOCK)
    INNER JOIN SB1010 PA WITH (NOLOCK)
        ON PA.B1_COD = G1.G1_COD
       AND PA.D_E_L_E_T_ = ''
       AND PA.B1_TIPO = 'PA'
       AND PA.B1_COD NOT LIKE '8000%'
       AND PA.B1_COD NOT LIKE '8001%'
    WHERE
        G1.D_E_L_E_T_ = ''
        AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)

    UNION ALL

    SELECT
        TE.PA_RAIZ,
        TE.DESC_PA_RAIZ,
        G1.G1_COD,
        G1.G1_COMP,
        TE.NIVEL + 1
    FROM TODAS_ESTRUTURAS_VALIDAS TE
    INNER JOIN SG1010 G1 WITH (NOLOCK)
        ON G1.G1_COD = TE.COMPONENTE
       AND G1.D_E_L_E_T_ = ''
       AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
    WHERE
        TE.NIVEL < @MAX_DEPTH
),

USO_MP_EM_PA AS (
    SELECT
        TE.COMPONENTE AS COD_MP,
        COUNT(DISTINCT TE.PA_RAIZ) AS TOTAL_PAS_VALIDOS,
        MIN(TE.PA_RAIZ) AS UNICO_PA_QUANDO_EXCLUSIVA
    FROM TODAS_ESTRUTURAS_VALIDAS TE
    INNER JOIN MATERIAS_PRIMAS_DO_PRODUTO MP
        ON MP.COD_MP = TE.COMPONENTE
    GROUP BY
        TE.COMPONENTE
)

SELECT
    EP.NIVEL,
    EP.PRODUTO_PAI,
    PAI.B1_DESC AS DESC_PRODUTO_PAI,
    EP.COMPONENTE,
    COMP.B1_DESC AS DESC_COMPONENTE,
    COMP.B1_TIPO AS TIPO_COMPONENTE,
    COMP.B1_UM AS UNIDADE_COMPONENTE,
    COMP.B1_GRUPO AS GRUPO_COMPONENTE,
    CAST(EP.QTD_POR AS VARCHAR(50)) AS QTD_POR,
    CAST(EP.QTD_ACUMULADA AS VARCHAR(50)) AS QTD_ACUMULADA,
    CASE
        WHEN COMP.B1_TIPO = 'MP' AND ISNULL(U.TOTAL_PAS_VALIDOS, 0) = 1 THEN 'SIM'
        WHEN COMP.B1_TIPO = 'MP' THEN 'NAO'
        ELSE NULL
    END AS MP_EXCLUSIVA,
    CASE
        WHEN COMP.B1_TIPO = 'MP' THEN ISNULL(U.TOTAL_PAS_VALIDOS, 0)
        ELSE NULL
    END AS TOTAL_PAS_VALIDOS_ONDE_MP_APARECE,
    EP.CAMINHO
FROM ESTRUTURA_PRODUTO EP
LEFT JOIN SB1010 PAI WITH (NOLOCK)
    ON PAI.B1_COD = EP.PRODUTO_PAI
   AND PAI.D_E_L_E_T_ = ''
LEFT JOIN SB1010 COMP WITH (NOLOCK)
    ON COMP.B1_COD = EP.COMPONENTE
   AND COMP.D_E_L_E_T_ = ''
LEFT JOIN USO_MP_EM_PA U
    ON U.COD_MP = EP.COMPONENTE
ORDER BY
    EP.CAMINHO
OPTION (MAXRECURSION 0);
```

---

## 11. Resultado validado para o produto 90261255

Produto:

```text
90261255 — CHICOTE DE LIGACAO CLIENTE KAVO
```

Resultado:

- Total retornado: 23 itens;
- MPs exclusivas encontradas: 2;
- PAs `8000%` e `8001%` foram ignorados.

MPs exclusivas:

| MP | Descrição | Onde aparece |
|---|---|---|
| `10070183` | CABO MANGA CIRCULAR PVC/PVC 8X0,25MM2 CZ MR/VM/LA/AR/AL/RA/CZ/PT 70°C 750V | Direto no PA `90261255` |
| `10010032` | CABO PVC 70°C 22AWG LA 300V NM 247-3 | Dentro do intermediário `50212155` |

---

## 12. Interpretação dos campos da query final

| Campo | Significado |
|---|---|
| `NIVEL` | Nível da estrutura |
| `PRODUTO_PAI` | Pai imediato do componente |
| `DESC_PRODUTO_PAI` | Descrição do pai |
| `COMPONENTE` | Código do componente |
| `DESC_COMPONENTE` | Descrição do componente |
| `TIPO_COMPONENTE` | PA, PI, MP etc. |
| `UNIDADE_COMPONENTE` | Unidade do componente |
| `GRUPO_COMPONENTE` | Grupo do componente |
| `QTD_POR` | Quantidade por montagem no pai imediato |
| `QTD_ACUMULADA` | Quantidade acumulada considerando níveis |
| `MP_EXCLUSIVA` | SIM/NAO somente para matérias-primas |
| `TOTAL_PAS_VALIDOS_ONDE_MP_APARECE` | Quantidade de PAs válidos onde a MP aparece |
| `CAMINHO` | Caminho hierárquico completo |

---

## 13. Regras de leitura do campo MP_EXCLUSIVA

| Valor | Significado |
|---|---|
| `SIM` | A MP aparece em apenas 1 PA válido |
| `NAO` | A MP aparece em mais de 1 PA válido |
| `NULL` ou vazio | O componente não é MP, geralmente é PI |

---

## 14. Observações importantes

### 14.1 Intermediários precisam ser abertos

Não basta olhar apenas os filhos diretos do PA.

Muitas MPs ficam dentro de produtos intermediários, como:

```text
90261255 > 50212155 > 10010032
```

Nesse exemplo, `10010032` é MP dentro do PI `50212155`, mas ainda pertence à estrutura do PA `90261255`.

---

### 14.2 Produtos 8000 e 8001 não devem contar

PAs iniciados por:

```text
8000
8001
```

devem ser ignorados na análise de exclusividade.

Motivo:

```text
São amostras ou testes e não representam produtos que serão produzidos normalmente.
```

---

### 14.3 Query de estrutura precisa bater com a rota

Para a query de estrutura bater com a rota oficial `/structure`, precisa conter:

```sql
G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
```

Sem esse filtro, aparecem componentes vencidos/históricos.

---

### 14.4 Exclusividade não é exclusividade por intermediário

A pergunta correta não é:

```text
A MP aparece só nesse PI?
```

A pergunta correta é:

```text
A MP aparece em quantos PAs válidos, considerando todos os níveis?
```

Se aparecer em apenas um PA válido, é exclusiva.

---

## 15. Modelo de resposta esperado ao executar a query final

Ao executar a query final para um produto, responder com:

```text
Consulta executada com sucesso para [CÓDIGO] — [DESCRIÇÃO].

Total retornado: [N] itens na estrutura vigente.
Matérias-primas exclusivas encontradas: [N].
Regra aplicada: PAs 8000% e 8001% foram desconsiderados.

Tabela 1 — Matérias-primas exclusivas
Tabela 2 — Estrutura completa com exclusividade

Fonte: API DELPI — /data/sql
Status da execução: sucesso
```

---

## 16. Checklist técnico antes de considerar a análise válida

- [ ] Usou `SG1010` para estrutura;
- [ ] Usou `SB1010` para descrição, tipo, unidade e grupo;
- [ ] Filtrou `D_E_L_E_T_ = ''`;
- [ ] Filtrou estrutura vigente por `G1_FIM`;
- [ ] Abriu intermediários recursivamente;
- [ ] Considerou MPs em todos os níveis;
- [ ] Considerou apenas PAs com `B1_TIPO = 'PA'`;
- [ ] Removeu PAs `8000%`;
- [ ] Removeu PAs `8001%`;
- [ ] Calculou quantos PAs válidos usam cada MP;
- [ ] Marcou exclusiva somente quando `COUNT(DISTINCT PA_RAIZ) = 1`;
- [ ] Usou `OPTION (MAXRECURSION 0)`.

---

## 17. Resumo da regra-mãe

```text
Matéria-prima exclusiva é aquela que, considerando a estrutura vigente e todos os intermediários, aparece em apenas um produto acabado válido, desconsiderando produtos de teste/amostra iniciados por 8000 ou 8001.
```

---

## 18. Catálogo global (roadmap)

Perguntas **sem código de PA** («quais MPs são exclusivas?», «quais produtos têm MP exclusiva?») exigem rota de **catálogo** — não coberta por `/structure/exclusivity` (que é por produto).

| Necessidade | Rota proposta | Status |
|-------------|---------------|--------|
| Listar MPs exclusivas + PA dono | `GET /products/exclusive-raw-materials/catalog?view=by_material` | Roadmap |
| Listar PAs com ≥1 MP exclusiva | `...?view=by_finished_product` | Roadmap |
| Estrutura de um PA com flags | `GET /products/{code}/structure/exclusivity` | ✅ Entregue |

**Não** adicionar flag `exclusive_raw_material` em `/products/{code}/structure` por default — consulta global de exclusividade é cara e quebra expectativa de consumidores da árvore BOM.

Playbook completo: [`playbook-catalogo-exclusividade-mp.md`](./playbook-catalogo-exclusividade-mp.md)  
Integração chat: [`playbook-15-anexo-catalogo-exclusividade-mp.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-anexo-catalogo-exclusividade-mp.md).