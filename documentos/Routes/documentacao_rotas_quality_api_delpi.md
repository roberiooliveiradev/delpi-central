# Documentação das Rotas de Qualidade — API DELPI

## Visão geral

O módulo `quality` da `api-delpi` concentra as rotas relacionadas ao domínio de qualidade, organizadas por contexto funcional.

Atualmente, o módulo contempla:

- não conformidades;
- kaizens;
- auditorias 5S;
- indicadores de PPM interno e externo.

A publicação das rotas é feita por um agregador do módulo `quality`, responsável por expor os submódulos em um único contexto HTTP.

---

## Base path do módulo

Todas as rotas deste módulo são publicadas sob o prefixo:

```text
/apps/api-delpi/quality
```

---

## Organização das rotas

Estrutura atual recomendada:

```text
app/interface/http/routes/quality/
  __init__.py
  quality_router.py
  nonconformity_routes.py
  kaizen_routes.py
  audit_5s_routes.py
  ppm_routes.py
```

---

## Padrão arquitetural

As rotas seguem o padrão adotado na `api-delpi`:

- Route;
- DTO;
- Use Case;
- Composer;
- Repository;
- Entity / Page.

Objetivos desse padrão:

- manter a camada HTTP fina;
- concentrar regra de negócio nos casos de uso;
- isolar acesso a dados nos repositórios;
- facilitar testes e evolução do frontend.

---

## Permissão

Todas as rotas do módulo `quality` devem usar a permissão:

```text
api-delpi.quality.access
```

---

## Padrão de resposta

### Sucesso

O retorno padrão de sucesso deve seguir o contrato central da API:

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {}
}
```

### Erro de validação

Quando houver erro de entrada, regra de negócio ou parâmetro inválido, o retorno deve usar `error_response(..., status_code=400)`.

Exemplo:

```json
{
  "success": false,
  "message": "Parâmetro inválido"
}
```

### Erro interno

Quando houver falha inesperada, a rota deve:

- registrar o erro com `log_error`;
- retornar `error_response(..., status_code=500)`.

Exemplo:

```json
{
  "success": false,
  "message": "Erro interno ao processar a solicitação."
}
```

---

## Router agregador do módulo

O arquivo `quality_router.py` é responsável por agregar os subrouters do módulo.

Padrão recomendado:

```python
from fastapi import APIRouter

from app.interface.http.routes.quality.nonconformity_routes import router as nonconformity_router
from app.interface.http.routes.quality.kaizen_routes import router as kaizen_router
from app.interface.http.routes.quality.audit_5s_routes import router as audit_5s_router
from app.interface.http.routes.quality.ppm_routes import router as ppm_router

router = APIRouter(prefix="/quality", tags=["Qualidade"])

router.include_router(nonconformity_router, prefix="/nonconformities")
router.include_router(kaizen_router, prefix="/kaizens")
router.include_router(audit_5s_router, prefix="/audit-5s")
router.include_router(ppm_router, prefix="/ppm")
```

No `main.py`, o correto é incluir o objeto `router` do agregador, e não o módulo Python.

Exemplo:

```python
from app.interface.http.routes.quality.quality_router import router as quality_router

