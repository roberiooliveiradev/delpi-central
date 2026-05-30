# Sugestões ricas de perguntas para o Minha DELPI Chat IA

Baseado na análise do arquivo `capabilities.json` em:

`minha-delpi-ai-api/app/content/pt-BR/assistant/capabilities.json`

Este documento reúne sugestões de perguntas, menus e blocos de exemplos para enriquecer a experiência do usuário no Minha DELPI Chat IA.

---

## 1. Ajuda e descoberta de capacidades

- O que você pode fazer?
- Me mostre o menu de opções.
- Quais consultas estão disponíveis?
- Quais dados você consegue acessar?
- Quais actions estão habilitadas neste agente?
- Você consegue consultar estoque?
- Você consegue buscar por fornecedor?
- Você sabe consultar LMP?
- Você consegue gerar gráfico?
- Quais comandos posso usar aqui?

---

## 2. Produto — consulta cadastral

- Me fale sobre o produto `10080001`.
- Mostre a ficha do produto `10080001`.
- Traga os dados cadastrais do produto `10080001`.
- Esse produto existe no ERP?
- Qual é a descrição completa desse código?
- Qual grupo, unidade, tipo e status desse produto?
- Esse produto está ativo ou bloqueado?
- Esse item é matéria-prima, intermediário ou produto acabado?
- Explique esse cadastro em linguagem simples.
- Mostre esse produto em formato de tabela.

---

## 3. Busca de produtos

- Busque produtos com descrição contendo `terminal bandeira`.
- Liste 10 produtos parecidos com `cabo pp`.
- Procure produtos do grupo `1008`.
- Liste produtos por código de grupo.
- Quais produtos têm `termoencolhível` na descrição?
- Encontre produtos parecidos com este texto.
- Busque por descrição, mas ignore acentos e pequenas diferenças.
- Mostre 3 exemplos de produtos com `TERM`.
- Liste produtos que parecem duplicados.
- Pesquise produtos por código, descrição ou grupo.

---

## 4. Estoque

- Qual o estoque do produto `10080001`?
- Quanto tem em saldo desse item?
- Mostre o estoque por depósito.
- Esse produto tem saldo disponível?
- Liste os depósitos onde esse produto aparece.
- Mostre estoque em tabela.
- Existe saldo bloqueado ou reservado?
- Qual o saldo total considerando todos os depósitos?
- Quais produtos de um grupo estão sem estoque?
- Compare o estoque de dois produtos.

---

## 5. Estrutura, BOM e LMP

- Mostre a estrutura do produto `10080001`.
- Quais componentes formam esse produto?
- Abra a BOM em formato de árvore.
- Liste matéria-prima, intermediário e produto acabado separadamente.
- Quanto de cada componente preciso para fabricar 100 unidades?
- Esse produto tem LMP cadastrada?
- Compare a estrutura de dois produtos.
- Explique a estrutura de forma simples.
- Mostre apenas os componentes de primeiro nível.
- Mostre a estrutura completa com todos os níveis.

---

## 6. Onde o item é usado

- Onde o produto `10080001` é usado?
- Quais produtos pai usam esse componente?
- Esse item entra em quais estruturas?
- Mostre todos os produtos acabados que dependem dessa matéria-prima.
- Esse componente afeta quais produtos se faltar estoque?
- Liste os pais diretos e indiretos desse item.
- Mostre onde esse item aparece na engenharia.
- Quais estruturas usam este terminal?
- Quais produtos podem ser impactados por esse cabo?
- Monte uma análise de impacto desse componente.

---

## 7. Fornecedores

- Quem fornece o produto `10080001`?
- Mostre fornecedores desse item em tabela.
- Esse produto tem fornecedor cadastrado?
- Qual fornecedor principal desse produto?
- Liste produtos sem fornecedor.
- Compare fornecedores de produtos semelhantes.
- Quais fornecedores atendem itens do grupo `1008`?
- Mostre histórico de fornecedores desse produto.
- Esse item tem fornecedor alternativo?
- Quais produtos dependem de fornecedor único?

---

## 8. Clientes

- Quem compra o produto `10080001`?
- Quais clientes compraram esse item?
- Mostre clientes relacionados a esse produto.
- Qual cliente mais comprou esse produto?
- Liste vendas desse produto por cliente.
- Esse produto é vendido para quais clientes?
- Mostre os clientes em tabela.
- Quais clientes compraram produtos desse grupo?
- Existe histórico de venda para esse item?
- Mostre os últimos clientes que compraram esse produto.

---

## 9. Compras

