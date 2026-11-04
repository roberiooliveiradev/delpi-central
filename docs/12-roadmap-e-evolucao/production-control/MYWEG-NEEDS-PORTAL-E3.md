# MyWEG Necessidades — Etapa 3 (Portal PCP)

> **Status:** tela JWT no MFE Production Control  
> **TASK_ID:** `MYWEG-NEEDS-E3-PORTAL-PCP`  
> **URL:** `/apps/production-control/myweg-needs?branch=02`  
> **E4 (SB1):** ver [MYWEG-NEEDS-PROTHEUS-E4.md](./MYWEG-NEEDS-PROTHEUS-E4.md) — colunas de código verificado / situação do vínculo.

## EXISTING_EQUIVALENT / REUSE_DECISION

| Item | Decisão |
|------|--------|
| EXISTING_EQUIVALENT | `DataTableSection` (`dataTableUi`), `PpcWorkspaceHeader`, `createDashboardLoadingActivityCard`, `httpClient`/`ppcApi`, `routeParser`, filtros server-side (Demanda/Materiais) |
| REUSE | Rotas JWT E2 `/myweg/need-batches*` · catálogo `subplugins.json` · permissões Core já cadastradas |
| CRIAR | `MyWegNeedsPage` + hook + copy/help · ícone rail `factory` |
| NÃO | endpoints novos, consulta SB1, ETL, MFE→Postgres, comparação entre coletas (E5) |

## Autorização

Backend (autoridade): `production-control.access` + `production-control.myweg-needs.view` + `production-control.view.filial-02`.

Menu: subplugin só aparece se o catálogo filtrado pelo BFF incluir o item.  
Filial 01: UI bloqueia consulta e oferece ação explícita para `branch=02` (sem troca silenciosa).

## Contrato consumido

- `GET /myweg/need-batches`
- `GET /myweg/need-batches/latest`
- `GET /myweg/need-batches/{batchId}`
- `GET /myweg/need-batches/{batchId}/items` (`search`, `remessaFrom`, `remessaTo`, `page`, `pageSize`)

Quantidades: strings decimais · formatação pt-BR sem `float`.
