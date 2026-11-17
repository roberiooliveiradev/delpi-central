# Produtos de terceiros: valoração do inventário (B1_TPMAT)

**GLPI #1614 · Regra gerencial somente leitura**. Complementa
[cadastro-produto.md](./cadastro-produto.md), sem alterar o corpus DAVI congelado.

## Vocabulário Protheus

| Campo | Regra |
|---|---|
| `SB1010.B1_TPMAT` | `1` = produto próprio; `2` = terceiro |
| `SB1010.B1_COD` | Chave do material ao parear `SD3010.D3_COD` |
| `SB1010.B1_FILIAL` | Preferir cadastro da filial do movimento; fallback para global |
| `SD3010.D3_CUSTO1` | Valor total (não unitário) do ajuste de inventário |
| `SD3010.D3_QUANT` e `SB7010.B7_QUANT` | Quantidades e contagens físicas, sempre mantidas |

Não confundir `B1_TPMAT` (propriedade do material) com `SB6` (remessas e beneficiamento).

## O que fazer

1. Em consulta de **acuracidade física**, manter a presença, contagem e quantidade dos materiais de terceiros.
2. Em consulta do **impacto gerencial em R$** das divergências `INVENT`, usar `CASE WHEN B1_TPMAT = '2' THEN 0 ELSE D3_CUSTO1 END` na expressão **antes da agregação**, tanto no resumo quanto no detalhe/série/ranking.
3. Reutilizar `THIRD_PARTY_PRODUCT_TPMAT` de `app/domain/totvs/protheus_product_types.py` e `inventory_adjustment_monetary_value_sql` de `app/domain/services/supplies/inventory_adjustment_service.py`.
4. No SQL, selecionar no máximo um cadastro SB1 por movimento, com `OUTER APPLY TOP (1)` e preferência por `B1_FILIAL` da linha, depois filial global; não multiplicar o lançamento por vários cadastros do mesmo código.
5. Preservar a origem do custo e a valoração contábil R07/TTAT, que têm contrato distinto.

## O que NÃO fazer

- Não filtrar `B1_TPMAT=2` do **inventário físico**, embora no painel de Refugos a regra de negócio seja excluir esses produtos.
- Não implementar a máscara financeira no frontend nem editar custos no Protheus.
- Não multiplicar `D3_CUSTO1` por `D3_QUANT`, nem recalcular movimentos históricos.
- Não assumir `B1_TPMAT=2` quando o cadastro de produto está ausente.

Veja [escopo de implementação e validação](../../../../docs/12-roadmap-e-evolucao/supplies/GLPI-1614-MATERIAIS-TERCEIROS-ACURACIDADE-VALOR-ZERO.md).
