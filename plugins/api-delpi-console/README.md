# Console API DELPI

Microfrontend para explorar rotas da **api-delpi**, executar requests de teste e inspecionar envelopes de resposta. Monitoramento contínuo (polling 30 s) com glance RED, alertas e SLI da janela amostrada.

## Rotas do app

| Path | Descrição |
|------|-----------|
| `/apps/api-delpi-console` | Início — glance RED (req/erros/p95/pool%/alertas) + error budget da janela + atalhos |
| `/apps/api-delpi-console/documentacao` | Documentação interativa (`/apps/api-delpi/docs`) com JWT automático |
| `/apps/api-delpi-console/verificacoes` | Smoke suites (essencial, PPM, engenharia/agendamento) com exportação CSV/JSON |
| `/apps/api-delpi-console/sql` | Saúde SQL — top queries por duração e repetição |
| `/apps/api-delpi-console/cache` | Cache LMP/estoque, callers, **connection pools** (Plugins Postgres / TOTVS) e comparador de deploy |
| `/apps/api-delpi-console/alertas` | Alertas abertos/histórico (`smoke_failure`, `p95_latency`, `slow_sql`, `pool_saturation`) |
| `/apps/api-delpi-console/explorer` | Explorador OpenAPI; **writes** (POST/PUT/PATCH/DELETE) pedem confirmação host-contained |
| `/apps/api-delpi-console/spec` | Inventário OpenAPI, diff vs baseline, **contratos de envelope** (`GET /system/envelope-contracts`) |
| `/apps/api-delpi-console/history` | Histórico local de chamadas |

## UI e Module Federation

- Superfícies novas (glance KPI, error budget, confirmação de write) usam **`@delpi/plugin-ui`** (remote MF).
- Layout legado da página permanece em classes `adc-*` (tokens); **não** inventar CSS de card/KPI no MFE.
- Contrato de telemetria: `GET /system/console-health` (RED, pools, `sli`/`slo` da janela em memória — ≠ SLO 30d).
- Textos/limiares de alerta: `api-delpi/app/content/console_alerts.json` + `CONSOLE_ALERT_POOL_SATURATION_PCT`.

## Permissão

- `api-delpi-console.view`

As smoke suites são carregadas de `GET /system/smoke-definitions` (fonte: `api-delpi/app/content/smoke_definitions.json`), com fallback local em `src/content/smokeSuites.ts`.

## Desenvolvimento

```bash
cd plugins/api-delpi-console
npm install
npm run dev
```

Build de produção (requer resolução do remote `@delpi/plugin-ui` via federation):

```bash
npm run build
```

## Docker

Preferir scripts sequenciais da infra (evita OOM):

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build api-delpi-console
```

## Registro na Core API

O manifesto expõe **apenas a rota principal** no launcher do portal; Documentação, Verificações, Explorador etc. são navegação interna do MFE.

Após alterar o manifesto, **re-registre** o app para remover sub-rotas antigas do menu:

```bash
curl -X POST "http://localhost/core-api/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @api-delpi-console.manifest.json
```

## Documentação interativa

O console embute a documentação oficial da api-delpi (`/docs`) e envia o JWT do portal via `postMessage` (`DELPI_AUTH`), o mesmo contrato usado em iframes do portal. Ver `api-delpi/app/main.py`.

## Header de rastreamento

Todas as chamadas à api-delpi enviam:

```http
X-Delpi-Caller-App: api-delpi-console
```

## Playbook e roadmap

Ver `api-delpi/docs/roadmaps/playbook-api-delpi-console.md`.
