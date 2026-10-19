# DAVI — validação de estoque sem giro e acuracidade (GLPI #1197)

As quatro consultas canônicas existentes de Suprimentos passam a integrar a descoberta dinâmica READ do DAVI:

| Necessidade | Operação |
| --- | --- |
| Resumo da acuracidade oficial | `get_supplies_inventory_accuracy_summary` |
| Detalhamento das contagens | `get_supplies_inventory_accuracy_items` |
| Resumo do estoque sem giro | `get_supplies_non_moving_stock_summary` |
| Detalhamento do estoque sem giro | `get_supplies_non_moving_stock_items` |

## Contrato e segurança

A descoberta e a execução continuam nas duas ferramentas existentes. Inputs são derivados do OpenAPI e intersectados com a allowlist governada. Não há URL, SQL, método HTTP ou operação arbitrária. A autorização permanece nas rotas canônicas, com a identidade do usuário, sem credencial de serviço ou permissão nova.

- Filiais são arrays repetíveis (`branch`); omitir mantém o consolidado autorizado.
- Estoque sem giro admite `warehouse` repetível e filtros de itens `turnover_status`, `blocked`, `product_codes`, `search`.
- Acuracidade admite `month` ou um par de datas; a competência tem precedência conforme o contrato do owner. Filtros `outcome` e `search` afetam somente o detalhe.
- Datas personalizadas devem ser fornecidas juntas e têm limite DAVI de 731 dias. As rotas internas não têm seu contrato alterado.
- As listas são paginadas, limitadas a 50 linhas por chamada do DAVI; a projeção mantém total e sinalização de completude. Uma página parcial não valida o universo inteiro.
- Somente campos de resposta aprovados são projetados, incluindo referência, denominadores, exclusões e origem da avaliação financeira.

## Validação após deploy

1. Solicitar ao DAVI “resumo de acuracidade” e depois “detalhamento das contagens”, usando as mesmas datas e filiais. Para reproduzir o print do chamado: 01/05/2025 a 31/05/2026, consolidado, sem filtro de resultado/busca, primeira página com 20 linhas.
2. Sem filtros exclusivos do detalhe, comparar seu total com `summary.valid_count_total`; a quantidade recebida por página pode ser menor. Comparar as corretas/divergentes com o denominador avaliável, mantendo as exclusões separadas.
3. Consultar resumo e detalhe do estoque sem giro no mesmo recorte. O resumo abrange o estoque elegível; um detalhe filtrado para sem giro não deve ter seu total comparado com o universo completo.
4. Preservar a fonte de avaliação `sb2_current_snapshot`: a janela histórica filtra consumo, não transforma o valor em estoque histórico. Histórico insuficiente não equivale a material sem giro.
5. Uma falha deve ser reportada como erro; não como zero registros. Ajustes de inventário e valor de estoque isolado não substituem essas quatro consultas.

## Correção associada

A consulta de itens de acuracidade repetia a coluna de ordenação no desempate. A ordenação por produto do estoque sem giro possuía o mesmo defeito. As colunas são agora únicas e preservam a chave estável para paginação. Nas duas telas, erros do detalhamento são exibidos com tentativa novamente e Atualizar recarrega resumo e itens.

Testes locais usam as rotas reais e a autorização real, substituindo somente identidade/RBAC e o caso de uso na fronteira do banco. Não comprovam os dados do Protheus ou o comportamento do deploy de produção; executar o roteiro acima após deploy de `api-delpi` e `dashboard-supplies`.
