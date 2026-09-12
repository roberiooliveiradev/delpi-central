# Minha DELPI Copilot — Modelo de Dados, Estado e Persistência

**Status:** target arquitetural; C0.S0 deve mapear modelos/repositories existentes antes de criar migrations.

## 1. Princípio

Persistir somente o necessário para continuidade, auditoria e segurança. Não criar banco paralelo de capabilities nem armazenar chain-of-thought.

## 2. Estados principais

### 2.1 Workspace Context

**Owner primário:** Portal/MFE em runtime.  
**Persistência:** efêmera por padrão; snapshot bounded no turno somente quando necessário para continuidade/auditoria.

Campos conceituais:

```text
version
appId
routeId
entityRefs[]
filters
selection
dateRange
visibleDataRefs[]
source
updatedAt
```

Não persistir:

- estado React inteiro;
- tokens;
- secrets;
- datasets completos;
- valores não usados sem justificativa.

### 2.2 Capability Projection

**Owner:** derivada das authorities canônicas.  
**Persistência:** preferir derivação/cache/index materializado; nunca virar segunda fonte de contrato.

Business:

```text
OpenAPI/Action Catalog → projection
```

Platform:

```text
Core /me/apps + generic platform action definitions → projection
```

Qualquer cache deve carregar provenance/version/hash e ser invalidável.

### 2.3 Workflow Execution

Criar modelo persistido apenas em C4 se o workflow precisar sobreviver a confirmação/reload/timeout.

Campos mínimos conceituais:

```text
workflowId
conversationId
turnId
requestId
userId/subjectRef
planVersion
status
createdAt
updatedAt
currentCheckpoint
```

Status:

```text
planned
running
waiting_confirmation
succeeded
partially_succeeded
failed
cancelled
```

Não persistir raciocínio privado.

### 2.4 Workflow Step

```text
stepId
workflowId
capabilityRef
sourceActionRef quando business action
dependsOn[]
status
attemptCount
idempotencyKey quando aplicável
startedAt
finishedAt
resultRef/errorCode
confirmationRef quando aplicável
```

`resultRef` deve preferir referência/resultado sanitizado, evitando copiar payload sensível inteiro sem necessidade.

### 2.5 Confirmation lifecycle

Campos conceituais:

```text
confirmationId
workflowId/turnId
stepId/actionRef
argumentsHash
preview sanitized
sensitivity
status
requestedAt
expiresAt
decidedAt
decision
```

Status:

```text
pending
confirmed
rejected
expired
invalidated
```

Se os argumentos finais mudarem, `argumentsHash` muda e a confirmação anterior deve ser invalidada.

### 2.6 Audit event

Preferir infraestrutura de observabilidade/auditoria existente.

Registrar quando aplicável:

```text
requestId
workflowId
stepId
user subject
capability/action ref
policy decision
confirmation ref
execution status
duration
result/error classification
timestamp
```

Redigir PII/segredos conforme padrões existentes.

## 3. Estado de conversa

Reutilizar persistence de conversa/turn metadata da AI API.

Possíveis extensões, somente após inventário:

```text
workspaceContextSnapshot
workflowRefs[]
lastEntityRefs[]
pendingConfirmationRefs[]
```

Não duplicar a memória estruturada já existente.

## 4. Idempotência

Writes em workflow precisam de idempotência quando houver retry/reload/replay possível.

Ordem de preferência:

1. idempotency contract nativo da API de domínio;
2. use case de domínio com chave idempotente;
3. proteção coordenada no orchestration layer somente se arquiteturalmente necessária e sem mascarar ausência de garantia no backend.

Nunca assumir que `POST` é seguro para retry.

## 5. Retention e LGPD

Antes de persistir novo dado:

- finalidade;
- base/necessidade operacional;
- retenção;
- minimização;
- acesso;
- auditoria;
- exclusão/anonimização quando aplicável.

Integração deve respeitar documentação de auditoria/LGPD da plataforma.

## 6. Migrations

C0.S0 deve responder:

```text
Existe modelo de workflow atual?
Existe confirmation persistence atual?
Turn metadata já suporta workspace context?
Existe audit event suficiente?
Existe idempotency storage?
```

Somente os `NO` que correspondam a requisito real justificam migration.

## 7. Evolução de schema

Quando migration for necessária:

```text
expand additive
→ deploy reader compatible
→ deploy writer
→ backfill se necessário
→ cutover
→ remover legado em release posterior
```

Toda migration precisa de:

- owner;
- forward path;
- rollback/mitigation;
- indexes;
- constraints;
- testes;
- impacto de volume;
- observabilidade.

## 8. State machine do workflow

```text
PLANNED
  ↓
RUNNING ───────────────→ FAILED
  │
  ├─ needs confirmation → WAITING_CONFIRMATION
  │                         │
  │                         ├─ reject/expire → CANCELLED/FAILED conforme plano
  │                         └─ confirm → RUNNING
  │
  ├─ all required steps ok → SUCCEEDED
  └─ optional/noncritical failure → PARTIALLY_SUCCEEDED
```

Writes críticos não podem ser executados após precondition required falhar.

## 9. State machine de Platform Command

```text
PROPOSED
→ VALIDATED
→ AUTHORIZED_TARGET_RESOLVED
→ EXECUTED
→ SUCCEEDED | REJECTED | FAILED
```

O Portal resolve/revalida o target no instante da execução.

## 10. O que explicitamente não criar

- tabela manual de endpoints do Copilot;
- tabela manual de path→intent;
- cópia persistida do OpenAPI por capability como segunda authority;
- “memory” paralela por app;
- workflow engine separado que duplica planner/executor existentes;
- armazenamento de chain-of-thought;
- credentials/tokens em workflow state.