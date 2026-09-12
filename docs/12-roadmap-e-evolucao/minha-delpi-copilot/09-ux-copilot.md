# 09 — UX do Minha DELPI Copilot

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Princípio

O Copilot deve parecer parte da plataforma e do trabalho real, não uma janela de chat isolada. Ao mesmo tempo, ele é uma **aplicação própria**, com MFE e API próprios, hospedada de forma integrada pelo Portal e adaptável a diferentes dispositivos/surfaces.

A linguagem natural é a porta de entrada; texto não é a única modalidade e conversa não é a única surface.

```text
Conversation
+ Context
+ Voice/Media when authorized
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

## 3. Disponibilidade para usuários

A direção de produto é que o entry point do Copilot possa estar presente para usuários autenticados da Minha DELPI conforme rollout/permissão do próprio Copilot.

Presença não implica capability universal.

A UI deve deixar claro quando algo está indisponível por:

- permissão;
- app/contexto;
- policy;
- device;
- modality/provider;
- safety restriction.

## 4. Surfaces

O mesmo MFE/runtime deve poder materializar experiências distintas:

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

Nenhuma surface cria segundo product state ou segundo planner.

## 5. Painel lateral global

Uso cotidiano:

- conversar sem sair do app;
- receber Workspace Context;
- mostrar context chips;
- navegar;
- executar reads/writes governados;
- acompanhar activity;
- mostrar sources/evidence;
- receber Decision Gates;
- criar/abrir Task/Case;
- anexar imagem/documento ou usar voz quando autorizado.

O painel é uma **surface do mesmo `plugins/minha-delpi-copilot`**, hospedada pelo Portal.

## 6. Página completa / Workspace

Adequada para:

- análise longa;
- comparação;
- multimodalidade;
- Tasks/Workflows;
- Cases/Evidence Board;
- artifacts;
- histórico;
- meeting/frontline history quando autorizado;
- administração.

A página completa usa o mesmo MFE, a mesma Copilot API, a mesma sessão/contexto e os mesmos contracts do painel global.

## 7. Meeting Mode UX

Meeting Mode é iniciado explicitamente.

Exemplo de cabeçalho:

```text
Minha DELPI Copilot — Reunião
Revisão diária de produção

🎤 Microfone: ATIVO
📝 Transcrição: ATIVA
📷 Câmera: INATIVA
🖥 Tela: INATIVA
⏺ Gravação bruta: INATIVA
```

O usuário deve conseguir ver e alterar, conforme policy:

- modalidades ativas;
- finalidade;
- participantes/contexto;
- retenção quando relevante;
- stop/pause capture.

### Durante a reunião

UX pode combinar:

```text
transcrição ao vivo
respostas do Copilot
dados/gráficos consultados
lista de decisões
pendências
ações candidatas
sources/evidence
```

O Copilot deve conseguir responder por voz/texto sem esconder a origem dos dados.

## 8. Ata viva

Ao encerrar, Meeting Mode pode oferecer:

```text
Resumo
Dados consultados
Decisões confirmadas
Pendências
Ações propostas
Responsáveis/prazos
Sources/Evidence
```

Cada ação proposta deve ter estado explícito:

```text
PROPOSTA
CONFIRMADA
CRIADA/EXECUTADA
FALHOU
```

Exemplo:

```text
[ ] Revisar sensor da Prensa 04
Responsável sugerido: João
Prazo sugerido: 13/09

[Revisar]
[Criar Task]
[Descartar]
```

Ata não executa Business Action implicitamente.

## 9. Frontline Mode UX

Frontline prioriza uso no posto de trabalho.

Características:

- componentes grandes;
- fluxo simples;
- alto contraste;
- poucas ações simultâneas;
- voz hands-free;
- leitura curta;
- feedback sonoro/visual;
- desenho/imagem em destaque;
- tolerância a ruído/latência/degraded mode;
- suporte a touch/tablet/kiosk conforme hardware.

Exemplo:

```text
Bom dia, Carlos

OP 583922
Produto 90264238
Operação 30 — Crimpagem
Máquina PRESS-04

[ INICIAR / CONTINUAR ASSISTÊNCIA ]

