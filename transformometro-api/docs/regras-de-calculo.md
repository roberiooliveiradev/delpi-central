# Regras de cálculo — Transformômetro

Documento oficial alinhado ao [playbook de correções](playbook_correcoes.md). A implementação canônica está em **`tm_app/domain/calc_rules.py`**; `DashboardCalculatorService` e `DashboardLiveService` apenas delegam. O cache `transformometro.dashboard_calculos` deve refletir as mesmas regras do cálculo em tempo real.

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

## Dias do mês (corridos)

Os cálculos que prorrateiam por tempo usam **todos os dias do mês civil** (28–31 conforme o mês), não mês fixo de 30 dias:

- Filtro `YYYY-MM-DD` no dashboard: `dias_no_recorte / dias_do_mês` por competência.
- Vigência de revisão e recursos `proporcional_dias`: fração de dias corridos ativos no mês.
- Gráfico diário (front): distribui valores entre os dias corridos incluídos no filtro.

Modo **apenas dias úteis** (seg–sex + feriados nacionais) existe no código (`USE_ONLY_BUSINESS_DAYS`) mas está **desativado**.

## Horas economizadas (mensal por revisão)

Implementação: `calc_rules.hours_saved_in_competencia_month` / `total_minutes_saved_month`.

```text
minutos_baseline = volume_baseline × tempo_medio_execucao_min_baseline
minutos_melhoria = volume_melhoria × tempo_medio_execucao_min_melhoria
horas_economizadas_mes = max(0, minutos_baseline − minutos_melhoria) × fração_vigência / 60
```

Cada revisão usa **seu próprio** `volume_mensal` (mesma lógica da `economia_tempo` em R$). Com volumes iguais, equivale a `(Δtempo × volume) / 60`.

**Fração de vigência** (`calc_rules.review_vigencia_fraction_in_month`): só reduz quando a revisão **começa ou termina** naquele mês. Revisão ativa sem data fim usa o **mês civil inteiro** — não `hoje`.

## Recorte do dashboard (prorrata)

Implementação: `calc_rules.prorate_dashboard_row_for_period` + `aggregate_period_from_rows`.

```text
métrica_no_recorte = métrica_mensal × (dias_do_filtro_no_mês / dias_do_mês)
investimento_unico_mes = integral na competência (sem prorrata por dia)
```

## Economia diária (ranking “Top economia diária”)

Implementação: `calc_rules.daily_averages_from_period_totals`.

```text
economia_diaria = economia_bruta_acumulada_no_recorte / dias_totais_do_recorte
horas_diaria = horas_acumuladas_no_recorte / dias_totais_do_recorte
```

O denominador soma os dias de cada competência no recorte (ou só os dias intersectados quando o filtro tem dia explícito).

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

Com filtro em formato **YYYY-MM-DD** (data inicial e final com dia), os cards de resumo, a evolução mensal retornada pela API e o ranking por família recalculam **linha a linha**:

- **Economia bruta**, custos recorrentes, recursos compartilhados e horas: `dias_no_filtro / dias_do_mês` na competência.
- **Investimento único**: valor integral da competência quando o mês intersecta o filtro (não divide o capex pelos dias).

O **ROI acumulado** do card é sempre `economia_liquida_total / investimento_total` do recorte (não média simples por revisão).

Exemplo: `2026-06-01` … `2026-06-03` aplica 3/30 da economia operacional em junho/2026, mas mantém o investimento único cheio de junho se houver sobreposição — o ROI passa a refletir o recorte parcial.

Com filtro só por competência mensal (`YYYY-MM`) ou sem dia explícito, permanecem os totais mensais cheios de cada competência no intervalo.

A proporcionalidade por vigência de recurso (`base_competencia = proporcional_dias`) é independente e continua no cálculo linha a linha do cadastro.

## Exportação CSV/Excel

As exportações usam as mesmas linhas do cálculo em tempo real (`DashboardLiveService.query_export_rows`) e incluem uma linha **TOTAIS DO RECORTE** com os mesmos agregados de `/dashboard/resumo`, incluindo ROI acumulado na coluna competência.

## Alertas

Alertas de economia líquida negativa usam `economia_liquida_mes` já calculada com a regra oficial (via `DashboardLiveService.query_process_monthly_liquida`).

## Comparativo de revisões

`ProcessRevisionCompareService` agrega por revisão: economia bruta, líquida, investimento único, recorrente, recursos compartilhados e investimento total.

## Cache `dashboard_calculos`

Leituras SQL legadas no `DashboardCalculoRepository` expõem `investimento_total` e `custo_recursos_compartilhados_total` com as mesmas fórmulas. Após mudança de regra, executar recálculo completo do cache.

### Recálculo automático (CRUD)

Com `TM_DASHBOARD_AUTO_RECALC=true` (padrão), mutações CRUD disparam `DashboardRecalcHookService`:

| Escopo | Gatilho |
|--------|---------|
| `processo_id` | processo, revisão (com processo), medição, investimento |
| `revisao_id` | exclusão de revisão sem escopo de processo |
| recálculo **full** | recurso compartilhado, custo de recurso, vínculo revisão↔recurso (rateio global) |

Desabilitar: `TM_DASHBOARD_AUTO_RECALC=false`.

### Leitura para chat / integrações

Endpoints sobre o cache materializado (não recalculam):

| Rota | Conteúdo |
|------|----------|
| `GET /dashboard/snapshot/meta` | contagem e `latest_calculated_at` |
| `GET /dashboard/snapshot/resumo` | agregados do cache |
| `GET /dashboard/snapshot/processos` | view `processo_competencia_snapshot` |
| `GET /dashboard/snapshot/linhas` | linhas `dashboard_calculos` (revisão × competência) |

O dashboard interativo (`GET /dashboard/resumo`, etc.) continua em tempo real via `DashboardLiveService`.

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
