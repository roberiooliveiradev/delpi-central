# Documentação Oficial — Rota de Produção

## 1. Visão geral

A rota de **Produção** da API DELPI expõe indicadores operacionais e financeiros consolidados para acompanhamento de desempenho fabril por filial e faixa de datas.

O conjunto atual de endpoints cobre cinco indicadores principais:

- **Direct Labor Cost %** — percentual de custo de mão de obra direta sobre a ROL
- **Production Cost %** — percentual de custo de produção sobre a ROL
- **Depreciation %** — percentual de depreciação sobre a ROL
- **Overall Equipment Effectiveness % (OEE)** — eficiência geral dos equipamentos
- **On-Time Delivery % (OTD)** — percentual de ordens de produção entregues no prazo

Todos os endpoints estão agrupados sob o prefixo:

```http
/apps/api-delpi/production
```

No router da aplicação, a definição atual é:

```python
router = APIRouter(prefix="/production", tags=["Produção"])
```

---

## 2. Objetivo funcional da rota

Esta rota existe para fornecer uma camada padronizada de consulta de indicadores de produção, com foco em:

- acompanhamento gerencial
- consumo por dashboards
- comparação por período
- consolidação por filial
- exposição consistente via API

A rota foi desenhada para seguir o padrão arquitetural da API DELPI em **Clean Architecture**, com separação entre:

- **rota HTTP**
- **DTO de entrada**
- **use case**
- **repository / port**
- **infraestrutura de dados**

---

## 3. Parâmetros padrão de entrada

Todos os endpoints de produção utilizam o mesmo DTO base de filtro:

```python
@dataclass
class ProductionRequest:
    branch: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
```

### Parâmetros HTTP aceitos

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---:|---|
| `branch` | string | não | Filial a ser considerada na consulta |
| `start_date` | string | não | Data inicial do período |
| `end_date` | string | não | Data final do período |

### Observações

- O formato de data aceito depende da infraestrutura de parsing utilizada internamente.
- Nos endpoints que calculam indicadores percentuais sobre ROL, os mesmos filtros também são repassados para o `GetRolRequest`.
- O comportamento real do filtro de datas depende do repositório de cada indicador, pois cada métrica pode usar uma coluna de data diferente.

---

## 4. Segurança e autorização

Todos os endpoints são protegidos por:

```python
@require_permission("api-delpi.access")
```

Isso significa que apenas usuários autenticados e autorizados com a permissão adequada podem consumir os indicadores da rota.

---

## 5. Contrato de resposta

Todos os endpoints seguem o padrão de resposta da aplicação via:

- `success_response(...)`
- `error_response(...)`

### Estrutura geral de sucesso

```json
{
  "success": true,
  "message": "...",
  "data": {
    "...": "..."
  }
}
```

### Estrutura geral de erro

```json
{
  "success": false,
  "message": "..."
}
```

### Tratamento padrão de erro

Cada endpoint trata:

- `ValueError` → HTTP 400
- `Exception` → HTTP 500

Além disso, a rota registra erros com `log_error(...)`.

---

## 6. Arquitetura da feature

A feature de Produção segue o padrão atual da API DELPI:

```text
HTTP Route
  ↓
ProductionRequest / GetRolRequest
  ↓
Composer
  ↓
Use Case
  ↓
Repository Port
  ↓
Repository Concreto
  ↓
Fonte de dados
```

### Fontes de dados utilizadas

#### Indicadores baseados em Google Sheets

- Direct Labor Cost %
- Production Cost %
- Depreciation %

Esses indicadores usam repositórios com `GoogleSheetsClient` e leitura CSV.

#### Indicadores baseados em TOTVS / SQL Server

- Overall Equipment Effectiveness %
- On-Time Delivery %
- ROL (para cálculo dos percentuais financeiros)

Esses indicadores usam repositórios baseados em `BaseRepository`, `QueryBuilder` e conexão com o banco do Protheus/TOTVS.

---

## 7. Endpoint — Direct Labor Cost %

### URL

```http
GET /apps/api-delpi/production/direct_labor_cost_pct
```

### Objetivo

Retornar o percentual médio de **custo de mão de obra direta** em relação à **ROL** no período filtrado.

### Fluxo de cálculo

1. A rota recebe `branch`, `start_date` e `end_date`
2. É criado um `ProductionRequest`
3. É criado também um `GetRolRequest` com os mesmos filtros
4. O use case consulta o repositório de mão de obra direta
5. O repositório retorna os custos encontrados na planilha
6. O use case calcula a média dos custos válidos
7. O use case consulta a ROL no repositório financeiro
8. O percentual é calculado com a fórmula:

```text
direct_labor_cost_pct = (average_direct_labor_cost / rol) * 100
```

### Resposta esperada

```json
{
  "success": true,
  "message": "Custo de mão de obra direta buscado com sucesso.",
  "data": {
    "direct_labor_cost_pct": 12.34
  }
}
```

