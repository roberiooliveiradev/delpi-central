# Apontamento de Produção — `/production/appointments`

**Status:** implementado (jul/2026)  
**Plugin previsto:** `production-appointments` (nome portal: Apontamento de Produção)  
**Spec / Fase 0:** [`docs/12-roadmap-e-evolucao/production-appointments/`](../../../../docs/12-roadmap-e-evolucao/production-appointments/)

Acompanha apontamentos de produção (`SH6010`, tipo `P`) por centro de trabalho via `SH1010` → `SHB010`.  
**Fora de escopo:** PPM, eficiência %, MOD. CT de inspeção final entra nos totais.

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
| GET | `/production/appointments/by-op` | `list_production_appointments_by_op` | `paged_list` |

## Parâmetros

| Parâmetro | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `branch` | sim | `01` (SC) ou `02` (ES) |
| `date_start`, `date_end` | não | `YYYY-MM-DD`; default = mês corrente (closed-open em `H6_DTAPONT`) |
| `work_center` | não | Ex.: `CT-70` |
| `op` | não | Ordem de produção |
| `product` | não | Código produto |
| `group_by` | séries | `day` (padrão) ou `day_work_center` |
| `page`, `page_size` | listas | Paginação (`page_size` máx. 200) |

## Exemplo

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/apps/api-delpi/production/appointments/summary?branch=01&date_start=2026-06-15&date_end=2026-07-15"
```

`data.totals` e `data.items[]` (por CT) incluem `qty_produced`, `qty_lost`, `appointment_count`; itens trazem `is_final_inspection` quando aplicável.

## Unidades (MI → UN)

`H6_QTDPROD` / `H6_QTDPERD` vêm do Protheus em milheiro quando `B1_UM = MI` (ou UM vazia, tratada como MI). A API converte para peças (`UN`) antes de responder:

| Endpoint | Onde aplica |
|----------|-------------|
| Lista / by-op | `ProductionOperationalQuantityService.normalize_items` (`qty_produced`, `qty_lost`; `unit` → `UN`) |
| Summary / series | Fator no SQL (`CASE` × `displayUnitFactor` de `production_operational_units.json`) |

Playbook: [`docs/roadmaps/playbook-conversao-unidades-protheus.md`](../roadmaps/playbook-conversao-unidades-protheus.md). O MFE **não** multiplica nem rotula “milheiro”.

## SQL

Builders: `app/infrastructure/persistence/totvs/production_appointments/production_appointments_sql.py`  
Probe Fase 0: `scripts/sql/production_appointments_fase0_probe.py`
