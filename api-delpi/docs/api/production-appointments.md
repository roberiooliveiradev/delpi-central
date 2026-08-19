# Apontamento de Produção — `/production/appointments`

**Status:** implementado (jul/2026)  
**Plugin previsto:** `production-appointments` (nome portal: Apontamento de Produção)  
**Spec / Fase 0:** [`docs/12-roadmap-e-evolucao/production-appointments/`](../../../docs/12-roadmap-e-evolucao/production-appointments/)

Acompanha apontamentos de produção (`SH6010`, tipo `P`) por centro de trabalho via `SH1010` → `SHB010`.

No **painel**, `totals.qty_produced` (KPI Qtd. produzida) e a série agregada por dia/mês somam só a **última operação do roteiro** (`SG2`) do produto acabado (`B1_TIPO = PA`) — apontamento que gera entrada em estoque. O ranking `items[]` por CT continua com todos os centros. Com filtro `work_center`, o KPI passa a ser o volume daquele CT.

CT de inspeção final + OP mãe alimentam o total produzido canônico (`/produced-totals`), consumido também por PPM e shipping-status.

## Permissões

| Código | Uso |
|--------|-----|
| `production-appointments.access` | Acesso ao app |
| `production-appointments.view` | Ambas filiais |
| `production-appointments.view.filial-sc` | Filial `01` |
| `production-appointments.view.filial-es` | Filial `02` |
| `api-delpi.access` | Bypass de leitura na API |

Gate: `branch_access_error(branch)` em toda rota com `branch`.

## Endpoints

| Método | Path | operationId | shape |
|--------|------|-------------|-------|
| GET | `/production/appointments/work-centers` | `list_production_appointment_work_centers` | `paged_list` |
| GET | `/production/appointments` | `list_production_appointments` | `paged_list` |
| GET | `/production/appointments/summary` | `get_production_appointments_summary` | `playbook_report` |
| GET | `/production/appointments/series` | `get_production_appointments_series` | `playbook_report` |
| GET | `/production/appointments/finished-ops/series` | `get_production_appointments_finished_ops_series` | `playbook_report` |
| GET | `/production/appointments/by-op` | `list_production_appointments_by_op` | `paged_list` |
| GET | `/production/appointments/child-ops` | `list_production_appointments_child_ops` | `paged_list` |
| GET | `/production/appointments/produced-totals` | `get_production_appointments_produced_totals` | `playbook_report` |

## Série temporal (apontamentos)

`GET /series` agrega produzida/perdida por `granularity` (`day`|`month`) e `group_by` (`day`|`day_work_center`):

- `day` / `month` sem `work_center` — `qty_produced` só na última operação do roteiro do PA (alinhado ao KPI do painel)
- `day_work_center` ou `work_center` informado — `qty_produced` do(s) CT(s) do recorte
- `qty_lost` permanece a soma de todos os apontamentos do recorte

Resposta: `points[]` com `bucket`, `periodo`, `appointment_date` (ISO), `qty_produced`, `qty_lost`, `appointment_count`.

## OPs finalizadas (série)

`GET /finished-ops/series` conta OPs com **`SC2.C2_DATRF` preenchido** no período (closed-open), agregadas por `granularity`:

- `day` (padrão) — bucket `YYYYMMDD` → `periodo` ISO `YYYY-MM-DD`
- `month` — bucket `YYYYMM` → `periodo` ISO `YYYY-MM`
- `mother_op=true` — só OP mãe (`RIGHT(C2_OP, 3) = 001`)
- `product` opcional — filtro exato em `C2_PRODUTO`

Resposta: `points[]` com `bucket`, `periodo`, `ops_finished_count` + `totals.ops_finished_count`.

## Totais produzidos (canônico)

`GET /produced-totals` expõe o denominador compartilhado com PPM e shipping:

- Fonte: **`SH6010.H6_QTDPROD`**
- CT de inspeção final (`HB_NOME LIKE '%INSPE%FINAL%'`)
- OP mãe (`H6_OP` sufixo `001`)
- Tipos SB1: default `PA,PI` (`product_types` opcional); shipping usa `PA`

Use case: `GetProducedQuantityUseCase` + `ProductionAppointmentsRepository` (único SQL).

## Parâmetros

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `branch` | sim | `01` (SC) ou `02` (ES) |
| `date_start`, `date_end` | não | `YYYY-MM-DD`; default = mês corrente (closed-open em `H6_DTAPONT`) |
| `work_center` | não | Ex.: `CT-70` |
| `op` | não | Ordem de produção (match exato) |
| `product` | não | Código produto (match exato) |
| `mother_op` | não | `true` = só OP mãe (sufixo `001` em `H6_OP` / `C2_OP`) |
| `search` | não | Texto livre nas listagens (`/appointments` e `/by-op`): operador, OP, produto, CT, recurso, etc. |
| `group_by` | séries de apontamento | `day` (padrão) ou `day_work_center` |
| `granularity` | séries (`/series`, `/finished-ops/series`) | `day` (padrão) ou `month` — bucket temporal |
| `page`, `page_size` | listas | Paginação (`page_size` máx. 200) |

## Exemplo

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/apps/api-delpi/production/appointments/summary?branch=01&date_start=2026-06-15&date_end=2026-07-15"
```

`data.totals.qty_produced` no painel (sem `work_center`) é a soma **só na última operação do roteiro do PA**; `qty_produced_scope` = `pa_last_routing_operation`. `data.items[]` (por CT) continua com todos os centros e `is_final_inspection`. Com `work_center`, o KPI usa o volume daquele CT (`qty_produced_scope` = `work_center`). `qty_lost`, contagem de apontamentos/OPs/CTs e a tabela não mudam de escopo.

Na **lista** (`GET /production/appointments`), cada item traz também:

| Campo | Origem |
|-------|--------|
| `appointment_date` | `H6_DTAPONT` |
| `start_date` / `start_time` | `H6_DATAINI` / `H6_HORAINI` |
| `end_date` / `end_time` | `H6_DATAFIN` / `H6_HORAFIN` |
| `operator_code` / `operator_name` | `H6_OPERADO` + `SYS_USR.USR_NOME` |
| `operation` | `H6_OPERAC` |
| `resource` / `resource_name` | `H6_RECURSO` + `SH1.H1_DESCRI` |

## Unidades (MI → UN)

`H6_QTDPROD` / `H6_QTDPERD` vêm do Protheus em milheiro quando `B1_UM = MI` (ou UM vazia, tratada como MI). A API converte para peças (`UN`) antes de responder:

| Endpoint | Onde aplica |
|----------|-------------|
| Lista / by-op | `ProductionOperationalQuantityService.normalize_items` (`qty_produced`, `qty_lost`; `unit` → `UN`) |
| Summary / series | Fator no SQL (`CASE` × `displayUnitFactor` de `production_operational_units.json`) |

Playbook: [`docs/api/padroes-totvs/playbooks/playbook-conversao-unidades-protheus.md`](./padroes-totvs/playbooks/playbook-conversao-unidades-protheus.md). O MFE **não** multiplica nem rotula “milheiro”.

## SQL

Builders: `app/infrastructure/persistence/totvs/production_appointments/production_appointments_sql.py`  
Probe Fase 0: `scripts/sql/production_appointments_fase0_probe.py`
