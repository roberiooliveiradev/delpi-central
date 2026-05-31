# Playbook 02 — Respostas operacionais DELPI

> **Status (31/05/2026):** [Parcial — ver STATUS](./STATUS_ROADMAP_MELHORIAS.md).


## Objetivo

Padronizar como o Minha DELPI Chat IA deve responder consultas operacionais sobre produtos, estoque, fornecedores, clientes, estrutura/BOM, compras, vendas, preços, roteiro, inspeção, notas fiscais, LMP/OV, KPIs e SQL.

A meta é entregar respostas claras, acionáveis e consistentes, sem parecer apenas uma tabela bruta.

---

## Princípio central

> Toda resposta operacional deve entregar: resumo, dados, alerta e próximo passo.

Formato recomendado:

1. Frase curta de confirmação.
2. Resumo do achado principal.
3. Tabela, gráfico, árvore ou KPI.
4. Alertas ou inconsistências.
5. Próximos passos clicáveis.

---

## Estrutura padrão de resposta

```md
Boa, encontrei os dados.

## Resumo
[principal conclusão]

## Dados
[tabela/gráfico/árvore]

## Atenção
[alertas, se houver]

## Próximos passos
[chips]
```

---

## Produto

### Perguntas típicas

- Me fale do produto `10080001`.
- Mostre a ficha do produto.
- Esse produto existe?
- Qual grupo e descrição?
- Está ativo ou bloqueado?
- Visão 360° do produto.

### Resposta ideal

- Código.
- Descrição.
- Grupo.
- Tipo.
- Unidade.
- Status.
- Observações.
- Links para estoque, fornecedores, estrutura, vendas e compras.

### Próximos passos

- Ver estoque.
- Ver fornecedores.
- Ver estrutura.
- Ver vendas.
- Ver compras.
- Onde é usado?
- Visão 360°.

---

## Estoque

### Perguntas típicas

- Qual o estoque do produto?
- Mostre saldo por armazém.
- Tem saldo disponível?
- Estoque por filial.
- Produtos sem estoque.

### Resposta ideal

- Saldo total.
- Saldo disponível.
- Reservado/empenhado.
- Filial.
- Armazém.
- Localização.
- Alerta de saldo baixo.

### Alertas

- Sem saldo disponível.
- Saldo negativo.
- Reservado maior que disponível.
- Produto com venda recente e sem estoque.
- Componente crítico sem saldo.

### Próximos passos

- Ver fornecedores.
- Ver compras recentes.
- Onde é usado?
- Ver vendas recentes.
- Gerar alerta de risco.

---

## Fornecedores

### Perguntas típicas

- Quem fornece este produto?
- Esse item tem fornecedor?
- Qual o part number?
- Último preço de compra?
- Lead time?

### Resposta ideal

- Código fornecedor.
- Nome fornecedor.
- Part number.
- Último preço.
- Data do último preço.
- Lead time cadastrado.
- Lead time real.
- Amostras.

### Alertas

- Sem fornecedor.
- Fornecedor único.
- Lead time real maior que cadastrado.
- Preço antigo.
- Sem compra recente.

### Próximos passos

- Ver compras.
- Ver notas de entrada.
- Comparar fornecedores.
- Ver produtos do fornecedor.
- Ver estoque.

---

## Clientes

### Perguntas típicas

- Quem compra este produto?
- Quais clientes compraram?
- Cliente que mais comprou?
- Última venda por cliente.

### Resposta ideal

- Cliente.
- Loja.
- Data última venda.
- Quantidade total.
- Valor total.
- Último preço.

### Próximos passos

- Ver vendas.
- Ver notas de saída.
- Gerar gráfico.
- Comparar clientes.
- Ver produtos similares.

---

## Estrutura/BOM

### Perguntas típicas

- Mostre a estrutura.
- Quais componentes formam esse produto?
- Abra em árvore.
- Quanto preciso para fabricar 100 unidades?
- Compare estruturas.

### Resposta ideal

- Árvore de níveis.
- Componentes.
- Quantidade por nível.
- Unidade.
- Produto pai.
- Matéria-prima/intermediário.
- Nível da BOM.

### Alertas

- Estrutura vazia.
- Componente sem fornecedor.
- Componente sem estoque.
- Componente usado em muitos produtos.
- Possível item crítico.

### Próximos passos

- Ver estoque dos componentes.
- Ver fornecedores.
- Onde componente é usado?
- Ampliar níveis.
- Comparar estrutura.

---

## Onde é usado

### Perguntas típicas

- Onde esse item é usado?
- Quais produtos pai usam esse componente?
- Esse componente impacta quais produtos?

### Resposta ideal

- Produto pai.
- Descrição.
- Nível.
- Quantidade.
- Relação com estrutura.
- Impacto potencial.

### Próximos passos

- Ver estoque.
- Ver vendas dos produtos impactados.
- Ver fornecedores.
- Análise de risco.
- Colocar na lousa.

---

## Compras

### Perguntas típicas

- Mostre compras do produto.
- Última compra.
- Histórico de compra.
- Preço de compra.
- Compras por fornecedor.

### Resposta ideal

- Data.
- Fornecedor.
- Quantidade.
- Preço unitário.
- Valor total.
- Nota/pedido.
- Filial.

### Alertas

- Preço variando muito.
- Sem compra recente.
- Fornecedor único.
- Última compra antiga.
- Lead time alto.

### Próximos passos

