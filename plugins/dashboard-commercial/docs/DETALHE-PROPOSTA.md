# Detalhe da proposta comercial

Rota MFE: `/apps/dashboard-commercial/proposta/{proposal_number}`  
Componente: `CommercialDetailPage.tsx`

O detalhe exibe cabeçalho AD1010, cliente/vendedor, **produtos da OV**, **estrutura BOM** (quando disponível) e histórico AIJ010 — alinhado ao padrão do dashboard LMP (`dashboard-lmps`).

---

## Fluxo de dados

O hook `useCommercialProposalDetail` dispara **duas** rotas comerciais em paralelo:

| Chamada | Rota | Conteúdo |
|---------|------|----------|
| Detalhe | `GET /commercial/proposals/{proposal_number}` | Cabeçalho AD1010, cliente, vendedor, **`list_products[]`** |
| Histórico | `GET /commercial/proposals/{proposal_number}/history/events` | Eventos AIJ010 enriquecidos |

Query comum: `branch` (obrigatório), `revision` (opcional), `date_start` / `date_end` (período do dashboard — repassado ao histórico).

A **estrutura BOM** não passa pela rota comercial. Para cada código em `list_products`, o MFE chama:

```text
GET /apps/api-delpi/products/{code}/structure?max_depth=6&page_size=200
```

(`productApi.ts` → `useCommercialProductStructures`)

---

## Seções da UI

| Seção | Fonte | Observação |
|-------|-------|------------|
| KPIs (status, abertura, fechamento) | Detalhe AD1010 | — |
| Proposta | Detalhe | Filial, revisão, processo, estágio, datas |
| Cliente e vendedor | Detalhe | SA1010 / SA3010 |
| **Produtos** | `list_products[]` | Tabela ADJ010 — jun/2026 |
| **Estrutura do produto** | `/products/{code}/structure` | Árvore BOM por produto — jun/2026 |
| Histórico da OV | `/history/events` | Timeline ou tabela AIJ010 |

Tooltips: `COMMERCIAL_HELP_TOOLTIPS.detail.*` em `src/content/helpTooltips.ts`.

---

## Produtos da OV (`list_products`)

### Por que reutilizar o repositório LMP

Proposta comercial e LMP compartilham a mesma OV TOTVS (**AD1010** cabeçalho + **ADJ010** itens). Em vez de duplicar SQL no repositório comercial, a API expõe `list_ov_products` no port `LMPQueryRepositoryPort`, implementado em `LMPQueryRepository` com o SQL existente `_sql_products_lmp`.

### API

| Camada | Arquivo |
|--------|---------|
| Port | `api-delpi/app/domain/ports/lmp/lmp_query_repository_port.py` → `list_ov_products` |
| Infra | `api-delpi/app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_repository.py` |
| Use case | `GetCommercialProposalUseCase` anexa `list_products` ao payload de `get_proposal` |
| Composition | `commercial_composer.py` injeta `LMPQueryRepository()` |

Resposta `data` de `GET /commercial/proposals/{proposal_number}`:

```json
{
  "proposal_number": "003446",
  "branch": "01",
  "revision": "08",
  "list_products": [
    {
      "code": "90123456",
      "description": "Produto exemplo (REF-01)",
      "group_code": "100",
      "type": "PI",
      "qtd_pi": 2
    }
  ]
}
```

### MFE

| Arquivo | Papel |
|---------|-------|
| `types/commercial.ts` | Tipo `CommercialProduct`; `list_products` em `CommercialProposalDetailData` |
| `utils/commercialProductsPresentation.tsx` | Colunas da tabela, badges de tipo (PA/PI), descrição com referência |
| `CommercialDetailPage.tsx` | Card **Produtos** com `DataTable` |

---

## Estrutura BOM (árvore de produtos)

Espelha o dashboard LMP (`useLmpProductStructures`, `LmpProductStructuresSection`, `ProductStructureTree`, `RichTree`).

| Arquivo (comercial) | Equivalente LMP |
|---------------------|-----------------|
| `hooks/useCommercialProductStructures.ts` | `useLmpProductStructures.ts` |
| `components/CommercialProductStructuresSection.tsx` | `LmpProductStructuresSection.tsx` |
| `components/ProductStructureTree.tsx` | idem |
| `components/RichTree.tsx` | idem |
| `components/StructureLegend.tsx` | idem |
| `utils/productStructureTree.ts` | idem |
| `types/productStructure.ts`, `types/richTree.ts` | idem |
| `index.css` (classes `.dc-*`) | `.lmps-*` |

Comportamento:

1. Deduplica códigos de `list_products`.
2. Carrega estruturas em paralelo (`Promise.allSettled`); aborta ao desmontar.
3. Renderiza a seção só se houver estrutura renderizável (`hasRenderableProductStructure`) ou enquanto carrega.
4. **Exportação tabular** (`buildProductStructuresPayload`) usa o mesmo `buildProductStructureTree` da UI — a API retorna `root` (PA) e `items[]` (componentes de 1º nível com `components` aninhados); não achatar só `root`.
4. Árvore expandível (profundidade inicial 1), legenda código/descrição/tipo/quantidade.

---

## Histórico AIJ010 (contexto)

O histórico usa o mesmo pipeline LMP (`GetLmpHistoryEventsUseCase`). O contexto do painel vem de **`get_lmp_history_panel_context`** (AD1010 lite) — **não** executa batch `AllListingAnchorRaw` mesmo quando o MFE envia `date_start`/`date_end`.

Ver:

- `api-delpi/docs/api/06-modulos-departamentais.md` — § Comercial e § Engenharia (`/history/events`)
- `plugins/dashboard-commercial/docs/API_MAPPING.md`

Commit de referência (performance): `d37d0c90`.

---

## Evolução recente do detalhe (jun/2026)

| Entrega | Commit (aprox.) | Descrição |
|---------|-----------------|-----------|
| Tooltips visíveis | `17126ebe` | Portal do balão de ajuda fora do root do dashboard |
| Botões Atualizar/Voltar | `aa9ba639` | Ações no header do detalhe |
| Histórico otimizado | `d37d0c90` | AD1010 lite; docs em `e02ec585` |
| Filtro WEG / novos negócios no ROL | `4a0d9914` | `customer_segment` em KPIs e gráfico |
| Produtos + BOM | `0bbefea3` | `list_products` + seção estrutura (este documento) |

---

## Testes

### API

```bash
docker exec delpi-api-delpi python -m pytest \
  tests/test_list_commercial_proposals_use_case.py -q
```

Caso `test_get_commercial_proposal_use_case_returns_detail_dict` valida `list_products` com mock de `LMPProduct`.

### MFE

```bash
cd plugins/dashboard-commercial && npm run build
```

### Checklist manual (detalhe)

| Área | O que validar |
|------|----------------|
| Navegação | Clique na linha da tabela → detalhe; **Voltar** preserva filtros na URL |
| Cabeçalho | Filial, revisão, status, cliente, vendedor |
| Produtos | Tabela com código, descrição, grupo, tipo, qtd PI; tooltips nas colunas |
| BOM | Árvore expandível por produto PI/PA; legenda; estado vazio quando sem estrutura |
| Histórico | Timeline / tabela AIJ010 |
| Ações | **Atualizar** recarrega detalhe + histórico (+ BOM) |
