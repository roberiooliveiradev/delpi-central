# Contratos de integração — Transformômetro → outras aplicações

Na refatoração Playbook 18 (instâncias, UUID interno, escopo híbrido), **quem consome dados de processos/melhorias fora do plugin Transformômetro não fala com transformometro-api**.

**Fronteira pública:** **api-delpi** (`GET /engineering/transforma-mais/*`).  
**Backend interno:** transformometro-api (cadastro, cálculo, rotas S2S espelhadas).

---

## 1. Quem consome o quê

```text
                    ┌─────────────────────────────────────────┐
                    │  api-delpi  (contrato público)          │
                    │  GET /engineering/transforma-mais/      │
                    │       processes                         │
                    │       processes/summary                 │
                    │  envelope: success, message, data, meta │
                    └─────────────────┬───────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
  strategic-indicators-api    dashboard-engineering          chat / agentes
  (delpi_api_client)          (engineeringApi.ts)            (OpenAPI api-delpi)
  KPI TRANSFORMA+             TransformaPage / dashboard

                    ┌─────────────────────────────────────────┐
                    │  transformometro-api  (interno S2S)     │
                    │  …/integrations/engineering/transforma-mais/*
                    │  ← TransformometroApiClient + service token
                    └─────────────────────────────────────────┘
```

| Consumidor | Cliente | Nunca chama |
|------------|---------|-------------|
| Strategic Indicators | `DelpiApiClient.get_transforma_mais_summary` → api-delpi | transformometro-api |
| dashboard-engineering | `GET /engineering/transforma-mais/*` via gateway | transformometro-api |
| Plugin Transformômetro | JWT → `/transformometro/*` nativo | api-delpi (cadastro próprio) |
| Agente chat (Transforma+) | api-delpi OpenAPI ou snapshot TM (superfície separada) | — |

---

## 2. Contrato público (api-delpi)

**Dono do contrato:** `api-delpi` — OpenAPI, `route_contract_registry.py`, DTOs, smoke.

| Rota pública | operationId | Registry |
|--------------|-------------|----------|
| `GET /engineering/transforma-mais/processes` | `list_transforma_mais_processes` | `transforma_mais_process` / `paged_list` |
| `GET /engineering/transforma-mais/processes/summary` | `get_transforma_mais_summary` | `transforma_mais_summary` / `scalar` |

**Implementação api-delpi:**

| Camada | Arquivo |
|--------|---------|
| Rotas HTTP | `app/interface/http/routes/engineering/engineering_router.py` |
| Gateway | `app/infrastructure/gateways/transformometro_transforma_mais_gateway.py` |
| DTO listagem | `app/domain/entities/transforma_mais/process.py` → `Process.to_dict()` |
| DTO summary | `app/application/dto/transforma_mais/process_summary_response.py` |
| Meta KPI summary | `enrich_dashboard_metric` + `ENGINEERING_TRANSFORMA_MAIS` no router |

**Playbook 18:** alterações visíveis a SI/MFE passam por **api-delpi** (DTO + OpenAPI + smoke). Só depois alinhar mapper interno no transformometro-api.

### 2.1 Listagem — `data` em sucesso

```json
{
  "total": 1,
  "items": [
    {
      "id": "uuid",
      "name_process": "string",
      "filial_id": "01",
      "sector_name": "engenharia",
      "daily_savings": 0.0,
      "payback_months": 0.0,
      "status": "ativo",
      "implementetion_date": "2025-01-15"
    }
  ]
}
```

| Campo | Congelado | Notas |
|-------|-----------|-------|
| `id` | sim | **`instancia_id` UUID** (Playbook 18 S9) — uma linha por instância operacional |
| `implementetion_date` | sim | Typo legado — não renomear sem bump de contrato |
| `filial_id` | sim | **`codigo_filial`** (`01`, `02`) — não UUID |
| `sector_name` | sim | **`codigo_setor`** — não UUID |
| `processo_id` | aditivo | UUID do processo-mestre |
| `instancia_id` | aditivo | Igual a `id` quando presente |
| `codigo_processo` | aditivo | Código de negócio do mestre |

Query params públicos: `id`, `name_process`, `filial_id`, `sector_name`, `status`, `start_date`, `end_date`.

### 2.2 Summary — `data` em sucesso

Campos base (`ProcessSummaryResponse.to_dict()`):

- `implemented_solutions_count`, `total_net_savings_until_now`, `total_hours_saved_until_now`
- `total_gross_costs_until_now`, `total_gross_savings_in_period`, `average_roi`
- `monthly_breakdown[]`, `range_summary`

