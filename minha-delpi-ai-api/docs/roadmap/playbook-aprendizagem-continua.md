# Playbook — Aprendizagem Contínua do Minha DELPI Chat IA

Projeto: Minha DELPI Chat IA
Escopo: memória, vocabulário, significados, feedback, pesquisa web, RAG, fine-tuning offline, adaptação por uso e inteligência progressiva.

---

## 1. Objetivo

Criar uma arquitetura para que o Minha DELPI Chat fique mais inteligente quanto mais for usado.

O chat deve aprender com:

- perguntas dos usuários;
- correções feitas pelo usuário;
- feedback positivo e negativo;
- termos novos;
- gírias e abreviações;
- nomes internos;
- conceitos técnicos;
- documentos da plataforma;
- pesquisas web autorizadas;
- resultados de consultas;
- erros recorrentes;
- padrões de uso;
- preferências de resposta;
- interações com lousa, anexos e gráficos.

O objetivo não é alterar os pesos do modelo a cada mensagem.

O objetivo é construir uma camada de aprendizado contínuo ao redor do LLM.

---

## 2. Princípio central

O chat deve aprender sem se contaminar.

Regra principal:

Aprender = observar + validar + armazenar + recuperar + testar + melhorar.

Não é:

- gravar tudo;
- confiar cegamente no usuário;
- treinar o modelo em tempo real sem validação;
- salvar dados sensíveis;
- transformar erro em conhecimento;
- pesquisar qualquer coisa na internet e assumir como verdade.

---

## 3. Modelo mental correto

Existem dois tipos de inteligência:

### 3.1 Inteligência paramétrica

É o conhecimento dentro dos pesos do modelo.

Exemplo:

- gramática;
- raciocínio geral;
- conhecimento amplo;
- capacidade de escrever;
- capacidade de resumir.

Esse conhecimento não deve ser alterado a cada conversa.

---

### 3.2 Inteligência não paramétrica

É o conhecimento externo ao modelo.

Exemplo:

- memória do usuário;
- glossário;
- documentos;
- banco vetorial;
- histórico;
- preferências;
- feedback;
- exemplos validados;
- fontes web;
- regras de projeto;
- playbooks.

Esse é o melhor lugar para implementar aprendizagem contínua.

RAG segue exatamente essa ideia: combinar o modelo com uma memória externa recuperável e atualizável, em vez de depender apenas do conhecimento armazenado nos pesos do modelo. O artigo original de RAG propôs combinar memória paramétrica do modelo com memória não paramétrica recuperada por índice denso, e pesquisas posteriores destacam RAG como forma de reduzir alucinação, aumentar rastreabilidade e atualizar conhecimento continuamente. :contentReference[oaicite:3]{index=3} :contentReference[oaicite:4]{index=4}

---

## 4. Arquitetura recomendada

Criar uma camada chamada:

ContinuousLearningLayer

Com os seguintes serviços:

- ChatLearningEventService
- ChatUserFeedbackLearningService
- ChatVocabularyLearningService
- ChatMeaningDiscoveryService
- ChatWebMeaningResearchService
- ChatMemoryConsolidationService
- ChatKnowledgeCandidateService
- ChatKnowledgeValidationService
- ChatKnowledgePromotionService
- ChatAdaptivePromptService
- ChatPersonalizationService
- ChatEvaluationDatasetService
- ChatFineTuningDatasetService
- ChatLearningGovernanceService
- ChatLearningMetricsService

---

## 5. Fluxo geral de aprendizagem

Fluxo:

Usuário interage
→ sistema registra evento de aprendizado
→ extrai intenção, termos, entidades e feedback
→ cria candidato de conhecimento
→ valida confiança
→ busca significado em fontes internas ou web, se permitido
→ salva em memória temporária
→ consolida conhecimento
→ promove para glossário/RAG/prompt/skill se aprovado
→ testa regressão
→ passa a recuperar nas próximas respostas

---

## 6. O que o chat pode aprender

