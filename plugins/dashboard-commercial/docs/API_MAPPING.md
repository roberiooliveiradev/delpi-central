# API — Dashboard Comercial

Base: `/apps/api-delpi/commercial`

Permissão: `dashboard-commercial.view` ou `api-delpi.access`

| Função | Método | Rota | Query |
|--------|--------|------|-------|
| `getHeadOfficeRolTarget` | GET | `/head_office_rol_target_pct` | `start_date`, `end_date` |
| `getBranchRolTarget` | GET | `/branch_rol_target_pct` | `start_date`, `end_date` |
| `getClosingRate` | GET | `/closing-rate` | `start_date`, `end_date`, `branch` |
| `getSalesOrderOtd` | GET | `/sales-order-otd` | `start_date`, `end_date`, `branch` |
| `getNewBusinessRolPct` | GET | `/new-business-rol-pct` | `start_date`, `end_date`, `branch` |
| `getNewClientsAverage` | GET | `/new-clients-average` | `start_date`, `end_date`, `branch` |
| `getNewClientsRolPct` | GET | `/new-clients-rol-pct` | `start_date`, `end_date`, `branch` |

Envelope: `{ success, message, data }` — ver tipos em `src/types/commercial.ts`.
