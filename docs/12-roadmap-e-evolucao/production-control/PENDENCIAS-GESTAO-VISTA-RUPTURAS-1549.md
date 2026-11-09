# Gestão à Vista · Pendências de OP e ruptura de estoque (#1549)

## Objetivo

Evoluir o card **Pendências** já existente no Portal PCP sem criar um card
adicional. O card exibe duas categorias, no mesmo fluxo cronológico:

| Categoria | Fonte | Data para ordenar |
| --- | --- | --- |
| `include_production_order` | DemandCoverageService / Demanda Protheus+MyWEG | `suggested_op_date` (necessidade − 2 dias, mínimo hoje) |
| `stock_rupture` | Delpi Reports / `safety_stock_shortage_30d` | `first_shortage_date` (mantém atrasadas) |

No mesmo dia, ruptura é exibida primeiro. Contador é o total combinado.
Itens são distintos por **filial + categoria + produto/material** e nunca
misturam unidades de peças do PA com MT/KG/MI da matéria-prima.

## Fonte autoritativa e regra de ruptura

Não calcular ruptura em JavaScript ou no BFF. O provider de Reports usa
`SafetyStockShortage30dAggregationService`, que constrói projeção por
`build_stock_projection` considerando saldo SB2 (01+98+99), pedidos de
compra SC7 elegíveis e empenhos SD4. Ruptura é a **primeira ocorrência de
saldo projetado negativo**, não o déficit abaixo do estoque de segurança.

Janela inicial de 30 dias, mantendo eventos vencidos com sua data de origem.
Campos aproveitados: `product_code`, `product_description`,
`branch`, `unit`, `first_shortage_date`, `available_stock`,
`shortage_balance`, `next_purchase`, `last_inventory_date` e `observation`.

## Fluxo e segurança

1. Usuário autenticado chama `GET /apps/production-control-api/demand/op-pendencies?branch=02`.
2. `DemandService` exige `production-control.demand.view` e autorização
   da filial, antes de acessar ou consultar qualquer dado adicional.
3. Serviço consulta a cobertura das demandas e seu cache atual.
4. Gateway BFF chama, com **token interno S2S**, a rota
   `GET /reports/providers/safety_stock_shortage_30d/pcp-pendencies?branch=02&horizonDays=30`
   da api-delpi. O endpoint recusa solicitações sem token interno válido.
5. Reports reaproveita seu preview/provider oficial, sem necessidade de
   conceder ao colaborador permissões amplas do plugin Reports.
6. BFF valida filial e janela, normaliza, agrupa e intercala rupturas
   e OPs. Fonte sem data/filial confiável é descartada.
7. O frontend renderiza o ícone/quantidade correspondente e abre modal
   da categoria com campos adequados à origem.

Cache de rupturas de 120 segundos por filial no processo do BFF. Botão
**Atualizar** da Gestão à Vista força leitura atualizada (inclui
`refresh=true`). Falha da rota Reports deixa a lista de OP intacta,
retorna `stock_source_status=unavailable` e
`source_status=partial`, com aviso; **não** interpreta erro como
"sem rupturas".

## Modal de ruptura

Exibe código e descrição do material, data original, filial, estoque
disponível, saldo projetado no primeiro evento, unidade cadastrada,
último inventário, próximo pedido de compra e observações quando existirem.
Oferece acesso ao plugin Estoque de Segurança para investigação aprofundada.
Não cria pedido de compra nem movimentação.

## Contrato e extensibilidade

A consulta BFF preserva dados da pendência de OP e acrescenta:
- `items`: união discriminada por `kind`;
- `count`: total de itens;
- `op_count`, `stock_rupture_count`: contadores separados;
- `stock_source_status`: `complete` ou `unavailable`;
- `stock_as_of`, `stock_horizon_days`;
- `source_status`, `warning`: estado combinado das fontes.

A chave de categoria evita que um material com o mesmo código de um PA
substitua uma pendência de inclusão de OP.

## QA e deploy

CI: `.github/workflows/production-control-quality.yml` valida build,
typecheck e testes do MFE, testes de pendências do BFF e rota Reports
isoladamente. A checagem transversal de arquitetura também permanece ativa.

Serviços a publicar, em sequência: `api-delpi`,
`production-control-api`, `production-control`.
Sem migrações ou alteração de cadastros TOTVS.

Homologar nas duas filiais: lista intercalada e cronológica, quantidade
com unidade original, rupturas vencidas, clique no modal, acesso ao
Estoque de Segurança, atualização do painel e comportamento sob falha da
fonte Reports. Manter o chamado #1549 aberto até validar produção.
