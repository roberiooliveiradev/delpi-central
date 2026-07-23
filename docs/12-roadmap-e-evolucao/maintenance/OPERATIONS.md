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

**V006 (UUID):** converte `motivos.motivo_id` e `status_peca.status_id` de serial para UUID (reposições já usavam UUID). Em banco novo (V002 atualizado), V006 é no-op. Após upgrade, IDs numéricos deixam de existir na API — o MFE não exibe coluna ID.

**V007 (views):** cria views `vw_motivos_ativos`, `vw_status_peca_ativos`, `vw_reposicoes_detalhe`, `vw_reposicoes_preventiva`, `vw_reposicoes_ultima_por_par` e índice parcial em `reposicoes`. Repositórios de leitura usam as views — recriar `maintenance-api` após deploy para aplicar a migration.

**V008 (revisão programada):** tabela `revisao_programada` + view `vw_revisao_programada_ativos` — agenda por ferramenta (intervalo em meses, data de referência).

**V009 (realizações):** tabela `revisao_programada_realizacao` — histórico de marcações «feito» com data customizada.

**V010 (auditoria):** índice parcial `idx_audit_logs_filial_ferramenta_data` em `audit_logs` para timeline por ferramenta.

## Auditoria operacional (ferramenta)

Mutações de **reposição** e **revisão programada** (incluindo marcar feito, editar e remover realizações) gravam em `maintenance.audit_logs`:

| Campo | Valor típico |
|-------|----------------|
| `entidade` | `ferramenta` |
| `entidade_id` | código da ferramenta |
| `acao` | ex.: `reposicao.create`, `revisao_programada.registrar`, `revisao_realizacao.delete` |
| `filial` | `01` ou `02` |
| `usuario_sub` | subject do JWT |
| `payload` | JSON com ids e campos relevantes (peça, golpes, datas, etc.) |

**Consulta:** `GET /maintenance/mini-aplicadores/ferramentas/{codigo}/auditoria?filial=01&page=1&page_size=10` — exige `mini-applicators.view.filial-XX`.

**UI:** seção «Auditoria da ferramenta» no detalhe do mini-aplicador (`FerramentaAuditoriaSection`).

**Importante:** eventos aparecem **a partir das mutações após o deploy** — histórico anterior ao go-live da feature não é retroativo.

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
| `maintenance.programas-maquinas.view.filial-01` / `02` | Ranking e consulta de produtos para programas de máquina |
| `maintenance.programas-maquinas.manage.filial-01` / `02` | Cadastrar/remover produtos dos programas de máquina |
| `maintenance.manutencao-geral.view.filial-01` | Abrir formulário Manutenção geral (só filial 01 hoje) |

Fluxo: escolher filial no **Início** (se houver mais de uma); submódulos visíveis conforme permissão `*.view.filial-XX` de cada submódulo; mutações exigem `*.manage.filial-XX` da filial ativa. Após alterar permissões na Core API, o usuário deve **logout/login**.

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
| Select de peça lista mais itens que componentes | Rebuild API + MFE — `/pecas` e select derivam da árvore `/componentes` (3019*), não de vínculos SG1010 expirados |
| Checkbox do multi-select enorme | Rebuild MFE — override CSS em `.dm-multi-select__option input[type="checkbox"]` |
| Auditoria vazia no detalhe da ferramenta | Normal se não houve mutação após deploy; conferir V010 aplicada e permissão `view.filial-XX` |
| 500 em `/revisoes-programadas/realizacoes` | Rebuild API — listagem usa `fetch_paged` com argumentos nomeados (commit `91796098`) |
| Referência de revisão «volta» após editar feito | Esperado — API recalcula `data_ultima_revisao` pela realização mais recente |

## CI

```bash
./scripts/ci-maintenance-api.sh
cd plugins/maintenance && npm run build
```