- Mostre compras do produto `10080001`.
- Qual foi a última compra desse item?
- Mostre histórico de compras.
- Quem foi o fornecedor da última compra?
- Qual foi o preço da última compra?
- Liste compras por data.
- Mostre compras em tabela.
- Compare preço de compra entre fornecedores.
- Quais produtos não são comprados há muito tempo?
- Quais compras recentes envolvem esse grupo de produtos?

---

## 10. Vendas e faturamento

- Mostre vendas do produto `10080001`.
- Qual o faturamento desse item?
- Esse produto vendeu nos últimos meses?
- Mostre vendas por cliente.
- Mostre vendas por período.
- Liste as últimas vendas desse produto.
- Compare venda de dois produtos.
- Mostre gráfico de vendas por mês.
- Quais produtos mais venderam em determinado grupo?
- Quais produtos não vendem há muito tempo?

---

## 11. Preços e tabelas

- Qual o preço do produto `10080001`?
- Mostre a tabela de preço desse produto.
- Quanto custa esse item?
- Existe preço cadastrado para esse produto?
- Compare preço de venda e preço de compra.
- Mostre preços por cliente ou tabela.
- Esse preço está atualizado?
- Liste produtos sem preço.
- Mostre variação de preço ao longo do tempo.
- Qual o último preço praticado na venda?

---

## 12. Roteiro de produção

- Qual o roteiro do produto `10080001`?
- Mostre as etapas de produção desse item.
- Esse produto tem roteiro cadastrado?
- Quais operações fazem parte do roteiro?
- Mostre roteiro em tabela.
- Compare roteiro de dois produtos.
- Quais recursos ou centros de trabalho aparecem no roteiro?
- Quais produtos usam determinado roteiro?
- Explique o roteiro em linguagem simples.
- Mostre gargalos possíveis no roteiro.

---

## 13. Inspeção e qualidade

- Mostre o plano de inspeção do produto `10080001`.
- Esse item tem inspeção cadastrada?
- Quais critérios de qualidade existem para esse produto?
- Mostre inspeções por produto.
- Quais produtos precisam de inspeção?
- Existe plano de controle para esse item?
- Mostre a inspeção em tabela.
- Liste produtos sem plano de inspeção.
- Compare inspeção de dois produtos.
- Explique os critérios de inspeção desse item.

---

## 14. Movimentações internas

- Mostre movimentações internas do produto `10080001`.
- Esse item teve transferência?
- Liste movimentações por depósito.
- Mostre entradas e saídas internas.
- Qual foi a última movimentação interna?
- Mostre movimentações por período.
- Compare saldo com movimentações.
- Quais depósitos movimentaram esse produto?
- Mostre histórico em tabela.
- Identifique movimentações atípicas.

---

## 15. Notas fiscais de entrada

- Mostre notas de entrada do produto `10080001`.
- Quais NFs de entrada têm esse item?
- Qual foi a última nota de entrada?
- Mostre fornecedor, data e quantidade.
- Liste notas de entrada por período.
- Compare notas de entrada com compras.
- Mostre NFs de entrada em tabela.
- Esse produto teve entrada fiscal recentemente?
- Quais produtos do grupo X tiveram nota de entrada?
- Mostre itens de NF relacionados a esse código.

---

## 16. Notas fiscais de saída

- Mostre notas de saída do produto `10080001`.
- Quais NFs de saída têm esse produto?
- Qual foi a última nota de saída?
- Mostre cliente, data, quantidade e valor.
- Liste notas de saída por período.
- Compare notas de saída com pedidos.
- Mostre faturamento por nota fiscal.
- Esse item foi faturado recentemente?
- Quais clientes receberam esse produto?
- Mostre NFs de saída em tabela.

---

## 17. Ordem de venda / OV

- Consulte a OV `123456`.
- Mostre os itens dessa OV.
- Essa OV está pendente?
- Quais itens da OV ainda não foram entregues?
- Mostre produto, quantidade vendida e quantidade entregue.
- Compare OV com nota fiscal.
- Liste OVs de um cliente.
- Mostre OVs por período.
- Quais OVs têm produtos do grupo `1008`?
- Explique essa OV em linguagem simples.

---

## 18. SQL

- Monte uma query SQL para listar produtos ativos.
- Revise esta query SQL.
- Explique esse erro de SQL.
- Corrija esta consulta SELECT.
- Monte uma consulta para buscar produtos por grupo.
- Monte uma consulta para vendas por mês.
- Transforme essa pergunta em SQL.
- Explique o resultado dessa query.
- Otimize essa consulta.
- Gere uma query segura somente leitura.

---

## 19. Perguntas de comparação

