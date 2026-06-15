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

## 4. Deploy após as mudanças

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

## 5. Testes de regressão

```bash
cd api-delpi
.venv/bin/pytest tests/test_production_appointment_time_analysis.py \
  tests/test_production_efficiency_valid_range.py -q
```

Build dos plugins:

```bash
cd plugins/dashboard-production && npm run build
cd plugins/eficiencia-fabril && npm run build
```

---

## 6. Documentação relacionada

- [06-modulos-departamentais.md](./06-modulos-departamentais.md) — rotas `/production/*`
- [plugins/dashboard-production/README.md](../../../plugins/dashboard-production/README.md)
- [plugins/eficiencia-fabril/README.md](../../../plugins/eficiencia-fabril/README.md)
- `minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md` — contrato para agentes