- Agrupar por fornecedor.
- Gerar gráfico.
- Ver notas de entrada.
- Comparar preço.
- Ver estoque atual.

---

## Vendas

### Perguntas típicas

- Mostre vendas do produto.
- Faturamento.
- Vendas por cliente.
- Vendas por período.
- Últimas vendas.

### Resposta ideal

- Data.
- Cliente.
- Quantidade.
- Preço.
- Valor total.
- Pedido/OV.
- Nota fiscal.

### Alertas

- Venda recente sem estoque.
- Queda de venda.
- Preço fora do padrão.
- Cliente concentrado.
- Produto sem venda recente.

### Próximos passos

- Gerar gráfico.
- Agrupar por cliente.
- Comparar período.
- Ver estoque.
- Ver notas de saída.

---

## Preços

### Perguntas típicas

- Qual o preço do produto?
- Existe tabela de preço?
- Compare preço de compra e venda.
- Último preço praticado.

### Resposta ideal

- Tabela.
- Preço venda.
- Preço máximo.
- Desconto.
- Último preço praticado.
- Custo médio, se disponível.

### Alertas

- Produto sem preço.
- Preço desatualizado.
- Margem baixa.
- Divergência com venda recente.

### Próximos passos

- Ver vendas.
- Ver compras.
- Comparar margem.
- Ver tabela completa.
- Exportar.

---

## Roteiro

### Perguntas típicas

- Qual o roteiro de produção?
- Quais operações?
- Tempo padrão?
- Máquinas e centros de trabalho?

### Resposta ideal

- Sequência.
- Operação.
- Descrição.
- Centro de trabalho.
- Recurso.
- Setup.
- Tempo padrão.
- Obrigatoriedade.

### Alertas

- Sem roteiro.
- Operação sem recurso.
- Tempo padrão ausente.
- Possível gargalo.

### Próximos passos

- Ver estrutura.
- Ver estoque dos componentes.
- Comparar roteiro.
- Calcular tempo total.
- Colocar na lousa.

---

## Inspeção

### Perguntas típicas

- Plano de inspeção.
- Critérios de qualidade.
- Método e frequência.
- Produtos sem inspeção.

### Resposta ideal

- Tipo de inspeção.
- Característica.
- Especificação.
- Método.
- Frequência.
- Resultado.

### Alertas

- Sem plano.
- Resultado reprovado.
- Especificação ausente.
- Frequência não definida.

### Próximos passos

- Criar checklist.
- Comparar inspeção.
- Ver fornecedor.
- Ver notas.
- Colocar na lousa.

---

## OV/LMP

### Perguntas típicas

- Consulte a OV.
- Mostre a LMP.
- Itens pendentes.
- Entregas.
- Compare OV com NF.

### Resposta ideal

- Nº OV.
- Cliente.
- Produto.
- Quantidade vendida.
- Quantidade entregue.
- Data entrega.
- Status.
- Valor.

### Alertas

- Item pendente.
- Entrega vencida.
- Quantidade não entregue.
- Divergência com NF.

### Próximos passos

- Ver estoque dos itens.
- Ver estrutura.
- Ver notas fiscais.
- Ver produção.
- Gerar relatório.

---

## KPIs

### Perguntas típicas

- Mostre KPIs do período.
- Indicadores abaixo da meta.
- Compare com mês anterior.
- KPIs por departamento.

### Resposta ideal

- Indicador.
- Valor.
- Meta.
- Variação.
- Período.
- Departamento.
- Status.

### Alertas

- Abaixo da meta.
- Variação negativa.
- Sem dados.
- Meta ausente.

### Próximos passos

- Gerar gráfico.
- Ver tendência.
- Explicar variação.
- Comparar departamentos.
- Resumo executivo.

---

## SQL

### Perguntas típicas

- Monte uma query.
- Revise SQL.
- Execute SQL.
- Explique erro.
- Transforme pergunta em SQL.

### Regras

- Diferenciar elaborar de executar.
- Bloquear comandos destrutivos.
- Executar apenas com action permitida.
- Mostrar consulta antes se houver risco.
- Limitar resultados grandes.

### Próximos passos

- Executar.
- Explicar.
- Otimizar.
- Gerar gráfico.
- Exportar CSV.

---

## Resultado vazio

Nunca responder apenas “não encontrei”.

Resposta ideal:

```md
Não encontrei registros para esse filtro.

Possíveis motivos:
- código incorreto;
- período muito restrito;
- filial diferente;
- ausência de cadastro;
- dados não disponíveis nesta fonte.

Posso tentar:
[chips]
```

Chips:

- Buscar por descrição.
- Ampliar período.
- Remover filtro.
- Verificar código.
- Escolher outro agente.

---

## Erro

Resposta ideal:

```md
Não foi possível concluir a consulta agora.

O que você pode tentar:
- tentar novamente;
- reduzir o período;
- informar um código;
- trocar agente;
- abrir diagnóstico.
```

---

## Métricas

- Taxa de respostas com próximo passo.
- Taxa de resultado vazio recuperado.
- Feedback “não respondeu”.
- Feedback “formato ruim”.
- Feedback “consulta errada”.
- Uso de chips após resposta operacional.
- Tempo até próxima ação do usuário.

---

## Resumo executivo

Respostas operacionais devem ser mais que dados. Devem orientar decisão. O padrão ideal é: resumo, dados, alertas e próximos passos. Isso torna o chat útil para engenharia, compras, comercial, PCP, fiscal, qualidade e diretoria.