🎤 Perguntar ao Copilot
📷 Mostrar problema
📄 Abrir desenho
⚠ Registrar ocorrência
🛠 Chamar manutenção
```

## 10. Contexto operacional visível

Frontline deve exibir context chips simples e corrigíveis:

```text
OP 583922
PRESS-04
Produto 90264238 · Rev. F
Operação 30
```

Esses elementos vêm de `WorkspaceContext`/`EntityRef`, não de inferência visual isolada.

Usuário deve poder corrigir entidade errada antes de uma ação material.

## 11. Voice UX

Comandos/falas comuns:

```text
“próxima etapa”
“repete”
“mais devagar”
“abra o desenho”
“qual medida devo conferir?”
“isso já aconteceu?”
“registre um problema”
“chame o líder”
```

Regras:

- transcript parcial pode ser mostrado;
- comando material deve confirmar entendimento quando necessário;
- voz não reduz Decision Gate;
- erro de reconhecimento deve ser corrigível;
- em ambiente ruidoso, oferecer fallback touch/text.

## 12. Camera/image UX

Ao ativar câmera:

- indicator persistente;
- finalidade explícita;
- botão stop;
- snapshot/frame usado pode ser mostrado;
- finding aponta para região quando possível;
- confidence/limitations visíveis quando materiais.

Exemplo:

```text
Possível desalinhamento — confiança moderada
Região: terminal X4

Não confirmado como defeito.
Plano de controle exige inspeção da característica 27.

[Ver desenho]
[Ver característica]
[Registrar ocorrência]
```

## 13. Video UX

Progressive capability:

```text
imagem
→ vídeo curto
→ sessão assistida com amostragem
→ realtime avançado
```

Usuário deve saber se o vídeo está:

- apenas sendo processado;
- persistido;
- convertido em Evidence;
- descartado após processamento.

Long video pode mostrar progresso assíncrono em Task/Activity.

## 14. Screen share UX

Meeting/Workspace podem permitir screen share quando autorizado.

Indicadores:

- surface compartilhada;
- status on/off;
- redaction warning;
- stop rápido.

Screen share não autoriza o Copilot a clicar/automatizar negócio no DOM.

## 15. Entry points contextuais

Exemplos:

```text
Analisar com Copilot
Explicar indicador
Perguntar sobre cliente
Investigar problema
Criar ação a partir deste resultado
Perguntar por voz
Mostrar problema com câmera
Iniciar reunião assistida
Iniciar assistência Frontline
```

Passar `EntityRef`, `EvidenceRef`, `OutcomeRef` ou Workspace Context estruturado; evitar prompts gigantes hardcoded.

## 16. Activity operacional

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

Media activity também pode mostrar:

```text
Ouvindo
Transcrevendo
Analisando imagem
Processando vídeo
Consultando OP
Aguardando confirmação
```

## 17. Estados UX

Turn/task/workflow/media session podem usar estados coerentes:

```text
planning
running
capturing
processing
waiting_for_input
waiting_for_decision
waiting_for_event
partially_completed
completed
blocked
failed
cancelled
```

Não inventar vocabulário incompatível para cada surface.

## 18. Epistemic UX

Distinguir visualmente quando material:

- **Fato**;
- **Cálculo**;
- **Hipótese**;
- **Conclusão**;
- **Recomendação**.

Uma hipótese visual não deve ter o mesmo tratamento de um fato confirmado por medição.

## 19. Evidence/Sources

Permitir expandir:

- source system/document/media;
- entity;
- timestamp/freshness;
- filtros/período;
- page/region/frame/time range quando aplicável;
- confidence/limitations;
- transcript segment quando permitido.

Não sobrecarregar resposta simples; progressive disclosure.

## 20. Decision Gate UX

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

Não esconder write atrás de texto, voz ou gesto ambíguo.

## 21. Resultados ricos

Usar componentes/rendering do próprio Copilot e `@delpi/plugin-ui` quando houver equivalente compartilhado para:

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
- comparison;
- transcript;
- media evidence;
- meeting decisions/actions;
- frontline instruction step.

Não importar renderer/component interno de `plugins/minha-delpi-chat` como dependency.

## 22. Suggested actions

Somente capabilities autorizadas:

```text
[Abrir registro]
[Comparar período]
[Investigar como Case]
[Criar solicitação]
[Gerar relatório]
[Acompanhar mudança]
[Chamar manutenção]
[Registrar ocorrência]
```

Sugestão não significa execução.

## 23. Navigation UX

Quando Copilot navegar:

- activity curta;
- conversa preservada pela própria Copilot API;
- painel permanece quando apropriado;
- Workspace Context atualiza após navegação;
- focus acessível/previsível.

## 24. Context chips

Exemplo administrativo:

```text
Portal Comercial
Cliente 000123
Filial 01
Setembro/2026
Caso Q-2026-0042
```

Exemplo operacional:

```text
Produção
OP 583922
PRESS-04
Produto 90264238
Operação 30
```

Usuário pode remover/corrigir contexto não desejado.

Contexto explícito novo vence memória antiga.

## 25. Copilot Task UX

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

## 26. Copilot Case UX

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
Meeting refs
Frontline session refs quando autorizados
```

