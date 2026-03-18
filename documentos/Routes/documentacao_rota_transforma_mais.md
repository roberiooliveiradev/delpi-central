# Documentação da rota Transforma Mais

## Visão geral

A feature **Transforma Mais** consulta uma planilha pública do Google Sheets, normaliza os dados e expõe dois endpoints HTTP:

- `GET /transforma-mais/processes`
- `GET /transforma-mais/processes/summary`

No contexto da aplicação, considerando o `root_path` configurado em `main.py`, os caminhos efetivos ficam sob:

- `/apps/api-delpi/transforma-mais/processes`
- `/apps/api-delpi/transforma-mais/processes/summary`

A fonte de dados é uma planilha Google Sheets lida como CSV por um client dedicado.

---

## Arquitetura da feature

### Router
Responsável por:

- receber os parâmetros HTTP
- criar os DTOs de entrada
- chamar os use cases
- traduzir erros para respostas HTTP

### Use cases
Existem dois casos de uso:

- `ListProcessUseCase`: listagem de processos
- `GetProcessSummaryUseCase`: resumo consolidado

### Port
O contrato do repositório é definido por `ProcessQueryRepositoryPort`, com os métodos:

- `list_process(request)`
- `get_process_summary(request)`

### Repository
A implementação concreta está em `ProcessRepository`, responsável por:

- ler a planilha
- mapear linhas para entidade/modelo interno
- aplicar filtros
- calcular indicadores e série mensal

### Provider
A integração com Google Sheets fica em `GoogleSheetsClient`, que:

- monta a URL de exportação CSV
- baixa o conteúdo
- lê as linhas
- normaliza os nomes das colunas

### Composer
A composição injeta:

- `sheet_id`
- `gid`
- `timeout`

com suporte a variáveis de ambiente e fallback default.

---

## Configuração

### Variáveis de ambiente

- `GOOGLE_SHEETS_TIMEOUT`
- `TRANSFORMA_MAIS_SHEET_ID`
- `TRANSFORMA_MAIS_SHEET_GID`

Se não forem definidas, o composer usa valores padrão.

Exemplo:

```env
GOOGLE_SHEETS_TIMEOUT=10
TRANSFORMA_MAIS_SHEET_ID=1pqXRoXjSS91TxVqHioCPWKQVfY2ZAg-w
TRANSFORMA_MAIS_SHEET_GID=127374664
```

---

## Entidade de domínio

A entidade retornada na listagem é `Process`.

### Campos

- `id`
- `name_process`
- `sector_name`
- `daily_savings`
- `payback_months`
- `status`
- `implementetion_date`

---

# Endpoint 1 — Listar processos

## URL

```http
GET /apps/api-delpi/transforma-mais/processes
```

## Objetivo

Retornar os processos da planilha com filtros opcionais.

## Query params

- `id`
- `name_process`
- `sector_name`
- `status`
- `start_date`
- `end_date`

## Descrição dos filtros

### `id`
Filtra por ocorrência parcial no identificador do processo.

### `name_process`
Filtra por ocorrência parcial no nome do processo.

### `sector_name`
Filtra por ocorrência parcial no setor.

### `status`
Filtra por ocorrência parcial no status.

### `start_date`
Filtra pela data mínima de implementação.

### `end_date`
Filtra pela data máxima de implementação.

## Regra de filtro por datas

O filtro de datas é aplicado sobre a **data de implementação** do processo.

### Formatos aceitos

- `YYYY-MM-DD`
- `DD/MM/YYYY`
- `DD-MM-YYYY`
- `YYYY/MM/DD`
- `MM/DD/YYYY`
- `MM-DD-YYYY`

## Exemplo de chamada

```http
GET /apps/api-delpi/transforma-mais/processes?sector_name=Engenharia&status=Concluído&start_date=2025-11-01&end_date=2025-11-30
Authorization: Bearer <token>
```

## Exemplo de resposta

```json
{
  "success": true,
  "total": 2,
  "items": [
    {
      "id": "12",
      "name_process": "Controle de LMP's",
      "sector_name": "Engenharia",
      "daily_savings": 2.04,
      "payback_months": 32.83,
      "status": "Concluído",
      "implementetion_date": "13/01/2026"
    }
  ]
}
```

## Respostas de erro

### 400
Retornada quando:

- `start_date` é inválida
- `end_date` é inválida
- `start_date > end_date`

Exemplo:

```json
{
  "detail": "start_date inválida. Use formatos como YYYY-MM-DD ou DD/MM/YYYY."
}
```

### 500
Retornada em falhas inesperadas no processamento.

```json
{
  "detail": "Erro ao listar processos da planilha: ..."
}
```

---

# Endpoint 2 — Resumo consolidado

## URL

```http
GET /apps/api-delpi/transforma-mais/processes/summary
```

