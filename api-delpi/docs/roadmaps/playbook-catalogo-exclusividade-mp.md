# Playbook — Catálogo de matérias-primas exclusivas (MP exclusiva × PA)

**Status:** implementado (jun/2026)  
**Parent:** [`playbook-estrutura-produto-exclusividade-mp.md`](./playbook-estrutura-produto-exclusividade-mp.md)  
**Relacionado:** [`playbook-15-rotas-operacionais-sem-sql.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-rotas-operacionais-sem-sql.md)

---

## 1. Objetivo

Atender perguntas **transversais** (sem código de produto na mensagem):

| Pergunta do usuário | Hoje | Alvo |
|---------------------|------|------|
| «Quais produtos têm matéria-prima exclusiva?» | SQL ad hoc ou `/data/sql` | Rota de catálogo |
| «Quais matérias-primas são exclusivas?» | idem | Mesma rota, `view=by_material` |
| «Liste os PAs com MP exclusiva» | idem | `view=by_finished_product` |
| «Estrutura do PA X com exclusividade» | ✅ `GET /products/{code}/structure/exclusivity` | Manter |
| «Onde o item Y é usado?» | ✅ `GET /products/{code}/parents` | Manter (sem flag exclusiva) |

**Definição (regra-mãe):** MP exclusiva = aparece em **exactamente 1** PA válido (tipo `PA`, vigência `G1_FIM`, excluir códigos `8000%` e `8001%`), considerando BOM multinível (PIs abertos). Ver §17 do playbook estrutura.

---

## 2. Rotas existentes (não duplicar)

| Método | Path | operationId | Escopo |
|--------|------|-------------|--------|
| GET | `/products/{code}/structure` | `get_product_structure` | Árvore BOM **sem** exclusividade |
| GET | `/products/{code}/structure/exclusivity` | `get_product_structure_exclusivity` | Estrutura **de um PA** + flag por MP |
| GET | `/products/{code}/parents` | `get_product_parents` | Onde o produto é usado (árvore reversa) |
| GET | `/products/{code}/factory-status` | `get_product_factory_status` | Composto (usa exclusividade internamente) |

Implementação exclusividade por produto: `ProductPlaybookRepository.fetch_structure_with_exclusivity` — SQL já homologado (playbook estrutura §10).

---

## 3. Lacuna — catálogo global

Não existe rota que varra **todos os PAs válidos** e devolva:

- lista de MPs exclusivas + PA dono; ou
- lista de PAs que possuem ≥1 MP exclusiva na estrutura.

SQL validado: playbook estrutura **§8** (`MP_EXCLUSIVA` com `HAVING COUNT(DISTINCT PA_RAIZ) = 1`).

---

## 4. Rotas propostas (api-delpi)

### 4.1 Rota principal — catálogo

```http
GET /products/exclusive-raw-materials/catalog
```

| Campo | Valor |
|-------|-------|
| operationId | `list_exclusive_raw_materials_catalog` |
| entity | `exclusive_raw_materials_catalog` |
| shape | `playbook_report` |

**Query params:**

| Param | Default | Descrição |
|-------|---------|-----------|
| `view` | `by_material` | `by_material` \| `by_finished_product` |
| `limit` | `50` | TOP N (máx. 500) |
| `offset` | `0` | Paginação |
| `finished_product_code` | — | Filtrar um PA específico |
| `raw_material_code` | — | Filtrar uma MP específica |
| `group_code` | — | Filtrar PA ou MP por grupo SB1010 |
| `max_depth` | `50` | Profundidade BOM (igual exclusivity) |
| `include_test_products` | `false` | Se `true`, inclui PA `8000%`/`8001%` |

#### `view=by_material` (default)

Responde: «quais matérias-primas são exclusivas?»

```json
{
  "items": [
    {
      "raw_material_code": "10010032",
      "raw_material_description": "CABO PVC ...",
      "raw_material_unit": "MT",
      "raw_material_group": "1001",
      "finished_product_code": "90261255",
      "finished_product_description": "CHICOTE DE LIGACAO ...",
      "finished_product_unit": "UN",
      "exclusive_raw_material": true
    }
  ],
  "summary": {
    "total_exclusive_materials": 120,
    "total_finished_products_with_exclusive": 95,
    "excluded_test_product_prefixes": ["8000", "8001"]
  }
}
```

#### `view=by_finished_product`

Responde: «quais produtos (PA) têm matéria-prima exclusiva?»

```json
{
  "items": [
    {
      "finished_product_code": "90261255",
      "finished_product_description": "CHICOTE DE LIGACAO ...",
      "exclusive_raw_material_count": 2,
      "exclusive_raw_materials": [
        { "raw_material_code": "10070183", "raw_material_description": "..." },
        { "raw_material_code": "10010032", "raw_material_description": "..." }
      ]
    }
  ],
  "summary": {
    "total_finished_products": 95,
    "total_exclusive_links": 120
  }
}
```

> **Nota performance:** consulta pesada (CTE recursiva em todos os PAs). Exigir `limit` default baixo; cache opcional (TTL 15–60 min) em fase 2.

---

### 4.2 Rota auxiliar — PAs com exclusividade (lista simples)

Alternativa mais leve se o catálogo completo for pesado demais:

```http
GET /products/with-exclusive-raw-materials
```

| operationId | `list_finished_products_with_exclusive_raw_materials` |
| shape | `paged_list` |

Retorna só códigos/descrições de PA + contagem de MPs exclusivas (sem detalhar cada MP). Detalhe → `structure/exclusivity` ou catalog `view=by_material`.

---

## 5. Fluxo do usuário no chat

```text
1. «Quais matérias-primas são exclusivas?»
   → list_exclusive_raw_materials_catalog?view=by_material&limit=20

2. «Quais produtos têm MP exclusiva?»
   → list_exclusive_raw_materials_catalog?view=by_finished_product

3. «Mostre a estrutura do 90261255 com exclusividade»
   → get_product_structure_exclusivity (já existe)

4. «Onde a MP 10010032 é usada?»
   → get_product_parents?code=10010032  (não confundir com exclusividade)
   → ou catalog filtrado raw_material_code=10010032
```

Desambiguação chat:

| Frase | Rota |
|-------|------|
| exclusiva(s), matéria-prima exclusiva, MP exclusiva | catalog ou structure/exclusivity |
| estrutura, BOM, componentes | `/structure` ou `/structure/exclusivity` se citar exclusiva |
| onde é usado, pais, árvore reversa | `/parents` |

---

## 6. Avaliação — flag de exclusividade nas rotas existentes

### 6.1 `GET /products/{code}/structure` — **não alterar (default)**

| Critério | Análise |
|----------|---------|
| **Consumidores** | Chat (`get_product_structure`), export Excel, testes OpenAPI |
| **Contrato atual** | `hierarchy` — `root` + `items[]` recursivos via `BomTreeBuilder`; campos: `code`, `description`, `type`, `unit`, `quantity` |
| **Custo de calcular exclusividade** | Alto — exige CTE `TODAS_ESTRUTURAS_VALIDAS` sobre **todos os PAs** por request |
| **Risco de quebra** | Baixo se campo opcional **additive**; **alto** se clientes validam schema estrito ou performance SLA |

**Recomendação:** **não** incluir `exclusive_raw_material` em `/structure` por default.

Motivos:

1. **Performance:** cada consulta de estrutura viraria scan global de BOM — inaceitável para MFEs que só querem árvore.
2. **Separação de responsabilidades:** `/structure` = BOM; `/structure/exclusivity` = BOM + regra de negócio exclusividade.
3. **Contrato estável:** [`fase-0-inventario-contrato-respostas.md`](./fase-0-inventario-contrato-respostas.md) define `get_product_structure` como `hierarchy` sem campos de playbook.

**Alternativa segura (fase 3, opcional):**

```http
GET /products/{code}/structure?include_exclusive_flags=true
```

- Só calcula exclusividade quando query param explícito.
- Documentar como **opt-in**; default `false`.
- Mesmo assim, preferir manter `/structure/exclusivity` como rota canônica para o chat.

---

### 6.2 `GET /products/{code}/parents` — **não alterar**

| Critério | Análise |
|----------|---------|
| **Uso** | «Onde este produto/componente é usado?» — árvore reversa |
| **Semântica exclusividade** | Não se aplica diretamente (parents ≠ «é exclusiva?») |
| **Risco** | Adicionar flags confundiria consumidores; cálculo global igualmente caro |

**Recomendação:** manter `/parents` sem flag. Para «MP X é exclusiva de qual PA?», usar **catalog** filtrado por `raw_material_code`.

---

### 6.3 `GET /products/{code}/structure/exclusivity` — **já é a rota de detalhe**

Campos existentes por linha (`product_playbook_repository.py`):

| Campo API | Significado |
|-----------|-------------|
| `exclusive_raw_material` | `SIM` / `NAO` / null |
| `total_valid_finished_products_using_mp` | contagem PAs |
| `exclusive_finished_product` | (interno no SQL) |

**Nenhuma mudança breaking** necessária. Opcional fase 2: normalizar `exclusive_raw_material` para boolean `true/false` **adicional** (`exclusive_raw_material_label` mantém `SIM`/`NAO` para compatibilidade).

---

### 6.4 Resumo decisão compatibilidade

| Rota | Alterar? | Motivo |
|------|----------|--------|
| `/structure` | ❌ Não (default) | Performance + contrato hierarchy |
| `/structure?include_exclusive_flags=` | ⚠️ Opcional futuro | Opt-in explícito |
| `/structure/exclusivity` | ✅ Já atende detalhe | — |
| `/parents` | ❌ Não | Semântica diferente |
| **Nova** `/exclusive-raw-materials/catalog` | ✅ Sim | Catálogo global |
| **Nova** `/with-exclusive-raw-materials` | ✅ Opcional | Lista leve de PAs |

---

## 7. Implementação api-delpi

### 7.1 Camadas

```text
GET /products/exclusive-raw-materials/catalog
  → build_list_exclusive_raw_materials_catalog_use_case()
    → ProductExclusiveRawMaterialRepository
      → fetch_exclusive_catalog_by_material()
      → fetch_exclusive_catalog_by_finished_product()
    → api_delpi_success(..., operation_id="list_exclusive_raw_materials_catalog")
```

Reutilizar:

- Filtros PA teste (`8000%`, `8001%`) — extrair constante compartilhada com `product_playbook_repository.py`
- Vigência `G1_FIM > today`
- `summarize_structure` / helpers de `product_playbook_service.py`

### 7.2 SQL base

Copiar CTEs de [`playbook-estrutura-produto-exclusividade-mp.md`](./playbook-estrutura-produto-exclusividade-mp.md) §8 (`ESTRUTURA_PA` → `MP_POR_PA` → `MP_EXCLUSIVA`).

Parametrizar:

- `TOP (@limit)` + offset via `ROW_NUMBER()` se necessário
- filtros opcionais `finished_product_code`, `raw_material_code`, `group_code`

### 7.3 Registro

```python
# route_contract_registry.py
"list_exclusive_raw_materials_catalog": RouteContract(
    "exclusive_raw_materials_catalog", "playbook_report"
),
```

### 7.4 Testes

| Teste | Assert |
|-------|--------|
| MP em 1 PA → exclusiva | item no catalog |
| MP em 2 PAs → não listada | ausente |
| PA 80001234 ignorado | `include_test_products=false` |
| `view=by_finished_product` | agrupa MPs por PA |
| Produto homologado `90261255` | ≥2 MPs exclusivas (playbook §11) |

Fixtures: `tests/fixtures/exclusive_raw_material_catalog.json`

---

## 8. Integração chat (minha-delpi-ai-api)

Doc: [`playbook-15-anexo-catalogo-exclusividade-mp.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-15-anexo-catalogo-exclusividade-mp.md)

