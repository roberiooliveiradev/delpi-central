# Análise e sugestões — `stream.json`

Arquivo analisado:

`minha-delpi-ai-api/app/content/pt-BR/assistant/stream.json`

## Objetivo do arquivo

O `stream.json` centraliza mensagens curtas exibidas durante o fluxo de geração de resposta do Minha DELPI Chat IA.

Ele cobre estados como:

- Conexão iniciada.
- Carregamento do histórico.
- Consulta à documentação autorizada.
- Execução de ferramentas internas.
- Geração e finalização da resposta.
- Título padrão de sessão.
- Geração automática de título.
- Contexto RAG vazio.
- Cabeçalhos de contexto documental e ferramentas.
- Playback da resposta.
- Cancelamento.
- Erro genérico.

Esse arquivo é importante para a experiência do usuário, porque mostra o que o sistema está fazendo enquanto a resposta é preparada.

---

# Estrutura encontrada

## Status de processamento

| Chave | Texto atual |
|---|---|
| `statusConnected` | Conectado. Preparando resposta... |
| `statusDirectAnswer` | Resposta pronta. |
| `statusLoadingHistory` | Carregando histórico da conversa... |
| `statusSearchingKnowledge` | Consultando documentação autorizada... |
| `statusRunningTools` | Consultando dados autorizados... |
| `statusGeneratingAnswer` | Gerando resposta... |
| `statusFinalizing` | Finalizando resposta... |
| `playbackStatus` | Exibindo resposta... |
| `cancelledStatus` | Resposta cancelada. |
| `errorGenericStatus` | Não foi possível concluir a resposta. Tente novamente. |

## Título de sessão

| Chave | Finalidade |
|---|---|
| `sessionTitleDefault` | Título padrão para nova conversa |
| `sessionTitleEmptyValues` | Valores considerados vazios ou genéricos |
| `titleGenerationSystem` | Instrução para gerar título curto |
| `titleGenerationUserTemplate` | Template do prompt de título |

## Contextos

| Chave | Finalidade |
|---|---|
| `ragEmptyContext` | Mensagem quando nenhum trecho documental foi encontrado |
| `toolContextHeader` | Cabeçalho para resultados de ferramentas internas |
| `ragContextHeader` | Cabeçalho para contexto documental autorizado |

---

# 1. Status de conexão

## Chave

`statusConnected`

## Texto atual

> Conectado. Preparando resposta...

## Finalidade

Indica que a conexão de streaming foi estabelecida e que o backend começou a preparar a resposta.

## Perguntas/casos relacionados

- Usuário enviou uma nova mensagem.
- Sistema abriu canal de resposta.
- Resposta ainda não começou a aparecer.
- O chat está preparando contexto antes de gerar texto.

## Sugestões de melhoria

Adicionar variantes por tipo de fluxo:

```json
{
  "statusConnectedByMode": {
    "default": "Conectado. Preparando resposta...",
    "agent": "Conectado ao agente. Preparando consulta...",
    "rag": "Conectado. Preparando consulta documental...",
    "tools": "Conectado. Preparando dados autorizados..."
  }
}
```

## Texto alternativo sugerido

> Conectado. Organizando o contexto da conversa...

---

# 2. Resposta direta

## Chave

`statusDirectAnswer`

## Texto atual

> Resposta pronta.

## Finalidade

Usado quando não há necessidade de RAG, ferramentas ou processamento mais pesado.

## Exemplos de uso

- Small talk.
- Resposta simples.
- Ajuda curta.
- Mensagem de identidade.
- Resposta baseada em contexto imediato.

## Sugestões de melhoria

Adicionar status mais natural:

```json
{
  "statusDirectAnswerVariants": [
    "Resposta pronta.",
    "Pronto.",
    "Tudo certo.",
    "Resposta gerada."
  ]
}
```

## Observação

Para interface corporativa, “Resposta pronta.” é bom: curto, claro e neutro.

---

# 3. Carregamento de histórico

## Chave

`statusLoadingHistory`

## Texto atual

> Carregando histórico da conversa...

## Finalidade

Indica que o sistema está recuperando mensagens anteriores para manter contexto.

## Casos de uso

- Continuação de conversa.
- Pergunta como “explique essa tabela”.
- Refinamento de uma consulta anterior.
- Pedido de “faça o mesmo”.
- Pedido de “continue”.
- Resposta dependente de contexto anterior.

## Sugestões de melhoria

Adicionar status com foco no valor:

```json
{
  "statusLoadingHistoryDetailed": "Carregando histórico para manter o contexto..."
}
```

## Possível texto alternativo

> Recuperando contexto da conversa...

