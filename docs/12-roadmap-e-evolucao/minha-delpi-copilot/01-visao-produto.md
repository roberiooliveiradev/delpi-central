# 01 — Visão de produto

## 1. Definição

O **Minha DELPI Copilot** é uma **nova aplicação standalone** da Minha DELPI e a camada inteligente operacional transversal da plataforma.

Ele acompanha o usuário, entende contexto, conecta dados/conhecimento, navega, executa operações autorizadas e sustenta trabalho além de um turno.

Ele possui API, MFE, persistência, manifesto e deploy próprios. Não é expansão do `minha-delpi-ai-api` ou `plugins/minha-delpi-chat`.

## 2. North Star

> **Entender o contexto da organização, conectar dados, pessoas, processos e aplicações, investigar problemas, executar trabalho, acompanhar resultados e transformar conhecimento empresarial em ação governada.**

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
```

## 3. Promessa

> O usuário diz o objetivo. O Copilot encontra contexto e recursos autorizados, aplica conhecimento adequado, mostra evidências, executa o permitido, pede a decisão humana correta e acompanha o trabalho até um outcome verificável.

## 4. Relação com a plataforma

```text
Portal      → host/context/navigation
Core API    → apps/routes/RBAC/governance
Keycloak    → identity/SSO
Gateway     → routing
plugin-ui   → shared design system
Domain APIs → business data/rules
Copilot API → intelligence/work runtime
Copilot MFE → product UX
```

O Copilot reutiliza a **plataforma**, não o runtime do Minha DELPI Chat.

## 5. Pilares

### Explicar/consultar
- páginas/campos/indicadores/processos;
- dados corporativos;
- documentos/normas;
- relações entre entities.

### Analisar
- comparar períodos/entities;
- cruzar APIs;
- usar Business Graph;
- analisar documentos/desenhos;
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
- artifacts.

## 6. Copilot único

O usuário não escolhe “Agente Engenharia”, “Agente Qualidade” etc.

```text
one Copilot
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal tools
+ authorized capabilities
```

## 7. Experiência-alvo

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

Tudo executado pelo runtime próprio do Copilot.

## 8. Personas

- usuário operacional;
- analista;
- gestor;
- especialista de área;
- colaborador de Case/Room;
- administrador/governança.

## 9. UX principles

- language natural é entrada, não única surface;
- evidence/state visíveis;
- hypothesis não vira fact;
- Decision Gate explica impacto;
- contexto corrigível/removível;
- não repetir pergunta respondida;
- distinguir prepared/executed/verified;
- Task/Case/Inbox quando chat é insuficiente;
- no manual agent selection;
- accessibility by default;
- full-page e panel usam o mesmo produto/runtime.

## 10. Non-goals

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
- tratar Simulation como efeito real.

## 11. Métricas

Macro: **Task Completion Rate**.

Complementares:

- Safe Execution Rate;
- Evidence Coverage;
- First Plan Success;
- Clarification Efficiency;
- Correction Rate;
- Case Resolution Rate;
- Watch Signal Quality;
- latency/cost;
- AI-ready coverage;
- standalone availability;
- Chat-independence failures = zero.

## 12. Implantação

A ordem é foundation-first:

```text
platform/architecture
→ standalone bootstrap
→ context/platform commands
→ intelligence
→ reads/graph
→ writes/durable
→ work/proactivity
→ autonomy/optimization
```

Fonte de verdade: `16-execution-master-plan.md`.