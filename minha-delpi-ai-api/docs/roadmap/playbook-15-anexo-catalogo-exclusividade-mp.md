# Playbook 15 — Anexo: catálogo de exclusividade MP (chat)

**Parent api-delpi:** [`api-delpi/docs/roadmaps/playbook-catalogo-exclusividade-mp.md`](../../../api-delpi/docs/roadmaps/playbook-catalogo-exclusividade-mp.md)  
**Parent playbook 15:** [`playbook-15-rotas-operacionais-sem-sql.md`](./playbook-15-rotas-operacionais-sem-sql.md)

---

## 1. Objetivo

Conectar perguntas **sem código de produto** ao catálogo de MPs exclusivas, mantendo `/structure/exclusivity` para detalhe quando o usuário informar o PA.

---

## 2. Mapa de rotas

| Intenção | operationId | Path |
|----------|-------------|------|
| Quais **MPs** são exclusivas? | `list_exclusive_raw_materials_catalog` | `/products/exclusive-raw-materials/catalog?view=by_material` |
| Quais **PAs** têm MP exclusiva? | `list_exclusive_raw_materials_catalog` | `...?view=by_finished_product` |
| Estrutura do PA **com** flag exclusiva | `get_product_structure_exclusivity` | `/products/{code}/structure/exclusivity` ✅ |
| Estrutura **sem** exclusividade | `get_product_structure` | `/products/{code}/structure` |
| Onde produto/MP é usado | `get_product_parents` | `/products/{code}/parents` |

---

## 3. Desambiguação

| Usuário | NÃO usar | Usar |
|---------|----------|------|
| «Quais matérias-primas exclusivas existem?» | `/data/sql`, scan manual | `list_exclusive_raw_materials_catalog` |
| «Quais produtos têm MP exclusiva?» | `/products/search` | catalog `by_finished_product` |
| «Estrutura do 90261255» (sem citar exclusiva) | exclusivity | `get_product_structure` |
| «Estrutura do 90261255 **com exclusividade**» | `/structure` | `get_product_structure_exclusivity` |
| «Compare estruturas» | catalog | orquestração multi-fetch `/structure` |
| «Onde a 10010032 é usada?» | catalog | `/parents` ou catalog filtrado `raw_material_code` |

---

## 4. Por que não enriquecer `/structure` no chat

O roteador **não** deve redirecionar perguntas de estrutura simples para SQL ou forçar `/structure/exclusivity` quando o usuário não pediu exclusividade.

A flag `exclusive_raw_material` **não** será pedida via query param em `/structure` no chat — evita:

- latência (scan global de PAs);
- regressão em respostas que hoje usam árvore `hierarchy` limpa;
- conflito com MFEs/dashboards que consomem a mesma rota api-delpi.

Detalhe completo: análise §6 do playbook api-delpi.

---

## 5. Vocabulário sugerido (`product_query_intent.json`)

Nova seção `exclusiveRawMaterialCatalog`:

- matéria-prima exclusiva, mp exclusiva, quais são exclusivas
- produtos com mp exclusiva, listar exclusivas, catálogo de exclusivas

Excludes: estrutura completa, compare estruturas (sem menção a exclusiva).

Seção existente `structureExclusivity`:

- acionar **`get_product_structure_exclusivity`** só com **código de produto** + menção a exclusividade.

---

## 6. Seleção de rota

| Serviço | Regra |
|---------|-------|
| `ChatProductQueryIntentService` | `_looks_like_exclusive_catalog_question` — sem código PA |
| `ExternalActionRouteSelectionService` | Path `/exclusive-raw-materials/catalog` |
| Com código + «exclusiv» | `structure/exclusivity` (existente) |
| `ChatSqlOperationalIntentService` | **Não** SQL de exclusividade quando catalog existir |

Parâmetros: `view`, `limit`, filtros `raw_material_code` / `finished_product_code`.

---

## 7. Apresentação

| Rota | Presenter |
|------|-----------|
| catalog `by_material` | Tabela MP + PA exclusivo |
| catalog `by_finished_product` | Tabela PA + contagem MPs |
| structure/exclusivity | Perfil `structure_exclusivity` ✅ |

Chips: «Ver estrutura do PA {code}» → `get_product_structure_exclusivity`.

---

## 8. Testes regressão

| ID | Mensagem | operationId esperado |
|----|----------|---------------------|
| EX01 | «quais matérias-primas são exclusivas?» | `list_exclusive_raw_materials_catalog` |
| EX02 | «quais produtos têm matéria-prima exclusiva?» | catalog + `view=by_finished_product` |
| EX03 | «estrutura do 90261255 com exclusividade» | `get_product_structure_exclusivity` |
| EX04 | «estrutura do 90261255» | `get_product_structure` (não exclusivity) |

---

## 9. Ordem de implementação

1. Deploy api-delpi + sync OpenAPI  
2. Vocabulário + intent  
3. Seleção + presenter  
4. Desligar SQL para EX01–EX02  
5. Smoke + `api-delpi-rotas-agente.md`
