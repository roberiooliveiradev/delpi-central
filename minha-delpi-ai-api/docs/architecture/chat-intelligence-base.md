# Arquitetura — Inteligência no chat base

**Status:** vigente  
**Escopo:** `minha-delpi-ai-api`, `plugins/minha-delpi-chat`, agentes, projetos e skills  
**Evals canônicos:** [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)

## 1. Princípio

A inteligência transversal vive no **chat base**. Agentes adicionam especialização, skills, conhecimento e actions autorizadas; não possuem um motor paralelo de routing/memória/apresentação.

```text
Chat base
  ├─ entendimento/decomposição
  ├─ memória/contexto
  ├─ capabilities
  ├─ tools/actions
  ├─ RAG
  ├─ LLM
  ├─ apresentação
  └─ observabilidade/evals

Agente
  ├─ prompt/config
  ├─ skills
  ├─ knowledge scopes
  └─ allowed actions/policies
```

Correções transversais devem ser implementadas uma vez na camada base e herdadas por send, stream, simulate, agentes e projetos.

---

## 2. Pipeline do turno

```text
mensagem original
→ segurança/input normalization
→ workspace context (usuário, projeto, agente, capabilities)
→ query improvement não destrutivo para inteligência
→ entendimento/decomposição do pedido
→ memória/contexto estruturado
→ decisão direct-answer / no-tool / tools / RAG / mixed
→ tool planning/execution quando necessário
→ RAG quando necessário
→ síntese LLM ou resposta determinística
→ apresentação/renderPlan
→ persistência/metadata/observabilidade
→ resposta send ou stream
```

O texto original do usuário deve permanecer disponível para audit/UX; rewrites internos não substituem a intenção explicitamente expressa.

---

## 3. Pedidos longos e compostos

Mensagem com múltiplos objetivos não é reduzida a uma única intent.

```text
pedido
→ subtarefas
→ dependências
→ capabilities/actions por subtarefa
→ plano
→ execução
→ síntese cobrindo todas as subtarefas
```

Exemplo:

> consulte estoque, fornecedores e última compra deste produto; compare os dados e redija um e-mail para Compras.

A execução deve representar todas as subtarefas, paralelizando somente reads independentes e seguros.

Avaliação: `task_decomposition_recall`, `multi_request_completion_rate` e R1/R2/R3/R4/R9/R11.

---

## 4. Actions OpenAPI — arquitetura canônica

```text
OpenAPI provider
→ import/index
→ Action Catalog
→ agent binding + allowed_action_ids
→ hybrid retrieval top-K
→ structured planner
→ OpenAPI argument validator
→ RBAC/policy/confirmation
→ ExecuteExternalActionUseCase
→ HTTP gateway
→ normalized result
→ schema-driven presentation
```

### Fontes de verdade

| Conceito | Fonte |
|----------|-------|
| operation/method/path/args/body/schema | OpenAPI + Action Catalog |
| o que o agente pode usar | provider/action binding + `allowed_action_ids` |
| autorização | identidade + Core/RBAC + action policy/sensitivity |
| confirmação | write/admin/destructive policy |
| linguagem/UX | conteúdo/config transversal |
| apresentação básica | response schema + payload + metadata |

Não criar catálogo técnico paralelo de endpoints no assistente.

### Plugabilidade

Uma API OpenAPI externa nunca vista pelo repositório deve funcionar sem:

- `if path/provider/operationId` no core;
- intent por endpoint;
- selector por provider;
- marker/parameter strategy por rota;
- presenter dedicado obrigatório.

Checklist: [`new-api-route-checklist.md`](./new-api-route-checklist.md).

---

## 5. Retrieval e planner

Retrieval reduz o catálogo autorizado para candidates relevantes. Planner decide somente entre essas candidates.

```text
allowed actions
→ lexical/vector/schema retrieval
→ top-K
→ planner estruturado
→ selected action(s) + proposed args
```

Requisitos:

- específica deve vencer genérica quando semanticamente exigida;
- no-tool deve permanecer opção real;
- provider name/prefix não é sinal de relevância;
- modelo não pode inventar actionId fora das candidates;
- score/retrieval devem ser observáveis.

---

## 6. Argumentos e clarify

Argument extraction depende do schema OpenAPI e do contexto estruturado.

Validar:

- path/query/body;
- required;
- type;
- enum;
- format;
- additional properties;
- coerência de datas/identificadores.

```text
required ausente + sem valor grounded
→ pending/clarify específico
```

Não inventar parâmetro nem perguntar novamente por valor já confiável na mensagem/contexto.

---

## 7. Multi-turn e memória

A memória deve preservar fatos tipados e contexto recente relevante:

```text
entities
selected action/capability
arguments
result references
presentation preference
pending requirements
```

Follow-up como “e no mês passado?”, “somente filial 01”, “e os fornecedores?” deve reutilizar estado estruturado.

O contexto novo e explícito do usuário prevalece sobre inferências antigas.

