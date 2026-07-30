# Cadastro de produto (SB1) — padrões Delpi

Parte da [biblioteca de padrões TOTVS](./README.md).

---

## Campos recorrentes

| Campo | Significado | Nota Delpi |
|-------|-------------|------------|
| `B1_COD` | Código do produto | Chave de join com `BC_PRODUTO`, `B2_COD`, etc. |
| `B1_DESC` | Descrição | Labels de ranking / registros |
| `B1_UM` | Unidade de medida | Ver [unidades-medida.md](./unidades-medida.md) |
| `B1_CUSTD` | Custo padrão | Fallback de valoração quando `B2_CM1` do almoxarifado falta — [armazem-custo.md](./armazem-custo.md) |
| `B1_TPMAT` | Produto de terceiro (SX3) | `1` = Não · `2` = Sim |

---

## Produto de terceiro (`B1_TPMAT`)

Painéis de **refugo em R$** e filtros associados **excluem** `B1_TPMAT = 2` (Sim).

Constante de domínio (refugos): `THIRD_PARTY_PRODUCT_TPMAT = "2"` em `refugos_scope.py`.

### O que fazer

1. Em rota de valoração/perda de material alinhada ao painel scrap: `LTRIM(RTRIM(SB1.B1_TPMAT)) <> '2'` (ou constante).
2. Documentar o exclusão na doc da rota e no help do MFE quando o usuário puder estranhar a ausência do item.

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| Filtrar terceiro só no frontend | Totais e rankings ficam inconsistentes |
| Esquecer o filtro em uma das rotas do mesmo domínio (`resumo` vs `rankings` vs `registros`) | Divergência entre KPIs |

---

## Referências

- Refugos: [scrap-monitoring.md](../scrap-monitoring.md)
- Custo: [armazem-custo.md](./armazem-custo.md)
- Produtos (API geral): [02-produtos.md](../02-produtos.md)
