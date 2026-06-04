# API DELPI — Testes sem acesso ao TOTVS (Google Sheets)

> **Quando usar:** VPN TOTVS indisponível, SQL Server inacessível ou ambiente dev offline do Protheus.  
> **Código de testes:** `api-delpi/tests/test_google_sheets_routes_live.py`

---

## 1. Diagnóstico rápido

A API pode estar **online** mesmo com TOTVS fora:

```bash
curl -s http://localhost/apps/api-delpi/health
# {"status":"online"}
```

Rotas que dependem **só** de **Google Sheets** continuam funcionando. Rotas que calculam percentuais sobre **ROL** ou consultam tabelas Protheus falham com erro 500/timeout.

---

## 2. Rotas recomendadas (sem TOTVS)

| Método | Path | Fonte de dados | Permissão |
|--------|------|----------------|-----------|
| GET | `/quality/kaizens/summary` | Google Sheets (`QUALITY_*`) | `dashboard-quality.view` ou `api-delpi.quality.access` |
| GET | `/quality/audit-5s/summary` | Google Sheets | idem |
| GET | `/quality/kaizens/summary?date_start=01-01-2026&date_end=31-12-2026` | Sheets + filtro | idem |

**Leitura direta das planilhas** (sem passar pelos use cases HTTP):

| Planilha | Env |
|----------|-----|
| Kaizen | `QUALITY_SHEET_ID` + `QUALITY_KAIZEN_SHEET_GID` |
| Audit 5S | `QUALITY_SHEET_ID` + `QUALITY_AUDIT_5S_SHEET_GID` |
| EBITDA | `FINANCIAL_EBITDA_SHEET_ID` + `FINANCIAL_EBITDA_SHEET_GID` |
| Mão de obra direta | `DIRECT_LABOR_SHEET_ID` + `DIRECT_LABOR_SHEET_GID` |
| Economia negociações (Suprimentos) | `SUPPLIES_IDD_SHEET_ID` + `SUPPLIES_NEGOTIATION_SAVINGS_SHEET_GID` |

---

## 3. Rotas que ainda exigem TOTVS

Mesmo lendo parte dos dados em Sheets, estas rotas chamam `FinancialRepository` / repositórios TOTVS:

| Path | Motivo |
|------|--------|
| `/financial/ebitda_pct`, `/fixed_cost_pct`, `/pmr` | ROL por filial no SQL Server |
| `/production/direct_labor_cost_pct`, `/production_cost_pct`, `/depreciation_pct` | ROL para percentual |
| `/commercial/*`, `/sales/*`, `/products/*` | Protheus |
| `/production/eficiencia-fabril/*` | View TOTVS |
| `/quality/ppm/*`, `/quality/nonconformities/*` | TOTVS |

Para homologar **dashboard-quality** sem TOTVS, use Kaizen e Audit 5S.

---

## 4. Teste HTTP com token de serviço

Útil em CI ou quando o Keycloak não expõe password grant:

```bash
TOKEN="${API_DELPI_INTERNAL_SERVICE_TOKEN}"

curl -s -H "Authorization: Bearer $TOKEN" \
     -H "X-Delpi-Caller-App: dashboard-quality" \
     "http://localhost/apps/api-delpi/quality/kaizens/summary" | jq '.success,.message'
```

O token de serviço **não** dispara rastreamento de uso (middleware ignora `API_DELPI_INTERNAL_SERVICE_TOKEN`).

---

## 5. Testes automatizados (container)

```bash
docker exec delpi-api-delpi sh -c 'cd /app && PYTHONPATH=/app pytest \
  tests/test_google_sheets_routes_live.py -v'
```

Cobertura do arquivo:

- leitura CSV real das 4 planilhas configuradas;
- `GET /quality/kaizens/summary` e `/quality/audit-5s/summary` via `TestClient`;
- confirma que token de serviço não agenda `schedule_app_usage_record`.

Suite completa (uso + sheets):

```bash
docker exec delpi-api-delpi sh -c 'cd /app && PYTHONPATH=/app pytest \
  tests/test_google_sheets_routes_live.py \
  tests/test_app_usage_tracker.py \
  tests/test_app_usage_tracking_middleware.py -q'
```

---

## 6. Teste manual do rastreamento de uso

1. Usuário com consentimento **`usage_tracking`** ativo (Portal → Privacidade e Dados).
2. Abrir **dashboard-quality** no portal (não token de serviço).
3. Verificar debounce na Core API (`app_usage_events` com `source=integration`, `caller_app_id=dashboard-quality`).

Middleware: `api-delpi/app/middleware/app_usage_tracking_middleware.py`  
Integração: [rastreamento-uso-apps.md](../../../docs/04-core-api/rastreamento-uso-apps.md).

---

## 7. Documentos relacionados

- [00-visao-geral.md](./00-visao-geral.md)
- [01-health.md](./01-health.md)
- [visao-geral-api-delpi.md](../../../docs/07-api-delpi/visao-geral-api-delpi.md)
- [troubleshooting.md](../../../docs/10-guias-operacionais/troubleshooting.md) §13
