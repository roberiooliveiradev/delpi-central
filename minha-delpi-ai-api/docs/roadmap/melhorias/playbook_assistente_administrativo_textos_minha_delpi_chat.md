# Playbook — Assistente administrativo excelente em textos

> **Status (03/06/2026):** [Concluído](./STATUS_ROADMAP_MELHORIAS.md) — UI F3 no MFE; inteligência F1–7 em [`playbook-especialista-editor-textos.md`](../playbook-especialista-editor-textos.md).


Projeto: **Minha DELPI Chat IA**

Objetivo: transformar o chat também em um assistente administrativo de alto nível, capaz de ajudar com escrita, revisão, correção, tradução, resumo, e-mails, atas, comunicados, documentos internos, respostas profissionais e padronização de linguagem — com qualidade comparável a assistentes generalistas como ChatGPT, mas adaptado ao ambiente corporativo DELPI.

---

## 1. Visão geral

Hoje o Minha DELPI Chat IA já está muito orientado a:

- consultas operacionais;
- produtos;
- estoque;
- fornecedores;
- vendas;
- compras;
- LMP/OV;
- dados via actions;
- RAG/documentação;
- agentes especialistas.

A próxima evolução é ampliar a utilidade do chat para tarefas administrativas e textuais do dia a dia.

O chat deve ajudar o usuário a:

- escrever melhor;
- corrigir erros;
- revisar tom;
- traduzir;
- resumir;
- estruturar documentos;
- transformar ideias soltas em texto profissional;
- gerar e-mails;
- criar comunicados;
- criar atas;
- criar checklists;
- melhorar mensagens para clientes, fornecedores e colegas;
- simplificar textos técnicos;
- adaptar linguagem para diferentes públicos.

---

# 2. Princípio central

## O chat não deve ser apenas “consulta de ERP”

Ele deve funcionar em dois grandes modos:

1. **Modo operacional**
   - consulta dados autorizados;
   - usa actions, RAG, tools;
   - responde com tabelas, gráficos, cards e dados.

2. **Modo administrativo/textual**
   - ajuda a escrever, revisar, traduzir e organizar textos;
   - usa o LLM como principal motor;
   - não chama API operacional sem necessidade;
   - preserva o texto do usuário;
   - melhora clareza, gramática, tom e estrutura.

## Regra de ouro

> Se a pergunta for sobre escrever, revisar, traduzir, resumir ou transformar texto, o chat deve priorizar qualidade textual, não rota operacional.

---

# 3. Base do projeto que favorece essa evolução

O modelo conceitual do projeto já define que uma conversa possui mensagens, fontes, anexos, artefatos e pode ou não ter um agente. O chat comum usa políticas padrão, e agentes adicionam prompt, skills, actions e contexto sem substituir o motor do chat.

Isso é importante porque a habilidade administrativa deve ser uma competência transversal do chat base, herdada por agentes quando fizer sentido.

A documentação também define que uma **Skill** é um módulo de comportamento carregado no prompt, não uma rota HTTP nem permissão de banco. Isso encaixa perfeitamente com uma skill de escrita/revisão/tradução.

A arquitetura do chat base já prevê pipeline de mensagens, histórico, tools, RAG e LLM. Também reforça que melhorias de inteligência transversal devem ficar na camada base e serem herdadas por agentes, projetos e demais consumidores.

A arquitetura pré-LLM também recomenda etapas antes do modelo para reduzir custo, aumentar confiabilidade, proteger o sistema e enriquecer o prompt. Para tarefas textuais, isso significa detectar intenção textual antes de tentar usar actions operacionais.

---

# 4. O que o usuário deve conseguir pedir

## 4.1 Escrita

- Escreva um e-mail para o fornecedor cobrando retorno.
- Monte um comunicado interno sobre mudança de horário.
- Escreva uma mensagem para o cliente explicando o atraso.
- Crie uma resposta profissional para este texto.
- Transforme estas ideias em um texto bem escrito.
- Escreva uma introdução para um relatório.
- Monte uma justificativa formal.
- Redija uma solicitação de compra.
- Escreva uma mensagem curta para WhatsApp corporativo.
- Crie um texto para abertura de chamado.

## 4.2 Correção