### Observações técnicas

- Apenas valores de custo válidos entram no cálculo da média
- Se a ROL for zero ou ausente, o percentual retorna `null`
- O cálculo usa média simples dos registros retornados pela planilha

---

## 8. Endpoint — Production Cost %

### URL

```http
GET /apps/api-delpi/production/production_cost_pct
```

### Objetivo

Retornar o percentual médio de **custo de produção** em relação à **ROL** no período filtrado.

### Fluxo de cálculo

1. Receber filtros da rota
2. Criar `ProductionRequest`
3. Criar `GetRolRequest`
4. Consultar o repositório de custo de produção
5. Calcular a média dos custos válidos
6. Consultar a ROL
7. Aplicar a fórmula:

```text
production_cost_pct = (average_production_cost / rol) * 100
```

### Resposta esperada

```json
{
  "success": true,
  "message": "Custo de produção buscado com sucesso.",
  "data": {
    "production_cost_pct": 48.91
  }
}
```

### Observações técnicas

- O fluxo é estruturalmente idêntico ao de mão de obra direta
- O valor vem de planilha distinta, mas segue o mesmo padrão de composição
- Se não houver ROL válida, o percentual retorna `null`

---

## 9. Endpoint — Depreciation %

### URL

```http
GET /apps/api-delpi/production/depreciation_pct
```

### Objetivo

Retornar o percentual médio de **depreciação** em relação à **ROL** no período filtrado.

### Fluxo de cálculo

1. Receber filtros da rota
2. Criar `ProductionRequest`
3. Criar `GetRolRequest`
4. Consultar o repositório de depreciação
5. Calcular a média dos custos válidos
6. Consultar a ROL
7. Aplicar a fórmula:

```text
depreciation_pct = (average_depreciation_cost / rol) * 100
```

### Resposta esperada

```json
{
  "success": true,
  "message": "Depreciação buscada com sucesso.",
  "data": {
    "depreciation_pct": 7.42
  }
}
```

### Observações técnicas

- O fluxo segue exatamente o mesmo padrão de custo percentual sobre a ROL
- O indicador é apropriado para visão gerencial e comparação temporal

---

## 10. Endpoint — Overall Equipment Effectiveness %

### URL

```http
GET /apps/api-delpi/production/overall_equipment_effectiveness_pct
```

### Objetivo

Retornar a **eficiência geral dos equipamentos (OEE)** no período filtrado.

### Fonte de dados

View `vw_Apontamentos_Eficiencia` — coluna `EFICIENCIA_PERCENTUAL` (tempo previsto ÷ tempo real × 100).

### Fluxo de cálculo

1. Receber filtros da rota
2. Criar `ProductionRequest`
3. Executar o use case de OEE
4. O repositório monta o `WHERE` com `build_fabril_view_filters`
5. A consulta lê os registros da view fabril
6. O SQL calcula a média de `EFICIENCIA_PERCENTUAL` na faixa 0–199%
7. O valor é retornado como percentual de OEE

### Observações técnicas importantes

#### Conversão segura de valores

O cálculo do OEE considera apenas eficiência na faixa operacional **0–199%** (outliers excluídos de médias/KPIs).

A estratégia no SQL é:

```sql
ROUND(AVG(EFICIENCIA_PERCENTUAL), 2)
```

Isso garante que:

- espaços sejam removidos
- strings vazias virem `NULL`
- valores não numéricos não quebrem a consulta
- o `AVG(...)` ignore valores inválidos

#### Normalização de Decimal

Como o retorno do SQL Server pode vir como `Decimal`, a infraestrutura base de repositório precisa normalizar esse tipo para `float` antes da serialização JSON.

### Resposta esperada

```json
{
  "success": true,
  "message": "Eficiência geral dos equipamentos buscada com sucesso.",
  "data": {
    "overall_equipment_effectiveness_pct": 83.57
  }
}
```

---

## 11. Endpoint — On-Time Delivery %

### URL

```http
GET /apps/api-delpi/production/on_time_delivery_pct
```

### Objetivo

Retornar o percentual de **ordens de produção entregues no prazo** dentro da faixa informada.

### Regra de negócio

Uma OP é considerada:

- **No prazo** quando `C2_DATRF <= C2_DATPRF`
- **Em atraso** quando `C2_DATRF > C2_DATPRF`

A apuração deve considerar **OP distinta**, usando `C2_NUM` como chave de consolidação.

### Tabela principal

- `SC2010` — Ordens de Produção

### Campos relevantes

- `C2_FILIAL`
- `C2_NUM`
- `C2_DATPRF` — data prevista de entrega
- `C2_DATRF` — data real de fim
- `D_E_L_E_T_`

### Critérios de inclusão

Entram no cálculo apenas registros que atendem a todos os critérios abaixo:

