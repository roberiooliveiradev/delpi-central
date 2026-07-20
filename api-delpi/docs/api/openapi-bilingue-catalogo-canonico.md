# OpenAPI bilíngue e catálogo canônico

## Princípio

O **OpenAPI da api-delpi** é a única fonte de verdade para catálogos (TV, chat e outras apps):

| Camada | Idioma / conteúdo |
|--------|-------------------|
| `summary` / `description` nativos | **Inglês** — preenchidos no OpenAPI ao vivo a partir de `x-delpi.locale.en` (Swagger UI) |
| `x-delpi.locale` | **EN + pt-BR** (summary, description, whenToUse) — chat/TV leem daqui |
| `x-delpi.params.<name>.locale` | Labels/descrições de query params em EN + pt-BR; EN também hidrata `parameters[].description` no Swagger (substitui vazio, eco do nome ou texto PT) |
| `x-delpi.params.<name>.format` | Hint OpenAPI (ex.: `"date"`) — Swagger mostra date picker; declarado em `openapi_param_locale.json` |
| `x-delpi.category` | Categoria de produto (`commercial`, `production`, …) |
| `x-delpi.tv` | Espelho de `locale.pt-BR` para compatibilidade |

Consumidores **importam** o contrato (baseline / OpenAPI), não reinventam enums nem labels.

Diretriz Cursor (obrigatória em rotas novas): **`.cursor/rules/api-delpi-openapi-route-standards.mdc`**.

Cobertura de testes HTTP (meta smoke + gate): **[`playbook-route-test-coverage-100.md`](../roadmaps/playbook-route-test-coverage-100.md)**.

---

## Como construir uma rota futura (obrigatório)

### 1. Router FastAPI

```python
@router.get("/path", operation_id="get_domain_thing")  # estável, snake_case
@require_any_permission(SOME_PERM)
def handler(
    branch: str | None = BRANCH_QUERY_OPTIONAL,  # de query_param_enums.py
    granularity: str = GRANULARITY_QUERY_MONTH,
):
    return api_delpi_success(data, operation_id="get_domain_thing")  # igual ao decorator
```

| Regra | Detalhe |
|-------|---------|
| `operation_id` no decorator | Sempre; se o `def` for curto (`update_audit`), o oid canônico vai no decorator |
| Mesmo id no envelope | `api_delpi_success(..., operation_id=...)` idêntico |
| Chat-critical | Preferir `**agent_route(...)` **sem** segundo `operation_id=` (evita `TypeError` no startup) |
| Domínio fechado | `enum=` **e** `pattern=` via factories em [`query_param_enums.py`](../../app/interface/http/query_param_enums.py) — **sempre** `BRANCH_QUERY_OPTIONAL()` (nova instância); **nunca** reutilizar o mesmo objeto `Query()`. Só `enum=` documenta OpenAPI; **sem `pattern` não há 422 em runtime** |
| Datas | Params de data em `openapi_param_locale.json` com `"format": "date"` (ou nome canônico); o injector aplica no schema OpenAPI |
| Description do Query | Inglês (ou deixar o injector sobrescrever PT com `locale.en`) |
| Filial consolidável | `BRANCH_QUERY_OPTIONAL` (`01`/`02`) — **não** default HTTP `"01"` |

### 2. Contrato e segurança

1. `route_contract_registry.py` — `entity` + `shape`.
2. Permissão em `api_delpi_permissions.py` (sem string literal no router).
3. Filial TOTVS: `branch_access_error` quando houver escopo por filial.
4. Upload: volume Compose — ver `persistent-upload-storage.mdc`.

### 3. Textos bilíngues

| Onde | O quê |
|------|--------|
| [`tv_route_audience.json`](../../app/content/tv_route_audience.json) | `locale.en` + `locale.pt-BR` (`summary` **distintos**); `category`; params específicos da rota |
| [`openapi_param_locale.json`](../../app/content/openapi_param_locale.json) | Param **novo** compartilhado (branch, periodDays, …) |
| Summary nativo OpenAPI | Inglês (espelhado de `locale.en` no enrich do baseline) |

Loader: `route_locale_catalog_service` → `openapi_delpi_extension_injector` (anexa `x-delpi` **e** aplica `locale.en` em summary/description nativos para o Swagger).

### 4. TV / MFE (sem inventário paralelo)

