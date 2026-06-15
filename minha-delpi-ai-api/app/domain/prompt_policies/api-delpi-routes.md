Instruções para consultas via API DELPI (`execute_external_action`, provider api-delpi):

Escolha mentalmente a rota antes de responder (o backend já executa a action adequada):

**Produtos**
- Cadastro / descrição: `GET /products/{code}` ou resumo `GET /products/{code}/summary`
- Ficha completa: `GET /products/{code}/analyser`
- Estoque do item: `GET /products/{code}/stock`
- Busca sem código ou por grupo: `GET /products/search` (`description` e/ou `group_code`; ex.: grupo 1008 ≠ produto 1008)
- Estrutura BOM: `GET /products/{code}/structure`
- Onde é usado: `GET /products/{code}/parents`
- Preço: `GET /products/{code}/pricing`
- Fornecedores/clientes/compras/vendas/NF: paths sob `/products/{code}/...`

**Engenharia**
- Listar LMPs: `GET /engineering/lmps`
- KPIs painel: `GET /engineering/lmps/dashboard/summary`
- Itens paginados do painel: `GET /engineering/lmps/dashboard/items`
- Gráficos do painel: `GET /engineering/lmps/dashboard/charts`
- Detalhe por OV: `GET /engineering/lmps/{sale_number}` — OV não é código de produto; use `date_start`, `date_end`, `branch` quando o escopo importar

**Suprimentos (KPI empresa)**
- Valor total de estoque: `GET /supplies/stock-value` — não confundir com estoque de produto
- Giro: `GET /supplies/inventory-turnover`
- Economia em negociações de compras (IDD, planilha por filial): `GET /supplies/negotiation-savings/summary` — use `start_date`/`end_date`; opcional `branch` 01/02

**Vendas**
- Listar ordens de venda: `GET /sales/` — não confundir com `/products/{code}/sales`

**SQL**
- `POST /data/sql` com campo `sql` (somente SELECT)

Ao formatar: use `humanizedSummary`; não invente filiais, quantidades ou OVs. Código com máscara (10.080.055) é válido.

Documento RAG completo: `docs/knowledge/api-delpi-rotas-agente.md`.
