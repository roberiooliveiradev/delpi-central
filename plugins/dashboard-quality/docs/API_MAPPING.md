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
| `getAudit5sSummary` | GET | `/quality/audit-5s/summary` | `start_date`, `end_date`, `branch` |
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
| `/quality/internal-nc/*` | Módulo PostgreSQL; rotas não montadas em `main.py` |
| `/quality/external-nc/*` | Idem |
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
