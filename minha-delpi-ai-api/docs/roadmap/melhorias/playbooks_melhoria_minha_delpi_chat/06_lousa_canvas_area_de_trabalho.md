# Playbook 06 — Lousa/canvas como área de trabalho

## Objetivo

Transformar a lousa/canvas em uma área de trabalho produtiva para rascunhos, relatórios, atas, análises, textos, comparações e resultados operacionais.

A lousa não deve ser apenas um lugar para copiar uma resposta. Ela deve funcionar como um editor assistido pelo chat.

---

## Visão

A lousa deve permitir que o usuário construa documentos com ajuda do assistente:

- e-mails;
- atas;
- relatórios;
- checklists;
- análises de produto;
- comparativos;
- resumos executivos;
- comunicados;
- procedimentos;
- planos de ação;
- registros de reunião.

---

## Princípio central

> O chat conversa; a lousa organiza o trabalho.

O usuário deve poder dizer:

- coloque isso na lousa;
- acrescente essa tabela;
- transforme em relatório;
- revise o texto da lousa;
- traduza a lousa;
- gere checklist;
- atualize com os dados do produto;
- salve como artefato.

---

## Casos de uso

## 1. Rascunho de e-mail

Usuário:

> Escreva um e-mail para fornecedor cobrando prazo.

Depois:

> Coloque na lousa.

Depois:

> Deixe mais firme.

A lousa deve atualizar o rascunho.

---

## 2. Ata de reunião

Usuário cola anotações:

> Transforme em ata e coloque na lousa.

Lousa contém:

- data;
- participantes;
- pauta;
- pontos discutidos;
- decisões;
- pendências;
- responsáveis.

---

## 3. Relatório operacional

Usuário:

> Faça uma visão 360° do produto 10080001.

Depois:

> Transforme em relatório na lousa.

Lousa contém:

- cadastro;
- estoque;
- fornecedores;
- compras;
- vendas;
- estrutura;
- riscos;
- recomendações.

---

## 4. Comparação

Usuário:

> Compare os produtos 10080001 e 10080002.

Depois:

> Coloque a comparação na lousa.

Lousa contém tabela comparativa e conclusão.

---

## Comandos que o chat deve entender

### Criar

- coloque isso na lousa;
- abra na lousa;
- crie uma lousa com esse texto;
- transforme em documento;
- mande para canvas.

### Atualizar

- atualize a lousa;
- substitua o texto da lousa;
- deixe mais formal;
- corrija a lousa;
- traduza a lousa.

### Acrescentar

- acrescente isso na lousa;
- adicione essa tabela;
- inclua uma seção de pendências;
- coloque esse gráfico também.

### Transformar

- transforme em checklist;
- transforme em ata;
- transforme em relatório;
- transforme em comunicado;
- transforme em e-mail.

### Exportar

- exporte a lousa;
- salve como markdown;
- gere PDF;
- copie o conteúdo;
- baixe o documento.

---

## Ações rápidas na resposta

Após toda resposta útil, oferecer:

- Colocar na lousa.
- Acrescentar à lousa.
- Transformar em checklist.
- Transformar em relatório.
- Criar comunicado.
- Criar ata.

---

## Ações rápidas dentro da lousa

Botões:

- Revisar texto.
- Reescrever.
- Traduzir.
- Resumir.
- Criar checklist.
- Criar tabela.
- Adicionar dados.
- Exportar.
- Limpar.
- Voltar versão.

---

## Memória da lousa

O chat precisa saber:

- se existe lousa aberta;
- qual conteúdo atual;
- última versão;
- última resposta adicionada;
- fonte do conteúdo;
- se veio de API, RAG ou texto;
- se há alterações não salvas.

Modelo:

```json
{
  "canvas": {
    "active": true,
    "lastContentType": "report",
    "lastUpdatedFromMessageId": "uuid",
    "sections": ["Resumo", "Dados", "Pendências"],
    "source": "tool_result"
  }
}
```

---

## Regras de atualização

## Cópia simples

Usuário:

> Coloque isso na lousa.

Ação:

- usar última resposta útil;
- ignorar small talk;
- não copiar mensagens como “Por nada”.

## Append

Usuário:

> Acrescente isso na lousa.

Ação:

- manter conteúdo atual;
- adicionar nova seção;
- evitar duplicar título;
- preservar histórico.

## Substituição

Usuário:

> Substitua a lousa por essa versão.

Ação:

- substituir conteúdo;
- guardar versão anterior.

## Merge operacional

Usuário:

> Acrescente o estoque do produto 10080001 na lousa.

Ação:

- consultar action;
- formatar resultado;
- adicionar seção na lousa.

---

## Estrutura de documento

A lousa deve trabalhar com markdown estruturado.

### Relatório

```md
# Relatório

## Resumo executivo

## Dados consultados

## Análise

## Riscos

## Recomendações

## Próximos passos
```

### Ata

```md
# Ata de reunião

## Participantes

## Pauta

## Pontos discutidos

## Decisões

## Pendências
```

### Checklist

```md
# Checklist

- [ ] Item 1
- [ ] Item 2
```

---

## Integração com anexos

Se o usuário anexar arquivo:

- resumir na lousa;
- extrair pendências;
- transformar em ata;
- revisar texto;
- gerar comunicado;
- comparar com outro arquivo.

---

## Integração com tabelas

A partir de tabela:

- adicionar tabela na lousa;
- gerar resumo da tabela;
- gerar gráfico e conclusão;
- extrair pendências;
- criar relatório.

---

## Integração com gráficos

A partir de gráfico:

- explicar gráfico na lousa;
- adicionar imagem/dados;
- gerar conclusão;
- destacar maior/menor valor;
- sugerir ações.

---

## UX recomendada

## Barra lateral ou painel

A lousa pode aparecer em painel lateral com:

- título;
- conteúdo;
- ações;
- histórico de versões;
- botão exportar;
- botão fechar.

## Indicador no chat

Quando a lousa estiver ativa:

> Lousa aberta: Relatório do produto 10080001

Botões:

- Abrir.
- Atualizar.
- Exportar.
- Limpar.

---

## Versionamento

Guardar versões:

```json
{
  "version": 3,
  "createdAt": "datetime",
  "sourceMessageId": "uuid",
  "operation": "rewrite_formal",
  "content": "..."
}
```

Permitir:

- voltar versão;
- comparar versões;
- ver alterações.

---

## Segurança

A lousa deve deixar claro quando é rascunho.

Para textos formais:

> Rascunho gerado pelo assistente. Revise antes de enviar.

Para dados operacionais:

> Dados baseados na consulta executada nesta sessão.

---

## Testes

- Colocar última resposta útil.
- Não copiar “obrigado”.
- Append sem duplicar.
- Atualizar texto da lousa.
- Adicionar resultado de action.
- Transformar em ata.
- Exportar markdown.
- Usar anexo.
- Restaurar versão anterior.
- Limpar lousa.

---

## Métricas

- Quantidade de lousas criadas.
- Ações mais usadas.
- Exportações.
- Feedback por conteúdo de lousa.
- Uso com documentos.
- Uso com respostas operacionais.
- Tempo de edição.
- Versões por lousa.

---

## Resumo executivo

A lousa deve virar a área de trabalho do chat. O usuário conversa para gerar conteúdo e usa a lousa para organizar, editar, revisar e exportar. Isso aumenta muito a utilidade administrativa e analítica do Minha DELPI Chat IA.
