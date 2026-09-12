# 02 — Arquitetura

## 1. Objetivo arquitetural

O Copilot deve ser uma camada transversal sobre a arquitetura atual da Minha DELPI, reutilizando identidade, RBAC, Core API, Portal Shell, `minha-delpi-ai-api`, OpenAPI Action Catalog, RAG, multimodalidade, MFEs e apps iframe.

Não criar um produto paralelo à plataforma.

A identidade do produto também é única:

> **Existe um único Minha DELPI Copilot.** Especialização por Engenharia, Qualidade, Suprimentos, Comercial, Financeiro, RH e demais domínios ocorre por **Expertise Packs**, **Domain Playbooks**, knowledge scopes, capabilities e ferramentas multimodais — não por troca de agente/runtime.

Fonte detalhada: [`27-single-copilot-specialization-architecture.md`](./27-single-copilot-specialization-architecture.md).

## 2. Componentes

```text
Portal Shell
├─ Router
├─ AuthContext
├─ Apps/Routes autorizados
├─ Copilot UI
├─ CopilotBridge
├─ IframeBridge
└─ WorkspaceContextBridge

minha-delpi-ai-api
├─ Turn Understanding
├─ Context/Memory
├─ Capability Retrieval
├─ Expertise Retrieval
├─ Domain Playbook Retrieval
├─ Knowledge Retrieval
├─ Multimodal Evidence
├─ Planner / Workflow Runtime
├─ Policies/Confirmation
├─ Action Execution
├─ Analysis/Synthesis
└─ Observability/Evals

Core API
├─ identidade efetiva
├─ apps/rotas
├─ permissions/RBAC
└─ auditoria/governança

Business APIs
├─ api-delpi
├─ APIs de portais
├─ serviços específicos
└─ integrações externas OpenAPI
```

## 3. Pipeline canônico

```text
mensagem + workspace context + attachments
→ segurança/input validation
→ structured understanding
→ goals/subtasks/dependencies/entities/domain signals
→ authorized capability discovery
→ expertise retrieval
→ playbook retrieval
→ knowledge retrieval
→ multimodal extraction quando aplicável
→ bounded context composition
→ structured plan
→ policy/RBAC/sensitivity
→ confirm quando necessário
→ generic execution
→ observations/results
→ domain-aware analysis/synthesis
→ renderPlan + UI commands
→ persistence/audit/evals
```

## 4. Tipos de capability

```text
Business Action
→ operação de negócio via API/use case

Platform Action
→ operação do Portal/Shell

Knowledge Capability
→ RAG/search/documentos

Analysis Capability
→ transformação/comparação/síntese grounded

Artifact Capability
→ geração de relatório/mensagem/arquivo

Multimodal Capability
→ extração/percepção de documento/imagem/desenho

Workflow Capability
→ composição governada de múltiplas capabilities
```

## 5. Tipos de especialização

Especialização é ortogonal a capability.

```text
Expertise Pack
→ linguagem, conceitos, critérios, guidance e knowledge scopes de um domínio

Domain Playbook
→ método operacional/analítico com evidências, etapas e critérios

Project Context
→ arquivos, preferências, knowledge e contexto persistível de um workspace

Multimodal Tool
→ mecanismo de percepção/extração; não identidade de agente
```

Exemplo:

```text
Capability: consultar reclamações
Expertise: quality-industrial
Playbook: quality.root-cause
Tool: document-vision
```

## 6. Fonte de verdade por responsabilidade

| Conceito | Fonte de verdade |
|---|---|
| identidade | Keycloak + Core context |
| permissões efetivas | Core API |
| apps/rotas autorizadas | `/core-api/me/apps` / contratos equivalentes |
| operação de negócio | API/use case + OpenAPI |
| contrato técnico de action | OpenAPI + Action Catalog |
| confirmação/sensitivity | policy determinística |
| contexto visual atual | Portal/MFE/iframe Workspace Context |
| conhecimento documental | fontes RAG autorizadas |
| expertise | Expertise Catalog |
| método de domínio | Domain Playbook Catalog |
| percepção multimodal | serviços multimodais/versionados |
| navegação | Platform Capability Catalog derivado do Portal |
| apresentação de dados | schema/payload/metadata → renderPlan |

