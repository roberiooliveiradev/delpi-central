# Changelog — Diretivas de produto no chat (jun/2026)

Integração ponta a ponta de `GET /products/directives/{identifier}` (api-delpi) no **chat base** — roteamento, apresentação e comentário operacional.

## Contexto

Perguntas como «diretivas 90260882» ou «diretivas 10018137» devem retornar **estrutura (BOM)**, **fornecedores por MP** e **última NF de compra**, não o cadastro genérico (`GET /products/{code}`).

Playbook api-delpi: `api-delpi/docs/roadmaps/playbook-diretivas-produto.md`.

---

## 1. api-delpi

| Item | Arquivo / rota |
|------|----------------|
| Rota HTTP | `GET /products/directives/{identifier}` → `get_product_directives` |
| Contrato | `shape: composite_analysis`, `entity: product_directives` |
| Payload | `resolution`, `product`, `structure`, `raw_materials[]` (suppliers + last_purchase), `summary` |
| Repositórios batch | `product_raw_material_price_repository`, `product_suppliers_repository` (consultas em lote) |

---

## 2. minha-delpi-ai-api — Roteamento (seleção de action)

### Vocabulário e intent

| Arquivo | Alteração |
|---------|-----------|
| `product_query_intent.json` | Seção `directives.terms` |
| `external_action_responses.json` | `vocabularyFastPaths` → `productDirectives` |
| `api_route_domains.json` | Domínio `product_directives` |

### Fast-path declarativo

| Módulo | Responsabilidade |
|--------|------------------|
| `ExternalActionVocabularyRouteSelectionService` | Matcher `directives` + markers `/directives/`, `get_product_directives` |
| `ExternalActionProductRouteSelectionService._find_allowed_actions_by_markers` | Lookup no **catálogo completo** (`list_actions`) — não depende do top-N semântico |
| `postgres_external_action_repository.find_candidate_actions` | Keywords `diretiva(s)` no ramo produto (defesa extra) |

**Bug corrigido (jun/2026):** com ~179 actions autorizadas, `find_candidate_actions` (limite 80) omitia `/products/directives/`; o pipeline caía em `get_product_detail`. Solução: vocabulary fast-path resolve a action pelo catálogo via markers JSON.

### Testes de roteamento

- `test_external_action_vocabulary_route_selection_service.py` — incl. regressão quando candidatos semânticos não trazem diretivas
- `test_external_action_product_route_selection_service.py::test_select_product_directives_prefers_directives_route`
- `chat_intelligence_regression_cases.py` — casos `directives` + código DELPI / referência cliente

---

## 3. minha-delpi-ai-api — Apresentação

### Perfil e entidade

| Arquivo | Chave |
|---------|-------|
| `chat_api_delpi_response_profile_service.py` | `product_directives`, fallback `/directives/` |
| `presentation_profiles.json` | Perfil `directives`, `tableAssembly.builder`, `commentaryProfileKey: directives` |
| `presenter_content.json` | `routePresentations.directives`, `compositeAnalysisInsights.directives` |
| `column_labels.json` | `directivesRawMaterials` |

### Presenter

| Módulo | Função |
|--------|--------|
| `product_directives_presenter.py` | Prosa + **3 tabelas separadas** via `build_all_table_presentations` |
| `entity_route_presenter.py` | Rota humanizada `product_directives` |
| `presentation_builder_presenter.py` | `_build_presentation_by_entity` |
| `external_action_result_presenter.py` | `build_product_directives_table_presentations` |

**Tabelas (jun/2026):**

1. **Estrutura do produto (BOM)** — somente MPs de `raw_materials[]` (`directivesRawMaterials`)
2. **Fornecedores por matéria-prima** — vínculos MP × fornecedor com código/descrição da MP (`directivesSuppliers`)
3. **Última compra por matéria-prima** — NF recente por MP com código/descrição da MP (`directivesLastPurchase`)

### Montagem de tabelas (Playbook 12)

| Módulo | Alteração |
|--------|-----------|
| `ChatPresentationTableAssemblyService.builder_registry` | Registro de `build_product_directives_table_presentations` |

**Bug corrigido (jun/2026):** o perfil JSON referenciava o builder, mas o registry não o expunha → `tablePresentations: null`, UI só com texto e mensagem «sem dados tabulares para visualização».

### dataAnswer / comentário

| Módulo | Alteração |
|--------|-----------|
| `ChatOperationalDataCommentaryService._build_directives_commentary` | Perfil `directives` (substitui `generic_list` vazio) |
| `ChatDataInsightService._resolve_rows` | Fallback em `raw_materials[]` quando não há `items` |
| `humanized_data_response.json` | `nextActions` e `recommendations.directives` |

---

## 4. MFE (minha-delpi-chat)

| Módulo | Alteração |
|--------|-----------|
| `nativeSingleViewBuilder.ts` / `renderPlanSegmentBuilder.ts` | Modo **Tabela** e **Automático** com **todas** as `tablePresentations` (não só a primeira) |
| `presentationCategoryFilter.ts` | Filtros usam `fieldLabels` das colunas da API (PT-BR) |
| `ChatRichTable.tsx` / `ChatRichChart.tsx` | Repasse de rótulos humanizados aos dropdowns de filtro |

Testes: `assistantContentDirectivesModes.test.ts`, `presentationCategoryFilter.test.ts`, `ChatRichTable.filterLabels.test.ts`, `nativeSingleViewBuilder.test.ts`, `renderPlanSegmentBuilder.test.ts`.

---

## 5. Ajustes de conteúdo tabular (jun/2026 — segunda entrega)