app.include_router(quality_router)
```

---

# 1. Não Conformidades

## Objetivo

Disponibilizar listagem paginada de não conformidades internas e externas a partir da tabela `QI2010`.

A tabela `QI2010` representa a capa/cadastro principal da FNC, contendo tipo, datas, status, item, descrição, quantidade devolvida/rejeitada quando preenchida e vínculos de cliente/fornecedor quando aplicável.

---

## Endpoint

```http
GET /apps/api-delpi/quality/nonconformities/
```

---

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `type` | string | não | `internal`, `external` ou `all` |
| `branch` | string | não | Filial |
| `date_start` | string | não | Data inicial do filtro |
| `date_end` | string | não | Data final do filtro |
| `status` | string | não | Status da NC |
| `item_code` | string | não | Código do item/produto |
| `description` | string | não | Trecho da descrição |
| `page` | int | não | Página da listagem |
| `page_size` | int | não | Tamanho da página |

---

## Regras de tipo

O campo usado para classificar a FNC é `QI2_TIPO`.

| Valor | Significado | Tipo API |
|---|---|---|
| `1` | Interna | `internal` |
| `2` | Cliente | `external` |
| `3` | Fornecedor | `external` ou `supplier`, se futuramente separado |

Regras atuais:

- `internal` → `QI2_TIPO = '1'`;
- `external` → `QI2_TIPO IN ('2','3')`;
- `all` → todos os tipos.

---

## Campos principais da QI2010 usados nas rotas

| Campo | Descrição | Uso |
|---|---|---|
| `QI2_FILIAL` | Filial | Filtro e retorno |
| `QI2_FNC` | Código da FNC | Identificação da NC |
| `QI2_REV` | Revisão da FNC | Identificação da revisão |
| `QI2_TIPO` | Tipo da FNC | Interna, cliente ou fornecedor |
| `QI2_OP` | Ordem de Produção | Vínculo produtivo quando preenchido |
| `QI2_ITEM` | Item/produto | Produto ou item associado à NC |
| `QI2_DESCR` | Descrição resumida | Descrição exibida na listagem |
| `QI2_QTDDEV` | Quantidade devolvida/rejeitada | Numerador do PPM quando preenchido |
| `QI2_REGIST` | Data de registro | Exibição em `registered_date` na listagem de NC |
| `QI2_OCORRE` | Data da ocorrência | Data base do filtro de período em NC, PPM e série de NC |
| `QI2_STATUS` | Status da FNC | Situação da NC |
| `QI2_CODCLI` | Código do cliente | Usado para NC externa cliente |
| `QI2_LOJCLI` | Loja do cliente | Usado para NC externa cliente |
| `QI2_CODFOR` | Código do fornecedor | Usado para NC fornecedor |
| `QI2_LOJFOR` | Loja do fornecedor | Usado para NC fornecedor |
| `QI2_OPERAD` | Operador | Operador informado no registro, quando preenchido |
| `QI2_MATRES` | Usuário responsável | Responsável pela FNC |
| `QI2_FILRES` | Filial do usuário responsável | Filial do responsável |
| `D_E_L_E_T_` | Exclusão lógica | Considerar apenas registros ativos |

---

## Comportamento esperado

- rota paginada;
- sem `branch`, lista todas as filiais;
- com `branch`, lista apenas a filial informada;
- retorno no padrão `Page`;
- considerar apenas registros ativos com `D_E_L_E_T_ = ' '`;
- datas devem ser tratadas no padrão Protheus `YYYYMMDD` no banco e formatadas para apresentação quando necessário.

---

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/nonconformities/?type=all&branch=02&page=1&page_size=20
```

---