---

# 4. Consulta à documentação autorizada

## Chave

`statusSearchingKnowledge`

## Texto atual

> Consultando documentação autorizada...

## Finalidade

Indica que o sistema está buscando conteúdo documental autorizado, provavelmente via RAG.

## Casos de uso

- Perguntas sobre processos internos.
- Ajuda sobre funcionalidades.
- Explicações baseadas em documentação.
- Políticas, manuais e conteúdo institucional.
- Perguntas sobre uso da plataforma.

## Sugestões de melhoria

Adicionar diferenciação por fonte:

```json
{
  "statusSearchingKnowledgeBySource": {
    "docs": "Consultando documentação autorizada...",
    "projectFiles": "Consultando arquivos do projeto...",
    "attachments": "Analisando anexos enviados...",
    "knowledgeBase": "Buscando na base de conhecimento autorizada..."
  }
}
```

## Texto alternativo sugerido

> Buscando informações na documentação autorizada...

---

# 5. Consulta de dados autorizados

## Chave

`statusRunningTools`

## Texto atual

> Consultando dados autorizados...

## Finalidade

Indica que uma ou mais ferramentas/actions internas estão sendo executadas.

## Casos de uso

- Consulta de produto.
- Estoque.
- Fornecedores.
- Clientes.
- LMP.
- Estrutura/BOM.
- Compras.
- Vendas.
- Preços.
- Notas fiscais.
- Indicadores.
- SQL autorizado.

## Sugestões de melhoria

Adicionar status por domínio:

```json
{
  "statusRunningToolsByDomain": {
    "stock": "Consultando estoque autorizado...",
    "product": "Consultando produto autorizado...",
    "supplier": "Consultando fornecedores autorizados...",
    "sales": "Consultando vendas autorizadas...",
    "purchase": "Consultando compras autorizadas...",
    "invoice": "Consultando notas fiscais autorizadas...",
    "production": "Consultando produção autorizada...",
    "kpi": "Consultando indicadores autorizados...",
    "sql": "Executando consulta SQL autorizada..."
  }
}
```

## Benefício

O usuário entende melhor o que está acontecendo, principalmente quando a consulta demora.

---

# 6. Geração de resposta

## Chave

`statusGeneratingAnswer`

## Texto atual

> Gerando resposta...

## Finalidade

Indica que o sistema já tem contexto/dados suficientes e está montando a resposta final.

## Sugestões de melhoria

Adicionar status mais explicativo:

```json
{
  "statusGeneratingAnswerDetailed": "Organizando os dados e gerando a resposta..."
}
```

## Casos úteis

- Após retorno de API.
- Após RAG.
- Após múltiplas consultas.
- Antes de formatar tabela/resumo/gráfico.

---

# 7. Finalização

## Chave

`statusFinalizing`

## Texto atual

> Finalizando resposta...

## Finalidade

Indica etapa final antes de entregar a resposta.

## Sugestões de melhoria

Adicionar status para formatação:

```json
{
  "statusFormatting": "Formatando resposta...",
  "statusBuildingTable": "Montando tabela...",
  "statusBuildingChart": "Preparando gráfico...",
  "statusSummarizing": "Preparando resumo..."
}
```

## Benefício

Ajuda quando o resultado exige formatação, tabela ou gráfico.

---

# 8. Título padrão de sessão

## Chave

`sessionTitleDefault`

## Texto atual

> Nova conversa

## Finalidade

Define o título inicial de uma conversa antes de gerar um título baseado no conteúdo.

## Valores vazios reconhecidos

O arquivo considera como vazios ou genéricos:

- nova conversa
- novo chat
- conversa sem titulo
- conversa sem título
- sem titulo
- sem título
- chat novo
- conversa nova
- untitled
- new chat

## Sugestões de melhoria

Adicionar outras variações comuns:

```json
{
  "sessionTitleEmptyValuesExtra": [
    "sem nome",
    "conversa",
    "chat",
    "nova sessão",
    "sessão nova",
    "título automático",
    "conversa automática"
  ]
}
```

---

# 9. Geração automática de título

## Chaves

- `titleGenerationSystem`
- `titleGenerationUserTemplate`

## Regra atual

O sistema deve criar títulos curtos para conversas corporativas, em português, sem aspas, sem ponto final e com no máximo 6 palavras.

## Exemplos bons de títulos

- Consulta de estoque
- Produto sem fornecedor
- Vendas por período
- Estrutura do produto
- Indicadores de produção
- Notas fiscais de saída
- Ajuda sobre agentes
- Roteiro de produção
- Comparação de produtos
- SQL de vendas

