# 09 — UX do Minha DELPI Copilot

**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Princípio

O Copilot deve parecer parte da plataforma e do trabalho real, não uma janela de chat isolada. Ao mesmo tempo, ele é uma **aplicação própria**, com MFE e API próprios, hospedada de forma integrada pelo Portal e adaptável a diferentes dispositivos/surfaces.

A linguagem natural é a porta de entrada; texto não é a única modalidade e conversa não é a única surface.

```text
Conversation
+ Context
+ Voice/Media/Biometric Identity when authorized
+ Activity
+ Evidence
+ Decisions
+ Tasks
+ Cases
+ Rooms
+ Inbox
+ Watch
```

## 2. Uma única identidade de produto

A UI não deve exigir que o usuário escolha “Agente Engenharia”, “Agente Qualidade” etc.

Quando útil, pode mostrar conhecimentos aplicados sem representar troca de runtime.

Biometric recognition também não cria uma segunda identidade de produto nem uma nova user authority: apenas sugere/associa `userRef` quando governado.

## 3. Disponibilidade para usuários

A direção de produto é que o entry point do Copilot possa estar presente para usuários autenticados da Minha DELPI conforme rollout/permissão do próprio Copilot.

Presença não implica capability universal.

A UI deve deixar claro quando algo está indisponível por:

- permissão;
- app/contexto;
- policy;
- device;
- modality/provider;
- biometric governance;
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
📷 Câmera: ATIVA
👤 Reconhecimento de participantes: ATIVO
🖥 Tela: INATIVA
⏺ Gravação bruta: INATIVA
```

O usuário deve conseguir ver e alterar, conforme policy:

- modalidades ativas;
- identity recognition ativo/inativo;
- finalidade;
- participantes/contexto;
- retenção quando relevante;
- stop/pause capture.

### Durante a reunião

UX pode combinar:

```text
transcrição ao vivo
participante/speaker associado
confidence/correção quando material
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
Participantes/associações confirmadas
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
Usuário reconhecido: Carlos
Status: identidade confirmada

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

Se biometric match for ambíguo:

```text
Não consegui confirmar quem está usando este posto.

[Sou Carlos]
[Entrar com minha conta]
[Cancelar]
```

Nunca assumir identidade de baixa confiança silenciosamente.

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
- speaker association pode ser mostrada quando habilitada;
- comando material deve confirmar entendimento quando necessário;
- voz não reduz Decision Gate;
- erro de reconhecimento deve ser corrigível;
- em ambiente ruidoso, oferecer fallback touch/text.

## 12. Camera/image UX

Ao ativar câmera:

- indicator persistente;
- finalidade explícita;
- mostrar se face recognition está ativo;
- botão stop;
- snapshot/frame usado pode ser mostrado;
- finding aponta para região quando possível;
- confidence/limitations visíveis quando materiais.

Finding visual de peça/produto e candidate identity de pessoa são resultados distintos e devem ser apresentados separadamente.

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
- usado para identity recognition;
- persistido;
- convertido em Evidence;
- descartado após processamento.

Long video pode mostrar progresso assíncrono em Task/Activity.

## 14. Biometric Identity UX

Quando a capability estiver habilitada, reconhecimento de face/voz deve ser **visível, corrigível e não autoritativo**.

A UI pode mostrar:

```text
Reconhecido como: Carlos Oliveira
Confiança: alta
Fonte: face + sessão atual

[Está correto]
[Não sou eu]
[Trocar usuário]
```

Para baixa confiança:

```text
Não foi possível confirmar sua identidade.

[Selecionar meu usuário]
[Entrar novamente]
```

Regras:

- não mostrar embedding/template;
- não expor lista de candidatos desnecessariamente;
- não criar enrollment automaticamente a partir de uma correção;
- permitir recusar/corrigir association;
- enrollment/revocation ficam em fluxo administrativo/seguro apropriado;
- pessoa não enrolled permanece `Participante N`/`Usuário não confirmado` quando necessário;
- biometric result não deve ser apresentado como “autorizado a executar”.

## 15. Enrollment UX

Se enrollment biométrico for disponibilizado ao usuário/admin autorizado, o fluxo deve explicar:

- modalidade (`face`/`voice`);
- finalidade;
- onde/como o template será usado;
- retenção/revogação;
- necessidade de novas amostras;
- estado `ACTIVE | REVOKED | DELETED`;
- opção de revogar/deletar conforme policy.

Não misturar “tirar foto de perfil” com enrollment biométrico sem decisão explícita.

## 16. Human Observation UX

Quando o Copilot analisar processo humano, apresentar **o que foi observado**, não um julgamento sobre a pessoa.

Bom:

```text
Observação
• etapa 4 foi repetida 3 vezes
• houve 42 s entre as etapas 5 e 6
• o operador solicitou ajuda antes da inspeção

Hipótese de processo
• pode existir dificuldade na montagem do terminal X4
```

Proibido como UX default:

```text
“operador desmotivado”
“pessoa pouco confiável”
“parece nervoso”
“baixo potencial”
```

Não apresentar person score oculto ou ranking derivado de rosto/voz/comportamento.

## 17. Screen share UX

Meeting/Workspace podem permitir screen share quando autorizado.

Indicadores:

- surface compartilhada;
- status on/off;
- redaction warning;
- stop rápido.

Screen share não autoriza o Copilot a clicar/automatizar negócio no DOM.

## 18. Entry points contextuais

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

## 19. Activity operacional

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

Media/biometric activity pode mostrar:

```text
Ouvindo
Transcrevendo
Analisando imagem
Processando vídeo
Reconhecendo participante
Identidade não confirmada
Consultando OP
Aguardando confirmação
```

## 20. Estados UX

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

Identity association usa estados próprios quando exibidos:

```text
unknown
candidate
confirmed
corrected
rejected
```

## 21. Epistemic UX

Distinguir visualmente quando material:

- **Fato**;
- **Cálculo**;
- **Hipótese**;
- **Conclusão**;
- **Recomendação**.

Uma hipótese visual/Human Observation não deve ter o mesmo tratamento de um fato confirmado por medição/regra oficial.

## 22. Evidence/Sources

Permitir expandir:

- source system/document/media;
- entity;
- participant/userRef quando realmente necessário;
- timestamp/freshness;
- filtros/período;
- page/region/frame/time range quando aplicável;
- confidence/limitations;
- transcript segment quando permitido.

Não expor biometric template como Evidence.

## 23. Decision Gate UX

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

Biometric identity pode ajudar a contextualizar o actor, mas Decision Gate usa sessão/actor autenticado.

Não esconder write atrás de texto, voz, gesto ou reconhecimento biométrico ambíguo.

## 24. Resultados ricos

Usar componentes/rendering do próprio Copilot e `@delpi/plugin-ui` quando houver equivalente compartilhado para texto, KPI, tabela, gráfico, árvore, cards de entidade, timeline, checklist, evidence board, workflow/task progress, comparison, transcript, media evidence, meeting decisions/actions e frontline instruction step.

Não importar renderer/component interno de `plugins/minha-delpi-chat` como dependency.

## 25. Suggested actions

Somente capabilities autorizadas. Sugestão não significa execução.

## 26. Navigation UX

Quando Copilot navegar:

- activity curta;
- conversa preservada pela própria Copilot API;
- painel permanece quando apropriado;
- Workspace Context atualiza após navegação;
- focus acessível/previsível.

## 27. Context chips

Contexto administrativo e operacional deve ser removível/corrigível. Contexto explícito novo vence memória antiga.

## 28. Copilot Task UX

Task card/page mostra objetivo, status, progresso real, steps resumidos, pending decisions, results/evidence, links e cancel quando permitido.

Task não precisa parecer conversa.

## 29. Copilot Case UX

Case é workspace de investigação/trabalho e deve deixar claro o que é source data e o que é interpretação do Copilot.

## 30. Interaction Room UX

Room associada a Case pode oferecer conversa humana, arquivos, menções, resumo do Copilot, decisões/pending actions, evidence/entidades e ata relacionada. Resumo respeita source ACL.

## 31. Copilot Inbox UX

Sections possíveis:

```text
Aguardando você
Em andamento
Concluído
Alertas
```

Leitura de item nunca executa write implicitamente.

## 32. Watch UX

Usuário deve entender o que está sendo acompanhado, condição, modo `OBSERVE | ADVISE | ACT`, prazo, pause/disable e actions possíveis. ACT requer destaque de autonomia/policy.

## 33. Multimodal UX

Para desenho/documento/imagem/vídeo:

- mostrar arquivo/página/região/frame/time range quando possível;
- destacar findings com confidence/limitation;
- permitir voltar à evidência;
- não fingir leitura de região ilegível;
- mostrar quando um resultado veio de áudio/transcrição versus API oficial.

## 34. Training/help UX

Frontline pode oferecer modo passo a passo com próxima/repetir/desenho/vídeo/pedir ajuda/registrar problema. Isso não substitui certificação/qualificação oficial.

## 35. Privacy UX

Captura e identity recognition precisam ser observáveis pelo usuário.

Quando material, mostrar:

- finalidade;
- modalidades ativas;
- reconhecimento de identidade ativo/inativo;
- retenção;
- quem poderá acessar;
- se raw media será persistida;
- como encerrar a sessão.

## 36. Shared-device UX

Em terminal compartilhado:

- indicar usuário ativo;
- indicar quando identidade é apenas candidate versus sessão confirmada;
- oferecer logout/troca de usuário rápida;
- limpar conversation/context/media/identity-candidate local ao trocar usuário;
- não mostrar conteúdo do usuário anterior;
- exigir reautenticação quando policy determinar.

## 37. Industrial safety UX

Copilot deve diferenciar claramente orientação, recomendação, solicitação empresarial e comando físico de máquina. Comando físico não faz parte da experiência default.

## 38. Simulation UX

Separar estado atual, premissas simuladas, resultado projetado e limitações. `Aplicar` inicia nova Business Action governada.

## 39. Histórico/reload

Após F5/reload/session resume:

- conversa permanece conforme persistence da Copilot API;
- Task/Case/Workflow recupera status real;
- pending Decision não executa automaticamente;
- completed write não repete;
- Workspace Context é revalidado;
- media capture/identity recognition não reinicia silenciosamente;
- microphone/camera/screen exigem estado/permission explícitos;
- biometric candidate anterior não autentica nova sessão automaticamente;
- ausência do Chat não altera a experiência.

## 40. Correção e feedback

Usuário pode corrigir contexto/entidade/interpretação/transcrição/identity association.

Correção de identidade:

- corrige associação da sessão/evidence;
- não re-enrolla silenciosamente;
- gera telemetry/eval signal;
- respeita revoke/delete policy.

Feedback alimenta telemetry/evals/candidate improvement, não altera production behavior imediatamente.

## 41. Acessibilidade

- keyboard navigation;
- focus management;
- screen-reader labels;
- status não depende só de cor;
- captions/transcript para áudio;
- visual alternative para feedback sonoro;
- large-touch targets para Frontline;
- contraste/legibilidade industrial;
- voice/biometric recognition não podem ser o único meio de executar função crítica.

## 42. UX success

O usuário deve conseguir evoluir naturalmente:

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

Biometric identity, quando ativa, reduz fricção sem virar permission authority; Human Observation aumenta contexto sem transformar o Copilot em avaliador psicológico do trabalhador.
