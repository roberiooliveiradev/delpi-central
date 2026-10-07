# Suprimentos — ajustes de inventário (furo/sobra)

Rotas de **conciliação de inventário**: ajustes gerados pelo processamento
da contagem física (`SB7`, origem `MATA270`) e gravados em `SD3` com
`D3_DOC = 'INVENT'`.

**Não confundir** com:

| Rota | Papel |
|------|--------|
| `/products/{code}/internal-movements` | Extrato de **um** produto; `kind=inventory_adjustment` filtra o mesmo universo |
| [`/supplies/stock-balances/*`](./supplies-stock-balances.md) | Saldo por armazém (quantidade/valor `SB2`) |
| [`/supplies/stock-value`](./supplies-estoque-historico.md) | Valoração consolidada e histórico |

Playbook de origem: [padroes-totvs/playbooks/playbook-correcao-estoque-supplies-inventario.md](./padroes-totvs/playbooks/playbook-correcao-estoque-supplies-inventario.md).

## Endpoints

| Método | Path | operationId | shape |
|--------|------|-------------|-------|
| `GET` | `/supplies/inventory-adjustments/summary` | `get_supplies_inventory_adjustments_summary` | `playbook_report` |
| `GET` | `/supplies/inventory-adjustments` | `list_supplies_inventory_adjustments` | `paged_list` |

Permissão: `api-delpi.access` (`API_DELPI_ACCESS`).

## Semântica canônica (domain-owned)

A classificação vive em
`app/domain/services/supplies/inventory_adjustment_service.py` e
`app/domain/totvs/protheus_internal_movements.py`. O repositório apenas
referencia as expressões — nenhum consumidor reescreve a regra.

| Fato Protheus | Significado |
|---------------|-------------|
| `D3_DOC = 'INVENT'` + `D3_CF = 'RE0'` | **Sobra** (ajuste de entrada) — `nature=surplus` |
| `D3_DOC = 'INVENT'` + `D3_CF = 'DE0'` | **Furo** (ajuste de saída) — `nature=shortage` |

**O TM não é autoridade para ajuste**: a sobra é gravada com `TM 999`
(o mesmo TM do consumo de produção) e o furo com `TM 499`. A natureza
vem exclusivamente do `D3_CF`. `D3_TPMOVAJ` não é usado no ambiente;
`SF5` não contém os TMs 499/999.

```text
signed_quantity = +D3_QUANT (RE0) | -D3_QUANT (DE0)
signed_value    = +D3_CUSTO1 (RE0) | -D3_CUSTO1 (DE0)
```

`D3_CUSTO1` é tratado nesta capability como **valor total do movimento
na moeda 1**, não como custo unitário. Portanto o valor histórico do ajuste
é agregado diretamente de `D3_CUSTO1`; **não** multiplicar
`D3_QUANT * D3_CUSTO1`. A mesma convenção é usada no cálculo histórico
SB9+SD3. A validação live da filial 01 no período de regressão abaixo
reproduz os totais reconciliados usando essa interpretação.

## Proveniência SB7

SB7 é **apoio** de proveniência, não autoridade. O documento de
inventário (`B7_DOC`) e a quantidade contada (`B7_QUANT`) são
correlacionados por `filial + produto + armazém + data de emissão`;
a base investigada apresentou alta correlação (4.849/4.852 linhas
2025+), o que **não** estabelece vínculo um-para-um autoritativo.

Contrato fail-closed (set-based, sem `TOP 1`/`MIN`/`MAX` como
autoridade):

- **exatamente um** documento candidato (`B7_DOC` normalizado não
  vazio, não deletado) → `inventory_document` = documento e
  `counted_quantity` = `SUM(B7_QUANT)` das linhas físicas **daquele**
  documento;
- **zero** ou **mais de um** documento candidato →
  `inventory_document` = `null` e `counted_quantity` = `null`;
- múltiplas linhas físicas do **mesmo** `B7_DOC` não são ambiguidade
  — agregam na quantidade contada do documento.

## Tabelas e colunas

