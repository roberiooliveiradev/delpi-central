# 09 — UX do Minha DELPI Copilot

## 1. Princípio

O Copilot deve parecer parte da plataforma, não uma janela de chat isolada.

A linguagem natural é a porta de entrada; o produto também possui surfaces de trabalho persistente, evidence, decisions e acompanhamento.

```text
Chat
+ Context
+ Activity
+ Evidence
+ Decisions
+ Tasks
+ Cases
+ Rooms
+ Inbox
+ Watch
```

## 2. Uma única identidade

A UI não deve exigir que o usuário escolha “Agente Engenharia”, “Agente Qualidade” etc.

Quando útil, pode mostrar:

```text
Conhecimentos aplicados
• Engenharia
• Qualidade
• Suprimentos
```

sem representar troca de identidade/runtime.

## 3. Painel lateral global

Uso cotidiano:

- conversar sem sair do app;
- receber Workspace Context;
- mostrar context chips;
- navegar;
- executar reads/writes governados;
- acompanhar activity;
- mostrar sources/evidence;
- receber Decision Gates;
- criar/abrir Task/Case.

## 4. Página completa

Adequada para:

- análise longa;
- comparação;
- multimodalidade;
- Tasks/Workflows;
- Cases/Evidence Board;
- artifacts;
- histórico.

## 5. Entry points contextuais

Exemplos:

```text
Analisar com Copilot
Explicar indicador
Perguntar sobre cliente
Investigar problema
Criar ação a partir deste resultado
```

Passar `EntityRef`, `EvidenceRef`, `OutcomeRef` ou Workspace Context estruturado; evitar prompts gigantes hardcoded.

## 6. Activity operacional

Mostrar estado verificável, não CoT.

Exemplo:

```text
Investigando reclamação
✓ Produto identificado
✓ Histórico de qualidade consultado
✓ Desenho analisado
○ Consultando lote/OP
○ Aguardando nova revisão
```

## 7. Estados UX

Turn/task/workflow podem usar estados coerentes:

```text
planning
running
waiting_for_input
waiting_for_decision
waiting_for_event
partially_completed
completed
blocked
failed
cancelled
```

Não inventar novo vocabulário incompatível para cada surface.

## 8. Epistemic UX

Distinguir visualmente quando material:

- **Fato**;
- **Cálculo**;
- **Hipótese**;
- **Conclusão**;
- **Recomendação**.

Uma hipótese não deve ter o mesmo tratamento visual de um fato confirmado.

## 9. Evidence/Sources

Permitir expandir:

- source system/document;
- entity;
- timestamp/freshness;
- filtros/período;
- page/region de arquivo quando aplicável;
- confidence/limitations quando aplicável.

Não sobrecarregar resposta simples; progressive disclosure.

## 10. Decision Gate UX

Substitui cartão genérico de “confirmar”.

Pode apresentar:

```text
Ação
Entidade
Mudanças principais
Impacto
Evidence usada
Risco
Gate requerido
```

Ações possíveis dependem do gate:

```text
Entendi
Confirmar / Cancelar
Revisar e confirmar
Aprovar / Rejeitar
```

Não esconder write atrás de texto ambíguo.

## 11. Resultados ricos

Reutilizar render pipeline para:

- texto;
- KPI;
- tabela;
- gráfico;
- árvore;
- cards de entidade;
- timeline;
- checklist;
- evidence board;
- workflow/task progress;
- comparison.

## 12. Suggested actions

Somente capabilities autorizadas:

```text
[Abrir registro]
[Comparar período]
[Investigar como Case]
[Criar solicitação]
[Gerar relatório]
[Acompanhar mudança]
```

Sugestão não significa execução.

## 13. Navigation UX

Quando Copilot navegar:

- activity curta;
- conversa preservada;
- painel permanece quando apropriado;
- Workspace Context atualiza após navegação;
- focus acessível/previsível.

## 14. Context chips

Exemplo:

```text
Portal Comercial
Cliente 000123
Filial 01
Setembro/2026
Caso Q-2026-0042
```

Usuário pode remover contexto não desejado.

Contexto explícito novo vence memória antiga.

## 15. Copilot Task UX

Task card/page mostra:

- objetivo;
- status;
- progresso real;
- steps resumidos;
- pending decisions;
- results/evidence;
- links para app/Case;
- cancel quando permitido.

Task não precisa parecer conversa.

## 16. Copilot Case UX

Case é workspace de investigação/trabalho:

```text
Cabeçalho/objetivo
Entidades relacionadas
Evidence Board
Hipóteses/conclusões
Tasks/Workflows
Decisões/Ações
Timeline
Room
Artifacts
```

Deve deixar claro o que é source data e o que é interpretação do Copilot.

## 17. Interaction Room UX

Room associada a Case pode oferecer:

- conversa humana;
- arquivos;
- menções;
- resumo do Copilot;
- decisões/pending actions;
- link para evidence/entidades.

Resumo não pode revelar source data que o usuário não pode acessar.

## 18. Copilot Inbox UX

Sections possíveis:

```text
Aguardando você
Em andamento
Concluído
Alertas
```

Itens linkam para Task/Case/Decision/Workflow/entity.

Leitura de item nunca executa write implicitamente.

## 19. Watch UX

Usuário deve entender:

- o que está sendo acompanhado;
- condição/gatilho;
- modo `OBSERVE | ADVISE | ACT`;
- prazo/expiração;
- como pausar/desabilitar;
- quais actions ACT poderia executar quando permitido.

ACT requer destaque de autonomia/policy.

## 20. Multimodal UX

Para desenho/documento:

- mostrar arquivo/página/região quando possível;
- destacar findings com confidence/limitation;
- permitir voltar à evidência;
- não fingir leitura de região ilegível.

## 21. Simulation UX

Separar claramente:

```text
Estado atual
Premissas simuladas
Resultado projetado
Limitações
```

Botão `Aplicar` nunca é continuidade implícita; inicia uma Business Action nova e governada.

## 22. Histórico/reload

Após F5:

- conversa permanece conforme persistence atual;
- Task/Case/Workflow recupera status real;
- pending Decision não executa automaticamente;
- completed write não repete;
- Workspace Context é reconstruído/revalidado.

## 23. Correção e feedback

Usuário pode corrigir contexto/entidade/interpretação.

Feedback pode classificar:

- resposta;
- action;
- evidence;
- navigation;
- analysis;
- recommendation.

Feedback alimenta telemetry/evals/candidate improvement, não altera production behavior imediatamente.

## 24. Acessibilidade

- keyboard navigation;
- focus management;
- screen-reader labels;
- status não depende só de cor;
- activity live-region apropriada;
- Decision Gate acessível;
- errors recuperáveis;
- tables/graphs com alternativas textuais quando necessário.

## 25. UX success

O usuário deve conseguir começar por uma pergunta e, quando o problema crescer, evoluir naturalmente:

```text
Turn
→ Task
→ Case
→ Room/Inbox/Watch
```

sem aprender uma coleção de agentes ou trocar de ferramenta mental.