### 6.1 Palavras novas

Exemplos:

- abreviações internas;
- nomes de processos;
- apelidos de produtos;
- siglas;
- termos de engenharia;
- nomes de relatórios;
- nomes de módulos;
- nomes de documentos.

Exemplo:

Usuário:
"Quando eu falar TRANSFORMA, estou falando do módulo de engenharia."

Aprendizado:

{
  "type": "vocabulary",
  "term": "TRANSFORMA",
  "meaning": "módulo de engenharia",
  "scope": "project",
  "confidence": "high",
  "source": "user_explicit_definition"
}

---

### 6.2 Preferências do usuário

Exemplos:

- responder curto;
- sempre em txt;
- usar tom formal;
- não explicar correções;
- mostrar antes/depois;
- sempre sugerir próximos passos.

---

### 6.3 Correções

Exemplo:

Usuário:
"Não, você entendeu errado. Eu estava falando do chat comum, não do agente de produtos."

Memória:

{
  "type": "correction",
  "content": "Neste contexto, 'chat' refere-se ao chat comum, não ao agente de produtos.",
  "priority": "high"
}

---

### 6.4 Padrões de erro

Exemplo:

Usuários digitam com frequência:

"como vc s chama?"

O sistema aprende que isso significa:

"como você se chama?"

Esse aprendizado deve virar regra de normalização.

---

### 6.5 Conhecimento validado

Exemplo:

- documentação oficial;
- playbooks aprovados;
- respostas corrigidas;
- glossário validado;
- fontes web oficiais;
- decisões de projeto.

---

### 6.6 Formatos preferidos

Exemplo:

Usuário sempre pede:

- playbook em txt;
- roadmap em fases;
- tabela comparativa;
- resposta objetiva;
- exemplos práticos.

---

## 7. O que o chat não deve aprender automaticamente

Não salvar automaticamente:

- senhas;
- tokens;
- chaves de API;
- dados pessoais sensíveis;
- fofoca;
- suposição do modelo;
- erro do usuário;
- resposta alucinada;
- dado operacional temporário;
- preço interno sem permissão;
- dado de cliente sem escopo;
- informação confidencial sem política.

Regra:

Memória não é lixeira de conversa.

---

## 8. Camadas de memória

### 8.1 Memória de turno

Dura apenas durante a resposta atual.

Uso:

- resolver pronome;
- entender pergunta;
- usar último trecho.

---

### 8.2 Memória de sessão

Dura durante a conversa.

Uso:

- preferências temporárias;
- produto ativo;
- arquivo ativo;
- última query SQL;
- última lousa;
- tarefa em andamento.

---

### 8.3 Memória de usuário

Dura entre sessões, se permitido.

Uso:

- preferências estáveis;
- modo de escrita;
- formato favorito;
- histórico de uso.

Requer governança.

---

### 8.4 Memória de projeto

Dura para um projeto ou workspace.

Uso:

- glossário do projeto;
- decisões;
- padrões;
- documentos;
- playbooks;
- contexto compartilhado.

---

### 8.5 Memória global validada

Conhecimento aprovado pela equipe.

Uso:

- documentação oficial;
- capacidades do chat;
- termos corporativos;
- regras de roteamento;
- padrões de resposta.

---

## 9. Pipeline de aprendizagem de palavra nova

Quando surgir uma palavra desconhecida:

Mensagem do usuário
→ detectar termo desconhecido
→ verificar se existe no glossário
→ verificar se existe em documentos internos
→ verificar se existe em memória do projeto
→ se permitido, pesquisar na web
→ gerar candidato de significado
→ classificar confiança
→ pedir confirmação se necessário
→ salvar como candidato
→ usar futuramente com baixa/média/alta confiança

---

## 10. Serviço de vocabulário

Criar:

ChatVocabularyLearningService

Responsabilidades:

- detectar termos novos;
- detectar abreviações;
- detectar typos recorrentes;
- detectar sinônimos;
- detectar termos técnicos;
- armazenar significado;
- mapear termo para intenção;
- mapear termo para entidade;
- sugerir atualização do normalizador.

Estrutura:

{
  "term": "s chama",
  "normalized": "se chama",
  "type": "typo",
  "scope": "global",
  "confidence": 0.96,
  "evidenceCount": 18,
  "examples": [
    "como vc s chama?",
    "como voce s chama?"
  ],
  "suggestedAction": "add_normalization_rule"
}

---

## 11. Serviço de pesquisa de significado

Criar:

ChatMeaningDiscoveryService

Responsabilidade:

Descobrir o significado de termos desconhecidos.

Fontes por prioridade:

1. Glossário oficial.
2. Documentação do projeto.
3. Memória validada.
4. Histórico da sessão.
5. Base vetorial.
6. Pesquisa web autorizada.
7. Pergunta de clarificação ao usuário.

---

## 12. Pesquisa web para significado

Criar:

ChatWebMeaningResearchService

Usar web apenas quando:

- termo não existir internamente;
- termo parecer público;
- usuário permitir;
- não houver dado sensível;
- fonte externa for adequada.

Não pesquisar web quando:

- termo parece interno/confidencial;
- termo envolve cliente, preço, pedido, projeto restrito;
- usuário pediu para não pesquisar;
- há fonte interna suficiente.

Resposta ideal:

"Não encontrei esse termo no glossário interno. Posso pesquisar fontes públicas para tentar entender o significado?"

---

## 13. Classificação de termos desconhecidos

| Tipo | Exemplo | Ação |
|---|---|---|
| typo | "s chama" | normalizar |
| abreviação | "vc" | expandir |
| sigla interna | "LMP" | buscar glossário interno |
| termo técnico | "RAG" | buscar documentação/conhecimento |
| termo público | "PKCE" | pode usar docs/web |
| nome de cliente | "Cliente X" | não pesquisar web sem cuidado |
| código interno | "10080001" | tratar como entidade operacional |
| conceito novo | "modo lousa" | buscar docs do projeto |

---

## 14. Candidatos de conhecimento

Todo aprendizado novo deve entrar primeiro como candidato.

Tabela conceitual:

learning_candidates

Campos:

- id
- type
- term
- proposed_meaning
- source
- evidence
- confidence
- scope
- status
- created_by
- created_at
- reviewed_by
- reviewed_at

Status:

- pending
- auto_approved
- approved
- rejected
- expired
- promoted

---

## 15. Promoção de conhecimento

Um candidato pode virar:

- regra de normalização;
- entrada no glossário;
- chunk RAG;
- prompt policy;
- skill instruction;
- exemplo few-shot;
- caso de teste;
- sugestão de UI;
- preferência de usuário;
- playbook.

Exemplo:

Termo:
"como vc s chama"

Promoção:

- adicionar normalização;
- adicionar teste;
- adicionar padrão em identity.json;
- medir se erro desaparece.

---

## 16. Aprendizado por feedback

Quando usuário dá feedback negativo, registrar:

- mensagem original;
- resposta;
- intenção detectada;
- ferramentas usadas;
- contexto usado;
- motivo do feedback;
- resposta corrigida;
- sugestão de melhoria.

Exemplo:

Feedback:
"não entendeu pergunta simples"

Ação:

- adicionar ao dataset de classificação;
- melhorar normalização;
- adicionar teste;
- ajustar gate simples.

---

## 17. Aprendizado por correção explícita

Se o usuário disser:

"Quando eu falar X, quero dizer Y."

Salvar com alta confiança.

Exemplo:

Usuário:
"Quando eu disser lousa, estou falando do canvas do chat."

Memória:

{
  "type": "term_definition",
  "term": "lousa",
  "meaning": "canvas do chat",
  "scope": "global_or_project",
  "confidence": "high"
}

---

## 18. Aprendizado por padrão repetido

Se muitos usuários digitam:

- "vc s chama"
- "oq vc faz"
- "q horas sao"
- "me ajuda ai"

O sistema deve criar candidatos automáticos.

Critério:

- ocorrência >= 10;
- feedback negativo associado;
- solução provável >= 0.85;
- sem risco operacional.

---

## 19. Aprendizado por uso de botão

Se usuários sempre clicam em determinado botão após uma resposta, melhorar sugestões.

Exemplo:

Após e-mail, usuários clicam muito em "Deixar mais curto".

Ação:

- priorizar chip "Deixar mais curto";
- sugerir versão curta automaticamente em alguns casos;
- registrar preferência por usuário, se permitido.

---

## 20. Aprendizado por resultado operacional

Se uma consulta frequentemente retorna vazio, aprender recuperação.

Exemplo:

Usuários consultam "estoque produto X" e resultado vazio.

O sistema aprende a sugerir:

- buscar por descrição;
- consultar outra filial;
- ampliar filtro;
- verificar código.

---

## 21. Aprendizado por documentos

Quando novos documentos forem adicionados:

- indexar;
- extrair glossário;
- extrair entidades;
- extrair FAQs;
- extrair exemplos;
- gerar chunks;
- atualizar RAG;
- criar testes de perguntas esperadas.

---

## 22. Arquitetura de memória semântica

Usar embeddings para:

- termos;
- perguntas;
- respostas corrigidas;
- documentos;
- chunks;
- glossário;
- exemplos.

Armazenar em banco vetorial ou tabela com embedding.

Busca:

query
→ normalização
→ busca lexical
→ busca vetorial
→ reranking
→ top resultados
→ resposta

RAG é indicado justamente para manter conhecimento externo atualizável e citável, em vez de depender apenas dos pesos do modelo. Pesquisas de RAG destacam benefícios como atualização contínua, uso de bases externas e maior rastreabilidade. :contentReference[oaicite:5]{index=5}

---

## 23. Arquitetura de memória episódica

Salvar episódios úteis:

- tarefa concluída;
- correção importante;
- preferência do usuário;
- decisão de projeto;
- erro recorrente;
- consulta refinada;
- documento criado.

Exemplo:

{
  "episode": "Usuário pediu playbooks em txt para copiar",
  "scope": "user",
  "confidence": 0.93
}

---

## 24. Aprendizado por fine-tuning offline

Não fazer fine-tuning em tempo real.

Fluxo seguro:

Interações
→ feedback
→ curadoria
→ dataset
→ avaliação
→ fine-tuning offline
→ teste A/B
→ deploy controlado
→ monitoramento

Entradas possíveis para fine-tuning:

- perguntas com resposta correta;
- correções do usuário;
- exemplos de roteamento;
- exemplos de fallback;
- exemplos de escrita;
- exemplos de SQL;
- exemplos de não entendimento.

Nunca treinar com:

- dados sensíveis;
- respostas ruins;
- conversas sem consentimento;
- dados sem anonimização;
- erros sem correção.

---

## 25. Human-in-the-loop

O sistema deve aprender com supervisão.

Papéis:

- usuário corrige;
- admin aprova candidatos;
- especialista valida glossário;
- desenvolvedor promove regra;
- testes garantem regressão.

Aprendizagem sem revisão pode causar:

- contaminação de memória;
- respostas erradas;
- viés;
- vazamento de dados;
- normalização ruim;
- alucinação reforçada.

---

## 26. Evitar aprendizagem tóxica

Criar:

ChatLearningSafetyGuard

Bloquear aprendizado se:

- contém segredo;
- contém dado pessoal sensível;
- contém instrução maliciosa;
- contradiz regra oficial;
- vem de fonte não confiável;
- é apenas hipótese do modelo;
- é feedback hostil sem conteúdo útil;
- tenta burlar permissão.

---

## 27. Controle por confiança

Cada memória deve ter confiança.

