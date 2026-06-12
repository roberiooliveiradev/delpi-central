# Arquitetura — Manutenção API (`maint_app`)

**Última atualização:** jun/2026 (Fases 0–2)

## Visão geral

```text
Portal (shell)
  └── MFE plugins/maintenance
        └── GET /apps/maintenance-api/maintenance/*
              └── maintenance-api (FastAPI, maint_app)
                    ├── Postgres plugins (reposições, motivos, status)
                    └── api-delpi via HTTP (ferramentas, peças, golpes TOTVS)
```

Produto e diagramas de contexto: [ARCHITECTURE.md produto](../../docs/12-roadmap-e-evolucao/maintenance/ARCHITECTURE.md).

## Componentes (alvo)

| Componente | Container (dev) | Responsabilidade |
|------------|-----------------|------------------|
| MFE | `delpi-maintenance` | UI React federada |
| API | `delpi-maintenance-api` | CRUD + preventiva + gateways |
| API Delpi | `delpi-api-delpi` | SQL Protheus — contrato único |
| Gateway nginx | `delpi-gateway` | Proxy `/apps/maintenance-api/` e `/apps/maintenance/` |
| Postgres | `delpi-postgres-plugins` | Schema `maintenance` |

## Pacote `maint_app` (estrutura alvo)

```text
maint_app/
  main.py
  config.py
  composition/maintenance_composer.py
  interface/http/routes/
    reposicao_routes.py
    motivo_routes.py
    status_routes.py
    preventiva_routes.py
    options_routes.py
  application/services/
    reposicao_service.py
    preventiva_service.py
  domain/
    entities/
    services/          # validadores puros
    ports/
      reposicao_repository_port.py
      mini_applicators_totvs_port.py
  infrastructure/
    persistence/repositories/
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

| Tabela | Fase |
|--------|------|
| `schema_migrations` | V001 |
| `motivos`, `reposicoes`, `status_peca`, `audit_logs` | V002 |
| Views de leitura (`vw_*`) | V007 |

### Views (V007)

Leituras paginadas e preventiva usam views em `maintenance` (constantes em `infrastructure/persistence/views.py`):

| View | Uso |
|------|-----|
| `vw_motivos_ativos` | Listagem de motivos (sem `excluido`) |
| `vw_status_peca_ativos` | Listagem de regras de status |
| `vw_reposicoes_detalhe` | Histórico da ferramenta com `motivo_descricao` |
| `vw_reposicoes_preventiva` | Reposições que entram no cálculo preventivo |
| `vw_reposicoes_ultima_por_par` | Última reposição preventiva por par filial/ferramenta/peça |

Escritas (`INSERT`/`UPDATE`/`soft_delete`) permanecem nas tabelas base.

Índices:

- `(filial, codigo_ferramenta, codigo_peca, data_reposicao DESC)` em `reposicoes` (parcial `excluido = FALSE`, V007)
- `(excluido)` parcial onde aplicável

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

## Testes

| Tipo | Onde |
|------|------|
| Validação reposição | `tests/test_reposicao_service.py` |
| Preventiva / status | `tests/test_preventiva_service.py` |
| Gateway (mock client) | `tests/test_delpi_mini_applicators_gateway.py` |
| Rotas paginadas / preventiva | `tests/test_preventiva_routes.py`, `tests/test_operational_status_routes.py` |
| CI monorepo | `scripts/ci-maintenance-api.sh` (37 testes) |

## Referências

- SI: `strategic-indicators-api/docs/ARCHITECTURE.md`
- TM: `transformometro-api/tm_app/`
- Playbook fronteiras: [PLAYBOOK-01](../../docs/12-roadmap-e-evolucao/maintenance/PLAYBOOK-01-fronteiras-api-delpi.md)
