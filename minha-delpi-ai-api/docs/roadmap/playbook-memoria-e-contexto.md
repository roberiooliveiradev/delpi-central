# Playbook — Memória e Contexto do Minha DELPI Chat IA

**Status (03/06/2026):** Fase 1 **concluída** — `ChatConversationStateService` (activeTopic/activeTask, siga/próximo, correções, mudança de assunto, «isso» ambíguo). Fases 2–9 em backlog. Base legada: Playbook 01. Validação: `scripts/run_memory_context_validation.sh` · Arquitetura: [`../architecture/session-memory.md`](../architecture/session-memory.md).

Projeto: Minha DELPI Chat IA
Escopo: memória de conversa, contexto de sessão, continuidade entre perguntas, preferências do usuário, recuperação de referências, RAG conversacional, memória de longo prazo, arquitetura neural e governança de contexto.

---

## 1. Objetivo

Criar uma camada avançada de memória e contexto para que o chat da Minha DELPI consiga interagir como um assistente inteligente, mantendo continuidade semelhante ao ChatGPT.

O chat deve conseguir:

- lembrar o assunto atual da conversa;
- entender referências como “isso”, “aquele produto”, “a resposta anterior”, “a tabela”, “o último e-mail”;
- manter preferências do usuário durante a sessão;
- respeitar instruções de comportamento dadas pelo usuário;
- reutilizar informações já fornecidas;
- não perguntar novamente o que já foi informado;
- resumir contexto antigo;
- recuperar fatos relevantes de conversas anteriores, quando permitido;
- diferenciar memória temporária de memória persistente;
- evitar usar contexto errado;
- explicar quando não tiver contexto suficiente;
- preservar continuidade em tarefas longas;
- permitir que o usuário corrija o contexto;
- permitir limpar, editar ou substituir contexto;
- melhorar a assertividade das respostas.

---

## 2. Princípio central

O chat deve ser orientado por contexto, não apenas pela última mensagem.

Regra principal:

Resposta boa = mensagem atual + intenção + histórico relevante + entidades ativas + preferências + fontes confiáveis + limites claros.

O chat não deve simplesmente responder à última frase isoladamente.

Ele deve interpretar a conversa como uma sequência.

---

## 3. Problema que este playbook resolve

Sem memória e contexto, o chat pode:

- esquecer o produto mencionado antes;
- perder a consulta anterior;
- não entender “adicione isso”;
- repetir perguntas;
- ignorar instruções de tom;
- misturar assuntos;
- usar resposta errada como referência;
- perder o estado de uma análise;
- não lembrar preferências do usuário;
- não continuar uma tarefa longa;
- responder de forma genérica;
- não perceber correções feitas pelo usuário;
- usar contexto antigo quando o usuário já mudou de assunto.

---

## 4. Tipos de memória

A arquitetura deve separar memória em camadas.

### 4.1 Memória imediata

É o conteúdo das últimas mensagens dentro da janela de contexto.

Uso:

- entender a pergunta atual;
- responder follow-ups curtos;
- resolver “isso” e “esse item”;
- manter continuidade recente.

Duração:

- apenas durante a conversa ativa.

---

### 4.2 Memória de sessão

É o estado estruturado da conversa atual.

Armazena:

- assunto ativo;
- entidades mencionadas;
- última resposta útil;
- último arquivo analisado;
- última tabela;
- último gráfico;
- última consulta SQL;
- última lousa;
- preferências temporárias;
- agente ativo;
- filtros usados;
- intenção atual;
- tarefa em andamento.

Duração:

- enquanto durar a sessão.

---

### 4.3 Memória de tarefa

É a memória específica de uma tarefa em andamento.

Exemplos:

- escrever um e-mail;
- montar uma ata;
- analisar uma planilha;
- construir uma consulta SQL;
- revisar um desenho técnico;
- criar documentação;
- gerar um relatório;
- preparar apresentação.

Armazena:

- objetivo da tarefa;
- versão atual;
- alterações pedidas;
- pendências;
- decisões;
- formato final;
- restrições.

---

### 4.4 Memória semântica

É o conhecimento consolidado sobre fatos estáveis.

Exemplos:

- o que é a Minha DELPI;
- como funciona a plataforma;
- glossário;
- funcionalidades do chat;
- playbooks;
- documentação interna;
- regras de arquitetura;
- padrões de resposta;
- descrições de módulos.

Implementação recomendada:

- base vetorial;
- documentos versionados;
- embeddings;
- busca híbrida;
- reranking;
- citações;
- validade temporal.

---

### 4.5 Memória episódica

É o histórico de interações e eventos.

Exemplos:

- usuário pediu ontem um relatório;
- usuário corrigiu que determinado cálculo estava errado;
- usuário trabalhou em uma consulta SQL específica;
- usuário criou uma ata;
- usuário analisou determinado arquivo;
- usuário pediu sempre respostas objetivas nesta sessão.

Uso:

- continuidade;
- retomada;
- personalização;
- recuperação de decisões anteriores.

Atenção:

Memória episódica persistente exige governança, permissão e opção de exclusão.

---

### 4.6 Memória procedural

É a memória de como agir.

Exemplos:

- como corrigir texto;
- como montar e-mail;
- como explicar ELI5;
- como analisar SQL;
- como tratar erros;
- como usar lousa;
- como gerar gráficos;
- como responder com fontes;
- como escolher entre API, RAG, web e texto puro.

Pode ser implementada por:

- system prompts;
- playbooks;
- skills;
- policies;
- exemplos few-shot;
- roteadores de intenção.

---

### 4.7 Memória de preferências

Armazena preferências do usuário.

Exemplos:

- responder em português;
- ser mais direto;
- não explicar correções;
- sempre usar markdown;
- preferir respostas em texto para copiar;
- sempre sugerir assunto de e-mail;
- usar tom formal;
- não usar listas longas;
- chamar a plataforma de Minha DELPI;
- preservar termos técnicos.

