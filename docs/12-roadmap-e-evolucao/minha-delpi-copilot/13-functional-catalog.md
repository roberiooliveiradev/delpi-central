# 13 — Catálogo funcional do Minha DELPI Copilot

**Status:** catálogo funcional temático  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Objetivo

Descrever as capacidades do produto independentemente da fase, sem duplicar a ordem de implementação. A sequência canônica vive em `16-execution-master-plan.md`.

## 2. Conversa e entendimento

- linguagem natural PT-BR;
- pedidos simples/compostos;
- follow-up contextual;
- clarify mínimo;
- entity resolution;
- structured goals;
- memória/references sem chain-of-thought;
- texto e voz como modalidades de entrada.

## 3. Surfaces

```text
GLOBAL
WORKSPACE
MEETING
FRONTLINE
```

Todas usam a mesma Copilot API, identidade, policies e Evidence model.

## 4. Navegação e contexto

- abrir app/rota/entidade;
- selecionar view/aba;
- aplicar filtro visual;
- focus;
- deep link;
- Workspace Context;
- context chips;
- contexto por MFE/iframe;
- contexto operacional via EntityRefs para OP, máquina, produto, lote, operação, posto e material;
- bounded device/session metadata quando necessário.

## 5. Copilot único e especialização

- uma identidade de produto;
- Expertise Packs;
- Domain Playbooks;
- composição cross-domain;
- project preferences;
- unknown pack sem core patch;
- nenhuma capability concedida por expertise.

## 6. Knowledge

- procedimentos/manuais/normas;
- help contextual;
- Reference Knowledge;
- Operational Knowledge;
- Decision Knowledge;
- Experience Knowledge;
- Semantic Knowledge;
- ACL em todas as camadas;
- candidate knowledge a partir de reuniões/processos somente com governance.

## 7. Multimodalidade

- PDF;
- imagem;
- desenho técnico;
- foto de defeito;
- certificados/relatórios;
- áudio/voz;
- câmera;
- vídeo curto;
- screen share quando autorizado;
- OCR/VLM/STT/TTS quando necessário;
- page/region/frame/time-range provenance;
- confidence/limitations;
- media retention/policy refs.

## 8. Voice

- speech-to-text;
- text-to-speech;
- hands-free commands;
- correction/repeat;
- voice activity em Meeting/Frontline;
- mesma policy/Decision Gate do texto.

Voz nunca é bypass de autorização.

## 9. Meeting Mode

- sessão explícita;
- transcrição;
- perguntas por voz/texto;
- consulta de dados reais durante reunião;
- screen/camera/media quando autorizado;
- fatos/decisões/pendências;
- candidate actions;
- ata viva;
- Tasks/Cases/Room linkage;
- retomada na reunião seguinte.

## 10. Meeting artifacts

Ata/meeting artifact pode conter:

```text
participants refs
transcript ref
summary
source data/evidence
decisions
pending topics
candidate actions
confirmed actions
Task/Case refs
```

Ação extraída da fala não é execução automática.

## 11. Frontline Mode

- UI simplificada;
- touch/tablet/kiosk;
- voz hands-free;
- câmera/imagem;
- instrução passo a passo;
- desenho/revisão;
- OP/operação/máquina contextual;
- histórico de qualidade/manutenção;
- registrar ocorrência;
- chamar líder/manutenção/qualidade;
- training assistance;
- degraded fallback quando modalidade não estiver disponível.

## 12. Process learning

- observar processo apenas quando autorizado;
- capturar insight/prática como candidate;
- associar Evidence/context;
- expert/owner review;
- eval/version/publish;
- nunca auto-mudar instrução/processo.

## 13. Evidence e explicabilidade

- SourceRef/EvidenceRef;
- media provenance;
- freshness;
- facts;
- calculations;
- hypotheses;
- conclusions;
- recommendations;
- conflicting evidence;
- source expansion na UX.

## 14. Business Reads

Quando APIs/actions autorizadas existirem:

- produtos/estoque/estrutura;
- comercial;
- suprimentos;
- produção;
- financeiro;
- qualidade;
- engenharia;
- manutenção;
- solicitações;
- demais domínios onboarded.

Concreto = OpenAPI/Action Catalog + RBAC, nunca lista hardcoded deste documento.

## 15. DELPI Business Graph

- canonical EntityRef;
- relações cross-domain;
- authoritative/inferred provenance;
- permission-aware traversal;
- source API fetch;
- depth/cycle budgets;
- sibling relation onboarding;
- ligação de media/evidence/meeting/frontline refs às entities sem replicar master data.

## 16. Análise

- comparar períodos/entidades;
- métricas/cálculos grounded;
- anomalias/tendências quando método suportar;
- causalidade somente com evidence suficiente;
- cross-domain synthesis;
- processo/tempo/ciclo quando dados oficiais sustentarem;
- limitação explícita.

## 17. Recommendations

Próximos passos baseados em:

- goals;
- evidence/outcomes;
- Workspace Context;
- authorized capabilities;
- policy;
- work state.

Sugestão não é execução.

## 18. Business Writes

Conforme API/RBAC/policy:

- criar;
- editar;
- aprovar/rejeitar;
- atribuir;
- comentar;
- cancelar/arquivar;
- iniciar processos;
- registrar ocorrência/solicitação.

Sempre via Business Action, não UI automation.

## 19. Decision Gates

- NO_GATE;
- ACKNOWLEDGE;
- CONFIRM;
- REVIEW_AND_CONFIRM;
- APPROVAL_WORKFLOW;
- BLOCK.