Nenhuma expertise/playbook pode duplicar permission, path, method, operationId ou schema como authority técnica paralela.

## 7. Princípio UI ↔ Copilot

A UI e o Copilot devem convergir para os mesmos use cases.

```text
MFE/UI ──────┐
             ▼
       Business Use Case/API
             ▲
Copilot ─────┘
```

Automação de UI só deve ser usada para ações verdadeiramente visuais, como navegação, foco, troca de aba ou aplicação de preferência local.

## 8. CopilotBridge

Responsável no Portal por receber **Platform Commands tipados** e validá-los antes da execução.

Exemplos:

```json
{
  "type": "portal.open_app",
  "target": { "appId": "portal-suprimentos" }
}
```

```json
{
  "type": "portal.open_entity",
  "target": {
    "entityType": "purchaseRequest",
    "entityId": "SC-00123"
  }
}
```

O LLM não produz `window.location`, URL arbitrária nem código React. Ele escolhe uma capability conhecida e o Portal executa o comando validado.

## 9. WorkspaceContextBridge

Responsável por sincronizar contexto útil do Portal/MFE/iframe com o Copilot:

```text
appId
routeId
entityRefs
filters
dateRange
selection
visibleDataRefs
presentationState
```

O contexto deve ser pequeno, estruturado, versionado e sem despejar estado React completo ou DOM.

## 10. Capability Discovery

O planner não recebe o universo inteiro indiscriminadamente.

```text
permissions efetivas
→ capabilities permitidas
→ semantic retrieval
→ top-K
→ planner restrito aos candidates
```

O mesmo princípio já usado para Actions OpenAPI deve ser expandido para capabilities da plataforma.

## 11. Expertise Discovery

Também não carregar todas as especializações em todo turno.

```text
goals + entities + workspace + attachments + project preferences
→ expertise semantic retrieval
→ policy/compatibility filter
→ top-K Expertise Packs
→ playbooks relevantes
→ bounded expertise context
```

A seleção é dinâmica. O usuário não precisa alternar manualmente entre agentes.

### Regra crítica

```text
expertise selecionada
≠ permission concedida
```

O pack pode recomendar capabilities, mas o planner só recebe/executa as permitidas ao usuário.

## 12. Domain Playbooks

Playbooks descrevem método, não implementação técnica.

```text
playbook
→ goals/stages/evidence checklist/decision criteria
+ authorized capabilities
+ current context
→ WorkflowPlan
```

Exemplos:

- `quality.8d`;
- `quality.root-cause`;
- `engineering.drawing-review`;
- `operations.delivery-delay-analysis`.

Fonte: [`29-domain-playbooks-specification.md`](./29-domain-playbooks-specification.md).

## 13. Multimodalidade

Documentos, imagens e desenhos entram como evidência estruturada:

```text
attachment
→ native/OCR/VLM extraction
→ structured evidence + provenance/confidence
→ expertise/playbook interpretation
→ optional Business/Knowledge Actions
→ grounded synthesis
```

A percepção não deve ser acoplada a um agente selecionado.

Fonte: [`30-multimodal-expertise-and-drawing-analysis.md`](./30-multimodal-expertise-and-drawing-analysis.md).

## 14. Execução agentic

O executor deve operar em ciclos observáveis:

```text
PLAN
→ ACT
→ OBSERVE
→ UPDATE STATE
→ CONTINUE | COMPLETE | CLARIFY
```

"Agentic" aqui descreve o padrão de execução/autonomia, **não múltiplas identidades de agente por departamento**.

Limites de segurança e custo controlam número de passos, tools, retries e profundidade.

## 15. Persistência

Persistir estado suficiente para continuidade sem depender de reinterpretação total:

- goals;
- selected capabilities;
- selected expertise refs quando relevante;
- selected playbook refs;
- resolved entities;
- resolved arguments;
- pending requirements;
- result references;
- workspace context relevante;
- project context;
- confirmations;
- audit events.

Não persistir chain-of-thought.

Expertise selecionada no turno não deve virar authority permanente; turnos futuros podem reavaliar conforme objetivo/contexto.

## 16. Migração do modelo atual de agents

A base atual possui conceitos de agent activation, specialization, skills e soft handoff. A arquitetura alvo exige migração incremental:

```text
agent specialization
→ Expertise Packs / knowledge scopes

agent-bound operational tools
→ authorized capabilities + policy

soft agent handoff
→ expertise/capability retrieval + clarify/unavailable

agent/project customization
→ Project Context + preferred expertise quando aplicável
```

Sessões legadas precisam de compatibilidade temporária, porém `LEGACY_FALLBACK` material não pode permanecer como solução final.

Fonte: [`31-agent-to-expertise-migration-plan.md`](./31-agent-to-expertise-migration-plan.md).

## 17. Clean Architecture

### Domain

- modelos de capability;
- modelos/regras puras de expertise e playbook;
- policies puras;
- contracts de plan/confirmation;
- regras de autonomia;
- sem filesystem/HTTP/DB/LLM.

### Application

- discover capabilities;
- retrieve expertise/playbooks;
- compose bounded expertise context;
- plan task;
- execute workflow;
- bind arguments;
- coordinate confirmation;
- build response/render commands;
- coordinate multimodal evidence.

### Infrastructure

- Core/RBAC gateway;
- OpenAPI catalog repository;
- Portal capability repository;
- Expertise/Playbook repositories/indexes;
- HTTP execution;
- LLM/embedding providers;
- multimodal adapters;
- persistence;
- vector/search adapters.

### Interfaces

- REST/SSE;
- Portal events;
- admin endpoints.

### Composition

- DI/wiring de implementations concretas.

## 18. Alterações arquiteturais obrigatórias a inventariar/implementar

O C0.S0 deve mapear o runtime atual e preparar mudanças em especial:

1. `ChatWorkspaceAgentActivationService`: remover dependência conceitual de agente ativo para habilitar tools operacionais;
2. `ChatSoftAgentHandoffService`: substituir troca de agente por recuperação/replanejamento de expertise/capability;
3. `AgentSpecializationService`: migrar presets úteis para Expertise Packs/knowledge scopes;
4. `ChatSkillRegistry`: preservar skills úteis, mas desacoplar `has_agent` quando não for requisito real e eliminar semântica técnica frágil incompatível com OpenAPI-first;
5. sessão/persistência: tratar `agent_id` como compatibilidade legada onde aplicável;
6. UI: remover dependência de seleção manual de agente no Copilot após migration gates;
7. projetos: separar customização/contexto de projeto da identidade do Copilot.

Plano de execução: [`32-expertise-runtime-implementation-plan.md`](./32-expertise-runtime-implementation-plan.md).

## 19. Requisitos de escalabilidade

- novo app não exige editar o planner central;
- novo endpoint OpenAPI não exige selector dedicado;
- novo Expertise Pack não exige editar planner central;
- novo Playbook compatível não exige criar agente;
- capabilities/expertise/playbooks podem ser indexados e buscados semanticamente;
- catálogos podem ser materializados/cacheados sem virar authority paralela;
- execução deve ser idempotente quando contrato permitir;
- writes precisam de correlation/audit ids;
- workflows longos precisam checkpoints e recuperação;
- um pedido cross-domain deve compor especializações no mesmo turno.

## 20. Critério arquitetural de sucesso

O sistema deve suportar, sem troca de agente:

> "Analise este desenho, verifique os riscos de qualidade, consulte reclamações semelhantes, compare fornecedores e monte um 8D preliminar."

O mesmo runtime deve ativar Engenharia + Qualidade + Suprimentos, multimodalidade, RAG e Business Actions autorizadas, preservando identidade, contexto, RBAC, policy e audit.