Deve ter controle:

- preferência temporária;
- preferência persistente;
- preferência por tipo de tarefa;
- preferência revogada.

---

## 5. Modelo mental recomendado

A memória do chat deve seguir um ciclo:

1. Ler a mensagem atual.
2. Recuperar contexto relevante.
3. Resolver referências.
4. Atualizar estado da sessão.
5. Decidir a ação.
6. Gerar resposta.
7. Registrar o que deve ser lembrado.
8. Esquecer ou compactar o que não é mais útil.

Esse ciclo pode ser chamado de:

Context Memory Loop

---

## 6. Arquitetura geral proposta

Criar uma camada de memória independente, acoplada ao chat, mas separada do modelo LLM.

Componentes:

- ContextOrchestrator
- ConversationStateManager
- MemoryWriteService
- MemoryReadService
- MemoryConsolidationService
- ReferenceResolutionService
- EntityTracker
- UserPreferenceManager
- TaskStateManager
- ConversationSummarizer
- ContextCompressionService
- SemanticMemoryRetriever
- EpisodicMemoryRetriever
- ProceduralMemoryProvider
- ContextRankingService
- ContextSafetyFilter
- ContextAuditService
- MemoryFeedbackService

---

## 7. Fluxo completo de contexto

Fluxo recomendado:

Mensagem do usuário
→ detectar intenção
→ recuperar estado da sessão
→ extrair entidades
→ resolver referências
→ recuperar memórias relevantes
→ ranquear contexto
→ montar prompt contextual
→ executar resposta
→ analisar resposta
→ gravar nova memória
→ atualizar estado
→ sugerir próximos passos

---

## 8. ContextOrchestrator

Responsabilidade:

Orquestrar todo o contexto antes de chamar o modelo.

Entrada:

- mensagem atual;
- histórico recente;
- usuário;
- sessão;
- agente ativo;
- arquivos anexados;
- ferramentas disponíveis;
- permissões;
- contexto salvo.

Saída:

- prompt contextual organizado;
- entidades resolvidas;
- memória relevante;
- preferências aplicadas;
- restrições;
- instruções de resposta.

---

## 9. ConversationStateManager

Responsabilidade:

Manter o estado estruturado da conversa.

Exemplo:

{
  "sessionId": "sess_123",
  "activeTopic": "especialista SQL",
  "activeTask": "criar playbook",
  "lastUserIntent": "create_playbook",
  "lastAssistantOutputType": "txt_playbook",
  "activeEntities": {
    "platform": "Minha DELPI",
    "feature": "memória e contexto",
    "audience": "outra IA implementadora"
  },
  "preferences": {
    "format": "txt para copiar",
    "language": "pt-BR",
    "detailLevel": "completo"
  }
}

---

## 10. EntityTracker

Responsabilidade:

Extrair e manter entidades importantes.

Tipos de entidade:

- produto;
- cliente;
- fornecedor;
- pedido;
- arquivo;
- gráfico;
- tabela;
- consulta SQL;
- e-mail;
- ata;
- pessoa;
- setor;
- agente;
- app;
- rota;
- plugin;
- documento;
- período;
- filial;
- status;
- métrica;
- intenção;
- preferência.

Exemplo:

Usuário:

Consulte o produto 10080022. Agora veja fornecedores.

Estado esperado:

{
  "activeEntities": {
    "productCode": "10080022"
  },
  "referenceResolution": {
    "fornecedores": "fornecedores do produto 10080022"
  }
}

---

## 11. ReferenceResolutionService

Responsabilidade:

Resolver expressões ambíguas.

Exemplos:

- isso;
- esse;
- essa resposta;
- o anterior;
- aquela tabela;
- esse produto;
- esse arquivo;
- a última consulta;
- a lousa;
- o gráfico;
- ele;
- ela;
- esse código;
- essa versão.

Ordem de prioridade:

1. Última entidade explícita do mesmo tipo.
2. Última resposta útil.
3. Último artefato gerado.
4. Último arquivo anexado.
5. Última tabela ou gráfico.
6. Última tarefa ativa.
7. Perguntar ao usuário se houver ambiguidade.

Exemplo de resposta em caso ambíguo:

Quando você diz “isso”, você quer se referir à última resposta, à tabela gerada ou ao arquivo analisado?

---

## 12. TaskStateManager

Responsabilidade:

Manter continuidade de tarefas longas.

Exemplos de tarefas:

- criar playbook;
- escrever e-mail;
- revisar documento;
- montar SQL;
- analisar dados;
- criar apresentação;
- gerar relatório;
- corrigir lousa;
- montar ata.

Estado de tarefa:

{
  "taskId": "task_123",
  "type": "playbook_creation",
  "objective": "Criar playbook de memória e contexto",
  "currentVersion": 3,
  "status": "in_progress",
  "lastAction": "expanded_architecture",
  "constraints": [
    "sem depender de TOTVS",
    "linguagem clara para outra IA implementar"
  ],
  "pending": [
    "adicionar métricas",
    "adicionar testes"
  ]
}

---

## 13. UserPreferenceManager

Responsabilidade:

Gerenciar preferências do usuário.

Preferências temporárias:

- válidas apenas na sessão;
- derivadas de frases como “agora responda curto”;
- expiram quando usuário mudar assunto ou revogar.

Preferências persistentes:

- só devem ser salvas se a plataforma permitir;
- devem ter transparência;
- devem permitir exclusão;
- devem ser usadas com cautela.

Exemplos:

{
  "userPreferences": {
    "language": "pt-BR",
    "responseFormat": "txt para copiar",
    "tone": "direto e técnico",
    "likesPlaybooks": true,
    "avoidInventing": true
  }
}

---

## 14. MemoryWriteService

Responsabilidade:

Decidir o que deve ser salvo.

Nem tudo deve virar memória.

Salvar quando:

- usuário declara preferência;
- usuário corrige uma informação importante;
- usuário define uma regra de comportamento;
- usuário escolhe um formato recorrente;
- surge uma entidade ativa importante;
- há decisão em tarefa longa;
- há resumo consolidado útil;
- há feedback negativo relevante;
- há instrução de projeto.

Não salvar:

- dado sensível sem necessidade;
- segredo;
- senha;
- token;
- informação pessoal desnecessária;
- conteúdo acidental;
- texto temporário irrelevante;
- erro que já foi corrigido;
- detalhe técnico sem valor futuro.

---

## 15. MemoryReadService

Responsabilidade:

Buscar memórias úteis para a resposta atual.

Critérios:

- relevância semântica;
- recência;
- prioridade;
- confiança;
- tipo de tarefa;
- usuário;
- sessão;
- fonte;
- validade temporal;
- permissão;
- escopo.

Não carregar memória demais.

Regra:

Contexto recuperado deve ser útil, pequeno e confiável.

---

## 16. MemoryConsolidationService

Responsabilidade:

Transformar histórico bruto em memória organizada.

Funções:

- resumir conversas longas;
- consolidar decisões;
- remover duplicações;
- atualizar preferências;
- arquivar entidades antigas;
- detectar contradições;
- marcar contexto obsoleto;
- gerar memória semântica;
- gerar memória episódica.

Exemplo:

Histórico bruto:

Usuário pediu 10 vezes “coloque em txt para copiar”.

Memória consolidada:

Usuário frequentemente prefere playbooks em bloco txt para copiar.

---

## 17. ConversationSummarizer

Responsabilidade:

Criar resumos de conversa para economizar contexto.

Tipos de resumo:

- resumo curto;
- resumo operacional;
- resumo de decisões;
- resumo de entidades;
- resumo de tarefas pendentes;
- resumo técnico;
- resumo para retomada.

Resumo ideal:

{
  "summary": "O usuário está criando playbooks para melhorar o Minha DELPI Chat IA. O formato preferido é txt para copiar. O playbook atual é sobre memória e contexto.",
  "entities": ["Minha DELPI Chat IA", "playbook", "memória e contexto"],
  "decisions": ["usar linguagem clara para outra IA implementar"],
  "pending": ["adicionar arquitetura, testes, métricas e roadmap"]
}

---

## 18. ContextCompressionService

Responsabilidade:

Compactar contexto sem perder informações importantes.

Estratégias:

1. Compressão extrativa
   - preserva frases originais importantes.

2. Compressão abstrativa
   - reescreve em resumo menor.

3. Compressão estruturada
   - transforma conversa em JSON.

4. Compressão por prioridade
   - mantém apenas entidades, decisões e restrições.

5. Compressão hierárquica
   - resumo de mensagens → resumo de sessão → memória consolidada.

---

## 19. SemanticMemoryRetriever

Responsabilidade:

Buscar conhecimento por significado.

Implementação recomendada:

- embeddings;
- busca vetorial;
- busca lexical;
- busca híbrida;
- reranker;
- filtros por fonte;
- filtros por data;
- filtros por permissão;
- filtros por tipo.

Exemplo:

Usuário:

Como funciona autorização?

O sistema pode recuperar:

- documentação de RBAC;
- permission resolver;
- app authorization;
- fluxo de requisição;
- JWT.

---

## 20. EpisodicMemoryRetriever

Responsabilidade:

Buscar episódios de conversa anteriores.

Exemplos:

- “Como fizemos no playbook anterior?”
- “Continue de onde paramos.”
- “Use o mesmo padrão do último.”
- “Faça igual ao documento anterior.”
- “Lembra quando corrigimos isso?”

Retorno ideal:

- episódio relevante;
- resumo;
- data;
- tarefa;
- confiança;
- limitação;
- link interno se existir.

---

## 21. ProceduralMemoryProvider

Responsabilidade:

Fornecer instruções de como agir.

Exemplos:

- playbook de escrita;
- playbook de SQL;
- playbook de erros;
- playbook de lousa;
- playbook de web;
- playbook de análise de desenho;
- regras oficiais do GPT arquiteto DELPI;
- templates de resposta.

Uso:

Antes de responder, o sistema deve carregar o procedimento mais específico para a intenção detectada.

---

## 22. ContextRankingService

Responsabilidade:

Escolher quais memórias entram no prompt.

Critérios de ranking:

- relevância semântica;
- proximidade temporal;
- relação com tarefa ativa;
- autoridade da fonte;
- confiança;
- especificidade;
- preferência do usuário;
- escopo correto;
- não contradição;
- tamanho.

Pontuação sugerida:

score =
  0.35 * semantic_similarity
+ 0.20 * recency
+ 0.15 * task_match
+ 0.10 * source_authority
+ 0.10 * user_preference_match
+ 0.10 * confidence

---

## 23. ContextSafetyFilter

Responsabilidade:

Impedir uso indevido de memória.

Bloquear:

- segredos;
- senhas;
- tokens;
- dados pessoais desnecessários;
- dados sensíveis sem permissão;
- contexto de outro usuário;
- contexto de outra sessão sem autorização;
- fonte obsoleta;
- memória contradita por correção mais recente.

Regra:

Memória não deve vazar dados nem substituir permissão.

---

## 24. Estratégia neural 1 — Embeddings semânticos

Usar embeddings para transformar mensagens, documentos e memórias em vetores.

Objetivo:

- recuperar conteúdos semanticamente parecidos;
- encontrar contexto mesmo com palavras diferentes;
- buscar memórias antigas relevantes;
- mapear termos técnicos e sinônimos.

Exemplo:

Usuário fala:

“controle de acesso”

Sistema recupera:

- RBAC;
- permissões;
- autorização;
- Permission Resolver;
- /me/apps.

---

## 25. Estratégia neural 2 — Reranking

Após recuperar candidatos por embedding e busca lexical, usar reranker.

Objetivo:

- reduzir falso positivo;
- melhorar precisão;
- escolher os trechos mais úteis;
- evitar carregar documentos apenas superficialmente parecidos.

