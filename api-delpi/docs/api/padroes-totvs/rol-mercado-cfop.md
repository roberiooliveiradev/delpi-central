# ROL comercial — mercado interno vs externo (CFOP)

Convenção Delpi para classificar linhas de venda (`SD2.D2_CF`) no faturamento / ROL.

## Regra

| Mercado | Primeiro dígito do CFOP (`LEFT(D2_CF, 1)`) | Exemplos típicos |
|---------|-------------------------------------------|------------------|
| **Interno** (Brasil) | `5` ou `6` | 5101, 6101, … |
| **Externo** (exportação) | `7` | 7101, … |

Código canônico: `CommercialRolReturnSql.is_domestic_market_predicate` /
`is_export_market_predicate` / `market_filter_predicate` em
`app/domain/services/commercial/commercial_rol_return_sql.py`.

## Países de destino (exportação)

Nas linhas com CFOP de exportação, o país do cliente vem de `SA1.A1_PAIS`
(join cliente da linha). Listar distintos no recorte filtrado — não inventar
país a partir do CFOP.

## O que não fazer

- Usar TES (`SF4`) sozinho para decidir mercado (CFOP é a fonte desta regra).
- Confundir com custo de almoxarifado (`B2_CM1`) — ver [armazem-custo.md](./armazem-custo.md).
- Tratar CFOP `1`/`2` (entradas) como venda no ROL de faturamento.

## Consumidores

- `GET /commercial/rol/by-product` — split Interno / Externo / Total.
- Filtro `market=domestic|export` no mesmo contrato.
