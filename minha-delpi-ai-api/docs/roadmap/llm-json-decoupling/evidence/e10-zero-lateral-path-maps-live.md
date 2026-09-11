# E10 — Live zero mapa lateral

**Status:** `ATENDIDO` (2026-09-11)  
**Onda:** I (plano 10)  
**Harness:** `scripts/smoke_e10_zero_lateral_path_maps_live.py`  
**JSON:** `docs/roadmap/llm-json-decoupling/evidence/e10-zero-lateral-path-maps-live.json`

## Objetivo

Provar em runtime (gateway + chat + Action Catalog) que, após remoção dos mapas laterais:

1. content do assistente não reintroduz keys laterais;
2. domínio operacional chega em `metadata.apiRouteDomain` via catalog/inference;
3. siblings (produto × KPI) continuam corretos;
4. pedido sem sentido não explode nem carrega `pathMarkers` no payload.

## Veredito live

```text
content_no_lateral_keys = PASS
product_stock_domain    = PASS  (apiRouteDomain=product, /products/10080022/stock)
department_kpi_sibling  = PASS  (apiRouteDomain=department_kpi, /commercial/closing-rate/series)
unknown_safe_negative   = PASS
OVERALL = PASS
```

## Dataset

| Caso | Mensagem |
|------|----------|
| Positive | `qual o estoque do produto 10080022?` |
| Sibling | `qual a taxa de conversão comercial neste mês?` |
| Negative | `xyzzy quux foobar sem sentido operacional 999?` |

Override: `SMOKE_PRODUCT_CODE`, `SMOKE_BASE_URL`, `SMOKE_USER` / `SMOKE_PASSWORD`.

## Como reproduzir

```bash
cd minha-delpi-ai-api
.venv/bin/python -u scripts/smoke_e10_zero_lateral_path_maps_live.py
```
