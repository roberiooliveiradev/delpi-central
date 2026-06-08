# Limpeza de legado — Strategic Indicators API

**Última atualização:** 2026-06-08

Documento de referência para remover código herdado da api-delpi que o SI **não usa mais** após a migração HTTP (maio/2026).

## Contexto

O `strategic-indicators-api` nasceu como cópia podada da api-delpi. Hoje:

- **HTTP público:** só `/strategic-indicators/*` e integração de metas (`/integrations/dashboard-goals`).
- **Medições TOTVS:** 100% via `delpi_*_gateway` + `DelpiApiClient`.
- **Medições Sheets:** 100% via api-delpi HTTP (gateways `delpi_*`).

## Fases

### Fase 1 — Remoção segura (sem mudar comportamento do painel)

**Objetivo:** apagar código morto e dependências que não entram no grafo de execução dos snapshots.

| Item | Caminho / artefato | Motivo |
|------|-------------------|--------|
| Repositórios TOTVS | `si_app/infrastructure/persistence/totvs/**` | Substituídos por gateways HTTP; composers não injetam mais |
| Pool TOTVS / pyodbc | `si_app/infrastructure/providers/totvs/**` | Só usado pelos repos TOTVS |
| Sheets Transforma+ legado | `si_app/infrastructure/persistence/google_sheets/transforma_mais/**` | Engenharia via `GET /engineering/transforma-mais/*` (api-delpi) |
| Port morto | `si_app/domain/ports/transforma_mais/process_query_port.py` | Só referenciado pelo `ProcessRepository` removido |
| Factories HTTP antigas | `build_get_*` não importados em `financial_composer`, `production_composer`, `quality_composer` | Restos das rotas departamentais da api-delpi |
| Dependência | `pyodbc` em `requirements.txt` | Só TOTVS direto no SI |
| Imagem Docker | `unixodbc`, `msodbcsql18`, toolchain ODBC no `Dockerfile` | Só para pyodbc |
| Config / compose | `TOTVS_*`, `DB_HOST`→TOTVS no serviço `strategic-indicators-api` | SI não conecta mais ao SQL Server |
| Docs | `CODE_STRUCTURE`, `DEPLOYMENT`, `OPERATIONS`, `PERFORMANCE_IMPLEMENTATION` | Remover referências ao pool TOTVS **no SI** |

**Testes:** suite `strategic-indicators-api/tests/` — nenhum teste importa `persistence.totvs`.

**Não remover na fase 1:**

- Gateways `delpi_*`, use cases e DTOs departamentais usados pelos snapshot providers.
- ~~Portal RH (`persistence/portal_rh/`)~~ removido na fase 5.

**Fase 2 concluída:** SI não lê mais Google Sheets localmente; planilhas só na api-delpi.

---

### Fase 2 — Alinhar Google Sheets via api-delpi HTTP

**Objetivo:** uma única fonte de leitura de planilhas (api-delpi), como já feito para suprimentos (`/supplies/negotiation-savings/summary`).

| Departamento | Hoje no SI | Migrar para (api-delpi) |
|--------------|------------|--------------------------|
| Qualidade | ~~`KaizenRepository`, `Audit5SRepository` local~~ **feito jun/2026** | `GET /quality/kaizens/summary`, `GET /quality/audit-5s/summary` |
| Financeiro | ~~Sheets locais~~ **feito jun/2026** | `GET /financial/ebitda_pct`, `/fixed_cost_pct`, `/pmr` |
| Produção | ~~Sheets locais~~ **feito jun/2026** | `GET /production/direct_labor_cost_pct`, `/production_cost_pct`, `/depreciation_pct` |

**Passos por indicador:**

1. Garantir rota estável na api-delpi (já existe na maioria).
2. Criar/estender gateway no SI (padrão `DelpiNegotiationSavingsGateway`).
3. Trocar composer do departamento para usar gateway em vez de `persistence/google_sheets`.
4. Remover repositório Sheets duplicado no SI.
5. Atualizar `DATA_SOURCES.md` e testes de snapshot.

**Risco:** diferenças sutis de normalização de datas/filiais entre SI e api-delpi — validar com testes de regressão em `tests/fixtures/` ou casos em `test_*_snapshot*.py`.

---

### Fase 3 — Enxugar camada duplicada (concluída jun/2026)

**Objetivo:** reduzir cópia estrutural da api-delpi mantendo só o necessário para snapshots.

**Removido:**

- Use cases departamentais sem rota HTTP no SI (financial `get_*_pct`, production `get_*_pct`, `list_ppm`, `list_nonconformity`, commercial `new_clients_*`, LMP `list/get` fora do snapshot).
- Ports/entidades/DTOs órfãos (repos de produção Sheets, nonconformity, new clients).
- Gateways mortos (`DelpiNonconformityGateway`, `DelpiNewClients*Gateway`) e factories não usadas nos composers.

**Mantido (ainda no grafo de snapshots):** use cases finos em qualidade/comercial/suprimentos que encapsulam gateways — refatorar para chamada direta nos services fica como melhoria futura opcional.

---

### Fase 4 — Limpeza na api-delpi (concluída jun/2026 — snapshot services mortos)

**Objetivo:** remover cópias legadas no serviço de dados que o SI já não consome diretamente.

| Item | api-delpi | Motivo |
|------|-----------|--------|
| `*_metrics_snapshot_service` departamentais | commercial, production, quality, supplies, engineering | Builders existiam nos composers mas **nenhuma rota HTTP** usava; agregação ficou só no SI |
| Mantidos | `financial_metrics_snapshot_service`, `hr_metrics_snapshot_service` | Rotas `/financial/ebitda_pct`, `/pmr`, `/hr/*` |