- Corrija este texto.
- Revise ortografia e gramática.
- Melhore a pontuação.
- Corrija sem mudar muito meu estilo.
- Corrija e destaque o que mudou.
- Revise este e-mail antes de eu enviar.
- Verifique se tem erro de português.
- Deixe mais claro.
- Corrija mantendo tom formal.
- Corrija para português do Brasil.

## 4.3 Reescrita

- Reescreva de forma mais profissional.
- Deixe mais direto.
- Deixe mais educado.
- Deixe mais firme, mas sem ser grosseiro.
- Deixe mais simples.
- Deixe mais técnico.
- Deixe mais comercial.
- Deixe mais objetivo.
- Reescreva para um fornecedor.
- Reescreva para um cliente.

## 4.4 Tradução

- Traduza para inglês.
- Traduza para espanhol.
- Traduza para português.
- Traduza mantendo tom profissional.
- Traduza este e-mail para inglês comercial.
- Traduza e adapte para fornecedor estrangeiro.
- Traduza sem ficar literal demais.
- Traduza mantendo termos técnicos.
- Traduza para linguagem simples.
- Revise esta tradução.

## 4.5 Resumo

- Resuma este texto.
- Faça um resumo executivo.
- Liste os pontos principais.
- Transforme em tópicos.
- Faça um resumo para diretoria.
- Faça um resumo para produção.
- Resuma em 5 linhas.
- Resuma em uma frase.
- Gere os encaminhamentos.
- Gere as pendências.

## 4.6 Organização

- Transforme este texto em checklist.
- Transforme em ata de reunião.
- Organize por tópicos.
- Crie uma pauta.
- Crie plano de ação.
- Separe em problemas, causas e ações.
- Organize em tabela.
- Monte uma sequência de passos.
- Transforme em procedimento.
- Transforme em comunicado.

## 4.7 Comparação e crítica textual

- Compare essas duas versões.
- Qual versão está mais clara?
- O tom está adequado?
- Essa mensagem parece rude?
- O texto está profissional?
- Tem ambiguidade?
- O cliente pode interpretar mal?
- O fornecedor vai entender?
- Melhore a argumentação.
- Dê sugestões de melhoria.

---

# 5. Categorias de intenção textual

Criar um serviço:

`ChatTextTaskIntentService`

## Categorias recomendadas

| Categoria | Exemplos |
|---|---|
| `write` | escreva, redija, monte, crie |
| `correct` | corrija, revise ortografia, arrume português |
| `rewrite` | reescreva, melhore, deixe mais formal |
| `translate` | traduza, passe para inglês/espanhol |
| `summarize` | resuma, pontos principais |
| `structure` | checklist, ata, tabela, tópicos |
| `tone_adjust` | mais educado, mais firme, mais simples |
| `compare_texts` | compare versões, qual está melhor |
| `extract_actions` | pendências, próximos passos |
| `email` | e-mail, assunto, resposta |
| `message` | WhatsApp, Teams, mensagem curta |
| `document` | relatório, comunicado, procedimento |

---

# 6. Como diferenciar texto de consulta operacional

## Deve entrar em modo textual

Mensagens como:

- “corrija este texto”
- “traduza isso”
- “escreva um e-mail”
- “melhore a mensagem”
- “resuma o texto abaixo”
- “transforme em ata”
- “deixe mais profissional”
- “crie um comunicado”
- “revise esta resposta”
- “faça uma versão curta”

## Deve entrar em modo operacional

Mensagens como:

- “qual o estoque do produto 10080001”
- “quem fornece esse item”
- “mostre vendas”
- “consulte a OV”
- “execute essa SQL”
- “liste produtos do grupo 1008”

## Casos mistos

Exemplo:

> Consulte o estoque do produto 10080001 e escreva um e-mail para compras avisando o risco.

Fluxo correto:

1. Executar consulta de estoque.
2. Interpretar risco.
3. Gerar e-mail com base nos dados.
4. Não inventar o que não foi consultado.

---

# 7. Pipeline recomendado

Adicionar uma etapa antes da seleção operacional:

```text
Mensagem do usuário
  → segurança
  → workspace/agente/projeto
  → normalização
  → ChatTextTaskIntentService
      se for tarefa textual pura:
        → TextTaskPreparationService
        → PromptPolicyService(text-admin-assistant.md)
        → LLM
      se for textual + operacional:
        → tools/actions
        → TextTaskComposerService
        → LLM ou direct answer
      se não for textual:
        → pipeline operacional atual
```

