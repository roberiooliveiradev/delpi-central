# API — Dashboard Comercial

Base: `/apps/api-delpi/commercial`

Permissão: `dashboard-commercial.view` ou `api-delpi.access`

| Função | Método | Rota | Query |
|--------|--------|------|-------|
| `getHeadOfficeRolTarget` | GET | `/head_office_rol_target_pct` | `start_date`, `end_date` — ROL filial 01; meta SI: `commercial_rol`, branch `01` |
| `getBranchRolTarget` | GET | `/branch_rol_target_pct` | `start_date`, `end_date` — ROL filial 02; meta SI: `commercial_rol`, branch `02` |
| `getCommercialRolSeries` | GET | `/rol-series` | `start_date`, `end_date`, `granularity` — séries `rol_matrix` / `rol_branch` (01/02) |
| `getClosingRate` | GET | `/closing-rate` | `start_date`, `end_date`, `branch` |
| `getCommercialProposals` | GET | `/proposals` | `start_date`, `end_date`, `branch`, `status` (`won`/`open`), `page`, `page_size` |
| `getCommercialProposalByNumber` | GET | `/proposals/{proposal_number}` | `branch` (obrig.), `revision` |
| `getCommercialProposalHistoryEvents` | GET | `/proposals/{proposal_number}/history/events` | `branch`, `revision`, `date_start`, `date_end` |
| `getSalesOrderOtd` | GET | `/sales-order-otd` | `start_date`, `end_date`, `branch` |
| `getNewBusinessRolPct` | GET | `/new-business-rol-pct` | `start_date`, `end_date`, `branch` |
| `getNewClientsAverage` | GET | `/new-clients-average` | `start_date`, `end_date`, `branch` |
| `getNewClientsRolPct` | GET | `/new-clients-rol-pct` | `start_date`, `end_date`, `branch` |

Envelope: `{ success, message, data }` — ver tipos em `src/types/commercial.ts`.
