# Financeiro — Inadimplência

Backend analítico de títulos financeiros quitados para o indicador de
inadimplência / pontualidade da Minha DELPI.

## Objetivo

Expor agregações e listagens sobre a view somente leitura:

```text
dbo.VW_FINANCEIRO_INADIMPLENCIA
```

A view já consolida as regras de negócio do Protheus. A API **não** consulta
diretamente `SE1010`, `SE5010` ou `SA1010` e **não** recria essas regras.

## Fonte de dados

| Item | Valor |
|---|---|
| Banco | SQL Server `DELPI` (TOTVS) |
| View | `dbo.VW_FINANCEIRO_INADIMPLENCIA` |
| Acesso | somente leitura, `WITH (NOLOCK)` |
| Filtro temporal | `MES_REFERENCIA >= start` **e** `MES_REFERENCIA < end_exclusive` |

## Período padrão

Quando `start_date` e `end_date` são omitidos:

```text
últimos 12 meses completos
```

Exemplo em julho/2026:

```text
data_inicio = 2025-07-01
data_fim_exclusiva = 2026-07-01
```

O mês corrente incompleto **não** entra no padrão.

Regras:

- informe **ambas** as datas ou **nenhuma**;
- `end_date` é **limite exclusivo**;
- período máximo: **60 meses**;
- datas em ISO `YYYY-MM-DD`.

## Fórmulas

### Por quantidade

```text
percentual_em_dia_qtd = SUM(PAGO_EM_DIA) / COUNT(*) * 100
percentual_inadimplencia_qtd = SUM(PAGO_COM_ATRASO) / COUNT(*) * 100
```

### Por valor

```text
percentual_em_dia_valor =
  SUM(VALOR_TITULO quando PAGO_EM_DIA = 1) / SUM(VALOR_TITULO) * 100

percentual_inadimplencia_valor =
  SUM(VALOR_TITULO quando PAGO_COM_ATRASO = 1) / SUM(VALOR_TITULO) * 100
```

Percentuais arredondados em 2 casas. Divisão por zero retorna `0.0`.

## Faixas de atraso (`FAIXA_ATRASO`)

| Ordem | Código | Rótulo |
|---|---|---|
| 1 | `EM_DIA` | Em dia |
| 2 | `ATRASO_1_A_5_DIAS` | 1 a 5 dias |
| 3 | `ATRASO_6_A_15_DIAS` | 6 a 15 dias |
| 4 | `ATRASO_16_A_30_DIAS` | 16 a 30 dias |
| 5 | `ATRASO_ACIMA_30_DIAS` | Acima de 30 dias |

## Endpoints

Base: `/apps/api-delpi/financeiro/inadimplencia`

| Método | Path | operationId |
|---|---|---|
| GET | `/resumo` | `get_financeiro_inadimplencia_resumo` |
| GET | `/mensal` | `get_financeiro_inadimplencia_mensal` |
| GET | `/faixas-atraso` | `get_financeiro_inadimplencia_faixas_atraso` |
| GET | `/clientes` | `get_financeiro_inadimplencia_clientes` |
| GET | `/titulos` | `get_financeiro_inadimplencia_titulos` |

### Parâmetros comuns

| Param | Tipo | Default | Notas |
|---|---|---|---|
| `start_date` | date | período padrão | inclusivo |
| `end_date` | date | período padrão | exclusivo |

### `/clientes`

| Param | Default | Notas |
|---|---|---|
| `page` | 1 | |
| `page_size` | 20 | máx. 100 |
| `sort_by` | `late_amount` | whitelist |
| `sort_dir` | `desc` | `asc` \| `desc` |
| `q` | — | CLIENTE / NOME_CLIENTE / NOME_REDUZIDO |
| `only_with_delays` | `true` | |

### `/titulos`

| Param | Default | Notas |
|---|---|---|
| `customer_code` | — | detalhe do ranking |
| `store_code` | — | detalhe do ranking |
| `status` | `all` | `all` \| `on_time` \| `late` |
| `delay_range` | — | códigos oficiais |
| `q` | — | número, prefixo, cliente, nome |
| `page` / `page_size` | 1 / 20 | máx. 100 |
| `sort_by` | `amount` | whitelist + desempate estável |

## Exemplos de resposta

### Resumo

```json
{
  "periodo": {
    "data_inicio": "2025-07-01",
    "data_fim_exclusiva": "2026-07-01",
    "rotulo": "Últimos 12 meses completos"
  },
  "totais": {
    "titulos": 6111,
    "titulos_em_dia": 5624,
    "titulos_atraso": 487,
    "valor_total": 57190199.49,
    "valor_atraso": 5552009.4
  },
  "indicadores": {
    "percentual_em_dia_qtd": 92.03,
    "percentual_inadimplencia_qtd": 7.97,
    "percentual_em_dia_valor": 90.29,
    "percentual_inadimplencia_valor": 9.71
  }
}
```

## Permissão prevista

```text
financeiro-inadimplencia.access
financeiro-inadimplencia.view
```

Também aceita `api-delpi.access` (lista `FINANCEIRO_INADIMPLENCIA_READ_PERMISSIONS`).

**Pendência de integração:** cadastrar a permissão no RBAC/Keycloak e no
manifesto do plugin MFE. Nesta etapa a API já valida via
`@require_any_permission`.

## Observações

- View somente leitura; não criar migrations TOTVS nesta camada.
- Payload `data` em snake_case (padrão da api-delpi).
- Envelope `{ success, message, data, meta }` via `api_delpi_success`.
