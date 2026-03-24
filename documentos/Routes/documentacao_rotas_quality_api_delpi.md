# Documentação das Rotas de Qualidade — API DELPI

## Visão geral

O módulo `quality` da `api-delpi` concentra as rotas relacionadas ao domínio de qualidade, organizadas por contexto funcional.

Atualmente, o módulo contempla:

- não conformidades
- kaizens
- auditorias 5S
- indicadores de PPM interno e externo

A publicação das rotas é feita por um agregador do módulo `quality`, responsável por expor os submódulos em um único contexto HTTP.

## Base path do módulo

Todas as rotas deste módulo são publicadas sob o prefixo:

```text
/apps/api-delpi/quality
```

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

## Padrão arquitetural

As rotas seguem o padrão adotado na `api-delpi`:

- Route
- DTO
- Use Case
- Composer
- Repository
- Entity / Page

Objetivos desse padrão:

- manter a camada HTTP fina
- concentrar regra de negócio nos casos de uso
- isolar acesso a dados nos repositórios
- facilitar testes e evolução do frontend

## Permissão

Todas as rotas do módulo `quality` devem usar a permissão:

```text
api-delpi.quality.access
```

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

- registrar o erro com `log_error`
- retornar `error_response(..., status_code=500)`

Exemplo:

```json
{
  "success": false,
  "message": "Erro interno ao processar a solicitação."
}
```

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

## Endpoint

```http
GET /apps/api-delpi/quality/nonconformities/
```

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `type` | string | não | `internal`, `external` ou `all` |
| `branch` | string | não | filial |
| `date_start` | string | não | data inicial do filtro |
| `date_end` | string | não | data final do filtro |
| `status` | string | não | status da NC |
| `item_code` | string | não | código do item/produto |
| `description` | string | não | trecho da descrição |
| `page` | int | não | página da listagem |
| `page_size` | int | não | tamanho da página |

## Regras de tipo

- `internal` → NCs internas
- `external` → NCs externas agregadas
- `all` → todos os tipos

## Comportamento esperado

- rota paginada
- sem `branch`, lista todas as filiais
- com `branch`, lista apenas a filial informada
- retorno no padrão `Page`

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/nonconformities/?type=all&branch=02&page=1&page_size=20
```

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

## Endpoint

```http
GET /apps/api-delpi/quality/kaizens/summary
```

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `title` | string | não | filtro textual do título |
| `status` | string | não | filtro de status |
| `date_start` | string | não | data inicial |
| `date_end` | string | não | data final |

## Comportamento esperado

- rota de resumo
- preparada para cards e gráficos
- sem regra de negócio no frontend

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/kaizens/summary?status=aberto
```

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

## Endpoint

```http
GET /apps/api-delpi/quality/audit-5s/summary
```

## Query params

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `start_date` | string | não | data inicial |
| `end_date` | string | não | data final |

## Comportamento esperado

- rota de resumo
- foco em indicadores e consolidação
- ideal para cards e visão executiva

## Exemplo de requisição

```http
GET /apps/api-delpi/quality/audit-5s/summary?start_date=2026-01-01&end_date=2026-03-31
```

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

- `summary`: consolidado do período
- `list`: composição detalhada do numerador

Essa padronização foi adotada para facilitar a implantação do frontend com:

- cards e indicadores no topo
- tabelas de auditoria e drilldown abaixo

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

## Query params comuns

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `branch` | string | não | filial |
| `date_start` | string | não | data inicial |
| `date_end` | string | não | data final |

## Query params da list

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `page` | int | não | página |
| `page_size` | int | não | tamanho da página |

## Regra de tipo

### PPM interno

- usa NC interna
- tipo: `internal`

### PPM externo

- usa NC externa
- tipo: `external`

## Regra oficial do cálculo

### Numerador

O numerador vem da `QI2010`:

- campo: `QI2_QTDDEV`
- data base: `QI2_REGIST`

### Denominador

O denominador vem da `SH6010`:

- campo: `H6_QTDPROD`
- data base: `H6_DATAINI`

## Conversão de unidade

Aprendizado consolidado do indicador:

- `QI2_QTDDEV` está em unidade
- `H6_QTDPROD` está em milheiro

Por isso, a normalização correta é:

```text
PPM = (soma QI2_QTDDEV / (soma H6_QTDPROD * 1000)) * 1.000.000
```