**Strategic Indicators** lê via api-delpi:

- Prioridade: `total_gross_savings_in_period`
- Fallback: soma de `monthly_breakdown[].gross_savings_month`

Query: `filial_id` (= branch `01`/`02`), `start_date`, `end_date`.

O summary na api-delpi pode incluir campos extras de `enrich_dashboard_metric` (metas/KPI) — também fazem parte do contrato observado pelo SI quando presentes.

---

## 3. Backend interno (transformometro-api)

Rotas S2S espelhadas para o gateway api-delpi:

- `GET /transformometro/integrations/engineering/transforma-mais/processes`
- `GET /transformometro/integrations/engineering/transforma-mais/processes/summary`

| Camada | Arquivo |
|--------|---------|
| Rotas | `tm_app/interface/http/routes/integrations_routes.py` |
| Mapper domínio → shape engenharia | `tm_app/application/integrations/engineering_transforma_mais.py` |
| Cliente HTTP | `shared/transformometro_client/client.py` |

**Regra:** o `data` devolvido ao transformometro-client deve continuar **compatível** com o que `TransformometroTransformaMaisGateway` mapeia para `Process` / `ProcessSummaryResponse`. Não é contrato para SI — é contrato **TM ↔ api-delpi**.

Testes TM: `tests/test_engineering_transforma_mais.py`.

### 3.1 Leitura rápida via cache (jun/2026)

Quando `dashboard_calculos` contém linhas (após `POST /transformometro/dashboard/recalcular`):

| Rota S2S | Fonte | Fallback |
|----------|-------|----------|
| `GET …/processes` | View `instancia_operacional_snapshot` | Cálculo live (`build_instancia_list`) |
| `GET …/processes/summary` | `query_resumo` + `query_evolucao` (view `dashboard_competencia_evolucao`) | Cálculo live (`build_summary`) |

- Filtros de data no summary são normalizados para competência `YYYY-MM` (`_normalize_competencia_bound`).
- Contrato `data` **inalterado** — só muda latência (~ms vs ~1s+).
- Views SQL: migration **V020**; modelo instância N:N setores: **V019**.

---

## 4. Playbook 18 — checklist de compatibilidade

Ordem de trabalho quando mudar domínio (instâncias, UUID):

1. **Cálculo/domínio** no transformometro-api.
2. **Mapper S2S** `engineering_transforma_mais.py` — mesmos campos que hoje (+ aditivos opcionais).
3. **Gateway api-delpi** — só se novos campos forem expostos publicamente; senão pass-through.
4. **DTOs api-delpi** — só campos aditivos até bump de versão.
5. **Smoke api-delpi** — `transforma-mais-summary` em `smoke_definitions.json`.
6. **SI / dashboard-engineering** — regressão KPI e telas Transforma+.

### Campos aditivos permitidos (sem bump)

Em `items[]`: `processo_id`, `instancia_id`, `codigo_processo`.

### Semântica de `id` na listagem (Playbook 18)

Uma linha por **instância operacional**; `id` = `instancia_id` (UUID); incluir `processo_id` (mestre) como aditivo. Comunicar em release notes — SI/dashboard contam linhas da listagem.

### Breaking change

- Bump explícito (OpenAPI / `dataVersion` / doc).
- PR coordenado: **transformometro-api + api-delpi + consumidores**.
- **Proibido:** mudar `data` da api-delpi só no TM sem passar pelo gateway/DTO.

---

## 5. Fora do contrato api-delpi Transforma+

| Superfície | Observação |
|------------|------------|
| CRUD `/transformometro/processos`, dashboard nativo | Plugin Transformômetro only |
| Snapshot chat / dashboard | `GET /transformometro/dashboard/snapshot/*` — agente via OpenAPI TM; contrato próprio |
| Instâncias operacionais (cache) | `GET /transformometro/dashboard/snapshot/instancias` — view `instancia_operacional_snapshot` |

---

## 6. Referências

| Doc / código | Caminho |
|--------------|---------|
| Playbook 18 | `docs/12-roadmap-e-evolucao/transformometro-app/PLAYBOOK-18-instancias-filial-setor-escopo.md` |
| Playbook contrato api-delpi | `minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md` |
| Inventário rotas | `api-delpi/docs/roadmaps/fase-0-inventario-contrato-respostas.md` |
| SI engenharia | `si_app/infrastructure/gateways/delpi_engineering_gateway.py` |
