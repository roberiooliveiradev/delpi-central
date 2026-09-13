# Minha DELPI Copilot

> **Status:** `PLANNED / NOT_STARTED`  
> **Decisão de produto:** **aplicação nova e standalone**  
> **Visão:** **um único Copilot para escritório, reuniões, chão de fábrica, fontes externas e operações autônomas governadas**  
> **Próxima etapa:** **C0.S0 — Platform/Media/Device/Biometric/External/Automation/OT Rebaseline Inventory**  
> **Ordem executável:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
> **Boundary standalone:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
> **Multimodal/Meeting/Frontline:** [`53-multimodal-meeting-frontline-and-industrial-copilot.md`](./53-multimodal-meeting-frontline-and-industrial-copilot.md)  
> **Biometric/Human Observation:** [`54-biometric-identity-and-human-observation-governance.md`](./54-biometric-identity-and-human-observation-governance.md)  
> **Internet/External Connectors:** [`55-internet-research-and-external-connectors.md`](./55-internet-research-and-external-connectors.md)  
> **Microsoft Teams:** [`56-microsoft-teams-connector-and-meeting-integration.md`](./56-microsoft-teams-connector-and-meeting-integration.md)  
> **Autonomous Operations/Execution Hub:** [`57-event-driven-autonomous-operations-and-automation-execution-hub.md`](./57-event-driven-autonomous-operations-and-automation-execution-hub.md)  
> **Prompt do Cursor:** [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md)  
> **Requirements:** [`25-requirements-traceability.md`](./25-requirements-traceability.md) — `CP-001…CP-248`  
> **Ledger:** [`evidence/execution-ledger.md`](./evidence/execution-ledger.md)

## 1. Decisão fundamental

O **Minha DELPI Copilot não é uma expansão do Minha DELPI Chat**.

```text
Minha DELPI Chat                 Minha DELPI Copilot
-----------------------------    ------------------------------
plugins/minha-delpi-chat         novo MFE próprio
minha-delpi-ai-api               nova API própria
runtime/persistência do Chat     runtime/persistência próprios
release do Chat                  release próprio

                 SEM DEPENDÊNCIA DE RUNTIME
```

O Copilot preserva as fundações corporativas existentes — Portal, Core API, Keycloak, Gateway, Manifest, Module Federation, `plugin-ui` e Domain APIs — mas possui inteligência, estado, deploy e evolução próprios.

## 2. North Star

> **Minha DELPI Copilot é a interface e a inteligência operacional entre pessoas, sistemas, dados, automações e a operação física da DELPI. Ele pesquisa, percebe eventos, entende contexto, combina regras determinísticas e raciocínio de IA, toma decisões governadas, coordena APIs, automações/RPAs e pessoas, verifica resultados, comunica os envolvidos e transforma experiência validada em aprendizado governado.**

```text
PERCEBER   → eventos, dados, mensagens, mídia e contexto operacional
ENTENDER   → pesquisar, correlacionar, explicar, analisar
DECIDIR    → rules/policies + AI reasoning quando necessário
PREPARAR   → plano, draft, preview, Task, Decision
EXECUTAR   → APIs, functions, RPA, computer-use governado, Human Task
VERIFICAR  → outcome/postcondition real
COMUNICAR  → Minha DELPI, email, Teams, WhatsApp e canais autorizados
APRENDER   → candidate knowledge/policy/playbook após review/eval
```

## 3. Não é “Chat + RAG”

O runtime alvo aceita tanto intenção humana quanto eventos:

```text
user request OR EventEnvelope
→ context / Business Graph / Evidence
→ DecisionPathPolicy
   FAST | OPERATIONAL | REASONING
→ Policy / Decision Gate / AutonomyPolicy
→ Durable Workflow
→ semantic capability
→ executor
→ verified Outcome
→ Evidence / Notification / Learning candidate
```

Nem todo evento chama um LLM. Condições determinísticas usam regras/Policies/State Machines quando suficientes.

## 4. Surfaces e presença

```text
GLOBAL      → painel contextual no Portal
WORKSPACE   → página completa
MEETING     → reunião assistida multimodal
FRONTLINE   → operador/posto/máquina
TEAMS       → futura surface app/tab/bot do mesmo Copilot
BACKGROUND  → Watch/Workflow reagindo a eventos governados
```

Todas compartilham a mesma Copilot API, Core/RBAC, Policy/Decision Gate, Evidence e Durable Work runtime.

## 5. Três espaços de informação

```text
MINHA DELPI
→ Core / Domain APIs / Business Graph / Knowledge / apps

INTERNET
→ Search + Safe Web Fetch + SourceRef/EvidenceRef

CONNECTED SOURCES
→ Microsoft 365/Outlook/Teams
→ Google Workspace/Gmail
→ WhatsApp Business
→ Slack/GitHub/outros futuros connectors
```

External scopes nunca elevam Core RBAC. Conteúdo externo é untrusted data para system/policy.

## 6. Automation & Execution Hub

Não construir apenas um “Hub de RPAs”. O target conceitual é:

> **Minha DELPI Automation & Execution Hub**

Separação:

```text
COPILOT
= inteligência, contexto, decisão, planning e orquestração

AUTOMATION & EXECUTION HUB
= execução por contracts governados
```

Executor preference:

```text
1. API oficial
2. integração nativa suportada
3. função/script determinístico
4. RPA
5. computer-use/UI automation governada
6. Human Task
```

RPA é executor substituível, nunca authority de business rule.

## 7. Semantic capability antes do executor

