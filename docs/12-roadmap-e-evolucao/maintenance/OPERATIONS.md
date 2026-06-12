# Operações — Manutenção (mini-aplicadores)

Runbook para equipe após go-live. Postgres (`maintenance` schema) é a fonte de verdade operacional; TOTVS continua via api-delpi.

## URLs (dev local)

| Recurso | URL |
|---------|-----|
| Portal | `http://localhost/apps/maintenance` |
| Mini-aplicadores | `/apps/maintenance/mini-aplicadores` |
| Relatório preventivo | `/apps/maintenance/mini-aplicadores/relatorio` |
| Configuração | `/apps/maintenance/mini-aplicadores/configuracao` |
| Home filial 01 | `/apps/maintenance/filial-01` |
| Home filial 02 | `/apps/maintenance/filial-02` |
| API health | `/apps/maintenance-api/maintenance/health` |

## Rotina diária

1. **Reposições** — registrar trocas de peça em Mini-aplicadores (filial 01 ou 02).
2. **Preventiva** — revisar ranking em Relatório preventivo (CRÍTICO / ATENÇÃO / OK).
3. **Configuração** — ajustar motivos e faixas de status quando necessário.
4. Cadastro oficial somente no portal (sem Access após migração).

## Deploy / upgrade

### Produção (`minhadelpi.com.br`)

Sintoma típico: home do módulo com `Unexpected token '<'` — o gateway ainda não roteia `/apps/maintenance-api/` (resposta = HTML do portal).

```bash
cd /path/to/delpi-central
git pull

docker compose -f infra/docker-compose.yml --env-file infra/.env build maintenance-api maintenance gateway
docker compose -f infra/docker-compose.yml --env-file infra/.env up -d --force-recreate maintenance-api maintenance gateway

# Smoke (deve retornar JSON, não HTML)
bash scripts/homologacao/check-maintenance-prod.sh
# ou: curl -s https://minhadelpi.com.br/apps/maintenance-api/maintenance/health | head -c 80
```

Re-registrar manifest **v0.2.1** na Core API se permissões/rotas ainda não foram atualizadas.

**Gateway:** locations de API devem enviar `Cache-Control: no-store` (commit `e38ff14c` e posteriores). Sem isso, CDN/proxy pode devolver HTML do portal em `/apps/maintenance-api/*`.

### Dev local

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

O **manifesto** registra o app e declara permissões/rotas. Rotas internas usam `"showInMenu": false` — o menu lateral do portal mostra só o tile **Manutenção**; filial e submódulos ficam no MFE.

```bash
export TOKEN="<jwt com apps.manage>"
export BASE_URL="http://localhost"
./plugins/maintenance/scripts/register-manifest.sh
```

Permissões canônicas (ver `maintenance.manifest.json` v0.2.1):

| Permissão | Uso |
|-----------|-----|
| `maintenance.view` | Abrir o módulo (início) |
| `maintenance.manage` | Cadastro de filiais (`/apps/maintenance/filiais`) |
| `maintenance.mini-applicators.view.filial-01` / `02` | Ler ferramentas, relatório e histórico na filial |
| `maintenance.mini-applicators.manage.filial-01` / `02` | Reposições, motivos e status preventivo na filial |
| `maintenance.manutencao-geral.view.filial-01` | Formulário manutenção geral (filial 01) |

Fluxo: escolher filial no **Início** (se houver mais de uma); submódulos visíveis conforme `mini-applicators.view.filial-XX`; mutações exigem `mini-applicators.manage.filial-XX` da filial ativa. Após alterar permissões na Core API, o usuário deve **logout/login**.

**Não usar** permissões genéricas fora do manifesto (`maintenance.view.filial-XX`, `maintenance.manage.filial-XX`, `maintenance.mini-applicators.view` sem sufixo de filial) — a API não as mapeia para escopo.

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
| 403 em mutação | RBAC — usuário precisa `maintenance.mini-applicators.manage.filial-XX` da filial escolhida no início |
| Aba Configuração não aparece | Falta `mini-applicators.manage.filial-XX` ou manifesto desatualizado na Core API |
| Tabela mostra só 50 ferramentas | Rebuild do MFE — lista usa paginação server-side (`page_size=20`) |
| «Falha na requisição» genérico no relatório | Conferir JWT e permissão `mini-applicators.view.filial-XX`; resposta 403/401 agora exibe `detail` do FastAPI. Typo histórico em `_SUBMODULE_ID` (`mini-aplicadores`) causava 403 silencioso — corrigido |
| Select de peça lista componentes | Rebuild API + MFE — reposição usa `/pecas` (`3019*`); estoque usa `/componentes` |
| Checkbox do multi-select enorme | Rebuild MFE — override CSS em `.dm-multi-select__option input[type="checkbox"]` |

## CI

```bash
./scripts/ci-maintenance-api.sh
cd plugins/maintenance && npm run build
```