Deve deixar claro o que é source data e o que é interpretação do Copilot.

## 27. Interaction Room UX

Room associada a Case pode oferecer:

- conversa humana;
- arquivos;
- menções;
- resumo do Copilot;
- decisões/pending actions;
- link para evidence/entidades;
- ata/meeting artifact relacionado.

Resumo não pode revelar source data que o usuário não pode acessar.

## 28. Copilot Inbox UX

Sections possíveis:

```text
Aguardando você
Em andamento
Concluído
Alertas
```

Itens linkam para Task/Case/Decision/Workflow/entity/meeting artifact.

Leitura de item nunca executa write implicitamente.

## 29. Watch UX

Usuário deve entender:

- o que está sendo acompanhado;
- condição/gatilho;
- modo `OBSERVE | ADVISE | ACT`;
- prazo/expiração;
- como pausar/desabilitar;
- quais actions ACT poderia executar quando permitido.

ACT requer destaque de autonomia/policy.

## 30. Multimodal UX

Para desenho/documento/imagem/vídeo:

- mostrar arquivo/página/região/frame/time range quando possível;
- destacar findings com confidence/limitation;
- permitir voltar à evidência;
- não fingir leitura de região ilegível;
- mostrar quando um resultado veio de áudio/transcrição versus API oficial.

## 31. Training/help UX

Frontline pode oferecer modo passo a passo:

```text
✓ etapa 1
✓ etapa 2
→ etapa 3 atual
○ etapa 4
```

Usuário pode:

```text
[Próxima]
[Repetir]
[Mostrar desenho]
[Ver vídeo]
[Pedir ajuda]
[Registrar problema]
```

Isso não substitui certificação/qualificação oficial.

## 32. Privacy UX

Captura precisa ser observável pelo usuário.

Não usar câmera/microfone ocultos.

Quando material, mostrar:

- finalidade;
- retenção;
- quem poderá acessar;
- se raw media será persistida;
- como encerrar a sessão.

## 33. Shared-device UX

Em terminal compartilhado:

- indicar usuário ativo;
- oferecer logout/troca de usuário rápida;
- limpar conversation/context local ao trocar usuário;
- não mostrar conteúdo do usuário anterior;
- exigir reautenticação quando policy determinar.

## 34. Industrial safety UX

Copilot deve diferenciar claramente:

```text
orientação
recomendação
solicitação empresarial
comando físico de máquina
```

Comando físico não faz parte da experiência default.

Qualquer futura integração OT deve ter UI própria, status de machine/safety preconditions e confirmation/policy específicos.

## 35. Simulation UX

Separar claramente:

```text
Estado atual
Premissas simuladas
Resultado projetado
Limitações
```

Botão `Aplicar` nunca é continuidade implícita; inicia uma Business Action nova e governada.

## 36. Histórico/reload

Após F5/reload/session resume:

- conversa permanece conforme persistence da **Copilot API**;
- painel e página completa convergem para o mesmo estado autorizado;
- Task/Case/Workflow recupera status real do backend do Copilot;
- pending Decision não executa automaticamente;
- completed write não repete;
- Workspace Context é reconstruído/revalidado pelo Portal;
- media capture não reinicia silenciosamente;
- microphone/camera/screen exigem estado/permission explícitos;
- ausência do Minha DELPI Chat não altera a experiência do Copilot.

## 37. Correção e feedback

Usuário pode corrigir contexto/entidade/interpretação/transcrição.

Feedback pode classificar:

- resposta;
- action;
- evidence;
- navigation;
- analysis;
- recommendation;
- transcript;
- visual finding;
- meeting summary;
- frontline guidance.

Feedback alimenta telemetry/evals/candidate improvement, não altera production behavior imediatamente.

## 38. Acessibilidade

- keyboard navigation;
- focus management;
- screen-reader labels;
- status não depende só de cor;
- activity live-region apropriada;
- Decision Gate acessível;
- errors recuperáveis;
- tables/graphs com alternativas textuais;
- captions/transcript para áudio;
- visual alternative para feedback sonoro;
- large-touch targets para Frontline;
- contraste/legibilidade em ambiente industrial;
- voice não pode ser o único meio de executar função crítica.

## 39. UX success

O usuário deve conseguir começar por uma pergunta e, quando o problema crescer, evoluir naturalmente:

```text
Turn
→ Task
→ Case
→ Room/Inbox/Watch
```

ou mudar de modalidade/surface:

```text
texto ↔ voz ↔ imagem/vídeo
Global ↔ Workspace ↔ Meeting ↔ Frontline
```

sem aprender uma coleção de agentes, trocar de runtime ou perder governança/contexto.