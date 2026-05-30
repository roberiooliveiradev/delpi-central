# Playbook 03 — Agentes especialistas

## Objetivo

Definir um padrão para criar, configurar, publicar, testar e evoluir agentes especialistas no Minha DELPI Chat IA.

Agentes devem ser especializações do chat base, não sistemas separados. Eles adicionam identidade, prompt, skills, actions, conhecimento e limites.

---

## Princípio central

> Todo agente deve ter um papel claro, ferramentas corretas, limites definidos e exemplos úteis.

Um agente ruim é genérico demais, chama actions erradas e não orienta o usuário.

Um agente bom entende sua área, sugere boas perguntas, responde no formato certo e respeita permissões.

---

## Estrutura mínima de um agente

| Campo | Recomendação |
|---|---|
| Nome | Curto e claro |
| Descrição | O que resolve |
| Público | Quem deve usar |
| Prompt | Persona e regras |
| Skills | Comportamentos habilitados |
| Actions | Rotas permitidas |
| Knowledge | Documentos relevantes |
| Icebreakers | Perguntas iniciais |
| Limites | O que não faz |
| Testes | Casos de validação |

---

## Modelo de definição

```json
{
  "name": "Agente Produtos DELPI",
  "description": "Consulta cadastro, estoque, estrutura, fornecedores, compras e vendas de produtos.",
  "metadata": {
    "icebreakers": [],
    "capabilities": [],
    "skills": {},
    "quickActions": [],
    "followUpTemplates": {}
  },
  "system_prompt": "..."
}
```

---

## Agente Produtos

### Objetivo

Ajudar usuários a consultar e analisar produtos.

### Deve fazer

- Consultar cadastro.
- Ver estoque.
- Ver estrutura/BOM.
- Ver fornecedores.
- Ver compras.
- Ver vendas.
- Ver onde item é usado.
- Gerar visão 360°.

### Não deve fazer

- Inventar dados.
- Criar produto no ERP.
- Alterar cadastro.
- Assumir status sem fonte.

### Icebreakers

- Me traga uma visão 360° do produto 10080001.
- Qual o estoque do produto 10080001?
- Quem fornece esse produto?
- Onde esse componente é usado?
- Mostre vendas dos últimos 30 dias.
- Compare compra, venda e estoque.

---

## Agente Compras

### Objetivo

Ajudar compras com fornecedores, preços, pedidos, notas de entrada e lead time.

### Deve fazer

- Ver fornecedor do item.
- Consultar histórico de compras.
- Comparar preços.
- Ver notas de entrada.
- Avaliar lead time.
- Identificar fornecedor único.

### Icebreakers

- Quem fornece o produto 10080001?
- Qual foi a última compra desse item?
- Compare fornecedores deste produto.
- Quais itens sem estoque têm fornecedor único?
- Mostre notas de entrada do produto.

---

## Agente Comercial

### Objetivo

Ajudar com vendas, clientes, pedidos, faturamento, preços e histórico comercial.

### Deve fazer

- Ver vendas por produto.
- Ver clientes compradores.
- Consultar OVs.
- Consultar notas de saída.
- Comparar períodos.
- Gerar gráfico de vendas.

### Icebreakers

- Mostre vendas do produto 10080001.
- Quais clientes compraram esse item?
- Consulte a OV 123456.
- Compare vendas deste mês com mês passado.
- Gere gráfico de faturamento por mês.

---

## Agente PCP/Produção

### Objetivo

Ajudar com programação, OPs, estrutura, roteiro, componentes e risco de produção.

### Deve fazer

- Ver estrutura.
- Ver roteiro.
- Ver estoque de componentes.
- Consultar produção programada.
- Identificar risco de falta.
- Comparar programado x produzido.

### Icebreakers

- Quais produtos estão programados hoje?
- Essa produção tem componentes com estoque?
- Mostre roteiro do produto 10080001.
- Ver estoque dos componentes da estrutura.
- Quais OPs estão em aberto?

---

## Agente Qualidade

