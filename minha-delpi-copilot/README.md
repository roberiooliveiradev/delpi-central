# Minha DELPI Copilot

Ponto de entrada da iniciativa no monorepo `delpi-central`.

O Copilot é uma **aplicação nova e standalone** da Minha DELPI, composta por API e MFE próprios e integrada ao Portal/Core/Gateway/Keycloak/APIs existentes.

Ele não é evolução do `minha-delpi-ai-api` nem de `plugins/minha-delpi-chat`.

A visão alvo é **um único Copilot para escritório, reuniões, chão de fábrica, fontes externas autorizadas e operações autônomas governadas**. O mesmo runtime atende Global, Workspace, Meeting, Frontline, uma futura surface Teams e operações background via Watch/Workflow.

O Copilot não é apenas `Chat + RAG`: ele deve perceber eventos, contextualizar, decidir, preparar ou executar ações governadas, verificar o resultado real, comunicar e transformar experiência validada em aprendizado.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Platform/Media/Device/Biometric/External/Automation/OT inventory
RUNTIME_DIFF = NONE
```

## Authorities

- [Plano Mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Boundary standalone](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/50-standalone-copilot-application-architecture.md)
- [Ownership/contracts](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/17-component-and-contract-map.md)
- [Architecture/design patterns](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/49-architecture-and-design-patterns-standard.md)
- [Platform integration baseline](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/51-platform-integration-baseline.md)
- [Repository/bootstrap plan](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/52-standalone-repository-and-bootstrap-plan.md)
- [Multimodal/Meeting/Frontline/Industrial](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/53-multimodal-meeting-frontline-and-industrial-copilot.md)
- [Biometric Identity/Human Observation](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/54-biometric-identity-and-human-observation-governance.md)
- [Internet Research/External Connectors](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/55-internet-research-and-external-connectors.md)
- [Microsoft Teams Connector/Meeting](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/56-microsoft-teams-connector-and-meeting-integration.md)
- [Event-Driven Autonomous Operations / Automation & Execution Hub](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/57-event-driven-autonomous-operations-and-automation-execution-hub.md)
- [Tests/acceptance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [State/persistence](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/21-data-and-state-model.md)
- [Cursor prompt](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Product specification](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Traceability CP-001…CP-248](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Documentation governance](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/48-documentation-governance-and-architecture-review.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Target owners

```text
minha-delpi-copilot-api/       → intelligence/context/decision/work/orchestration backend
plugins/minha-delpi-copilot/   → Global/Workspace/Meeting/Frontline/admin federated MFE
portal/                        → host/context/navigation
core-api/                      → apps/routes/RBAC/governance/user authority
keycloak                       → identity/SSO
gateway/                       → routing
plugins/plugin-ui/             → shared design system
Domain APIs                    → business data/rules/actions
External Providers             → external account/resource authority
Microsoft 365 / Teams          → external collaboration/source/action provider
Secret/Vault owner             → provider/RPA credential material
Automation executors           → API/function/RPA/computer-use execution behind adapters
OT/domain systems              → machine/process truth and industrial safety owners
```

## Copilot versus Automation & Execution Hub

```text
COPILOT
= inteligência
+ contexto
+ decisão
+ planning
+ policy
+ orquestração

AUTOMATION & EXECUTION HUB
= execução governada
```

O Hub não é apenas RPA e não cria outro cérebro.

Preferência de executor:

```text
1 API oficial
2 integração nativa suportada
3 função/script determinístico
4 RPA
5 computer-use/UI automation governada
6 Human Task
```

O planner conhece capabilities semânticas, como:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
```

Ele não conhece clicks, seletores, coordenadas ou detalhes internos de bots.

## Continuous Operational Intelligence

O Copilot deve poder reagir a eventos sem depender de uma pergunta humana:

```text
EVENT / SIGNAL
→ CONTEXT
→ DECISION PATH
   FAST | OPERATIONAL | REASONING
→ POLICY / DECISION / AUTONOMY
→ DURABLE WORKFLOW
→ SEMANTIC CAPABILITY
→ EXECUTOR
→ VERIFIED OUTCOME
→ EVIDENCE / NOTIFICATION
→ LEARNING CANDIDATE
```

Nem todo evento chama um LLM. Critérios verificáveis de readiness/anomalia usam regras/Policies determinísticas quando suficientes.

## Watch e autonomia

```text
OBSERVE
ADVISE
PREPARE
ACT
```

`ACT` pertence a C7. `PREPARE != ACT`.

Autonomia é definida por capability + contexto + risco + ator + limites + ambiente + policy.

```text
GLOBAL_UNRESTRICTED_L5 = FORBIDDEN
L5_DEFAULT = OFF
```

L5 exige allowlist, budgets/limits, revalidation, kill switch e Outcome verificado.

## Outcome truth

```text
technical executor success != verified business outcome
```

Exemplos:

```text
HTTP 200
-X→ nota definitivamente emitida

RPA clicou Salvar
-X→ transação confirmada
```

Quando material, o Copilot verifica postcondition em uma fonte autoritativa antes de declarar conclusão e notificar as pessoas.

## Ordem de construção

```text
C0 Platform + Architecture + Media/Privacy/Biometric/External/Automation/OT Foundation Freeze
→ C1 Standalone Application Bootstrap
→ C2 Portal + Operational Context + Platform Commands
→ C3 Intelligence + Multimodal/Biometric/Internet/Connector/Decision Foundations
→ C4 Business + External Reads + Graph + Operational Read Intelligence
→ C5 Governed Business/External/Automation Writes + Durable Foundation
→ C6 Product Work + Meeting/Frontline + Automation Hub + Events/Learning
→ C7 Autonomous Operations + Advanced Realtime/External Proactivity + Rollout
```

## Boundaries essenciais

```text
Minha DELPI Chat offline
→ Copilot continua funcional

event payload
-X→ permission or direct write authority

RPA bot
-X→ business rule authority

planner
-X→ RPA click/selector/coordenada

supported authoritative API
→ preferred before RPA by default

worker/device/biometric identity
-X→ business permission

technical executor success
-X→ business completion without required verification

PREPARE
-X→ ACT implicitly

global Copilot L5
-X→ unrestricted autonomy

computer-use
→ sandboxed/allowlisted fallback only

free-form LLM/RPA output
-X→ physical machine safety actuation
```

## Primeira ação

Abrir o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md) e executar apenas **C0.S0**.

Nenhuma pasta/runtime de Automation Hub, RPA executor, Event engine ou autonomous ACT deve ser criada antes de `C0.S7 FOUNDATION_FREEZE=PASS`.
