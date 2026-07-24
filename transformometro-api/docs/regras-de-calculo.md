# Regras de cálculo — Transformômetro

Documento oficial alinhado ao [playbook de correções](playbook_correcoes.md). A implementação canônica está em **`tm_app/domain/calc_rules.py`**; `DashboardCalculatorService` e `DashboardLiveService` apenas delegam. O cache `transformometro.dashboard_calculos` deve refletir as mesmas regras do cálculo em tempo real.

## Instância = ambiente isolado; processo = soma das instâncias

**Conceito (jul/2026).** Cada **instância** de um processo é um ambiente independente: tem **baseline próprio**, **parâmetros de medição próprios** (medições/investimentos/recursos da própria timeline) e **setores próprios**. Isso cobre casos reais em que o mesmo processo:

- começou em datas diferentes em cada unidade;
- tem parâmetros de cálculo diferentes entre unidades;
- não atinge os mesmos setores.

O cálculo mensal itera **por instância**. Para **cada revisão comparável**, a referência de comparação é resolvida por `_pick_reference_review`:

1. Se `revisao_referencia_id` estiver preenchido → usa essa revisão (mesma instância).
2. Se NULL (legado) → fallback `_pick_baseline_review` (baseline mais antiga da instância).

```text
economia(revisão R, mês) = custo(referência de R) − custo(R)   [componentes ≥ 0]
economia(instância, mês)   = Σ revisões comparáveis válidas no mês
economia(processo, mês)  = Σ instâncias ativas
```

## Categorias de cálculo de benefício (Playbook 22)

Campo na revisão: `beneficio_calculo_categoria` (default **`automatico`** — novos cadastros e backfill V041 a partir de `economia_tempo` legado).

| Código | Interpretação |
|---|---|
| `automatico` | Não classificado; avisos/breakdown destacam o que os dados mostram. Totais = regras fixas abaixo. |
| `economia_tempo` | Foco em Δtempo/custo; orientação de cadastro: volumes iguais à referência (1:1). O motor **não** força 1:1. |
| `reducao_volume` | Benefício principal = menos execuções (volumes reais). |
| `ganho_capacidade` | `vol_rev > vol_ref` → capacidade valorizada e **incluída** na economia bruta / ROI. |
| `economia_qualidade` | Ênfase em retrabalho/erro (já entram na bruta). |
| `misto` | Declaração explícita de mais de um tipo; totais financeiros iguais às regras fixas. |

```text
economia_custo = Σ componentes (tempo, retrabalho, erro, outros, recursos)
ganho_capacidade = max(0, Δvolume) × (tempo_ref / 60) × custo_hora_ref
                   × fração_mês_útil
economia_bruta = economia_custo + ganho_capacidade   [entra no ROI]
economia_liquida = economia_bruta − investimento_total_mês
economia_reducao_volume = max(0, −Δvolume) × (tempo_ref / 60) × custo_hora_ref
                          [sinal analítico; sem double-count — já está em economia_custo]
```

Persistência em `dashboard_calculos`: colunas `beneficio_calculo_categoria`, `ganho_capacidade`, `economia_reducao_volume`, `delta_volume`. Recalcular cache após deploy da migration (não na migration).

- **Instância ativa no mês**: tem pelo menos uma revisão comparável válida naquela competência. Se a unidade B começou depois, só entra nos meses em que está ativa.
- **Investimento** e **horas** seguem a mesma soma por instância.
- **ROI** consolidado = `Σ economia_líquida / Σ investimento` do recorte.
- **Processo com 1 instância**: soma de 1 = ele mesmo (retrocompatível).
- **Filtro por unidade/departamento**: mostra o valor **real da(s) instância(s)** no recorte (sem multiplicador multi-unidade).

**Implementação (row-level).** Cada linha `(revisão, competência)` carrega `instancias_ativas_mes` como **metadado** (nº de instâncias ativas no mês). A agregação (`calc_rules.prorate_dashboard_row_for_period` / `aggregate_period_from_rows`) **soma** as linhas sem dividir por esse fator.

