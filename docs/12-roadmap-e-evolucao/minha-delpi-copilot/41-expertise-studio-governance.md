# Minha DELPI Copilot — Expertise Studio

**Status:** arquitetura de administração proposta  
**Objetivo:** permitir que conhecimento especializado e playbooks evoluam com governança, testes e versionamento sem recriar agentes.

## 1. Conceito

`Expertise Studio` é a superfície administrativa para gerenciar:

- Expertise Packs;
- Domain Playbooks;
- terminology/glossary;
- knowledge scopes;
- schemas de saída;
- exemplos positivos/negativos;
- eval datasets;
- lifecycle/versionamento;
- owners/reviewers.

Ele **não é um criador de agentes**.

## 2. Lifecycle

```text
DRAFT
→ REVIEW
→ TESTING
→ APPROVED
→ PUBLISHED
→ DEPRECATED
→ RETIRED
```

Nenhuma edição publicada entra em produção sem nova versão/candidate e gates aplicáveis.

## 3. Roles

Exemplos:

```text
Expertise Author
Domain Reviewer
AI/Platform Reviewer
Security Reviewer quando necessário
Publisher/Admin
```

RBAC administrativo não concede permissões de negócio ao Copilot.

## 4. Editor de Expertise Pack

Campos conceituais:

```text
key/version
label/description
domain tags
applicability signals
methodology/guidance
required/desired evidence
knowledge scopes
playbook refs
output schema refs
multimodal requirements
limitations
examples
eval refs
owner/reviewers
```

Proibido usar o Studio para cadastrar manualmente path/method/operationId como catálogo de APIs.

## 5. Editor de Playbook

Deve permitir descrever:

- objetivo;
- etapas metodológicas;
- evidence requirements;
- decision points;
- completion criteria;
- optional/required steps;
- outputs esperados;
- applicable expertise;
- rules/owners;
- eval cases.

Playbook não deve conter executor HTTP específico.

## 6. Preview/Simulation

Antes de publicar:

- mostrar conteúdo compilado que será consumido pelo runtime;
- executar casos de teste;
- comparar versão atual vs candidata;
- detectar regressões;
- medir token/context footprint;
- validar schemas;
- revisar references inexistentes.

## 7. Eval gate

Cada Pack/Playbook material precisa de:

```text
positive cases
sibling cases
negative/not-applicable cases
compound cases quando relevante
safety cases
expected structured output
```

Para multimodal: incluir documentos/desenhos de teste representativos e licença/uso apropriados.

## 8. Versionamento

SemVer ou esquema equivalente:

- PATCH: correção sem mudança de contrato;
- MINOR: nova orientação/método compatível;
- MAJOR: mudança material de output/processo/semântica.

Runtime/audit deve registrar versão efetivamente utilizada.

## 9. Rollout

```text
published candidate
→ internal users
→ domain canary
→ metrics/review
→ wider rollout
```

Rollback para versão anterior deve ser suportado.

## 10. Diff semântico

A UI deve destacar alterações em:

- metodologia;
- evidence requirements;
- outputs;
- applicable scopes;
- safety/limitations;
- linked playbooks/knowledge.

## 11. Métricas por versão

- selection precision;
- task completion;
- correction rate;
- evidence coverage;
- clarification efficiency;
- expert approval rate;
- latency/token impact;
- unsafe/blocked outcomes.

## 12. Governed Learning integration

Feedback não publica automaticamente mudanças.

O Studio recebe sugestões como:

```text
candidate improvement
→ author accepts/edits
→ eval
→ review
→ publish
```

## 13. Não fazer

- permitir prompt arbitrário publicado sem review;
- tratar Expertise como permission;
- criar agentId por expertise;
- guardar secrets no conteúdo;
- acoplar método a endpoint técnico específico;
- publicar porque um exemplo manual funcionou.

## 14. Primeiro MVP

Pode começar como administração técnica/versionada sem UI completa:

- storage/repository;
- schemas;
- CLI/admin endpoints;
- tests/evals;
- version lifecycle.

UI Studio vem depois sem mudar o contrato canônico.