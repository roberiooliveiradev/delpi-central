# Acompanhamento de Refugos — `/refugos`

Consultas de **refugo em valor (R$)** a partir de **`SBC010`** (`BC_TIPO = 'R'`), com joins em `SB1010`, custo médio agregado de `SB2010`, motivos `CYO010`, OP/`SC2010` (PA), e operador `SYS_USR`.

**Não substitui** as rotas chat/operacionais `GET /production/losses/*` (quantidade). Este módulo alimenta o dashboard MFE **scrap-monitoring**.

**Permissão:** `scrap-monitoring.access`, `scrap-monitoring.view`, `scrap-monitoring.view.filial-sc`, `scrap-monitoring.view.filial-es` ou `api-delpi.access`

**Validação por filial:** usuários com permissão apenas de uma filial recebem `403` ao consultar a outra (exceto superadmin ou `scrap-monitoring.view`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

Plugin consumidor: `plugins/scrap-monitoring` · Filiais: SC=`01`, ES=`02`.

---

## Endpoints

| Método | Rota | `meta.shape` | `meta.operationId` |
|---|---|---|---|
| GET | `/refugos/health` | `scalar` | `get_refugos_health` |
| GET | `/refugos/filtros` | `scalar` | `get_refugos_filtros` |
| GET | `/refugos/resumo` | `scalar` | `get_refugos_resumo` |
| GET | `/refugos/rankings` | `playbook_report` | `get_refugos_rankings` |
| GET | `/refugos/registros` | `paged_list` | `get_refugos_registros` |

---

## Parâmetros comuns

| Parâmetro | Alias | Descrição |
|---|---|---|
| `filial` | — | Filial Protheus `01` (SC) ou `02` (ES) — **obrigatório** (exceto `/health`) |
| `dataInicio` | `dataInicio` | Data inicial `YYYY-MM-DD` (default: 1º dia do mês atual) |
| `dataFim` | `dataFim` | Data final `YYYY-MM-DD` (default: hoje) |
| `mp` | — | Filtro opcional por código de matéria-prima |
| `pa` | — | Filtro opcional por produto acabado (via OP) |
| `op` | — | Filtro opcional por ordem de produção |
| `motivo` | — | Filtro opcional por código CYO (`BC_MOTIVO`) |
| `centroTrabalho` | `centroTrabalho` | Filtro opcional por `BC_RECURSO` (ex.: `CT-23`) |

Janela máxima: **24 meses**. Ranking default: top **10** (`limit` até 50). Registros: `page`, `pageSize` (máx. 100).

---

## Valor (R$)

```text
ValorPerda = BC_QUANT * COALESCE(NULLIF(AVG(B2_CM1), 0), NULLIF(B1_CUSTD, 0), 0)
```

`AVG(B2_CM1)` é calculado por filial+produto (sem multiplicar linhas por `B2_LOCAL`). Validado na Fase 0 contra TOTVS (`api-delpi/scripts/sql/refugos_totvs_probe.py`).

---

## `/refugos/resumo`

Retorna:

| Campo | Significado |
|---|---|
| `totalValor` / `totalQuantidade` / `ocorrencias` | Totais do período |
| `registrosSemCusto` | Linhas com custo unitário zero |
| `valorDia` | Soma no dia de `dataFim` |
| `valorMes` | Soma do mês calendário de `dataFim` até `dataFim` |

---

## `/refugos/rankings`

Query obrigatória: `dimension` ∈ `motivo` \| `materia_prima` \| `produto_acabado` \| `centro_trabalho` \| `colaborador`.

Cada item: `{ code, label, quantity, value, sharePct, occurrenceCount }`.

---

## `/refugos/registros`

Listagem paginada alinhada à tela de acompanhamento (data, OP, PA, MP, descrição, motivo, qtd, UM, valor, CT, colaborador).

---

## Exemplo

```bash
curl -sS -H "Authorization: Bearer $TOKEN" \
  "$API/refugos/resumo?filial=01&dataInicio=2026-04-01&dataFim=2026-04-27"

curl -sS -H "Authorization: Bearer $TOKEN" \
  "$API/refugos/rankings?filial=01&dimension=motivo&dataInicio=2026-04-01&dataFim=2026-04-27"
```
