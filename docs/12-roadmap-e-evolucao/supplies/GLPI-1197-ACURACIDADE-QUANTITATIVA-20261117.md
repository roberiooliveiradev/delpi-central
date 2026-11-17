# Acuracidade quantitativa do inventário | revisão da regra (17/11/2026)

## Solicitação da operação

**Acuracidade não deve ser o percentual de contagens sem ajuste.** O indicador correto para a operação é a proximidade da **quantidade física contada** com o **saldo que deveria existir** para cada produto/local/evento. Depois, calcular a **média aritmética simples de todos os percentuais calculáveis no período** (mês ou intervalo selecionado).

Exemplo informado pelo solicitante: se havia 100 unidades esperadas e foram encontradas 10, a acuracidade do item é **10%**, e não **0%** apenas porque houve ajuste.

### Fórmula de cada contagem

```text
diferença = quantidade contada − quantidade teórica
acuracidade do item = máx(0%, 100% − (|diferença| / quantidade teórica) × 100)
acuracidade do período = soma das acuracidades individuais / nº de contagens pontuáveis
```

A diferença absoluta penaliza falta **e** sobra. A pontuação é limitada a [0, 100]%; não permite acuracidade negativa ou superior a 100%. Não ponderar pelo saldo, pela quantidade absoluta nem pelo custo financeiro.

| Teórico | Contado | Tipo | Acuracidade |
|---:|---:|---|---:|
| 100 | 10 | falta de 90 | 10% |
| 100 | 110 | sobra de 10 | 90% |
| 100 | 100 | sem diferença | 100% |
| 100 | 0 | falta total | 0% |
| 100 | 200 | sobra de 100 | 0% |
| 93 | 55 | falta de 38 | 59,14% |
| 256,105 | 249,8 | falta de 6,305 | 97,54% |

Se duas contagens pontuáveis tiverem 10% e 100%, a média é **55%** (não ponderada pelas quantidades esperadas 100:1).

### Tratamento de dados não calculáveis

- `theoretical_quantity > 0` e `B7_STATUS='2'`: **pontuável**.
- `theoretical_quantity = 0`, inclusive com sobra, ou saldo teórico negativo: **sem percentual**. Não dividir por zero nem contar como 0% ou 100%; separar em `unscorable_count`.
- Contagens ainda pendentes de processamento seguem fora da média; contabilizar em `excluded_pending_processing`.
- Sem registros pontuáveis no recorte: `accuracy_percentage=null` e `status=unavailable` (motivo `no_scorable_theoretical_quantity` quando houver contagens avaliáveis).
- O valor só é arredondado a duas casas **após** somar os percentuais individuais, para evitar viés de arredondamento.

## Fonte e granularidade

- Protheus SQL Server, eventos `SB7010` agrupados por filial + produto + armazém + data. Quantidade contada: `SUM(B7_QUANT)`. Considerar contagens processadas `B7_STATUS='2'`.
- Saldo teórico existente na API: **contado + falta − sobra**, via movimentos de ajuste `SD3010` com `D3_DOC='INVENT'`, sem estorno, vinculados ao mesmo evento. Preserva a regra e a fonte de cálculo já implementadas; não acessa valores de estoque de outra competência.
- Cada evento pontuável contribui **uma vez** para a média. O produto pode aparecer em mais de uma contagem no período e cada evento conta como uma observação.
- `month=YYYY-MM` ou `start_date/end_date` definem o período; sem período explícito permanece o último mês fechado do SB9, como no contrato existente. A média calculada não depende do tamanho da página de detalhe nem dos filtros de pesquisa da tabela.
- `branch=01`, `branch=02` ou consolidado: o consolidado usa a soma de percentuais sobre o número total de eventos pontuáveis **das duas filiais**, e não a média simples dos percentuais já agregados por filial.

## Contratos preservados e campos novos

- `GET /supplies/inventory-accuracy/summary` conserva `summary.accuracy_percentage` para os atuais consumidores (portal e velocímetro), mas **altera explicitamente sua regra** para média aritmética dos percentuais de quantidades.
- `summary.accuracy_calculation = arithmetic_mean_quantity_accuracy`.
- `summary.scored_count`: quantidade de eventos efetivamente incluídos na média.
- `summary.unscorable_count`: quantidade de processados sem saldo teórico positivo. Também em `exclusions.unscorable_nonpositive_theoretical`.
- `by_branch[].accuracy_percentage`, `scored_count`, `unscorable_count`: mesmas regras por unidade.
- `GET /supplies/inventory-accuracy/items` passa a mostrar `quantity_accuracy_percentage` para conferir a conta **por item**.
- `accurate_count` e `divergent_count` continuam existindo para auditoria de quantos eventos geraram ou não ajuste, mas **não** participam do KPI. `coverage_percentage` mantém sua interpretação original (proporção de contagens avaliáveis/total de válidas).
- `shortage_value_total`, `surplus_value_total`, `theoretical_quantity`, `counted_quantity` e classificação de resultado permanecem inalterados.

## Interface

A tela de Acuracidade em Dashboard Suprimentos explica que o KPI é uma média de percentuais por contagem e acrescenta uma coluna **Acuracidade (%)** ao detalhamento. O tooltip inclui exemplos de perda e sobra, a exclusão dos teóricos não positivos e a ausência de ponderação.

## Validação antes de publicar

1. Teste de fórmula: 100→10=10%; 100→110=90%; 100→100=100%; 100→0=0%; 100→200=0%; piso zero; divisão por zero indisponível.
2. Média simples de dois itens (10%, 100%) = 55%. Confirmar consolidação por filial sem dar o mesmo peso a filiais de volumes diferentes, salvo se tiverem a mesma quantidade de contagens.
3. Verificar que uma contagem sem ajuste entra com 100% (teórico = contado), contagens pendentes ficam excluídas e valores com teórico zero são segregados.
4. Homologar com dados reais de Rio Bananal, comparando pelo menos 10 itens com SB7/SD3 e recalculando manualmente, inclusive faltas e sobras.
5. Validar acesso autorizado, respostas sem dados, rotas consumidas pelo Portal Suprimentos e pelo TV Dashboard e exibição em gauges de 0–100%.
6. Verificar em HML antes de merge/deploy, sem operações de escrita no Protheus.

**Limitação conhecida:** a precisão do percentual depende do saldo teórico reconstruído com os ajustes de inventário que já são reconhecidos pela API. Pareamentos atípicos de SB7/SD3 precisam de conciliação com o relatório de inventário do Protheus. O resultado representa **a média dos eventos contados** no recorte, não um percentual financeiro de valor total do estoque.

**Status:** alteração preparada em PR independente. Nenhum deploy ou modificação no ERP foi feito.
