# Cadastro de cliente (SA1)

Convenções Delpi ao buscar / identificar cliente TOTVS para Portal Comercial e emissões.

## Campos de nome

| Campo | Uso |
|-------|-----|
| `A1_NOME` | Razão social |
| `A1_NREDUZ` | Nome fantasia / reduzido operacional (pedidos, gap, Minha carteira) |

Busca de vínculo de carteira (`search_active_customers`) deve casar em **código**, **`A1_NOME`** e **`A1_NREDUZ`**. Display preferencial: `COALESCE(NULLIF(RTRIM(A1_NREDUZ), ''), A1_NOME)`.

Referência de implementação: lookup NF (`TotvsInvoiceIssuanceLookupRepository.search_customers`) já inclui `A1_NREDUZ`.

## Bloqueio (`A1_MSBLQL`)

- `'1'` = bloqueado no cadastro.
- Gap «sem cobertura» usa **pedidos abertos** (SC5/view) e **não** filtra SA1 — contas bloqueadas com pedido aberto aparecem no painel.
- Busca para **vincular à carteira** deve **incluir** bloqueados (só exclui `D_E_L_E_T_`), senão o admin não consegue amarrar o gap.

## Loja (`A1_LOJA` / `C5_LOJACLI`)

Loja numérica: normalizar com `zfill(2)` (`1` → `01`) em chaves de cobertura / identidade. SC5 e SA1 podem divergir no padding. Na agregação de métricas, o join SA1×SC5 casa loja por igualdade **ou** por `TRY_CAST(… AS INT)`.

## Gap «sem cobertura» × cadastro

Universo operacional = pedidos abertos **∩ SA1**. Código só no SC5 (órfão, sem linha em `SA1010`) **não** entra no gap nem na busca de vínculo — regularizar cadastro no Protheus antes de amarrar carteira.
