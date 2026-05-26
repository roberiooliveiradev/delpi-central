# Inteligência do chat — Onda 10

**Status:** concluída (maio/2026)  
**Pré-requisitos:** [Onda 9](./apresentacao-rica-chat-onda-9.md)

## Objetivo

Ampliar a cobertura de seleção de rotas, melhorar títulos do presenter com base no path da API, implementar nova rota `/products/{code}` na api-delpi e alcançar **100% de acerto** em suite de 36 cenários reais de seleção de ação.

---

## Entregas da onda

| # | Entrega | Descrição | Status |
|---|---------|-----------|--------|
| 10.1 | Rota `/products/{code}` | Nova rota na api-delpi retornando dados cadastrais do produto (leve, sem analyser pesado) | Concluído |
| 10.2 | Rota `/products/{code}/summary` | Nova rota consolidando produto + estoque + preços em chamada única | Concluído |
| 10.3 | Títulos contextuais no presenter | `present()` e `build_presentation()` agora recebem `path` e geram títulos precisos (Estrutura, Estoque, Parents, etc.) | Concluído |
| 10.4 | Ampliação do intent DESCRIPTION | Novos termos: "o que é o produto", "detalhes do", "me fale sobre", "informações completas", "dados cadastrais" | Concluído |
| 10.5 | Ampliação do intent PARENTS | Novos termos: "pai do", "quais produtos usam", "produtos que usam", "itens que usam" | Concluído |
| 10.6 | Detecção de pricing | "quanto custa", "custo do" adicionados como triggers para `/pricing` | Concluído |
| 10.7 | Detecção de notas fiscais | "notas de entrada", "notas de saída" com distinção inbound/outbound | Concluído |
| 10.8 | Fix seleção de OVs | `/sales/` preferido para "listar ordens de venda"; paths com `/products/` excluídos do matcher | Concluído |
| 10.9 | Fix filtro de candidatos | "ordens de venda", "pedidos de venda" adicionados ao branch LMP/OV no `find_candidate_actions` | Concluído |
| 10.10 | Detecção KPI expandida | Mais path tokens reconhecidos (snapshot, ebitda, pmr, closing-rate, etc.) | Concluído |
| 10.11 | Suite de testes 36 cenários | Cobertura completa: descrição, estrutura, estoque, parents, pricing, fornecedores, clientes, compras, vendas, roteiro, inspeção, movimentações, notas, search, LMPs, OVs, KPIs | Concluído |

---

## 10.1 — Rota `/products/{code}`

Rota leve que retorna apenas dados cadastrais do produto (`code`, `description`, `type`, `unit`, `group_code`, `active`, `default_warehouse`, `last_purchase_price`, `standard_cost`, `last_revision_date`, `ncm_ipi_position`).

**Scoring:** +200 para intent DESCRIPTION (preferido sobre analyser).

## 10.2 — Rota `/products/{code}/summary`

Consolida produto + estoque (top 10 locais) + preços em uma única chamada. Útil para quando o agente precisa de uma visão geral sem múltiplas requisições.

## 10.3 — Títulos contextuais

O método `_infer_items_title(items, path)` analisa o path da API chamada e retorna títulos como:
- `/structure` → "Estrutura do produto"
- `/parents` → "Produtos pai (onde é usado)"
- `/stock` → "Estoque do produto"
- `/suppliers` → "Fornecedores do produto"
- `/customers` → "Clientes do produto"
- etc.

Quando o path não é fornecido, heurísticas baseadas nos campos (`level`, `quantity`, `branch`, `warehouse`) inferem o tipo.

## 10.4–10.7 — Ampliação de vocabulário

Novos termos adicionados a:
- `_looks_like_description_question`: "o que é o produto", "detalhes do", "me fale sobre", "dados cadastrais", "informações completas"
- `_looks_like_parents_question`: "pai do", "pais do", "quais produtos usam", "produtos que usam"
- `wants_pricing`: "quanto custa", "custo do"
- `wants_invoices`: "nota de entrada", "notas de saída" (com distinção inbound/outbound)
- `_looks_like_product_question`: "quanto custa", "custo do", "pai do", "notas de entrada/saída"

