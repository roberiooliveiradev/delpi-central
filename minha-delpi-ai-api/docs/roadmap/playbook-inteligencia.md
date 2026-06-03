# Playbook Final — Tornar o Minha DELPI Chat Mais Inteligente

Projeto: Minha DELPI Chat IA
Escopo: chat comum, agentes, roteamento de intenção, memória, small talk, identidade, tarefas textuais, SQL, anexos, lousa, pesquisa web, gráficos, feedback, métricas e UX.

---

## 1. Objetivo

Tornar o Minha DELPI Chat mais inteligente, natural, rápido e confiável.

O chat deve entender melhor o usuário, responder perguntas simples sem exagero, escolher ferramentas corretamente, lembrar contexto, trabalhar textos como um assistente administrativo, consultar dados quando necessário, explicar resultados, lidar com erros e evoluir com feedback.

O objetivo não é apenas adicionar mais funcionalidades.

O objetivo é criar uma experiência em que o chat:

- entende perguntas simples;
- entende erros de digitação;
- sabe quando responder direto;
- sabe quando usar ferramentas;
- sabe quando não usar ferramentas;
- lembra o contexto da conversa;
- respeita preferências do usuário;
- ajuda com textos, e-mails, atas e documentos;
- consulta dados com assertividade;
- interpreta resultados;
- sugere próximos passos úteis;
- explica quando não entendeu;
- melhora com métricas e feedback.

---

## 2. Princípio central

Inteligência no chat = entender intenção + contexto + ferramenta correta + resposta clara.

Regra principal:

Para pergunta simples, resposta simples.
Para tarefa textual, resposta textual.
Para consulta operacional, ferramenta/API.
Para documento, leitura/análise de arquivo.
Para dúvida sobre o próprio chat, autoajuda.
Para contexto ambíguo, perguntar.
Para pedido não entendido, dizer que não entendeu.

---

## 3. Problema atual observado

Na tela analisada, o usuário perguntou:

"como vc s chama?"

O chat iniciou etapas como:

- contexto da sessão carregado;
- histórico pronto;
- pensando intenção e rota OpenAPI;
- planejando ferramentas adicionais.

Isso é incorreto para uma pergunta simples de identidade.

Resposta esperada:

"Eu sou o Minha DELPI Chat."

Sem OpenAPI.
Sem RAG.
Sem diagnóstico visível.
Sem planejamento de ferramentas.
Sem delay desnecessário.

---

## 4. Causa provável no projeto atual

O projeto já possui serviços para small talk, identidade, utilidades e roteamento, mas eles entram tarde demais no fluxo.

O `ChatTurnPreparationService` prepara histórico, emite atividades, avalia rota OpenAPI e só depois resolve algumas respostas diretas.

Isso cria uma experiência artificial para perguntas simples.

Correção central:

Criar um gate inicial de pergunta simples antes de qualquer atividade, ferramenta, RAG ou LLM.

---

## 5. Arquitetura final proposta

Criar ou consolidar uma camada chamada:

ChatIntelligenceCore

Com submódulos:

- ChatSimpleTurnGateService
- ChatIntentRouterService
- ChatMessageNormalizationService
- ChatConversationMemoryService
- ChatReferenceResolutionService
- ChatAssistantIdentityService
- ChatSmallTalkService
- ChatCapabilitiesService
- ChatTextTaskService
- ChatSqlSpecialistService
- ChatAttachmentUnderstandingService
- ChatCanvasCoordinatorService
- ChatWebResearchService
- ChatPresentationDecisionService
- ChatErrorRecoveryService
- ChatFeedbackLearningService
- ChatMetricsService

---

## 6. Novo fluxo inteligente do turno

Fluxo recomendado:

Mensagem do usuário
→ normalização
→ gate simples
→ roteamento de intenção
→ memória/contexto
→ decisão de ferramenta
→ execução, se necessário
→ resposta direta ou LLM
→ apresentação rica
→ sugestões de próximos passos
→ feedback/métricas
→ atualização de memória

O ponto mais importante:

O gate simples deve acontecer antes de qualquer streaming técnico.

---

## 7. Gate simples obrigatório

Criar:

ChatSimpleTurnGateService

Responsabilidade:

Resolver imediatamente:

- saudação;
- agradecimento;
- despedida;
- bem-estar;
- nome do assistente;
- quem é você;
- o que você faz;
- o que você pode fazer;
- ajuda inicial;
- hora/data;
- não entendi;
- mensagens ambíguas simples.

Entrada:

{
  "message": "como vc s chama?",
  "workspaceContext": {},
  "previousMessages": []
}

