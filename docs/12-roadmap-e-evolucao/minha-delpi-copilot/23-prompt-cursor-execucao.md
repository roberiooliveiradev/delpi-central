# Prompt mestre — Cursor — Minha DELPI Copilot

Copie este documento para o Cursor ou instrua o Cursor a lê-lo diretamente antes de executar a iniciativa.

---

Você deve implementar o **Minha DELPI Copilot** de forma incremental, seguindo integralmente a documentação canônica do repositório e sem criar arquitetura paralela.

## Fonte de verdade

Leia obrigatoriamente antes de qualquer alteração:

1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`
2. `.cursor/rules/development-standards-index.mdc`
3. regras `.cursor` aplicáveis a planning, execution, tests, security, OpenAPI, AI e Clean Architecture
4. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`
5. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md`
6. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md`
7. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/18-app-onboarding-matrix.md`
8. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/19-rollout-and-migrations.md`
9. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md`
10. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md`
11. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/22-cursor-execution-protocol.md`
12. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md`
13. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md`

Também leia a documentação vigente de `minha-delpi-ai-api`, Portal/Core e do componente específico que estiver sendo alterado.

## Missão

Construir o Copilot como uma segunda interface operacional da Minha DELPI:

```text
usuário
→ linguagem natural
→ goals/subtasks
→ capabilities autorizadas
→ plano operacional
→ policy/RBAC/confirmation
→ execução
→ observação
→ análise/síntese
→ navegação/resultado
```

O Copilot deve explicar, consultar, analisar, navegar e executar tudo que estiver representado por capabilities autorizadas, sempre respeitando os mesmos contratos e permissões da UI.

## Arquitetura obrigatória

```text
Business Actions
→ OpenAPI + Action Catalog
→ validator/policy/confirmation
→ executor genérico existente

Platform Actions
→ /me/apps + Portal authorized routes
→ Platform Capability Projection
→ typed PlatformCommand
→ CopilotBridge
→ Router/MFE

Workspace Context
→ MFE publisher
→ Portal context store
→ bounded structured turn context

Agentic workflows
→ goals/DAG
→ capabilities existentes
→ mesmos executors/policies
```

### Não criar

- segundo motor de IA/planner/tools;
- catálogo manual central de endpoints;
- lista manual de app→URL para o Copilot;
- selector por endpoint/provider;
- path/operationId hardcoded para semântica;
- DOM automation quando existe API/use case;
- permission model próprio do Copilot;
- workflow HTTP executor paralelo;
- memória paralela por app;
- chain-of-thought persistida;
- agente independente por departamento como novo core.

## Dependência da Onda J

A implementação atual de `llm-json-decoupling` possui documentação com `VERIFY_FINAL_FAILED`.

Não ignore isso e não declare resolvido neste projeto.

- C0–C2 podem avançar independentemente: contratos, navegação e Workspace Context.
- C3+ pode preparar scaffolding/testes, porém **Business Actions production-ready** dependem dos gates OpenAPI-first/tool/eval relevantes aprovados no candidate vigente.

## Ordem obrigatória

Execute uma subetapa por vez:

```text
C0.S0
→ C0.S1
→ C0.S2
→ C1.S1
→ C1.S2
→ C1.S3
→ C1.S4
→ C1.S5
→ C1.S6
→ C2.S1...
```

Continue conforme o grafo do `16-execution-master-plan.md`.

**Não pule C0.S0.**

## C0.S0 — primeira ação

Antes de editar runtime:

1. capture `git status` e HEAD;
2. inventarie código real de Portal, Core, AI API, Chat MFE, manifests e APIs;
3. identifique producer/consumer/owner;
4. atualize `18-app-onboarding-matrix.md` com fatos/evidence;
5. atualize `17-component-and-contract-map.md` se os contratos reais diferirem das hipóteses;
6. registre evidence no ledger;
7. somente então defina C0.S1 como desbloqueada.

Onde não houver prova, use `TO_INVENTORY`/`NOT_PROVEN`. Não invente.

## Protocolo por etapa

```text
REVALIDATE HEAD + WORKING TREE
→ READY_TO_EXECUTE
→ BASELINE
→ MINIMUM CORRECT DIFF
→ WIRING REAL
→ UNIT/CONTRACT
→ INTEGRATION
→ POSITIVE
→ SIBLING
→ NEGATIVE
→ SECURITY/RBAC
→ GENERALIZATION quando aplicável
→ ADVERSARIAL DIFF REVIEW
→ SEMANTIC RESIDUAL SEARCH
→ POSTCONDITIONS
→ COMPLETE_GATE
→ LEDGER/DOCS
→ NEXT
```

Sem `COMPLETE_GATE=PASS`, a próxima dependente não está liberada.

## Capability Projection

Nunca transformar o Capability Catalog em nova fonte técnica.

Business capability:

```text
Action Catalog authority
→ projection para discovery/retrieval/UX
→ sourceRef
→ executor retorna à Action authority
```

Platform capability:

```text
Core /me/apps authority
+ tipos genéricos do Shell
→ projection
```

Não copiar path/method/operationId/schema para JSON manual de capability.

## Platform Actions

Primeiro target funcional:

```text
portal.open_app
portal.open_route
```

O LLM gera target lógico/ID autorizado, nunca URL livre.

`CopilotBridge` deve:

- validar schema;
- resolver target contra rotas atuais autorizadas;
- revalidar no instante da execução;
- executar Router/Shell action;
- emitir resultado tipado/auditável.

## Workspace Context

Contexto deve ser bounded e tipado:

```text
appId
routeId
entityRefs
filters
selection
dateRange
visibleDataRefs
```

Não enviar estado React inteiro. Não usar contexto como permissão.

## Business Actions

UI e Copilot devem convergir:

```text
UI ───────────┐
              ▼
          API/use case
              ▲
