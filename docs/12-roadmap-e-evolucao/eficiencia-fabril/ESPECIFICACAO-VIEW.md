# Especificação — View `dbo.vw_Apontamentos_Eficiencia`

> Fonte operacional do plugin **eficiência fabril**.  
> Validação Fase 0: [FASE0-VALIDACAO.md](./FASE0-VALIDACAO.md) (2026-05-27).

---

## Objetivo

Consolidar apontamentos de produção do Protheus (`SH6010`), calculando eficiência operacional, tempos previsto/real, tempo ganho ou perdido e resultado financeiro de MOD.

- **Granularidade:** 1 linha = 1 apontamento
- **Exclusão fixa na view:** recurso `CT-00`

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
| `OP`, `PRODUTO`, `CENTRO_TRABALHO`, `OPERACAO` | Identificação / filtros |
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

**Agregação global de eficiência (dashboard):**

```text
SUM(TEMPO_PREVISTO_HORAS) / SUM(TEMPO_REAL_HORAS) × 100
```

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

1. **Default:** `STATUS_REGISTRO = 'OK'` (toggle “incluir registros com problema”).
2. **Eficiência agregada:** sempre ponderada por `TEMPO_REAL_HORAS`.
3. **MOD:** somar `LUCRO_MOD` / `PREJUIZO_MOD` apenas em registros com `STATUS_MOD = 'OK'` (avaliar na Fase 1).
4. **CT-00:** já excluído na view; validação confirma `ct00_count = 0`.
5. **Filiais:** default `01` e `02` (mesmo padrão LMPs).

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
