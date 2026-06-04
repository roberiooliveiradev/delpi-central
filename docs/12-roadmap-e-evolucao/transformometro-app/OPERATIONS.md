# Operações — Transformômetro

Runbook para equipe após go-live (Postgres como fonte de verdade).

## URLs

| Recurso | URL |
|---------|-----|
| Portal | `https://www.minhadelpi.com.br/apps/transformometro` |
| Dashboard | `/apps/transformometro/dashboard` |
| Processos | `/apps/transformometro/processos` |
| Recursos (catálogo) | `/apps/transformometro/recursos` |
| Exportar / Importar JSON | `/apps/transformometro/dados` |
| API health | `/apps/transformometro-api/transformometro/health` |

## Rotina diária

1. Cadastro e alterações somente pela **UI** ou API (`transformometro-api`).
2. Após mudanças relevantes (revisão ativa, vigências, medições): **Dashboard → Recalcular**.
3. **Alertas** (economia líquida negativa ≥3 meses) e export **CSV** ou **Excel** no dashboard.
4. Cadastro: preencher **família** e **agrupador ferramenta** quando o processo participa de rateio compartilhado.
5. **Recursos compartilhados:** cadastrar em **Recursos** (menu); vincular em Processos → revisão → aba Recursos.
6. **Revisões:** cadastrar baseline/melhorias e **Definir como ativa** quando for usar no dashboard (sem aprovação).
7. Cadastro oficial somente no portal (sem importação de planilha).

## Registro Core API e RBAC

```bash
export TOKEN="<jwt com apps.manage>"
export BASE_URL="https://www.minhadelpi.com.br"
./plugins/transformometro/scripts/register-manifest.sh
```

Atribuir ao perfil de engenharia/gestão, no mínimo:

- `transformometro.view`
- `transformometro.processes.manage`
- `transformometro.revisions.manage`
- `transformometro.dashboard.recalculate`
- `transformometro.shared-resources.manage` (catálogo Recursos)
- `transformometro.data.transfer` (exportar / importar JSON em `/dados`)

## Troubleshooting

| Sintoma | Ação |
|---------|------|
| `db_ready: false` | `TM_RUN_MIGRATIONS_ON_STARTUP=true`, reiniciar API, ver logs `tm_migrations_*` |
| POST processo 500 | Rebuild API (fix `SimpleNamespace` no audit); ver logs |
| Dashboard zerado | Cadastrar revisões + medições → **Recalcular** |
| Import `uq_processos_codigo` | Usar `--replace` ou `git pull` com reconcile por `codigo_processo` |
| Números ≠ planilha antiga | Esperado: spec usa delta de recursos na bruta; ver [OVERVIEW.md](./OVERVIEW.md) |
| SI 401 Transformômetro | `API_DELPI_INTERNAL_SERVICE_TOKEN` nos 3 serviços; rebuild SI |
| SI 404 Transformômetro | `TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000` (sem `/apps/`) |

## Auditoria

Mutações gravam em `transformometro.audit_logs` (entity_type, action, user_id, payload_json).

## Integração com api-delpi e Strategic Indicators

Não duplicar leitura SQL nem calculador: consumir a API oficial.

| Consumidor | Rotas públicas (inalteradas) | Upstream interno |
|------------|------------------------------|-------------------|
| dashboard-engineering | `/apps/api-delpi/engineering/transforma-mais/*` | `transformometro-api` |
| strategic-indicators | snapshot engenharia | `transformometro-api` |

Endpoints de integração (contrato legado engenharia):

- `GET /transformometro/integrations/engineering/transforma-mais/processes`
- `GET /transformometro/integrations/engineering/transforma-mais/processes/summary`

Cliente compartilhado: `shared/transformometro_client` (`TransformometroApiClient`).

Variáveis:

- `TRANSFORMOMETRO_API_BASE_URL` — chamadas **entre containers**: `http://transformometro-api:8000` (sem `/apps/...`; o nginx faz rewrite só no browser). Rotas: `/transformometro/integrations/engineering/transforma-mais/*`
- `API_DELPI_INTERNAL_SERVICE_TOKEN` — token **já previsto** no `infra/.env` de produção (`append-missing-env-production.sh`); mesmo valor em `transformometro-api`, `strategic-indicators-api` e `api-delpi`. Header: `X-Delpi-Service-Token` (padrão DELPI, igual conceito ao `CORE_API_INTEGRATIONS_SERVICE_TOKEN` da Core API).
- ~~`TRANSFORMOMETRO_SERVICE_BEARER`~~ — **removido** (legado, substituído por `API_DELPI_INTERNAL_SERVICE_TOKEN`).

**401 em Indicadores:** JWT em threads (`submit_in_request_context` + `request_authorization`), ignorar snapshot/cache com 401 antigo, e garantir `API_DELPI_INTERNAL_SERVICE_TOKEN` no `.env`.