Resumo:

| Arquivo | Ação |
|---------|------|
| `production_operational_intent.json` ou `product_query_intent.json` | Termos: «mp exclusiva», «matéria prima exclusiva», «quais produtos têm exclusiva» |
| `ExternalActionRouteSelectionService` | Path `/exclusive-raw-materials/catalog` **sem** `{code}` |
| `ChatProductQueryIntentService` | Não confundir com `/structure` genérico |
| Presenter | Tabela catalog + link «ver estrutura» → `structure/exclusivity` se usuário citar PA |
| `api-delpi-rotas-agente.md` | Frases exemplo |

Intents:

- **Catálogo** (sem código) → `list_exclusive_raw_materials_catalog`
- **Estrutura + exclusividade** (com código) → `get_product_structure_exclusivity` (existente)
- **Estrutura simples** → `get_product_structure`

---

## 9. Roadmap

| Fase | Entrega | Dependência |
|------|---------|-------------|
| **E1** | `GET /products/exclusive-raw-materials/catalog` (`view=by_material`) | ✅ api-delpi |
| **E2** | `view=by_finished_product` + paginação | ✅ E1 |
| **E3** | Chat intent + presenter + regressão | ✅ jun/2026 |
| **E4** (opcional) | Cache + `GET /products/with-exclusive-raw-materials` | métricas de latência |
| **E5** (opcional) | `?include_exclusive_flags=true` em `/structure` | só se demanda MFE |