Pipeline:

query
→ busca vetorial top 50
→ busca lexical top 50
→ união
→ reranker neural
→ top 5 final
→ prompt

---

## 26. Estratégia neural 3 — Classificação de intenção

Usar modelo classificador para detectar intenção.

Classes:

- text_task;
- sql_task;
- product_query;
- document_analysis;
- memory_update;
- preference_update;
- explanation;
- web_search;
- chart_request;
- canvas_action;
- file_action;
- error_recovery;
- general_chat.

Saída:

{
  "intent": "memory_context_playbook",
  "confidence": 0.94,
  "requiresMemory": true,
  "requiresTool": false,
  "requiresClarification": false
}

---

## 27. Estratégia neural 4 — Extração de entidades

Usar modelo de NER ou LLM estruturado para extrair entidades.

Saída:

{
  "entities": [
    {
      "type": "feature",
      "value": "memória e contexto",
      "confidence": 0.98
    },
    {
      "type": "product",
      "value": "Minha DELPI Chat IA",
      "confidence": 0.99
    }
  ]
}

---

## 28. Estratégia neural 5 — Resolução de correferência

Usar modelo para identificar a que pronomes e expressões se referem.

Exemplos:

- isso → último playbook;
- ele → chat;
- essa funcionalidade → memória e contexto;
- a anterior → resposta anterior;
- esse arquivo → último arquivo anexado.

Quando confiança baixa:

Perguntar antes de agir.

---

## 29. Estratégia neural 6 — Memória hierárquica

Inspirar a arquitetura em camadas de memória:

- contexto imediato;
- resumo da sessão;
- memória de tarefa;
- memória semântica;
- memória episódica;
- memória persistente.

A cada resposta, o sistema decide:

- o que fica no prompt;
- o que fica no resumo;
- o que vai para armazenamento;
- o que será esquecido.

---

## 30. Estratégia neural 7 — Gating de memória

Implementar um mecanismo de decisão antes de escrever memória.

Perguntas do gate:

- isso será útil no futuro?
- é uma preferência?
- é uma decisão?
- é sensível?
- é confiável?
- foi dito pelo usuário?
- contradiz memória anterior?
- deve expirar?
- precisa de confirmação?

Saída:

{
  "shouldWrite": true,
  "memoryType": "preference",
  "ttl": "session",
  "confidence": 0.92,
  "content": "Usuário prefere playbooks em txt para copiar."
}

---

## 31. Estratégia neural 8 — Reflexão controlada

Usar reflexão para consolidar aprendizados.

A reflexão não deve inventar.

Ela deve gerar:

- resumo;
- decisões;
- preferências;
- pendências;
- contradições;
- riscos;
- próximos passos.

Exemplo:

Após várias mensagens, gerar:

O usuário está construindo um conjunto de playbooks para evoluir o chat comum. Prefere respostas completas, em formato txt para copiar, com linguagem implementável por outra IA.

---

## 32. Estratégia neural 9 — Detecção de contradição

O sistema deve detectar quando uma memória nova contradiz uma anterior.

Exemplo:

Memória antiga:

Usuário prefere respostas curtas.

Nova mensagem:

Agora quero respostas completas e detalhadas.

Ação:

- atualizar preferência da sessão;
- marcar preferência antiga como substituída;
- não usar as duas ao mesmo tempo.

---

## 33. Estratégia neural 10 — Learned forgetting

Implementar esquecimento controlado.

Esquecer ou despriorizar:

- contexto obsoleto;
- preferências temporárias expiradas;
- tarefas concluídas;
- entidades antigas sem uso;
- arquivos antigos;
- filtros antigos;
- decisões substituídas.

Não esquecer rapidamente:

- instruções oficiais;
- preferências confirmadas;
- decisões de projeto;
- correções do usuário;
- avisos de erro recorrente.

---

## 34. Contexto ativo

O chat deve sempre manter um contexto ativo.

Exemplo:

{
  "activeContext": {
    "topic": "playbooks de melhoria do chat",
    "currentPlaybook": "memória e contexto",
    "format": "txt para copiar",
    "audience": "IA implementadora",
    "style": "completo e técnico"
  }
}

Esse contexto deve ser usado para resolver mensagens curtas como:

- siga;
- próximo;
- faça o mesmo;
- continue;
- agora coloque em md;
- agora resuma;
- agora aprofunde.

---

## 35. Barra de contexto na UI

Recomendação para frontend:

Mostrar uma barra discreta com:

- assunto ativo;
- tarefa ativa;
- arquivo ativo;
- entidade ativa;
- filtro ativo;
- preferência ativa.

Exemplo:

Contexto ativo:
Playbook · Memória e Contexto · Formato txt · Público: IA implementadora

Ações:

- editar contexto;
- limpar contexto;
- fixar contexto;
- ver memória usada.

---

## 36. Comandos de memória que o usuário deve poder usar

O chat deve entender:

- lembre disso nesta conversa;
- esqueça isso;
- limpe o contexto;
- use o contexto anterior;
- ignore a resposta anterior;
- continue de onde paramos;
- use o mesmo padrão;
- não use mais essa informação;
- corrija sua memória;
- isso está errado;
- considere isso daqui para frente;
- volte para o assunto anterior;
- troque o contexto para X;
- quais informações você está usando?

---

## 37. Resposta quando contexto estiver incerto

Quando a confiança for baixa, o chat deve perguntar.

Exemplo:

Não tenho certeza se “isso” se refere ao playbook anterior ou ao texto sobre SQL. Você quer continuar qual deles?

Botões:

- Playbook anterior
- Texto SQL
- Última resposta
- Novo assunto

---

## 38. Resposta quando o usuário corrigir o contexto

Usuário:

Não, eu estava falando do playbook de textos.

Resposta:

Entendido. Vou considerar o playbook de textos como contexto ativo a partir de agora.

Ação interna:

- atualizar activeTopic;
- registrar correção;
- reduzir peso do contexto incorreto;
- continuar resposta.

---

## 39. Memória de instruções de comportamento

O chat deve manter instruções comportamentais enquanto forem válidas.

Exemplos:

- “responda como arquiteto”
- “não invente”
- “use linguagem simples”
- “sempre em txt”
- “não cite TOTVS”
- “use exemplos”
- “não coloque em lousa”
- “seja mais técnico”

Estado:

{
  "behaviorDirectives": [
    {
      "instruction": "usar linguagem clara para outra IA implementar",
      "scope": "current_task",
      "priority": "high"
    }
  ]
}

---

## 40. Prioridade de contexto

Quando houver conflito, aplicar prioridade:

1. Regras oficiais do sistema.
2. Segurança e permissões.
3. Instruções oficiais do projeto.
4. Pedido atual do usuário.
5. Correções recentes do usuário.
6. Estado da tarefa ativa.
7. Preferências de sessão.
8. Memória persistente.
9. Histórico antigo.
10. Conhecimento geral.

---

## 41. Memória e permissões

Memória não pode ultrapassar autorização.

Exemplo:

Se o usuário não tem permissão para um app, a memória não deve revelar dados desse app.

A arquitetura da Minha DELPI já define que a Core API é a fonte oficial de autorização de apps e rotas, e o Portal deve consumir a visão autorizada via `/me/apps`. Portanto, a memória deve respeitar o mesmo princípio: lembrar não significa autorizar.

---

## 42. Memória e RAG

RAG e memória devem trabalhar juntos.

Diferença:

- RAG busca conhecimento documental.
- Memória busca contexto conversacional e preferências.
- Estado da sessão mantém o foco atual.
- Prompt final combina tudo.

Pipeline:

pergunta
→ memória de sessão
→ memória semântica
→ RAG documental
→ reranking
→ resposta com fontes

---

## 43. Memória e anexos

Quando o usuário anexa arquivo, registrar:

- nome do arquivo;
- tipo;
- resumo;
- última ação;
- trechos relevantes;
- limitações;
- se foi usado na resposta.

Exemplo:

{
  "activeAttachment": {
    "filename": "relatorio.xlsx",
    "type": "spreadsheet",
    "lastAction": "summary",
    "summary": "Planilha com dados de vendas mensais."
  }
}

---

## 44. Memória e lousa

A lousa deve ter memória própria.

Armazenar:

- documento ativo;
- tipo do documento;
- versão;
- última alteração;
- origem;
- pendências;
- instruções de edição.

Exemplo:

{
  "canvas": {
    "active": true,
    "title": "Playbook de Memória e Contexto",
    "documentType": "playbook",
    "version": 4,
    "lastOperation": "append_section"
  }
}

---

## 45. Memória e SQL

Para consultas SQL, manter workspace:

{
  "sqlWorkspace": {
    "objective": "ranking de vendas",
    "dialect": "postgresql",
    "tables": ["orders", "customers"],
    "filters": {
      "period": "last_6_months"
    },
    "selectedColumns": [],
    "lastSql": "",
    "lastResultSummary": {}
  }
}

Permitir:

- adicione coluna;
- remova filtro;
- compare com anterior;
- explique a query;
- gere gráfico.

---

## 46. Memória e textos

Para escrita, manter:

{
  "textWorkspace": {
    "documentType": "email",
    "tone": "formal",
    "audience": "fornecedor",
    "lastVersion": 2,
    "constraints": [
      "não inventar prazo",
      "manter cordialidade"
    ]
  }
}

Permitir:

- deixe mais formal;
- deixe mais curto;
- mantenha o sentido;
- gere 3 versões;
- coloque na lousa.

---

## 47. Memória e gráficos

Para gráficos, manter:

{
  "chartContext": {
    "dataSource": "última tabela",
    "chartType": "bar",
    "xAxis": "produto",
    "yAxis": "quantidade",
    "filters": {}
  }
}

Permitir:

- troque para linha;
- filtre por mês;
- mostre como tabela;
- explique o gráfico.

---

## 48. Memória e erros

Quando houver erro, registrar:

- ação tentada;
- ferramenta usada;
- parâmetros;
- erro;
- alternativa sugerida;
- se foi resolvido.

Isso permite:

- evitar repetir a falha;
- sugerir correção;
- diagnosticar recorrência.

---

## 49. Estrutura de banco sugerida

Tabelas conceituais:

memory_items
- id
- user_id
- session_id
- scope
- type
- content
- content_json
- embedding
- source
- confidence
- priority
- ttl
- expires_at
- created_at
- updated_at
- deleted_at

conversation_sessions
- id
- user_id
- title
- active_topic
- summary
- state_json
- created_at
- updated_at

conversation_messages
- id
- session_id
- role
- content
- metadata_json
- created_at

memory_events
- id
- memory_id
- action
- reason
- created_at

user_preferences
- id
- user_id
- key
- value
- scope
- confidence
- source
- expires_at
- created_at
- updated_at

task_states
- id
- session_id
- task_type
- status
- objective
- state_json
- created_at
- updated_at

---

## 50. Tipos de memory_items

Tipos recomendados:

- preference
- entity
- decision
- correction
- summary
- task_state
- document_state
- artifact_reference
- instruction
- feedback
- fact
- warning
- error_pattern
- user_profile
- project_context

---

## 51. Escopos de memória

Escopos:

- message
- turn
- session
- task
- user
- workspace
- project
- global

Exemplos:

- session: “nesta conversa, responder em txt”
- user: “usuário prefere respostas em pt-BR”
- project: “produto se chama Minha DELPI”
- task: “playbook atual é memória e contexto”
- global: regras gerais da plataforma

---

## 52. TTL e expiração

Nem toda memória deve durar para sempre.

Sugestão:

| Tipo | TTL |
|---|---|
| entidade ativa | sessão |
| preferência temporária | sessão |
| tarefa ativa | até conclusão |
| correção do usuário | longa duração |
| decisão de projeto | longa duração |
| erro técnico pontual | curta duração |
| resumo de conversa | média duração |
| dado sensível | não persistir ou expirar rápido |

---

## 53. Escrita de memória com confirmação

Para memória persistente, quando necessário, perguntar:

Você quer que eu considere essa preferência nas próximas conversas também?

Opções:

- Sim, lembrar
- Só nesta conversa
- Não lembrar

---

## 54. Transparência

O usuário deve conseguir perguntar:

- o que você lembra sobre esta conversa?
- qual contexto você está usando?
- por que você respondeu assim?
- limpe o contexto;
- remova essa preferência;
- mostre minhas preferências.

Resposta deve ser clara:

Estou usando estes pontos de contexto:
- Você está criando playbooks para o Minha DELPI Chat IA.
- O formato preferido é txt para copiar.
- O público é outra IA que vai implementar.
- O playbook atual é sobre memória e contexto.

---

## 55. Privacidade

A memória deve respeitar:

- consentimento;
- minimização;
- segurança;
- controle do usuário;
- auditoria;
- retenção;
- exclusão;
- permissões;
- separação por usuário;
- separação por workspace.

Nunca salvar:

- senhas;
- tokens;
- chaves de API;
- dados bancários;
- segredos industriais sem política;
- informações pessoais sensíveis desnecessárias.

---

## 56. Prompt contextual recomendado

Antes de chamar o LLM, montar um bloco de contexto estruturado.

Exemplo:

[Contexto da sessão]
- Usuário está criando playbooks para melhorias do Minha DELPI Chat IA.
- Formato preferido: txt para copiar.
- Nível desejado: completo e implementável.
- Público: outra IA/desenvolvedor que implementará.

[Tarefa ativa]
- Criar playbook de memória e contexto.
- Incluir estratégias neurais e melhores práticas.

[Preferências]
- Responder em português.
- Não inventar informações.
- Ser claro e técnico.

[Entidades ativas]
- Minha DELPI Chat IA
- memória de sessão
- contexto
- RAG
- lousa
- playbooks

[Instruções]
- Produzir documento completo.
- Linguagem simples para outra IA implementar.
- Não expor dados sensíveis.

---

## 57. Contrato de contexto para o LLM

Formato sugerido:

{
  "contextPacket": {
    "sessionSummary": "...",
    "activeTask": {},
    "activeEntities": [],
    "userPreferences": [],
    "relevantMemories": [],
    "retrievedDocs": [],
    "constraints": [],
    "forbiddenAssumptions": [],
    "responseFormat": "txt"
  }
}

---

## 58. Context window budgeting

O sistema deve controlar o orçamento de tokens.

Prioridade no prompt:

1. Instruções críticas.
2. Pedido atual.
3. Estado da tarefa ativa.
4. Correções recentes.
5. Entidades ativas.
6. Preferências relevantes.
7. Trechos RAG/documentos.
8. Resumo da sessão.
9. Histórico recente.
10. Exemplos.

Não colocar histórico bruto inteiro quando resumo resolve.

---

## 59. Estratégia de recuperação híbrida

Usar três buscas combinadas:

1. Busca lexical
   - boa para códigos, nomes, siglas.

2. Busca vetorial
   - boa para significado.

3. Busca estrutural
   - boa para entidades, datas, tarefas e arquivos.

Resultado final deve passar por reranking.

---

## 60. Memória com grafo de conhecimento

Criar grafo para relações importantes.

Nós:

- usuário;
- projeto;
- app;
- plugin;
- documento;
- tarefa;
- entidade;
- preferência;
- decisão;
- arquivo;
- resposta;
- erro.

Arestas:

- usuário prefere formato;
- tarefa usa documento;
- resposta gerou lousa;
- entidade pertence a projeto;
- erro ocorreu em ação;
- decisão substitui decisão anterior.

Exemplo:

Robério → prefere → txt para copiar
Playbook SQL → relacionado a → Especialista SQL
Minha DELPI → possui → Portal
Portal → consome → /me/apps

---

## 61. Estratégia de memória multimodal

Preparar arquitetura para:

- texto;
- imagens;
- PDFs;
- planilhas;
- gráficos;
- desenhos técnicos;
- áudios futuros;
- screenshots.

Cada artefato deve ter:

- resumo textual;
- metadados;
- entidades extraídas;
- embeddings;
- links para origem;
- estado de processamento.

---

## 62. Detecção de mudança de assunto

O chat deve identificar quando o usuário muda de tema.

Sinais:

- “agora vamos...”
- “novo assunto”
- “mudando”
- “deixe isso”
- “vamos falar de...”
- mudança brusca de entidade;
- intenção totalmente diferente.

Ação:

- encerrar ou pausar tarefa anterior;
- criar novo activeTopic;
- manter histórico anterior recuperável;
- não misturar contextos.

---

## 63. Retomada de assunto anterior

Usuário pode dizer:

- volte ao playbook anterior;
- continue o SQL;
- retome o e-mail;
- volte para a ata;
- siga de onde paramos.

Ação:

- buscar task_state correspondente;
- carregar resumo;
- confirmar se houver múltiplos candidatos;
- continuar.

---

## 64. Memória de “siga” e “próximo”

O chat deve entender mensagens curtas com base no estado.

Exemplo:

Usuário:

próximo

Se havia sequência de playbooks:

- gerar próximo playbook.

Usuário:

siga

Se havia documento em partes:

- continuar próxima seção.

Se não houver contexto:

Não encontrei uma sequência ativa. Você quer que eu continue qual assunto?

---

## 65. Correções do usuário têm alta prioridade

Quando o usuário corrige o chat, registrar com alta prioridade.

Exemplo:

Usuário:

Não é DELPI Central, é Minha DELPI.

Memória:

{
  "type": "correction",
  "content": "Usar Minha DELPI como nome oficial; DELPI Central é legado.",
  "priority": "high"
}