| Tabela | Colunas |
|--------|---------|
| `SD3010` | `D3_FILIAL`, `D3_EMISSAO`, `D3_COD`, `D3_LOCAL`, `D3_DOC`, `D3_TM`, `D3_CF`, `D3_QUANT`, `D3_CUSTO1`, `D3_ESTORNO`, `D_E_L_E_T_` |
| `SB7010` | `B7_FILIAL`, `B7_COD`, `B7_LOCAL`, `B7_DATA`, `B7_DOC`, `B7_QUANT`, `D_E_L_E_T_` |
| `SB1010` | `B1_COD`, `B1_DESC`, `B1_UM`, `D_E_L_E_T_` |

Excluídos sempre: `D_E_L_E_T_ <> ''` e `D3_ESTORNO = 'S'`.

## Filtros

| Param | Default | Comportamento |
|-------|---------|----------------|
| `start_date` / `end_date` | **obrigatórios** | Intervalo fechado, máximo **366 dias**; aliases legados `date_start`/`date_end` aceitos |
| `branch` | omitido | Consolidado (sem predicado `D3_FILIAL`) |
| `branch=01` / `branch=02` | — | Filial concreta |
| `product_code` | omitido | Todos os produtos |
| `warehouse` | omitido | Todos os armazéns (`D3_LOCAL`) |
| `nature` | omitido | `shortage` (furo) ou `surplus` (sobra); qualquer outro valor → HTTP 400 |
| `page` / `page_size` | `1` / `50` | Só no endpoint de itens; `page_size` máx. **500** (`page_50_500`) no contrato da API; a superfície DAVI minimiza para máx. **50** |

Internamente o período é aplicado como intervalo fechado-aberto
(`D3_EMISSAO >= start` e `D3_EMISSAO < end + 1 dia`), com todas as
datas normalizadas para `YYYYMMDD` no SQL e devolvidas em ISO
`YYYY-MM-DD` na resposta.

## Resposta — summary

`summary` (totais do período) mais dimensões `by_month`, `by_branch` e
`by_nature`, cada uma com:

```text
adjustment_count / shortage_count / surplus_count
gross_quantity / net_quantity (assinada)
gross_value / net_value (assinado)
shortage_quantity / shortage_value
surplus_quantity / surplus_value
```

### Indicador principal e nomenclatura DAVI

Quando o pedido do usuário for **"ajuste de estoque"** ou
**"ajuste de inventário"** sem natureza, o indicador principal é o
**ajuste líquido**. O contrato HTTP permanece inalterado; a apresentação
DAVI usa os campos existentes:

| Semântica user-facing | Campo canônico | Fórmula |
|---|---|---|
| `valor_sobra` | `summary.surplus_value` | soma da magnitude dos movimentos `surplus` |
| `valor_furo` | `summary.shortage_value` | soma da magnitude dos movimentos `shortage` |
| `valor_ajuste_liquido` | `summary.net_value` | `surplus_value - shortage_value` |
| `valor_ajuste_bruto` | `summary.gross_value` | `surplus_value + shortage_value` |
| `quantidade_sobra` | `summary.surplus_quantity` | soma das quantidades `surplus` |
| `quantidade_furo` | `summary.shortage_quantity` | soma das quantidades `shortage` |
| `quantidade_liquida` | `summary.net_quantity` | `surplus_quantity - shortage_quantity` |
| movimentos de sobra | `summary.surplus_count` | contagem `surplus` |
| movimentos de furo | `summary.shortage_count` | contagem `shortage` |
| movimentos totais | `summary.adjustment_count` | movimentos `INVENT` válidos no recorte |

`net_value > 0` significa **sobra líquida**; `net_value < 0`
significa **furo líquido**. `gross_value` mede magnitude movimentada e
**nunca** deve ser apresentado como ajuste líquido.

Pedido explícito de **furo** usa `nature=shortage`; pedido explícito de
**sobra** usa `nature=surplus`. O Agent não reclassifica movimentos a
partir de `D3_TM`, `D3_CF` ou `D3_TPMOVAJ`: a classificação continua
domain-owned e o repositório reutiliza a expressão canônica.

