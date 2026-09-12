# Minha DELPI Copilot — Rollout, Migrações e Implantação

**Status:** plano operacional  
**Princípio:** implantação incremental, reversível e observável. Sem big-bang.

## 1. Estratégia geral

A primeira versão do Copilot não exige um novo microserviço dedicado. Evoluir componentes existentes:

```text
portal
minha-delpi-ai-api
plugins/minha-delpi-chat
Core API
APIs de domínio
MFEs
```

Criar serviço novo somente se uma necessidade técnica mensurável não couber nos owners atuais e houver ADR aprovada.

## 2. Sequência de deployment

### Release R0 — contratos/testes

Sem mudança visível ao usuário.

Entrega:

- schemas/tipos v1;
- harness contratual;
- observabilidade mínima;
- app readiness inventory.

Rollback: remover artefatos não consumidos ou desligar flag com exit criteria.

### Release R1 — navegação Copilot

Entrega:

- authorized Portal Capability Projection;
- CopilotBridge;
- `portal.open_app`;
- `portal.open_route`;
- transport send/stream;
- UX “Abrir no app”.

Disponibilização: cohort interno/canary.

### Release R2 — contexto

Entrega:

- WorkspaceContext;
- Portal Context Store;
- SDK/helper para MFE;
- primeiro MFE piloto;
- contextual explanation/deep navigation.

Rollout por MFE, opt-in.

### Release R3 — reads de negócio

**Pré-condição:** gates relevantes da AI/OpenAPI-first atuais aprovados no candidate vigente.

Entrega:

- Business Capability Projection;
- read parity;
- resultados + deep links;
- app coverage scanner.

Rollout inicialmente read-only.

### Release R4 — writes L3/L4

Entrega:

- prepare-only;
- preview de argumentos;
- confirmation protocol;
- write não destrutivo piloto;
- idempotency/audit.

Não liberar destructive nesta release salvo caso explicitamente aprovado e testado.

### Release R5 — workflows compostos

Entrega:

- DAG;
- partial failure;
- checkpoints;
- persist/reload;
- multi-app read;
- mixed read+write confirmed.

### Release R6 — ecossistema AI-ready

Entrega:

- SDK/templates;
- readiness scanner;
- waves de onboarding;
- coverage dashboard.

### Release R7 — autonomia governada

Entrega gradual L5, se aprovada. OFF por default.

## 3. Feature flags

Feature flag é mecanismo de rollout, não dívida eterna.

Cada flag deve registrar:

```text
name
owner
scope
introducedAt
successCriteria
rollbackTrigger
exitCriteria
plannedRemoval
```

Flags sugeridas conceitualmente — nomes reais somente após inventário das convenções atuais:

```text
copilotPlatformActionsEnabled
copilotWorkspaceContextEnabled
copilotBusinessReadsEnabled
copilotWritePrepareEnabled
copilotConfirmedWritesEnabled
copilotAgenticWorkflowsEnabled
copilotAutonomyL5Enabled
```

Não criar dial por endpoint/app quando uma flag transversal resolve o rollout.

## 4. Migrações de contrato

Preferir mudanças aditivas e versionadas.

Quando contrato persistido precisar mudar:

```text
EXPAND
→ BACKFILL quando necessário
→ DUAL READ somente se inevitável e com exit criteria
→ CUTOVER
→ CONTRACT
```

Não manter dual-write/dual-read indefinidamente.

## 5. Migrações de banco

Criar tabela/coluna somente quando persistência for necessária e owner existente não puder representar o dado.

Possíveis necessidades, a confirmar em C0.S0/C4:

- workflow execution durável;
- step execution state;
- confirmation lifecycle;
- idempotency/audit references.

Antes de criar migration:

1. procurar modelo/repository existente;
2. provar requisito de persistência;
3. definir retention/LGPD;
4. definir rollback;
5. criar migration compatível;
6. testar upgrade e downgrade quando suportado pelo padrão local.

## 6. Ordem de rollout por capacidade

```text
explain
→ navigation
→ context-aware explain
→ read
→ analysis
→ prepare write
→ confirmed write
→ workflow
→ limited autonomy
```

Não inverter esta ordem apenas para demonstrar uma feature visual.

## 7. Cohorts

Rollout deve suportar, conforme infraestrutura vigente:

- ambiente;
- usuário/grupo interno;
- app;
- capability kind;
- autonomy level.

A seleção do cohort não concede permission de negócio. RBAC continua obrigatório.

## 8. Rollback

### Platform Actions

- desabilitar projection/bridge via flag;
- chat volta a responder texto/deep link quando aplicável;
- nenhuma rota do Portal fica inacessível manualmente.

### Workspace Context

- parar publisher/consumer;
- chat continua funcional sem contexto visual.

### Business Actions

- desligar availability no Copilot;
- UI continua operando pela API normalmente.

### Workflows

- impedir novos workflows;
- preservar estado/audit dos em andamento;
- definir política segura para `waiting_confirmation` e `running`.

## 9. Critérios de promoção

Uma release só promove cohort quando:

- tests/contract passam;
- security/RBAC negatives passam;
- error rate dentro do limite definido na própria release;
- audit/traces disponíveis;
- rollback foi testado;
- nenhuma dimensão required relevante está FAIL/INCONCLUSIVE;
- documentação/evidence apontam para o mesmo HEAD.

## 10. Critérios de interrupção

Stop-the-line para:

- execução não autorizada;
- write sem confirmação requerida;
- capability fora do catálogo autorizado;
- URL/action arbitrária criada pelo modelo;
- vazamento de segredo/token;
- duplicação de catálogo técnico como workaround;
- erro de idempotência que duplica write;
- evidência irreproduzível.

## 11. Produção

Antes de release ampla:

```text
canary interno
→ canary por app
→ canary writes L4
→ workflows selecionados
→ análise de métricas/incidentes
→ expansão gradual
```

L5 não faz parte do rollout padrão; requer decisão explícita de governança.