| Confiança | Origem |
|---|---|
| alta | usuário definiu explicitamente, admin aprovou ou fonte oficial |
| média | inferência com evidência repetida |
| baixa | hipótese ou termo novo sem validação |

Uso:

- alta: pode orientar resposta;
- média: pode sugerir com cautela;
- baixa: deve pedir confirmação.

---

## 28. Memória não substitui autorização

Mesmo que o chat "lembre" algo, ele não pode usar isso para burlar permissões.

A arquitetura da Minha DELPI já separa autenticação e autorização: Keycloak autentica, e a Core API resolve permissões efetivas. :contentReference[oaicite:6]{index=6} O aprendizado deve respeitar o mesmo princípio.

Regra:

Lembrar não significa autorizar.

---

## 29. Integração com arquitetura atual

A Minha DELPI separa governança da plataforma e domínios operacionais: Core API governa plataforma, API DELPI atende dados e regras operacionais, Portal entrega experiência visual, plugins implementam módulos e Keycloak autentica usuários. :contentReference[oaicite:7]{index=7}

Distribuição sugerida:

### Backend IA / API DELPI

- memória semântica;
- memória episódica;
- busca web;
- embeddings;
- RAG;
- feedback;
- classificação;
- aprendizado.

### Core API

- permissões;
- governança;
- auditoria;
- consentimentos;
- usuários;
- acesso ao que pode ser aprendido.

### Portal

- UX de memória;
- mostrar contexto usado;
- permitir corrigir;
- permitir esquecer;
- feedback;
- botões de aprendizado.

### Banco

- learning_candidates;
- memory_items;
- vocabulary_terms;
- feedback_events;
- evaluation_cases.

---

## 30. Modelo de dados sugerido

### memory_items

- id
- user_id
- project_id
- session_id
- scope
- type
- content
- content_json
- embedding
- confidence
- source
- status
- expires_at
- created_at
- updated_at

---

### vocabulary_terms

- id
- term
- normalized_term
- meaning
- type
- scope
- source
- confidence
- evidence_count
- approved
- created_at
- updated_at

---

### learning_candidates

- id
- candidate_type
- input_text
- proposed_rule
- proposed_meaning
- evidence_json
- confidence
- risk_level
- status
- reviewer_id
- created_at
- reviewed_at

---

### feedback_events

- id
- user_id
- session_id
- message_id
- rating
- reason
- comment
- detected_intent
- expected_intent
- corrected_answer
- created_at

---

### evaluation_cases

- id
- category
- input
- expected_intent
- expected_answer
- must_not_use_tools
- must_not_use_rag
- source_feedback_id
- status

---

## 31. Pipeline de autoaprendizagem

### Etapa 1 — Captura

Registrar:

- mensagem;
- intenção;
- resposta;
- feedback;
- contexto;
- ferramentas usadas;
- erro ou sucesso.

---

### Etapa 2 — Extração

Extrair:

- termos novos;
- typos;
- entidades;
- preferências;
- correções;
- padrões recorrentes.

---

### Etapa 3 — Candidatura

Criar candidato:

- nova regra;
- novo termo;
- novo teste;
- nova memória;
- novo exemplo.

---

### Etapa 4 — Validação

Validar por:

- confiança;
- fonte;
- repetição;
- segurança;
- aprovação humana;
- teste automático.

---

### Etapa 5 — Promoção

Promover para:

- memória;
- glossário;
- RAG;
- normalizador;
- prompt;
- skill;
- teste;
- fine-tuning dataset.

---

### Etapa 6 — Avaliação

Rodar testes:

- regressão;
- roteamento;
- small talk;
- texto;
- SQL;
- memória;
- segurança.

---

### Etapa 7 — Publicação

Aplicar em produção com:

- feature flag;
- versão;
- rollback;
- monitoramento.

---

## 32. Exemplo prático: aprender “como vc s chama”

### Interação

Usuário:
como vc s chama?

Chat erra ou demora.

Feedback:
não entendeu pergunta simples.

### Aprendizado

Candidato:

{
  "type": "normalization_rule",
  "input": "como vc s chama",
  "normalized": "como voce se chama",
  "intent": "assistant_identity.name",
  "confidence": 0.95
}

### Promoção

- adicionar regra ao normalizador;
- adicionar padrão ao identity.json;
- adicionar teste unitário;
- adicionar teste de streaming;
- medir queda de erro.

---

## 33. Exemplo prático: aprender termo interno

Usuário:
"Quando eu disser Onda 13, estou falando da fase de visão documental."

Sistema:

- salva como termo de projeto;
- pergunta se deve lembrar sempre no projeto;
- cria candidato de glossário;
- passa a recuperar esse significado no contexto.

Resposta:

"Entendido. Nesta conversa, vou considerar 'Onda 13' como a fase de visão documental."

Se o usuário autorizar:

"Posso salvar esse significado no glossário do projeto?"

---

## 34. Exemplo prático: pesquisar significado na web

Usuário:
"o que é PKCE?"

Sistema:

1. Verifica glossário interno.
2. Verifica docs internas.
3. Se não houver, usa conhecimento geral ou web se atualizado/preciso.
4. Salva termo público no glossário candidato.

Resposta:

"PKCE é uma extensão do OAuth2 usada para proteger fluxos de autenticação em apps públicos. Posso salvar esse termo no glossário técnico?"

---

## 35. Pesquisa web com controle

Se o termo for público:

- pesquisar;
- priorizar fonte oficial;
- resumir;
- salvar fonte;
- criar candidato.

Se for interno:

- não pesquisar sem autorização.

Exemplo:

"Procure significado de CFW500"
→ pode pesquisar web.

"Procure significado do cliente X e nosso preço"
→ bloquear preço interno.

---

## 36. Métricas de inteligência progressiva

Medir:

- novas palavras detectadas;
- typos corrigidos;
- candidatos criados;
- candidatos aprovados;
- candidatos rejeitados;
- feedback negativo reduzido;
- fallback reduzido;
- tempo de resposta reduzido;
- acerto de intenção aumentado;
- uso de memória;
- taxa de resposta direta;
- ferramentas evitadas;
- testes criados a partir de feedback;
- melhorias promovidas.

---

## 37. Dashboard de aprendizagem

Criar painel admin:

### Vocabulário

- termos novos;
- termos aprovados;
- termos pendentes;
- termos rejeitados.

### Typos

- erros mais comuns;
- normalizações sugeridas;
- impacto na intenção.

### Feedback

- motivos mais comuns;
- respostas ruins;
- intenções erradas.

### Memória

- memórias usadas;
- memórias corrigidas;
- memórias removidas.

### RAG

- documentos mais recuperados;
- termos sem fonte;
- fontes web salvas.

### Testes

- testes gerados;
- testes falhando;
- cobertura por intenção.

---

## 38. Aprendizagem com eventos

Usar arquitetura event-driven.

Eventos:

- chat.message.received
- chat.intent.detected
- chat.response.generated
- chat.feedback.submitted
- chat.term.unknown_detected
- chat.term.candidate_created
- chat.term.approved
- chat.memory.created
- chat.memory.used
- chat.normalization_rule.suggested
- chat.evaluation_case.created
- chat.learning_candidate.promoted

O projeto já usa abordagem event-driven com publicação após commit para evitar eventos sobre mudanças que falharam no banco. Esse mesmo padrão deve ser seguido na aprendizagem contínua. :contentReference[oaicite:8]{index=8}

---

## 39. Segurança e governança

Regras:

1. Aprendizado persistente exige escopo claro.
2. Usuário deve poder apagar memórias.
3. Dados sensíveis devem ser bloqueados.
4. Aprendizado global deve passar por aprovação.
5. Toda regra nova deve ter teste.
6. Toda fonte web deve ter URL e data.
7. Toda memória deve ter confiança.
8. Toda memória deve ter origem.
9. Toda memória deve respeitar permissão.
10. Toda promoção deve ser auditável.