### Regressão congelada — filial 01, 2026-01-01 a 2026-10-07

| Indicador | Esperado |
|---|---:|
| valor_sobra | 2.082.103,531 |
| valor_furo | 1.908.939,208 |
| valor_ajuste_liquido | 173.164,323 |
| valor_ajuste_bruto | 3.991.042,739 |
| quantidade_sobra | 549.666,291 |
| quantidade_furo | 489.976,062 |
| quantidade_liquida | 59.690,229 |
| movimentos_sobra | 977 |
| movimentos_furo | 474 |
| movimentos_totais | 1.451 |

## Discovery semântico DAVI

A capability existente é reutilizada; não existe capability paralela para
"ajuste de estoque".

O discovery separa intenção **agregada** da intenção **detalhada** por
vocabulário governado na allowlist:

- agregado (`summary`): ajuste/acerto/diferença de estoque ou inventário,
  furo, sobra, "sobra menos furo", saldo de ajustes, total, valor,
  bruto e líquido;
- detalhe (`list`): itens, produtos, documentos, lançamentos, listagem,
  detalhe ou detalhamento dos ajustes.

Regras de execução permanecem fora do retrieval:

- pedido de **furo** → `nature=shortage`;
- pedido de **sobra** → `nature=surplus`;
- pedido genérico de ajuste de estoque/inventário → omitir `nature` e
  retornar ambas as naturezas;
- `start_date`, `end_date`, `branch`, `warehouse` e
  `product_code` continuam filtros do contrato existente.

O discovery não classifica movimentos por `D3_TM`, `D3_CF` ou
`D3_TPMOVAJ`; esses códigos não se tornam autoridade do Agent. A
classificação shortage/surplus continua domain/backend-owned.

## Resposta — items

Paginado (`page`, `page_size`, `total`, `total_pages`). Cada item traz
`issue_date`, `branch`, `product_code`, `product_description`, `unit`,
`warehouse`, `document`, `movement_category=inventory_adjustment`,
`movement_direction`, `movement_label`, `inventory_adjustment_nature`,
`nature_label`, `quantity`, `signed_quantity`, `movement_value`,
`signed_value`, `inventory_document` (`B7_DOC`, quando a
proveniência é inequívoca) e `counted_quantity` (`B7_QUANT` agregada
do documento provado).

## Governança DAVI

Ambas as operações estão na allowlist `davi_external_read_allowlist.json`
(v18, `DAVI-INVENTORY-MATERIAL-FLOW-IMPLEMENTATION-001`, corrigida por
`DAVI-INVENTORY-MATERIAL-FLOW-CORRECTIVE-001`) com inputs e response
fields explícitos.

Limite de paginação por superfície: **API owner** `page_size` máx.
**500**; **DAVI** (`list_supplies_inventory_adjustments`) máx. **50**
— minimização de contexto externo, sem alterar o contrato canônico.

A classificação de `kind` em
`/products/{code}/internal-movements` aceita `inventory_adjustment`
como recorte do mesmo predicado canônico — o documento `INVENT`
**nunca** é classificado como `warehouse_transfer`.

## Ownership e governança atual

| Item | Estado |
|------|--------|
| Technical owner | **api-delpi / Supplies** (`InventoryAdjustmentsRepositoryPort` → `InventoryAdjustmentsRepository` → SD3 + SB7 de apoio) |
| Business owner | **TO_INVENTORY** — o owner organizacional/de negócio ainda não foi ratificado; **não** deve ser inferido do nome do bounded context Supplies |
| Permissão backend atual | `api-delpi.access` (`API_DELPI_ACCESS`, `@require_permission`) |
| AUTHZ intent | **PASS** — `docs/api/00-visao-geral.md` documenta `api-delpi.access` cobrindo Suprimentos/Financeiro; rotas Supplies financeiramente sensíveis comparáveis (`stock-value`, `cpv`, `negotiation-savings`) já aceitam `API_DELPI_ACCESS` na política vigente; nenhuma permissão criada/alterada nesta correção |
