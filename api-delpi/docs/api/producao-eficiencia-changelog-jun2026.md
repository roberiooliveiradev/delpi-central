# Produção — eficiência, OEE e dashboards (jun/2026+)

Registro das mudanças alinhadas entre **api-delpi**, **dashboard-production**, **eficiencia-fabril** e **strategic-indicators**.

Documentação de faixa válida: [regras-faixa-eficiencia-producao.md](./regras-faixa-eficiencia-producao.md).  
Fórmula canônica (`HY_TEMPAD`): [padroes-totvs/apontamentos-tempo-padrao.md](./padroes-totvs/apontamentos-tempo-padrao.md).

> **Estado atual (ago/2026):** KPI OEE, listagem OEE, série OEE e eficiência fabril usam o **mesmo** % recalculado (`setup + HY_TEMPAD × qtd`). A tabela da §1 abaixo descreve o estado de **jun/2026** (ainda lia o % da view no KPI) — ver **§7.2** para o alinhamento.

---

## 1. Eficiência por tempos (fim do `H6_ZEFICI`)

A partir de jun/2026 a plataforma **não usa mais** o campo Protheus `H6_ZEFICI` para medir eficiência.

| Superfície | Fonte da métrica (jun/2026) | Fonte atual (ago/2026) |
|------------|-----------------------------|-------------------------|
| KPI OEE, listagem OEE | `EFICIENCIA_PERCENTUAL` da view | % canônico TEMPAD (`production_fabril_efficiency_sql.py`) |
| Eficiência Fabril (appointments) | recalcula TEMPAD no SELECT | idem (módulo compartilhado) |
| Detalhe (`GET /production/oee/appointments/{id}`) | tempos em SH6010 | idem (`production_oee_sql.py`) |

### API (módulos canônicos)

| Arquivo | Mudança |
|---------|---------|
| `production_oee_sql.py` | `oee_pct` e `status` no detalhe SH6010 passam a usar `OEE_EFFICIENCY_FROM_TIMES_EXPR` |
| `production_appointment_time_analysis.py` | Findings unificados na métrica por tempos; removidos `efficiency_divergence`, duplicatas ZEFICI × tempos |
| `production_efficiency_valid_range.py` | Docstring alinhada à regra por tempos |

### Diagnóstico (`time_analysis.findings`)

Códigos removidos (não mais aplicáveis):

- `efficiency_times_out_of_range` (duplicata)
- `low_efficiency_from_times` (duplicata)
- `efficiency_divergence` (comparação ZEFICI × tempos)

`oee_out_of_range` e `low_efficiency_reported` permanecem, com mensagens referindo **eficiência calculada por tempos**.

---

## 2. Textos de cálculo legíveis no detalhe

Campos `formula_planned`, `formula_real` e `formula_efficiency` em `time_analysis` foram reescritos **sem códigos Protheus** (`H6_*`, `SHY010`, `SG2`).

| Campo API | Texto exibido ao usuário |
|-----------|--------------------------|
| `formula_planned` | Tempo de preparação (setup) + tempo padrão da operação × (quantidade apontada ÷ quantidade planejada da OP) |
| `formula_real` | Diferença entre horário de término e início do apontamento; se início/fim não estiverem informados, usa o tempo registrado no apontamento |
| `formula_efficiency` | Tempo previsto ÷ tempo real × 100 — acima de 100% indica produção mais rápida que o previsto |

Na UI (OEE e Eficiência Fabril):

- Rótulos: **Cálculo do tempo previsto / real / eficiência**
- `real_hours_source`: «Horário de início e término do apontamento» ou «Tempo informado no apontamento»
- Exportações Excel/PDF usam os mesmos rótulos

Fonte canônica: `app/domain/production/production_appointment_time_analysis.py`.

---

## 3. Auto-refresh nos dashboards (5 minutos)

Com a aba do navegador **visível**, os painéis principais recarregam dados automaticamente a cada **5 minutos** (`300_000 ms`).

| Plugin | Página | Hook | O que recarrega |
|--------|--------|------|-----------------|
| dashboard-production | `DashboardProductionPage` | `useAutoRefresh` | KPIs + séries OEE e OTD |
| eficiencia-fabril | `DashboardEficienciaFabrilPage` | `useAutoRefresh` | Bulk `/appointments` + agregação local |

Comportamento:

- Não dispara com aba em background (`document.visibilityState === hidden`)
- Botão **Atualizar** continua disponível para refresh manual imediato
- Constante: `DASHBOARD_AUTO_REFRESH_MS` em `src/hooks/useAutoRefresh.ts` de cada plugin