## Sugestões de melhoria

Adicionar regras para preservar entidades importantes:

```json
{
  "titleGenerationRules": {
    "maxWords": 6,
    "preserveProductCode": true,
    "preserveSaleNumber": true,
    "preferBusinessContext": true,
    "avoidGenericTitles": true,
    "avoidSensitiveData": true
  }
}
```

## Exemplos de títulos por pergunta

| Pergunta | Título sugerido |
|---|---|
| “Mostre estoque do produto 10080001” | Estoque do produto 10080001 |
| “Quem fornece esse item?” | Fornecedores do produto |
| “Compare vendas deste mês” | Comparação de vendas mensais |
| “Execute essa SQL” | Consulta SQL |
| “O que você pode fazer?” | Capacidades do assistente |

---

# 10. Contexto RAG vazio

## Chave

`ragEmptyContext`

## Texto atual

> Nenhum trecho documental relevante foi encontrado.

## Finalidade

Indica que a busca documental não retornou contexto útil.

## Sugestões de melhoria

Adicionar orientação ao usuário:

```json
{
  "ragEmptyContextWithHint": "Nenhum trecho documental relevante foi encontrado. Tente usar outros termos, enviar um arquivo ou especificar melhor o assunto."
}
```

## Resposta ideal

> Não encontrei documentação relevante para esse assunto. Posso tentar buscar com outros termos ou responder com base no que já está na conversa.

---

# 11. Cabeçalho de ferramentas internas

## Chave

`toolContextHeader`

## Texto atual

> Resultados de ferramentas internas autorizadas:

## Finalidade

Separar contexto retornado por tools/actions autorizadas.

## Sugestões de melhoria

Adicionar cabeçalhos por tipo:

```json
{
  "toolContextHeaders": {
    "default": "Resultados de ferramentas internas autorizadas:",
    "product": "Dados autorizados do produto:",
    "stock": "Dados autorizados de estoque:",
    "sales": "Dados autorizados de vendas:",
    "sql": "Resultado da consulta SQL autorizada:",
    "kpi": "Indicadores autorizados:"
  }
}
```

---

# 12. Cabeçalho de contexto documental

## Chave

`ragContextHeader`

## Texto atual

> Contexto documental autorizado:

## Finalidade

Separar contexto vindo de documentação autorizada.

## Sugestões de melhoria

Adicionar contexto mais claro:

```json
{
  "ragContextHeaders": {
    "default": "Contexto documental autorizado:",
    "docs": "Trechos da documentação autorizada:",
    "attachments": "Trechos dos anexos enviados:",
    "project": "Trechos dos arquivos do projeto:"
  }
}
```

---

# 13. Playback da resposta

## Chave

`playbackStatus`

## Texto atual

> Exibindo resposta...

## Finalidade

Indica que a resposta está sendo apresentada ao usuário.

## Sugestões de melhoria

O texto atual é bom. Poderia haver variante para respostas longas:

```json
{
  "playbackStatusLong": "Exibindo resposta completa..."
}
```

---

# 14. Cancelamento

## Chave

`cancelledStatus`

## Texto atual

> Resposta cancelada.

## Finalidade

Indica que o usuário ou sistema interrompeu a geração.

## Sugestões de melhoria

Adicionar próxima ação:

```json
{
  "cancelledStatusWithHint": "Resposta cancelada. Você pode enviar uma nova pergunta ou reformular o pedido."
}
```

---

# 15. Erro genérico

## Chave

`errorGenericStatus`

## Texto atual

> Não foi possível concluir a resposta. Tente novamente.

## Finalidade

Mensagem padrão para falha inesperada.

## Sugestões de melhoria

Criar erros mais específicos:

```json
{
  "errorStatuses": {
    "generic": "Não foi possível concluir a resposta. Tente novamente.",
    "network": "Falha de conexão. Verifique sua rede e tente novamente.",
    "timeout": "A resposta demorou além do esperado. Tente novamente com um pedido mais específico.",
    "tool": "Não foi possível consultar os dados autorizados agora.",
    "rag": "Não foi possível consultar a documentação autorizada agora.",
    "permission": "Não foi possível acessar essa informação com as permissões atuais.",
    "cancelled": "Resposta cancelada."
  }
}
```

---

# Estados adicionais recomendados

## 1. Fila/aguardando

```json
{
  "statusQueued": "Aguardando processamento..."
}
```

## 2. Validando permissões

```json
{
  "statusCheckingPermissions": "Validando permissões..."
}
```

## 3. Interpretando pergunta

```json
{
  "statusUnderstandingQuestion": "Interpretando sua pergunta..."
}
```

