# 01 — Visão de produto

## 1. Definição

O **Minha DELPI Copilot** é a camada inteligente operacional transversal da Minha DELPI. Ele acompanha o usuário, entende contexto, conecta dados e conhecimento, navega pela plataforma, executa operações autorizadas e sustenta trabalho que pode continuar além de um único turno de chat.

Não é um chatbot separado nem um conjunto de agentes departamentais. É uma nova forma de operar a mesma plataforma.

## 2. North Star

> **Entender o contexto da organização, conectar dados, pessoas, processos e aplicações, investigar problemas, executar trabalho, acompanhar resultados e transformar conhecimento empresarial em ação governada.**

Quatro verbos:

```text
PERGUNTAR  → entender, pesquisar, explicar, analisar
FAZER      → navegar, consultar, criar, alterar, aprovar, executar
ACOMPANHAR → monitorar, detectar, alertar, reagir
TRABALHAR  → investigar, colaborar, planejar, acompanhar, concluir
```

## 3. Promessa do produto

> O usuário diz o objetivo. O Copilot encontra contexto e recursos autorizados, aplica conhecimento adequado, mostra evidências, executa o que for permitido, pede a decisão humana correta quando necessário e acompanha o trabalho até um outcome verificável.

## 4. Pilares

### Explicar e consultar

- páginas, campos, indicadores e processos;
- dados corporativos;
- documentos/normas;
- relações entre entidades;
- erros/limitações sem expor detalhes sensíveis.

### Analisar

- comparar períodos/entidades;
- cruzar APIs;
- usar Business Graph;
- analisar documentos/desenhos;
- separar fato, cálculo, hipótese, conclusão e recomendação;
- mostrar evidence/provenance.

### Navegar

- app/rota/entidade;
- view/aba/filtro;
- MFE/iframe context;
- deep links autorizados.

### Executar

- Business Actions reais via APIs/use cases;
- Decision Gates proporcionais ao risco;
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

- relatórios;
- resumos;
- análises;
- mensagens/e-mails;
- planos de ação;
- artifacts suportados.

## 5. Copilot único

O usuário não precisa escolher entre “Agente Engenharia”, “Agente Qualidade” etc.

```text
mesmo Copilot
+ Expertise Packs
+ Domain Playbooks
+ Knowledge
+ Multimodal tools
+ authorized capabilities
```

Problemas cross-domain podem combinar várias especialidades no mesmo trabalho.

## 6. Experiência-alvo

Usuário:

> “Esse produto está dando problema no cliente. Investigue se é desenho, fabricação ou fornecedor e monte um 8D.”

O Copilot pode, de acordo com permissions/APIs disponíveis:

1. resolver produto/reclamação;
2. abrir um Case;
3. percorrer relações relevantes no Business Graph;
4. consultar qualidade/produção/suprimentos;
5. analisar desenho/anexos;
6. organizar Evidence Board;
7. aplicar Engineering + Quality Expertise;
8. aplicar 8D Playbook;
9. criar Tasks para pendências;
10. aguardar nova evidence/evento quando necessário;
11. apresentar conclusões/limitações;
12. preparar ações;
13. submeter writes ao Decision Gate;
14. verificar outcomes;
15. manter audit/continuidade.

Tudo sem trocar de agente.

## 7. Personas

### Usuário operacional
Quer concluir tarefas sem decorar caminhos da plataforma.

### Analista
Quer investigar, cruzar evidências e explicar causas.

### Gestor
Quer síntese, riscos, decisões e acompanhamento.

### Especialista de área
Quer método profissional, evidência e integração com seus processos.

### Colaborador de Case/Room
Quer participar de investigação/decisão compartilhada com o Copilot.

### Administrador/governança
Quer gerir capabilities, policies, expertise/playbooks, quality/evals, rollout e audit.

## 8. Princípios de UX

- linguagem natural é entrada, não única surface;
- evidência e estado operacional são visíveis;
- nenhuma hipótese se apresenta como fato;
- Decision Gate explica impacto real;
- contexto pode ser corrigido/removido;
- não repetir pergunta já respondida;
- distinguir preparado/executado/verificado;
- Task/Case/Inbox são usados quando chat deixa de ser unidade suficiente;
- nenhuma tarefa normal exige seleção manual de agente;
- accessibility by default.

## 9. Não objetivos

O Copilot não deve:

- obter mais permissão que o usuário;
- usar DOM automation quando API/use case existe;
- inventar endpoint/URL/action/permission;
- duplicar Business Graph como banco mestre;
- criar logic/business state paralelos às aplicações;
- criar engine de IA por departamento;
- persistir chain-of-thought;
- executar write sem policy/Decision Gate requerido;
- aprender automaticamente em produção com correções do usuário;
- tratar Simulation como efeito real.

## 10. Métricas de sucesso

Métrica macro: **Task Completion Rate**, segmentada por:

- navigation;
- read;
- analysis;
- write;
- Task;
- Case;
- Workflow.

Complementares:

- Safe Execution Rate;
- Evidence Coverage;
- First Plan Success;
- Clarification Efficiency;
- Correction Rate;
- Case Resolution Rate;
- Watch Signal Quality;
- latency/cost;
- AI-ready coverage.

## 11. Princípio de implantação

A ambição do produto não altera a ordem de construção: primeiro foundations compartilhadas, depois features. Fonte de verdade: `16-execution-master-plan.md`.