Páginas de **listagem** OEE/OTD e **detalhe** de apontamento **não** têm auto-refresh automático (apenas refresh manual).

---

## 7. Performance KPI OEE (`get_overall_equipment_effectiveness_pct`) — jun/2026

Alerta **Saúde SQL** (`slow_sql`): query com `FILIAL = ?` na view fabril levava **~14 s** (limiar 2,5 s); a variante consolidada `GROUP BY` filial rodava em **~1 s**.

### Causa

| Fator | Detalhe |
|-------|---------|
| Leitura sem `NOLOCK` | Bloqueio em dashboard / Indicadores Estratégicos |
| Plano ruim | `AVG` com filial explícita vs. agregação por filial |
| Repetição | `strategic-indicators-api` consulta filial 01 e 02 em sequência |

### Correção (api-delpi)

| Artefato | Mudança |
|----------|---------|
| `production_fabril_oee_kpi_sql.py` | SQL canônico KPI: `WITH (NOLOCK)`, `TRY_CAST(EF.EFICIENCIA_PERCENTUAL)` |
| `overall_equipment_effectiveness_repository.py` | KPI por filial reutiliza query **agrupada** (`GROUP BY` filial) e extrai a filial pedida |
| `production_kpi_cache.py` | Namespace `production-oee-by-branch` — 2ª filial no mesmo período não repete SQL |

### Cache (TTL `QUERY_CACHE_TTL_SECONDS`, default 300 s)

| Chave | Uso |
|-------|-----|
| `production-oee\|filial\|início\|fim` | Resposta KPI por filial |
| `production-oee-by-branch\|filial\|início\|fim` | Lista `{ branch, oee_pct }` (consolidada quando filial vazia) |

### Efeito esperado

- **1ª chamada** (cache frio): ~1 s em vez de ~14 s.
- **2ª filial** (mesmo período): hit em `production-oee-by-branch`.
- **Polling** (5 min): hits em `production-oee` e `production-oee-by-branch`.

### Testes

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_production_oee_kpi_sql.py tests/test_chart_query_cache.py -q
```

Console: `operation_id` = `get_overall_equipment_effectiveness_pct` — hash antigo `b884554ccf71c3d2` deve desaparecer ou cair para ~1 s no frio.

---

## 7.1 Performance série OEE (`get_production_oee_series`) — jul/2026

Alerta **Saúde SQL** (`slow_sql`): a série diária (`OverallEquipmentEffectivenessRepository._load_oee_kpi_by_day_and_branch`, `operation_id = get_production_oee_series`) atingiu **~4970 ms** (limiar 2500 ms).

### Causa

| Fator | Detalhe |
|-------|---------|
| Scans redundantes | Cada refresh do dashboard fazia **dois** scans pesados da mesma view fabril com os mesmos filtros: KPI por filial (`GROUP BY filial`) **e** série por dia (`GROUP BY dia+filial`). A série já contém todos os componentes do KPI. |
| Predicado não-sargável duplicado | `AND RTRIM(LTRIM(EF.FILIAL)) <> ''` no repository além do `<> ''` + `FILIAL IN ('01','02')` já emitidos por `build_fabril_view_filters`. |
| Custo residual | A view `vw_Apontamentos_Eficiencia` faz join de 6 tabelas Protheus (SH6010, SHY010, SC2010, SYS_USR, SH1010, SBZ010); o join domina o custo do scan a frio. |

### Correção (api-delpi)

| Artefato | Mudança |
|----------|---------|
| `production_fabril_oee_kpi_sql.py` | `OEE_FABRIL_KPI_BY_DAY_AND_BRANCH_SELECT` passa a expor componentes brutos `efficiency_sum` (`SUM`) e `efficiency_sample_count` (`COUNT` de não-nulos) |
| `production_oee_series_aggregation_service.py` | `resolve_period_oee_by_branch` deriva o OEE do período por filial das linhas diárias (`Σsum / Σcount`, arredondado uma única vez) — equivalente a `ROUND(AVG(efficiency_pct), 2)` sobre o % da agregação diária |
| `overall_equipment_effectiveness_repository.py` | `_load_overall_equipment_effectiveness_by_branch` deriva da série diária (`list_oee_kpi_by_day_and_branch`, cacheada) — **elimina** o scan separado `OEE_FABRIL_KPI_BY_BRANCH_SELECT`; removido o predicado `FILIAL <> ''` redundante da série diária |

### Efeito esperado

- KPI OEE por filial + série passam a compartilhar **um único** scan da view (cache `production-oee-series-daily`), reduzindo a repetição de `slow_sql`.
- Resultados **idênticos** (derivação matematicamente equivalente ao `AVG`).

### Recomendação DBA (custo residual a frio)

O tempo restante a frio (~1–2 s) é do join da view. Para reduzir abaixo do limiar de forma durável, avaliar no SQL Server:

- Índice nas tabelas-base cobrindo **filial + data** de produção (SH6010: `H6_FILIAL`, `H6_DTPROD`), alinhado aos filtros da view.
- Alternativa: view indexada / tabela materializada de apontamentos de eficiência para leitura analítica.

### Testes

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_production_oee_kpi_sql.py tests/test_chart_query_cache.py \
  tests/test_production_oee_appointments_repository.py \
  tests/test_get_production_oee_series_use_case.py tests/test_get_production_oee_use_case.py \
  tests/unit/domain/services/test_production_oee_series_aggregation_service.py -q
```

