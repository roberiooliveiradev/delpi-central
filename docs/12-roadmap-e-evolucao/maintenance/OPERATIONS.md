# Operações — Manutenção (mini-aplicadores)

Runbook para equipe após go-live. Postgres (`maintenance` schema) é a fonte de verdade operacional; TOTVS continua via api-delpi.

## URLs (dev local)

| Recurso | URL |
|---------|-----|
| Portal | `http://localhost/apps/maintenance` |
| Mini-aplicadores | `/apps/maintenance/mini-aplicadores` |
| Relatório preventivo | `/apps/maintenance/relatorio` |
| Configuração | `/apps/maintenance/configuracao` |
| API health | `/apps/maintenance-api/maintenance/health` |

## Rotina diária

1. **Reposições** — registrar trocas de peça em Mini-aplicadores (filial 01 ou 02).
2. **Preventiva** — revisar ranking em Relatório preventivo (CRÍTICO / ATENÇÃO / OK).
3. **Configuração** — ajustar motivos e faixas de status quando necessário.
4. Cadastro oficial somente no portal (sem Access após migração).

## Deploy / upgrade

```bash
# 1. Backup Postgres (schema maintenance)
pg_dump -h localhost -U plugins -n maintenance plugins > maintenance-$(date +%Y%m%d).sql

# 2. Rebuild containers
cd /path/to/delpi-central
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env build maintenance-api maintenance
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up -d --force-recreate maintenance-api maintenance delpi-gateway

# 3. Conferir health
curl -s http://localhost/apps/maintenance-api/maintenance/health | python3 -m json.tool
```

**Migrations automáticas:** `MAINT_RUN_MIGRATIONS_ON_STARTUP=true` aplica pendentes no startup. Falha impede subida do serviço.

## Registro Core API e RBAC

O manifesto registra o app; permissões são atribuídas na **Core API** (não Keycloak).

```bash
export TOKEN="<jwt com apps.manage>"
export BASE_URL="http://localhost"
chmod +x plugins/maintenance/scripts/register-manifest.sh
./plugins/maintenance/scripts/register-manifest.sh
```

Permissões mínimas (ver `maintenance.manifest.json`):

- `maintenance.view`
- `maintenance.replacements.manage`
- `maintenance.view.filial-01` / `maintenance.view.filial-02` (escopo filial)

## Migração Access → Postgres (one-shot)

1. No WinForms, exportar tabelas do `MiniAplicadoresBD` para CSV (UTF-8).
2. Copiar para `fixtures/maintenance/access/` (opcional).
3. Executar:

```bash
cd maintenance-api
set -a && source ../infra/.env && set +a
python scripts/import_access_csv.py \
  --motivos ../fixtures/maintenance/access/TabMotivo.csv \
  --status ../fixtures/maintenance/access/TabStatusPeca.csv \
  --reposicoes ../fixtures/maintenance/access/TabReposicoes.csv \
  --filial 01
```

Use `--dry-run` para validar contagem antes de gravar.

**Dev local (sem Access):** seed mínimo para testar relatório:

```bash
docker exec delpi-maintenance-api python scripts/bootstrap_dev_sample.py --filial 01
```

4. Validar preventiva: comparar ≥5 pares ferramenta/peça com WinForms.
5. Desligar escrita no Access; manter WinForms somente leitura até validação completa.

## Troubleshooting

| Sintoma | Ação |
|---------|------|
| Card «Status da API» com erro no portal | Conferir JWT, gateway e `GET /apps/maintenance-api/maintenance/health` |
| `db_ready: false` | Verificar migrations e variáveis `PLUGINS_DB_*` |
| Golpes zerados no relatório | api-delpi indisponível ou filial incorreta; conferir logs `maintenance-api` |
| 403 em mutação | RBAC filial — usuário precisa `maintenance.manage.filial-XX` ou `maintenance.replacements.manage` global |

## CI

```bash
./scripts/ci-maintenance-api.sh
cd plugins/maintenance && npm run build
```
