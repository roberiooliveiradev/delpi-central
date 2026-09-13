# 01 — Visão de produto

**Status:** visão canônica de produto  
**Order authority:** [`16-execution-master-plan.md`](./16-execution-master-plan.md)  
**Standalone boundary:** [`50-standalone-copilot-application-architecture.md`](./50-standalone-copilot-application-architecture.md)  
**Requirements:** `CP-001…CP-310`

## 1. Definição

A **DÉLIA — DELPI · Ecossistema de Ligações, Inteligência e Automação** é uma nova aplicação standalone de Continuous Operational Intelligence e a camada inteligente operacional transversal da Minha DELPI.

Ela não é apenas um assistente de chat. O target combina:

```text
Continuous Operational Intelligence
+ Process Intelligence
+ Decision Intelligence
+ Governed Automation Orchestration
+ Analytical/Predictive Intelligence
+ AI Governance
```

Possui API/MFE/persistence/manifest/deploy próprios e não depende do Minha DELPI Chat.

## 2. North Star

> **A DÉLIA acompanha o usuário e a operação, entende texto/voz/imagem/documentos/contexto empresarial e industrial, conhece dados/processos/métricas autorizados, pesquisa fontes internas e externas, prevê e simula cenários, toma decisões governadas, coordena APIs/automações/pessoas, verifica o resultado real e transforma experiência validada em conhecimento — preservando authorities, privacidade e segurança.**

```text
PERCEBER
→ ENTENDER
→ PESQUISAR
→ ANALISAR
→ PREVER/SIMULAR
→ DECIDIR
→ PREPARAR/EXECUTAR
→ VERIFICAR
→ COMUNICAR
→ APRENDER COM GOVERNANÇA
```

## 3. Promessa

> O usuário diz, mostra ou demonstra o objetivo. A DÉLIA encontra contexto e recursos autorizados, aplica conhecimento/semântica adequados, mostra Evidence, escolhe o menor caminho de decisão suficiente, prepara ou executa o permitido e acompanha até Outcome verificável.

## 4. Plataforma e authorities

```text
Portal         → host/navigation/published context
Core API       → apps/routes/RBAC/governance
Keycloak       → identity/SSO
Gateway        → routing
plugin-ui      → design system
Domain APIs    → business data/rules/actions
Providers      → external resources/scopes
Automation Hub → technical execution
OT systems     → machine/safety truth
DÉLIA          → intelligence/context/Evidence/Policy/Decision/Work/orchestration/outcome coordination
```

DÉLIA reutiliza a plataforma, não o runtime do Chat. Nenhuma dessas integrações amplia a authority do respectivo owner.

## 5. Surfaces

```text
GLOBAL      → contextual panel
WORKSPACE   → full-page analysis/work
MEETING     → meeting assistance
FRONTLINE   → shopfloor/operator assistance
TEAMS       → future surface of same DÉLIA runtime
BACKGROUND  → Watches/Workflows
ADMIN       → governance surfaces by role
```

## 6. Personalização sem nova authority

Personal Memory pode lembrar preferências, tópicos/projetos acompanhados e continuidade de trabalho, com controles de inspeção/correção/exclusão/desabilitação.

```text
Personal Memory != Organizational Knowledge
Personal Memory != RBAC
Personal Memory != live business truth
```

## 7. Entendimento empresarial

A DÉLIA combina:

```text
Business Graph          → relações entre entidades
Semantic Business Layer → definição oficial de métricas/conceitos
Process Intelligence    → como o processo realmente acontece
Knowledge/Expertise     → conhecimento e método
```

Nenhuma camada replica todos os systems of record.

## 8. Process Intelligence

A partir de event logs autorizados, o produto pode descobrir variants, gargalos, esperas, retrabalho, desvios de processo e oportunidades de automação, medir before/after e gerar process maps/BPMN candidates.

Process Mining mede processo; não é mecanismo de scoring oculto de trabalhadores.

## 9. Event / Decision Intelligence

O usuário não é a única fonte de trigger.

```text
event
→ context
→ FAST | OPERATIONAL | REASONING
→ OBSERVE / ADVISE / PREPARE / ACT conforme policy/fase
```

Nem todo evento chama LLM. Critérios formais de readiness usam facts/regras determinísticas quando disponíveis.

C5 pode liberar ACT governado de capabilities específicas; C7 adiciona autonomia avançada/Watch ACT selecionado. L5 permanece OFF por default.

## 10. Automation Hub / execução

DÉLIA é owner de inteligência, Policy, Decision e Work/orquestração. Automation Hub é owner da execução técnica de automações sob seu boundary.

Preferência de executor:

```text
official API
→ native integration
→ deterministic function/script
→ RPA
→ governed computer-use
→ Human Task
```

API é preferida quando há contrato autoritativo suportado. Planner trabalha com capabilities semânticas e nunca manipula click/selector de RPA.

## 11. Outcome truth

```text
technical execution success
!=
verified business outcome
```

A DÉLIA deve verificar postconditions em fonte autoritativa antes de afirmar sucesso material.

## 12. Analysis / Artifacts

A DÉLIA pode executar análises em sandbox isolado e produzir artefatos editáveis/versionados/provenanced: reports, spreadsheets, presentations, charts, BPMN, A3/8D/FMEA candidates, procedures/checklists, project plans e outros work products.

Human edits não são sobrescritos silenciosamente.

## 13. Predictive / Prescriptive / Twin

O produto deve evoluir de descriptive/diagnostic para predictive/prescriptive intelligence.

```text
Prediction != FACT
Recommendation != Authorization
Simulated State != Production State
Simulate != Apply
```

Operational Twin permite cenários/what-if sem virar system of record.

## 14. External / Internet / Teams / Interoperability

DÉLIA pode pesquisar internet, conectar fontes autorizadas e operar com Microsoft 365/Teams/Google/WhatsApp Business/etc. via provider-neutral adapters quando os contratos/providers forem aprovados.

MCP-compatible tools e A2A-compatible agents podem ser integrados sob approval/allowlists; discovery nunca significa trust automático.

## 15. AI Control Tower / Model Lifecycle / Marketplace

A DELPI deve saber:

- quais AI/model/automation/tool/agent/Edge assets existem;
- quem é owner;
- que dados/capabilities acessam;
- risk/eval/health/cost/value/incidents;
- como disable/rollback/revoke.

Model lifecycle governa eval→approval→deployment→drift→rollback/revoke. Marketplace governa reusable capabilities/assets. Install/enable não concede permissions.

## 16. Meeting / Frontline / Edge

Meeting distingue transcript/resumo/decisão/candidate action/executed outcome.

Frontline prioriza hands-free/large-touch/current procedure/drawing/OP/machine context e pode usar governed Edge/offline assistance quando gates e evidência provarem infraestrutura e safety boundaries.

Offline never widens authority.

## 17. Biometric Identity / Human Observation

Reconhecimento de usuários conhecidos/enrolled por face/voz pode existir como capability governada, closed-set e purpose-specific, quando priorizado/aprovado.

```text
biometric match
!= authentication
!= permission
```

Unknown/low-confidence stays unknown/confirmable; enrollment/templates are explicit/revocable/protected.

Human Observation fica limitada a evidência observável do processo; não infere personality, honesty, emotion-as-truth, health/sensitive traits ou employee potential/disciplinary propensity.

## 18. Industrial safety

DÉLIA não é safety controller.

```text
free-form LLM/model/vision/voice/RPA/Edge
-X→ arbitrary PLC/CNC/robot/machine command
```

Future physical actuation requires separate industrial safety initiative/gate with deterministic typed commands/interlocks/owners/fail-safe/audit.

## 19. Governed learning

```text
experience/source/process/execution
→ Evidence
→ candidate
→ review/eval/privacy/freshness
→ versioned publish
```

No conversation, observation, public page, process variant or successful automation becomes production policy automatically.

## 20. Non-goals / prohibitions

- depend on Chat runtime/database/API;
- duplicate Core/RBAC/domain rules;
- bypass Automation Hub technical-execution ownership where applicable;
- provider/executor/model/tool hardcode in planner;
- unrestricted browser/sandbox/computer control;
- hidden media/biometric/task surveillance;
- Process Mining employee ranking;
- Personal Memory as company truth;
- metric formula invented ad hoc by LLM;
- prediction as fact;
- simulation/twin writing production directly;
- Edge/offline wider permissions;
- Marketplace/package granting permission;
- global unrestricted L5;
- arbitrary machine actuation.

## 21. Product metrics

Track task/case completion, Evidence Coverage, Process improvement, Watch quality, verified automation outcomes, exception/human intervention, Meeting/Frontline success, prediction quality, artifact usefulness, memory corrections, model health/drift, cost and **verified business value**.

Avoid vanity metrics and hidden people scoring.

## 22. Implantação

Foundation-first only:

```text
C0 Foundation Freeze
→ C1 Standalone Bootstrap
→ C2 Context/Commands
→ C3 Capability Foundations
→ C4 Reads/Analysis
→ C5 Governed ACT + Durable Work
→ C6 Product Governance/Experience
→ C7 Advanced Autonomy/Scale
```

Fonte de verdade: `16-execution-master-plan.md`.
