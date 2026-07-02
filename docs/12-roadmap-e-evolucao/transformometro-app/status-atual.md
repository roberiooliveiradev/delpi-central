# Status atual — Transformômetro

Atualizado: **jul/2026** (instância = ambiente isolado; economia do processo = **média das instâncias ativas** — motor, cache/views V021).

> **Regra jul/2026 — média por instância.** Cada instância tem baseline/parâmetros próprios. A economia consolidada de um processo é a **média aritmética das instâncias ativas no mês** (`Σ economia_instância / nº_instâncias_ativas`); investimento, horas e ROI seguem a mesma média. Recorte por unidade/setor mostra o **valor real** da instância (média de 1 = ela mesma). Fonte da regra: `transformometro-api/docs/regras-de-calculo.md`.

## Fonte de dados e pipeline (runtime)

| Camada | Papel |
|--------|-------|
| **Postgres** (`schema transformometro`) | Fonte de verdade — cadastro, cache `dashboard_calculos`, views V020 |
| **transformometro-api** | CRUD, cálculo, recalc, integração S2S |
| **plugins/transformometro** | UI oficial de cadastro e dashboard |
| **api-delpi** | Contrato público `GET /engineering/transforma-mais/*` → `TransformometroTransformaMaisGateway` |
| **strategic-indicators-api** | KPI Transforma+ via `DelpiEngineeringGateway` → api-delpi |
| **dashboard-engineering** | `TransformaPage` (read-only) → api-delpi |

**Não participam do pipeline:** planilha Google Sheets, `ProcessSummaryCalculator`, `api-delpi/.../google_sheets/transforma_mais/process_repository.py` (código morto).

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
| **Média por instância** (motor + cache) | ✅ jul/2026; `_calculate_monthly_series` por instância, `calc_rules` divide por `instancias_ativas_mes`, cache/views **V021** (agregação 2 níveis) |
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

Com `TM_RUN_MIGRATIONS_ON_STARTUP=true` (padrão no compose e `infra/.env`), o container **`delpi-transformometro-api`** aplica V001–V021 pendentes no **startup** (`run_migrations_on_startup` no lifespan FastAPI). Falha de migration **impede** a API de subir.

> **V021** redefine `processo_competencia_snapshot` e `dashboard_competencia_evolucao` com a média por instância (agregação em 2 níveis). Após aplicar, rodar **recalc full** para o cache refletir a nova regra.

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

## Verificação ambiente dev (jun/2026)

Com `docker compose ... up` no stack local:

- Migrations **V001–V020** aplicadas (`migrations_runner status`)
- Integração S2S `GET .../integrations/engineering/transforma-mais/processes` retorna instâncias do Postgres (IDs UUID)
- api-delpi `GET /engineering/transforma-mais/*` responde 200 via gateway interno

```bash
docker exec delpi-transformometro-api python -m tm_app.infrastructure.persistence.plugins.migrations_runner status
docker exec delpi-api-delpi python -c "
import os, urllib.request, json
t = os.environ['API_DELPI_INTERNAL_SERVICE_TOKEN']
u = 'http://transformometro-api:8000/transformometro/integrations/engineering/transforma-mais/processes'
r = urllib.request.urlopen(urllib.request.Request(u, headers={'X-Delpi-Service-Token': t}))
d = json.loads(r.read())['data']
print('total instancias:', d.get('total'), 'items:', len(d.get('items') or []))
"
```

## Pendente (operacional)

| Item | Responsável |
|------|-------------|
| Deploy produção com runbook acima | Ops |
| Atribuir permissões escopadas na Core API / Portal RBAC (quem precisar) | Ops |
| Planilha somente leitura | Google Workspace |
| Limpeza código morto Sheets na api-delpi (Fase 6) | Dev |

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
