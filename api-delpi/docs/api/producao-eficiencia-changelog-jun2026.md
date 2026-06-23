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
