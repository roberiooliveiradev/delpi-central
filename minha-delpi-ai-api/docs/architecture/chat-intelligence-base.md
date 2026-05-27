# Arquitetura — Inteligência no chat base

**Status:** vigente (maio/2026)  
**Público:** desenvolvimento `minha-delpi-ai-api`, plugin `minha-delpi-chat`, gestão de agentes

---

## Princípio

O **chat** é onde a inteligência transversal evolui. **Agentes** são instâncias de chat com mais habilidades, contextos e actions — não um motor paralelo.

| Conceito | Papel |
|----------|--------|
| **Chat (sessão)** | Pipeline de mensagens, histórico, tools, RAG, LLM |
| **Agente** | `system_prompt`, skills, actions permitidas, especialização de conhecimento |
| **Projeto** | Prompt de projeto, agente padrão, agrupamento de sessões |
| **Simulação / admin** | Mesmo pipeline, com rascunho ou sandbox |

Melhorias de inteligência (comparação, insights, fast path operacional, resposta direta, contexto de ferramentas no histórico) devem ser implementadas na **camada base** e **herdadas** automaticamente por agentes, projetos e demais consumidores.

---

## Pipeline base

```text
Mensagem do usuário
  → Segurança (input)
  → ChatWorkspaceContextService (projeto + agente + capabilities)
  → ChatIntelligencePipelineService
        · decisão operacional / análise
        · contexto de conversa (incl. previews de tools no histórico)
  → ChatToolContextService (seleção e execução de tools/actions)
        · finalize: modo análise, supressão de direct answer
  → RAG (escopo agente/projeto/anexos)
  → ChatPromptBuilderService + prompt_policies
  → LLM (stream ou send)
```

### Serviços centrais

| Serviço | Função |
|---------|--------|
| `ChatIntelligencePipelineService` | Orquestra decisões pré/pós-tools compartilhadas |
| `ChatConversationContextService` | Texto de histórico + dados de `toolCalls` em metadata |
| `ChatAnalysisIntentService` | Detecção de comparação / insights |
| `ChatCanvasIntentService` | Pedido de enviar conteúdo à lousa (não confunde com Canva.com) |
| `ChatCanvasContentService` | Monta markdown da última resposta assistant + confirmação |
| `ChatToolContextService` | Execução de tools; aceita `previous_messages` para herdar análise |
| `ChatOperationalPipelineService` | Fast path operacional (desligado em modo análise) |
| `ExternalActionSelectionService` | Roteamento OpenAPI (não dispara consulta em pedido analítico nem em pedido de lousa) |
| `PromptPolicyService` | Policies globais (`operational-agent.md`, `chat-analysis-insights.md`, …) |

Use cases (`SendChatMessageUseCase`, `StreamChatMessageUseCase`, `AdminAgentSimulateUseCase`) **não** devem acumular regras de inteligência — apenas passam histórico e flags ao pipeline.

---

## O que o agente adiciona (e só isso)

1. **Prompt** — personalidade e instruções (`system_prompt`).
2. **Skills** — policies extras (`metadata.skills`).
3. **Actions** — subset de rotas OpenAPI (`allowedActionIds` / providers).
4. **RAG** — filtros de especialização (tags, categorias, namespaces).
5. **Limites** — `max_tool_calls`, confirmação de escrita, capabilities.

O agente **não substitui** detecção de intenção, pipeline operacional ou modo análise comparativa.

---

## Checklist para novas features de inteligência

- [ ] Implementação em serviço/domain compartilhado (não só no JSON do agente).
- [ ] `ChatToolContextService` ou pipeline atualizado se afetar tools/histórico.
- [ ] Policy em `prompt_policies/` se mudar comportamento do LLM para todos.
- [ ] Testes unitários + caso em `chat_intelligence_regression_cases.py` quando aplicável.
- [ ] Sem duplicar lógica entre stream e send.
- [ ] Simulação admin recebe `previous_messages` quando depender de histórico.

---

## Referências

- Roadmap onda 1 (pipeline): [`../roadmap/inteligencia-chat-onda-1.md`](../roadmap/inteligencia-chat-onda-1.md)
- Agentes (HTTP): [`../api/03-agentes.md`](../api/03-agentes.md)
- Modelo conceitual: [`../api/12-modelo-conceitual.md`](../api/12-modelo-conceitual.md)
- Regra Cursor: [`.cursor/rules/chat-intelligence-base.mdc`](../../../.cursor/rules/chat-intelligence-base.mdc)
