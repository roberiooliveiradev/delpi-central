Instruções para consultas via API DELPI (`execute_external_action`, provider api-delpi):

Escolha mentalmente a rota antes de responder (o backend já executa a action adequada):

**Produtos**
- Cadastro / descrição: `GET /products/{code}` ou resumo `GET /products/{code}/summary`
- Ficha completa: `GET /products/{code}/analyser`
- Estoque do item: `GET /products/{code}/stock`
- Busca sem código: `GET /products/search`
- Estrutura BOM: `GET /products/{code}/structure`
- Onde é usado: `GET /products/{code}/parents`
- Preço: `GET /products/{code}/pricing`
- Fornecedores/clientes/compras/vendas/NF: paths sob `/products/{code}/...`

**Engenharia**
- Listar LMPs: `GET /engineering/lmps`
- KPIs painel: `GET /engineering/lmps/dashboard/summary`
- Detalhe por OV: `GET /engineering/lmps/{sale_number}` — OV não é código de produto

**Suprimentos (KPI empresa)**
- Valor total de estoque: `GET /supplies/stock-value` — não confundir com estoque de produto
- Giro: `GET /supplies/inventory-turnover`

**Vendas**
- Listar ordens de venda: `GET /sales/` — não confundir com `/products/{code}/sales`

**SQL**
- `POST /data/sql` com campo `sql` (somente SELECT)

Ao formatar: use `humanizedSummary`; não invente filiais, quantidades ou OVs. Código com máscara (10.080.055) é válido.

Documento RAG completo: `docs/knowledge/api-delpi-rotas-agente.md`.
