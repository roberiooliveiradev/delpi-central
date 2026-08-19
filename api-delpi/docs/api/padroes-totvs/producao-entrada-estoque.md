# Produção — entrada em estoque (última operação do PA)

Parte da [biblioteca de padrões TOTVS](./README.md).

## Princípio

A quantidade de **produto acabado que entra em estoque** no apontamento é a da **última operação do roteiro** (`SG2`) daquele PA — não a soma de todos os CTs e não necessariamente o CT de inspeção final.

No Protheus Delpi esse apontamento (`SH6` tipo `P`) é o que origina o movimento `SD3` com `D3_CF = PR0`. A inspeção final (`HB_NOME LIKE '%INSPE%FINAL%'`) coincide com a última operação **quando** o roteiro termina em INSPECIONAR; em outros PAs a última operação é outro CT (impressão, terminais, enrolar fio, etc.).

## O que fazer

| Necessidade | Regra |
|-------------|-------|
| KPI Qtd. produzida do plugin `production-appointments` | `SUM(H6_QTDPROD)` onde `B1_TIPO = PA` e `H6_OPERAC = MAX(G2_OPERAC)` do produto/filial |
| Expedição / PPM / `produced-totals` | Continua inspeção final + OP mãe — [playbook-pa-inspecao-expedicao.md](./playbooks/playbook-pa-inspecao-expedicao.md) |
| Ranking por CT / perda / lista | Todos os apontamentos do recorte (não aplicar última operação) |

Constantes: `PA_STOCK_ENTRY_PRODUCT_TYPE`, `produced_qty_scope` em `app/domain/production/production_appointments/production_appointments_scope.py`.  
Tipo PA: `PRODUCT_TYPE_FINISHED_GOOD` em `app/domain/totvs/protheus_product_types.py`.  
SQL do KPI: `OUTER APPLY` + seek em `SG20103` (`G2_FILIAL`, `G2_PRODUTO`, `G2_OPERAC`) — sem `LTRIM`/`RTRIM` na chave e sem agregar o roteiro inteiro.

## O que NÃO fazer

- Somar todos os CTs no card de produzida (conta corte/montagem como peça acabada).
- Fixar CT-70 / INSPECIONAR como proxy de entrada em estoque.
- Trocar o KPI para `SUM(SD3.D3_QUANT)` — a fonte operacional do plugin é o apontamento (`SH6`); `PR0` duplicado no estoque não deve inflar o card.
- Agregar o `SG2010` inteiro com `LTRIM`/`RTRIM` na chave do JOIN (quebra o índice `SG20103`).

## Relação com Power BI

Consultas de produção acabada em `SD3010` (`D3_CF = 'PR0'` e `B1_TIPO = 'PA'`) medem **estoque**, não apontamento. O card em `SH6` na última operação do PA aproxima esse volume; diferenças residuais vêm de `PR0` duplicado ou data `D3_EMISSAO` ≠ `H6_DTAPONT`.
