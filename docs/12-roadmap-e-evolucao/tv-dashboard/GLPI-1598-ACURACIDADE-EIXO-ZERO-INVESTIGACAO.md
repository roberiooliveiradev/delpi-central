# GLPI #1598 — Investigação de acuracidade e correção de polaridade de colunas

**Data:** 17/11/2026 · **Status:** correção visual em PR; regra de negócio da acuracidade pendente de homologação com Estoque/Controladoria.

## A. Evidência do gráfico mensal de divergências

Tela: GR Diário, Rio Bananal (filial 02), série mensal de **saldo líquido** `net_value_brl`. O gráfico mostrava perdas e sobras com sinais corretos nos rótulos, mas áreas de coluna visualmente enganosas: a função `ChartSeriesBar` usava `baselineY = margin.top + plotH` (menor valor do eixo) mesmo quando o domínio cruzava zero. Resultava em barras negativas desenhadas desde o mínimo (ex.: -781.891) até cada valor, de forma que pequenas perdas pareciam grandes.

**Correção:** as barras verticais usam `toY(0)` para a origem, `toY(value)` para o extremo e altura `abs(toY(value)-toY(0))`. Negativas ficam abaixo de zero, positivas acima. Barras horizontais passam a usar a mesma geometria. O eixo categórico de gráficos de colunas/barras e combo cruza o zero; os rótulos de negativos são posicionados do lado correto. Mantidos os demais tipos de gráfico sem mudança da origem, e os dados/cores não são manipulados.

**Regressões:** teste de extremos reais de janeiro/novembro (perda -1.982 vs -781.891), sinal positivo +85.251, escala apenas negativa, horizontal, área mínima de clique e eixo em zero. Mudança no kit compartilhado `plugins/plugin-ui`, utilizado pelo editor e pelo player.

**Foco do aceite:** conferir em TV 16:9 que janeiro (-1.982) produz coluna quase nula abaixo do zero, novembro (-781.891) produz coluna longa para baixo; sobras +85.251 crescem para cima; e os valores/cores permanecem iguais aos da API.

## B. Investigação de Accuracy 0%

**Fonte oficial consultada:** operação DAVI/DELPI `get_supplies_inventory_accuracy_summary`, filial 02; detalhes em `get_supplies_inventory_accuracy_items` (consulta autorizada e somente leitura).

### Resultados capturados em 17/11/2026

| Competência | Válidas | Avaliáveis | Corretas | Divergentes | Accuracy | Coverage |
|---|---:|---:|---:|---:|---:|---:|
| 2026-10 | 41 | 41 | 1 | 40 | 2,44% | 100% |
| 2026-11 | 39 | 39 | 0 | 39 | 0,00% | 100% |

Sem filtros de mês a rota seleciona o mês do último fechamento SB9: no momento da consulta, **outubro/2026 (2,44%)**. Com `month=2026-11`, usa novembro e retorna **0%**.

O detalhamento de novembro confirma contagens processadas `B7_STATUS='2'` com vínculos a movimentos de ajuste SD3 INVENT na amostra consultada. O método atual é:
- `accurate_count` = evento SB7 processado **sem** ajuste SD3 INVENT (pareamento por filial, produto, local e data);
- `evaluable_count_total` = contagens processadas;
- `accuracy_percentage = 100 * accurate_count/evaluable_count_total`;
- `coverage_percentage = 100 * evaluable_count_total/valid_count_total`;
- Quando não há contagens avaliáveis, `accuracy_percentage=null`, não zero.

**Conclusão comprovada:** não é um bug de apresentação do velocímetro nem arredondamento: a **API retorna 0% segundo a fórmula programada** em novembro. **Não é prova de 0% de acuracidade global do estoque.** A amostra é restrita às contagens registradas em SB7, e a hipótese de subregistro de contagens sem ajuste precisa ser conferida com o fluxo MATA270/Contagem da Delpi e com o cadastro/configuração SB7.

### Para validar o significado de "acuracidade" na TV

1. O responsável operacional precisa confirmar qual a **base do denominador**: contagens físicas registradas, produtos/posições inventariados, ou valor financeiro do estoque.
2. Verificar se todas as contagens corretas também geram linhas em SB7 para o período e se o status de conclusão adotado na Delpi é `B7_STATUS='2'`. Sem isso, a rota só representa o subconjunto registrado e seu percentual não é confiável como KPI corporativo.
3. Conferir ao menos uma amostra de contagens sem acerto e outra com acerto, cruzando com SD3 INVENT e o histórico do MATA270; investigar fechamentos SB9 e períodos de inventário.
4. Se o indicador pretendido for **acuracidade financeira**, acordar denominador e fórmula com Controladoria (por exemplo, valor base inventariado). **Não substituímos o percentual por `100 - abs(ajustes)/valor estoque` sem definições e reconciliação oficiais.**
5. Até a homologação, usar o gauge com rótulo explícito **"% de contagens sem ajuste (base SB7)"**, e preferir o estado **"em validação"** em vez de uma meta oficial ou avaliação de desempenho.
6. Data de referência do widget: **não confundir filtro dinâmico do TV Dashboard com o default da API**. A fonte de acuracidade sem `month` nem `start_date/end_date` busca último fechamento SB9, não necessariamente o mês atual.

## Entrega e segurança

Esta PR corrige **somente o renderizador do gráfico**, sem modificar SQL, fórmula de acuracidade ou dados. Não marca chamado #1598 como solucionado antes de validar com Suprimentos/Controladoria e conferir a TV publicada.

**Após merge/deploy:** reconstruir `plugin-ui` e `tv-dashboard`, sem necessidade de reconstruir `api-delpi` para corrigir o gráfico. Roteiro de teste em homologação: selecionar rota `get_supplies_inventory_adjustments_tv_monthly_series`, campo `net_value_brl`, filial 02, granularidade `month`, período ano até hoje.
