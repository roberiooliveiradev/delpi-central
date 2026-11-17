# GLPI #1609 | TV Dashboard: cor do percentual, ocultação e código de produto

**Registro:** 17/11/2026. **Ambiente:** editor TV Dashboard, apresentação e backend (`tv-dashboard-api`). **Referência:** GR Diário de Rio Bananal/ES.

## Solicitação

1. **Cor do valor do velocímetro:** o valor percentual exibido no centro não acompanha integralmente a cor editada pelo usuário.
2. **Título não desaparece:** ao ocultar o título, o nome automático da rota continua aparecendo.
3. **Código incorretamente formatado:** em **GR Diário · Itens com divergência no período**, `10080711` vira `10.080.711` ao exibir a coluna `product_code`.

## Diagnóstico técnico

- **Gauge (cor):** `SpeedometerGauge` usa uma tag SVG `<text>` para o número e uma `<tspan>` para `%`. O texto pai tinha `fill` inline, mas a classe da unidade possuía `fill` próprio, portanto o `tspan` ignorava a cor da parte `gaugeValue`.
- **Gauge (título):** o título de cima (`ChartTitle`) e o rótulo de baixo (`gaugeLabel`) são componentes diferentes. A apresentação ocultava o `ChartTitle` por `showTitle=false`, mas o `gaugeLabel` continuava visível por padrão mesmo com `showGaugeLabel=false` quando seu registro ainda não havia sido materializado em `chartParts`. Por isso o nome da rota parecia ser um título que não podia ser ocultado.
- **Tabela (identificador):** a rota `get_supplies_inventory_adjustments_tv_weekly_items` declara `product_code: string`, mas a materialização de `displayRows` no backend aplicava a formatação numérica geral às cadeias compostas só de algarismos. A tela consome `displayRows` já formatados, então o erro precisa ser resolvido **antes** do paint.

## Solução aplicada nesta PR

- `SpeedometerGauge.tsx`: passa a aplicar a cor explícita de `gaugeValue` também ao `tspan` da unidade. Sem cor explícita, mantém o estilo visual anterior.
- `GaugeChartView.tsx`: exibe o rótulo somente quando o estado explícito da parte `gaugeLabel` permitir; sem materialização, respeita `chartOptions.showGaugeLabel`. O título também respeita `chartParts.title.visible` quando informado.
- `display_format_service.py`: campos de código/identificador (`product_code`, demais `*_code`, `*_id`, `code`, `codigo`, `sku` etc.) são apresentados como valores **literais**, mesmo quando parecem números; não acrescenta pontos de milhar nem elimina zeros à esquerda. Demais medidas numéricas mantêm a formatação usual.
- Testes de regressão em `SpeedometerGauge.test.tsx`, `GaugeChartView.test.tsx` e `test_display_format_service.py`, incluídos na CI do TV Dashboard.

## Regras de aceite

1. No editor, selecionar o **percentual central** do gauge e configurar sua **Cor do texto**. O número e `%` devem exibir a cor escolhida, tanto no editor como na TV publicada.
2. Ao ocultar o **Título** do velocímetro e o **Rótulo do velocímetro**, o nome da rota deve desaparecer. O usuário pode ativar qualquer um dos dois elementos separadamente.
3. Na tabela da rota `get_supplies_inventory_adjustments_tv_weekly_items`, `10080711` deve ser mostrado como `10080711` (nunca `10.080.711`). `00123456` preserva os zeros. Quantidades e valores financeiros continuam formatados normalmente.
4. Nenhuma alteração de origem de dados, SQL do Protheus ou regra de negócio. Não alterar slides/rotas publicados na elaboração da PR; apenas componentes compartilhados.

## Publicação

A PR é separada. Após merge, publicar em ordem os serviços `plugin-ui` (remote compartilhado), `tv-dashboard` (editor/presentation) e `tv-dashboard-api` (formatação `displayRows`). **Não executar deploy antes do merge nem encerrar GLPI #1609 antes da validação em produção.**
