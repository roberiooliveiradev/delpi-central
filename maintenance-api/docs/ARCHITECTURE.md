# Arquitetura — Manutenção API (`maint_app`)

**Última atualização:** jun/2026 (revisão programada + auditoria da ferramenta)

## Visão geral

```text
Portal (shell)
  └── MFE plugins/maintenance
        └── GET /apps/maintenance-api/maintenance/*
              └── maintenance-api (FastAPI, maint_app)
                    ├── Postgres plugins (reposições, motivos, status, revisão, audit)
                    └── api-delpi via HTTP (ferramentas, peças, golpes TOTVS)
```

Produto e diagramas de contexto: [ARCHITECTURE.md produto](../../docs/12-roadmap-e-evolucao/maintenance/ARCHITECTURE.md).

## Componentes (alvo)

| Componente | Container (dev) | Responsabilidade |
|------------|-----------------|------------------|
| MFE | `delpi-maintenance` | UI React federada |
| API | `delpi-maintenance-api` | CRUD + preventiva + revisão programada + audit + gateways |
| API Delpi | `delpi-api-delpi` | SQL Protheus — contrato único |
| Gateway nginx | `delpi-gateway` | Proxy `/apps/maintenance-api/` e `/apps/maintenance/` |
| Postgres | `delpi-postgres-plugins` | Schema `maintenance` |

## Pacote `maint_app` (estrutura alvo)

```text
maint_app/
  main.py
  config.py
  core/auth_actor.py
  composition/maintenance_composer.py
  interface/http/
    audit_http.py
    routes/
      operational_routes.py
      mini_applicators_routes.py
      preventiva_routes.py
      ...
  application/services/
    reposicao_service.py
    preventiva_service.py
    revisao_programada_service.py
  domain/
    entities/
    services/
    ports/
      mini_applicators_totvs_port.py
  infrastructure/
    persistence/repositories/
      operational_repositories.py
      audit_repository.py
    gateways/delpi_mini_applicators_gateway.py
  infrastructure/persistence/migrations_runner.py
```

## Gateways api-delpi

| Gateway | Port | Endpoints |
|---------|------|-----------|
| `delpi_mini_applicators_gateway.py` | `MiniApplicatorsTotvsPort` | `/engineering/mini-applicators/*` |

Fluxo (igual SI):

1. Composer instancia `DelpiApiClient` + gateway.
2. Service de aplicação depende do **port**, não do client.
3. JWT propagado: `bearer_authorization_from_context()`.

Variáveis: `DELPI_API_URL`, `DELPI_API_TIMEOUT`.

## Postgres

| Tabela / objeto | Migration |
|-----------------|-----------|
| `schema_migrations` | V001 |
| `motivos`, `reposicoes`, `status_peca`, `audit_logs` | V002 |
| Config por filial | V003–V005 |
| UUID motivos/status | V006 |
| Views de leitura (`vw_*`) | V007 |
| `revisao_programada`, `vw_revisao_programada_ativos` | V008 |
| `revisao_programada_realizacao` | V009 |
| Índice audit por ferramenta | V010 |

### Views (V007+)

Leituras paginadas e preventiva usam views em `maintenance` (constantes em `infrastructure/persistence/views.py`):

| View | Uso |
|------|-----|
| `vw_motivos_ativos` | Listagem de motivos (sem `excluido`) |
| `vw_status_peca_ativos` | Listagem de regras de status |
| `vw_reposicoes_detalhe` | Histórico da ferramenta com `motivo_descricao` |
| `vw_reposicoes_preventiva` | Reposições que entram no cálculo preventivo |
| `vw_reposicoes_ultima_por_par` | Última reposição preventiva por par filial/ferramenta/peça |
| `vw_revisao_programada_ativos` | Agendas de revisão por ferramenta |

Escritas (`INSERT`/`UPDATE`/`soft_delete`) permanecem nas tabelas base.

### Auditoria (`audit_logs`)

| Campo | Descrição |
|-------|-----------|
| `entidade` | Fixo `ferramenta` para timeline no detalhe |
| `entidade_id` | Código da ferramenta |
| `acao` | `reposicao.create`, `revisao_programada.registrar`, etc. |
| `payload` | JSON com ids e campos da mutação |
| `usuario_sub` | Subject JWT |

Gravação: `log_ferramenta_audit()` em `interface/http/audit_http.py` — chamado após mutações em `operational_routes.py`. Falha no audit não reverte a operação.

Leitura: `GET /maintenance/mini-aplicadores/ferramentas/{codigo}/auditoria` → `AuditRepository.list_by_ferramenta_paged()`.

Índices:

- `(filial, codigo_ferramenta, codigo_peca, data_reposicao DESC)` em `reposicoes` (parcial `excluido = FALSE`, V007)
- `(filial, entidade_id, data_criacao DESC)` em `audit_logs` where `entidade = 'ferramenta'` (V010)

## Envelope HTTP

Respostas via helper compartilhado (`shared` ou cópia do padrão TM/SI):

```json
{ "success": true, "message": "...", "data": { } }
```

Erros de validação: `success: false`, HTTP 4xx, mensagem clara (PT via content bundle quando houver UI).

## Listagens paginadas

| Módulo | Arquivo |
|--------|---------|
| Normalização | `application/list_query.py` — `ListQuery`, `normalize_list_query`, `paginate_slice` |
| FastAPI deps | `interface/http/list_query_params.py` — `page`, `page_size`, `sort_by`, `sort_dir` |

Resposta típica em `data`: `{ "items": [...], "total": N }`.

### Rotas operacionais relevantes

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET/POST/PUT/DELETE` | `/maintenance/reposicoes` | CRUD reposições |
| `GET/POST/PUT/DELETE` | `/maintenance/revisoes-programadas` | Agenda por ferramenta |
| `POST` | `/maintenance/revisoes-programadas/{id}/registrar` | Marcar revisão feita |
| `GET/PUT/DELETE` | `/maintenance/revisoes-programadas/realizacoes` | Histórico editável |
| `GET` | `/maintenance/mini-aplicadores/ferramentas/{codigo}/auditoria` | Timeline audit |

## Testes

| Tipo | Onde |
|------|------|
| Validação reposição | `tests/test_reposicao_service.py` |
| Preventiva / status | `tests/test_preventiva_service.py` |
| Revisão programada | `tests/test_revisao_programada_service.py` |
| Auditoria | `tests/test_audit_repository.py`, `test_audit_http.py`, `test_audit_routes.py` |
| Gateway (mock client) | `tests/test_delpi_mini_applicators_gateway.py` |
| Rotas paginadas / preventiva | `tests/test_preventiva_routes.py`, `tests/test_operational_status_routes.py` |
| CI monorepo | `scripts/ci-maintenance-api.sh` (**56 testes**) |

## Referências

- SI: `strategic-indicators-api/docs/ARCHITECTURE.md`
- TM: `transformometro-api/tm_app/` (padrão `audit_logs`)
- Playbook fronteiras: [PLAYBOOK-01](../../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md)
- Runbook: [OPERATIONS.md](../../docs/12-roadmap-e-evolucao/maintenance/OPERATIONS.md)
