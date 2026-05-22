# Operações — Transformômetro

Runbook para equipe após go-live (Postgres como fonte de verdade).

## URLs

| Recurso | URL |
|---------|-----|
| Portal | `https://www.minhadelpi.com.br/apps/transformometro` |
| Dashboard | `/apps/transformometro/dashboard` |
| Processos | `/apps/transformometro/processos` |
| Recursos (catálogo) | `/apps/transformometro/recursos` |
| Import (admin) | `/apps/transformometro/import` |
| API health | `/apps/transformometro-api/transformometro/health` |

## Rotina diária

1. Cadastro e alterações somente pela **UI** ou API (`transformometro-api`).
2. Após mudanças relevantes (revisão ativa, vigências, medições): **Dashboard → Recalcular**.
3. **Alertas** (economia líquida negativa ≥3 meses) e export **CSV** ou **Excel** no dashboard.
4. Cadastro: preencher **família** e **agrupador ferramenta** quando o processo participa de rateio compartilhado.
5. **Recursos compartilhados:** cadastrar em **Recursos** (menu); vincular em Processos → revisão → aba Recursos.
6. **Revisões:** enviar para análise → aprovar → só então **Definir como ativa** (workflow V005).
7. Não editar a planilha Transforma+ em produção (somente leitura ou desligada).

## Importação / reimportação

### Primeira carga (já feita)

```bash
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply --replace
```

### Atualizar da planilha (contingência)

```bash
# Pré-visualizar
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --preview

# Merge (mantém UUIDs por codigo_processo)
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply

# Substituir tudo (cuidado)
docker exec delpi-transformometro-api python scripts/migrate_transforma_mais_sheet.py --apply --replace
```

Validar no JSON de saída: `diff.all_match: true` (economia líquida/bruta vs planilha).

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
- `transformometro.admin` (import planilha)

## Notificações de workflow (portal)

Guia completo: [NOTIFICACOES-WORKFLOW.md](./NOTIFICACOES-WORKFLOW.md).

Resumo: variáveis em `infra/.env` / `infra/.env.prod` → serviço `transformometro-api`. Após alterar: `docker compose up -d --force-recreate transformometro-api` (e rebuild Core API + Portal na primeira vez, categoria `transformometro`).

## Desligar escrita na planilha Google

Checklist (manual, Google Workspace):

1. Comunicar que o cadastro oficial é o **Transformômetro** no portal.
2. Na planilha `TRANSFORMA_MAIS_SHEET_ID`: restringir edição (visualizador para consulta histórica) ou mover para pasta arquivada.
3. Remover links de edição em procedimentos internos / Apps Script de escrita.
4. Manter `TRANSFORMA_MAIS_*` no `.env` só se ainda usar import de contingência.
5. SI e `dashboard-engineering` consomem **Postgres via transformometro-api** (não Sheets).

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
| Sino sem alerta de revisão | `TM_NOTIFICATIONS_ENABLED=true`, aprovadores preenchidos, token Core API igual ao `infra/.env` |

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
- `TRANSFORMOMETRO_SERVICE_BEARER` — legado opcional; evitar duplicar segredo.

**401 em Indicadores:** JWT em threads (`submit_in_request_context` + `request_authorization`), ignorar snapshot/cache com 401 antigo, e garantir `API_DELPI_INTERNAL_SERVICE_TOKEN` no `.env`.