## Importante

Tarefas textuais geralmente **não precisam** de:

- action;
- RAG;
- OpenAPI;
- SQL;
- rota operacional;
- dados ERP.

A menos que o usuário peça explicitamente para usar dados do sistema ou documento anexado.

---

# 8. Nova skill recomendada

Criar skill:

`administrative-writing`

ou

`text-assistant`

## Descrição

Skill para escrita, revisão, tradução, resumo, formatação e adaptação de textos administrativos.

## O que ela faz

- Corrige português.
- Reescreve textos.
- Traduz.
- Resume.
- Cria e-mails.
- Gera atas.
- Cria comunicados.
- Organiza ideias.
- Adapta tom.
- Cria checklists.
- Simplifica linguagem técnica.

## O que ela não faz

- Não inventa dados da empresa.
- Não cria promessas comerciais sem confirmação.
- Não altera sentido sem avisar.
- Não assina em nome de pessoas sem autorização.
- Não envia e-mail diretamente, só redige.
- Não usa dados operacionais se não forem fornecidos/consultados.

---

# 9. Policy sugerida: `administrative-writing-skill.md`

```md
# Skill — Assistente administrativo de textos

Você ajuda usuários da DELPI com escrita, revisão, tradução, resumo e organização de textos.

## Objetivos
- Melhorar clareza, gramática, ortografia e tom.
- Preservar o sentido original do usuário.
- Adaptar o texto ao público: cliente, fornecedor, colega, diretoria, produção, compras, comercial.
- Entregar textos prontos para uso quando solicitado.
- Oferecer alternativas quando útil.

## Regras
1. Se o usuário pedir correção, entregue uma versão corrigida.
2. Se o usuário pedir reescrita, preserve o sentido e melhore o tom.
3. Se o usuário pedir tradução, traduza com naturalidade, não palavra por palavra.
4. Se houver ambiguidade, faça no máximo uma pergunta objetiva.
5. Não invente fatos, prazos, preços, nomes, compromissos ou decisões.
6. Não prometa em nome da empresa sem o usuário fornecer essa intenção.
7. Em mensagens sensíveis, use tom profissional e cuidadoso.
8. Quando o usuário pedir “só corrija”, não explique demais.
9. Quando o usuário pedir “mostre alterações”, entregue antes/depois ou lista de mudanças.
10. Para e-mails, inclua assunto se fizer sentido.
11. Para atas, separe participantes, pauta, decisões, pendências e responsáveis quando houver dados.
12. Para tradução técnica, preserve códigos, nomes de produtos, unidades e siglas.

## Formatos úteis
- Versão final
- Antes/depois
- Texto curto
- Texto formal
- Texto simples
- E-mail com assunto
- Checklist
- Ata de reunião
- Resumo executivo
- Tabela de pendências
```

---

# 10. Modos de resposta textual

## 10.1 Só corrigir

Usuário:

> Corrija este texto.

Resposta:

```md
Segue a versão corrigida:

...
```

Sem explicação longa.

## 10.2 Corrigir com explicação

Usuário:

> Corrija e explique os principais ajustes.

Resposta:

1. Versão corrigida.
2. Principais ajustes.
3. Observações.

## 10.3 Reescrever com tom

Usuário:

> Deixe mais formal.

Resposta:

1. Versão formal.
2. Opcional: “mantive o sentido original”.

## 10.4 Criar do zero

Usuário:

> Escreva um e-mail para fornecedor cobrando prazo.

Resposta:

- Assunto.
- Corpo do e-mail.
- Alternativa mais firme, se útil.

## 10.5 Traduzir

Usuário:

> Traduza para inglês.

Resposta:

- Tradução.
- Observação sobre termos mantidos, se necessário.

## 10.6 Resumir

Usuário:

> Resuma esse texto.

Resposta:

- Resumo curto.
- Pontos principais, se fizer sentido.

---

# 11. Padrões de saída

## Correção simples

```md
Segue a versão corrigida:

> [texto corrigido]
```

## Correção com alterações

```md
## Versão corrigida

[texto corrigido]

## Principais ajustes

- Corrigi concordância em...
- Ajustei pontuação em...
- Troquei uma expressão informal por...
```

## E-mail

