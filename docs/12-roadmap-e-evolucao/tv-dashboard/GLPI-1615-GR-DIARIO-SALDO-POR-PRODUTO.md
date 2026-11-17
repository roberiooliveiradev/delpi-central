# GLPI #1615 | GR Diário: itens com saldo líquido por produto

**Data:** 17/11/2026 · **Owner:** api-delpi · **Consumidor:** TV Dashboard
**Endpoint/operationId preservados:** GET /supplies/inventory-adjustments/tv/weekly-items · get_supplies_inventory_adjustments_tv_weekly_items

## Problema

O agrupamento anterior por filial + produto + armazém + natureza multiplicava linhas do mesmo produto quando tinha falta/sobra ou inventários em locais distintos. Nova regra: **uma linha por filial e produto**, após compensar todos os movimentos elegíveis do período.

## Contrato do ranking

- Agrupamento SQL por filial e produto, antes do TOP, com filtros de período, filial e armazém preservados. Se branch=all, filiais continuam separadas.
- signed_quantity = sobras - faltas (sinal físico); signed_value_brl = sobras - faltas em R$ (sinal financeiro).
- quantity e value_brl = módulos dos saldos líquidos, não somatórios brutos.
- Natureza final: sobra, falta ou compensado. Se sinais físico e financeiro divergirem, nature_label informa ambos; quantity_nature_label e financial_nature_label ficam disponíveis.
- warehouse = "Todos" (sem filtro) ou armazém escolhido (com filtro); warehouse_count informa a quantidade de armazéns envolvidos. Não há agrupamento por armazém na tabela.
- Contadores movement_count, shortage_count, surplus_count e unpriced_movements preservados.
- item_grain = branch_product. total_groups conta grupos produto + filial; ordenação TOP por módulo do saldo em R$, desempate por módulo da quantidade.
- Materiais de terceiros (B1_TPMAT=2) continuam com valor gerencial R$ 0 (GLPI #1614); suas quantidades permanecem.

Exemplo: produto P001 com falta de 100 un./R$500 no local 01 e sobra de 80 un./R$400 no local 99 agora gera **uma única linha**, signed_quantity=-20 e signed_value_brl=-100.

## Não alterado

Os KPIs de divergência **bruta** e a série geral permanecem com os valores brutos (faltas + sobras); somente a rota de itens apresenta o saldo líquido por produto. Mantidos estornos excluídos, documento INVENT, classificação RE0/DE0, permissões, período, segurança SQL, R07/TTAT e custos originais Protheus. Sem migrações ou escrita no ERP.

## Testes e implantação

Testes: test_tv_inventory_product_net_balance_1615.py, test_tv_inventory_divergences_1598.py, test_inventory_third_party_zero_value_1614.py e test_inventory_divergence_1598_overlays.py (tv-dashboard-api).

Após PR incorporada na main:
    cd /home/operador/projetos/delpi-central
    git pull --ff-only origin main
    bash ./infra/scripts/up-prod-sequential.sh --build api-delpi tv-dashboard-api

Validar com amostras de SD3 em dois armazéns, sentidos opostos, compensação integral, material terceiro, branch=01/02/all, filtro específico de armazém e TOP N. Chamado #1615 permanece aberto até aceite em produção.
