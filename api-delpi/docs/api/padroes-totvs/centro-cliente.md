# Centro do cliente (SA7 / ZC0)

O centro que separa unidades do mesmo código de cliente (por exemplo as lojas WEG) **não** está no cadastro SA1 nem na nota fiscal. Está na amarração produto–cliente e no cadastro mestre customizado.

| Campo | Tabela | Uso |
|-------|--------|-----|
| `A7_XCENT` | `SA7010` (dicionário `SA7`) | Centro do cliente, texto. Preenchido na amarração produto + cliente + loja |
| `ZC0_CODIGO` / `ZC0_DESC` / `ZC0_ATIVO` | `ZC0010` (dicionário `ZC0`) | Cadastro mestre do centro no contexto cliente + loja |

## Grão

Uma amarração é `A7_PRODUTO` + `A7_CLIENTE` + `A7_LOJA`. Nesse trio há no máximo um centro distinto. A mesma loja pode ter vários centros em produtos diferentes (a loja `01` usa `1100` e `1200`).

`A1_NOME` e `A1_NREDUZ` não são o centro. Várias lojas compartilham a mesma razão social. Ver [cadastro-cliente.md](./cadastro-cliente.md).

O código do centro **não** é global: `ZC0` amarra `ZC0_CLIENT` + `ZC0_LOJA` + `ZC0_CODIGO`. Não juntar ZC0 só pelo código.

## Filial compartilhada

SA7 (e, nesta instalação, ZC0) é tratado como dicionário compartilhado: os fragments SQL **não** filtram `A7_FILIAL` / `ZC0_FILIAL`. Não hardcodar filial vazia no consumidor; o grouped subquery já ignora o campo, alinhado ao censo atual (`A7_FILIAL` tende a ser vazio).

## Classificação vs filtro

Há dois usos distintos:

| Uso | Join | Linha sem `A7_XCENT` |
|-----|------|----------------------|
| Filtro `customer_centers` nas rotas ROL/OTD | `INNER JOIN` via `customer_center_link_sql` — só entra quando o parâmetro vem preenchido | Fora do recorte |
| Classificação analítica (`GET /commercial/rol/by-customer-center`) | `LEFT JOIN` via `customer_center_classification_join_sql` + mestre `customer_center_master_join_sql` | Permanece no resultado como `customer_center = null`, `customer_center_name = "SEM CENTRO"` |

O fragmento de filtro agrupa produto + cliente + loja e usa `MAX(A7_XCENT)`, para linhas repetidas da amarração não multiplicarem quantidade. O de classificação usa `MAX(NULLIF(A7_XCENT, ''))` para centro vazio virar NULL.

## Snapshot atual (limitação conhecida)

A classificação **não** é gravada na SD2/SF2. A rota lê o cadastro **vigente** de SA7/ZC0.

Se hoje o produto do cliente/loja está no centro `1200` e amanhã `A7_XCENT` mudar para `1300`, uma consulta histórica reclassifica faturamentos antigos no `1300`. Não há tabela de histórico nesta versão.

## O que fazer

- Filtrar fato comercial (linha de pedido `SC6` ou item de nota `SD2`/`SD1`) com `customer_centers` no filtro canônico `CommercialAnalysisFilterService`.
- Entrar na `SA7010` só quando o filtro vier preenchido, pelo fragmento `customer_center_link_sql` em `app/domain/totvs/protheus_customer_center.py`.
- Para **agrupar** faturamento por centro, usar a rota `/commercial/rol/by-customer-center` (LEFT JOIN + ZC0). Não reutilizar o INNER JOIN de filtro.
- Ligar o fato com `RTRIM/LTRIM` em produto, cliente e loja.
- Juntar ZC0 por cliente + loja + código do centro.

## O que não fazer

- Não gravar allowlist dos centros no código. Um centro novo no Protheus passa a valer sem deploy de regra.
- Não juntar a `SA7010` crua na linha do fato.
- Não usar `A1_NOME` para separar unidades que compartilham razão social.
- Não aplicar o join de filtro em fato sem produto (cabeçalho de proposta `AD1`).
- Não juntar `ZC0010` somente por `ZC0_CODIGO`.
- Não criar snapshot histórico de centro sem pedido explícito.

## Índices recomendados (não criar automaticamente)

Consulta analítica em `SD2010` com join em SA7/ZC0. Se o plano de execução mostrar scan pesado, avaliar com DBA (sem deploy automático):

| Tabela | Colunas sugeridas | Motivo | Impacto esperado |
|--------|-------------------|--------|------------------|
| `SD2010` | `D2_FILIAL`, `D2_EMISSAO` (filtro cedo de período/filial) | Cardinalidade alta do faturamento | Reduz scan do fato |
| `SD1010` | `D1_FILIAL`, `D1_DTDIGIT` | Devoluções no mesmo recorte | Simétrico ao SD2 |
| `SA7010` | `A7_CLIENTE`, `A7_LOJA`, `A7_PRODUTO` | Join de classificação produto×cliente×loja | Evita scan da amarração |
| `ZC0010` | `ZC0_CLIENT`, `ZC0_LOJA`, `ZC0_CODIGO` | Mestre do centro no contexto cliente/loja | Lookup do descritivo |

Os joins atuais usam `RTRIM/LTRIM` nas chaves CHAR do Protheus (padrão já adotado no filtro `customer_centers`). Isso pode impedir seek no índice; medir no ambiente antes de criar índice function-based.

## Censo conhecido (não é allowlist)

Centros preenchidos hoje existem só no cliente `000001`. Exemplos: `1100` e `1200` na loja `01`, `1320` na loja `11`, `1505` na loja `12`, `1106` na loja `09`, `1700` na loja `06`. Lojas sem nenhum centro continuam acessíveis por `customer_code_stores`.
