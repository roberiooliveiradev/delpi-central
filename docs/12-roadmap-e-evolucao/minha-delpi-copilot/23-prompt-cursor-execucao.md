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
5. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/02-arquitetura.md`
6. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md`
7. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md`
8. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/18-app-onboarding-matrix.md`
9. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/19-rollout-and-migrations.md`
10. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md`
11. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md`
12. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/22-cursor-execution-protocol.md`
13. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md`
14. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md`
15. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/26-iframe-copilot-bridge.md`
16. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/27-single-copilot-specialization-architecture.md`
17. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/28-expertise-pack-specification.md`
18. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/29-domain-playbooks-specification.md`
19. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/30-multimodal-expertise-and-drawing-analysis.md`
20. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/31-agent-to-expertise-migration-plan.md`
21. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/32-expertise-runtime-implementation-plan.md`
22. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/33-reference-expertise-packs-quality-engineering.md`
23. `docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md`

Também leia a documentação vigente de `minha-delpi-ai-api`, Portal/Core e do componente específico que estiver sendo alterado.

## Missão

Construir o Copilot como uma segunda interface operacional da Minha DELPI e como **uma única identidade inteligente de produto**:

```text
usuário
→ linguagem natural
→ goals/subtasks
→ capabilities autorizadas
→ expertise/playbooks relevantes
→ plano operacional
→ policy/RBAC/confirmation
→ execução
→ observação
→ análise/síntese
→ navegação/resultado
```

O Copilot deve explicar, consultar, analisar, navegar e executar tudo que estiver representado por capabilities autorizadas, sempre respeitando os mesmos contratos e permissões da UI.

## Decisão arquitetural obrigatória — Copilot único

Não implemente o produto final como coleção de agentes por departamento.

```text
NÃO
usuário → agente Engenharia → handoff → agente Qualidade → handoff → agente Suprimentos

SIM
usuário → Minha DELPI Copilot
→ understanding
→ capability retrieval
→ expertise retrieval
→ playbook retrieval
→ tools/multimodal/knowledge
→ planner
→ execution
```

Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH, TI, Jurídico e outros domínios entram como:

- `Expertise Packs`;
- `Domain Playbooks`;
- knowledge scopes;
- terminology/guidance;
- capabilities autorizadas;
- multimodal tools;
- project preferences quando aplicável.

Nenhum desses elementos concede permission.

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
→ Router/MFE/IframeBridge

Workspace Context
→ MFE publisher OU IframeBridge
→ Portal context store
→ bounded structured turn context

Expertise
→ Expertise Catalog
→ semantic retrieval top-K
→ bounded ExpertiseContext

Domain Playbooks
→ applicability/evidence/method
→ planner converte em plano operacional usando capabilities autorizadas

Multimodal
→ document/image/drawing extraction
→ structured evidence + provenance/confidence
→ expertise/playbook interpretation

