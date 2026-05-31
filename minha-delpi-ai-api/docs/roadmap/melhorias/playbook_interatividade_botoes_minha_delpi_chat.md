# Playbook — Interatividade no Minha DELPI Chat IA

> **Status (31/05/2026):** [Parcial — ver STATUS](./STATUS_ROADMAP_MELHORIAS.md).


Projeto: **Minha DELPI Chat IA**

Objetivo: melhorar a interação do usuário com o chat por meio de botões clicáveis, chips contextuais, sugestões de próximos passos, ações rápidas por resposta, menus guiados e feedback estruturado.

---

## 1. Diagnóstico da tela atual

Na tela observada, o usuário pergunta:

> O que você consegue consultar?

O agente responde em texto:

> Entendi que você quer saber se eu consigo executar algo — não que eu execute agora...

A resposta é correta, mas pouco interativa. Ela exige que o usuário digite manualmente o próximo passo.

## Oportunidade

Depois de uma resposta desse tipo, o chat deveria oferecer opções clicáveis como:

- Ver lista completa
- Consultar produto
- Ver estoque
- Buscar fornecedor
- Ver estrutura/BOM
- Ver vendas
- Ver compras
- Consultar LMP/OV
- Gerar gráfico
- Anexar arquivo

Ou seja: o chat não deve apenas explicar; deve **guiar a próxima ação**.

---

# 2. Base do projeto que já permite isso

O projeto já tem vários recursos prontos ou parcialmente prontos para criar uma experiência mais interativa.

## 2.1 Tela inicial com sugestões

O componente `ChatEmptyState` já aceita `starters`, mostra uma saudação variável e renderiza chips clicáveis quando existe `onUseStarter`.

Ele já usa textos como:

- “Ei, {nome}. O que vamos resolver hoje?”
- “Pode perguntar do seu jeito.”
- “Tudo pronto por aqui.”

Também já mostra a dica:

> Escolha uma sugestão ou escreva do seu jeito. Aceito pequenos errinhos de digitação.

Isso é uma ótima base para cards e botões iniciais.

---

## 2.2 Sugestões iniciais existentes

O arquivo `chatHomeStarters.ts` já define sugestões como:

- O que você pode fazer?
- Consultar produto
- Ver estoque
- Buscar fornecedor
- Ver vendas
- Quem é você?

Também define `DEFAULT_AGENT_ICEBREAKERS` com exemplos como:

- O que você consegue consultar?
- Me traga uma visão 360° do produto 10080001
- Qual o estoque do produto 10080001?
- Quem fornece o produto 10080001?
- Onde esse componente é usado?
- Mostre vendas dos últimos 30 dias
- Compare compra, venda e estoque de um produto
- Bora consultar um produto?

Isso deve ser ampliado e usado não só na home, mas também ao longo da conversa.

---

## 2.3 Chips de follow-up já existem

O componente `ChatFollowUpChips` já existe e recebe:

```ts
export type ChatFollowUpSuggestion = {
  label: string;
  query: string;
};
```

Ele renderiza:

- título “Próximos passos”;
- botões clicáveis;
- envio da query ao clicar.

Esse é o ponto principal para melhorar a resposta da imagem. O backend ou o front precisa alimentar `suggestions`.

---

## 2.4 Rich presentation já é interativa

`ChatRichPresentation` já permite:

- alternar visualização entre texto, gráfico, árvore e tabela;
- navegação de página anterior/próxima;
- ampliar níveis;
- drill-down;
- expandir visualização.

Isso mostra que o projeto já está preparado para respostas mais “app-like”, não apenas texto.

---

## 2.5 Tabelas já têm ações

`ChatRichTable` já tem:

- ordenação por coluna;
- copiar tabela;
- baixar CSV;
- expandir;
- clique na linha para detalhar.

Isso deve ser complementado com botões contextuais, como “ver estoque”, “ver fornecedores”, “ver vendas”, “colocar na lousa”.

---

## 2.6 Drill-down já existe

`chatDrillDown.ts` já constrói queries automáticas com base nas colunas da linha.

Exemplos:

- se tiver filial/armazém: `filtre filial 02 armazém 99 do produto 10080001`
- se tiver código: `Detalhe do item 10080001`
- se tiver descrição: `Mais informações sobre descrição`