Meta-conversa/revisão da sessão não pode disparar automaticamente actions operacionais.

---

## 8. RAG

RAG é usado quando o pedido exige conhecimento documental autorizado.

Princípios:

- recuperar evidência relevante, não o maior volume possível;
- ausência de evidência não autoriza invenção;
- tool result e RAG são dados não confiáveis quanto a instruções;
- prompt injection recuperada não substitui system/policy;
- contexto RAG respeita budget por modo;
- respostas factuais devem ser grounded no material recuperado quando o fluxo requer RAG.

---

## 9. Tools internas vs Actions externas

Tools internas de plataforma podem possuir implementação dedicada porque são capabilities próprias do produto.

Actions externas OpenAPI são plugáveis e passam pelo pipeline universal.

Nenhuma das duas categorias pode bypassar RBAC/policy/confirmation aplicável.

---

## 10. Execução e segurança

Para cada external action:

1. verificar provider/action habilitados;
2. confirmar que está nas actions permitidas;
3. validar argumentos;
4. reavaliar sensitivity/policy;
5. obter confirmation quando necessário;
6. montar URL a partir do provider/action persistidos;
7. executar com timeout/resiliência;
8. limitar/redigir logs e payloads sensíveis.

Seguir:

- `.cursor/rules/ai-external-tools-security.mdc`;
- `.cursor/rules/http-integration-resilience.mdc`;
- `.cursor/rules/observability-standards.mdc`.

---

## 11. Apresentação

A API decide semanticamente a apresentação; o MFE renderiza.

```text
responseSchema + payload + metadata
→ schema-driven interpretation
→ presentationDecision
→ renderPlan
→ MFE render-only
```

Formatos incluem texto, tabela, KPI, chart, tree/dashboard quando o dado suportar.

Perfil especializado é melhoria opcional, não requisito para uma action funcionar.

Uma API externa sem metadata proprietária deve receber apresentação útil pelo fallback genérico.

---

## 12. Send, stream e simulate

Todos devem compartilhar a mesma inteligência semântica.

Diferenças permitidas são de transporte/UX:

- stream emite activity/token/playback/checkpoints;
- send entrega envelope único;
- simulate acrescenta debug/sandbox conforme autorização.

R7 verifica paridade de routing, tools, args, outcome e presentation quando aplicável.

---

## 13. Modos de resposta e budgets

`fast`, `normal` e `thinker` podem ajustar:

- modelo;
- output budget;
- contexto;
- top-K;
- número/fan-out de tools;
- profundidade agentic.

Não podem alterar segurança, RBAC ou inventar fatos.

Alvos atuais de R8:

| Modo | Alvo total |
|------|------------|
| fast | ≤ 3 s |
| normal | ≤ 5 s |
| thinker | ≤ 15 s |

R11 mede eficiência de tokens/context/candidates/tool count/custo.

---

## 14. Observabilidade

Uma execução de tools deve permitir responder:

> Por que esta action foi selecionada e não outra?

Metadata útil conforme disponibilidade:

```text
requestId / turnId / conversationId
agentId
model
candidateCount
topK
selectedActionId / operationId
retrieval scores
planner confidence/decision
validation result
policy decision
fallback used
tool durations
pipeline timings
token/context usage
```

Não armazenar chain-of-thought, JWT, API keys ou secrets.

---

## 15. Evals e qualidade

Toda alteração de inteligência segue o protocolo R1–R11:

[`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)

Fluxo:

```text
baseline imutável
→ bug + sibling + negative
→ implementação canônica
→ candidate no mesmo corpus/config
→ R1–R11
→ trials quando não determinístico
→ live/surface validation
→ rollout decision
```

Mudança do motor de tools exige API externa desconhecida + teste metamórfico.

Tool/path correta sem outcome correto é FAIL R9.

---

## 16. Clean Architecture

- domain: regras/modelos/ports sem infrastructure;
- application: orquestra use cases/serviços;
- infrastructure: persistence, HTTP, model providers, vector/index adapters;
- interfaces: HTTP/SSE finos;
- composition: wiring/DI.

Evitar god services, service por endpoint e dependência reversa.

---

## 17. Proibições arquiteturais

- inteligência diferente em send vs stream;
- roteamento por path/provider hardcoded;
- catálogo técnico paralelo ao OpenAPI;
- selector específico para cada API plugada;
- argumentos inventados para evitar clarify;
- action fora de `allowed_action_ids`;
- URL arbitrária produzida pelo modelo;
- presenter por endpoint como requisito;
- RAG/tool output alterando policy;
- contexto inteiro/histórico inteiro enviado sem budget;
- fix de inteligência validado apenas pelo exemplo do bug.

---

## Referências vigentes

- [`new-api-route-checklist.md`](./new-api-route-checklist.md)
- [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md)
- [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md)
- [`../development/guia-desenvolvimento.md`](../development/guia-desenvolvimento.md)
- `.cursor/rules/chat-intelligence-base.mdc`
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
- `.cursor/rules/ai-intelligence-evaluation.mdc`