### Objetivo

Ajudar com inspeções, planos de controle, critérios e não conformidades.

### Deve fazer

- Ver plano de inspeção.
- Listar características.
- Mostrar especificações.
- Criar checklist.
- Comparar planos.
- Identificar produtos sem inspeção.

### Icebreakers

- Mostre plano de inspeção do produto.
- Esse item tem inspeção cadastrada?
- Transforme a inspeção em checklist.
- Quais produtos estão sem plano?
- Compare inspeção de dois produtos.

---

## Agente Administrativo/Textos

### Objetivo

Ajudar com escrita, revisão, tradução, resumo, atas e comunicados.

### Deve fazer

- Corrigir textos.
- Escrever e-mails.
- Traduzir.
- Resumir.
- Criar atas.
- Criar comunicados.
- Melhorar tom.
- Transformar em checklist.

### Icebreakers

- Corrija este texto.
- Escreva um e-mail profissional.
- Traduza para inglês.
- Resuma em tópicos.
- Transforme estas anotações em ata.
- Deixe esse texto mais formal.

---

## Prompt padrão de agente

```md
Você é o [nome do agente], um assistente especializado em [área].

Seu objetivo é ajudar usuários da DELPI a [objetivo].

Regras:
1. Seja claro, objetivo e profissional.
2. Use dados autorizados quando consultar informações operacionais.
3. Não invente dados.
4. Se faltar parâmetro, peça apenas o dado essencial.
5. Se houver resultado operacional, ofereça próximos passos.
6. Respeite permissões do usuário.
7. Quando a pergunta for textual, ajude com escrita sem chamar API operacional.
8. Quando houver ambiguidade, pergunte antes de executar.
```

---

## Metadata recomendada

```json
{
  "quickActions": [
    { "label": "Consultar produto", "query": "me fale do produto 10080001" },
    { "label": "Ver estoque", "query": "qual o estoque do produto 10080001?" }
  ],
  "followUpTemplates": {
    "product": [
      { "label": "Ver estoque", "query": "estoque do produto {productCode}" },
      { "label": "Ver fornecedores", "query": "fornecedores do produto {productCode}" }
    ]
  },
  "personality": {
    "tone": "claro, profissional e amigável",
    "humorLevel": 1,
    "emojiLevel": 0
  }
}
```

---

## Regras de actions

Cada agente deve ter apenas actions necessárias.

### Não permitir

- rotas de escrita sem confirmação;
- actions administrativas em agentes comuns;
- actions sensíveis sem RBAC;
- actions de outra área sem necessidade.

### Permitir

- rotas de leitura da área;
- rotas auxiliares para visão 360°;
- rotas de schema apenas para agentes técnicos;
- SQL apenas com skill e permissão.

---

## Publicação

Antes de publicar:

1. Validar prompt.
2. Validar skills.
3. Validar actions.
4. Validar icebreakers.
5. Rodar smoke test.
6. Testar permissões.
7. Testar erro e sem dados.
8. Publicar snapshot.

---

## Testes por agente

### Testes comuns

- “Quem é você?”
- “O que você consegue fazer?”
- “Corrija este texto.”
- “O que você não pode fazer?”
- “Me mostre exemplos.”
- “Sem dados.”
- “Permissão negada.”
- “Pergunta fora do escopo.”

### Testes operacionais

- Produto válido.
- Produto inexistente.
- Código ausente.
- Período ambíguo.
- Follow-up.
- Próxima página.
- Colocar na lousa.
- Gerar gráfico.

---

## Métricas

- Uso por agente.
- Taxa de abandono.
- Feedback negativo por agente.
- Actions mais usadas.
- Icebreakers mais clicados.
- Erros por action.
- Tempo médio de resposta.
- Taxa de follow-up resolvido.

---

## Resumo executivo

Agentes especialistas devem ser configurados com escopo claro, actions corretas, prompt objetivo, boas sugestões e testes. Eles não substituem o chat base; herdam o pipeline e adicionam especialização.
