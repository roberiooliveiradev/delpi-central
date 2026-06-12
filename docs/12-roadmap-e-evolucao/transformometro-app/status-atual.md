# Status atual — Transformômetro

Atualizado: **jun/2026** (Playbook 18 S1–S12 — instâncias N setores, views cache, Transforma+ acelerado).

## Entregue

| Área | Status |
|------|--------|
| API + migrations **V001–V020** | ✅ Auto no boot (`TM_RUN_MIGRATIONS_ON_STARTUP=true`) |
| Processo-mestre + **instâncias** (filial + N setores) | ✅ V013–V015 + **V019**; painel MFE multi-setor |
| **CRUD filiais** + editar/excluir instância | ✅ MFE `FiliaisPage` + `PUT/DELETE /instancias/{id}` |
| Filiais / setores **UUID** + `codigo_*` | ✅ V011–V012; CRUD + options |
| Revisões por instância + URL canônica | ✅ V014/V018; redirect legado no MFE |
| **Escopo híbrido** `escopo_recurso` | ✅ V016; formulário Recursos + calculador |
| Cache dashboard UUID + denorm | ✅ V017; recalc obrigatório pós-migration |
| **Views leitura rápida** | ✅ V020; snapshot instâncias + evolução mensal |
| **Transforma+ S2S via cache** | ✅ `engineering_transforma_mais.py` (fallback live) |
| Visões dashboard `view` | ✅ API + toggle MFE + `access_scope` |
| Duplicar **instância** (replicar timeline) | ✅ `POST /instancias/{id}/duplicar` |
| Integração Transforma+ por instância | ✅ `id` = `instancia_id` |
| **RBAC filial** server-side | ✅ S10; manifesto com permissões escopadas |
| CRUD completo + dashboard Fase 4 | ✅ |
| Backup JSON 1.1 | ✅ bundles `filiais`, `processo_instancias`, `processo_instancia_setores` |
| Testes API | ✅ `scripts/ci-transformometro-api.sh` (123+) |
| Build MFE | ✅ Docker build `transformometro` |
| Documentação Playbook 18 | ✅ modelagem, arquitetura, regras de cálculo, status |

## Migrations automáticas

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose e `infra/.env`), o container **`delpi-transformometro-api`** aplica V001–V020 pendentes no **startup** (`run_migrations_on_startup` no lifespan FastAPI). Falha de migration **impede** a API de subir.

Conferir:

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
```

## Pós-deploy Playbook 18 (obrigatório na 1ª vez)

1. **Backup JSON** do cadastro atual (`import_cadastro_json.py export`).
2. Rebuild + recreate `transformometro-api` + `transformometro`.
3. Migrations sobem sozinhas; validar `status` até **V020**.
4. **Bootstrap filiais** (V011 não faz seed):  
   `python scripts/bootstrap_filiais_from_cadastro.py -i fixtures/cadastro/...json`
5. **Recalc full** do dashboard (obrigatório após V017/V019/V020): Dashboard → Recalcular ou `POST /transformometro/dashboard/recalcular`.
6. Registrar manifesto atualizado (`register-manifest.sh`) — permissões RBAC filial + rota `/filiais`.
7. Smoke: dashboard (3 visões), processo → instâncias → revisão URL canônica, Transforma+ summary (<500ms com cache).

Detalhe: [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md) · [OPERATIONS.md](./OPERATIONS.md).

## Pendente (operacional)

| Item | Responsável |
|------|-------------|
| Deploy produção com runbook acima | Ops |
| Atribuir permissões escopadas no Keycloak (quem precisar) | Ops |
| Planilha somente leitura | Google Workspace |

## Variáveis de produção (checklist)

```bash
API_DELPI_INTERNAL_SERVICE_TOKEN=<mesmo valor em api-delpi, SI, transformometro-api>
TRANSFORMOMETRO_API_BASE_URL=http://transformometro-api:8000
TM_RUN_MIGRATIONS_ON_STARTUP=true
PLUGINS_DB_*=<postgres-plugins>
```

## Comandos úteis

```bash
cd ~/projetos/delpi-central
git pull
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env build transformometro-api transformometro
docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up -d --force-recreate transformometro-api transformometro

./scripts/ci-transformometro-api.sh
cd plugins/transformometro && npm run build   # ou build via Docker

export TOKEN="..." BASE_URL="https://www.minhadelpi.com.br"
./plugins/transformometro/scripts/register-manifest.sh
```

## Referências

- [PLAYBOOK-18-instancias-filial-setor-escopo.md](./PLAYBOOK-18-instancias-filial-setor-escopo.md)
- [PLAYBOOK-MODELAGEM.md](./PLAYBOOK-MODELAGEM.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [ROADMAP.md](./ROADMAP.md)
- [OPERATIONS.md](./OPERATIONS.md)
- [regras-de-calculo.md](../../../transformometro-api/docs/regras-de-calculo.md)
- [playbook-18-implementation-status.md](../../../transformometro-api/docs/playbook-18-implementation-status.md)
- [DEPLOYMENT.md](../../../transformometro-api/docs/DEPLOYMENT.md)
