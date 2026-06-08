# Limpeza de legado — Strategic Indicators API

**Última atualização:** 2026-06-04

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
| Sheets Transforma+ legado | `si_app/infrastructure/persistence/google_sheets/transforma_mais/**` | Engenharia usa `TransformometroTransformaMaisGateway` |
| Port morto | `si_app/domain/ports/transforma_mais/process_query_port.py` | Só referenciado pelo `ProcessRepository` removido |
| Factories HTTP antigas | `build_get_*` não importados em `financial_composer`, `production_composer`, `quality_composer` | Restos das rotas departamentais da api-delpi |
| Dependência | `pyodbc` em `requirements.txt` | Só TOTVS direto no SI |
| Imagem Docker | `unixodbc`, `msodbcsql18`, toolchain ODBC no `Dockerfile` | Só para pyodbc |
| Config / compose | `TOTVS_*`, `DB_HOST`→TOTVS no serviço `strategic-indicators-api` | SI não conecta mais ao SQL Server |
| Docs | `CODE_STRUCTURE`, `DEPLOYMENT`, `OPERATIONS`, `PERFORMANCE_IMPLEMENTATION` | Remover referências ao pool TOTVS **no SI** |

**Testes:** suite `strategic-indicators-api/tests/` — nenhum teste importa `persistence.totvs`.

**Não remover na fase 1:**

- Gateways `delpi_*`, use cases e DTOs departamentais usados pelos snapshot providers.
- Portal RH (`persistence/portal_rh/`).

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

**Pendente:** extrair contratos idênticos para `shared/`; RH via HTTP no SI.

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
