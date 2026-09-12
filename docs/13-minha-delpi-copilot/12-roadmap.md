# 12 — Roadmap de implementação

## Visão geral

A implantação deve ser incremental. O objetivo é gerar valor cedo sem transformar o Copilot em um motor paralelo de UI automation.

```text
Fase 0 — Fundamentos e contratos
Fase 1 — Platform Actions + CopilotBridge
Fase 2 — Workspace Context
Fase 3 — Business Capability Parity
Fase 4 — Agentic Workflows
Fase 5 — AI-ready ecosystem
Fase 6 — Autonomia governada e otimização
```

---

# Fase 0 — Fundamentos e contratos

## Objetivo

Preparar o modelo conceitual sem alterar ainda o comportamento dos apps.

## Entregas

- modelo `Capability`;
- categorias e sensitivity;
- contratos de `PlatformCommand`;
- contrato de `WorkspaceContext`;
- estratégia de Authorized Capability View;
- ownership e boundaries;
- eventos de audit/observability;
- testes de contrato.

## Critério de saída

```text
CAPABILITY_MODEL = APPROVED
PLATFORM_COMMAND_SCHEMA = APPROVED
WORKSPACE_CONTEXT_SCHEMA = APPROVED
SECURITY_MODEL = APPROVED
```

---

# Fase 1 — Platform Actions + CopilotBridge

## Objetivo

Fazer o Copilot navegar pela Minha DELPI de forma segura e contextual.

## Escopo mínimo

- `portal.open_app`;
- `portal.open_route`;
- `portal.open_entity` para uma entidade piloto;
- `portal.select_tab`/`set_view_context` em um app piloto;
- capability catalog derivado de apps/rotas autorizados;
- `CopilotBridge` no Shell;
- result/observation de navegação;
- activity no chat.

## Piloto sugerido

Portal Comercial ou Portal de Suprimentos, escolhendo um app com rotas e entidades já estáveis.

## Evals

- usuário autorizado abre app;
- usuário sem permissão não recebe capability;
- app desconhecido registrado dinamicamente funciona sem patch no planner;
- URL arbitrária é rejeitada;
- F5 preserva conversa e reconstrói contexto de navegação seguro.

---

# Fase 2 — Workspace Context Protocol

## Objetivo

Permitir perguntas e comandos relativos à tela atual.

## Entregas

- `WorkspaceContextBridge` no Portal;
- adapter padrão para MFEs;
- entity refs;
- filters;
- selection;
- visible data refs;
- context chips no composer;
- prioridade do contexto explícito da mensagem;
- persist/reload rules.

## Casos de aceite

```text
“explique este cliente”
“e os pedidos dele?”
“agora só filial 01”
“abra esse pedido”
```

sem exigir repetição de IDs já disponíveis.

---

# Fase 3 — Business Capability Parity

## Objetivo

Transformar operações reais dos apps em capabilities executáveis pela IA.

## Estratégia

Não tentar cobrir toda a plataforma de uma vez.

### Onda 3A — Reads

- produto;
- estoque;
- cliente;
- pedidos;
- compras;
- indicadores;
- solicitações.

### Onda 3B — Writes de baixo risco

- criar solicitação;
- adicionar comentário;
- alterar responsável;
- registrar observação.

### Onda 3C — Aprovações e operações sensíveis

- aprovar/rejeitar;
- cancelar;
- alterar cadastros críticos.

## Entrega por app

Manter matriz UI → use case/API → capability → permission → sensitivity.

---

# Fase 4 — Agentic Workflows

## Objetivo

Permitir tarefas compostas multi-app.

## Entregas

- Goal DAG;
- step dependencies;
- parallel reads;
- checkpoints;
- partial failure;
- replan;
- confirmation resumida de múltiplos writes;
- workflow audit trail;
- limits/budgets.

## Caso-âncora

```text
“Analise por que este item está atrasado,
abra os dados relevantes,
crie uma solicitação para Compras
e avise o responsável.”
```

---

# Fase 5 — Ecossistema AI-ready

## Objetivo

Fazer novos apps entrarem no Copilot por contrato, sem projeto manual de integração.

## Entregas

- checklist AI-ready no template de plugins;
- OpenAPI quality gates;
- Workspace Context adapter template;
- entity deep link metadata;
- UI capability registration;
- smoke “unknown app”;
- dashboard de capability coverage.

## Meta

Novo app padrão deve conseguir:

```text
ser descoberto
→ ser aberto
→ publicar contexto
→ expor reads/writes
→ funcionar no Copilot
```

sem alterar o core genérico da IA.

---

# Fase 6 — Autonomia governada

## Objetivo

Aumentar automação sem aumentar risco indevidamente.

## Entregas

- policies L0–L5 por capability;
- auto-execution allowlists governadas;
- workflow templates;
- scheduled/triggered workflows quando houver infraestrutura apropriada;
- budget por usuário/agente;
- cost optimization;
- feedback/eval loops;
- progressive rollout.

---

# Dependências arquiteturais

Antes de avançar para writes em escala, o programa atual de OpenAPI-first/LLM deve estar com os gates materiais resolvidos. O Copilot não deve ampliar o alcance de uma camada de actions ainda inconsistente.

Especialmente:

- Action Catalog universal;
- schema-driven binding;
- RBAC/policy/confirmation;
- evidence/evals confiáveis;
- unknown-provider generalization;
- clean architecture do executor.

---

# Priorização recomendada

## MVP de percepção de valor

```text
Fase 1 + parte da Fase 2
```

Isso permite rapidamente:

> “Abra o Portal Comercial.”

> “Vá para pedidos em aberto.”

> “Explique este cliente.”

sem ainda introduzir riscos grandes de escrita.

## MVP operacional

```text
Fase 3A + 3B
```

Permite consultar e criar solicitações simples.

## Copilot pleno

```text
Fase 4 + Fase 5
```

Passa a executar objetivos multi-app e a aprender novos apps por contrato.

---

# Regras de rollout

Cada fase segue:

```text
PLAN
→ CONTRACTS
→ PILOT
→ EVALS
→ CANARY
→ OBSERVABILITY
→ SCALE
```

Nunca fazer rollout global de write capability sem eval de autorização, confirmação, idempotência e recuperação de falha.

---

# Primeira implementação recomendada

A primeira implementação concreta deve ser:

```text
Portal Capability Catalog
+ CopilotBridge
+ portal.open_app
+ portal.open_route
+ Workspace Context mínimo
```

Por quê:

- alto impacto perceptível;
- baixo risco de negócio;
- reutiliza `/me/apps` e Router existentes;
- estabelece protocolo Shell ↔ Copilot;
- prepara todas as fases seguintes.