| Artefato | Papel |
|----------|--------|
| Gerador `scripts/generate_tv_data_routes_from_openapi.py` | Lê baseline + overlays; **sem** `PARAM_LABELS_PT` |
| [`tv_param_ux_defaults.json`](../../../tv-dashboard-api/tv_app/content/tv_param_ux_defaults.json) | Default UX filial `"01"` — **não** é contrato HTTP |
| `scripts/sync_tv_data_param_catalog.py --write` | Regenera `dataParamCatalog.ts` + labels do presentation |

### 5. Sync após a rota existir

```bash
# Export OpenAPI (recomendado no container)
docker exec delpi-api-delpi python -c \
  "from app.main import app; import json; open('/tmp/o.json','w').write(json.dumps(app.openapi()))"
docker cp delpi-api-delpi:/tmp/o.json /tmp/openapi_full.json

cd api-delpi
python scripts/sync_openapi_baseline.py --from-json /tmp/openapi_full.json
# ou só locale, se o baseline já tem parameters:
# python scripts/sync_openapi_baseline.py --enrich-locale-only

cd ..
python3 scripts/generate_tv_data_routes_from_openapi.py --write
python3 scripts/generate_tv_data_routes_from_openapi.py --check
python3 scripts/check_tv_openapi_catalog_parity.py --check --strict-auto-ids
python api-delpi/scripts/audit_openapi_operation_ids.py --check
python3 scripts/sync_tv_data_param_catalog.py --write && --check
```

Chat: seguir [12-procedimento-reimport-openapi.md](./12-procedimento-reimport-openapi.md) + checklist [new-api-route-checklist](../../.cursor/rules/new-api-route-checklist.mdc).

### 6. Smoke HTTP e inventário de cobertura

Toda rota nova precisa de **smoke Nível A** (`meta.operationId` / envelope) e sincronização do inventário:

```bash
cd api-delpi
# escrever teste com o operationId literal (ver tests/support/route_contract_smoke.py)
pytest tests/ -q -k "<operation_id>"
python scripts/audit_route_test_coverage.py --write
python scripts/audit_route_test_coverage.py --check
python scripts/audit_route_test_coverage.py --check-complete  # zero gap
```

Playbook: [playbook-route-test-coverage-100.md](../roadmaps/playbook-route-test-coverage-100.md)  
Inventário: [`route_test_coverage.json`](../../app/content/route_test_coverage.json)

### 7. O que é proibido

- Auto-id FastAPI (`*_get` / `*_post`) como contrato estável.
- Labels/enums só no MFE ou no gerador TV.
- `en.summary == pt-BR.summary` (stubs).
- Segundo `operation_id=` junto com `**agent_route`.
- Editar `dataParamCatalog.ts` sem regenerar do JSON canônico.
- Entregar rota sem smoke Nível A / sem atualizar o inventário de cobertura.
- Confiar só em `Query(enum=…)` para validação runtime (usar `pattern=` nas factories).

---

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

Polimento EN em lote:

```bash
cd api-delpi
python scripts/polish_openapi_locale_en.py --write
python scripts/sync_openapi_baseline.py --enrich-locale-only
```

## Sync (procedimento completo)

Ver § 5 acima. Inventário: [`openapi_operation_id_inventory.json`](../../app/content/openapi_operation_id_inventory.json).

| Onda | Escopo | Estado |
|------|--------|--------|
| R0–R5 | operationId, locale, labels, chat import | feito |
| R6 | 5S ids, enums Query, UX defaults, params por rota, sync MFE | feito |
| R7 | Cobertura HTTP 100% das rotas (`audit_route_test_coverage` + smokes Nível A) | feito |

Gate estrito:

```bash
python3 scripts/check_tv_openapi_catalog_parity.py --check --strict-auto-ids
python api-delpi/scripts/audit_openapi_operation_ids.py --check-aliases-coverage
cd api-delpi && python scripts/audit_route_test_coverage.py --check-complete
```

## Overlay TV-only

[`tv_data_route_overlays.json`](../../../tv-dashboard-api/tv_app/content/tv_data_route_overlays.json):
`valueFields`, `tvConstraints`, `fixedQueryParams` — **não** enums/labels de domínio.

## Apps

- TV / portal → textos `pt-BR`
- Swagger → EN nativo
- Chat → `locale.pt-BR` no import OpenAPI