Inclui impact preview, args hash, evidence refs, expiry e revalidation.

## 20. Artefatos

- relatório;
- resumo executivo;
- tabela;
- comunicação/e-mail;
- plano de ação;
- documentação;
- ata de reunião;
- transcript/meeting summary quando permitido;
- apresentação/arquivo quando capability existir.

Artefato não executa business write implicitamente.

## 21. Workflows

- goal/DAG;
- dependencies;
- safe parallel reads;
- Decision Gates;
- retry/idempotency;
- partial failure;
- checkpoints;
- activity;
- cancel/timeout;
- no duplicate write.

## 22. Durable Work

- wait_user;
- wait_approval;
- wait_event;
- wait_time;
- resume após F5/restart;
- event correlation;
- state persistence quando necessário;
- Meeting/Frontline actions podem virar Task/Workflow sem engine paralela.

## 23. Copilot Tasks

- objective;
- progress;
- steps;
- decisions pendentes;
- result/evidence refs;
- meeting/frontline refs quando aplicável;
- links;
- cancel quando suportado.

## 24. Copilot Cases

- investigação longa;
- entity refs;
- Evidence Board;
- hypotheses/decisions/actions;
- Tasks/Workflows;
- timeline;
- Room;
- artifacts;
- meeting/frontline refs;
- lifecycle/resolution/reopen.

## 25. Interaction Rooms

- participantes;
- mensagens;
- arquivos;
- resumo grounded;
- pending actions;
- Case linkage;
- meeting artifact linkage;
- source permissions preservadas.

## 26. Copilot Inbox

- waiting_for_user;
- working;
- completed;
- alerts;
- Decision/Task/Case/Workflow links;
- meeting actions pendentes;
- dedupe/status lifecycle.

## 27. Copilot Watch

- OBSERVE;
- ADVISE;
- ACT.

Com event matching, dedupe, cooldown, expiry, permission revalidation e autonomy policy.

## 28. Event-driven continuity

- resume workflow por evento;
- alertas;
- acompanhar status;
- continuar investigação após dependência externa;
- preferir event source real a polling hardcoded.

## 29. Organizational Knowledge e Governed Learning

- Decision/Experience records;
- Solution Patterns;
- feedback → candidate;
- meeting/process/frontline insight → candidate;
- review/eval/version/publish;
- rollback;
- nunca auto-publicar conversa/correção/observação.

## 30. Expertise Studio

- draft;
- review;
- eval;
- publish;
- deprecate;
- rollback;
- usage/quality telemetry.

Não é criador de agentes.

## 31. Simulation

- baseline;
- assumptions;
- deterministic/domain model owner;
- projected impact;
- limitations;
- `SIMULATE != APPLY`.

## 32. Model Router

Classes conceituais:

```text
FAST
STANDARD
DEEP_REASONING
MULTIMODAL
LONG_CONTEXT
REALTIME_MEDIA quando futuramente justificado
```

Seleção por Compute Policy, data policy, latency/cost e quality requirements.

## 33. Iframes

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Contexto/comandos visuais por bridge seguro; Business Actions por API.

## 34. Autonomia

```text
L0 explain
L1 navigate
L2 read/analyze
L3 prepare
L4 governed execute
L5 explicitly allowlisted autonomy
```

L5 OFF por default.

**Autonomia empresarial não implica comando físico de máquina.**

## 35. Industrial/OT boundary

Default:

```text
Copilot observa/consulta/explica/recomenda
Copilot prepara ação empresarial
Copilot -X→ comando físico arbitrário
```

Qualquer future machine control exige safety gate separado, deterministic adapters, interlocks independentes, authorization e audit.

## 36. Privacy/media governance

- visible capture state;
- purpose;
- consent/policy;
- class-specific retention;
- data minimization;
- shared-device session isolation;
- no implicit facial recognition/emotion detection;
- no hidden worker surveillance.

## 37. Administração

- capability/action coverage;
- app readiness;
- expertise/playbooks;
- knowledge lifecycle;
- Task/Case/Workflow;
- Decision Gates;
- Watch;
- media providers/session budgets;
- meeting/frontline coverage;
- model usage/cost;
- failures/retries;
- privacy/retention;
- safe execution;
- audit;
- rollout/kill switch.

## 38. Onboarding AI-ready

```text
L1 discoverable
L2 context-ready
L3 read-ready
L4 write-ready
L5 workflow-ready
```

Novo app entra por shared contracts sem patch central.

Frontline-ready pode ainda exigir device/context/media requirements próprios sem alterar os níveis AI-ready de negócio.

## 39. Fora do padrão

- DOM automation para substituir API;
- browser/cross-origin hacks;
- bypass de permission;
- endpoint selector hardcoded;
- chain-of-thought persistence;
- agent engine por departamento;
- Business Graph duplicando bancos;
- confirmation system paralelo ao Decision Gate;
- automatic production learning por feedback;
- hidden audio/video capture;
- raw-media retention sem policy;
- facial/emotion surveillance por default;
- arbitrary LLM→machine control;
- qualidade automática baseada apenas em impressão visual não validada.

## 40. Experiência final

O usuário deve sentir que o Copilot:

```text
sabe onde estou
+ entende o objetivo
+ entende quando falo/mostro algo
+ encontra entidades/fontes corretas
+ aplica conhecimento especializado
+ mostra evidence
+ navega e executa com governança
+ acompanha trabalho ao longo do tempo
+ participa de reuniões de forma transparente
+ ajuda o operador no trabalho real
+ colabora com pessoas
+ aprende somente por processo governado
+ respeita minhas permissões e privacidade
```
