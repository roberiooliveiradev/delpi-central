# Centro do cliente (SA7)

O centro que separa unidades do mesmo código de cliente (por exemplo as lojas WEG) **não** está no cadastro SA1. Está na amarração produto–cliente.

| Campo | Tabela | Uso |
|-------|--------|-----|
| `A7_XCENT` | `SA7010` (dicionário `SA7`) | Centro do cliente, texto. Preenchido na amarração produto + cliente + loja |

## Grão

Uma amarração é `A7_PRODUTO` + `A7_CLIENTE` + `A7_LOJA`. Nesse trio há no máximo um centro distinto. A mesma loja pode ter vários centros em produtos diferentes (a loja `01` usa `1100` e `1200`).

`A1_NOME` e `A1_NREDUZ` não são o centro. Várias lojas compartilham a mesma razão social. Ver [cadastro-cliente.md](./cadastro-cliente.md).

## O que fazer

- Filtrar fato comercial (linha de pedido `SC6` ou item de nota `SD2`/`SD1`) com `customer_centers` no filtro canônico `CommercialAnalysisFilterService`.
- Entrar na `SA7010` só quando o filtro vier preenchido, pelo fragmento `customer_center_link_sql` em `app/domain/totvs/protheus_customer_center.py`.
- O fragmento agrupa produto + cliente + loja e usa `MAX(A7_XCENT)`, para linhas repetidas da amarração não multiplicarem quantidade.
- Ligar o fato com `RTRIM/LTRIM` em produto, cliente e loja.
- Tratar linha sem amarração, ou com centro vazio, como fora do filtro: o `INNER JOIN` mais `IN` não a inclui.

## O que não fazer

- Não gravar allowlist dos centros no código. Um centro novo no Protheus passa a valer sem deploy de regra.
- Não juntar a `SA7010` crua na linha do fato.
- Não usar `A1_NOME` para separar unidades que compartilham razão social.
- Não aplicar este join em fato sem produto (cabeçalho de proposta `AD1`).

## Censo conhecido (não é allowlist)

Centros preenchidos hoje existem só no cliente `000001`. Exemplos: `1100` e `1200` na loja `01`, `1320` na loja `11`, `1505` na loja `12`, `1106` na loja `09`, `1700` na loja `06`. Lojas sem nenhum centro continuam acessíveis por `customer_code_stores`.
