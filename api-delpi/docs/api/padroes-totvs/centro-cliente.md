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

## Dinâmica e censo (não é allowlist)

A regra do produto é **genérica**: qualquer cliente/loja com `A7_XCENT` na SA7 entra no catálogo e na conferência do vínculo. Não há allowlist por código de cliente (WEG é só o exemplo mais comum).

Catálogo e assignments leem a SA7 em tempo de consulta. Centro **novo** no Protheus passa a aparecer no seletor e nas linhas sem deploy de regra. O vínculo antigo da carteira **não** herda sozinho: só vale depois de ser gravado e conferido contra a lista atual.

Censo observado (snapshot de dados, sujeito a mudar no Protheus): no ambiente Delpi os centros preenchidos concentravam-se no cliente `000001` (ex.: `1100`/`1200` loja `01`, `1320` loja `11`, `1505` loja `12`, `1106` loja `09`, `1700` loja `06`). Lojas sem nenhum centro continuam acessíveis por `customer_code_stores` / fallback do par.

A lista para um seletor é `GET /commercial/customer-centers` (`list_commercial_customer_centers`). O rótulo é o nome reduzido de uma loja do centro mais o código, não um mapa fixo de unidades.

O mapa código + loja + centro é `GET /commercial/customer-center-assignments` (`list_commercial_customer_center_assignments`). O vínculo da carteira usa esse trio.

Pedidos em aberto, pedidos recém-encerrados, notas da conta e a série de faturamento aceitam `customer_centers`. Sem o parâmetro, o predicado não entra. A linha de pedido projeta o centro com `LEFT JOIN` no mesmo fragmento agrupado.