## Instância multi-unidade (`todas_filiais_ativas`)

**Conceito (jul/2026).** Uma instância com `todas_filiais_ativas = true` representa **um único ambiente operacional** replicado em todas as filiais ativas (timeline, baseline e medições compartilhadas). Substitui duplicatas cadastrais `(processo × filial)` quando os parâmetros são idênticos.

```text
multiplicador = escopo_unidades   se todas_filiais_ativas
              = 1                 caso contrário (instância por filial ou recorte filial/departamento)

economia_instância_escalada(mês) =
  economia_bruta_revisão × multiplicador
  (idem horas_economizadas_mes; economia_liquida_mes após custos da própria linha)
```

| Métrica | Escala com multiplicador? |
|---------|---------------------------|
| `economia_bruta`, `economia_liquida_mes`, `horas_economizadas_mes` | Sim, **por instância** antes da soma entre instâncias do processo |
| Investimento único / recorrente da revisão | Não (permanece o valor cadastrado na timeline) |
| Recursos compartilhados | Não — rateio continua via `escopo_recurso` / pool global |

- **Visão consolidada:** `escopo_unidades` = nº de filiais ativas no recorte analítico (ex.: 2 unidades → economia da instância multi-unidade conta **2×**).
- **Visão filial ou departamento:** multiplicador **1** (uma unidade no recorte).
- **Processo com várias instâncias:** após escalar cada instância, aplica-se a **soma** entre instâncias ativas no mês.

**Implementação:** `DashboardCalculatorService._instance_unit_multiplier`, `_scale_instance_economy_row`; parâmetro `escopo_unidades` em `build_dashboard_rows` / `build_summary`. `DashboardViewScopeService.resolve_escopo_unidades` + `count_active_filiais` propagam o valor em `DashboardLiveService`, `DashboardRecalcService` e Transforma+ (consolidado).

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

Exibido como **razão** (ex.: `4,1×`), sem multiplicar por 100. A chave da API permanece `roi_medio` por compatibilidade. Não descontar investimento duas vezes: a economia líquida já inclui todos os custos.

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

**Fração de vigência** (`calc_rules.review_vigencia_fraction_in_month`): só reduz quando a revisão **começa ou termina** naquele mês (incluindo o teto de validade de 1 ano). Revisão ativa sem data fim nem aniversário no mês usa o **mês civil inteiro** — não `hoje`.

## Validade da revisão (1 ano)

Implementação: `calc_rules.review_validity_end_date` / `review_effective_end_date`; constante `REVIEW_VALIDITY_MONTHS = 12`.

- A economia de uma revisão comparável (`melhoria`, `automacao`, `correcao`) é contabilizada por **12 meses** a partir do início do cálculo (`review_calculation_start_date` = `max(data_implantacao, data_inicio_vigencia)`).
- **Aniversário** = `início + 12 meses` (exclusivo). A partir dele a revisão **deixa de contar** (`fração_vigência = 0`), mesmo sem `data_fim_vigencia`.
- **Fim efetivo** = `min(data_fim_vigencia, aniversário − 1 dia)` — aplicado em `review_vigencia_fraction_in_month` e em `_is_review_valid_for_month`.
- **Supersessão**: uma **nova revisão implantada** (`revisao_ativa = true`) assume o cálculo pela seleção `revisao_ativa` (mesma lógica de sempre) e tem **seu próprio ciclo de 12 meses**. Se a revisão vigente vence sem sucessora, o processo passa a contribuir com **0** naquele ambiente.
- Baseline **não** tem validade (não é contabilizado na economia).

### Acompanhamento de vencimento (90 dias)

`DashboardCalculatorService._build_review_vencimento` enriquece cada item da lista de instâncias com:

