# Especificação — View TOTVS Controle de Retrabalhos

> Fonte operacional do plugin **controle-retrabalhos**.

---

## Objetivo

Expor no SQL Server apontamentos de **horas improdutivas de retrabalho** para:

- KPIs e evolução mensal por filial;
- Rankings por recurso e colaborador;
- Listagem detalhada paginada para auditoria operacional.

**View canônica:** `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS`

**Filtro de negócio:** `MOTIVO = 'RT'` (retrabalho).

**Filiais:** `01` (SC), `02` (ES). Coluna: `FILIAL`.

---

## Constantes (código)

| Constante | Valor |
|-----------|--------|
| `RETRABALHO_HORAS_IMPRODUTIVAS_VIEW` | `dbo.VW_BI_RT_HORAS_IMPRODUTIVAS` |
| `RETRABALHO_MOTIVO_CODE` | `RT` |
| `FONTE_CUSTO_SEM_CUSTO` | `SEM CUSTO` |

Definidas em `api-delpi/app/domain/quality/retrabalho/retrabalho_view_scope.py`.

---

## Colunas usadas pela API (detalhes)

| Coluna view | Campo API |
|-------------|-----------|
| `DATA_REFERENCIA` | `dataReferencia` |
| `FILIAL` | `filial` |
| `OP` | `op` |
| `PRODUTO` | `produto` |
| `OPERACAO` | `operacao` |
| `RECURSO` | `recurso` |
| `CENTRO_CUSTO` | `centroCusto` |
| `CODIGO_OPERADOR` / `NOME_OPERADOR` | `codigoOperador` / `nomeOperador` |
| `TEMPO_HORAS` | `tempoHoras` |
| `VALOR_PARADA_RS` | `valorParada` |
| `FONTE_CUSTO` | `fonteCusto` |
| `MOTIVO` | `motivo` |
| `OBSERVACAO` | `observacao` |
| `RECNO` | `recno` |

---

## SQL — práticas

- `WITH (NOLOCK)` em todas as leituras analíticas.
- Filtros parametrizados (`?`): datas, filial, motivo RT.
- Período default: últimos **12 meses** (máx. **24**).
- Paginação detalhes: offset/limit com `page` / `pageSize`.

Implementação: `api-delpi/app/infrastructure/persistence/totvs/retrabalho/retrabalho_sql.py`.

---

## Validação Fase 0

Script: `api-delpi/scripts/validate_retrabalho_horas_improdutivas_view.py`

```bash
docker exec delpi-api-delpi python scripts/validate_retrabalho_horas_improdutivas_view.py
```

Teste unitário SQL (estrutura): `api-delpi/tests/test_retrabalho_sql.py`.