---

## 40. Níveis de aprendizagem

### Nível 1 — Sessão

Aprende só na conversa atual.

Exemplo:

"Neste chat, responda curto."

---

### Nível 2 — Usuário

Aprende preferência do usuário.

Exemplo:

"Eu prefiro respostas em tópicos."

---

### Nível 3 — Projeto

Aprende glossário e decisões do projeto.

Exemplo:

"No projeto Minha DELPI, lousa significa canvas."

---

### Nível 4 — Organização

Aprende termos aprovados globalmente.

Exemplo:

"Minha DELPI é o nome oficial da plataforma."

---

### Nível 5 — Modelo

Fine-tuning offline com dataset aprovado.

Exemplo:

Melhorar classificador de intenção com interações reais anonimizadas.

---

## 41. Roadmap de implementação

### Fase 1 — Captura e feedback

- Registrar eventos de conversa.
- Registrar feedback estruturado.
- Criar tabela learning_candidates.
- Criar tabela vocabulary_terms.
- Criar avaliação de intenção.

---

### Fase 2 — Normalização aprendida

- Detectar typos recorrentes.
- Sugerir novas regras.
- Aprovar regras no admin.
- Criar testes automáticos.

---

### Fase 3 — Memória de usuário e sessão

- Memória temporária.
- Preferências.
- Correções.
- Contexto ativo.
- Esquecer/limpar memória.

---

### Fase 4 — Glossário vivo

- Extrair termos.
- Buscar significado interno.
- Pesquisar web quando autorizado.
- Criar candidatos.
- Aprovar no admin.
- Integrar ao RAG.

---

### Fase 5 — RAG adaptativo

- Indexar termos aprovados.
- Recuperar glossário em perguntas.
- Reranking.
- Fontes citáveis.
- Atualização contínua.

---

### Fase 6 — Avaliação automática

- Criar dataset de regressão.
- Rodar testes por intenção.
- Medir melhoria.
- Bloquear promoção que quebra casos antigos.

---

### Fase 7 — Fine-tuning offline

- Curadoria de interações.
- Anonimização.
- Treino offline.
- Avaliação.
- Deploy controlado.
- Rollback.

---

## 42. Critérios de aceite

O sistema estará funcionando quando:

1. O chat aprender typos recorrentes.
2. O chat aprender preferências do usuário.
3. O chat criar candidatos de glossário.
4. O chat pesquisar significados públicos quando autorizado.
5. O chat pedir confirmação para termos ambíguos.
6. O chat não salvar dados sensíveis.
7. O chat melhorar roteamento com feedback.
8. O chat gerar testes a partir de erros.
9. O chat reduzir respostas “não entendi” ao longo do tempo.
10. O chat continuar seguro mesmo aprendendo.

---

## 43. Anti-padrões

Evitar:

1. Treinar pesos em tempo real sem validação.
2. Salvar tudo que o usuário fala.
3. Aprender informações falsas.
4. Aprender resposta gerada pelo próprio modelo como fato.
5. Pesquisar dados internos na web.
6. Usar memória como autorização.
7. Não permitir apagar memória.
8. Não registrar origem.
9. Não medir impacto.
10. Promover regra sem teste.
11. Fine-tuning com dados sensíveis.
12. Aprender com feedback sem curadoria.

---

## 44. Resumo executivo

Para o Minha DELPI Chat ficar mais inteligente quanto mais é usado, o caminho correto é criar uma camada de aprendizagem contínua ao redor do modelo.

Essa camada deve:

- capturar interações;
- detectar termos novos;
- entender typos;
- pesquisar significados quando permitido;
- criar memórias;
- validar conhecimento;
- promover conhecimento aprovado;
- gerar testes;
- melhorar prompts, RAG, normalização, roteamento e, quando seguro, fine-tuning offline.

Regra final:

O chat não deve aprender tudo automaticamente.
Ele deve aprender com evidência, validação, memória segura e feedback.