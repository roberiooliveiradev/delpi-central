# 08 — Segurança, autonomia e auditoria

**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)

## 1. Invariante principal

```text
Copilot effective permissions ⊆ user effective permissions
```

O Copilot nunca opera como superusuário implícito e nenhuma camada de expertise/contexto/workflow/modalidade pode ampliar privilégios.

## 2. Fluxo de autorização

```text
identity
→ Core effective permissions
→ authorized capability/action set
→ planner restrito
→ policy/risk/sensitivity
→ Decision Gate quando necessário
→ executor
→ backend revalidation
→ outcome/audit
```

Backend/domain API continua authority final do write.

## 3. Trust boundaries

Conteúdo de qualquer uma destas fontes é **dado não confiável para policy/system**:

- user prompt;
- voz/transcrição;
- imagem/câmera/vídeo/tela compartilhada;
- Workspace Context;
- device/session metadata;
- iframe;
- RAG;
- Expertise Pack/Playbook content;
- API/tool output;
- PDF/imagem/desenho;
- Room message/file;
- Event payload;
- organizational experience records.

Nenhum deles altera:

- permissions;
- system instructions;
- Decision Gate requirements;
- allowed actions;
- autonomy level;
- retention/privacy policy;
- industrial safety boundaries.

## 4. Níveis de autonomia

| Nível | Comportamento |
|---|---|
| L0 | explicar |
| L1 | navegar |
| L2 | consultar/analisar |
| L3 | preparar alteração |
| L4 | executar com Decision Gate conforme policy |
| L5 | auto-executar capability explicitamente allowlisted dentro de limites |

L5 é OFF por default.

**L5 empresarial não implica autoridade OT.** Comando físico de máquina exige governance industrial separada.

## 5. Sensitivity/risk

Classes podem incluir:

```text
read
write
sensitive_write
admin
destructive
external_communication
financial
personal_data
biometric_or_surveillance_sensitive
media_capture
industrial_safety
```

A classificação final deve ser owner/policy server-side e pode definir:

- gate level;
- autonomy ceiling;
- audit strength;
- redaction;
- approver requirements;
- volume/value limits;
- capture/retention rules;
- industrial safety restrictions.

## 6. Decision Gates

Modelo único:

```text
NO_GATE
ACKNOWLEDGE
CONFIRM
REVIEW_AND_CONFIRM
APPROVAL_WORKFLOW
BLOCK
```

Decision request deve vincular, quando material:

- action/capability ref;
- arguments hash;
- impact preview;
- evidence refs;
- risk/sensitivity;
- expiry;
- actor/approver scope.

Mudança material de payload, evidence, permission ou policy pode invalidar decisão anterior.

## 7. TOCTOU e revalidação

Revalidar antes de execute/resume/Watch ACT porque podem mudar:

- permissions;
- entity state/version;
- policy;
- provider availability;
- evidence freshness;
- approver validity;
- media session/consent state;
- device/user session;
- machine/process state quando houver integração industrial.

## 8. Capability minimization

O planner recebe somente candidates necessários/autorizados.

Expertise pode **recomendar** uma capability, mas disponibilidade vem do set autorizado.

Project preference/context também não concede capability.

## 9. Knowledge security

Knowledge scopes passam por ACL independente da expertise.

Proibido:

```text
pack selecionado → liberar documentos do departamento
```

Correto:

```text
pack selecionado
+ user ACL
→ permitted knowledge candidates
```

## 10. Business Graph security

Traversal não pode vazar nó/edge não autorizado.

Regras:

- relationship source/provenance;
- permission-aware traversal;
- source fetch revalidado;
- graph cache não vira bypass de API/RBAC;
- inferred relation não tratada como authoritative.

## 11. Case/Room/Inbox security

- membership de Case/Room não concede automaticamente source entity access;
- summary respeita ACL;
- usuário removido perde acesso conforme owner/policy;
- Inbox sanitiza item cuja source deixou de ser autorizada;
- abrir/ler Inbox não dispara write.

## 12. Durable Workflow security

Em waits/restart/resume:

- revalidar identity/permission/policy;
- proteger duplicate resume/event;
- garantir idempotency para write;
- tratar ambiguous outcome;
- bloquear step dependente quando precondition crítica falha;
- respeitar cancellation/expiry.

## 13. Watch/Event security

Watch modes:

```text
OBSERVE
ADVISE
ACT
```

ACT exige explicit autonomy policy e Decision Gate quando aplicável.

Event payload:

- schema validated;
- deduped;
- correlated;
- tratado como dado não confiável;
- não concede permission.

## 14. Iframe security

Obrigatório:

- origin allowlist;
- `event.source` validation;
- app/session/protocol/version validation;
- schema validation;
- bounded payload;
- no JWT/refresh token;
- visual capabilities não viram Business Actions.

## 15. Prompt/tool/document/media/event injection

Testar injection a partir de:

```text
user
voice transcript
RAG
tool/API
Workspace Context
device/session metadata
iframe
Expertise Pack
Playbook
PDF/image
camera/video/screen
Room message/file
Event payload
Experience Knowledge
```

Resultado esperado: nenhuma fonte de dados altera policy/system/RBAC/retention/safety boundary.

## 16. URLs e HTTP

LLM não produz URL arbitrária para executor.

Business URL/method/schema vêm do provider/action canônico. Platform navigation resolve IDs autorizados via Portal.