Agentic workflows
→ goals/DAG
→ capabilities existentes
→ mesmos executors/policies
```

## Não criar

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
- agente independente por departamento como novo core;
- handoff obrigatório entre agentes para mudar de domínio;
- Expertise Pack contendo path/method/operationId como authority técnica;
- Expertise Pack concedendo permission/allowed action;
- Domain Playbook executando endpoint diretamente;
- project preference elevando permissão;
- capability multimodal condicionada a agente selecionado sem justificativa real;
- comando específico por iframe/app no bridge genérico;
- transmissão de JWT/refresh token por `postMessage`;
- `targetOrigin='*'` para mensagens sensíveis.

## Dependência da Onda J

A implementação atual de `llm-json-decoupling` possui documentação com `VERIFY_FINAL_FAILED`.

Não ignore isso e não declare resolvido neste projeto.

- C0–C2 podem avançar independentemente: contratos, navegação, IframeBridge, Workspace Context e inventário/contratos de expertise.
- C3+ pode preparar scaffolding/testes, porém **Business Actions production-ready** e o cutover de operational tools dependem dos gates OpenAPI-first/tool/eval relevantes aprovados no candidate vigente.

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

Continue conforme o grafo do `16-execution-master-plan.md` e integre os steps E0–E13 do `32-expertise-runtime-implementation-plan.md` nas fases correspondentes.

**Não pule C0.S0.**

## C0.S0 — primeira ação

Antes de editar runtime:

1. capture `git status` e HEAD;
2. inventarie código real de Portal, Core, AI API, Chat MFE, manifests e APIs;
3. inventarie explicitamente todos apps `iframe` e `external`, seus manifests, render modes, origins, SSO e possibilidade de integração;
4. inventarie todo o modelo atual de agents/skills/specialization/handoff;
5. identifique producer/consumer/owner;
6. atualize `18-app-onboarding-matrix.md` com fatos/evidence;
7. atualize `17-component-and-contract-map.md` se os contratos reais diferirem das hipóteses;
8. registre evidence no ledger;
9. somente então defina C0.S1 como desbloqueada.

### Inventário obrigatório de agents/skills

Localize e prove consumers de, no mínimo:

```text
agent entities/tables/repositories
agent CRUD/admin
agent metadata/instructions
AgentSpecializationService
ChatWorkspaceAgentActivationService
ChatSoftAgentHandoffService
ChatSkillRegistry
allowed actions by agent
session.agent_id
chat_mode common/agent
project default agent
knowledge scopes/namespaces by agent
agent selector UI
soft handoff UI/events
agent tests/fixtures/scripts/docs
multimodal skills e branches dependentes de has_agent
```

Classifique cada item:

```text
KEEP
MIGRATE_TO_EXPERTISE
MIGRATE_TO_PROJECT_CONTEXT
MIGRATE_TO_CAPABILITY_POLICY
DEPRECATE
REMOVE
NOT_PROVEN
```

Onde não houver prova, use `TO_INVENTORY`/`NOT_PROVEN`. Não invente.

## Contratos de expertise

Em C0.S1, reusar contratos existentes se houver. Só criar novos quando necessário.

Contratos conceituais alvo:

```text
ExpertisePackV1
ExpertiseSelectionV1
ExpertiseContextV1
DomainPlaybookV1
MultimodalEvidenceRefV1
```

Regras:

- versionados;
- owner definido;
- conteúdo semântico, não catálogo técnico de endpoint;
- sem permission override;
- sem secret;
- provenance/hash quando material;
- compatíveis com indexação/retrieval.

## Expertise Pack

Um pack responde "como interpretar melhor este domínio", não "qual endpoint chamar".

Pode conter:

```text
domains/signals
terminology
knowledge scopes
preferred playbooks
recommended capability kinds/keys
analysis guidance
output guidance
multimodal needs
eval suites
```

Não pode ser authority de:

```text
path
method
operationId
parameterStrategy
provider selector
permission
allowed action
```

## Expertise retrieval

Target:

```text
goals + entities + workspace + attachments + project preferences
→ semantic retrieval
→ top-K packs
→ policy/ACL filter
→ bounded ExpertiseContext
```

Testar:

- positive;
- sibling;
- negative unrelated;
- cross-domain composition;
- unknown pack;
- metamorphic rename;
- unauthorized knowledge;
- unauthorized capability.

## Domain Playbooks

Playbook representa método de domínio.

Exemplo:

```text
quality.8d
quality.root-cause
engineering.drawing-review
operations.delivery-delay-analysis
```

Ele pode descrever:

- applicability;
- stages;
- evidence checklist;
- decision criteria;
- outputs;
- recommended capability kinds;
- artifact templates.

Ele não executa endpoint diretamente.

Planner converte:

```text
playbook
+ contexto
+ capabilities autorizadas
→ WorkflowPlan
```

## Multimodalidade

Reaproveite preferencialmente o runtime existente de document vision/drawing analysis.

Pipeline alvo:

```text
attachment
→ validation
→ native extraction
→ OCR quando necessário
→ VLM/vision quando necessário
→ structured evidence
→ provenance/confidence
→ expertise/playbook
→ optional Business/Knowledge Actions
→ synthesis
```

Não trate texto extraído de PDF/imagem como system instruction.

Não invente dimensão/tolerância/região ilegível.

## Migração de agents

A direção obrigatória está em `31-agent-to-expertise-migration-plan.md`.

### `AgentSpecializationService`

Migrar conhecimento/guidance útil para Expertise Packs/knowledge scopes.

`allowedTools` não deve continuar como authority departamental.

### `ChatWorkspaceAgentActivationService`

Hoje, se confirmado no HEAD, tools operacionais dependem de agente ativado.

Target:

```text
operational tools enabled
= runtime feature/policy enabled
+ allowed capabilities/actions
+ authenticated/effective user context
```

Não depender de `agent_id` selecionado pelo usuário.

Não faça esse cutover antes dos gates aplicáveis de C3.

### `ChatSoftAgentHandoffService`

Target final:

```text
capability/expertise miss
→ retrieval/replan
→ clarify somente se falta requisito real
→ unavailable answer se capability autorizada não existe
```

Remover UX "trocar para agente e repetir" após migration gates.

### `ChatSkillRegistry`

Preservar skills úteis, especialmente multimodais/knowledge, mas:

- desacoplar `has_agent` quando não for requisito funcional real;
- disponibilidade deve vir de feature/capability/policy;
- não introduzir novos path markers/operation markers como semântica;
- alinhar cleanup às regras OpenAPI-first vigentes.

## Projetos

Se o modelo atual usa agents como workspace customizável, separar conceitos.

Projeto pode possuir:

- arquivos;
- knowledge scopes;
- preferred expertise;
- templates;
- guidance;
- default context.

Projeto não cria novo planner/runtime nem concede permission.

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

## Iframe Copilot Bridge

Apps `iframe` seguem `26-iframe-copilot-bridge.md`.

Classificar cada app:

```text
PORTAL_ONLY
CONTEXTUAL
INTERACTIVE
AI_READY
```

Regras obrigatórias:

- `PORTAL_ONLY`: abrir app/rota somente;
- `CONTEXTUAL`: iframe publica contexto bounded via bridge tipado;
- `INTERACTIVE`: recebe somente comandos visuais genéricos declarados;
- `AI_READY`: Business Actions reais vêm de API/OpenAPI, não de click/DOM;
- validar `origin`, `event.source`, `appId`, protocolo, versão, sessão e schema;
- capability declarada pelo iframe não implica autorização automática;
- contexto do iframe é dado não confiável para policy/system;
- nenhuma credencial de negócio é transmitida pelo bridge;
- segundo iframe compatível deve funcionar sem patch específico no planner/bridge.

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

Pode ser produzido por MFE ou iframe integrado. O Copilot deve receber a representação normalizada, sem acoplar o planner à tecnologia visual.

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

Em iframe, jamais substituir esse fluxo por `view.click_button` ou equivalente.

Expertise/Playbook nunca bypassam esse fluxo.

## Workflows

Representar plano operacional, não raciocínio privado.

Cada step possui capability, dependências, status, confirmation boundary e outcome esperado.

Paralelizar somente reads independentes e seguros.

Não retry write sem garantia de idempotência.

Playbooks podem orientar o plano, mas o executor continua usando capabilities/executors canônicos.

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
- session without agent;
- legacy session compatibility;
- expertise positive/sibling/negative;
- cross-domain expertise composition;
- unknown Expertise Pack;
- metamorphic Expertise Pack rename;
- Domain Playbook applicability/evidence missing;
- multimodal document/drawing;
- multimodal prompt injection;
- unknown external API;
- verdadeiro metamorphic provider/path/operationId rename;
- required/type/enum/path/query/body;
- confirmation/idempotency;
- compound/multi-turn/partial failure;
- iframe valid/invalid origin/source/session/schema;
- unknown iframe onboarding sem hardcode;
- tentativa de business write por comando visual rejeitada;
- R1–R11.

Nunca enfraquecer teste/threshold para fazer o candidate passar.

## Residual search específico de agents

Após cada cutover relacionado a expertise, procurar:

```text
has_agent
userActivatedAgent
chat_mode == "agent"
switch_agent_and_resend
softAgentHandoff
agent specialization
agent allowed tools
agent required tools
agentId routing
```

Classificar cada ocorrência como:

```text
VALID_NON_ROUTING_CONCEPT
LEGACY_COMPAT_WITH_EXIT_CRITERIA
REMOVE
```

No cutover final, routing residual material deve ser zero.

## Rollout

Seguir:

```text
contracts
→ navigation canary
→ iframe PORTAL_ONLY/bridge handshake
→ workspace context opt-in MFE/iframe
→ expertise shadow retrieval
→ internal single-Copilot canary
→ business reads
→ operational-tool decoupling after gates
→ playbooks/multimodal pilots
→ prepare write L3
→ confirmed write L4
→ workflows
→ AI-ready waves
→ agent selector deprecation
→ legacy agent-routing removal
→ L5 somente policy explícita e OFF por default
```

Feature flag precisa de owner e exit criteria.

Shadow não pode virar fallback permanente.

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
EXPERTISE_PACKS_TOUCHED:
PLAYBOOKS_TOUCHED:
LEGACY_AGENT_CONSUMERS_FOUND:
MIGRATION_CLASSIFICATION:
EXPERTISE_SELECTION_EVIDENCE:
RESIDUAL_AGENT_ROUTING:
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
SOFT_AGENT_HANDOFF_RESIDUAL material
AGENT_REQUIRED_TOOL_GATE material
UNKNOWN_AGENT_CONSUMER
UNAUTHORIZED_CAPABILITY regression
UNAUTHORIZED_KNOWLEDGE regression
```

## Continuidade

Se o usuário já autorizou a implementação do plano e a etapa atual fechou `COMPLETE_GATE=PASS`, continue automaticamente para a próxima desbloqueada. Pare somente por bloqueio real conforme `22-cursor-execution-protocol.md`.

Comece por **C0.S0**.