- Compare estoque, vendas e compras do produto A e B.
- Compare dois produtos parecidos.
- Compare fornecedores de dois itens.
- Compare estrutura de dois produtos.
- Compare preço de compra e preço de venda.
- Compare vendas por cliente.
- Compare movimentações antes e depois de uma data.
- Compare produtos de um mesmo grupo.
- Compare descrição cadastrada com descrição padrão.
- Compare dados cadastrais entre itens similares.

---

## 20. Perguntas com saída em gráfico

- Mostre vendas do produto em gráfico.
- Faça um gráfico mensal de faturamento.
- Mostre evolução do estoque.
- Faça gráfico de compras por fornecedor.
- Mostre ranking de clientes em gráfico.
- Compare produtos em gráfico.
- Mostre consumo mensal desse item.
- Faça gráfico de entradas e saídas.
- Mostre curva de vendas dos últimos 12 meses.
- Gere um gráfico com os produtos mais vendidos.

---

# Sugestão de organização para menu do usuário

## Produto

- Me fale do produto `10080001`.
- Busque produtos com descrição `cabo`.
- Liste produtos do grupo `1008`.

## Estoque

- Estoque do produto `10080001`.
- Saldo por depósito.
- Produtos sem estoque.

## Engenharia

- Estrutura do produto `10080001`.
- Onde esse item é usado?
- Compare duas estruturas.

## Compras

- Compras do produto `10080001`.
- Última compra.
- Fornecedores do item.

## Vendas

- Vendas do produto `10080001`.
- Clientes que compram esse item.
- Faturamento por período.

## Fiscal

- Notas de entrada do produto.
- Notas de saída do produto.
- Compare OV com NF.

## Qualidade

- Inspeção do produto.
- Plano de inspeção.
- Produtos sem inspeção.

## SQL

- Monte uma query.
- Revise esse SQL.
- Explique esse erro.

---

# Sugestão de seção JSON para enriquecer o `capabilities.json`

```json
{
  "richExamples": {
    "product360": [
      "Me traga uma visão 360° do produto 10080001",
      "Mostre cadastro, estoque, estrutura, fornecedores, clientes, compras e vendas do produto 10080001"
    ],
    "impactAnalysis": [
      "Onde o componente 10080001 é usado e quais produtos seriam impactados se faltar estoque?",
      "Faça uma análise de impacto desse item na produção"
    ],
    "comparison": [
      "Compare os produtos 10080001 e 10080002 em cadastro, estoque, vendas e estrutura",
      "Compare fornecedores, compras e preços desses dois itens"
    ],
    "charts": [
      "Mostre vendas mensais do produto 10080001 em gráfico",
      "Gere um gráfico de compras por fornecedor"
    ],
    "diagnostics": [
      "Esse produto está com cadastro completo?",
      "O que falta para esse produto ficar bem cadastrado?"
    ]
  },
  "combinedQuestions": [
    "Tenho o código do produto: mostre estoque, fornecedor, estrutura e últimas vendas.",
    "Esse item está sem estoque. Onde ele é usado e quem fornece?",
    "Esse produto vendeu recentemente? Tem estoque suficiente?",
    "Esse componente é crítico? Mostre onde é usado, saldo e compras recentes.",
    "Compare compra, venda e estoque desse produto."
  ]
}
```

---

# Perguntas combinadas recomendadas

Estas perguntas são mais úteis para usuários reais porque cruzam mais de uma fonte de dados.

- Tenho o código do produto: mostre estoque, fornecedor, estrutura e últimas vendas.
- Esse item está sem estoque. Onde ele é usado e quem fornece?
- Esse produto vendeu recentemente? Tem estoque suficiente?
- Esse componente é crítico? Mostre onde é usado, saldo e compras recentes.
- Compare compra, venda e estoque desse produto.
- Esse produto tem cadastro completo, estoque disponível e histórico de venda?
- Onde esse componente é usado e qual seria o impacto se ele faltar?
- Mostre visão geral do produto com cadastro, estoque, compras, vendas e estrutura.
- Quais produtos de um grupo estão sem estoque, mas tiveram venda recente?
- Quais itens têm fornecedor único e aparecem em várias estruturas?

---

# Observação final

A recomendação principal é transformar as perguntas simples baseadas em endpoints em perguntas orientadas a negócio.

Em vez de mostrar apenas:

- Estoque
- Fornecedores
- Vendas
- Compras
- Estrutura

Também mostrar sugestões como:

- Este produto é crítico?
- Está faltando alguma informação no cadastro?
- Existe risco de falta para produção?
- Quem compra e quem fornece esse item?
- Qual o impacto desse componente nas estruturas?
- O produto tem estoque suficiente para a demanda recente?

Isso torna o Minha DELPI Chat IA mais útil para usuários de engenharia, compras, comercial, PCP, fiscal, qualidade e cadastro.