```md
**Assunto:** [assunto]

Olá, [nome].

[corpo]

Atenciosamente,  
[assinatura]
```

## Mensagem curta

```md
Segue uma versão curta:

[texto]
```

## Comunicado

```md
# Comunicado

Prezados,

[texto]

Atenciosamente,  
[área/equipe]
```

## Ata

```md
# Ata de reunião

**Data:**  
**Participantes:**  
**Pauta:**  

## Pontos discutidos

## Decisões

## Pendências

| Ação | Responsável | Prazo |
|---|---|---|
```

## Tradução

```md
Segue a tradução:

[texto traduzido]
```

## Resumo executivo

```md
## Resumo executivo

[parágrafo curto]

## Pontos principais

- ...
- ...
```

---

# 12. Botões e chips para tarefas de texto

Após uma resposta textual, oferecer chips:

## Após correção

- Deixar mais formal
- Deixar mais curto
- Mostrar alterações
- Traduzir para inglês
- Transformar em e-mail
- Copiar texto

## Após e-mail

- Mais formal
- Mais direto
- Tom mais firme
- Tom mais amigável
- Criar assunto alternativo
- Traduzir

## Após resumo

- Mais curto
- Mais detalhado
- Transformar em checklist
- Gerar ata
- Gerar pendências
- Criar comunicado

## Após tradução

- Revisar tradução
- Deixar mais natural
- Versão formal
- Versão comercial
- Voltar para português
- Manter termos técnicos

## Após texto longo

- Resumir
- Criar tópicos
- Criar checklist
- Criar tabela
- Colocar na lousa
- Exportar

---

# 13. Tela inicial: nova seção “Textos e documentos”

Além dos botões operacionais, adicionar starters administrativos.

## Cards sugeridos

### Escrever texto

Query:

> Escreva um e-mail profissional sobre...

### Corrigir texto

Query:

> Corrija este texto mantendo o sentido original:

### Traduzir

Query:

> Traduza este texto para inglês profissional:

### Resumir

Query:

> Resuma este texto em tópicos:

### Criar ata

Query:

> Transforme estas anotações em ata de reunião:

### Melhorar tom

Query:

> Reescreva este texto de forma mais profissional:

---

# 14. Menu do botão `+`

Adicionar seção:

## Textos

- Corrigir texto
- Escrever e-mail
- Traduzir
- Resumir
- Criar ata
- Criar comunicado
- Transformar em checklist
- Simplificar linguagem

Ao clicar, inserir template no input.

Exemplo:

```text
Corrija este texto mantendo o sentido original:

[cole o texto aqui]
```

---

# 15. Templates prontos para input

## Corrigir

```text
Corrija o texto abaixo, mantendo o sentido original e deixando em português profissional:

[cole o texto aqui]
```

## Reescrever

```text
Reescreva o texto abaixo de forma mais clara e profissional:

[cole o texto aqui]
```

## Traduzir

```text
Traduza o texto abaixo para inglês profissional, preservando termos técnicos, códigos e nomes próprios:

[cole o texto aqui]
```

## E-mail

```text
Escreva um e-mail profissional com base nas informações abaixo.

Objetivo:
Destinatário:
Tom desejado:
Informações principais:
```

## Ata

```text
Transforme as anotações abaixo em uma ata de reunião.

Data:
Participantes:
Anotações:
```

## Resumo

```text
Resuma o texto abaixo em tópicos, destacando decisões, pendências e próximos passos:

[cole o texto aqui]
```

---

# 16. Qualidade esperada para cada tarefa

## Correção

O chat deve:

- corrigir ortografia;
- corrigir gramática;
- corrigir pontuação;
- melhorar fluidez;
- preservar sentido;
- não adicionar informação nova;
- manter nomes, códigos e valores.

## Reescrita

O chat deve:

- melhorar clareza;
- ajustar tom;
- remover redundâncias;
- organizar melhor as ideias;
- preservar intenção;
- apontar se algo ficou ambíguo.

## Tradução

O chat deve:

- traduzir com naturalidade;
- preservar termos técnicos;
- preservar códigos, nomes, medidas e unidades;
- adaptar expressões idiomáticas;
- evitar tradução literal ruim;
- avisar quando um termo pode ter mais de uma tradução.

## Resumo

O chat deve:

- identificar ideia central;
- reduzir sem distorcer;
- separar pontos principais;
- destacar decisões e pendências;
- informar se o texto original não tem dados suficientes.

