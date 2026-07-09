# API — Dashboard Comercial

Base: `/apps/api-delpi/commercial`

Permissão: `dashboard-commercial.view` ou `api-delpi.access`

| Função | Método | Rota | Query |
|--------|--------|------|-------|
| `getHeadOfficeRolTarget` | GET | `/head_office_rol_target_pct` | `start_date`, `end_date` — ROL filial 01; meta SI: `commercial_rol`, branch `01` |
| `getBranchRolTarget` | GET | `/branch_rol_target_pct` | `start_date`, `end_date` — ROL filial 02; meta SI: `commercial_rol`, branch `02` |
| `getCommercialRolSeries` | GET | `/rol-series` | `start_date`, `end_date`, `granularity` — séries `rol_matrix` / `rol_branch` (01/02) |
| `getClosingRate` | GET | `/closing-rate` | `start_date`, `end_date`, `branch` |
| `getCommercialProposals` | GET | `/proposals` | `start_date`, `end_date`, `branch`, `status` (`won`/`open`), `customer_segment`, `page`, `page_size`, `sort_by`, `sort_dir`, `search` |
| `getCommercialProposalByNumber` | GET | `/proposals/{proposal_number}` | `branch` (obrig.), `revision` — cabeçalho AD1010 + cliente/vendedor + **`list_products[]`** (ADJ010 via `list_ov_products`) |
| `getCommercialProposalHistoryEvents` | GET | `/proposals/{proposal_number}/history/events` | `branch`, `revision`, `date_start`, `date_end` |
| `getProductStructure` | GET | `/products/{code}/structure` *(api-delpi produtos, não `/commercial`)* | `max_depth`, `page_size` — BOM carregada no detalhe por produto (`productApi.ts`) |
| `getSalesOrderOtd` | GET | `/sales-order-otd` | `start_date`, `end_date`, `branch`, `customer_segment` — inclui linhas faturadas e não faturadas (ver `api-delpi/docs/api/comercial-sales-order-otd.md`) |
| `getNewBusinessRolPct` | GET | `/new-business-rol-pct` | `start_date`, `end_date`, `branch` |
| `getNewClientsAverage` | GET | `/new-clients-average` | `start_date`, `end_date`, `branch` |
| `getNewClientsRolPct` | GET | `/new-clients-rol-pct` | `start_date`, `end_date`, `branch` |

**Histórico da proposta:** reutiliza `GetLmpHistoryEventsUseCase` (AIJ010 + enriquecimento). Contexto do painel via `get_lmp_history_panel_context` (AD1010 lite) — **não** executa batch `AllListingAnchorRaw` mesmo com `date_start`/`date_end` na URL. Ver `api-delpi/docs/api/06-modulos-departamentais.md` § Engenharia — `/history/events`.

**Produtos e BOM (jun/2026):** `GET /proposals/{proposal_number}` inclui `list_products[]` (SQL ADJ010 compartilhado com LMP). Estrutura analítica via `GET /products/{code}/structure`. Ver [DETALHE-PROPOSTA.md](./DETALHE-PROPOSTA.md).

**Listagem paginada (jun/2026):** `sort_by`, `sort_dir` e `search` no servidor. Detalhes em [PROPOSTAS-PERIODO.md](./PROPOSTAS-PERIODO.md).

Envelope: `{ success, message, data }` — ver tipos em `src/types/commercial.ts`.
