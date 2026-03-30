# Documentação da rota Transforma Mais

## Visão geral

A feature **Transforma Mais** expõe duas rotas HTTP para consulta de processos e geração de resumo consolidado:

* `GET /apps/api-delpi/engineering/transforma-mais/processes`
* `GET /apps/api-delpi/engineering/transforma-mais/processes/summary`

A feature trabalha com dados brutos de processos, revisões, medições, investimentos e recursos compartilhados, aplicando regras de cálculo para economia bruta, custos brutos, economia líquida, horas economizadas, payback e ROI.

---

## Endpoints

## 1. Listagem de processos

### URL

```http
GET /apps/api-delpi/engineering/transforma-mais/processes
```

### Objetivo

Retornar os processos do Transforma Mais com filtros opcionais.

### Query params suportados

* `id`
* `name_process`
* `filial_id`
* `sector_name`
* `status`
* `start_date`
* `end_date`

### Descrição dos filtros

#### `id`

Filtra por ocorrência parcial no identificador do processo.

#### `name_process`

Filtra por ocorrência parcial no nome do processo.

#### `filial_id`

Filtra os processos por filial.

#### `sector_name`

Filtra por ocorrência parcial no setor.

#### `status`

Filtra por ocorrência parcial no status do processo.

#### `start_date`

Filtra pela data mínima de implementação exibida no processo.

#### `end_date`

Filtra pela data máxima de implementação exibida no processo.

### Estrutura de resposta

```json
{
  "success": true,
  "message": "Processos do Transforma Mais listados com sucesso.",
  "data": {
    "total": 2,
    "items": [
      {
        "id": "be4e59cd-1373-45bc-9a83-d202102e69cb",
        "name_process": "Acompanhamento de refugo",
        "filial_id": "01",
        "sector_name": "qualidade",
        "daily_savings": 7.21,
        "payback_months": 1.0,
        "status": "ativo",
        "implementetion_date": "26/09/2025"
      }
    ]
  }
}
```

### Significado dos campos retornados

* `id`: identificador do processo.
* `name_process`: nome do processo.
* `filial_id`: filial vinculada ao processo.
* `sector_name`: setor do processo.
* `daily_savings`: economia líquida diária estimada do processo.
* `payback_months`: quantidade estimada de meses para retorno do investimento único.
* `status`: status do processo.
* `implementetion_date`: data de implantação ou início de vigência da revisão exibida.

---

## 2. Resumo consolidado

### URL

```http
GET /apps/api-delpi/engineering/transforma-mais/processes/summary
```

### Objetivo

Retornar o resumo consolidado dos processos com indicadores acumulados e breakdown mensal.

### Query params suportados

* `filial_id`
* `start_date`
* `end_date`

### Comportamento do filtro `filial_id`

Quando informado, o sistema filtra toda a base antes do cálculo do resumo:

* processos
* revisões
* medições
* investimentos
* vínculos de recursos compartilhados
* recursos compartilhados vinculados

Ou seja, o resumo passa a refletir apenas os dados da filial solicitada.

---

## Estrutura da resposta

```json
{
  "success": true,
  "message": "Resumo dos processos do Transforma Mais carregado com sucesso.",
  "data": {
    "implemented_solutions_count": 4,
    "total_net_savings_until_now": 5792.25,
    "total_hours_saved_until_now": 162.42,
    "total_gross_costs_until_now": 1135.2,
    "average_roi": 15.5,
    "monthly_breakdown": [
      {
        "month": "2025-09",
        "gross_savings_month": 479.85,
        "gross_costs_month": 300.1,
        "gross_investment_month": 193.1,
        "gross_recurring_investment_month": 0,
        "shared_resource_cost_month": 107,
        "net_savings_month": 179.75
      }
    ],
    "range_summary": {
      "start_date": null,
      "end_date": null,
      "accumulated_net_savings_until_now": 5792.25
    }
  }
}
```

---

## Significado dos campos do resumo

### `implemented_solutions_count`

Quantidade de revisões comparáveis consideradas no cálculo.

São consideradas comparáveis as revisões com cenário:

* `melhoria`
* `automacao`
* `correcao`

### `total_net_savings_until_now`

Economia líquida acumulada de todo o período retornado.

Fórmula conceitual:

```text
total_net_savings_until_now = soma do net_savings_month
```

### `total_hours_saved_until_now`

Total acumulado de horas economizadas com base na redução de tempo operacional entre baseline e revisão atual.

### `total_gross_costs_until_now`

Total acumulado de custos brutos do período.

Esse total soma, mês a mês:

* investimentos únicos
* investimentos recorrentes
* custos de recursos compartilhados

Fórmula conceitual:

```text
total_gross_costs_until_now = soma do gross_costs_month
```

### `average_roi`

