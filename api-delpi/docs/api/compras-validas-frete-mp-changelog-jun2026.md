# Compras válidas de MP — exclusão de NF de frete (jun/2026)

Registro da correção em **última compra**, **diretivas** e **ranking de compras** quando notas de transportadora/frete aparecem alocadas no código da matéria-prima em `SD1010`.

Playbooks relacionados:

- [playbook-diretivas-produto.md](../roadmaps/playbook-diretivas-produto.md)
- [playbook-analise-preco-materia-prima.md](../roadmaps/playbook-analise-preco-materia-prima.md)

---

## 1. Problema

Perguntas de **diretivas** e `GET /products/{code}/last-purchase` listavam, em alguns MPs, a **transportadora** como última compra — embora o filtro existente já excluía fornecedores com `%TRANSP%` no nome e os internos `000019` / `001149`.

**Causa:** no Protheus, notas de **frete** podem ser escritas no `SD1010` com o **código da MP** (`D1_COD`), sem quantidade de material:

| Campo | NF de frete (alocada na MP) | NF de compra real |
|-------|----------------------------|-------------------|
| `D1_QUANT` | `0` | `> 0` |
| `D1_TES` | tipicamente `040` | `001`, `204`, … |
| `D1_PEDIDO` | vazio | pode ter pedido |
| `D1_CF` | tipicamente `2352` | `2101`, `2151`, … |
| Fornecedor | pode **não** conter «TRANSP» (ex.: RODOLOG LOGISTICA LTDA) | fornecedor de material |

Homologação SQL (`POST /data/sql`):

```sql
-- Última linha bruta vs última compra válida (MP 10090481)
SELECT TOP 5 SD1.D1_DOC, SD1.D1_EMISSAO, SD1.D1_QUANT, SA2.A2_NOME
FROM SD1010 SD1 WITH (NOLOCK)
INNER JOIN SA2010 SA2 ON SA2.A2_COD = SD1.D1_FORNECE AND SA2.A2_LOJA = SD1.D1_LOJA AND SA2.D_E_L_E_T_ = ''
WHERE SD1.D_E_L_E_T_ = '' AND SD1.D1_COD = '10090481'
ORDER BY SD1.D1_EMISSAO DESC;
```

Antes do fix: última NF = RODOLOG LOGISTICA (`D1_QUANT = 0`). Depois: DELPI COMPONENTES LTDA (`D1_QUANT = 150`).

---

## 2. Solução (módulo canônico)

| Artefato | Responsabilidade |
|----------|------------------|
| `PurchaseValidityFilterService` | Filtros SQL reutilizáveis em repositórios SD1010 |
| `supplier_filter_sql()` | Internos + `UPPER(A2_NOME) NOT LIKE '%TRANSP%'` |
| `purchase_line_filter_sql()` | **`AND SD1.D1_QUANT > 0`** |
| `valid_purchase_filter_sql()` | União dos dois (uso padrão em compras válidas) |

**Não** filtrar por `%LOGIST%` ou `%EXPRESSO%` no nome: existem fornecedores legítimos (ex.: TSD LOGISTICA E DISTRIBUIDORA) com compras reais `D1_QUANT > 0`.

---

## 3. Rotas e repositórios afetados

| Rota / `operationId` | Repositório |
|----------------------|-------------|
| `GET /products/directives/{identifier}` · `get_product_directives` | `ProductRawMaterialPriceRepository.fetch_last_purchases_for_codes` |
| `GET /products/{code}/last-purchase` · `get_product_last_purchase` | `fetch_last_purchase` |
| Histórico de preço de compra | `fetch_purchase_price_history` |
| `GET /purchases/top-products` · `get_purchases_top_products` | `PurchasesRankingRepository` |

---

## 4. Testes

```bash
docker exec delpi-api-delpi sh -c 'cd /app && PYTHONPATH=/app pytest \
  tests/test_purchase_validity_filter_service.py \
  tests/test_product_directives.py -q'
```

Validação HTTP (token de serviço):

```bash
curl -s -H "Authorization: Bearer $API_DELPI_INTERNAL_SERVICE_TOKEN" \
  -H "X-Delpi-Caller-App: smoke" \
  "http://localhost/apps/api-delpi/products/10090481/last-purchase" \
  | jq '.data.last_purchase.supplier_name, .data.last_purchase.quantity'
# Esperado: fornecedor de material, quantity > 0
```

---

## 5. Commit de referência

`fix(api-delpi): exclui NF de frete na última compra de MPs` (jun/2026).
