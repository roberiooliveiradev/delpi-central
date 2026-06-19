# Vigência de estrutura (SG1010) — filtro completo (jun/2026)

Registro da unificação do filtro de **vigência da BOM** (`G1_INI` / `G1_FIM`) em todas as rotas de produto que percorrem `SG1010`.

Playbooks relacionados:

- [playbook-estrutura-produto-exclusividade-mp.md](../roadmaps/playbook-estrutura-produto-exclusividade-mp.md)
- [playbook-situacao-de-producao-pa.md](../roadmaps/playbook-situacao-de-producao-pa.md)
- [playbook-visaostatus-produto.md](../roadmaps/playbook-visaostatus-produto.md)

---

## 1. Problema

Várias rotas aplicavam apenas `G1_FIM > GETDATE()` ou **nenhum** filtro de vigência. Isso permitia:

- componentes com **início de vigência futuro** (`G1_INI > hoje`) na estrutura;
- linhas históricas em rotas sem filtro (`/parents`, `/guide`, `/inspection`);
- inconsistência entre `/structure` (parcial) e `/production-status` (intervalo completo com `reference_date`);
- em `/factory-status`, o bloco `structure` ignorava o `reference_date` da query.

---

## 2. Solução (módulo canônico)

| Artefato | Responsabilidade |
|----------|------------------|
| `ProductBomValidityFilterService` | Fragmentos SQL de vigência em `SG1010` |
| `validity_filter_sql(alias, reference_param)` | Intervalo completo com parâmetro (`@DATA_REF`) |
| `validity_filter_sql_for_today(alias)` | Intervalo completo com data do servidor (default das rotas sem `reference_date`) |

Filtro homologado (equivalente ao playbook de produção):

```sql
AND (G1_INI = '' OR G1_INI <= @DATA_REF)
AND (G1_FIM = '' OR G1_FIM >= @DATA_REF)
```

Quando a rota não recebe data, `@DATA_REF` é substituído por `CONVERT(CHAR(8), GETDATE(), 112)`.

**Testes:** `api-delpi/tests/test_product_bom_validity_filter_service.py`

---

## 3. Rotas e repositórios afetados

| Rota | Repositório |
|------|-------------|
| `GET /products/{code}/structure` | `ProductStructureRepository` |
| `GET /products/{code}/structure/excel` | `ProductStructureRepository` (via use case) |
| `GET /products/{code}/analyser` (bloco `structure`) | `ProductStructureRepository` |
| `GET /products/{code}/parents` | `ProductParentsRepository` |
| `GET /products/{code}/guide` | `ProductGuideRepository` |
| `GET /products/{code}/inspection` | `ProductInspectionRepository` |
| `GET /products/{code}/structure/exclusivity` | `ProductPlaybookRepository.fetch_structure_with_exclusivity` |
| `GET /products/directives/{identifier}` | `ProductPlaybookRepository.fetch_structure_with_exclusivity` |
| `GET /products/{code}/factory-status` | estrutura + estoque MP com `reference_date` |
| `GET /products/{code}/production-status` | `fetch_production_status` (refatorado para o serviço) |
| `GET /products/{code}/cost-impact-simulation` | `ProductCostImpactRepository` |
| `GET /products/exclusive-raw-materials/catalog` | `ProductExclusiveRawMaterialRepository` |

---

## 4. Comportamento por rota

| Contexto | Data de vigência |
|----------|------------------|
| `/structure`, `/analyser`, `/parents`, `/guide`, `/inspection`, `/structure/exclusivity`, `/directives`, `/cost-impact-simulation`, catálogo exclusividade | **Hoje** (servidor SQL) |
| `/production-status` | `reference_date` (query; default hoje) |
| `/factory-status` — blocos `structure` e `raw_material_stock` | `reference_date` (query; default hoje) |

Contrato HTTP **inalterado**: nenhuma query nova obrigatória nas rotas que já não expunham `reference_date`.

---

## 5. Gates de regressão

```bash
cd api-delpi
pytest tests/test_product_bom_validity_filter_service.py \
       tests/test_product_playbook_use_cases.py \
       tests/test_product_directives.py -q
```
