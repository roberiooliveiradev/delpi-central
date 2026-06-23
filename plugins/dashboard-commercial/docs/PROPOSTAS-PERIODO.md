# Tabela «Propostas do período» — Dashboard Comercial

Listagem paginada de OVs (AD1010) na página principal do dashboard comercial. Desde **jun/2026**, ordenação, busca e paginação são **server-side** na api-delpi; o MFE apenas renderiza o resultado e dispara novas consultas ao mudar filtros.

## Comportamento na UI

| Recurso | Onde | Comportamento |
|---------|------|----------------|
| **Status da proposta** | Dentro do card (toolbar, à direita da busca) | `Todas` / `Ganhas` / `Em aberto` → query `status` |
| **Busca** | Campo de texto no card | Debounce 350 ms → query `search` no servidor |
| **Ordenação** | Cabeçalhos da tabela | Clique alterna asc/desc → `sort_by` + `sort_dir` |
| **Paginação** | Rodapé do card | Seletor **10 / 20 / 50 / 100** itens por página; botões numerados, **Ir para** (dropdown) e Anterior/Próxima → `page` + `page_size` |
| **Exportação** | Ações no header do card | Busca até 200 registros com filtros/ordem/busca atuais antes de CSV/Excel/PDF |

Clique na linha abre o [detalhe da proposta](./DETALHE-PROPOSTA.md).

## Filtros de período e escopo

| Filtro global (FilterBar) | Efeito na listagem |
|---------------------------|-------------------|
| `start_date` / `end_date` | **Todas / Em aberto:** última revisão por OV com `AD1_DATA` no período. **Ganhas:** aceite (`AD1_DTASSI` / `proposal_acceptance_date`) no período e status 9. |
| `branch` | Restringe `AD1_FILIAL` |
| `customer_segment` | `weg` (cliente 000001) ou `new_business` (demais) |

## API — `GET /commercial/proposals`

Base: `/apps/api-delpi/commercial/proposals`

| Parâmetro | Tipo | Descrição |
|-----------|------|-----------|
| `start_date`, `end_date` | string | Período (YYYY-MM-DD) |
| `branch` | string | Filial (2 dígitos) |
| `status` | string | `won` (ganhas), `open` (sem fechamento ganho) ou omitir (todas) |
| `customer_segment` | string | `weg` ou `new_business` |
| `page` | int | Página (default 1) |
| `page_size` | int | Tamanho (1–200, default 50; UI: 10, 20, 50 ou 100) |
| `sort_by` | string | Coluna de ordenação (ver tabela abaixo) |
| `sort_dir` | string | `asc` ou `desc` |
| `search` | string | Busca textual (máx. 80 caracteres) |

### Colunas ordenáveis (`sort_by`)

| Valor API | Coluna na UI |
|-----------|----------------|
| `branch` | Filial |
| `proposal_number` | Nº proposta (`proposal` no MFE é mapeado para este valor) |
| `revision` | Rev. |
| `description` | Descrição |
| `proposal_date` | Data |
| `end_date` | Fim (data de aceite para ganhas) |
| `status_code` | Status (`status` no MFE) |
| `customer_code` | Cliente (`customer` no MFE) |
| `customer_store` | Loja |

Default sem `sort_by`: `proposal_date DESC`, `proposal_number DESC`, `revision DESC`.

### Busca (`search`)

Aplicada **após** deduplicar a última revisão por filial + número (`rn = 1`). Campos:

- Filial, número, revisão, descrição (case-insensitive), código de status, cliente, loja, estágio
- Rótulos de status em português (ex.: «ganha» → status `9`)

Implementação: `CommercialProposalListSearchService` (api-delpi).

## Resposta

```json
{
  "success": true,
  "data": {
    "items": [{ "branch", "proposal_number", "revision", "description", "proposal_date", "end_date", "status_code", "status_label", "status_category", "customer_code", "customer_store", "stage" }],
    "total": 46,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

## MFE — arquivos principais

| Arquivo | Papel |
|---------|--------|
| `src/pages/DashboardCommercialPage.tsx` | Estado de status, busca debounced, wiring da tabela |
| `src/hooks/useCommercialProposals.ts` | Fetch com filtros + paginação + sort + search |
| `src/hooks/useServerTable.ts` | Estado de página, tamanho da página e ordenação |
| `src/components/Pagination.tsx` | Rodapé: itens/página, páginas numeradas, salto direto |
| `src/utils/paginationPages.ts` | Cálculo de páginas visíveis (reticências) |
| `src/hooks/useDebouncedValue.ts` | Debounce da busca (350 ms) |
| `src/components/table/DataTableSection.tsx` | `serverPagination`, `serverSort`, `serverSearch`, `toolbarExtra` |
| `src/api/commercialApi.ts` | `getCommercialProposals`, `getCommercialProposalsForExport`, `resolveProposalSortApiKey` |
| `src/export/CommercialExportButtons.tsx` | `resolvePayload` / `resolveContext` para exportação assíncrona |

## api-delpi — arquivos principais

| Arquivo | Papel |
|---------|--------|
| `commercial_router.py` | Query params da rota |
| `list_commercial_proposals_request.py` | DTO |
| `commercial_proposals_repository.py` | SQL TOTVS, CTE última revisão, ORDER BY, OFFSET |
| `commercial_proposal_list_search_service.py` | Cláusula `search` |
| `commercial_proposal_acceptance_date_service.py` | Data de aceite para ganhas |

## Testes

### api-delpi

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_commercial_proposal_list_search_service.py \
  tests/test_commercial_proposals_repository.py \
  tests/test_list_commercial_proposals_use_case.py -q
```

### Validação live (TOTVS)

```bash
docker exec delpi-api-delpi python -c "
from app.application.dto.commercial.list_commercial_proposals_request import ListCommercialProposalsRequest
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_proposals_repository import CommercialProposalsRepository
repo = CommercialProposalsRepository()
base = dict(start_date='2026-06-01', end_date='2026-06-23', page=1, page_size=5)
print('total', repo.list_proposals(ListCommercialProposalsRequest(**base)).total)
print('weg', repo.list_proposals(ListCommercialProposalsRequest(**base, search='weg')).total)
print('sort', repo.list_proposals(ListCommercialProposalsRequest(**base, sort_by='proposal_number', sort_dir='asc')).items[0].proposal_number)
"
```

### MFE

```bash
cd plugins/dashboard-commercial && npm run ci
```

## Histórico de mudanças (jun/2026)

1. Ordenação movida do frontend (`useClientTableSort`) para o backend (`sort_by` / `sort_dir`).
2. Filtro **Status da proposta** reposicionado para dentro do card (antes ficava acima).
3. Paginação server-side (20/página).
4. Busca server-side com debounce; exportação respeita busca e ordenação.
5. Correção SQL Server: `ORDER BY` sem coluna duplicada ao ordenar por `proposal_number`.
6. Paginação ampliada: seletor de itens por página (10/20/50/100) e navegação com escolha direta da página no rodapé.

Commits de referência: `396d1fc2`, `5c3589d2`, `dd53d04f` e commit desta entrega (exportação PNG + paginação avançada).
