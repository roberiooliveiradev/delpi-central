# 08 — Segurança, autonomia e auditoria

**Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
**Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)

## 1. Invariante principal

```text
Copilot effective permissions ⊆ user effective permissions
```

O Copilot nunca opera como superusuário implícito e nenhuma camada de expertise/contexto/workflow/modalidade/biometria pode ampliar privilégios.

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

Biometric match pode ajudar a resolver `userRef`, mas **não substitui autenticação, Core RBAC, Decision Gate ou autorização final do backend**.

## 3. Trust boundaries

Conteúdo de qualquer uma destas fontes é **dado não confiável para policy/system**:

- user prompt;
- voz/transcrição;
- imagem/câmera/vídeo/tela compartilhada;
- biometric identity candidate;
- human observation result;
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

**L5 empresarial não implica autoridade OT nem autoridade biométrica para substituir identidade/autorização.**

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
biometric_data
human_observation
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
- provider restrictions;
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
- biometric enrollment/revocation quando identity association for material;
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
biometric/human observation metadata
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
- biometric template/media restrictions;
- industrial-data restrictions.

Provider fallback não pode diminuir security/data policy.

## 19. Meeting capture security

Meeting Mode exige sessão de captura explícita.

A UI deve indicar claramente, conforme ativo:

```text
microfone
transcrição
câmera
identity recognition
screen share
raw recording
```

Policy deve distinguir:

```text
transient capture
transcript retention
biometric matching
raw audio retention
raw video retention
screen retention
derived Evidence/artifact retention
```

Participante presente em reunião não autoriza automaticamente persistência ilimitada de mídia ou criação de enrollment biométrico.

## 20. Consentimento e data minimization

Antes de captura persistente ou enrollment biométrico definir:

- finalidade;
- quem iniciou;
- participantes/scope;
- modalidade;
- retenção;
- acesso;
- redaction;
- provider processing;
- delete/anonymize/revoke policy.

Default arquitetural: **reter o mínimo necessário**.

Transcript, Evidence derivada, mídia bruta e biometric template possuem lifecycles distintos.

## 21. Biometric identity security

A capability biométrica segue `54`.

Invariante:

```text
biometric match != authenticated session != permission grant
```

Requisitos mínimos:

- enrollment explícito e revogável;
- closed-set recognition/verification de usuários conhecidos/enrolled;
- unknown/low-confidence não força identidade;
- associação corrigível;
- biometric template protegido e não logado;
- strict server-side access;
- retention/deletion próprios;
- provider allowlist/data-policy;
- audit de enrollment/match/correction/revoke/delete;
- liveness/anti-spoof quando a finalidade exigir confiança adicional;
- nenhum template biométrico exposto ao MFE sem necessidade.

Ações sensíveis nunca usam biometria como único fator de autorização.

## 22. Human Observation boundaries

O Copilot pode analisar comportamentos **observáveis e relacionados ao processo**, como:

- etapa executada/não executada;
- interação com ferramenta/máquina/material;
- repetição/retrabalho;
- tempo entre etapas;
- deslocamento relevante ao fluxo;
- pedido de ajuda;
- postura/ergonomia quando houver método/owner apropriado;
- uso observável de EPI quando formalmente definido.

Por default, é proibido transformar rosto/voz/comportamento em inferências de:

```text
personalidade
honestidade/confiabilidade
intenção moral
lealdade
emoção como truth
saúde/diagnóstico
atributos sensíveis
aptidão profissional global
propensão disciplinar
```

Também é proibido usar biometria/Human Observation como authority automática para contratação, promoção, punição, remuneração, avaliação formal, suspensão ou desligamento.

Evidence operacional pode subsidiar processos humanos separados, mas não é julgamento automático sobre a pessoa.

## 23. Shared device security

Em tablet industrial, terminal, kiosk ou sala compartilhada:

- user atual precisa ser explícito;
- device identity != user identity;
- biometric candidate não mantém sessão indefinidamente;
- ambiguous match exige fallback/confirmation;
- logout/troca de usuário limpa contexto sensível;
- session timeout/lock;
- tokens não permanecem expostos;
- mídia/cache local é minimizada/limpa;
- usuário anterior não pode vazar WorkspaceContext/Conversation/Case para o próximo.

Business Action sempre depende do usuário/authority vigente, não apenas do device ou biometric candidate.

## 24. Industrial/OT safety boundary

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

## 25. Computer vision e qualidade

Imagem/vídeo gerados pelo Copilot são Evidence/Findings com confidence/limitations, salvo capability de inspeção automática explicitamente validada.

Regra default:

```text
visual finding
→ Evidence/Hypothesis
→ official inspection rule/measurement
→ authorized quality decision
```

Não aprovar/reprovar peça apenas pela impressão do LLM quando processo oficial exige medição/equipamento/tolerância distinta.

## 26. Organizational Knowledge safety

Feedback, reunião, observação de operador ou Case resolution não viram production truth automaticamente.

```text
candidate
→ provenance/Evidence
→ review
→ eval
→ publish
```

Decision/Experience record não armazena chain-of-thought.

Não criar perfil secreto persistente de trabalhador como mecanismo de aprendizagem.

## 27. Auditoria

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
copilot.biometric.enrolled|matched|corrected|revoked|deleted
copilot.human_observation.created
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
biometric modality/confidence/model-version when applicable
outcome/evidence refs
duration/error
timestamp/correlation
```

## 28. Dados proibidos em logs/state comuns

- JWT/refresh token;
- API key/password/secrets;
- chain-of-thought;
- full sensitive payload sem necessidade;
- provider credentials;
- raw audio/video/screenshots fora de storage/policy apropriados;
- biometric embeddings/templates em logs;
- raw enrollment media fora de storage/policy específicos;
- hidden person scoring.

## 29. Emergency stop

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
- desabilitar face recognition;
- desabilitar speaker recognition;
- bloquear enrollment biométrico;
- suspender Human Observation;
- bloquear qualquer OT integration separadamente.

## 30. Security success criteria

Segurança está correta quando uma capability autorizada continua útil, mas nenhuma tentativa de prompt/context/pack/event/room/voice/media/device/biometric signal consegue ampliar o que o usuário poderia fazer diretamente pelas regras da plataforma, nem ultrapassar privacy/retention/industrial safety boundaries.

Também deve valer:

```text
biometric identity is bounded, correctable and revocable
unknown remains unknown when confidence is insufficient
no biometric-only permission elevation
no emotion/personality/character inference
no automatic employment decision from biometrics
no hidden worker profiling
```
