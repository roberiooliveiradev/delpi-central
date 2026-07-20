# OpenAPI bilíngue e catálogo canônico

## Princípio

O **OpenAPI da api-delpi** é a única fonte de verdade para catálogos (TV, chat e outras apps):

| Camada | Idioma / conteúdo |
|--------|-------------------|
| `summary` / `description` nativos | **Inglês** (padrão OpenAPI / Swagger / integradores) |
| `x-delpi.locale` | **EN + pt-BR** (summary, description, whenToUse) |
| `x-delpi.params.<name>.locale` | Labels/descrições de query params em EN + pt-BR |
| `x-delpi.category` | Categoria de produto (`commercial`, `production`, …) |
| `x-delpi.tv` | Espelho de `locale.pt-BR` para compatibilidade |

Consumidores **importam** o contrato (baseline / OpenAPI), não reinventam enums nem labels.

## Onde curar textos

Arquivo: [`app/content/tv_route_audience.json`](../../app/content/tv_route_audience.json) (version ≥ 2).

```json
{
  "get_dashboard_department_idd": {
    "category": "system",
    "locale": {
      "en": { "summary": "...", "description": "...", "whenToUse": "..." },
      "pt-BR": { "summary": "...", "description": "...", "whenToUse": "...", "label": "..." }
    },
    "params": {
      "department_id": {
        "locale": {
          "en": { "label": "Department", "description": "..." },
          "pt-BR": { "label": "Departamento", "description": "..." }
        }
      }
    }
  }
}
```

Loader: `app.domain.services.route_locale_catalog_service` → injector `openapi_delpi_extension_injector` e baseline v3.

Params **globais** (branch, periodDays, …): [`app/content/openapi_param_locale.json`](../../app/content/openapi_param_locale.json) — mesclados em `x-delpi.params` **somente** para nomes presentes nos `parameters` da operação; override por rota em `tv_route_audience.json` ganha.

MFE TV: labels/hints gerados por `python3 scripts/sync_tv_data_param_catalog.py --write` (sem inventário paralelo manual).

Polimento EN em lote (stubs `locale.en` + summary nativo do baseline):

```bash
cd api-delpi
python scripts/polish_openapi_locale_en.py --write
python scripts/sync_openapi_baseline.py --enrich-locale-only
```

## Params tipados na origem

No router FastAPI:

- `operation_id="…"` estável (= envelope + registry)
- `Query(..., enum=[...], default=…)` quando o domínio for fechado
- `description` do Query em **inglês**

O gerador TV prefere `enum`/`default` do OpenAPI e labels de `x-delpi.params` / `openapi_param_locale.json`. **Não** há inventário paralelo `PARAM_LABELS_PT` / `PARAM_HINTS_PT` no script.

Defaults de filial no inspetor TV (`branch` → `"01"`) vivem em [`tv_param_ux_defaults.json`](../../../tv-dashboard-api/tv_app/content/tv_param_ux_defaults.json) — **UX apenas**, não alteram o contrato HTTP (`Query(None)` = consolidado quando permitido).

## Sync (procedimento)

```bash
# 1) Exportar OpenAPI do container (recomendado)
docker exec delpi-api-delpi python -c \
  "from app.main import app; import json; open('/tmp/o.json','w').write(json.dumps(app.openapi()))"
docker cp delpi-api-delpi:/tmp/o.json /tmp/openapi_full.json

# 2) Baseline v3 (parameters + xDelpi.locale/params/category)
cd api-delpi
python scripts/sync_openapi_baseline.py --from-json /tmp/openapi_full.json

# Só locale (sem reabrir FastAPI), se o baseline já existe:
python scripts/sync_openapi_baseline.py --enrich-locale-only

# 3) Catálogo TV
cd ..
python3 scripts/generate_tv_data_routes_from_openapi.py --write
python3 scripts/generate_tv_data_routes_from_openapi.py --check
python3 scripts/check_tv_openapi_catalog_parity.py --check
python api-delpi/scripts/audit_openapi_operation_ids.py --check
# Onda estrita (após aliases completos):
# python api-delpi/scripts/audit_openapi_operation_ids.py --check-aliases-coverage
```

## Ondas de estabilização de operationId

Inventário versionado: [`app/content/openapi_operation_id_inventory.json`](../../app/content/openapi_operation_id_inventory.json).

| Onda | Escopo |
|------|--------|
| R0 | Tooling + inventário + gates | feito |
| R1 | Qualidade (auto-ids) | feito |
| R2 | system / Agendamento / satélites | feito (300/300 estáveis) |
| R3 | Locale não-GET | feito (300/300 com locale) |
| R4 | Labels em `openapi_param_locale.json` + polimento EN | feito |
| R5 | Chat prefere `locale.pt-BR` no import OpenAPI | feito |
| R6 | Fechar gaps: 5S operation_id, enums Query, UX defaults TV, params por rota, sync MFE | feito |

Gate estrito (catálogo TV sem auto-id):

```bash
python3 scripts/check_tv_openapi_catalog_parity.py --check --strict-auto-ids
python api-delpi/scripts/audit_openapi_operation_ids.py --check-aliases-coverage
```

## Overlay TV-only

[`tv-dashboard-api/tv_app/content/tv_data_route_overlays.json`](../../../tv-dashboard-api/tv_app/content/tv_data_route_overlays.json):
`valueFields`, `tvConstraints`, `fixedQueryParams`, etc. — **não** enums/labels de domínio.

## Apps

- TV / portal → textos `pt-BR`
- Swagger → EN nativo
- Chat → pode usar `locale.pt-BR` no import OpenAPI