Copilot ──────┘
```

Para writes:

```text
args grounded
→ schema validation
→ RBAC/policy
→ preview
→ confirmation quando required
→ revalidation
→ execute
→ verify outcome
→ audit
```

## Workflows

Representar plano operacional, não raciocínio privado.

Cada step possui capability, dependências, status, confirmation boundary e outcome esperado.

Paralelizar somente reads independentes e seguros.

Não retry write sem garantia de idempotência.

## Testes

Use `20-testing-and-acceptance-matrix.md` como gate.

Obrigatório conforme a etapa:

- positive;
- sibling;
- negative;
- unauthorized;
- TOCTOU;
- injection;
- send/stream parity;
- reload/F5;
- unknown external API;
- verdadeiro metamorphic provider/path/operationId rename;
- required/type/enum/path/query/body;
- confirmation/idempotency;
- compound/multi-turn/partial failure;
- R1–R11.

Nunca enfraquecer teste/threshold para fazer o candidate passar.

## Rollout

Seguir:

```text
contracts
→ navigation canary
→ workspace context opt-in
→ business reads
→ prepare write L3
→ confirmed write L4
→ workflows
→ AI-ready waves
→ L5 somente policy explícita e OFF por default
```

Feature flag precisa de owner e exit criteria.

## Reporte obrigatório após cada subetapa

```text
STEP:
HEAD_BEFORE:
HEAD_AFTER:
STATUS:
REQUIREMENTS:
DEPENDENCIES:
FILES_CHANGED:
CANONICAL_OWNERS:
PRODUCERS_CONSUMERS:
BASELINE:
IMPLEMENTATION:
WIRING_PROOF:
TESTS:
POSITIVE:
SIBLING:
NEGATIVE:
SECURITY_RBAC:
GENERALIZATION:
RESIDUAL_SEARCH:
ADVERSARIAL_REVIEW:
DRIFTS:
POSTCONDITIONS:
COMPLETE_GATE:
LEDGER_UPDATED:
NEXT_UNLOCKED:
COMMIT:
PUSH:
```

## Status bloqueantes

Não declarar etapa concluída com:

```text
PARTIAL
INCONCLUSIVE
PENDING
LEGACY_FALLBACK material
SHADOW_ONLY sem exit criteria
TODO/FIXME/HACK/TEMPORARY material
TEST_NOT_RUN
STALE_EVIDENCE
```

## Continuidade

Se o usuário já autorizou a implementação do plano e a etapa atual fechou `COMPLETE_GATE=PASS`, continue automaticamente para a próxima desbloqueada. Pare somente por bloqueio real conforme `22-cursor-execution-protocol.md`.

Comece por **C0.S0**.