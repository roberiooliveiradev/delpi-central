# Regras de cálculo — Transformômetro

Documento oficial alinhado ao [playbook de correções](playbook_correcoes.md). O cache `transformometro.dashboard_calculos` deve refletir as mesmas regras do cálculo em tempo real (`DashboardCalculatorService` / `DashboardLiveService`).

## Economia líquida (mensal)

```text
economia_liquida_mes =
  economia_bruta
  - investimento_unico_mes
  - custo_recorrente_mes
  - custo_recursos_compartilhados_mes
```

```text
investimento_total_mes =
  investimento_unico_mes + custo_recorrente_mes + custo_recursos_compartilhados_mes
```

## ROI acumulado (recorte do dashboard)

```text
ROI acumulado = economia_liquida_total / investimento_total
```

A chave da API permanece `roi_medio` por compatibilidade com o frontend. Não descontar investimento duas vezes: a economia líquida já inclui todos os custos.

## Economia diária (ranking “Top economia diária”)

```text
economia_diaria = economia_bruta_acumulada_no_recorte / (30 × número_de_competências)
```

O ranking ordena por `economia_diaria` (capacidade de economia bruta), não por líquida.

## Payback (meses)

```text
payback_meses = investimento_unico_acumulado / economia_operacional_mensal
```

Onde `economia_operacional_mensal = economia_bruta - custo_recorrente_mes - custo_recursos_compartilhados_mes` (sem descontar o investimento único no denominador).

## Recursos compartilhados — `base_competencia`

| Valor | Comportamento |
|-------|----------------|
| `mensal_cheio` | Valor mensal integral na competência, se recurso e vínculo vigentes |
| `proporcional_dias` | `valor_mensal × (dias efetivos / dias do mês)` considerando `data_inicio_uso`, `data_fim_uso`, vigências do recurso |

## Filtros de data no dashboard

Os cards de resumo (`/dashboard/resumo`) somam **competências mensais inteiras** incluídas no recorte `competencia_inicio` … `competencia_fim`. Não há fator global de prorrata nos totais dos cards.

A proporcionalidade por dias dentro do mês aplica-se apenas a recursos com `base_competencia = proporcional_dias` (e às horas economizadas conforme vigência da revisão).

## Exportação CSV/Excel

As exportações usam as mesmas linhas do cálculo em tempo real (`DashboardLiveService.query_export_rows`) e incluem uma linha **TOTAIS DO RECORTE** com os mesmos agregados de `/dashboard/resumo`, incluindo ROI acumulado na coluna competência.

## Alertas

Alertas de economia líquida negativa usam `economia_liquida_mes` já calculada com a regra oficial (via `DashboardLiveService.query_process_monthly_liquida`).

## Comparativo de revisões

`ProcessRevisionCompareService` agrega por revisão: economia bruta, líquida, investimento único, recorrente, recursos compartilhados e investimento total.

## Cache `dashboard_calculos`

Leituras SQL legadas no `DashboardCalculoRepository` expõem `investimento_total` e `custo_recursos_compartilhados_total` com as mesmas fórmulas. Após mudança de regra, executar recálculo completo do cache.

## Histórico de revisões

A série mensal considera revisões comparáveis **pela vigência no mês**, não apenas `revisao_ativa = true` no cadastro atual.

## Recálculo do cache

Após alterar regras ou dados:

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner up
docker exec -i delpi-transformometro-api sh -lc 'python - <<PY
from tm_app.application.services.dashboard_recalc_service import DashboardRecalcService
print(DashboardRecalcService().recalculate())
PY'
```

Validação SQL: ver seção 4 do [playbook_correcoes.md](playbook_correcoes.md).