Esse mecanismo pode ser expandido para criar menus de ação por linha.

---

## 2.7 Feedback guiado já existe

O projeto já tem `ChatMessageFeedbackPanel`, que pergunta:

> Obrigado pelo aviso. O que faltou nesta resposta?

E `chatFeedbackReasons.ts` já possui motivos:

- Dado incorreto
- Não respondeu
- Faltou fonte
- Formato ruim
- Muito longo
- Muito curto
- Consulta errada

Esse recurso pode virar uma interação mais rica, com ações corretivas após o feedback.

---

## 2.8 Input já tem menu de ações

O `ChatInput` já possui:

- botão `+`;
- anexar arquivos;
- escolher agente;
- escolher projeto;
- remover agente/projeto do contexto;
- anexos com chips;
- botão de cancelar resposta.

Esse menu pode receber mais ações rápidas.

---

# 3. Princípio do playbook

A experiência deve transformar o chat de:

> “Digite o que você quer”

para:

> “Escolha, refine, aprofunde ou continue com um clique.”

## Regra de ouro

> Toda resposta útil deve oferecer um próximo passo útil.

Nem toda resposta precisa de 10 botões. Mas respostas como capacidades, produto, estoque, vendas, erro, resultado vazio e tabela devem sugerir o que o usuário pode fazer em seguida.

---

# 4. Tipos de interatividade recomendados

## 4.1 Starters iniciais

Aparecem na tela vazia.

Exemplos:

- O que você pode fazer?
- Consultar produto
- Ver estoque
- Buscar fornecedor
- Consultar OV/LMP
- Anexar arquivo
- Ver indicadores
- Abrir agentes

## 4.2 Chips pós-resposta

Aparecem após uma resposta do assistente.

Exemplos:

- Ver estoque
- Ver fornecedores
- Ver vendas
- Ver compras
- Ver estrutura
- Colocar na lousa
- Gerar gráfico
- Exportar

## 4.3 Botões por tipo de resultado

Aparecem dentro da apresentação rica.

Exemplos em uma tabela de produtos:

- Detalhar item
- Ver estoque
- Ver fornecedor
- Ver vendas
- Comparar

## 4.4 Menu de ações por mensagem

Aparece ao lado ou abaixo da resposta.

Exemplos:

- Copiar
- Reutilizar
- Editar pergunta
- Reenviar
- Continuar daqui
- Colocar na lousa
- Resumir
- Transformar em checklist

## 4.5 Botões de refinamento

Aparecem quando o resultado pode ser filtrado.

Exemplos:

- Filtrar por filial
- Mostrar só com saldo
- Ordenar por valor
- Próxima página
- Ampliar período
- Ver últimos 30 dias

## 4.6 Botões de formato

Aparecem quando o conteúdo pode ser transformado.

Exemplos:

- Tabela
- Gráfico
- Texto curto
- Checklist
- Resumo executivo
- Árvore
- Lousa

## 4.7 Botões de recuperação

Aparecem quando há erro ou resultado vazio.

Exemplos:

- Tentar por descrição
- Ampliar período
- Remover filtro
- Verificar código
- Escolher outro agente
- Tentar novamente

---

# 5. Padrão de dados para sugestões

O componente atual usa apenas:

```ts
{
  label: string;
  query: string;
}
```

Isso funciona, mas pode evoluir para algo mais rico.

## Modelo recomendado

```ts
export type ChatFollowUpSuggestion = {
  id?: string;
  label: string;
  query: string;
  icon?: string;
  kind?: "primary" | "secondary" | "danger" | "ghost";
  group?: "consultar" | "formatar" | "filtrar" | "exportar" | "corrigir";
  requiresConfirmation?: boolean;
  tooltip?: string;
};
```

## Exemplo

```json
{
  "label": "Ver estoque",
  "query": "qual o estoque do produto 10080001?",
  "icon": "warehouse",
  "group": "consultar",
  "kind": "primary",
  "tooltip": "Consulta o saldo disponível do produto"
}
```

---

# 6. Onde gerar as sugestões

Existem duas estratégias.

## 6.1 Frontend gera sugestões

Vantagens:

- Rápido de implementar.
- Não exige mudar API.
- Ideal para sugestões fixas por tela.

Desvantagens:

- Pouco inteligente.
- Difícil usar contexto de toolCalls.
- Pode sugerir ação não permitida.

## 6.2 Backend gera sugestões

Vantagens:

- Usa contexto real.
- Sabe action, produto, período, filial e permissões.
- Evita botão que o usuário não pode usar.
- Pode salvar no metadata da mensagem.

Desvantagens:

- Exige alterar payload.
- Precisa padronizar contrato.

## Recomendação

Usar abordagem híbrida:

- Frontend: starters fixos e fallback.
- Backend: sugestões contextuais por resposta.

---

# 7. Contrato recomendado no backend

Adicionar ao `ChatMessage.metadata` ou ao response `done/playback`:

```json
{
  "followUpSuggestions": [
    {
      "label": "Ver estoque",
      "query": "qual o estoque do produto 10080001?",
      "group": "consultar",
      "icon": "warehouse"
    },
    {
      "label": "Ver fornecedores",
      "query": "quem fornece o produto 10080001?",
      "group": "consultar",
      "icon": "users"
    },
    {
      "label": "Colocar na lousa",
      "query": "coloque essa resposta na lousa",
      "group": "formatar",
      "icon": "canvas"
    }
  ]
}
```

## No front

`ChatMessageList` deve ler:

```ts
message.metadata?.followUpSuggestions
```

e passar para:

```tsx
<ChatFollowUpChips suggestions={suggestions} onUseSuggestion={onReuseMessage} />
```

---

# 8. Regras para gerar sugestões

Criar serviço:

`ChatFollowUpSuggestionService`

## Entradas

- mensagem do usuário;
- resposta do assistente;
- toolCalls;
- presentation;
- action executada;
- entidade principal;
- capabilities do agente;
- permissões do usuário;
- contexto da sessão;
- feedback.

## Saída

Lista de sugestões ordenadas.

## Regras gerais

1. Não sugerir ação sem permissão.
2. Não sugerir gráfico se não houver dados numéricos.
3. Não sugerir próxima página se não houver próxima página.
4. Não sugerir “ver fornecedores” se não houver produto.
5. Não sugerir ações destrutivas como botão simples.
6. Limitar a 3–6 sugestões visíveis.
7. Agrupar sugestões se houver mais de 6.
8. A primeira sugestão deve ser a mais provável.
9. Usar query explícita, não vaga.
10. Sugerir recuperação em caso de erro ou vazio.

---

# 9. Sugestões por tipo de resposta

## 9.1 Resposta de capacidades

Quando o usuário pergunta:

> O que você consegue consultar?

Hoje a resposta é textual. Melhor resposta:

### Texto

> Posso te ajudar com consultas operacionais e respostas guiadas. Escolha uma opção para começar:

### Botões

- Produtos
- Estoque
- Fornecedores
- Estrutura/BOM
- Vendas
- Compras
- OV/LMP
- Indicadores
- SQL
- Anexar arquivo

### Queries

```json
[
  { "label": "Produtos", "query": "quais consultas de produto você consegue fazer?" },
  { "label": "Estoque", "query": "como consultar estoque?" },
  { "label": "Fornecedores", "query": "como consultar fornecedores de um produto?" },
  { "label": "Estrutura/BOM", "query": "como consultar estrutura de um produto?" },
  { "label": "OV/LMP", "query": "como consultar uma OV ou LMP?" }
]
```

## 9.2 Produto consultado

Após consultar produto:

- Ver estoque
- Ver fornecedores
- Ver estrutura
- Ver vendas
- Ver compras
- Onde é usado?
- Visão 360°
- Colocar na lousa

## 9.3 Estoque

Após estoque:

- Ver fornecedores
- Ver compras recentes
- Onde é usado?
- Ver vendas recentes
- Mostrar só saldo disponível
- Filtrar filial
- Exportar CSV
- Colocar na lousa

## 9.4 Fornecedores

Após fornecedores:

- Ver compras
- Ver último preço
- Comparar lead time
- Ver notas de entrada
- Ver produtos do fornecedor
- Colocar na lousa

## 9.5 Vendas

Após vendas:

- Gerar gráfico
- Agrupar por cliente
- Ver notas fiscais de saída
- Comparar com mês anterior
- Ver estoque atual
- Exportar CSV
- Colocar na lousa

## 9.6 Compras

