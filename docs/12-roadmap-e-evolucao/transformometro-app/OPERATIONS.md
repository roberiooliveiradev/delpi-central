# Operações — Transformômetro

Runbook para equipe após go-live (Postgres como fonte de verdade).  
**Playbook 18 (jun/2026):** ver também [status-atual.md](./status-atual.md) e [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md).

## URLs

| Recurso | URL |
|---------|-----|
| Portal | `https://www.minhadelpi.com.br/apps/transformometro` |
| Dashboard | `/apps/transformometro/dashboard` |
| Processos + instâncias | `/apps/transformometro/processos` → detalhe → painel instâncias |
| Filiais | `/apps/transformometro/filiais` |
| Setores | `/apps/transformometro/setores` |
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
8. **Instâncias:** replicar timeline entre filiais/setores pelo painel **Replicar instância** (canônico); evitar duplicar processo-mestre (legado deprecado).
9. **Dashboard:** escolher visão Consolidado / Filial / Departamento; usuários com RBAC filial veem escopo em `/options` → `access_scope`.
10. **Recursos:** definir **escopo de rateio** (`empresa` / `filial` / `setor`) no cadastro de Recursos.

## Deploy / upgrade Playbook 18

Ordem recomendada (local ou produção):

```bash
# 1. Backup cadastro
cd transformometro-api
set -a && source ../infra/.env && set +a
python scripts/import_cadastro_json.py export -o fixtures/cadastro/transformometro-cadastro-$(date +%Y%m%d).json

# 2. Rebuild containers (migrations V011–V020 no boot se TM_RUN_MIGRATIONS_ON_STARTUP=true)
cd ..
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env build transformometro-api transformometro
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up -d --force-recreate transformometro-api transformometro

# 3. Conferir migrations
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status

# 4. Bootstrap filiais (V011 não faz seed)
docker exec delpi-transformometro-api python scripts/bootstrap_filiais_from_cadastro.py -i fixtures/cadastro/transformometro-cadastro-YYYYMMDD.json

# 5. Recalc dashboard (V017 trunca cache)
# UI: Dashboard → Recalcular  OU  POST /dashboard/recalcular com JWT admin

# 6. Manifesto + RBAC
export TOKEN="..." BASE_URL="..."
./plugins/transformometro/scripts/register-manifest.sh
```

**Migrations automáticas:** `TM_RUN_MIGRATIONS_ON_STARTUP=true` aplica pendentes no startup da API. Falha impede subida do serviço.

**Pós-V017:** cache vazio até recalc full. **Pós-V014:** revisões backfilladas para instâncias legadas.

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
- Opcional RBAC filial: `transformometro.view.filial-01`, `transformometro.manage.filial-01`, `transformometro.view.consolidated`, …

## Troubleshooting

| Sintoma | Ação |
|---------|------|
| `db_ready: false` | `TM_RUN_MIGRATIONS_ON_STARTUP=true`, reiniciar API, logs `tm_migrations_*`; `migrations_runner status` |
| Migration falha no boot | Logs container; corrigir SQL/dados; **não** alterar migration já aplicada (checksum) |
| Dashboard zerado pós-upgrade | Esperado após V017 — **Recalcular** full |
| Visão consolidada bloqueada | RBAC: usuário precisa `transformometro.view.consolidated` ou só permissões globais |
| Instância/revisão 404 | Usar URL canônica `/instancias/{uuid}/revisoes/{uuid}` |
| POST processo 500 | Rebuild API (fix `SimpleNamespace` no audit); ver logs |
| Dashboard zerado | Cadastrar revisões + medições → **Recalcular** |
| Import `uq_processos_codigo` | Usar `--replace` ou `git pull` com reconcile por `codigo_processo` |
| Números ≠ planilha antiga | Esperado: spec usa delta de recursos na bruta; ver [OVERVIEW.md](./OVERVIEW.md) |
| SI 401 Transformômetro | `API_DELPI_INTERNAL_SERVICE_TOKEN` nos 3 serviços; rebuild SI |
| SI 404 Transformômetro | `TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000` (sem `/apps/`) |

## Auditoria

Mutações gravam em `transformometro.audit_logs` (entity_type, action, user_id, payload_json).

## Integração com api-delpi e Strategic Indicators

Não duplicar leitura SQL, planilha Google nem calculador legado: consumir a API oficial (Postgres via S2S).

**Runtime verificado (jun/2026):** `engineering_composer` na api-delpi usa somente `TransformometroTransformaMaisGateway`. O repositório Sheets em `google_sheets/transforma_mais/` não está ligado ao fluxo.

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