## E-mail

O chat deve:

- sugerir assunto;
- usar saudação adequada;
- ser claro;
- ter pedido/objetivo explícito;
- fechar profissionalmente;
- não assumir promessas ou prazos não informados.

---

# 17. Tom corporativo DELPI

## Padrão

- Claro.
- Profissional.
- Respeitoso.
- Direto.
- Levemente cordial.
- Sem exagero de formalidade.

## Evitar

- “Venho por meio deste” em excesso.
- Tom agressivo.
- Gírias.
- Emojis em documentos formais.
- Frases longas demais.
- Promessas não autorizadas.
- Linguagem vaga.

## Exemplos de tom

### Neutro profissional

> Solicito, por gentileza, a confirmação do prazo de entrega atualizado.

### Mais firme

> Precisamos receber a confirmação do prazo até o final do dia para evitar impacto no planejamento.

### Mais amigável

> Poderia, por gentileza, nos confirmar o prazo atualizado assim que possível?

### Mais direto

> Favor confirmar o prazo de entrega atualizado.

---

# 18. Público-alvo do texto

O chat deve adaptar conforme o público.

## Cliente

- cordial;
- claro;
- evita culpa;
- foca solução;
- cuidado com promessas.

## Fornecedor

- objetivo;
- cobra prazo ou retorno;
- mantém educação;
- pode ser mais firme.

## Diretoria

- resumo executivo;
- direto;
- dados principais;
- riscos e decisões.

## Produção

- linguagem prática;
- passos claros;
- evitar texto longo.

## Engenharia

- pode manter termos técnicos;
- precisa precisão;
- pode usar tabela/checklist.

## RH/comunicado interno

- tom humano;
- clareza;
- evita ambiguidade.

---

# 19. Tarefas com anexos

Quando o usuário anexar arquivo, o chat deve oferecer:

- Resumir documento.
- Corrigir texto do documento.
- Traduzir documento.
- Extrair pendências.
- Criar ata.
- Criar comunicado.
- Criar checklist.
- Gerar versão executiva.
- Identificar pontos confusos.
- Reescrever para outro público.

## Regra

Se o usuário pedir revisão de documento anexado, usar o anexo como fonte. Se o conteúdo for grande, avisar que pode trabalhar por partes.

---

# 20. Lousa/canvas para textos

A lousa deve ser usada como área de edição.

## Comandos

- Coloque esse e-mail na lousa.
- Atualize a lousa com a versão formal.
- Acrescente uma seção de pendências.
- Reescreva o texto da lousa.
- Faça uma versão curta da lousa.
- Traduza o conteúdo da lousa.
- Transforme a lousa em comunicado.

## Botões

- Revisar
- Reescrever
- Traduzir
- Resumir
- Checklist
- E-mail
- Comunicado
- Exportar

---

# 21. Interatividade para tarefas de texto

## Quando usuário pede “corrigir texto”

Mostrar chips:

- Só corrigir
- Corrigir e explicar
- Deixar formal
- Deixar simples

## Quando usuário pede “escrever e-mail”

Perguntar com botões se faltar dados:

- Para cliente
- Para fornecedor
- Para colega
- Para diretoria

E:

- Tom cordial
- Tom firme
- Tom direto
- Tom formal

## Quando usuário pede “traduzir”

Botões:

- Inglês
- Espanhol
- Português
- Inglês técnico
- Inglês comercial

## Quando usuário pede “resumir”

Botões:

- 3 linhas
- Tópicos
- Resumo executivo
- Pendências
- Checklist

---

# 22. Quando perguntar antes de escrever

Perguntar apenas quando faltar informação essencial.

## E-mail

Perguntar se faltar:

- destinatário/público;
- objetivo;
- tom desejado;
- informações básicas.

Mas se houver dados suficientes, escrever uma primeira versão e oferecer ajustes.

## Tradução

Se o idioma não for informado:

> Para qual idioma você quer traduzir?

Botões:

- Inglês
- Espanhol
- Português

## Correção

Não precisa perguntar. Corrigir direto.

## Resumo

Não precisa perguntar. Resumir direto.

---

# 23. Memória de preferência textual

O chat deve lembrar na sessão:

- “Sempre responda curto.”
- “Sempre me entregue em tópicos.”
- “Prefiro tom formal.”
- “Sempre mostre antes/depois.”
- “Não explique alterações, só entregue a versão final.”
- “Sempre traduza para inglês quando eu pedir tradução.”
- “Use linguagem simples.”

## Exemplo

Usuário:

> Daqui para frente, quando eu pedir correção, só me entregue a versão final.

Chat:

> Combinado. Nesta conversa, quando você pedir correção, vou entregar apenas a versão final corrigida.

---

# 24. Segurança e responsabilidade

## O chat não deve

- inventar fatos;
- criar acusações;
- prometer prazos sem informação;
- assinar por alguém;
- simular aprovação;
- ocultar informação crítica;
- gerar texto ofensivo;
- traduzir alterando sentido;
- transformar rascunho em compromisso jurídico;
- criar comunicado oficial sem indicar que é rascunho.

## Frase útil

> Posso montar uma versão de rascunho, mas recomendo validação interna antes do envio se o texto envolver prazo, preço, responsabilidade, contrato ou compromisso formal.

---

# 25. Formatos administrativos prontos

## E-mail de cobrança de retorno

```md
**Assunto:** Solicitação de retorno

Olá, [Nome].

Poderia, por gentileza, nos retornar sobre [assunto]?

Precisamos dessa confirmação para dar continuidade ao processo e evitar impacto no planejamento.

Fico no aguardo.

Atenciosamente,  
[Seu nome]
```

## E-mail de atraso

```md
**Assunto:** Atualização sobre prazo

Olá, [Nome].

Gostaria de informar que houve um ajuste no prazo referente a [assunto/item].

Estamos acompanhando a situação e retornaremos com uma atualização assim que houver nova confirmação.

Atenciosamente,  
[Seu nome]
```

## Comunicado interno

```md
# Comunicado interno

Prezados,

Informamos que [informação principal].

A mudança passa a valer a partir de [data] e tem como objetivo [motivo].

Em caso de dúvidas, procure [área/responsável].

Atenciosamente,  
[Área]
```

## Ata

```md
# Ata de reunião

**Data:** [data]  
**Participantes:** [nomes]  
**Tema:** [tema]

## Pontos discutidos

- ...

## Decisões

- ...

## Pendências

| Ação | Responsável | Prazo |
|---|---|---|
| ... | ... | ... |
```

## Checklist

```md
# Checklist

- [ ] Item 1
- [ ] Item 2
- [ ] Item 3
```

---

# 26. Resposta ideal por comando

## “Corrija esse texto”

Resposta:

```md
Segue a versão corrigida:

[texto]
```

## “Melhore esse texto”

Resposta:

```md
Segue uma versão mais clara e profissional:

[texto]
```

## “Traduza para inglês”

Resposta:

```md
Segue a tradução para inglês:

[texto]
```

## “Escreva um e-mail”

Resposta:

```md
**Assunto:** ...

Olá, ...

...
```

## “Resuma”

Resposta:

```md
## Resumo

...

## Pontos principais

- ...
```

---

# 27. Sugestões para `capabilities.json`

Adicionar seção de capacidades administrativas.

```json
{
  "textTasks": {
    "title": "Também posso ajudar com textos",
    "examples": [
      "Corrija este texto mantendo o sentido original",
      "Reescreva de forma mais profissional",
      "Traduza para inglês",
      "Resuma em tópicos",
      "Crie um e-mail para fornecedor",
      "Transforme estas anotações em ata",
      "Monte um comunicado interno",
      "Simplifique este texto técnico"
    ]
  }
}
```

---

# 28. Sugestões para `chatHomeStarters.ts`

Adicionar starters:

```ts
export const CHAT_TEXT_STARTERS = [
  { label: "Corrigir texto", query: "Corrija este texto mantendo o sentido original:\n\n" },
  { label: "Escrever e-mail", query: "Escreva um e-mail profissional sobre:\n\n" },
  { label: "Traduzir", query: "Traduza este texto para inglês profissional:\n\n" },
  { label: "Resumir", query: "Resuma este texto em tópicos:\n\n" },
  { label: "Criar ata", query: "Transforme estas anotações em ata de reunião:\n\n" },
  { label: "Melhorar tom", query: "Reescreva este texto de forma mais profissional:\n\n" }
];
```

---

# 29. Sugestões para chips pós-resposta