Após compras:

- Agrupar por fornecedor
- Comparar preço
- Ver notas de entrada
- Ver estoque atual
- Gerar gráfico
- Exportar CSV

## 9.7 Estrutura/BOM

Após estrutura:

- Ampliar níveis
- Ver estoque dos componentes
- Ver fornecedores dos componentes
- Onde esse componente é usado?
- Exportar árvore
- Colocar na lousa

## 9.8 KPI

Após KPI:

- Ver gráfico
- Comparar com meta
- Ver tendência
- Filtrar período
- Ver detalhes por departamento
- Explicar variação

## 9.9 Resultado vazio

Após nenhum dado:

- Tentar por descrição
- Ampliar período
- Remover filtro
- Conferir código
- Ver produtos parecidos
- Escolher outro agente

## 9.10 Erro

Após falha:

- Tentar novamente
- Reduzir período
- Verificar permissões
- Trocar agente
- Reportar problema
- Copiar erro

---

# 10. Botões clicáveis por mensagem

Em cada resposta assistant, além de copiar e feedback, sugerir ações.

## Ações padrão

- Copiar
- Reutilizar
- Colocar na lousa
- Resumir
- Transformar em checklist
- Continuar daqui

## Ações para resposta com tabela

- Copiar tabela
- Baixar CSV
- Expandir
- Gerar gráfico
- Filtrar
- Ordenar
- Detalhar linha

## Ações para resposta documental

- Ver fontes
- Resumir
- Transformar em passos
- Colocar na lousa
- Gerar checklist
- Perguntar mais sobre isso

## Ações para resposta operacional

- Ver relacionados
- Cruzar com estoque
- Cruzar com compras
- Cruzar com vendas
- Colocar na lousa
- Gerar relatório

---

# 11. Melhorias na tela inicial

A tela inicial deve ser mais parecida com um “hub de ação”.

## Layout recomendado

### Saudação

> Ei, Robério. O que vamos resolver hoje?

### Subtítulo

> Escolha uma opção ou pergunte do seu jeito.

### Cards principais

1. **Produto**
   - Consultar cadastro, estoque, estrutura e fornecedores.

2. **Estoque**
   - Ver saldo, armazém, reserva e risco de falta.

3. **Vendas**
   - Consultar vendas, clientes, faturamento e gráficos.

4. **Compras**
   - Ver compras, fornecedores, preços e notas de entrada.

5. **OV/LMP**
   - Consultar pedidos, itens pendentes e entregas.

6. **Arquivos**
   - Enviar PDF, Excel, CSV ou documentação.

## Chips rápidos

- O que você pode fazer?
- Visão 360° de produto
- Produtos sem estoque
- Vendas últimos 30 dias
- Analisar arquivo

---

# 12. Melhorias na resposta da imagem

## Resposta atual

A resposta explica, mas não oferece ação direta.

## Resposta recomendada

> Posso consultar várias áreas autorizadas. Escolha uma opção para começar:

### Botões

- Produto
- Estoque
- Fornecedores
- Estrutura/BOM
- Vendas
- Compras
- OV/LMP
- Indicadores
- SQL
- Ajuda completa

## Alternativa com grupos

### Consultas rápidas

- Produto
- Estoque
- Fornecedor
- OV/LMP

### Análises

- Vendas
- Compras
- Indicadores
- Comparar dados

### Formatos

- Tabela
- Gráfico
- Lousa
- Exportar

---

# 13. Menu do botão `+`

O botão `+` do `ChatInput` hoje já permite anexar arquivos e escolher agente/projeto.

Sugestão de novas seções:

## Arquivos

- Anexar arquivos
- Analisar último anexo
- Remover anexos

## Agentes

- Usar agente neste contexto
- Abrir página do agente
- Remover agente

## Projetos

- Usar projeto
- Abrir projeto
- Remover projeto

## Consultas rápidas

- Consultar produto
- Ver estoque
- Buscar fornecedor
- Consultar OV/LMP

## Formato da resposta

- Responder em tabela
- Responder em gráfico
- Responder curto
- Explicar simples
- Manter este formato

## Contexto

- Mostrar contexto ativo
- Limpar contexto
- Usar última resposta
- Colocar última resposta na lousa

---

# 14. Sugestões inteligentes no composer

