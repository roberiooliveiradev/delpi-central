# Especificação — View `dbo.vw_Apontamentos_Eficiencia`

> Fonte operacional do plugin **eficiência fabril**.  
> Validação Fase 0: [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) (2026-05-27).

---

## Objetivo

Consolidar apontamentos de produção do Protheus (`SH6010`), calculando eficiência operacional, tempos previsto/real, tempo ganho ou perdido e resultado financeiro de MOD.

- **Granularidade:** 1 linha = 1 apontamento
- **Exclusão na view:** recurso `CT-00` (na SQL da view)
- **Exclusão na api-delpi/MFE:** `CT-00`, `CT-70`, `CT-16A`, `CT-99` (não produtivos / regras de negócio)

---

## Tabelas de composição

| Tabela | Finalidade |
|--------|------------|
| `SH6010` | Movimentos/apontamentos de produção |
| `SHY010` | Tempos fixos da OP (setup + estimado) |
| `SC2010` | Ordem de produção (quantidade total) |
| `SYS_USR` | Nome/login do operador |
| `SH1010` | Recursos / centros de trabalho |
| `SBZ010` | Custo MOD/hora por centro de custo |

---

## Colunas (contrato para api-delpi / MFE)

| Coluna | Uso |
|--------|-----|
| `FILIAL` | Filtro |
| `OP`, `PRODUTO`, `DESCRICAO_PRODUTO`, `CENTRO_TRABALHO`, `OPERACAO` | Identificação / filtros |
| `COD_OPERADOR`, `LOGIN_OPERADOR`, `NOME_OPERADOR` | Filtro operador |
| `DATA_PRODUCAO` | Filtro período (tipo `DATE`) |
| `HORA_INICIO`, `HORA_FINAL`, `TEMPO_ORIGINAL` | Detalhe / ordenação |
| `QTD_APONTADA`, `QTD_TOTAL_OP` | Contexto |
| `TEMPO_REAL_HORAS`, `TEMPO_PREVISTO_HORAS` | KPI e agregação |
| `EFICIENCIA_INDICE`, `EFICIENCIA_PERCENTUAL` | KPI / gráficos |
| `CENTRO_CUSTO_RECURSO`, `PRODUTO_MOD`, `VALOR_MOD_HORA`, `STATUS_MOD` | MOD |
| `TEMPO_GANHO_PERDIDO_HORAS`, `RESULTADO_MOD`, `LUCRO_MOD`, `PREJUIZO_MOD` | KPI financeiro |
| `STATUS_RESULTADO_MOD`, `STATUS_REGISTRO` | Qualidade do registro |

---

## Fórmulas

```text
TEMPO_PREVISTO_HORAS = SETUP_OP + (HY_TEMPOM * (H6_QTDPROD / C2_QUANT))
EFICIENCIA_PERCENTUAL = (TEMPO_PREVISTO_HORAS / TEMPO_REAL_HORAS) × 100
TEMPO_GANHO_PERDIDO_HORAS = TEMPO_PREVISTO_HORAS - TEMPO_REAL_HORAS
RESULTADO_MOD = TEMPO_GANHO_PERDIDO_HORAS × VALOR_MOD_HORA
```

**Agregação no dashboard (implementado no MFE):**

```text
AVG(EFICIENCIA_PERCENTUAL)   -- média simples, registros OK, eficiência na faixa 0–199%
```

*(A ponderação por `SUM(TEMPO_PREVISTO)/SUM(TEMPO_REAL)` permanece válida como referência analítica, mas não é o KPI exibido.)*

| Eficiência % | Significado |
|--------------|-------------|
| > 100 | Mais rápido que o previsto |
| = 100 | No previsto |
| < 100 | Mais lento que o previsto |

---

## Literais validados (TOTVS — 2026-05-27)

### `STATUS_REGISTRO`

| Valor | Observação |
|-------|------------|
| `OK` | **Usar no dashboard por padrão** (~140k linhas) |
| `OPERADOR SEM VINCULO` | Excluir do KPI principal |
| `OP NAO ENCONTRADA` | Cadastro / OP |
| `TEMPO PREVISTO INVALIDO` | Cálculo |
| `PRODUTO MOD NAO ENCONTRADO NA SBZ` | Custo MOD |
| `TEMPO REAL ZERADO` | Divisão eficiência |
| `TEMPO REAL INVALIDO` | Formato tempo |

### `STATUS_MOD`

| Valor |
|-------|
| `OK` |
| `PRODUTO MOD NAO ENCONTRADO NA SBZ` |
| `RECURSO NAO ENCONTRADO NA SH1` |

### `STATUS_RESULTADO_MOD`

| Valor |
|-------|
| `LUCRO` |
| `PREJUIZO` |
| `NEUTRO` |
| `SEM VALOR MOD` |
| `TEMPO PREVISTO INVALIDO` |
| `TEMPO REAL ZERADO` |
| `TEMPO REAL INVALIDO` |

---

## Filiais

| `FILIAL` | Uso |
|----------|-----|
| `01` | Produção filial 01 |
| `02` | Produção filial 02 |

> Há 2 linhas com `FILIAL` vazio e `DATA_PRODUCAO` inválida (1900-01-01). O repository deve filtrar `FILIAL IN ('01','02')` ou equivalente.

---

## Volume (estimativa dev — maio/2026)

| Métrica | Valor |
|---------|-------|
| Total histórico (filiais 01+02) | ~373k linhas |
| Média últimos 30 dias | ~8,4k linhas/dia |
| Mai/2026 (mês corrente) | ~7k linhas |
| Pico diário recente | ~539 linhas |

**Implicação:** paginação server-side obrigatória na tabela; agregações no SQL.

---

## Regras de negócio para a aplicação

1. **Indicadores (KPIs/gráficos):** apenas `STATUS_REGISTRO = 'OK'` e `EFICIENCIA_PERCENTUAL` entre **0% e 199%** (inclusive).
2. **Tabela:** registros OK; eficiência fora da faixa exibidos como **Verificar** (fora dos indicadores).
3. **Eficiência agregada:** média simples de `EFICIENCIA_PERCENTUAL` (ver [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md)).
4. **CTs excluídos no repository:** `CT-00`, `CT-70`, `CT-16A`, `CT-99` (`LTRIM` em `CENTRO_TRABALHO`).
5. **Filiais:** `01` e `02` quando não há filtro de filial.
6. **Filtros UI:** operador por nome (`LIKE`); OP parcial; sem centro de custo na interface.

Detalhamento completo do plugin: [ESPECIFICACAO-PLUGIN.md](./ESPECIFICACAO-PLUGIN.md).

---

## SQL de referência

Arquivo no repositório:

`api-delpi/app/infrastructure/persistence/totvs/eficiencia_fabril/EFICIENCIA_FABRIL_VIEW.sql`

Script de validação:

```bash
docker exec delpi-api-delpi python scripts/validate_eficiencia_fabril_view.py \
  --markdown /tmp/FASE0-VALIDACAO.md
docker cp delpi-api-delpi:/tmp/FASE0-VALIDACAO.md \
  docs/12-roadmap-e-evolucao/eficiencia-fabril/FASE0-VALIDACAO.md
```