| Campo | Significado |
|---|---|
| `data_vencimento` | Aniversário da revisão que gera economia hoje (dd/mm/aaaa) |
| `dias_para_vencer` | Dias até o aniversário (negativo se já venceu) |
| `status_vigencia` | `vigente` · `vencendo` (≤ 90 dias, `REVIEW_EXPIRY_ALERT_DAYS`) · `vencida` |

Exposto em `GET /dashboard/vencimentos?dias=90` (`DashboardLiveService.list_vencimentos`), consumido pelo painel **“Revisões a vencer”** no dashboard do MFE.

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

## Recursos compartilhados — `escopo_recurso`

Implementação: `SharedResourceScopeService.filter_rateio_pool` · consumido por `DashboardCalculatorService`.

Define **quais vínculos revisão↔recurso** entram no denominador do rateio antes de aplicar `criterio_rateio` (`igualitario`, `por_revisoes_ativas`, `por_peso`).

| Valor | Pool de vínculos elegíveis |
|-------|----------------------------|
| `empresa` (padrão legado) | Todos os vínculos vigentes da empresa |
| `filial` | Vínculos cuja instância operacional tem a **mesma filial** da revisão âncora |
| `setor` | Vínculos cuja instância tem o **mesmo par filial × setor** da revisão âncora |

A **âncora** é a instância da revisão que recebe o custo rateado (`revisoes.instancia_id` → `processo_instancias`). Recursos sem `escopo_recurso` no JSON importado assumem `empresa` (sem mudança numérica imediata).

### Visões do dashboard e escopo

O parâmetro `view` (`consolidated` \| `filial` \| `department`) filtra **quais instâncias/revisões** entram nos KPIs. Recursos `empresa` continuam rateando no pool global; em visão filial ou departamento a **fatia exibida** é a parcela rateada para as revisões do recorte — nunca o custo integral do recurso.

Módulos: `DashboardViewScopeService` (filtro analítico) + `SharedResourceScopeService` (pool de rateio).

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

## Fonte única (motor live) + cache de consulta

**A fonte de verdade do dashboard é o motor live** (`DashboardLiveService` sobre `calc_rules`), não a planilha materializada. Isso vale para a UI, o snapshot/chat e o Transforma+ S2S. Vantagens: um único caminho de cálculo (sem divergência live × cache) e **faixas de tempo por dia** (prorrata `YYYY-MM-DD`) em todas as leituras.

### `DashboardQueryCache` (TTL + invalidação por geração)

Para não recomputar a cada polling sobre a **conexão Postgres única compartilhada**, os resultados são cacheados por uma janela curta:

- `tm_app/application/services/dashboard_query_cache.py` — singleton de processo, thread-safe.
- Cacheia `load_raw()` (as 8 queries de cadastro) e os resultados das leituras (`build_summary`, `calculation_rows`, ranking, família, `processo_competencia_rows`, export, lista de instâncias).
- **Invalidação por geração:** qualquer mutação de CRUD chama `dashboard_query_cache.invalidate()` — **O(1), em memória, sem recálculo pesado** no caminho de escrita. A próxima leitura recomputa preguiçosamente. Se um CRUD ocorre no meio de uma leitura, o valor obsoleto não é cacheado (checa geração antes de gravar).

| Flag | Default | Efeito |
|------|---------|--------|
| `TM_DASHBOARD_QUERY_CACHE` | `true` | Liga/desliga o cache de consulta |
| `TM_DASHBOARD_QUERY_CACHE_TTL_SECONDS` | `120` | Janela do TTL |
| `TM_DASHBOARD_PERSIST_CACHE` | `false` | Mantém a tabela materializada legada `dashboard_calculos` no hook de CRUD |

### Hook de CRUD (`DashboardRecalcHookService`)

Toda mutação **apenas invalida** o query cache (O(1)). O recálculo pesado da tabela `dashboard_calculos` só roda quando `TM_DASHBOARD_AUTO_RECALC=true` **e** `TM_DASHBOARD_PERSIST_CACHE=true` (leitura legada opt-in). Por padrão, o recálculo pesado no CRUD deixa de existir.