Saída:

{
  "matched": true,
  "intent": "assistant_identity",
  "subIntent": "name",
  "answer": "Eu sou o Minha DELPI Chat.",
  "requiresTool": false,
  "requiresRag": false,
  "requiresLlm": false,
  "hideActivity": true
}

---

## 8. Regras do gate simples

O gate simples deve:

1. Normalizar a mensagem.
2. Corrigir typos comuns.
3. Verificar se é pergunta simples.
4. Responder direto.
5. Encerrar o turno.
6. Registrar metadata.
7. Não emitir etapas técnicas.

Não deve ativar se a mensagem contiver:

- produto;
- estoque;
- fornecedor;
- cliente;
- pedido;
- venda;
- compra;
- SQL;
- anexo;
- PDF;
- desenho;
- gráfico;
- tabela;
- lousa;
- web;
- consultar;
- listar;
- buscar;
- mostrar.

---

## 9. Normalização avançada

Melhorar `ChatMessageNormalizationService`.

Adicionar correções:

- "oq" → "o que"
- "q" → "que", apenas em perguntas curtas
- "vc" → "voce"
- "cmo" → "como"
- "cm" → "como"
- "qual eh" → "qual e"
- "seu nom" → "seu nome"
- "como vc s chama" → "como voce se chama"
- "como voce s chama" → "como voce se chama"
- "vc s chama" → "voce se chama"
- "qm e vc" → "quem e voce"
- "qm é vc" → "quem e voce"
- "oq vc faz" → "o que voce faz"
- "oq vc pode fazer" → "o que voce pode fazer"
- "naum entendi" → "nao entendi"
- "num entendi" → "nao entendi"

Regra:

Não transformar "s" em "se" globalmente.
Fazer apenas por padrões contextuais.

---

## 10. Mapa mínimo de interações simples

### Identidade

"como vc s chama?"
→ "Eu sou o Minha DELPI Chat."

"qual seu nome?"
→ "Eu sou o Minha DELPI Chat."

"quem é você?"
→ "Sou o Minha DELPI Chat, assistente inteligente da plataforma Minha DELPI."

"vc é quem?"
→ "Sou o Minha DELPI Chat."

---

### Saudação

"ola"
→ "Olá! Sou o Minha DELPI Chat. Como posso ajudar hoje?"

"oi"
→ "Oi! Me diga o que você precisa."

"bom dia"
→ "Bom dia! Como posso ajudar?"

"boa tarde"
→ "Boa tarde! O que você precisa hoje?"

---

### Capacidades

"o que você pode fazer?"
→ "Posso ajudar com consultas, textos, documentos, gráficos, SQL, pesquisa web, lousa e dúvidas sobre a Minha DELPI."

"oq vc faz?"
→ "Ajudo com consultas, escrita, revisão de textos, documentos, análises e dúvidas da plataforma."

"como uso esse chat?"
→ "Pergunte do seu jeito. Você pode pedir consultas, textos, análise de arquivos, gráficos ou ajuda sobre a plataforma."

---

### Agradecimento

"obg"
→ "Por nada! Quando precisar, é só chamar."

"vlw"
→ "Valeu! Fico à disposição."

"obrigado"
→ "Por nada! Posso ajudar com mais alguma coisa."

---

### Não entendimento

"faz isso"
sem contexto
→ "Não entendi exatamente o que você quer que eu faça. Você quer corrigir texto, fazer consulta, analisar arquivo ou colocar algo na lousa?"

"arruma"
sem texto
→ "Não entendi o que devo arrumar. Envie o texto, arquivo ou explique o ajuste desejado."

"isso"
sem referente
→ "Não consegui identificar a que 'isso' se refere. Você quer usar a última resposta, uma tabela, um arquivo ou outro item?"

---

## 11. Fallback honesto

Quando não entender, o chat deve dizer que não entendeu.

Resposta padrão:

"Não entendi exatamente o seu pedido. Pode reformular com o que você quer fazer?"

Versão com opções:

"Não entendi exatamente o seu pedido. Posso ajudar com:
- responder uma dúvida simples;
- corrigir ou escrever um texto;
- fazer uma consulta;
- analisar um arquivo;
- gerar tabela, gráfico ou lousa.

Como você quer seguir?"

Regra:

Não inventar intenção.
Não chamar ferramenta para tentar adivinhar.
Não responder genericamente fingindo que entendeu.

---

## 12. Roteamento inteligente de intenção

Após o gate simples, usar o roteador.

Ordem:

1. Segurança.
2. Resposta a pendência ativa.
3. Gate simples.
4. Tarefa textual.
5. Lousa.
6. Follow-up com memória.
7. Consulta operacional.
8. SQL.
9. Anexo/documento.
10. Desenho técnico.
11. Pesquisa web.
12. RAG/documentação.
13. Fallback de não entendimento.

---

## 13. Regras de uso de ferramentas

### Não usar ferramentas

- saudação;
- identidade;
- agradecimento;
- pergunta sobre capacidades;
- correção textual simples;
- e-mail sem dados operacionais;
- explicação simples;
- ELI5 sem fonte externa;
- fallback de não entendimento.

### Usar ferramentas

- consulta real;
- dados operacionais;
- produto/estoque/fornecedor/venda/compra;
- SQL executado;
- anexo;
- desenho técnico;
- web explícita;
- RAG documental;
- gráfico a partir de dados.

---

## 14. Memória e contexto

Criar memória operacional de sessão com:

- entidade ativa;
- última resposta útil;
- última tabela;
- último gráfico;
- último arquivo;
- última consulta SQL;
- última lousa;
- preferências do usuário;
- tarefa ativa;
- agente ativo;
- filtros usados.

Exemplos:

"qual o estoque do produto 10080001?"
→ salva productCode = 10080001

"e os fornecedores?"
→ usa productCode = 10080001

"coloque isso na lousa"
→ usa última resposta útil

"deixe mais formal"
→ usa último texto gerado

---

## 15. Resolução de referências

Criar regras para:

- isso;
- esse produto;
- essa tabela;
- esse gráfico;
- esse arquivo;
- a resposta anterior;
- a consulta anterior;
- o último e-mail;
- a lousa;
- faça igual;
- próximo;
- siga.

Se houver ambiguidade:

"Não tenho certeza se você se refere à última resposta, à tabela ou ao arquivo. Qual deles devo usar?"

---

## 16. Preferências de sessão

O chat deve entender e respeitar:

- "responda curto";
- "sempre em txt";
- "sempre em tabela";
- "corrija sem explicar";
- "mostre antes e depois";
- "use tom formal";
- "não use ferramentas sem eu pedir";
- "daqui pra frente seja mais direto".

Salvar como:

{
  "scope": "session",
  "preference": "answer_style",
  "value": "short"
}

Permitir limpar:

- "limpe o contexto";
- "esqueça essa preferência";
- "volte ao normal";
- "começar do zero".

---

## 17. Tarefas textuais como habilidade nativa

O chat deve ser excelente em texto:

- correção;
- reescrita;
- e-mail;
- carta;
- ata;
- comunicado;
- relatório;
- documentação;
- resumo;
- tradução;
- checklist;
- plano de ação;
- ELI5;
- explicação técnica.

Regra:

Texto puro não chama API operacional.

Exemplo:

"corrija: o estoque esta baixo"
→ "O estoque está baixo."

Não consultar estoque.

---

## 18. Especialista SQL

O chat deve evoluir para especialista SQL genérico, não preso a um ERP específico.

Capacidades:

- gerar SQL;
- explicar SQL;
- revisar SQL;
- otimizar SQL;
- adaptar dialeto;
- validar schema;
- construir joins;
- CTEs;
- window functions;
- rankings;
- comparação entre períodos;
- deduplicação;
- análise de resultado;
- edição incremental.

Regra:

SQL de escrita é bloqueado por padrão.

Permitir:

- SELECT;
- WITH;
- EXPLAIN se seguro;
- CTEs;
- funções analíticas.

Bloquear:

- UPDATE;
- DELETE;
- INSERT;
- DROP;
- ALTER;
- TRUNCATE;
- EXEC;
- comandos administrativos.

---

## 19. Interpretação de resultados

Quando o chat trouxer dados, não deve apenas mostrar tabela.

Deve incluir:

- resumo;
- principais achados;
- limitações;
- alertas;
- próximos passos.

Exemplo:

"Consulta executada com sucesso.

Resumo:
- 10 registros retornados.
- Maior valor concentrado no item X.
- Resultado limitado ao TOP 10.

Próximos passos:
- gerar gráfico;
- adicionar coluna;
- exportar;
- colocar na lousa."

---

## 20. Anexos e documentos

Ao anexar arquivo:

Responder:

"Arquivo recebido. Posso resumir, corrigir, traduzir, extrair pendências, criar checklist, ata ou relatório."

Ações:

- resumir;
- corrigir;
- traduzir;
- extrair pendências;
- criar ata;
- criar checklist;
- criar relatório;
- comparar documentos;
- colocar na lousa.

Se não conseguir ler:

"Não consegui ler o arquivo com segurança. Você pode reenviar em outro formato ou colar o trecho que deseja analisar."

---

## 21. Lousa como área de trabalho

O chat deve usar lousa para:

- e-mails;
- atas;
- relatórios;
- comunicados;
- documentação;
- checklist;
- plano de ação;
- análise de arquivo;
- resultado de consulta.

Comandos:

- coloque isso na lousa;
- atualize a lousa;
- corrija a lousa;
- transforme em checklist;
- transforme em relatório;
- adicione essa tabela;
- gere versão curta;
- exporte.

---

## 22. Pesquisa web confiável

Usar web quando:

- usuário pedir explicitamente;
- informação for externa;
- informação for recente;
- pedir fonte oficial;
- pedir datasheet público;
- pedir notícia;
- pedir comparação externa.

Não usar web:

- para dado interno;
- para correção textual;
- para pergunta simples;
- sem necessidade.

Resposta deve incluir:

- resumo;
- fontes;
- limitações;
- confiança;
- próximos passos.

---

## 23. Apresentação rica

Escolher formato automaticamente:

| Situação | Formato |
|---|---|
| explicação simples | texto |
| lista | tabela |
| ranking | barra horizontal |
| período | linha |
| participação | rosca |
| indicador único | KPI |
| hierarquia | árvore |
| pendências | checklist |
| documento longo | lousa |

Sempre oferecer:

- ver tabela;
- gerar gráfico;
- explicar;
- exportar;
- colocar na lousa.

---

## 24. UX de streaming

Modo Normal:

- não mostrar etapas técnicas;
- não mostrar OpenAPI;
- não mostrar RAG;
- não mostrar "planejando ferramentas";
- mostrar apenas resposta;
- se demorar, mostrar "pensando..." discreto.

Modo Diagnóstico/Admin:

- mostrar etapas;
- intenção;
- tools;
- RAG;
- timings;
- memory snapshot;
- roteamento.

Regra:

Usuário comum não deve ver debug como resposta.

---

## 25. Botões iniciais inteligentes

No chat comum, starters devem ser amplos:

1. O que você pode fazer?
2. Corrigir texto
3. Escrever e-mail
4. Consultar dados
5. Analisar documento
6. Pesquisar na web

Em agente operacional:

1. O que você pode fazer?
2. Consultar produto
3. Ver estoque
4. Buscar fornecedor
5. Corrigir texto
6. Analisar documento

Evitar abrir sempre com "Ver estoque".

---

## 26. Botões pós-resposta

Após saudação:

- O que você pode fazer?
- Corrigir texto
- Escrever e-mail
- Consultar dados
- Analisar arquivo

Após texto:

- Deixar mais formal
- Deixar mais curto
- Mostrar alterações
- Colocar na lousa

Após consulta:

- Gerar gráfico
- Ver detalhes
- Exportar
- Colocar na lousa

Após erro:

- Tentar novamente
- Verificar filtro
- Ampliar busca
- Pedir ajuda

---

## 27. Erros e resultados vazios

Nunca responder só:

"Não encontrei."

Responder:

"Não encontrei dados para esse filtro.

Possíveis motivos:
- filtro restrito;
- código incorreto;
- período sem movimento;
- falta de permissão;
- fonte indisponível.

Posso tentar:
- ampliar período;
- remover filtro;
- buscar por descrição;
- tentar novamente."

---

## 28. Quando não entender

Implementar `ChatUnclearRequestService`.

Regras:

Se confidence < 0.60:

"Não entendi exatamente o seu pedido. Pode reformular?"

Se 0.60 <= confidence < 0.86:

"Entendi mais de uma possibilidade. Você quer [A] ou [B]?"

Exemplo:

"faz isso"

Sem contexto:

"Não entendi o que você quer que eu faça. Você quer corrigir texto, fazer consulta, analisar arquivo ou colocar algo na lousa?"

---

## 29. Metadata obrigatória por resposta

Cada resposta deve registrar:

{
  "intentRouting": {
    "intent": "...",
    "subIntent": "...",
    "confidence": 0.0,
    "requiresTool": false,
    "requiresRag": false,
    "requiresLlm": false,
    "decision": "...",
    "reason": "..."
  },
  "contextSnapshot": {
    "activeTopic": "...",
    "activeEntities": {},
    "memoryUsed": true
  },
  "responseQuality": {
    "directAnswer": true,
    "fallback": false,
    "toolSkipped": true
  }
}

---

## 30. Métricas de inteligência

Medir:

- perguntas simples respondidas direto;
- tempo médio de perguntas simples;
- tools evitadas;
- RAG evitado;
- LLM evitado;
- erros de intenção;
- fallback de não entendimento;
- contexto reutilizado;
- contexto errado;
- feedback negativo;
- clique em botões;
- uso de lousa;
- uso de anexos;
- tarefas textuais;
- consultas operacionais;
- recuperação após erro.

---

## 31. Feedback específico

Adicionar motivos:

- não entendeu pergunta simples;
- chamou ferramenta sem necessidade;
- demorou demais;
- perdeu contexto;
- usou contexto errado;
- não respeitou preferência;
- texto ficou ruim;
- consulta errada;
- resultado sem explicação;
- não disse que não entendeu;
- botões não ajudaram;
- mostrou diagnóstico técnico.

---

## 32. Testes obrigatórios

### Testes de pergunta simples

- ola
- bo dia
- como vc s chama
- qual seu nom
- qm e vc
- oq vc faz
- oq vc pode fazer
- obg
- vlw
- tchau
- q horas sao
- q dia e hoje

Esperado:

- resposta direta;
- sem tool;
- sem RAG;
- sem LLM pesado quando possível;
- sem activity técnica.

---

### Testes de não entendimento

- faz isso sem contexto
- arruma sem texto
- manda sem objeto
- aquilo sem referente
- tira isso sem contexto

Esperado:

- dizer que não entendeu;
- pedir esclarecimento;
- sugerir opções.

---

### Testes de roteamento

- estoque do produto 10080001 → ferramenta
- corrija: estoque esta baixo → texto, sem ferramenta
- pesquise na web sobre X → web
- coloque isso na lousa → canvas
- resuma esse PDF → anexo
- gere SQL → SQL
- o que você pode fazer → capacidades, sem ferramenta

---

### Testes de contexto

- produto 1001 → e fornecedores
- e as vendas?
- coloque isso na lousa
- deixe mais formal
- próximo
- siga
- limpe o contexto

---

## 33. Roadmap final de implementação

### Fase 1 — Correções imediatas

- Normalizar "como vc s chama".
- Adicionar padrões faltantes em identity.json.
- Trocar textos de saudação operacionais.
- Ocultar etapas técnicas no modo normal.
- Reordenar starters iniciais.

### Fase 2 — Gate simples

- Criar ChatSimpleTurnGateService.
- Rodar antes de on_stream_activity.
- Short-circuit para identidade, small talk, utilidades e capacidades.
- Registrar metadata correta.

### Fase 3 — Fallback inteligente

- Criar ChatUnclearRequestService.
- Adicionar respostas "não entendi".
- Adicionar botões de esclarecimento.
- Implementar thresholds de confiança.

### Fase 4 — Memória e contexto

- Consolidar ChatConversationMemoryService.
- Resolver referências.
- Guardar preferências.
- Criar barra de contexto.
- Permitir limpar/editar contexto.

### Fase 5 — Texto e documentos

- Expandir TextAssistantService.
- Melhorar e-mail, ata, carta, relatório e documentação.
- Integrar com lousa e anexos.

### Fase 6 — SQL e dados

- Evoluir especialista SQL genérico.
- Interpretar resultados.
- Permitir edição incremental.
- Gerar gráficos e relatórios.

### Fase 7 — Interatividade

- Botões contextuais.
- Menus por tabela/gráfico.
- Guided flows.
- Painel de ajuda.

### Fase 8 — Métricas e melhoria contínua

- Feedback estruturado.
- Dashboard de qualidade.
- Testes de regressão.
- Alertas de intenção errada.
- Relatório semanal.

---

## 34. Critérios finais de aceite

O chat será considerado mais inteligente quando:

1. Responder "como vc s chama?" corretamente.
2. Não mostrar pipeline técnico em perguntas simples.
3. Não chamar ferramenta sem necessidade.
4. Entender typos comuns.
5. Dizer que não entendeu quando não entender.
6. Manter contexto entre perguntas.
7. Respeitar preferências da sessão.
8. Ser excelente em textos.
9. Consultar dados só quando necessário.
10. Interpretar resultados, não apenas mostrar tabelas.
11. Sugerir próximos passos úteis.
12. Melhorar com feedback.

---

## 35. Resultado esperado

O Minha DELPI Chat deixará de parecer um formulário de consulta e passará a parecer um assistente inteligente.

Ele deve conversar bem, entender o contexto, responder rápido ao básico, usar ferramentas com precisão e ajudar o usuário a concluir tarefas reais.

Regra final:

O chat mais inteligente não é o que usa mais ferramentas.
É o que usa a ferramenta certa, na hora certa, e responde simples quando a pergunta é simples.