---

## 66. Evitar “context drift”

Context drift ocorre quando o chat se afasta da tarefa.

Estratégias:

- manter objetivo ativo;
- repetir internamente restrições;
- usar checkpoints;
- perguntar antes de mudar escopo;
- resumir progresso;
- validar entendimento;
- manter task_state;
- limitar contexto irrelevante.

---

## 67. Evitar “context poisoning”

Context poisoning ocorre quando conteúdo errado entra na memória.

Estratégias:

- validar fonte;
- diferenciar usuário, assistente e documento;
- não salvar suposições como fatos;
- marcar confiança;
- permitir correção;
- detectar contradição;
- expirar memórias incertas;
- não salvar resposta gerada como fato sem confirmação.

---

## 68. Níveis de confiança

Cada memória deve ter confidence.

Níveis:

- high: dito explicitamente pelo usuário ou fonte oficial.
- medium: inferido com boa evidência.
- low: hipótese ou contexto fraco.

Uso:

- high pode orientar respostas.
- medium pode ajudar, mas com cautela.
- low não deve gerar certeza.

---

## 69. Separar fato, preferência e inferência

Memórias devem ter tipo claro.

Fato:

Usuário trabalha no projeto Minha DELPI.

Preferência:

Usuário prefere playbooks em txt para copiar.

Inferência:

Usuário provavelmente quer respostas detalhadas para playbooks.

Nunca misturar inferência com fato.

---

## 70. Memória de fontes

Quando uma resposta usa documentação, salvar referência.

Exemplo:

{
  "sourceMemory": {
    "source": "docs/01-arquitetura/arquitetura-geral.md",
    "usedFor": "separação entre Core API e API DELPI",
    "confidence": "high"
  }
}

---

## 71. Governança no contexto da Minha DELPI

Implementar a memória respeitando a arquitetura da plataforma.

Sugestão de responsabilidades:

Portal:
- exibir contexto ativo;
- permitir limpar contexto;
- exibir preferências;
- acionar botões;
- mostrar memória usada.

Core API:
- autenticação/autorização;
- governança de permissões;
- controle de acesso à memória;
- auditoria;
- políticas de retenção.

API DELPI ou serviço IA:
- execução das funções de memória;
- embeddings;
- recuperação;
- ranking;
- sumarização;
- resposta.

Banco:
- armazenar sessões;
- memórias;
- embeddings;
- tarefas;
- feedback.

---

## 72. API interna sugerida

Endpoints conceituais:

GET /ai/context/session/{sessionId}
POST /ai/context/update
POST /ai/memory/write
POST /ai/memory/search
DELETE /ai/memory/{memoryId}
POST /ai/memory/forget
GET /ai/preferences
POST /ai/preferences
POST /ai/context/clear
GET /ai/context/active
POST /ai/context/resolve-reference

---

## 73. Permissões sugeridas

Permissões:

- ai.chat.access
- ai.memory.view
- ai.memory.manage
- ai.memory.delete
- ai.memory.admin
- ai.context.debug
- ai.feedback.view
- ai.feedback.manage

---

## 74. Eventos em tempo real

A arquitetura da Minha DELPI já usa eventos e Socket.IO para atualizar o Portal após mudanças. A memória pode usar padrão semelhante.

Eventos sugeridos:

- ai.context.updated
- ai.memory.created
- ai.memory.deleted
- ai.preference.updated
- ai.task.updated
- ai.context.cleared

Regra:

Persistir primeiro. Publicar evento depois.

---

## 75. Observabilidade

Registrar:

- memórias recuperadas;
- memórias usadas;
- score de relevância;
- fonte;
- tipo;
- tamanho do contexto;
- tempo de recuperação;
- decisão de escrita;
- decisão de descarte;
- resolução de referência;
- preferência aplicada;
- erro de contexto;
- feedback do usuário.

---

## 76. Debug para administradores

Exibir apenas para usuários autorizados:

{
  "contextDebug": {
    "activeTopic": "memória e contexto",
    "intent": "create_playbook",
    "memoriesRetrieved": 8,
    "memoriesUsed": 4,
    "referenceResolution": [],
    "preferencesApplied": [
      "format=txt"
    ],
    "tokenBudget": {
      "used": 6200,
      "max": 16000
    }
  }
}

---

## 77. Métricas principais

Medir:

- taxa de resolução de referência;
- taxa de contexto mantido;
- taxa de correção de contexto pelo usuário;
- quantidade de memórias criadas;
- quantidade de memórias usadas;
- memórias ignoradas;
- feedback “perdeu contexto”;
- feedback “usou contexto errado”;
- tempo de recuperação;
- precisão de intenção;
- taxa de tarefas retomadas;
- uso de “limpar contexto”;
- uso de preferências;
- redução de perguntas repetidas.

---

## 78. Feedback específico

Adicionar motivos:

- perdeu contexto;
- usou contexto errado;
- não lembrou preferência;
- lembrou coisa que não devia;
- perguntou algo que já informei;
- confundiu arquivo;
- confundiu produto;
- confundiu resposta anterior;
- ignorou instrução;
- misturou assuntos;
- não retomou tarefa;
- memória desatualizada.

---

## 79. Testes de regressão

Criar:

test_memory_context.py

Casos mínimos:

| Caso | Entrada | Esperado |
|---|---|---|
| M1 | “produto 1001”; depois “ver fornecedores” | usa produto 1001 |
| M2 | “corrija sem explicar”; próxima correção | só versão final |
| M3 | “próximo” em sequência de playbooks | gera próximo item |
| M4 | “isso” após tabela | refere-se à tabela |
| M5 | “isso” ambíguo | pergunta |
| M6 | usuário corrige contexto | atualiza estado |
| M7 | muda de assunto | cria novo activeTopic |
| M8 | volta ao assunto anterior | recupera task_state |
| M9 | preferência temporária | expira ao fim da sessão |
| M10 | memória contraditória | prioriza correção recente |
| M11 | anexar arquivo e pedir resumo depois | lembra arquivo ativo |
| M12 | consulta SQL e “adicione coluna” | edita query anterior |
| M13 | lousa ativa e “corrija” | corrige lousa |
| M14 | dado sensível | não grava memória |
| M15 | limpar contexto | remove active state |