Além dos botões pós-resposta, o input pode sugerir enquanto o usuário digita.

## Exemplos

Usuário digita:

> estoque

Sugestão:

- estoque do produto 10080001
- consultar estoque por armazém
- produtos sem estoque

Usuário digita:

> ov

Sugestão:

- consulte a OV 123456
- listar OVs por período
- itens pendentes da OV

Usuário digita:

> gráfico

Sugestão:

- gerar gráfico das vendas anteriores
- transformar tabela em gráfico
- gráfico por mês

---

# 15. Contexto ativo clicável

Criar uma barra discreta acima do input:

> Contexto ativo: Produto 10080001 · Filial 01 · Formato tabela

Com chips:

- Produto 10080001
- Filial 01
- Tabela
- Limpar

## Ações

Clicar em “Produto 10080001” abre menu:

- Ver estoque
- Ver fornecedores
- Ver vendas
- Ver compras
- Ver estrutura
- Remover do contexto

Clicar em “Tabela” abre menu:

- Manter tabela
- Trocar para texto
- Trocar para gráfico
- Remover preferência

---

# 16. Interação em tabelas

A tabela já permite copiar, exportar, expandir e clicar na linha. Melhorar com menu por linha.

## Ao clicar numa linha

Abrir popover:

- Detalhar item
- Ver estoque
- Ver fornecedores
- Ver vendas
- Ver compras
- Comparar com outro
- Colocar linha na lousa

## Quando houver coluna produto

Ações:

- Detalhar produto
- Estoque
- Fornecedores
- Estrutura
- Vendas

## Quando houver coluna cliente

Ações:

- Ver vendas do cliente
- Ver últimas notas
- Produtos comprados
- Resumo do cliente

## Quando houver coluna fornecedor

Ações:

- Ver compras
- Ver produtos fornecidos
- Ver notas de entrada
- Comparar lead time

## Quando houver coluna OV

Ações:

- Abrir OV
- Ver itens
- Ver pendências
- Comparar com NF

---

# 17. Interação em gráficos

## Botões recomendados

- Ver como tabela
- Filtrar período
- Comparar período anterior
- Exportar imagem
- Explicar gráfico
- Ver detalhe do maior ponto
- Ver detalhe do menor ponto

## Clique em ponto/barra

Gerar query:

> detalhe o mês de março de 2026 deste gráfico

ou

> mostre os registros que compõem este valor

---

# 18. Interação em árvore/BOM

## Botões recomendados

- Ampliar níveis
- Recolher níveis
- Ver estoque dos componentes
- Ver fornecedores dos componentes
- Exportar árvore
- Colocar na lousa
- Comparar estrutura

## Clique em nó

Menu:

- Detalhar componente
- Ver estoque
- Ver fornecedor
- Onde é usado?
- Ver compras
- Fixar como contexto

---

# 19. Interação com lousa/canvas

O projeto já tem lousa/canvas. Ela pode virar um elemento de produtividade.

## Botões por resposta

- Colocar na lousa
- Atualizar lousa
- Acrescentar à lousa
- Abrir lousa
- Exportar lousa

## Botões dentro da lousa

- Melhorar texto
- Transformar em checklist
- Transformar em relatório
- Adicionar tabela anterior
- Adicionar gráfico anterior
- Salvar como artefato

---

# 20. Sugestões por feedback

Quando o usuário der thumbs down, não parar só no motivo.

## Se motivo = Dado incorreto

Sugerir:

- Reexecutar consulta
- Conferir filtros
- Mostrar detalhes técnicos
- Reportar problema

## Se motivo = Não respondeu

Sugerir:

- Reformular com contexto
- Ver opções disponíveis
- Escolher agente
- Enviar exemplo

## Se motivo = Formato ruim

Sugerir:

- Mostrar em tabela
- Mostrar em gráfico
- Resumir
- Detalhar

## Se motivo = Consulta errada

Sugerir:

- Escolher rota/área
- Ver opções de consulta
- Usar outro agente
- Especificar produto/OV/período

## Novos motivos recomendados

Adicionar:

- Perdeu contexto
- Usou produto errado
- Não seguiu instrução
- Faltou próximo passo
- Botões sugeridos não ajudaram

---

# 21. Estados interativos de loading

