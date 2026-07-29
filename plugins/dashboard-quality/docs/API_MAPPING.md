# Mapeamento API — Dashboard Qualidade

Base URL (browser, via gateway):

```text
/apps/api-delpi
```

Prefixo de qualidade:

```text
/quality
```

**Permissão atual:** `api-delpi.quality.access`  
**Permissão prevista (Fase 0):** também `dashboard-quality.view`

**Envelope de resposta:**

```json
{
  "success": true,
  "message": "...",
  "data": { }
}
```

Documentação oficial: `api-delpi/docs/api/06-modulos-departamentais.md` (seção Qualidade), `10-referencia-rapida-endpoints.md`.

---

## Endpoints consumidos

| Função no plugin (prevista) | Método | Rota | Query params principais |
|---|---|---|---|
| `listNonconformities` | GET | `/quality/nonconformities` | `type`, `branch`, `date_start`, `date_end`, `status`, `item_code`, `description`, `page`, `page_size` |
| `getKaizenSummary` | GET | `/quality/kaizens/summary` | `title`, `status`, `branch`, `date_start`, `date_end` |
| `getKaizenById` | GET | `/quality/kaizens/{kaizen_id}` | — |
| `getAudit5sSummary` | GET | `/quality/audit-5s/summary` | `start_date`, `end_date`, `branch` — Postgres (`overall_score_pct`, exclui draft) |
| `getScrapCostPct` | GET | `/quality/scrap-cost-pct` | `branch`, `date_start`, `date_end` |
| `getReworkCostPct` | GET | `/quality/rework-cost-pct` | `branch`, `date_start`, `date_end` |
| `getPpmInternalSummary` | GET | `/quality/ppm/internal/summary` | `branch`, `date_start`, `date_end` |
| `getPpmExternalSummary` | GET | `/quality/ppm/external/summary` | `branch`, `date_start`, `date_end` |
| `listPpmInternal` | GET | `/quality/ppm/internal` | `branch`, `date_start`, `date_end`, `page`, `page_size` |
| `listPpmExternal` | GET | `/quality/ppm/external` | `branch`, `date_start`, `date_end`, `page`, `page_size` |
| `listQualityBranches` | GET | `/quality/branches` | `date_start`, `date_end` |
| `getPpmSeries` | GET | `/quality/ppm/{type}/series` | `granularity`, `branch`, `date_start`, `date_end` |
| `getNonconformitySeries` | GET | `/quality/nonconformities/series` | `type`, `granularity`, `branch`, `date_start`, `date_end`, filtros NC |

---

## Exemplos de URL completas

```text
GET /apps/api-delpi/quality/ppm/internal/summary?branch=01&date_start=2026-01-01&date_end=2026-05-18
GET /apps/api-delpi/quality/nonconformities?type=all&page=1&page_size=50
GET /apps/api-delpi/quality/kaizens/summary?branch=01
GET /apps/api-delpi/quality/audit-5s/summary?start_date=2026-01-01&end_date=2026-05-18
```

---

## Não consumir neste plugin (v1)

| Rota | Motivo |
|---|---|
| Indicadores estratégicos SI | API dedicada `strategic-indicators-api` |

---

## Implementação de referência (api-delpi)

Router: `api-delpi/app/interface/http/routes/quality/quality_router.py`  
Composition root: `api-delpi/app/composition/quality_composer.py`

Ao tipar o frontend, inspecionar DTOs em:

- `app/application/dto/ppm/`
- `app/application/dto/kaizen/`
- `app/application/dto/auditoria_5s/`
- `app/application/dto/nonconformity/`

---

## Kaizen — planilha e cálculo

Fonte: Google Sheets via `GET /quality/kaizens/summary` (sem TOTVS).

**Colunas usadas na planilha:** `filial`, `descricao`, `responsavel`, `area_setor`, `custo_investimento`, `segudos_por_ocorrecia` (ou `segundos_por_ocorrencia`), `ocorrecias_por_dia` (ou `ocorrencias_por_dia`), `custo_hora`, `status`, `data`, `deleted`.

**Não usar na planilha:** `horas_poupadas_dia`, `ganho_diario` — a API calcula `daily_savings`:

```
daily_savings = (segundos_por_ocorrencia × ocorrencias_por_dia / 3600) × custo_hora
```

**Campo no frontend:** `list_kaizen[].daily_savings`, `list_kaizen[].annual_savings` (`daily_savings × 365`) e `total_savings` (soma ponderada por dias ativos no período filtrado).

**Listagem completa (tabela do dashboard):** chamar `/kaizens/summary` **sem** `date_start`/`date_end` para todos os kaizens implantados; KPIs e gráficos continuam usando o período filtrado.

Documentação completa: `api-delpi/docs/api/06-modulos-departamentais.md` (§ Kaizen).

---

## Performance (jun/2026)

| Recurso | Comportamento no MFE | Cache api-delpi |
|---------|----------------------|-----------------|
| Gráfico PPM (`PpmPage`) | Série interna **ou** externa sob demanda; ambas só no modo «Comparar» | `ppm-{type}-series` + `ppm-summary` por bucket (TTL 300 s) |
| Hook `usePpmChartSeries` | Cache cliente 60 s (`useQualityResource`) | — |

Testes de regressão cache: `api-delpi/tests/test_ppm_query_cache.py`.