## Após texto corrigido

```json
[
  { "label": "Mais formal", "query": "deixe a versão anterior mais formal" },
  { "label": "Mais curto", "query": "faça uma versão mais curta do texto anterior" },
  { "label": "Mostrar alterações", "query": "mostre as principais alterações feitas" },
  { "label": "Traduzir", "query": "traduza o texto anterior para inglês" }
]
```

## Após e-mail

```json
[
  { "label": "Tom mais firme", "query": "deixe esse e-mail mais firme, mas educado" },
  { "label": "Mais curto", "query": "faça uma versão mais curta desse e-mail" },
  { "label": "Criar assunto", "query": "me dê 5 opções de assunto para esse e-mail" },
  { "label": "Traduzir", "query": "traduza esse e-mail para inglês profissional" }
]
```

---

# 30. Testes de regressão textual

Criar:

`test_chat_text_tasks.py`

## Casos

### T1 — Correção simples

Input:

> Corrija: nos vai enviar o pedido amanhã

Esperado:

> Nós vamos enviar o pedido amanhã.

### T2 — Reescrita formal

Input:

> Deixe mais formal: manda logo esse retorno

Esperado:

Texto profissional, sem agressividade.

### T3 — Tradução

Input:

> Traduza para inglês: precisamos confirmar o prazo de entrega

Esperado:

Tradução natural.

### T4 — Resumo

Input longo.

Esperado:

Resumo fiel, sem inventar.

### T5 — E-mail

Input:

> Escreva um e-mail cobrando retorno do fornecedor sobre prazo

Esperado:

Assunto + corpo.

### T6 — Não acionar API

Input:

> Corrija este texto: o estoque esta baixo

Esperado:

Não chamar rota de estoque.

### T7 — Texto + operação

Input:

> Consulte o estoque do produto 10080001 e escreva um e-mail avisando compras

Esperado:

Consulta operacional + e-mail baseado no dado.

### T8 — Preferência de sessão

Input:

> Daqui para frente, sempre me entregue só a versão final corrigida.

Depois:

> Corrija: o itens chegou atrasado

Esperado:

Apenas versão final.

### T9 — Anexo

Input com arquivo:

> Resuma esse documento em tópicos

Esperado:

Usar anexo.

### T10 — Termos técnicos

Input:

> Traduza mantendo os termos técnicos e códigos

Esperado:

Preserva códigos, medidas e siglas.

---

# 31. Métricas de qualidade textual

Medir por feedback:

- texto ficou claro;
- texto ficou profissional;
- tradução ficou natural;
- correção preservou sentido;
- resumo foi fiel;
- formato foi adequado;
- resposta foi curta/detalhada demais;
- não seguiu tom pedido;
- inventou informação.

Adicionar motivos de feedback:

```ts
{ id: "text_not_clear", label: "Texto não ficou claro" },
{ id: "changed_meaning", label: "Mudou o sentido" },
{ id: "bad_translation", label: "Tradução ruim" },
{ id: "wrong_tone", label: "Tom inadequado" },
{ id: "invented_info", label: "Inventou informação" }
```

---

# 32. UI recomendada

## Tela inicial

Adicionar grupo:

**Textos e documentos**

- Corrigir texto
- Escrever e-mail
- Traduzir
- Resumir
- Criar ata
- Criar comunicado

## Input

Placeholder dinâmico:

- “Cole um texto para corrigir, resumir ou traduzir...”
- “Peça um e-mail, comunicado, ata ou checklist...”

## Botão `+`

Adicionar seção “Textos”.

## Resposta

Para textos longos, mostrar botões:

- Copiar
- Colocar na lousa
- Reescrever
- Traduzir
- Resumir
- Transformar em checklist

## Lousa

Usar lousa como editor de rascunhos.

---

# 33. Prompt de sistema para chat comum

Adicionar ao prompt base:

```md
Você também é um assistente administrativo de textos.
Ajude com escrita, revisão, correção, tradução, resumo e organização de documentos.
Quando a tarefa for textual, não tente usar actions operacionais.
Preserve o sentido original do usuário.
Não invente fatos, prazos, valores ou compromissos.
Adapte o tom ao público solicitado.
Se o usuário pedir apenas correção, entregue a versão corrigida sem explicações longas.
```

---

# 34. Como evitar conflito com o agente operacional