O `stream.json` já tem status. Melhorar para estados com microinteração.

## Status com pequenas ações

Enquanto consulta:

> Consultando dados autorizados...

Botão:

- Cancelar

Se demorar:

> Está demorando um pouco. Quer limitar o período?

Botões:

- Cancelar
- Reduzir para últimos 30 dias
- Continuar aguardando

Se falhar:

> Não consegui concluir. Quer tentar de novo?

Botões:

- Tentar novamente
- Reduzir filtro
- Ver detalhes

---

# 22. Fluxos guiados

Algumas consultas podem ser feitas por fluxo de botões, sem o usuário digitar tudo.

## Fluxo: consultar produto

1. Botão: Consultar produto
2. Chat pergunta: “Você tem o código?”
3. Botões:
   - Tenho o código
   - Buscar por descrição
   - Ver exemplos
4. Se “Tenho o código”:
   - input fica com placeholder “Digite o código do produto”
5. Se “Buscar por descrição”:
   - input fica com placeholder “Digite parte da descrição”

## Fluxo: consultar estoque

1. Botão: Ver estoque
2. Pergunta:
   - De qual produto?
3. Depois:
   - Todas as filiais
   - Filial específica
   - Armazém específico

## Fluxo: vendas

1. Botão: Ver vendas
2. Pergunta:
   - Produto
   - Cliente
   - Período
3. Botões de período:
   - Hoje
   - Últimos 7 dias
   - Últimos 30 dias
   - Este mês
   - Mês passado
   - Personalizado

---

# 23. Botões para evitar ambiguidade

Quando o chat precisa perguntar algo, deve oferecer botões.

## Exemplo: mês sem ano

> Para março, qual ano você quer consultar?

Botões:

- Março de 2026
- Março de 2025
- Informar outro ano

## Exemplo: última semana

> Você quer semana passada fechada ou últimos 7 dias?

Botões:

- Semana passada
- Últimos 7 dias

## Exemplo: falta produto

> Para consultar estoque, preciso do produto.

Botões:

- Digitar código
- Buscar por descrição
- Ver exemplo

---

# 24. Sugestões com base em capabilities

O endpoint/camada de capabilities pode fornecer não só texto, mas opções.

## Proposta

```json
{
  "capabilityCards": [
    {
      "title": "Produtos",
      "description": "Cadastro, descrição, grupo e visão 360°.",
      "actions": [
        { "label": "Consultar produto", "query": "me fale do produto 10080001" },
        { "label": "Buscar por descrição", "query": "buscar produtos com descrição cabo" }
      ]
    },
    {
      "title": "Estoque",
      "description": "Saldo, armazém, reservas e disponibilidade.",
      "actions": [
        { "label": "Ver estoque", "query": "qual o estoque do produto 10080001?" }
      ]
    }
  ]
}
```

## Front

Renderizar como cards em vez de texto longo.

---

# 25. Personalização por agente

Cada agente pode ter:

```json
{
  "metadata": {
    "icebreakers": [],
    "quickActions": [],
    "followUpTemplates": {},
    "homeCards": []
  }
}
```

## Exemplo para agente Produto

```json
{
  "quickActions": [
    { "label": "Visão 360°", "query": "visão 360° do produto 10080001" },
    { "label": "Estoque", "query": "estoque do produto 10080001" },
    { "label": "Fornecedores", "query": "fornecedores do produto 10080001" },
    { "label": "Estrutura", "query": "estrutura do produto 10080001" }
  ]
}
```

---

# 26. Priorização visual

Nem toda ação deve ter o mesmo peso.

## Tipos

### Primária

Ação mais provável.

Exemplo:

- Ver lista completa
- Consultar produto

### Secundária

Ação útil, mas não principal.

Exemplo:

- Ver fornecedores
- Gerar gráfico

### Ghost

Ação auxiliar.

Exemplo:

- Copiar
- Ver detalhes

### Perigosa

Ações destrutivas ou sensíveis.

Exemplo:

- Excluir
- Executar escrita
- Enviar e-mail

Para ações perigosas, sempre pedir confirmação.

---

# 27. Onde colocar os botões

## Tela inicial

Starters e cards.

## Após cada resposta

Follow-up chips.

## Dentro de tabela/gráfico/árvore

Ações específicas do dado.

## No input `+`