---

## 7.2 Alinhamento OEE / SI / eficiência fabril (`HY_TEMPAD`) — ago/2026

**Sintoma:** no mesmo período (ex.: jul/2026, filial SC/`01`), dashboard Produção e Indicadores Estratégicos mostravam OEE **88,31%** enquanto Eficiência Fabril mostrava **~89,5%**.

**Causa raiz:** KPI OEE/SI ainda fazia `AVG(EF.EFICIENCIA_PERCENTUAL)` cru da view (previsto legado `HY_TEMPOM × qtd/C2`). A eficiência fabril já recalculava com `HY_TEMPAD × qtd` no SELECT de appointments.

### Correção (api-delpi)

| Artefato | Mudança |
|----------|---------|
| `production_fabril_efficiency_sql.py` | Expressões canônicas únicas (meta/hora, previsto, %, ganho/perda) |
| `production_fabril_standard_time_sql.py` | CTEs/joins SHY+SG2 compartilhados (OEE + EF) |
| `production_fabril_oee_kpi_sql.py` | `build_oee_fabril_kpi_*` — AVG do % recalculado na faixa 0–199 |
| `production_fabril_oee_sql.py` | Listagem OEE usa o mesmo `%` + `status` sobre ele |
| `production_fabril_ef_items_sql.py` | Consome as expressões compartilhadas (sem duplicar fórmula) |
| `overall_equipment_effectiveness_repository.py` | KPI/série/listagem via builders; faixa no % recalculado (não no da view) |
| `production_kpi_cache.py` | Namespaces `*-tempad-v2` (evita servir cache legado) |

### Contrato HTTP

Rotas e `operationId` **inalterados**. Consumidores (dashboard-production, strategic-indicators via `get_oee_pct`, chat) passam a receber o valor alinhado à eficiência fabril sem mudança de path.

### Testes

```bash
cd api-delpi
.venv/bin/python -m pytest \
  tests/test_production_oee_kpi_sql.py \
  tests/test_production_fabril_canonical_efficiency_sql.py \
  tests/test_production_fabril_appointment_filters.py \
  tests/test_ef_fabril_items_list_sql.py \
  tests/test_production_oee_appointments_batch_sql.py -q
```

Doc canônica da fórmula: [padroes-totvs/apontamentos-tempo-padrao.md](./padroes-totvs/apontamentos-tempo-padrao.md).

---

## 8. Deploy após as mudanças

```bash
cd infra
docker compose -f docker-compose.dev.yml --env-file .env up --build -d --force-recreate \
  api-delpi dashboard-production eficiencia-fabril gateway
```

Só backend (fórmulas / findings):

```bash
docker compose -f docker-compose.dev.yml restart api-delpi
```

Hard refresh no navegador (`Ctrl+Shift+R`) após rebuild dos MFEs.

---

## 9. Testes de regressão

```bash
cd api-delpi
.venv/bin/pytest tests/test_production_appointment_time_analysis.py \
  tests/test_production_efficiency_valid_range.py \
  tests/test_production_oee_kpi_sql.py tests/test_chart_query_cache.py -q
```

Build dos plugins:

```bash
cd plugins/dashboard-production && npm run build
cd plugins/eficiencia-fabril && npm run build
```

---

## 10. Documentação relacionada

- [06-modulos-departamentais.md](./06-modulos-departamentais.md) — rotas `/production/*`
- [plugins/dashboard-production/README.md](../../../plugins/dashboard-production/README.md)
- [plugins/eficiencia-fabril/README.md](../../../plugins/eficiencia-fabril/README.md)
- `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md` — contrato para agentes
