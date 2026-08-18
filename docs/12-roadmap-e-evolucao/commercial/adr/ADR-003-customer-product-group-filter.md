# ADR — Filtro família/grupo na Minha Carteira

**Status:** aceito (ago/2026)  
**Contexto:** P-CLI-FILT — filtrar carteira por família/grupo de produto.

## Decisão

1. **Conta → Oportunidades** já filtra por `product_group` (B1_GRUPO) via BFF analytics — manter.
2. **Minha Carteira (lista de clientes):** o dataset é agregado de **pedidos em aberto**; o item TOTVS traz `produto`, **não** `B1_GRUPO`.
3. Até enriquecer open-orders com grupo, a lista aceita filtro por **código de produto** (match em linhas em aberto do cliente).
4. Filtro por família/grupo na lista de clientes = **Backlog** até o envelope open-orders incluir `product_group` (api-delpi + BFF).

## Consequências

- Não inventar classificação de família no MFE.
- Não chamar api-delpi direto do MFE.