## 10.8–10.9 — Fix seleção de OVs

Problema: "listar ordens de venda" selecionava `/products/{code}/sales` ou `/products/search`.

Solução:
1. `_select_sale_orders_action` agora exclui paths com `/products/` ou `{code}`
2. `find_candidate_actions` agora reconhece "ordens de venda" e "pedidos de venda" no branch LMP/OV (que inclui `/sales%`)
3. Removido "venda" isolado da lista de triggers de products (era ambíguo)

## 10.11 — Suite de testes

36 cenários testados com 100% de acerto:

```
✅ descrição do produto 10080001    → /products/{code}
✅ o que é o produto 10080001       → /products/{code}
✅ qual a descrição do 10080001     → /products/{code}
✅ detalhes do produto 90260147     → /products/{code}
✅ me fale sobre o 10080001         → /products/{code}
✅ estrutura do produto 10080001    → /products/{code}/structure
✅ bom do produto 10080001          → /products/{code}/structure
✅ composição do 10080001           → /products/{code}/structure
✅ estoque do produto 10080001      → /products/{code}/stock
✅ saldo do produto 10080001        → /products/{code}/stock
✅ onde é usado o 10080001          → /products/{code}/parents
✅ pai do 10080001                  → /products/{code}/parents
✅ quais produtos usam o 10080001   → /products/{code}/parents
✅ preço do produto 10080001        → /products/{code}/pricing
✅ tabela de preço do 10080001      → /products/{code}/pricing
✅ quanto custa o 10080001          → /products/{code}/pricing
✅ fornecedores do produto 10080001 → /products/{code}/suppliers
✅ clientes do produto 10080001     → /products/{code}/customers
✅ compras do produto 10080001      → /products/{code}/purchases
✅ vendas do produto 10080001       → /products/{code}/sales
✅ roteiro do produto 10080001      → /products/{code}/guide
✅ inspeção do produto 10080001     → /products/{code}/inspection
✅ movimentações internas do 10080001 → /products/{code}/internal-movements
✅ notas de entrada do 10080001     → /products/{code}/inbound-invoice-items
✅ notas de saída do 10080001       → /products/{code}/outbound-invoice-items
✅ pesquise produtos cabo           → /products/search
✅ buscar produto motor             → /products/search
✅ procure por eixo                 → /products/search
✅ listar LMPs                      → /engineering/lmps
✅ LMPs em andamento                → /engineering/lmps
✅ listar ordens de venda           → /sales/
✅ pedidos de venda abertos         → /sales/
✅ qual o CPV?                      → /supplies/cpv
✅ qual o OTD de suprimentos?       → /supplies/otd
✅ giro de estoque                  → /supplies/inventory-turnover
✅ valor total de estoque           → /supplies/stock-value
```

---

## Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `api-delpi/app/interface/http/routes/product_routes.py` | Novas rotas `/products/{code}` e `/products/{code}/summary` |
| `minha-delpi-ai-api/.../external_action_result_presenter.py` | `present(path=)`, `build_presentation(path=)`, `_infer_items_title()`, ampliação de `_looks_like_kpi_response` |
| `minha-delpi-ai-api/.../external_action_selection_service.py` | Fix OVs, novos termos em `wants_*`, `_looks_like_product_question` expandido |
| `minha-delpi-ai-api/.../postgres_external_action_repository.py` | Branch LMP/OV expandido para ordens de venda; novos termos no filtro products |
| `minha-delpi-ai-api/.../chat_product_query_intent_service.py` | Vocabulário expandido em `_looks_like_description_question`, `_looks_like_parents_question`, `_looks_like_product_sub_intent` |
| `minha-delpi-ai-api/.../chat_tool_context_service.py` | Passa `path=` ao presenter |
| `minha-delpi-ai-api/.../execute_external_action_use_case.py` | Passa `path=` ao `build_presentation` |
| `tests/fixtures/chat_intelligence_regression_cases.py` | Ajuste "informações completas" → DESCRIPTION |
