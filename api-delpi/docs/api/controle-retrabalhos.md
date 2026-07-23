# Controle de Retrabalhos — `/retrabalhos`

Consultas de **horas improdutivas de retrabalho** (motivo TOTVS `RT`), alimentadas pela view **`dbo.VW_BI_RT_HORAS_IMPRODUTIVAS`**.

**Permissão:** `controle-retrabalhos.access`, `controle-retrabalhos.view`, `controle-retrabalhos.view.filial-sc`, `controle-retrabalhos.view.filial-es` ou `api-delpi.access`

**Validação por filial:** usuários com permissão apenas de uma filial recebem `403` ao consultar a outra (exceto superadmin ou `controle-retrabalhos.view`).

**Formato:** envelope `{ success, message, data, meta }` (Playbook 10).

Plugin consumidor: `plugins/controle-retrabalhos` · View: [ESPECIFICACAO-VIEW.md](../../../docs/12-roadmap-e-evolucao/controle-retrabalhos/ESPECIFICACAO-VIEW.md).

---

## Endpoints

| Método | Rota | `meta.shape` | `meta.operationId` |
|---|---|---|---|
| GET | `/retrabalhos/health` | `scalar` | `get_retrabalhos_health` |
| GET | `/retrabalhos/filtros` | `scalar` | `get_retrabalhos_filtros` |
| GET | `/retrabalhos/resumo` | `scalar` | `get_retrabalhos_resumo` |
| GET | `/retrabalhos/custo-x-rol` | `scalar` | `get_retrabalhos_custo_x_rol` |
| GET | `/retrabalhos/mensal` | `list` | `get_retrabalhos_mensal` |
| GET | `/retrabalhos/recursos` | `list` | `get_retrabalhos_recursos` |
| GET | `/retrabalhos/colaboradores` | `list` | `get_retrabalhos_colaboradores` |
| GET | `/retrabalhos/detalhes` | `paged_list` | `get_retrabalhos_detalhes` |

---

## Parâmetros comuns

| Parâmetro | Alias | Descrição |
|---|---|---|
| `filial` | — | Filial Protheus `01` (SC) ou `02` (ES) — **obrigatório** (exceto `/health`) |
| `data_inicio` | `dataInicio` | Data inicial `YYYY-MM-DD` (default: 12 meses atrás) |
| `data_fim` | `dataFim` | Data final `YYYY-MM-DD` (default: hoje) |
| `recurso` | — | Filtro opcional por recurso |
| `centro_custo` | `centroCusto` | Filtro opcional por centro de custo |
| `codigo_operador` | `codigoOperador` | Filtro opcional por operador |

Janela máxima: **24 meses**. Ranking default: top **10** (`limit` até 50). Detalhes: `page`, `pageSize` (máx. 100).

---

## GET `/retrabalhos/custo-x-rol`

**`meta.entity`:** `retrabalho_custo_x_rol`

Combina o custo de retrabalho do período (`/retrabalhos/resumo` → `totalCusto`) com o ROL financeiro da mesma filial/período (`/financial/rol` → `rol_with_ipi`).

| Campo | Descrição |
|---|---|
| `custoRetrabalho` | Custo de retrabalho (R$) no período |
| `rol` / `rolWithIpi` | ROL financeiro do denominador |
| `custoSobreRolPct` | `(custoRetrabalho / rolWithIpi) * 100` — `null` se ROL = 0 |
| `totalHoras` / `custoMedioHora` | Horas e custo médio/hora do numerador |
| `filtrosAplicados` | `recurso`, `centroCusto`, `codigoOperador` (afetam só o numerador) |
| `financialContext` | Contexto do ROL (receita bruta, devoluções, etc.) |

Parâmetros: mesmos de `/retrabalhos/resumo` (`filial` obrigatória; período e filtros opcionais).

---

## GET `/retrabalhos/resumo`

**`meta.entity`:** `retrabalho_horas_improdutivas_resumo`

**Campos principais `data`:**

| Campo | Descrição |
|---|---|
| `periodo` | `{ dataInicio, dataFim, filial }` |
| `totalApontamentos` | Quantidade de apontamentos RT |
| `totalHoras` | Horas improdutivas |
| `totalCusto` | Custo de parada (R$) |
| `custoMedioHora` | Custo médio por hora |
| `registrosSemCusto` / `horasSemCusto` | Registros com `FONTE_CUSTO = SEM CUSTO` |
| `principalRecursoPorHoras` | Top recurso no período |
| `principalColaboradorPorHoras` | Top colaborador no período |

---

## GET `/retrabalhos/mensal`

**`meta.entity`:** `retrabalho_horas_improdutivas_mensal`

**`data.items[]`:** série por mês (`anoMes`, `totalHoras`, `totalCusto`, …).

---

## GET `/retrabalhos/detalhes`

**`meta.entity`:** `retrabalho_horas_improdutivas_detalhe`

**Query adicional:** `page`, `pageSize`, `orderBy` (`data`|`horas`|`custo`), `orderDir` (`asc`|`desc`).

**`data`:** `items[]`, `page`, `pageSize`, `total`, `totalPages`.

---

## Performance

- Leitura analítica com `WITH (NOLOCK)` na view BI.
- Sem cache de resposta no v1 — dashboard dispara 5 requests paralelos no load inicial.
- Console Saúde SQL: `operation_id` estável (`get_retrabalhos_*`).

---

## Exemplos curl

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: controle-retrabalhos" \
     "http://localhost/apps/api-delpi/retrabalhos/resumo?filial=01" \
  | jq '.meta, .data.totalHoras'

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: controle-retrabalhos" \
     "http://localhost/apps/api-delpi/retrabalhos/detalhes?filial=01&page=1&pageSize=25" \
  | jq '.meta.shape, .data.total'
```

Validação Fase 0 da view:

```bash
docker exec delpi-api-delpi python scripts/validate_retrabalho_horas_improdutivas_view.py
```