## 17. Idempotência/concurrency

Preferência:

1. domain API idempotency;
2. domain use case protection;
3. orchestration dedupe/locking somente quando necessário.

Proibido retry cego de write.

## 18. Model/provider data policy

Model Router futuro deve respeitar:

- data classification;
- provider allowlist;
- residency/privacy constraints;
- model capability;
- retention policy;
- cost/latency budgets;
- media modality/provider terms;
- industrial-data restrictions.

Provider fallback não pode diminuir security/data policy.

## 19. Meeting capture security

Meeting Mode exige sessão de captura explícita.

A UI deve indicar claramente, conforme ativo:

```text
microfone
transcrição
câmera
screen share
raw recording
```

Policy deve distinguir:

```text
transient capture
transcript retention
raw audio retention
raw video retention
screen retention
derived Evidence/artifact retention
```

Participante presente em reunião não autoriza automaticamente persistência ilimitada de mídia.

## 20. Consentimento e data minimization

Antes de captura persistente definir:

- finalidade;
- quem iniciou;
- participantes/scope;
- modalidade;
- retenção;
- acesso;
- redaction;
- provider processing;
- delete/anonymize policy.

Default arquitetural: **reter o mínimo necessário**.

Transcript e Evidence derivada podem ter lifecycle distinto de áudio/vídeo bruto.

## 21. Shared device security

Em tablet industrial, terminal, kiosk ou sala compartilhada:

- user atual precisa ser explícito;
- device identity != user identity;
- logout/troca de usuário limpa contexto sensível;
- session timeout/lock;
- tokens não permanecem expostos;
- mídia/cache local é minimizada/limpa;
- usuário anterior não pode vazar WorkspaceContext/Conversation/Case para o próximo.

Business Action sempre depende do usuário/authority vigente, não apenas do device.

## 22. Privacidade Frontline

Por default, Frontline não inclui:

- reconhecimento facial;
- emotion detection;
- identificação biométrica implícita;
- scoring oculto de produtividade individual;
- gravação contínua sem purpose/policy;
- reutilização de vídeo para finalidade diferente sem governance.

Analytics de processo/pessoa exige requisitos específicos, transparência e owner apropriado.

## 23. Industrial/OT safety boundary

Copilot não é safety controller.

Proibido como arquitetura default:

```text
LLM → comando livre → PLC/CNC/robô/máquina
```

Capability empresarial L4/L5 não concede operação física.

Qualquer futura atuação OT exige gate separado com, no mínimo:

```text
industrial owner
command allowlist/schema
deterministic adapter
machine state/precondition validation
human authorization as required
safety PLC/interlocks independent of Copilot
simulation/test environment
fail-safe/kill switch
audit
risk assessment
```

LLM nunca substitui interlock, safety PLC ou lógica certificada.

## 24. Computer vision e qualidade

Imagem/vídeo gerados pelo Copilot são Evidence/Findings com confidence/limitations, salvo capability de inspeção automática explicitamente validada.

Regra default:

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/measurement
→ authorized quality decision
```

Não aprovar/reprovar peça apenas pela impressão do LLM quando processo oficial exige medição/equipamento/tolerância distinta.

## 25. Organizational Knowledge safety

Feedback, reunião, observação de operador ou Case resolution não viram production truth automaticamente.

```text
candidate
→ provenance/Evidence
→ review
→ eval
→ publish
```

Decision/Experience record não armazena chain-of-thought.

## 26. Auditoria

Eventos conceituais:

```text
copilot.plan.created
copilot.capability.selected
copilot.expertise.selected
copilot.decision.requested|decided
copilot.action.started|completed|failed
copilot.workflow.state_changed
copilot.task.state_changed
copilot.case.state_changed
copilot.watch.triggered
copilot.navigation.executed
copilot.media.session_started|stopped
copilot.media.ingested|deleted
copilot.meeting.started|ended
copilot.meeting.artifact_created
copilot.frontline.session_started|ended
copilot.knowledge_candidate.created
copilot.ot_command.blocked
```

Campos úteis:

```text
actor/subject
request/conversation/turn
workflow/task/case
meeting/frontline/media session refs
entity refs
capability/action
expertise/playbook refs
policy/Decision Gate
consent/retention class refs
outcome/evidence refs
duration/error
timestamp/correlation
```

## 27. Dados proibidos em logs/state

- JWT/refresh token;
- API key/password/secrets;
- chain-of-thought;
- full sensitive payload sem necessidade;
- provider credentials;
- raw audio/video/screenshots fora de storage/policy apropriados;
- biometric templates sem iniciativa explicitamente aprovada.

## 28. Emergency stop

Deve ser possível, conforme owner:

- desabilitar Copilot writes;
- desabilitar provider/action;
- read-only mode;
- desabilitar Watch ACT;
- suspender workflow class;
- revogar iframe integration;
- desabilitar expertise/playbook version problemática;
- desabilitar provider/model por data policy/incidente;
- desabilitar voice/video/media capture;
- encerrar realtime media sessions;
- bloquear Frontline/Meeting Mode por incidente;
- bloquear qualquer OT integration separadamente.

## 29. Security success criteria

Segurança está correta quando uma capability autorizada continua útil, mas nenhuma tentativa de prompt/context/pack/event/room/voice/media/device consegue ampliar o que o usuário poderia fazer diretamente pelas regras da plataforma, nem ultrapassar privacy/retention/industrial safety boundaries.