**Concluído (jun/2026):** `period_resolution` movido para `si_app/application/services/strategic_indicators/`.

### Fase 5 — RH via HTTP no SI (concluída jun/2026)

**Objetivo:** lógica Portal RH só na api-delpi; SI consome `GET /hr/snapshot`.

| Removido no SI | Substituído por |
|----------------|-----------------|
| `persistence/portal_rh/**` | `DelpiHrGateway` + `DelpiApiClient.get_hr_snapshot` |
| `providers/database/portal_rh_postgres_connection.py` | — |
| `PORTAL_RH_DB_*` no compose/config do SI | `DELPI_API_URL` (já usado pelos demais gateways) |

**Mantido na api-delpi:** `HrMetricsRepository`, rotas `/hr/*`.

### Fase 6 — Remoção de código morto + `delpi_domain` revertido (jun/2026)

| Item | Onde ficou | Removido |
|------|------------|----------|
| `spreadsheet_date.py` | **só api-delpi** (`app/shared/utils/`) | cópia no SI; pacote `shared/delpi_domain` |
| Contrato RH (`Hr*Snapshot`) | **só api-delpi** (`app/application/dto/hr/`) | SI parse local em `infrastructure/http/hr_snapshot_models.py` |
| `process_summary_calculator.py` | — (código morto) | ~1130 LOC × 2 em `domain/services/transforma_mais/` |

**Decisão:** DTOs/entidades departamentais **não** vão para `shared/` — ficam na api-delpi; o SI consome JSON HTTP.

### Fase 7 — Gateways HTTP puros no SI (concluída jun/2026)

**Objetivo:** SI consome api-delpi **somente via HTTP**; lógica de negócio departamental fica em `*_metrics_snapshot_service` ou `*_metrics_helpers.py`.

| Removido no SI | Substituído por |
|----------------|-----------------|
| DTOs/entidades/ports/use cases departamentais (suprimentos, financeiro, produção, comercial, qualidade, engenharia) | Gateways `Delpi*Gateway` com kwargs (`branch`, `start_date`, `end_date`) retornando `dict`/`float` |
| Múltiplas classes por domínio (`DelpiCpvGateway`, `DelpiOeeGateway`, …) | Uma classe por departamento: `DelpiSuppliesGateway`, `DelpiProductionGateway`, `DelpiCommercialGateway`, `DelpiQualityGateway`, `DelpiEngineeringGateway` |
| Use cases finos (`GetCPVUseCase`, `GetPpmSummaryUseCase`, …) | `supplies_metrics_helpers.py`, `engineering_metrics_helpers.py`; snapshot services chamam gateways direto |
| `shared/delpi_domain/` (já ausente) | Contratos HTTP em `si_app/infrastructure/http/` (ex.: `hr_snapshot_models.py`) |

**Mantido:** `si_app/application/dto/strategic_indicators/`, `si_app/domain/ports/strategic_indicators/`, `si_app/application/use_cases/strategic_indicators/`, `services/strategic_indicators/period_resolution.py`.

**api-delpi:** rotas e shapes de resposta **inalterados** (consumidores externos intactos).

### Fase 8 — Engenharia só via api-delpi HTTP (concluída jun/2026)

**Objetivo:** SI não calcula LMP localmente nem chama transformometro-api direto; engenharia consome apenas rotas `/engineering/*` da api-delpi.

| Removido no SI | Substituído por |
|----------------|-----------------|
| `lmp_business_rules.py` (~250 LOC) | `GET /engineering/lmps/dashboard/summary` |
| `get_lmp_dashboard_rows` + fallback `_from_rows` | `DelpiEngineeringGateway.get_lmp_dashboard_summary` |
| `TransformometroTransformaMaisGateway` | `GET /engineering/transforma-mais/processes/summary` |
| `services/lmp/*` (caches legados) | `engineering/engineering_lmp_summary_cache.py` |
| `TRANSFORMOMETRO_API_BASE_URL` no compose do SI | `DELPI_API_URL` (já usado) |

**Mantido na api-delpi:** `lmp_business_rules`, repos TOTVS, proxy Transformometro nas rotas `/engineering/*`.

**delpi_api_client:** `get_transforma_mais_summary()` adicionado.

### Housekeeping pós-fase 8 (concluído jun/2026)

| Item | Ação |
|------|------|
| `period_resolution.py` | Movido para `application/services/strategic_indicators/` |
| `financial_sheet_scope.py` | Removido; `FINANCIAL_CONSOLIDATED_BRANCH_KEY` em `shared/branch_filter.py` |
| PPM Qualidade `null` vs `0.0` | `_resolve_ppm` e provider sem `default_value=0.0` |
| `has_transformometro_*` | Substituído por `has_stale_period_snapshot_errors` |
| Compose | `api-delpi` com healthcheck; SI aguarda `service_healthy` (sem ciclo com api-delpi) |
| Docs | `DATA_SOURCES.md`, `LEGACY_CLEANUP.md` atualizados |

---

## Checklist pós-fase 1

```bash
cd strategic-indicators-api
PYTHONPATH=. pytest tests/ -q

# Container sem ODBC (rebuild)
cd ../infra
docker compose build strategic-indicators-api
docker compose up -d --force-recreate strategic-indicators-api
```

Validar no painel: árvore de departamentos e indicadores de Suprimentos/Comercial/Produção (fontes via api-delpi) continuam carregando.

## Referências

- [ARCHITECTURE.md](./ARCHITECTURE.md) — gateways HTTP
- [DATA_SOURCES.md](./DATA_SOURCES.md) — fontes por departamento
- [CODE_STRUCTURE.md](./CODE_STRUCTURE.md) — pacote `si_app`