| Tabela | Comportamento |
|--------|----------------|
| **Estrutura (BOM)** | Somente **matérias-primas** (`raw_materials[]`), perfil `directivesRawMaterials` — sem PIs/intermediários |
| **Fornecedores** | Colunas **Código MP** e **Descrição MP** antes do fornecedor (`directivesSuppliers`) |
| **Última compra** | Colunas **Código MP** e **Descrição MP** antes da NF (`directivesLastPurchase`) |

**Normalização de colunas:** `ChatPresentationFieldNormalizationService` re-detecta perfil via `detect` em `column_labels.json`. Fornecedores excluem linhas com `invoice_number`; última compra exige `raw_material_code` + `invoice_number` no path `/directives/`.

**Modos de apresentação:**

| Modo | UI esperada |
|------|-------------|
| Automático | Resumo + 3 tabelas (stack) |
| Tabela | 3 tabelas (`operationalTables` / `tablePresentations`) |
| Texto | Prosa + tabelas GFM embutidas |

Regressão: `test_product_directives_presentation_modes.py`, fixture `product_directives_90260882.json`, gate P6 `product_directives_auto` em `presentation_render_plan_gate.py`.

---

## 6. DOCIE (documentação only)

`docs/roadmap/docie-desacoplamento-selecao-rotas-openapi.md` — plano para registry declarativo de rotas (fases futuras; não bloqueia diretivas).

---

## 7. Validação

```bash
# Unitários API (container)
docker exec delpi-minha-delpi-ai-api env PYTHONPATH=/app pytest \
  tests/unit/domain/services/test_product_directives_presenter.py \
  tests/unit/application/use_cases/test_product_directives_presentation_modes.py \
  tests/unit/application/services/test_external_action_vocabulary_route_selection_service.py \
  tests/unit/domain/services/test_presentation_render_contract.py -q

# api-delpi
docker exec delpi-api-delpi env PYTHONPATH=/app pytest tests/test_product_directives.py -q

# MFE
cd plugins/minha-delpi-chat && npm run test -- --run \
  src/ui/components/assistantContentDirectivesModes.test.ts \
  src/ui/components/presentationCategoryFilter.test.ts \
  src/ui/components/ChatRichTable.filterLabels.test.ts
```

# E2E gateway (rober / 1234)
TOKEN=$(curl -s -X POST "http://localhost/auth/realms/delpi/protocol/openid-connect/token" \
  -d "client_id=delpi-central" -d "username=rober" -d "password=1234" -d "grant_type=password" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"message":"diretivas 90260882"}' \
  "http://localhost/apps/minha-delpi-ai/api/chat/sessions/<SESSION_ID>/messages" \
  | python3 -c "
import sys, json
dbg = json.load(sys.stdin).get('adminDebug') or {}
tc = (dbg.get('tooling') or {}).get('toolCalls') or [{}])[0]
meta = tc.get('metadata') or {}
print('path:', meta.get('path'))
print('actionId:', (tc.get('arguments') or {}).get('actionId'))
print('table rows:', len((meta.get('tablePresentation') or meta.get('presentation') or {}).get('rows') or []))
print('tablePresentations:', len(meta.get('tablePresentations') or []))
"
```

**Esperado:**

- `path`: `/products/directives/90260882`
- `actionId`: `api_delpi.products.get_product_directives`
- **3 tabelas:** MPs na estrutura; fornecedores e última compra com **Código MP** e **Descrição MP**
- Filtros de tabela/gráfico com rótulos PT-BR (não snake_case inglês)
- Sem «A consulta não retornou registros» nem sugestões `generic_list` indevidas

---

## 8. Correção api-delpi — NF de frete na última compra (jun/2026)

**Problema:** em alguns MPs, `last_purchase` nas diretivas (e em `GET /products/{code}/last-purchase`) apontava para transportadora ou empresa de logística — nota de **frete** alocada no código da MP (`SD1010.D1_QUANT = 0`), não compra de material.

**Correção (api-delpi):** `PurchaseValidityFilterService` + `D1_QUANT > 0` em `ProductRawMaterialPriceRepository`. O chat **não** precisa de patch local: consome a rota `get_product_directives` / `get_product_last_purchase`.

Documentação: `api-delpi/docs/api/compras-validas-frete-mp-changelog-jun2026.md`.

**Exemplo homologado:** MP `10090481` — antes RODOLOG LOGISTICA (qty 0); depois DELPI COMPONENTES LTDA (qty 150).

---

## 9. Arquivos tocados (resumo)

```
api-delpi/
  app/.../get_product_directives (rota, serviço, repositórios)
  docs/roadmaps/playbook-diretivas-produto.md

minha-delpi-ai-api/
  app/application/services/external_actions/
    external_action_vocabulary_route_selection_service.py
    external_action_product_route_selection_service.py
  app/domain/services/
    chat_presentation_table_assembly_service.py
    chat_data_insight_service.py
    chat_operational_data_commentary_service.py
    external_actions/presenters/product_directives_presenter.py
    external_actions/external_action_result_presenter.py
  app/infrastructure/persistence/postgres_external_action_repository.py
  app/content/pt-BR/assistant/
    product_query_intent.json
    external_action_responses.json
    presentation_profiles.json
    presenter_content.json
    column_labels.json
    humanized_data_response.json
  docs/changelog/2026-06-product-directives-chat.md
  tests/unit/... (vocabulary, presenter, presentation modes, regression cases)

plugins/minha-delpi-chat/
  src/ui/components/nativeSingleViewBuilder.ts
  src/ui/components/renderPlanSegmentBuilder.ts
  src/ui/components/presentationCategoryFilter.ts
  src/ui/components/ChatRichTable.tsx
  src/ui/components/ChatRichChart.tsx
  src/ui/components/*.test.ts (directives modes, filtros, render plan)
```