Menu de ferramentas e contexto.

## Na barra de contexto

Chips ativos.

## Em erro/resultado vazio

Ações de recuperação.

## Em feedback negativo

Ações corretivas.

---

# 28. Exemplo completo: pergunta da imagem

## Usuário

> O que você consegue consultar?

## Resposta ideal

```md
Posso consultar informações autorizadas em algumas frentes. Escolha uma opção para começar:
```

## Chips

```json
[
  { "label": "Produtos", "query": "quais consultas de produto você consegue fazer?" },
  { "label": "Estoque", "query": "como consultar estoque?" },
  { "label": "Fornecedores", "query": "como consultar fornecedores?" },
  { "label": "Estrutura/BOM", "query": "como consultar estrutura de produto?" },
  { "label": "Vendas", "query": "como consultar vendas?" },
  { "label": "Compras", "query": "como consultar compras?" },
  { "label": "OV/LMP", "query": "como consultar OV ou LMP?" },
  { "label": "Ver tudo", "query": "o que você pode fazer? mostre a lista completa" }
]
```

## Resultado esperado

O usuário clica em “Estoque”, e o chat responde:

> Consigo consultar saldo por produto, filial e armazém. Para começar, envie o código do produto.

Chips:

- Tenho o código
- Buscar por descrição
- Ver exemplo

---

# 29. Implementação recomendada

## Fase 1 — Usar o que já existe

- Alimentar `ChatFollowUpChips` com sugestões após respostas.
- Expandir `chatHomeStarters.ts`.
- Expandir `DEFAULT_AGENT_ICEBREAKERS`.
- Adicionar botões de capacidade na resposta de “o que você consegue consultar?”.
- Adicionar mais motivos em `chatFeedbackReasons.ts`.

## Fase 2 — Metadata de sugestões

- Backend envia `metadata.followUpSuggestions`.
- Front renderiza abaixo da resposta.
- Garantir que as queries sejam explícitas.

## Fase 3 — Sugestões por domínio

Criar:

`ChatFollowUpSuggestionService`

Com regras para:

- produto;
- estoque;
- fornecedores;
- vendas;
- compras;
- estrutura;
- KPI;
- erro;
- vazio;
- capabilities.

## Fase 4 — Menus contextuais

- Menu por linha de tabela.
- Menu por nó de árvore.
- Menu por ponto de gráfico.
- Menu por chip de contexto.

## Fase 5 — Fluxos guiados

- Produto.
- Estoque.
- OV/LMP.
- Vendas.
- Compras.
- Anexos.
- Indicadores.

---

# 30. Critérios de qualidade

## Uma boa sugestão deve ser

- clara;
- clicável;
- curta;
- permitida pelo perfil;
- contextual;
- explícita na query;
- útil como próximo passo.

## Uma sugestão ruim é

- vaga;
- sem contexto;
- impossível de executar;
- repetida;
- perigosa sem confirmação;
- genérica demais;
- não relacionada à resposta.

---

# 31. Métricas recomendadas

Medir:

| Métrica | Objetivo |
|---|---|
| CTR dos chips | Saber quais sugestões ajudam |
| Taxa de continuidade | Quantas conversas seguem após chips |
| Uso de starters | Quais cards iniciais funcionam |
| Uso de drill-down | Se clique em tabela é útil |
| Feedback negativo por formato | Avaliar UX da resposta |
| Feedback “não respondeu” | Melhorar suggestions |
| Tempo até primeira ação | Reduzir fricção |
| Taxa de consultas sem digitação | Medir sucesso de botões |

---

# 32. Testes de usabilidade

## Cenário 1 — Usuário novo

1. Entra no chat.
2. Vê cards.
3. Clica em “Consultar produto”.
4. Entende que precisa de código ou descrição.

Critério: não precisa digitar do zero.

## Cenário 2 — Usuário pergunta capacidades

1. Pergunta “o que você consegue consultar?”
2. Vê botões por área.
3. Clica em “Estoque”.
4. Recebe instrução guiada.

Critério: consegue avançar com cliques.

## Cenário 3 — Resultado de produto

1. Consulta produto.
2. Vê botões “Estoque”, “Fornecedores”, “Estrutura”.
3. Clica em “Fornecedores”.

Critério: não precisa repetir código.