Forma equivalente usada na prática:

```text
PPM = (soma QI2_QTDDEV / soma H6_QTDPROD) * 1000
```

## Comportamento de branch

### Summary

- com `branch` informado: retorna o consolidado da filial
- sem `branch`: retorna o consolidado geral de todas as filiais

### List

- com `branch` informado: lista apenas a filial
- sem `branch`: lista todas as filiais

## Tratamento de quantidade devolvida

`QI2_QTDDEV` pode vir como texto, vazio ou em formatos diferentes.

A conversão defensiva deve considerar:

- trim de espaços
- string vazia como nula
- tentativa de parse `pt-BR`
- fallback `en-US`
- fallback final para `0`

## Summary interno

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/internal/summary
```

### Exemplo

```http
GET /apps/api-delpi/quality/ppm/internal/summary?branch=02&date_start=2026-01-01&date_end=2026-03-24
```

### Resposta

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": {
    "type": "internal",
    "branch": "02",
    "date_start": "2026-01-01",
    "date_end": "2026-03-24",
    "total_devolvido_un": 12097.136,
    "total_produzido_milheiro": 261170.108,
    "total_produzido_un": 261170108,
    "ppm": 46.3189914521147
  }
}
```

## Summary externo

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/external/summary
```

### Resposta esperada

Mesmo contrato do summary interno, alterando apenas `type` para `external`.

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

## List externo

### Endpoint

```http
GET /apps/api-delpi/quality/ppm/external
```

### Objetivo

Listar as NCs que compõem o numerador do indicador de PPM externo.

### Resposta esperada

Mesmo contrato da list interna, alterando apenas o conjunto de dados filtrado como externo.

## Observações técnicas importantes do PPM

### 1. Serialização

As rotas de `list` não devem expor `Decimal` cru no JSON.

Toda quantidade retornada ao frontend deve estar serializada como `float` ou valor JSON compatível.

### 2. Summary sem branch

O `summary` deve retornar uma única linha consolidada quando `branch` não for informada.

Não deve agrupar por filial no SQL quando a intenção do endpoint for total geral.

### 3. List sem branch

A `list` sem `branch` deve trazer todas as filiais.

Ordenação recomendada:

- filial
- data de registro desc
- código da NC desc

---

# 5. Padrões recomendados para o frontend

## Consumo de summary

Usar para:

- cards
- indicadores
- cabeçalhos analíticos
- blocos de KPI

## Consumo de list

Usar para:

- tabelas detalhadas
- drilldown
- auditoria do numerador
- paginação

## Benefícios da dupla summary + list

- contrato consistente entre contextos
- facilidade de implantação do frontend
- clareza entre visão executiva e visão analítica
- menor necessidade de regras locais na UI

---

# 6. Regras de implementação das rotas do módulo quality

## Todas as rotas devem

- usar `@require_permission("api-delpi.quality.access")`
- registrar erro com `log_error`
- retornar `success_response(...)` em sucesso
- retornar `error_response(...)` em falha
- manter a camada HTTP fina
- delegar a regra aos use cases

## Nenhuma rota deve

- conter SQL direto
- conter regra de negócio complexa
- serializar entidades sensíveis manualmente no controller quando isso puder ser resolvido pela entidade ou pelo repositório
- misturar contratos diferentes de resposta no mesmo módulo

---

# 7. Resumo executivo

O módulo `quality` da `api-delpi` foi estruturado para concentrar rotas do domínio de qualidade em um contexto único, com submódulos organizados por responsabilidade:

- `nonconformities`
- `kaizens`
- `audit-5s`
- `ppm`

O módulo já está preparado para consumo por frontend usando dois padrões principais:

- `summary` para indicadores e cards
- `list` para tabelas e navegação paginada

No caso específico do PPM, as regras consolidadas são:

- numerador em `QI2010.QI2_QTDDEV`
- data do numerador em `QI2_REGIST`
- denominador em `SH6010.H6_QTDPROD`
- data do denominador em `H6_DATAINI`
- `H6_QTDPROD` convertido de milheiro para unidade
- `summary` sem filial = total geral
- `list` sem filial = todas as filiais

Essa padronização reduz complexidade no frontend, melhora a auditabilidade dos indicadores e prepara o módulo para evolução futura com dashboards, séries temporais, ranking por produto e detalhamento analítico.