O planner conhece:

```text
billing.invoice.issue
maintenance.request.create
production.report.validate
communication.email.send
inventory.read
```

Não conhece:

```text
click(x,y)
CSS/XPath selector
screen coordinate
RPA package internals
```

Uma capability pode migrar de RPA para API sem patch no planner/workflow.

## 8. Continuous Operational Intelligence

Watches podem observar condições como:

```text
pedido pronto para faturar
máquina parada
apontamento improvável
estoque crítico
fornecedor atrasado
OP aguardando material
qualidade desviando
prazo/approval expirando
resposta externa recebida
```

Modes:

```text
OBSERVE
ADVISE
PREPARE
ACT   # C7 only
```

`PREPARE != ACT`.

## 9. Outcome truth

Invariante:

```text
technical executor success != verified business outcome
```

Exemplos:

```text
HTTP 200 != nota emitida corretamente
RPA clicou Salvar != transação confirmada
provider accepted != entrega final quando async
```

Toda ação material usa postcondition/Outcome verification quando aplicável antes de comunicar conclusão.

## 10. Autonomia

Autonomia é resolvida por:

```text
capability
+ actor/service identity
+ source/event trust
+ context
+ risk/sensitivity
+ financial/material limits
+ environment
+ reversibility
+ policy
```

Não existe `Copilot=L5` global. L5 permanece OFF por default e exige allowlist, budgets/limits, revalidation, kill switch e verified Outcome.

## 11. Meeting / Frontline / Biometria

Meeting e Frontline são surfaces do mesmo runtime. Voz/câmera/biometria são modalidades/contexto, não permission bypass.

Biometric match:

```text
!= authenticated session
!= Core permission
!= Business Action authorization
```

Human Observation permanece limitada a fatos/padrões objetivos do processo e não pode virar inferência psicológica/sensível ou decisão trabalhista automática.

## 12. OT / máquinas

Copilot não é safety controller.

```text
approved telemetry/read
→ context/Evidence/analysis/recommendation

free-form LLM/RPA/computer-use
-X→ PLC/CNC/robot/machine safety actuation
```

Qualquer future physical actuation exige iniciativa/safety gate separado com typed deterministic commands, allowlist, state checks, industrial owner, interlocks independentes, test/simulation, fail-safe e audit.

## 13. Owners alvo

```text
minha-delpi-copilot-api/       → intelligence/work/automation orchestration runtime
plugins/minha-delpi-copilot/   → Global/Workspace/Meeting/Frontline/admin MFE
portal/                        → host/context/navigation
core-api/                      → apps/routes/RBAC/governance/user authority
keycloak                       → identity/SSO
gateway/                       → routing
plugins/plugin-ui/             → shared design system
Domain APIs                    → business data/rules/actions
External Providers             → external resource authority
Secret/Vault owner             → credential material
Automation executors           → execution mechanisms behind adapters
OT/domain systems              → machine/process truth and industrial safety owners
```

Automation & Execution Hub pode ser bounded module do Copilot ou neutral platform service somente após C0 ownership analysis. “Hub” não implica microservice antecipadamente.

## 14. Ordem canônica

```text
C0 — Platform + Architecture + Media/Privacy/Biometric/External/Automation/OT Foundation Freeze
→ C1 — Standalone Application Bootstrap
→ C2 — Portal + Operational Context + Platform Commands
→ C3 — Intelligence + Multimodal/Biometric/Internet/Connector/Decision Foundations
→ C4 — Business + External Reads + Graph + Operational Read Intelligence
→ C5 — Governed Business/External/Automation Writes + Durable Foundation
→ C6 — Product Work + Meeting/Frontline + Automation Hub + Events/Learning
→ C7 — Autonomous Operations + Advanced Realtime/External Proactivity + Rollout
```

## 15. C0 precisa congelar antes de qualquer runtime

Além do inventário já definido, C0 agora inclui:

```text
event sources/brokers/webhooks/schedulers
RPA tools/orchestrators/licences/bots/packages
scripts/functions/jobs
queues/workers/desktop execution infrastructure
service accounts/background identities
credential owners/injection
business postcondition/outcome sources
executor contracts/idempotency/retry
RPA artifacts/retention
notification/escalation channels
automation ownership/governance
kill switches/emergency stop
```

Nenhum Automation Hub/RPA runtime é criado em C0.S0.

## 16. Documentos canônicos

| Documento | Papel |
|---|---|
| `16` | única ordem de implementação |
| `17` | owners/primitives/contracts |
| `20` | testes/gates |
| `21` | state/persistence |
| `23` | prompt mestre Cursor |
| `25` | requirements `CP-*` |
| `49` | architecture/design patterns |
| `50` | standalone product boundary |
| `51` | factual platform baseline |
| `52` | estrutura física/bootstrap |
| `53` | multimodal/Meeting/Frontline/industrial |
| `54` | biometric/Human Observation |
| `55` | Internet/external connectors |
| `56` | Microsoft Teams |
| `57` | autonomous operations/Automation & Execution Hub |
| ledger | execution evidence/status |

## 17. Primeiro passo

Abrir [`23-prompt-cursor-execucao.md`](./23-prompt-cursor-execucao.md) e executar **somente C0.S0**.

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT = C0.S0
RUNTIME_DIFF = NONE
```

A primeira implementação após `C0.S7 FOUNDATION_FREEZE=PASS` continua sendo o **bootstrap standalone** da Copilot API/MFE — não RPA, não Event engine, não LLM autonomy.
