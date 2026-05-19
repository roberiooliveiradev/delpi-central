Instruções para consultas via API DELPI (`execute_external_action`, provider api-delpi):

Escolha mentalmente a rota antes de responder (o backend já executa a action adequada):

- **Produto por código** — descrição/ficha: `GET /products/{code}/analyser`. Estoque/saldo do item: `GET /products/{code}/stock`. Busca sem código exato: `GET /products/search`.
- **LMP** — listar várias: `GET /engineering/lmps`. Painel: `GET /engineering/lmps/dashboard`. Uma OV específica: `GET /engineering/lmps/{sale_number}` (número de OV não é código de produto).
- **Valor total de estoque da empresa** (KPI suprimentos): `GET /supplies/stock-value` — não usar estoque de produto.
- **SQL somente leitura**: `POST /data/sql` com campo `sql`.

Ao formatar a resposta: use o resumo humanizado da ferramenta; não invente filiais, quantidades ou OVs. Se `0 registro(s)`, informe claramente. Código com máscara (10.080.055) é válido.

Documento completo para RAG: `docs/knowledge/api-delpi-rotas-agente.md`.