### Cache materializado `dashboard_calculos` (legado, opt-in)

A tabela e as views V017–V021 permanecem para quem liga `TM_DASHBOARD_PERSIST_CACHE`. Quando populada, o snapshot lê dela como **fast-path**; caso contrário, o snapshot computa do motor live (mesmo contrato de campos). Leituras SQL no `DashboardCalculoRepository` expõem `investimento_total` e `custo_recursos_compartilhados_total` com as mesmas fórmulas. Após mudança de regra, executar recálculo completo do cache.

### Soma por instância no cache (agregação em 2 níveis)

O cache materializa **uma linha por revisão × competência** (com `instancia_id`). As leituras usam `DashboardCalculoRepository._instance_average_cte` e as views V022 fazem **duas agregações**:

1. `inst_lvl` — **soma** as revisões dentro de cada instância (grão instância × competência).
2. `proc_lvl` — **soma** entre as instâncias ativas (`SUM`, grão processo × competência).

O consolidado então **soma** os processos por competência. O filtro de escopo (filial/setor) entra **no grão de linha** antes da agregação.

Cobre: `query_resumo`, `query_evolucao`, `query_ranking_processos`, `query_process_monthly_liquida`, `query_resumo_por_familia` e as views `processo_competencia_snapshot` / `dashboard_competencia_evolucao` (V021). Linhas de detalhe (`query_linhas`, `query_export_rows`) permanecem no grão de revisão (valor real por revisão); os TOTAIS do recorte vêm de `query_resumo` (já mediado).

> `dashboard_competencia_evolucao` é **consolidada por empresa** (colunas de filial/setor nulas). Recortes por unidade/setor da evolução vêm de `query_evolucao` (filtro no grão de linha), não da view.

### Persistência legada da tabela (CRUD)

Só quando `TM_DASHBOARD_AUTO_RECALC=true` **e** `TM_DASHBOARD_PERSIST_CACHE=true`, o hook também atualiza `dashboard_calculos`:

| Escopo | Gatilho |
|--------|---------|
| `processo_id` | processo, revisão (com processo), medição, investimento |
| `revisao_id` | exclusão de revisão sem escopo de processo |
| recálculo **full** | recurso compartilhado, custo de recurso, vínculo revisão↔recurso (rateio global) |

Sem `TM_DASHBOARD_PERSIST_CACHE`, o hook só invalida o query cache — a tabela não é mantida.

### Leitura para chat / integrações

Endpoints de leitura analítica — **fonte única = motor live** (com query cache); usam a tabela materializada só como fast-path quando `TM_DASHBOARD_PERSIST_CACHE` está populado:

| Rota | Conteúdo |
|------|----------|
| `GET /dashboard/snapshot/meta` | modo (`live`/`persisted`) e freshness |
| `GET /dashboard/snapshot/resumo` | agregados (chaves do `query_resumo`) |
| `GET /dashboard/snapshot/processos` | processo × competência (média por instância) |
| `GET /dashboard/snapshot/linhas` | linhas revisão × competência |
| `GET /dashboard/snapshot/instancias` | instâncias operacionais (economia diária, payback) |

O dashboard interativo (`GET /dashboard/resumo`, etc.) e o Transforma+ S2S também usam `DashboardLiveService` — todos aceitam faixa de tempo por dia.

### KPI «Soluções implementadas»

Conta **melhorias** (`processo_instancias`) distintas que possuem revisão comparável **ativa** (`revisao_ativa = true`, cenário `melhoria` | `automacao` | `correcao`). É um snapshot do cadastro no recorte de visão (consolidado / unidade / departamento), **não** filtrado pela competência nem pelo volume de economia no período.

Implementação: `calc_rules.count_active_implemented_improvements` (live) e `DashboardDataRepository.count_active_implemented_improvements` (cache).

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