---

## 80. Testes de qualidade neural

Criar avaliação com datasets internos.

Cenários:

- conversa longa com mudança de assunto;
- tarefa em 20 turnos;
- vários arquivos anexados;
- múltiplas entidades parecidas;
- preferências conflitantes;
- instruções temporárias;
- retomada após pausa;
- referência ambígua;
- erro corrigido pelo usuário;
- contexto obsoleto.

Métricas:

- precisão de referência;
- precisão de entidade ativa;
- acerto de intenção;
- relevância da memória recuperada;
- taxa de alucinação por contexto;
- número de perguntas desnecessárias;
- satisfação do usuário.

---

## 81. Roadmap de implementação

**Fase 1 entregue (03/06/2026):** `ChatConversationStateService` + integração em `ChatConversationMemoryService` (equivalente a ConversationStateManager do §9).

### Fase 1 — Estado de sessão

- Criar ConversationStateManager.
- Armazenar activeTopic.
- Armazenar activeTask.
- Armazenar última resposta útil.
- Resolver “siga” e “próximo”.

### Fase 2 — Entidades e referências

- Criar EntityTracker.
- Criar ReferenceResolutionService.
- Resolver “isso”, “esse produto”, “a tabela”.
- Perguntar quando ambíguo.

### Fase 3 — Preferências de sessão

- Criar UserPreferenceManager.
- Detectar preferências.
- Aplicar preferências.
- Permitir limpar preferências.

### Fase 4 — Resumos e compressão

- Criar ConversationSummarizer.
- Criar ContextCompressionService.
- Resumir conversas longas.
- Manter decisões e pendências.

### Fase 5 — Memória semântica

- Criar embeddings.
- Criar busca vetorial.
- Criar busca híbrida.
- Criar reranker.
- Integrar com documentação e playbooks.

### Fase 6 — Memória episódica

- Salvar episódios relevantes.
- Recuperar tarefas anteriores.
- Retomar conversas.
- Permitir exclusão.

### Fase 7 — Contexto avançado

- Grafo de conhecimento.
- Detecção de contradição.
- Gating de escrita.
- Learned forgetting.
- Debug de contexto.

### Fase 8 — UX de memória

- Barra de contexto.
- Ver memória usada.
- Limpar contexto.
- Editar preferência.
- Fixar contexto.

### Fase 9 — Métricas e feedback

- Dashboard de memória.
- Testes de regressão.
- Feedback específico.
- Alertas de perda de contexto.

---

## 82. Anti-padrões

Evitar:

1. Salvar tudo como memória.
2. Usar histórico antigo sem relevância.
3. Usar memória de outro usuário.
4. Ignorar pedido atual por causa de memória antiga.
5. Não perguntar quando “isso” é ambíguo.
6. Tratar inferência como fato.
7. Salvar dado sensível.
8. Esquecer correção do usuário.
9. Repetir pergunta já respondida.
10. Misturar tarefas diferentes.
11. Encher o prompt com contexto irrelevante.
12. Usar RAG como memória conversacional.
13. Usar memória como autorização.
14. Não permitir apagar memória.
15. Não explicar qual contexto foi usado.

---

## 83. Prompt interno recomendado

Você é o módulo de memória e contexto do Minha DELPI Chat IA.

Antes de responder, faça:

1. Identifique a intenção da mensagem atual.
2. Verifique se há tarefa ativa.
3. Recupere entidades relevantes.
4. Resolva referências como “isso”, “esse”, “anterior”.
5. Aplique preferências de sessão.
6. Recupere memórias relevantes.
7. Ignore contexto irrelevante ou obsoleto.
8. Se houver ambiguidade crítica, pergunte.
9. Responda respeitando o contexto ativo.
10. Após responder, atualize o estado da sessão.
11. Salve apenas memórias úteis, seguras e justificadas.
12. Se o usuário corrigir algo, priorize a correção.

Nunca:
- invente memória;
- use memória como fato sem confiança;
- exponha memória sensível;
- misture contexto de usuários;
- ignore o pedido atual.

---

## 84. Exemplo de funcionamento ideal

Usuário:

Vamos criar um playbook de SQL avançado. Quero que seja genérico, sem TOTVS.

Chat:

Cria playbook SQL genérico.

Memória de sessão:

{
  "activeTask": "playbook_sql",
  "constraints": ["genérico", "sem TOTVS"],
  "format": "txt para copiar"
}

Usuário:

Agora faça um de memória e contexto.

Chat:

Entende que é novo playbook, mantém formato e nível de detalhe.

Usuário:

Use a mesma linguagem.

Chat:

Recupera padrão anterior: linguagem implementável por outra IA.

---

## 85. Resultado esperado

Depois da implementação, o chat deve:

- manter continuidade natural;
- entender mensagens curtas;
- lembrar preferências da sessão;
- resolver referências;
- retomar tarefas;
- reduzir perguntas repetidas;
- evitar perda de contexto;
- sugerir ações relevantes;
- usar memória com segurança;
- permitir controle pelo usuário;
- melhorar assertividade;
- parecer mais inteligente, útil e confiável.

---

## 86. Resumo executivo

A memória do chat não deve ser apenas histórico salvo.

Ela deve ser uma camada inteligente de contexto.

Essa camada deve:

- ler;
- selecionar;
- resumir;
- recuperar;
- ranquear;
- aplicar;
- atualizar;
- esquecer.

Regra final:

O chat deve lembrar o que é útil, esquecer o que atrapalha, perguntar quando houver dúvida e sempre respeitar o contexto atual do usuário.