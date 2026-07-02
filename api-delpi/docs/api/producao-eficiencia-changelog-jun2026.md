# Produção — eficiência, OEE e dashboards (jun/2026)

Registro das mudanças alinhadas entre **api-delpi**, **dashboard-production** e **eficiencia-fabril**.

Documentação de faixa válida: [regras-faixa-eficiencia-producao.md](./regras-faixa-eficiencia-producao.md).

---

## 1. Eficiência por tempos (fim do `H6_ZEFICI`)

A partir de jun/2026 a plataforma **não usa mais** o campo Protheus `H6_ZEFICI` para medir eficiência.

| Superfície | Fonte da métrica |
|------------|------------------|
| KPI OEE, listagem OEE, Eficiência Fabril | `EFICIENCIA_PERCENTUAL` na view `vw_Apontamentos_Eficiencia` = **(tempo previsto ÷ tempo real) × 100** |
| Detalhe do apontamento (`GET /production/oee/appointments/{id}`) | Mesmo cálculo em SH6010: roteiro (setup + tempo padrão × quantidade) e horários do apontamento |

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
| `production_oee_series_aggregation_service.py` | `resolve_period_oee_by_branch` deriva o OEE do período por filial das linhas diárias (`Σsum / Σcount`, arredondado uma única vez) — **exatamente** igual a `ROUND(AVG(EFICIENCIA_PERCENTUAL), 2)` |
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