ROI médio das revisões calculadas.

No cálculo atual, o ROI é tratado como razão de retorno sobre investimento único, e não como percentual já multiplicado por 100.

---

## Significado dos campos de `monthly_breakdown`

### `month`

Mês de competência no formato `YYYY-MM`.

### `gross_savings_month`

Economia bruta operacional do mês.

Esse valor considera apenas ganhos operacionais, como:

* redução de tempo
* redução de retrabalho
* redução de erros
* redução de outros desperdícios

Não desconta investimentos nem recursos compartilhados.

### `gross_costs_month`

Custo bruto total do mês.

Fórmula:

```text
gross_costs_month = gross_investment_month + gross_recurring_investment_month + shared_resource_cost_month
```

### `gross_investment_month`

Soma dos investimentos únicos lançados no mês.

### `gross_recurring_investment_month`

Soma dos investimentos recorrentes válidos no mês.

Atualmente o cálculo aceita recorrências como:

* `mensal`
* `trimestral`
* `semestral`
* `anual`

com rateio proporcional por mês quando aplicável.

### `shared_resource_cost_month`

Custo total de recursos compartilhados rateados no mês.

O cálculo considera apenas recursos elegíveis no mês, respeitando:

* status do recurso
* vigência do recurso
* vínculo ativo
* vigência do vínculo
* critério de rateio

### `net_savings_month`

Economia líquida do mês.

Fórmula:

```text
net_savings_month = gross_savings_month - gross_costs_month
```

Esse valor pode ser positivo ou negativo.

---

## Significado dos campos de `range_summary`

### `start_date`

Data inicial informada no filtro.

### `end_date`

Data final informada no filtro.

### `accumulated_net_savings_until_now`

Soma do `net_savings_month` dentro do intervalo retornado.

Se não houver filtro de datas, representa o acumulado de todo o período calculado.

---

## Regras de cálculo

## 1. Economia bruta

A economia bruta é calculada comparando a baseline com a revisão atual.

Entram nessa conta apenas diferenças operacionais:

* custo de tempo
* custo de retrabalho
* custo de erros
* outros desperdícios

Fórmula conceitual:

```text
gross_savings =
    (baseline_time_cost - current_time_cost)
  + (baseline_rework_cost - current_rework_cost)
  + (baseline_error_cost - current_error_cost)
  + (baseline_other_cost - current_other_cost)
```

## 2. Custos brutos

Os custos brutos do mês são compostos por:

* investimento único do mês
* investimento recorrente do mês
* custo rateado de recurso compartilhado do mês

## 3. Economia líquida

```text
net_savings = gross_savings - gross_costs
```

## 4. Recursos compartilhados

O custo de recurso compartilhado por revisão é calculado conforme o critério de rateio do recurso.

Critérios suportados:

### `igualitario`

Divide o valor do recurso igualmente entre os vínculos elegíveis.

### `por_revisoes_ativas`

Divide o valor do recurso pelo número de revisões elegíveis no mês.

### `por_peso`

Divide o valor proporcionalmente ao `peso_rateio` de cada vínculo.

## 5. Payback

O payback do processo é calculado por:

```text
payback_months = total_unique_investment / net_savings_month
```

Se a economia líquida mensal for menor ou igual a zero, o payback não é retornado.

## 6. Horas economizadas

As horas economizadas são calculadas a partir da diferença entre o tempo baseline e o tempo atual, multiplicada pelo volume mensal e ajustada pela fração ativa no mês.

---

## Exemplo de uso

### Listagem por filial

```http
GET /apps/api-delpi/engineering/transforma-mais/processes?filial_id=01
```

### Resumo por filial

```http
GET /apps/api-delpi/engineering/transforma-mais/processes/summary?filial_id=01
```

### Resumo por filial e período

```http
GET /apps/api-delpi/engineering/transforma-mais/processes/summary?filial_id=01&start_date=2025-09-01&end_date=2026-03-31
```

---

## Respostas de erro

### 400

Usada para erros de validação, como datas inválidas.

### 500

Usada para falhas inesperadas de processamento.

---

## Observações

* O resumo mensal considera meses corridos.
* O cálculo usa apenas revisões comparáveis.
* Recursos compartilhados inativos não entram no cálculo.
* Vínculos de recursos compartilhados também precisam estar ativos e elegíveis no mês.
* Os valores são arredondados apenas no resultado final exibido.

---

## Resumo funcional

### `GET /processes`

Use para:

* listar processos
* filtrar por filial
* filtrar por nome, setor e status
* consultar economia diária e payback estimado

### `GET /processes/summary`

Use para:

* obter visão consolidada por filial
* analisar economia bruta, custo bruto e economia líquida por mês
* consultar horas economizadas
* avaliar custos compartilhados e ROI
