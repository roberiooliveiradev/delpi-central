# G2 — Inventário do contrato oficial de estrutura (Totus / Domain API)

**Escopo:** somente contratos **já existentes**, comprovados no código do monorepo.  
**Sem** consulta direta a banco de outro bounded context nesta execução.  
**Amostra live `90264135`:** `TEST_NOT_RUN` / `AUTH_BLOCKED` (endpoint exige JWT + permissões; probe anônimo não retornou envelope de produto).

## Cadeia de ownership

```text
TOTVS Protheus SG1010 (+ SB1010)
  → api-delpi ProductStructureRepository.fetch_structure_rows
  → ListProductStructureUseCase (+ BomTreeBuilder)
  → HTTP GET /products/{code}/structure  (operationId=get_product_structure)
  → engineering-api DelegatedAuxiliarySource.fetch_product_structure
  → MCP/EVA product.structure (consumidor)
```

Fontes de código:

- `api-delpi/app/infrastructure/persistence/totvs/product_repositories/product_structure_repository.py`
- `api-delpi/app/application/use_cases/product/list_product_structure_use_case.py`
- `api-delpi/app/domain/entities/product/bom_node.py`
- `api-delpi/app/domain/services/product/product_bom_validity_filter_service.py`
- `api-delpi/app/interface/http/routes/product_routes.py` (`get_structure`)
- `engineering-api/.../delegated_auxiliary.py` (`fetch_product_structure`)
- AuthZ: `@require_any_permission(ENGINEERING_LMP_ACCESS)` =
  `API_DELPI_ACCESS` | `DASHBOARD_ENGINEERING_VIEW` | `DASHBOARD_LMPS_VIEW`

## Campos comprovados na explosão SG1

| Conceito | Fonte Totus / contrato | Presente na resposta? |
|---|---|---|
| Produto raiz | path `{code}` + nó `root.code` | **SIM** |
| Código do pai | `G1_COD` → `parent_code` (interno) / árvore aninhada | **SIM** (implícito na árvore `components[]`) |
| Código do filho | `G1_COMP` → `component_code` / `BomNode.code` | **SIM** |
| Nível estrutural | `bom_level` recursivo (1..max_depth) | **SIM** nas rows SQL; árvore aninha por profundidade |
| Tipo MP/PI/PA | `SB1.B1_TIPO` → `type` / `component_type` | **SIM** (`BomNode.type`) |
| Quantidade | `G1_QUANT` → `quantity` | **SIM** |
| Unidade | `SB1.B1_UM` (+ SEGUM/CONV opcionais) | **SIM** |
| Descrição | `SB1.B1_DESC` | **SIM** |
| Vigência | filtro `G1_INI`/`G1_FIM` vs `GETDATE()`; meta `bom_validity={filter:current,reference:server_date,validityColumns:G1_INI,G1_FIM}` | **SIM** |
| Revisão do desenho PDF | — | **CONTRACT_GAP** (estrutura não carrega revisão documental do PDF) |
| Identificação de ocorrência (item de tabela / path único multi-uso) | — | **CONTRACT_GAP** (`BomNode` não expõe `occurrence_id`; mesmo código sob pais diferentes aparece como nós distintos na árvore, sem ID de ocorrência de desenho) |
| Semântica de quantidade vs unidade de desenho | quantidade SG1 + UM SB1 | **parcial** — comparabilidade com coluna QTD. do PDF exige contrato de unidade (já tratado como INCONCLUSIVE em comparadores VAL-01) |

## Semântica de níveis (oficial)

- Nível 0 conceitual = produto consultado (`root`).
- Filhos diretos = `bom_level=1` na CTE; cada expansão incrementa `bom_level`.
- Tipo (`B1_TIPO`) classifica o **cadastro** do código (MP/PI/PA etc.); **não** deve ser inferido a partir do desenho ou do prefixo numérico no Understanding.
- Paginação: quando `page`/`page_size` informados, pagina **somente o 1º nível** de `root.components` (comportamento documentado historicamente no Doc 119 §8).

## Relacionados (não substituem structure)

| Operação | Uso |
|---|---|
| `GET /products/{code}/parents` | SG1 reverso (where-used) |
| `GET /products/{code}/structure/exclusivity` | playbook exclusividade MP — **não** árvore completa |
| Engineering `GET /v1/products/{code}/structure` | façade delegada user-parity para api-delpi |

## Lacunas relevantes a VAL-01

1. `CONTRACT_GAP:occurrence_id` — Totus structure não entrega ID de ocorrência de desenho (item A2, etc.).
2. `CONTRACT_GAP:drawing_revision_binding` — vigência BOM ≠ revisão do PDF.
3. Quantidade/UM oficiais não autorizam completar célula visual ausente.
4. Amostra runtime para `90264135` nesta sessão: não obtida sem credencial de usuário — inventário permanece **por contrato de código** (`PROVEN_IN_CODE`), payload live `TEST_NOT_RUN`.