Quando o usuário estiver em um agente operacional, ele ainda pode pedir texto.

Exemplo:

> Escreva um e-mail com base nesse estoque.

O agente deve conseguir ajudar.

Mas se o usuário disser apenas:

> Corrija este texto

O agente deve tratar como tarefa textual, não tentar consultar ERP.

## Regra

Tarefa textual explícita tem prioridade sobre roteamento operacional, exceto quando o texto pede consulta de dados.

---

# 35. Roadmap de implementação

## Fase 1 — Prompt e capabilities

- Criar policy `administrative-writing-skill.md`.
- Adicionar skill `administrative-writing`.
- Atualizar `capabilities.json`.
- Adicionar starters de texto.
- Adicionar chips pós-resposta textual.

## Fase 2 — Detecção determinística

- Criar `ChatTextTaskIntentService`.
- Impedir actions em tarefas textuais puras.
- Criar testes T1–T6.

## Fase 3 — Templates e UI

- Adicionar seção “Textos” no botão `+`.
- Adicionar cards de texto na home.
- Criar templates no input.
- Integrar lousa como editor de rascunhos.

## Fase 4 — Contexto e preferências

- Memorizar preferências textuais na sessão.
- “Sempre me entregue em tópicos.”
- “Sempre só a versão final.”
- “Sempre tom formal.”

## Fase 5 — Tarefas mistas

- Consulta operacional + geração de texto.
- Anexo + resumo.
- Tabela + e-mail.
- Resultado de estoque + comunicado.

---

# 36. Anti-padrões

Evitar:

1. Chamar API de produto quando o usuário só pediu correção textual.
2. Responder com explicação longa quando pediu “só corrija”.
3. Mudar sentido do texto sem avisar.
4. Inventar fatos para completar e-mail.
5. Traduzir literalmente termos que exigem adaptação.
6. Ignorar público-alvo.
7. Usar tom excessivamente informal em texto corporativo.
8. Fazer perguntas demais antes de criar um rascunho.
9. Não preservar códigos, nomes e valores.
10. Misturar dados operacionais não consultados no texto.

---

# 37. Exemplos práticos

## Exemplo 1 — Correção

Usuário:

> Corrija: segue em anexo os documento solicitado

Resposta:

> Seguem em anexo os documentos solicitados.

## Exemplo 2 — Reescrita profissional

Usuário:

> Melhore: preciso que você mande isso logo porque estamos atrasados

Resposta:

> Poderia, por gentileza, nos enviar essa informação o quanto antes? Precisamos dela para evitar impacto no andamento do processo.

## Exemplo 3 — E-mail

Usuário:

> Escreva um e-mail para fornecedor cobrando o prazo do pedido

Resposta:

```md
**Assunto:** Confirmação de prazo do pedido

Olá, [Nome].

Poderia, por gentileza, nos confirmar o prazo atualizado do pedido?

Precisamos dessa informação para alinhar nosso planejamento interno.

Fico no aguardo.

Atenciosamente,  
[Seu nome]
```

## Exemplo 4 — Tradução

Usuário:

> Traduza: precisamos confirmar o prazo de entrega até amanhã

Resposta:

> We need to confirm the delivery deadline by tomorrow.

## Exemplo 5 — Resumo

Usuário cola texto longo e pede:

> Resuma em tópicos

Resposta:

```md
## Pontos principais

- ...
- ...
- ...

## Pendências

- ...
```

---

# 38. Resumo executivo

Para que o Minha DELPI Chat IA seja também um excelente assistente administrativo, ele precisa tratar tarefas textuais como uma competência central do chat base.

As principais ações são:

1. Criar uma skill de escrita administrativa.
2. Detectar intenções textuais antes do roteamento operacional.
3. Não chamar actions quando o pedido for apenas texto.
4. Criar templates para correção, tradução, e-mail, resumo e ata.
5. Adicionar botões e starters para tarefas textuais.
6. Usar lousa/canvas como editor de rascunhos.
7. Memorizar preferências de estilo na sessão.
8. Testar correção, tradução, resumo, e-mail e tarefas mistas.
9. Medir qualidade textual por feedback específico.
10. Manter segurança: não inventar fatos, prazos, valores ou compromissos.

Com isso, o chat passa a ser útil tanto para consultar dados quanto para ajudar no trabalho administrativo diário.