## Cenário 4 — Tabela

1. Recebe tabela.
2. Ordena coluna.
3. Clica linha.
4. Escolhe “Detalhar item”.

Critério: drill-down funciona.

## Cenário 5 — Resultado vazio

1. Consulta sem dados.
2. Clica “Ampliar período”.
3. Nova consulta é executada.

Critério: usuário não fica travado.

---

# 33. Cuidados importantes

## Não poluir a tela

Mostrar no máximo:

- 4 chips principais;
- botão “Mais opções” para o restante.

## Não transformar tudo em botão

Ainda deve ser possível digitar livremente.

## Não sugerir ação sem permissão

Validar capabilities e allowed actions.

## Não esconder o texto

Botões ajudam, mas a resposta textual deve continuar compreensível.

## Não usar queries vagas

Evitar:

> fornecedores

Preferir:

> fornecedores do produto 10080001

## Não sugerir ações críticas sem confirmação

Exemplo:

- excluir;
- alterar;
- publicar;
- enviar;
- executar escrita.

---

# 34. Proposta de componentes novos

## `ChatSuggestionCardGrid`

Cards grandes para tela inicial e resposta de capacidades.

## `ChatContextBar`

Mostra contexto ativo.

## `ChatActionMenu`

Popover de ações por mensagem, linha, gráfico ou nó.

## `ChatGuidedFlow`

Fluxos com perguntas e botões.

## `ChatSuggestionGroup`

Agrupa chips por categoria:

- Consultar
- Formatar
- Filtrar
- Exportar
- Corrigir

## `ChatInlinePromptButtons`

Botões para responder clarificações:

- Março de 2026
- Março de 2025
- Últimos 7 dias
- Semana passada

---

# 35. Proposta de extensão para `capabilities.json`

Adicionar:

```json
{
  "interactive": {
    "cards": [
      {
        "title": "Produtos",
        "description": "Cadastro, descrição, estoque, estrutura e fornecedores.",
        "suggestions": [
          { "label": "Consultar produto", "query": "me fale do produto 10080001" },
          { "label": "Visão 360°", "query": "visão 360° do produto 10080001" }
        ]
      },
      {
        "title": "Estoque",
        "description": "Saldo por produto, filial, armazém e disponibilidade.",
        "suggestions": [
          { "label": "Ver estoque", "query": "qual o estoque do produto 10080001?" }
        ]
      }
    ]
  }
}
```

---

# 36. Proposta de extensão para resposta de tool

```json
{
  "metadata": {
    "followUpSuggestions": [
      {
        "label": "Ver estoque",
        "query": "qual o estoque do produto 10080001?",
        "group": "consultar"
      },
      {
        "label": "Ver fornecedores",
        "query": "quem fornece o produto 10080001?",
        "group": "consultar"
      },
      {
        "label": "Colocar na lousa",
        "query": "coloque essa resposta na lousa",
        "group": "formatar"
      }
    ],
    "contextChips": [
      { "label": "Produto 10080001", "kind": "product", "value": "10080001" },
      { "label": "Tabela", "kind": "format", "value": "table" }
    ]
  }
}
```

---

# 37. Resumo executivo

O projeto já tem boa parte da base para interatividade:

- starters na tela inicial;
- icebreakers por agente;
- chips de follow-up;
- tabelas com copiar, CSV, expandir e drill-down;
- rich presentation com texto/gráfico/tabela/árvore;
- feedback com motivos;
- input com menu de arquivos, agentes e projetos.

A melhoria principal é alimentar esses componentes com contexto real.

## Prioridades

1. Usar `ChatFollowUpChips` após respostas como “o que você consegue consultar?”.
2. Enviar `metadata.followUpSuggestions` pelo backend.
3. Criar sugestões por domínio: produto, estoque, vendas, compras, estrutura, KPI.
4. Expandir tela inicial com cards.
5. Adicionar barra de contexto ativo.
6. Adicionar menus por linha de tabela, nó de árvore e ponto de gráfico.
7. Transformar erros e resultados vazios em fluxos de recuperação.
8. Medir clique, continuidade e feedback.

Com isso, o Minha DELPI Chat IA deixa de ser apenas uma conversa textual e passa a funcionar como uma interface guiada, com o usuário avançando por botões, chips e ações contextuais.