- `D_E_L_E_T_ = ''`
- `C2_FILIAL = :FILIAL` quando `branch` for informado
- `C2_DATPRF` dentro da faixa informada
- `C2_DATPRF IS NOT NULL`
- `C2_DATRF IS NOT NULL`

### Lógica de cálculo

1. Receber `branch`, `start_date`, `end_date`
2. Criar `ProductionRequest`
3. Consultar `SC2010`
4. Consolidar OP distinta por `C2_NUM`
5. Classificar cada OP como no prazo ou atrasada
6. Calcular o percentual:

```text
on_time_delivery_pct = (ops_no_prazo / total_ops_finalizadas) * 100
```

### Resposta esperada

```json
{
  "success": true,
  "message": "On-Time Delivery buscado com sucesso.",
  "data": {
    "on_time_delivery_pct": 74.00
  }
}
```

### Observações técnicas

- O filtro de período deve cair sobre `C2_DATPRF`
- O percentual deve ser calculado sobre **OPs finalizadas**
- O uso de `NULLIF(COUNT(*), 0)` é recomendado para evitar divisão por zero
- A consolidação por `DISTINCT C2_NUM` é obrigatória para não distorcer o indicador

---

## 12. Resumo dos endpoints

| Endpoint | Indicador | Fonte principal |
|---|---|---|
| `/production/direct_labor_cost_pct` | Custo de mão de obra direta / ROL | Google Sheets + ROL TOTVS |
| `/production/production_cost_pct` | Custo de produção / ROL | Google Sheets + ROL TOTVS |
| `/production/depreciation_pct` | Depreciação / ROL | Google Sheets + ROL TOTVS |
| `/production/overall_equipment_effectiveness_pct` | OEE | TOTVS |
| `/production/on_time_delivery_pct` | OTD | TOTVS |

---

## 13. Exemplo consolidado de uso

### Requisição

```http
GET /apps/api-delpi/production/on_time_delivery_pct?branch=01&start_date=2026-03-01&end_date=2026-03-31
Authorization: Bearer <token>
```

### Resposta

```json
{
  "success": true,
  "message": "On-Time Delivery buscado com sucesso.",
  "data": {
    "on_time_delivery_pct": 74.0
  }
}
```

---

## 14. Padrões arquiteturais consolidados

A implementação da rota de Produção adota os seguintes princípios:

### Clean Architecture

- regras de negócio em use cases
- dependência de ports no domínio/aplicação
- repositories concretos em infraestrutura
- rota HTTP sem lógica de negócio relevante

### Composição explícita

Cada endpoint usa um builder dedicado no `production_composer.py`.

### Tratamento previsível de erros

- erro de validação → 400
- erro inesperado → 500
- log sempre registrado

### Contrato simples de saída

Cada endpoint retorna um dicionário enxuto com o indicador principal, facilitando:

- consumo por frontend
- consumo por dashboard
- evolução incremental da API

---

## 15. Evoluções futuras recomendadas

### 15.1 Endpoint consolidado de dashboard

Criar um endpoint único, por exemplo:

```http
GET /apps/api-delpi/production/summary
```

que retorne os cinco indicadores em uma única resposta.

### 15.2 Detalhamento opcional por indicador

Especialmente para OTD, pode ser útil permitir:

- lista de OPs consideradas
- total de OPs finalizadas
- total de OPs no prazo
- total de OPs atrasadas

### 15.3 Padronização de nomes de resposta

Manter todos os campos no formato explícito:

- `direct_labor_cost_pct`
- `production_cost_pct`
- `depreciation_pct`
- `overall_equipment_effectiveness_pct`
- `on_time_delivery_pct`

### 15.4 Validação explícita de formato de data

Hoje o parsing depende da infraestrutura dos repositórios. Uma melhoria é validar formato de data logo na borda HTTP.

### 15.5 Testes automatizados

Adicionar cobertura para:

- use cases com repositórios fake
- queries agregadas
- cenários sem dados
- cenários com divisão por zero
- normalização de `Decimal`
- OEE com eficiência fora da faixa 0–199% (outliers excluídos de médias)

---

## 16. Conclusão

A rota de Produção consolida uma base importante de indicadores industriais e financeiros na API DELPI.

Ela foi estruturada para suportar:

- governança central de métricas
- padronização de contratos de API
- separação arquitetural clara
- evolução incremental sem quebra de contrato

No estado atual, a feature entrega um conjunto consistente de indicadores essenciais de produção:

- custo de mão de obra direta sobre a ROL
- custo de produção sobre a ROL
- depreciação sobre a ROL
- eficiência geral dos equipamentos
- entrega no prazo

Essa base já é suficiente para alimentar dashboards, consultas operacionais e análises gerenciais, mantendo aderência à arquitetura da API DELPI e aos princípios de qualidade definidos para o projeto.