## Objetivo

Retornar indicadores consolidados dos processos concluídos e uma série mensal de economia operacional.

## Query params

- `start_date`
- `end_date`

## Estrutura da resposta

A resposta contém:

- `implemented_solutions`
- `total_savings_until_now`
- `total_hours_saved_until_now`
- `total_investment_until_now`
- `average_roi_percent`
- `monthly_description`
- `range`

### `monthly_description`
Cada item possui:

- `month`
- `total_savings_month`

### `range`
Possui:

- `start_date`
- `end_date`
- `accumulated_savings`

---

## Regras de cálculo

### `implemented_solutions`
Quantidade de processos com status concluído.

### `total_savings_until_now`
Soma da coluna **Economia até agora** dos processos concluídos.

### `total_hours_saved_until_now`
Calculado com base em:

- tempo atual por execução
- tempo após melhoria
- execuções por mês
- dias implantados

Fórmula:

```text
minutes_saved_per_execution = max(time_before - time_after, 0)
monthly_minutes_saved = minutes_saved_per_execution * executions_per_month
proportional_minutes_saved = monthly_minutes_saved * (days_implanted / 30)
hours = proportional_minutes_saved / 60
```

### `total_investment_until_now`
Soma direta da coluna de investimento total.

> Observação: este indicador agregado ainda é provisório. O detalhamento mensal de investimento foi removido porque a modelagem financeira ainda será refinada.

### `average_roi_percent`
Média simples da coluna **ROI anual (%)** dos processos concluídos.

### `monthly_description`
A série mensal retorna a **economia operacional total do mês**, sem acumular os meses anteriores.

A regra é:

1. Para cada processo concluído, identificar a data de implementação.
2. Para cada mês da série, calcular quantos dias o processo ficou ativo dentro daquele mês.
3. Multiplicar os dias ativos pela **economia por dia** do processo.
4. Somar todos os processos para obter `total_savings_month`.

Fórmula por processo:

```text
economia_do_processo_no_mes = dias_ativos_no_mes * economia_por_dia
```

Fórmula do mês:

```text
total_savings_month = soma da economia_do_processo_no_mes de todos os processos ativos no mês
```

### `range.accumulated_savings`
Soma de **Economia até agora** dos processos cuja data de implementação está dentro do intervalo informado.

---

## Exemplo de chamada

```http
GET /apps/api-delpi/transforma-mais/processes/summary?start_date=2025-09-01&end_date=2025-11-30
Authorization: Bearer <token>
```

## Exemplo de resposta

```json
{
  "success": true,
  "data": {
    "implemented_solutions": 21,
    "total_savings_until_now": 75681.16,
    "total_hours_saved_until_now": 2752.62,
    "total_investment_until_now": 44722.47,
    "average_roi_percent": 4.53,
    "monthly_description": [
      {
        "month": "2025-09",
        "total_savings_month": 2487.12
      },
      {
        "month": "2025-10",
        "total_savings_month": 4686.53
      },
      {
        "month": "2025-11",
        "total_savings_month": 16006.65
      }
    ],
    "range": {
      "start_date": "2025-09-01",
      "end_date": "2025-11-30",
      "accumulated_savings": 75550.71
    }
  }
}
```

## Respostas de erro

### 400
Retornada quando o range de datas é inválido.

### 500
Retornada em falhas inesperadas durante a geração do resumo.

---

## Normalização de colunas da planilha

O `GoogleSheetsClient` normaliza as colunas antes do repository consumir os dados.

Exemplos de transformação:

- espaços viram `_`
- `%` vira `percent`
- acentos são removidos
- `/` e `-` viram `_`

Isso permite acessar campos como:

- `nome_do_processo`
- `economia_por_dia`
- `roi_anual_percent`
- `data_da_implementacao`

---

## Segurança

A aplicação usa autenticação Bearer JWT global.

Exemplo de header:

```http
Authorization: Bearer <token>
```

---

## Resumo funcional

### `GET /transforma-mais/processes`
Use para:

- listar processos
- aplicar filtros textuais
- filtrar por data de implementação

### `GET /transforma-mais/processes/summary`
Use para:

- obter indicadores consolidados
- visualizar economia operacional por mês
- consultar economia acumulada por range de implantação

---

## Limitações atuais

- `total_investment_until_now` ainda é uma soma simples da coluna de investimento.
- o detalhamento mensal de investimento não é retornado.
- o cálculo mensal usa dias corridos, não dias úteis.
- o mês atual ainda pode precisar de ajuste futuro caso a regra mude para considerar apenas até a data corrente.

---

## Evoluções futuras sugeridas

- refinar a modelagem financeira de investimentos
- separar custos fixos, variáveis e de implantação
- revisar o cálculo agregado de investimento
- adicionar descrições e exemplos diretamente no Swagger