## Exemplo de resposta

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "items": [
      {
        "branch": "02",
        "code": "000000000412026",
        "revision": "00",
        "type_code": "1",
        "type_label": "internal",
        "status_code": "3",
        "status_label": "proceeds",
        "description": "ITEM TROCADO",
        "item_code": "90260999",
        "op_code": null,
        "registered_date": "24/03/2026",
        "occurrence_date": "24/03/2026",
        "priority_code": "3",
        "priority_label": "high",
        "origin_department": "0303",
        "destination_department": "20103",
        "customer_code": null,
        "customer_store": null,
        "supplier_code": null,
        "supplier_store": null,
        "produced_quantity": 700,
        "returned_quantity": 43
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

---

# 2. Kaizens

## Objetivo

Fornecer um resumo consolidado de kaizens para consumo em dashboards e cards do frontend.

---

## Endpoint

```http
GET /apps/api-delpi/quality/kaizens/summary
```

---

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `title` | string | não | Filtro textual do título |
| `status` | string | não | Filtro de status |
| `date_start` | string | não | Data inicial |
| `date_end` | string | não | Data final |

---

## Comportamento esperado

- rota de resumo;
- preparada para cards e gráficos;
- sem regra de negócio no frontend.

---

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/kaizens/summary?status=aberto
```

---

## Exemplo de resposta

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "total": 120,
    "open": 35,
    "in_progress": 20,
    "closed": 65
  }
}
```

---

# 3. Auditorias 5S

## Objetivo

Fornecer um resumo consolidado das auditorias 5S para painéis do frontend.

---

## Endpoint

```http
GET /apps/api-delpi/quality/audit-5s/summary
```

---

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `start_date` | string | não | Data inicial |
| `end_date` | string | não | Data final |

---

## Comportamento esperado

- rota de resumo;
- foco em indicadores e consolidação;
- ideal para cards e visão executiva.

---

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/audit-5s/summary?start_date=2026-01-01&end_date=2026-03-31
```

---

## Exemplo de resposta

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "total_audits": 58,
    "average_score": 87.4,
    "approved": 41,
    "reproved": 17
  }
}
```

---

# 4. PPM

## Objetivo

Disponibilizar indicadores de PPM interno e externo em dois formatos:

- `summary`: consolidado do período;
- `list`: composição detalhada do numerador.

Essa padronização foi adotada para facilitar a implantação do frontend com:

- cards e indicadores no topo;
- tabelas de auditoria e drilldown abaixo.

---

## Rotas disponíveis

### Summary

```http
GET /apps/api-delpi/quality/ppm/internal/summary
GET /apps/api-delpi/quality/ppm/external/summary
```

### List

```http
GET /apps/api-delpi/quality/ppm/internal
GET /apps/api-delpi/quality/ppm/external
```

---

## Query params comuns

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `branch` | string | não | Filial |
| `date_start` | string | não | Data inicial |
| `date_end` | string | não | Data final |

---

## Query params da list

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `page` | int | não | Página |
| `page_size` | int | não | Tamanho da página |

---

## Regra de tipo

### PPM interno

- usa FNC interna;
- tipo de rota: `internal`;
- filtro aplicado no banco: `QI2_TIPO = '1'`.

### PPM externo

- usa FNC externa agregada;
- tipo de rota: `external`;
- filtro aplicado no banco: `QI2_TIPO IN ('2','3')`.

Detalhamento dos tipos da `QI2010`:

| Valor `QI2_TIPO` | Significado | Uso atual no PPM |
|---|---|---|
| `1` | Interna | PPM interno |
| `2` | Cliente | PPM externo |
| `3` | Fornecedor | PPM externo agregado |

---

## Regra oficial do cálculo

### Fórmula geral

```text
PPM = (total_devolvido_un / total_produzido_un) * 1.000.000
```

Onde:

```text
total_produzido_un = total_produzido_milheiro_ajustado * 1000
```

---

## Numerador

O numerador vem da `QI2010`.

Campos usados:

| Campo | Uso |
|---|---|
| `QI2_QTDDEV` | Quantidade devolvida/rejeitada em unidade |
| `QI2_OCORRE` | Data base do filtro do numerador |
| `QI2_TIPO` | Classificação interna, cliente ou fornecedor |
| `QI2_FILIAL` | Filial da FNC |
| `D_E_L_E_T_` | Exclusão lógica |

Regras:

- considerar apenas registros ativos: `D_E_L_E_T_ = ' '`;
- filtrar por `QI2_FILIAL` quando `branch` for informado;
- filtrar o período por `QI2_OCORRE`;
- `internal` usa `QI2_TIPO = '1'`;
- `external` usa `QI2_TIPO IN ('2','3')`;
- `QI2_QTDDEV` está em unidade.

---

## Tratamento de quantidade devolvida

`QI2_QTDDEV` pode vir como texto, vazio ou em formatos diferentes.

A conversão defensiva deve considerar:

- trim de espaços;
- string vazia como nula;
- tentativa de parse `pt-BR`;
- fallback `en-US`;
- fallback final para `0`.

Expressão SQL usada:

```sql
COALESCE(
    TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
    TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
    0
)
```

---

## Denominador

O denominador vem da produção ajustada da `SH6010`.

A produção não deve ser calculada por soma direta de `H6_QTDPROD`, pois a `SH6010` pode conter múltiplos apontamentos para a mesma OP/produto/operação, principalmente em ambientes que apontam produção por operação.

A soma direta de `H6_QTDPROD` pode inflar o denominador quando a mesma quantidade aparece repetida em operações intermediárias.

---

## Regra atual do denominador ajustado

A regra aplicada atualmente é:

- tabela base: `SH6010`;
- campo de quantidade: `H6_QTDPROD`;
- data base: `H6_DTAPONT`;
- considerar apenas registros ativos: `SH6.D_E_L_E_T_ = ' '`;
- considerar apenas apontamentos produtivos: `SH6.H6_TIPO = 'P'`;
- excluir OP vazia: `SH6.H6_OP <> ''`;
- excluir produto vazio: `SH6.H6_PRODUTO <> ''`;
- cruzar com `SG2010` para considerar somente a operação final do roteiro;
- cruzar com `SB1010` para considerar somente produto acabado: `SB1.B1_TIPO = 'PA'`;
- cruzar com `SC2010` para obter a quantidade **programada** da OP (`C2_QUANT`);
- deduplicar apontamentos por `H6_FILIAL + H6_OP + H6_PRODUTO + H6_OPERAC`;
- usar `MAX(H6_QTDPROD)` como **apontado** por OP/operação final;
- calcular quantidade produzida por OP com a regra **programado − saldo = apontado** (ver abaixo);
- excluir os grupos `B1_GRUPO IN ('9043', '9028')` *(documentado; conferir implementação)*;
- converter `H6_QTDPROD` de milheiro para unidade multiplicando por `1000`.

---

## Quantidade produzida por OP — programado − saldo = apontado

Para cada OP na operação final do roteiro:

| Termo | Campo | Significado |
|---|---|---|
| **Programado** | `SC2010.C2_QUANT` | Quantidade planejada da ordem de produção |
| **Apontado** | `MAX(SH6010.H6_QTDPROD)` | Maior quantidade apontada na operação final (deduplica repasses) |
| **Saldo pendente** | `max(0, programado − apontado)` | O que ainda falta produzir na OP |
| **Produzido** | `programado − saldo` | Quantidade efetiva que entra no denominador |

Em texto:

```text
saldo_pendente = max(0, programado − apontado)
qtd_produzida_op = programado − saldo_pendente
```

Propriedades:

- Quando `apontado ≤ programado`, resulta em **`apontado`** (equivale a usar o MAX do apontamento).
- Quando `apontado > programado`, **limita ao programado** (não infla acima do planejado da OP).
- Quando `programado` ausente ou zero, usa **`apontado`** (fallback para OPs sem `C2_QUANT`).

Implementação de referência: `app/domain/services/ppm_produced_quantity.py` e `ppm_production_sql.py`.

Cruzamento OP:

```sql
SC2.C2_OP = SH6.H6_OP
OR SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN = SH6.H6_OP
```

---

## Tabelas usadas no denominador

| Tabela | Uso |
|---|---|
| `SH6010` | Apontamentos de produção |
| `SG2010` | Roteiro de operações; usada para identificar operação final por produto |
| `SC2010` | Ordens de produção; quantidade programada (`C2_QUANT`) |
| `SB1010` | Cadastro de produtos; usada para filtrar produto acabado e grupo |

---

## Identificação da operação final

A operação final do roteiro é identificada por produto usando:

```sql
MAX(G2.G2_OPERAC) AS operacao_final_roteiro
```

A CTE de roteiro considera validade do roteiro:

```sql
AND (G2.G2_DTINI = '' OR G2.G2_DTINI < :date_end)
AND (G2.G2_DTFIM = '' OR G2.G2_DTFIM >= :date_start)
```

Quando `branch` é informado, também é aplicado:

```sql
AND G2.G2_FILIAL = :branch
```

---

## Produção ajustada

A produção ajustada é obtida em duas etapas.

Primeiro, identifica-se a operação final por produto no roteiro:

```sql
WITH roteiro_final AS (
    SELECT
        G2.G2_FILIAL,
        G2.G2_PRODUTO,
        MAX(G2.G2_OPERAC) AS operacao_final_roteiro
    FROM SG2010 G2
    WHERE
        G2.D_E_L_E_T_ = ' '
        AND (G2.G2_DTINI = '' OR G2.G2_DTINI < :date_end)
        AND (G2.G2_DTFIM = '' OR G2.G2_DTFIM >= :date_start)
    GROUP BY
        G2.G2_FILIAL,
        G2.G2_PRODUTO
)
```

Depois, cruza-se a `SH6010` com a operação final, filtra-se PA, une-se `SC2010` e calcula-se a quantidade produzida:

```sql
apont_final AS (
    SELECT
        SH6.H6_FILIAL,
        SH6.H6_OP,
        SH6.H6_PRODUTO,
        SH6.H6_OPERAC,
        SB1.B1_GRUPO,
        CASE
            WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) <= 0 THEN MAX(ISNULL(SH6.H6_QTDPROD, 0))
            ELSE MAX(ISNULL(SC2.C2_QUANT, 0)) - CASE
                WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) > MAX(ISNULL(SH6.H6_QTDPROD, 0))
                THEN MAX(ISNULL(SC2.C2_QUANT, 0)) - MAX(ISNULL(SH6.H6_QTDPROD, 0))
                ELSE 0
            END
        END AS qtd_produzida_op
    FROM SH6010 SH6
    INNER JOIN roteiro_final RF
        ON RF.G2_FILIAL = SH6.H6_FILIAL
       AND RF.G2_PRODUTO = SH6.H6_PRODUTO
       AND RF.operacao_final_roteiro = SH6.H6_OPERAC
    INNER JOIN SB1010 SB1
        ON SB1.B1_COD = SH6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ' '
       AND SB1.B1_TIPO = 'PA'
    LEFT JOIN SC2010 SC2
        ON SC2.D_E_L_E_T_ = ' '
       AND SC2.C2_FILIAL = SH6.H6_FILIAL
       AND SC2.C2_PRODUTO = SH6.H6_PRODUTO
       AND (
            SC2.C2_OP = SH6.H6_OP
            OR SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN = SH6.H6_OP
       )
    WHERE
        SH6.D_E_L_E_T_ = ' '
        AND SH6.H6_TIPO = 'P'
        AND SH6.H6_OP <> ''
        AND SH6.H6_PRODUTO <> ''
        AND SH6.H6_DTAPONT >= :date_start
        AND SH6.H6_DTAPONT < :date_end
    GROUP BY
        SH6.H6_FILIAL,
        SH6.H6_OP,
        SH6.H6_PRODUTO,
        SH6.H6_OPERAC,
        SB1.B1_GRUPO
)
```

Por fim, calcula-se a produção do PPM excluindo os grupos fora do escopo atual:

```sql
prod AS (
    SELECT
        SUM(qtd_produzida_op) AS total_produzido_milheiro
    FROM apont_final
    WHERE
        B1_GRUPO NOT IN ('9043', '9028')
)
```

---

## Conversão de unidade

Aprendizado consolidado do indicador:

- `QI2_QTDDEV` está em unidade;
- `H6_QTDPROD` está em milheiro.

Portanto:

```text
total_produzido_un = total_produzido_milheiro_ajustado * 1000
PPM = (total_devolvido_un / total_produzido_un) * 1.000.000
```

---

## SQL conceitual do summary de PPM

O SQL abaixo representa a lógica de cálculo do summary.

```sql
WITH nc AS (
    SELECT
        SUM(
            COALESCE(
                TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'pt-BR'),
                TRY_PARSE(NULLIF(LTRIM(RTRIM(QI2_QTDDEV)), '') AS DECIMAL(18,3) USING 'en-US'),
                0
            )
        ) AS total_devolvido_un
    FROM QI2010
    WHERE
        D_E_L_E_T_ = ' '
        AND QI2_OCORRE >= :date_start
        AND QI2_OCORRE < :date_end
        -- AND QI2_FILIAL = :branch, quando informado
        -- AND QI2_TIPO = '1', para internal
        -- AND QI2_TIPO IN ('2','3'), para external
),
roteiro_final AS (
    SELECT
        G2.G2_FILIAL,
        G2.G2_PRODUTO,
        MAX(G2.G2_OPERAC) AS operacao_final_roteiro
    FROM SG2010 G2
    WHERE
        G2.D_E_L_E_T_ = ' '
        -- AND G2.G2_FILIAL = :branch, quando informado
        AND (G2.G2_DTINI = '' OR G2.G2_DTINI < :date_end)
        AND (G2.G2_DTFIM = '' OR G2.G2_DTFIM >= :date_start)
    GROUP BY
        G2.G2_FILIAL,
        G2.G2_PRODUTO
),
apont_final AS (
    SELECT
        SH6.H6_FILIAL,
        SH6.H6_OP,
        SH6.H6_PRODUTO,
        SH6.H6_OPERAC,
        SB1.B1_GRUPO,
        CASE
            WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) <= 0 THEN MAX(ISNULL(SH6.H6_QTDPROD, 0))
            ELSE MAX(ISNULL(SC2.C2_QUANT, 0)) - CASE
                WHEN MAX(ISNULL(SC2.C2_QUANT, 0)) > MAX(ISNULL(SH6.H6_QTDPROD, 0))
                THEN MAX(ISNULL(SC2.C2_QUANT, 0)) - MAX(ISNULL(SH6.H6_QTDPROD, 0))
                ELSE 0
            END
        END AS qtd_produzida_op
    FROM SH6010 SH6
    INNER JOIN roteiro_final RF
        ON RF.G2_FILIAL = SH6.H6_FILIAL
       AND RF.G2_PRODUTO = SH6.H6_PRODUTO
       AND RF.operacao_final_roteiro = SH6.H6_OPERAC
    INNER JOIN SB1010 SB1
        ON SB1.B1_COD = SH6.H6_PRODUTO
       AND SB1.D_E_L_E_T_ = ' '
       AND SB1.B1_TIPO = 'PA'
    LEFT JOIN SC2010 SC2
        ON SC2.D_E_L_E_T_ = ' '
       AND SC2.C2_FILIAL = SH6.H6_FILIAL
       AND SC2.C2_PRODUTO = SH6.H6_PRODUTO
       AND (
            SC2.C2_OP = SH6.H6_OP
            OR SC2.C2_NUM + SC2.C2_ITEM + SC2.C2_SEQUEN = SH6.H6_OP
       )
    WHERE
        SH6.D_E_L_E_T_ = ' '
        -- AND SH6.H6_FILIAL = :branch, quando informado
        AND SH6.H6_TIPO = 'P'
        AND SH6.H6_OP <> ''
        AND SH6.H6_PRODUTO <> ''
        AND SH6.H6_DTAPONT >= :date_start
        AND SH6.H6_DTAPONT < :date_end
    GROUP BY
        SH6.H6_FILIAL,
        SH6.H6_OP,
        SH6.H6_PRODUTO,
        SH6.H6_OPERAC,
        SB1.B1_GRUPO
),
prod AS (
    SELECT
        SUM(qtd_produzida_op) AS total_produzido_milheiro
    FROM apont_final
    WHERE
        B1_GRUPO NOT IN ('9043', '9028')
)
SELECT
    ISNULL(nc.total_devolvido_un, 0) AS total_devolvido_un,
    ISNULL(prod.total_produzido_milheiro, 0) AS total_produzido_milheiro,
    ISNULL(prod.total_produzido_milheiro, 0) * 1000 AS total_produzido_un,
    CASE
        WHEN ISNULL(prod.total_produzido_milheiro, 0) = 0 THEN 0
        ELSE (ISNULL(nc.total_devolvido_un, 0) / (prod.total_produzido_milheiro * 1000.0)) * 1000000.0
    END AS ppm
FROM nc
CROSS JOIN prod;
```

---

## Comportamento de branch

### Summary

- com `branch` informado: retorna o consolidado da filial;
- sem `branch`: retorna o consolidado geral de todas as filiais.

Quando `branch` for informado, ele deve ser aplicado tanto no numerador quanto no denominador:

- `QI2010.QI2_FILIAL`;
- `SG2010.G2_FILIAL`;
- `SH6010.H6_FILIAL`.

### List

- com `branch` informado: lista apenas a filial;
- sem `branch`: lista todas as filiais.

---

## Summary interno

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/internal/summary
```

### Exemplo

```http
GET /apps/api-delpi/quality/ppm/internal/summary?branch=01&date_start=2026-04-01&date_end=2026-05-01
```

### Resposta

Exemplo real validado para abril/2026, filial 01:

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "type": "internal",
    "branch": "01",
    "date_start": "2026-04-01",
    "date_end": "2026-05-01",
    "total_devolvido_un": 1754.0,
    "total_produzido_milheiro": 130.995,
    "total_produzido_un": 130995.0,
    "ppm": 13389.824039085508
  }
}
```

---

## Summary externo

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/external/summary
```

### Resposta esperada

Mesmo contrato do summary interno, alterando apenas `type` para `external`.

Exemplo conceitual:

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "type": "external",
    "branch": "01",
    "date_start": "2026-04-01",
    "date_end": "2026-05-01",
    "total_devolvido_un": 0.0,
    "total_produzido_milheiro": 130.995,
    "total_produzido_un": 130995.0,
    "ppm": 0.0
  }
}
```

---

## List interno

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/internal
```

### Objetivo

Listar as NCs que compõem o numerador do indicador de PPM interno.

### Exemplo

```http
GET /apps/api-delpi/quality/ppm/internal?branch=02&page=1&page_size=20
```

### Resposta

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "items": [
      {
        "branch": "02",
        "registered_date": "24/03/2026",
        "code": "000000000432026",
        "revision": "00",
        "ppm_type": "1",
        "ppm_type_description": "interno",
        "item_code": "90264143",
        "description": "ITEM TROCADO",
        "returned_quantity_original": "2000",
        "returned_quantity_un": 2000.0
      }
    ],
    "total": 32,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  }
}
```

---

## List externo

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/external
```

### Objetivo

Listar as NCs que compõem o numerador do indicador de PPM externo.

### Resposta esperada

Mesmo contrato da list interna, alterando apenas o conjunto de dados filtrado como externo.

---

## Observações técnicas importantes do PPM

### 1. Serialização

As rotas de `summary` e `list` não devem expor `Decimal` cru no JSON.

Toda quantidade retornada ao frontend deve estar serializada como `float` ou valor JSON compatível.

Campos calculados como `total_devolvido_un`, `total_produzido_milheiro`, `total_produzido_un` e `ppm` devem ser convertidos para tipos JSON serializáveis antes da resposta.

---

### 2. Summary sem branch

O `summary` deve retornar uma única linha consolidada quando `branch` não for informada.

Não deve agrupar por filial no SQL quando a intenção do endpoint for total geral.

---

### 3. List sem branch

A `list` sem `branch` deve trazer todas as filiais.

Ordenação recomendada:

- filial;
- data de registro desc;
- código da NC desc.

---

### 4. Cadastro das FNCs

O PPM depende diretamente dos registros existentes na `QI2010`.

Se as FNCs internas ou externas ainda não estiverem cadastradas, ou se `QI2_QTDDEV` estiver vazio, o numerador retornará zero ou valor diferente de planilhas manuais.

A API calcula apenas com base no que estiver registrado no Protheus.

Exemplo observado:

- março/2026, filial 01: a `QI2010` possuía poucos registros cadastrados, com interno igual a zero e externo igual a 10;
- abril/2026, filial 01: a `QI2010` possuía registros internos cadastrados totalizando 1.754 unidades.

---

### 5. Campo de data do numerador

O numerador usa `QI2_OCORRE`, ou seja, a data de ocorrência da FNC.

A `QI2010` também possui `QI2_REGIST`, data de registro. Essa data pode ser diferente da data de ocorrência e continua exposta em `registered_date` na listagem de NC.

Para o PPM atual, a regra adotada é:

```text
Data base do numerador = QI2_OCORRE
```

---

### 6. Campo de data do denominador

O denominador usa `H6_DTAPONT`, ou seja, a data do apontamento de produção.

Não usar `H6_DATAINI` para o PPM ajustado.

Regra adotada:

```text
Data base do denominador = H6_DTAPONT
```

---

### 7. Grupos excluídos do denominador

Atualmente, o denominador do PPM exclui os grupos:

```text
9043
9028
```

Essa regra foi adotada para aproximar o denominador ao escopo funcional do indicador validado.

Qualquer alteração nessa regra deve ser tratada como regra de negócio do PPM e refletida na documentação, no repositório e nos testes.

---

### 8. Operação final do roteiro

A operação final é identificada por `MAX(G2_OPERAC)` na `SG2010`.

Essa regra deve ser mantida enquanto não existir outro campo oficial de operação final, operação de reporte ou operação produtiva final.

Caso o especialista TOTVS/Protheus valide outro critério, a documentação e o repositório devem ser atualizados.

---

# 5. Padrões recomendados para o frontend

## Consumo de summary

Usar para:

- cards;
- indicadores;
- cabeçalhos analíticos;
- blocos de KPI.

---

## Consumo de list

Usar para:

- tabelas detalhadas;
- drilldown;
- auditoria do numerador;
- paginação.

---

## Benefícios da dupla summary + list

- contrato consistente entre contextos;
- facilidade de implantação do frontend;
- clareza entre visão executiva e visão analítica;
- menor necessidade de regras locais na UI.

---

# 6. Regras de implementação das rotas do módulo quality

## Todas as rotas devem

- usar `@require_permission("api-delpi.quality.access")`;
- registrar erro com `log_error`;
- retornar `success_response(...)` em sucesso;
- retornar `error_response(...)` em falha;
- manter a camada HTTP fina;
- delegar a regra aos use cases.

---

## Nenhuma rota deve

- conter SQL direto;
- conter regra de negócio complexa;
- serializar entidades sensíveis manualmente no controller quando isso puder ser resolvido pela entidade ou pelo repositório;
- misturar contratos diferentes de resposta no mesmo módulo.

---

# 7. Tabelas necessárias para o PPM

Para o PPM atual, as tabelas necessárias são:

| Tabela | Uso |
|---|---|
| `QI2010` | Numerador do PPM: FNCs internas, cliente e fornecedor |
| `SH6010` | Apontamentos de produção usados no denominador |
| `SG2010` | Roteiro de operações para identificar operação final |
| `SB1010` | Cadastro de produtos para filtrar PA e grupo |

---

# 8. Objeto de liberação SQL recomendado

Objeto de whitelist recomendado para a API SQL, considerando o módulo quality e os demais módulos já autorizados:

```json
{
  "allowed_tables": [
    "SB1010",
    "SG1010",
    "SG2010",
    "SH1010",

    "QP6010",
    "QP7010",
    "QP8010",

    "SC1010",
    "SC2010",
    "SC7010",
    "SF1010",
    "SH8010",
    "SH6010",

    "SH4010",

    "SD4010",
    "SD3010",
    "SB2010",
    "SBC010",

    "SD1010",

    "SA1010",
    "SA2010",
    "SA5010",

    "SC5010",
    "SC6010",

    "QI2010",

    "SX2010",
    "SX3010",
    "SIX010",
    "SX9010"
  ],
  "_notes": {
    "SB1010": "Cadastro de Produtos — usado para descrição, unidade, tipo, grupo e dados cadastrais dos produtos.",
    "SG1010": "Estrutura de Produtos / BOM — usada para consultar componentes, produto pai e composição do produto.",
    "SG2010": "Roteiro de Operações — usada para operações, recursos, centros de trabalho e identificação da operação final.",
    "SH1010": "Cadastro de Recursos — usada para consultar dados de recursos produtivos/máquinas.",

    "QP6010": "Inspeções / Plano de Controle — usada em validações de inspeção e qualidade do produto.",
    "QP7010": "Características de Inspeção — usada para critérios, características e requisitos de inspeção.",
    "QP8010": "Resultados/Itens de Inspeção — usada para detalhes vinculados aos planos e inspeções.",

    "SC1010": "Solicitações de Compra — usada para consultas de suprimentos e requisições de compra.",
    "SC2010": "Ordens de Produção — usada para OPs, produto da OP, quantidade prevista, datas e status.",
    "SC7010": "Pedidos de Compra — usada para análise de pedidos de compra e suprimentos.",
    "SF1010": "Cabeçalho de Nota Fiscal — usada apenas quando necessário cruzar documentos fiscais autorizados.",
    "SH8010": "Apontamentos / Produção — usada em cenários de produção, apontamento e histórico produtivo.",
    "SH6010": "Movimentação da Produção — tabela principal para apontamentos de produção e cálculo de produção realizada.",

    "SH4010": "Calendário / Turnos / Recursos Produtivos — usada em análises de capacidade, agenda ou programação produtiva.",

    "SD4010": "Empenhos / Requisições da OP — usada para componentes empenhados, consumo previsto e saldo de empenho.",
    "SD3010": "Movimentações Internas — usada para consumo, movimentação de estoque, apontamentos e validações de produção.",
    "SB2010": "Saldos em Estoque — usada para consulta de estoque por filial, local e produto.",
    "SBC010": "Perda por OP — usada para refugo, scrap, perdas por OP e análises internas de qualidade.",

    "SD1010": "⚠️ Itens de Notas Fiscais de Entrada — contém dados fiscais; usada para compras, entradas e histórico de aquisição.",

    "SA1010": "⚠️ Cadastro de Clientes — liberado por exceção DELPI, acesso controlado.",
    "SA2010": "⚠️ Cadastro de Fornecedores — liberado por exceção DELPI, acesso controlado.",
    "SA5010": "Amarração Produto x Fornecedor — usada para vínculo de fornecedores, partnumber e dados comerciais de suprimentos.",

    "SC5010": "Pedidos de Venda — usada para análises comerciais ou vínculos de demanda quando autorizado.",
    "SC6010": "Itens de Pedido de Venda — usada para itens vendidos, produtos, quantidades e vínculos comerciais quando autorizado.",

    "QI2010": "Não Conformidades — necessária para cálculo do PPM interno/externo e análise de FNCs.",

    "SX2010": "Dicionário de Tabelas Protheus — usada para localizar e descrever tabelas do sistema.",
    "SX3010": "Dicionário de Campos Protheus — usada para consultar colunas, tipos, tamanhos e descrições.",
    "SIX010": "Dicionário de Índices Protheus — usada para consultar chaves e índices das tabelas.",
    "SX9010": "Dicionário de Relacionamentos Protheus — usada para consultar relações entre tabelas.",

    "SD2010": "⚠️ Itens de Notas Fiscais de Saída — contém dados fiscais. Não está liberada em allowed_tables neste objeto.",
    "_policy": "Essas tabelas são liberadas apenas sob auditoria e controle interno de segurança. Consultas devem respeitar D_E_L_E_T_ = ' ' e evitar dados sensíveis quando não necessários."
  }
}
```

---

# 9. Resumo executivo

O módulo `quality` da `api-delpi` foi estruturado para concentrar rotas do domínio de qualidade em um contexto único, com submódulos organizados por responsabilidade:

- `nonconformities`;
- `kaizens`;
- `audit-5s`;
- `ppm`.

O módulo já está preparado para consumo por frontend usando dois padrões principais:

- `summary` para indicadores e cards;
- `list` para tabelas e navegação paginada.

No caso específico do PPM, as regras consolidadas atuais são:

- numerador em `QI2010.QI2_QTDDEV`;
- data do numerador em `QI2_OCORRE`;
- tipos definidos por `QI2_TIPO`;
- denominador calculado por produção ajustada, não soma direta;
- base do denominador em `SH6010.H6_QTDPROD`;
- data do denominador em `H6_DTAPONT`;
- operação final obtida via `SG2010.MAX(G2_OPERAC)`;
- somente produtos acabados `SB1010.B1_TIPO = 'PA'`;
- deduplicação por `H6_FILIAL + H6_OP + H6_PRODUTO + H6_OPERAC`;
- exclusão dos grupos `9043` e `9028`;
- `H6_QTDPROD` convertido de milheiro para unidade;
- `summary` sem filial = total geral;
- `list` sem filial = todas as filiais.

Essa padronização reduz complexidade no frontend, melhora a auditabilidade dos indicadores e prepara o módulo para evolução futura com dashboards, séries temporais, ranking por produto e detalhamento analítico.