## 4. Escolhendo agente/action

```json
{
  "statusSelectingAction": "Selecionando a melhor consulta..."
}
```

## 5. Montando tabela

```json
{
  "statusBuildingTable": "Montando tabela..."
}
```

## 6. Gerando gráfico

```json
{
  "statusBuildingChart": "Preparando gráfico..."
}
```

## 7. Resumindo dados

```json
{
  "statusSummarizingData": "Resumindo os dados encontrados..."
}
```

## 8. Exportando arquivo

```json
{
  "statusExportingFile": "Gerando arquivo para download..."
}
```

## 9. Reexecutando consulta

```json
{
  "statusRetrying": "Tentando novamente..."
}
```

## 10. Paginação

```json
{
  "statusLoadingMore": "Carregando mais resultados..."
}
```

---

# Sugestão de fluxo completo de status

## Resposta direta

1. Conectado. Preparando resposta...
2. Resposta pronta.
3. Exibindo resposta...

## Resposta com RAG

1. Conectado. Preparando resposta...
2. Carregando histórico da conversa...
3. Consultando documentação autorizada...
4. Gerando resposta...
5. Finalizando resposta...
6. Exibindo resposta...

## Resposta com action/API

1. Conectado. Preparando resposta...
2. Carregando histórico da conversa...
3. Consultando dados autorizados...
4. Gerando resposta...
5. Finalizando resposta...
6. Exibindo resposta...

## Resposta composta

1. Conectado. Preparando resposta...
2. Interpretando sua pergunta...
3. Validando permissões...
4. Consultando dados autorizados...
5. Resumindo os dados encontrados...
6. Montando tabela...
7. Finalizando resposta...
8. Exibindo resposta...

---

# Perguntas e casos de teste

## Status direto

- Oi
- Obrigado
- Quem é você?
- Como usar o chat?
- O que você pode fazer?

## Status com documentação

- Explique como funciona a Minha DELPI.
- O que é um agente?
- Como funciona permissão?
- Onde encontro determinada funcionalidade?
- Resuma esta documentação.

## Status com ferramentas

- Mostre estoque do produto 10080001.
- Consulte fornecedores do produto.
- Mostre vendas dos últimos 30 dias.
- Execute essa SQL.
- Mostre a LMP da OV 123456.

## Status com erro

- API indisponível.
- Timeout.
- Falta de permissão.
- RAG sem resultado.
- Cancelamento pelo usuário.

---

# Proposta de extensão JSON

```json
{
  "statusUnderstandingQuestion": "Interpretando sua pergunta...",
  "statusCheckingPermissions": "Validando permissões...",
  "statusSelectingAction": "Selecionando a melhor consulta...",
  "statusBuildingTable": "Montando tabela...",
  "statusBuildingChart": "Preparando gráfico...",
  "statusSummarizingData": "Resumindo os dados encontrados...",
  "statusExportingFile": "Gerando arquivo para download...",
  "statusRetrying": "Tentando novamente...",
  "statusLoadingMore": "Carregando mais resultados...",
  "errorStatuses": {
    "generic": "Não foi possível concluir a resposta. Tente novamente.",
    "network": "Falha de conexão. Verifique sua rede e tente novamente.",
    "timeout": "A resposta demorou além do esperado. Tente novamente com um pedido mais específico.",
    "tool": "Não foi possível consultar os dados autorizados agora.",
    "rag": "Não foi possível consultar a documentação autorizada agora.",
    "permission": "Não foi possível acessar essa informação com as permissões atuais."
  },
  "titleGenerationRules": {
    "maxWords": 6,
    "preserveProductCode": true,
    "preserveSaleNumber": true,
    "preferBusinessContext": true,
    "avoidGenericTitles": true
  }
}
```

---

# Recomendações finais

O `stream.json` é pequeno, mas muito importante para a percepção de qualidade do chat.

Ele informa ao usuário que o sistema está trabalhando e reduz a sensação de travamento.

As principais melhorias recomendadas são:

- Adicionar status para interpretação da pergunta.
- Adicionar status para validação de permissões.
- Diferenciar consulta documental de consulta operacional.
- Adicionar status específicos por domínio: estoque, produto, vendas, SQL, KPI.
- Criar mensagens específicas para timeout, permissão, ferramenta e RAG.
- Melhorar o fallback quando não há contexto documental.
- Adicionar status para tabela, gráfico, resumo, exportação e paginação.
- Reforçar regras de geração de títulos para manter nomes úteis e curtos.

Com essas melhorias, o Minha DELPI Chat IA fica mais transparente, confiável e agradável durante respostas demoradas ou consultas com múltiplas etapas.