---

## 10. Smoke

```bash
# Catálogo — MPs exclusivas
curl -s "$BASE/apps/api-delpi/products/exclusive-raw-materials/catalog?view=by_material&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.meta.operationId, .data.summary'

# PAs com exclusividade
curl -s "$BASE/apps/api-delpi/products/exclusive-raw-materials/catalog?view=by_finished_product&limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Detalhe (existente)
curl -s "$BASE/apps/api-delpi/products/90261255/structure/exclusivity" \
  -H "Authorization: Bearer $TOKEN" | jq '.data.summary.total_exclusive_raw_materials'
```

Frases chat: ver anexo chat §5.

---

## 11. Referências

| Doc | Conteúdo |
|-----|----------|
| [playbook-estrutura-produto-exclusividade-mp.md](./playbook-estrutura-produto-exclusividade-mp.md) | SQL e regras |
| [product_playbook_repository.py](../../app/infrastructure/persistence/totvs/product_repositories/product_playbook_repository.py) | Implementação atual |
| [fase-0-inventario-contrato-respostas.md](./fase-0-inventario-contrato-respostas.md) | Contratos existentes |
| [playbook-10-contrato-respostas-api-delpi.md](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md) | meta.shape |

---

## 12. Resumo executivo

- **Já existe** detalhe por PA: `/products/{code}/structure/exclusivity`.
- **Falta** catálogo global: nova rota `/products/exclusive-raw-materials/catalog` com duas visões (`by_material` / `by_finished_product`).
- **Não** colocar flag de exclusividade em `/structure` ou `/parents` por default — risco de performance e confusão semântica; rotas dedicadas preservam compatibilidade com outras aplicações.
