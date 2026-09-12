# 01 — Visão de produto

**Status:** visão canônica de produto  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Definição

O **Minha DELPI Copilot** é uma **nova aplicação standalone** da Minha DELPI e a camada inteligente operacional transversal da plataforma.

Ele acompanha o usuário, entende contexto, conecta dados/conhecimento, navega, executa operações autorizadas e sustenta trabalho além de um turno.

A visão de produto vai além do administrativo: o Copilot deve estar preparado para atender **escritório, reuniões, engenharia, manutenção, qualidade e chão de fábrica**, incluindo interação por texto, voz, imagem, câmera, vídeo e documentos quando autorizada.

Ele possui API, MFE, persistência, manifesto e deploy próprios. Não é expansão do `minha-delpi-ai-api` ou `plugins/minha-delpi-chat`.

## 2. North Star

> **Minha DELPI Copilot é a interface inteligente entre as pessoas e a operação da DELPI. Está presente no escritório e na fábrica, entende texto, voz, imagem, vídeo, documentos, contexto operacional e dados empresariais; ajuda pessoas a entender, decidir, executar e aprender, preservando permissões, evidências, segurança, privacidade e governança.**

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
APRENDER   → transformar experiência validada em conhecimento governado
```

## 3. Promessa

> O usuário diz ou demonstra o objetivo. O Copilot encontra contexto e recursos autorizados, aplica conhecimento adequado, mostra evidências, executa o permitido, pede a decisão humana correta e acompanha o trabalho até um outcome verificável.

“Demonstra” pode significar, quando a surface permitir:

- falar;
- mostrar uma imagem;
- apontar a câmera;
- compartilhar tela;
- anexar documento/desenho;
- contextualizar uma OP/máquina/produto/posto.

## 4. Relação com a plataforma

```text
Portal      → host/context/navigation
Core API    → apps/routes/RBAC/governance
Keycloak    → identity/SSO
Gateway     → routing
plugin-ui   → shared design system
Domain APIs → business data/rules
Copilot API → intelligence/work/media runtime
Copilot MFE → product UX
```

O Copilot reutiliza a **plataforma**, não o runtime do Minha DELPI Chat.

## 5. Presença e acesso

A direção de produto é disponibilizar o **entry point do Copilot amplamente aos usuários autenticados da Minha DELPI**, condicionado à permissão de acesso do Copilot e ao rollout definido.

Isso não significa que todos veem ou fazem as mesmas coisas.

```text
Copilot disponível
+
permissões efetivas do usuário
+
contexto atual
+
policies/risk
=
capabilities realmente disponíveis
```

Invariante:

```text
Copilot effective capabilities ⊆ user effective capabilities
```

## 6. Surfaces do mesmo produto

```text
GLOBAL      → painel lateral/contextual no Portal
WORKSPACE   → página completa para análise e trabalho prolongado
MEETING     → reunião com voz, tela, mídia, dados e ata viva
FRONTLINE   → operador/posto/máquina com voz, câmera e UI simplificada
```

São quatro experiências sobre **uma única Copilot API, uma identidade Copilot e uma governança comum**.

## 7. Pilares

### Explicar/consultar
- páginas/campos/indicadores/processos;
- dados corporativos;
- documentos/normas;
- relações entre entities;
- instruções e procedimentos operacionais.

### Analisar
- comparar períodos/entities;
- cruzar APIs;
- usar Business Graph;
- analisar documentos/desenhos/imagens/vídeos permitidos;
- separar fact/calc/hypothesis/conclusion/recommendation;
- mostrar evidence/provenance.

### Navegar
- app/route/entity;
- view/tab/filter;
- MFE/iframe context;
- authorized deep links.

### Executar
- real Business Actions via Domain APIs;
- Decision Gates;
- outcome verification;
- idempotency/audit.

### Trabalhar ao longo do tempo
- Durable Workflow;
- Task;
- Case;
- Interaction Room;
- Inbox;
- Watch/event resume.

### Produzir
- relatórios/resumos;
- análises;
- mensagens/e-mails;
- planos de ação;
- atas de reunião;
- artifacts.

### Assistir pessoas no trabalho físico
- ajuda hands-free;
- explicação de operação/desenho;
- câmera/imagem como Evidence;
- histórico de problemas;
- escalation para líder/manutenção/qualidade;
- treinamento contextual;
- registro governado de ocorrências.

## 8. Copilot único

O usuário não escolhe “Agente Engenharia”, “Agente Qualidade” etc.

```text
one Copilot
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal tools
+ authorized capabilities
```

O mesmo Copilot pode atender um comprador, engenheiro, operador, técnico, gestor ou diretor; o que muda é o contexto, expertise e conjunto autorizado de capabilities.

## 9. Experiência-alvo administrativa/técnica

> “Esse produto está dando problema no cliente. Investigue se é desenho, fabricação ou fornecedor e monte um 8D.”

O Copilot pode:

1. resolver produto/reclamação;
2. abrir Case;
3. percorrer Business Graph;
4. consultar qualidade/produção/suprimentos;
5. analisar desenho;
6. organizar Evidence Board;
7. aplicar Engineering + Quality Expertise;
8. aplicar 8D Playbook;
9. criar Tasks;
10. aguardar evidência/evento;
11. apresentar conclusions/limitations;
12. preparar ações;
13. submeter writes a Decision Gate;
14. verificar outcomes;
15. manter audit/continuidade.

## 10. Experiência-alvo em reunião

> “Copilot, mostre a produção de ontem da Linha 2 e compare com a meta.”

Durante Meeting Mode o Copilot pode:

- transcrever com consentimento;
- responder perguntas usando APIs reais;
- registrar tópicos/decisões/pendências;
- gerar ata;
- transformar ações confirmadas em Tasks/Cases/solicitações;
- retomar pendências na reunião seguinte.

A ata deve distinguir **transcrição, resumo, decisão humana, ação proposta e ação efetivamente executada**.

## 11. Experiência-alvo Frontline

> “Estou nesta operação e não estou conseguindo encaixar o terminal. Mostra a posição correta e verifica se já aconteceu antes.”

O Copilot pode usar:

```text
operador autenticado
+ posto/terminal
+ OP/operação
+ máquina
+ produto/revisão
+ desenho/instrução
+ histórico de qualidade/manutenção
+ voz/câmera
```

para orientar, mostrar Evidence, registrar problema ou escalar ajuda.

Ele **não** substitui interlock de máquina, critério oficial de inspeção ou autorização humana obrigatória.

## 12. Aprendizado organizacional

O Copilot pode ajudar a capturar conhecimento tácito e práticas observadas, mas não altera produção automaticamente.

```text
observação/experiência
→ candidate knowledge
→ Evidence
→ specialist/owner review
→ eval
→ versioned publish
```

Nunca:

```text
uma observação do operador
→ nova regra de produção automática
```

## 13. Personas

- operador de produção;
- técnico/manutenção;
- inspetor/qualidade;
- usuário operacional;
- analista;
- engenheiro/especialista;
- comprador/comercial/financeiro;
- gestor;
- participante de reunião;
- colaborador de Case/Room;
- administrador/governança.

## 14. UX principles

- linguagem natural é entrada, não única surface;
- voz/câmera/vídeo são modalidades, não bypasses de autorização;
- evidence/state visíveis;
- hypothesis não vira fact;
- Decision Gate explica impacto;
- contexto corrigível/removível;
- não repetir pergunta respondida;
- distinguir prepared/executed/verified;
- Task/Case/Inbox quando chat é insuficiente;
- no manual agent selection;
- accessibility by default;
- full-page/panel/meeting/frontline usam o mesmo produto/runtime;
- capture de mídia sempre explícita e visível;
- data minimization por padrão.

## 15. Segurança industrial e privacidade

O Copilot não deve virar caminho livre:

```text
LLM → PLC/CNC/robô/máquina
```

Qualquer futura atuação OT requer gate arquitetural e de segurança industrial separado, com comando determinístico, allowlist, interlocks independentes, autorização, simulation/test environment, fail-safe e audit.

Também não é objetivo inicial:

- reconhecimento facial;
- emotion detection;
- vigilância contínua;
- scoring oculto de pessoas;
- armazenamento indiscriminado de vídeo/áudio;
- aprovação/reprovação de peça baseada apenas em impressão visual de LLM.

## 16. Non-goals

O Copilot não deve:

- depender do runtime/database/API do Minha DELPI Chat;
- obter mais permission que o usuário;
- duplicar Core/RBAC;
- duplicar domain business rules;
- usar DOM automation quando API existe;
- inventar endpoint/URL/action/permission;
- usar Graph como master database;
- criar AI engine por departamento;
- persistir chain-of-thought;
- executar write sem required policy/Decision Gate;
- auto-learn production behavior;
- tratar Simulation como efeito real;
- operar máquina arbitrariamente;
- capturar pessoas/mídia sem finalidade e policy explícitas.

## 17. Métricas

Macro: **Task Completion Rate**.

Complementares:

- Safe Execution Rate;
- Evidence Coverage;
- First Plan Success;
- Clarification Efficiency;
- Correction Rate;
- Case Resolution Rate;
- Watch Signal Quality;
- Meeting Action Closure Rate;
- Meeting Summary Correction Rate;
- Frontline Help Resolution Rate;
- Escalation Quality;
- media/session latency and cost;
- privacy/consent violations = zero;
- unsafe OT actuation attempts blocked = 100%;
- AI-ready coverage;
- standalone availability;
- Chat-independence failures = zero.

## 18. Implantação

A ordem é foundation-first:

```text
platform/architecture/media/OT/privacy foundations
→ standalone bootstrap
→ context/platform commands
→ intelligence + multimodal foundations
→ reads/graph
→ writes/durable
→ work + Meeting/Frontline + proactivity
→ advanced realtime/autonomy/optimization
```

Fonte de verdade: `16-execution-master-plan.md`.