# Arquitetura — minha-delpi-ai-api

> **Público:** backend, revisores de PR, agentes Cursor  
> **Princípio:** o **chat base** concentra a inteligência transversal; agentes adicionam prompt, skills e actions.

---

## Documento principal

**Leitura obrigatória:** [`chat-intelligence-base.md`](./chat-intelligence-base.md)

Contém o mapa completo de serviços (~200 entradas), roteamento api-delpi, streaming, apresentação rica, memória, web search e checklist para novas features.

---

## Índice por domínio

### Pipeline e turno

| Documento | Assunto |
|-----------|---------|
| [chat-intelligence-base.md](./chat-intelligence-base.md) | Pipeline send/stream, serviços centrais, roteamento |
| [chat-pre-llm-layers.md](./chat-pre-llm-layers.md) | Fases ingresso → resolução → montagem LLM |
| [intent-routing.md](./intent-routing.md) | `ChatIntentRouterService`, intents, metadata |
| [session-memory.md](./session-memory.md) | Memória de sessão, assertividade, projeto compartilhado |

### Apresentação e conteúdo

| Documento | Assunto |
|-----------|---------|
| [new-api-route-checklist.md](./new-api-route-checklist.md) | **Nova rota** — HTTP, registry, perfil, CI |
| [chat-assistant-content-presentation.md](./chat-assistant-content-presentation.md) | `presentationDecision`, stack, multi-rota, MFE |
| [assistant-content-catalog.md](./assistant-content-catalog.md) | Bundles JSON e serviços loader |
| [product-operational-content.md](./product-operational-content.md) | Escopos de produto, plural, estoque |
| [presenter-content-migration-audit.md](./presenter-content-migration-audit.md) | Auditoria migração presenter → JSON |
| [humanized-narrative-stack-jun2026.md](./humanized-narrative-stack-jun2026.md) | Narrativa pós-tool (panorama, atenção) |
| [vocabulary-centralization-jun2026.md](./vocabulary-centralization-jun2026.md) | Vocabulário SQL e intent centralizado |

### Capacidades transversais

| Documento | Assunto |
|-----------|---------|
| [email-writing.md](./email-writing.md) | E-mail corporativo (intent, guard, chips) |
| [text-correction.md](./text-correction.md) | Correção de texto, typos, composer |
| [continuous-learning.md](./continuous-learning.md) | Aprendizado contínuo (planejado) |

### Decisões e baseline

| Documento | Assunto |
|-----------|---------|
| [adr/README.md](./adr/README.md) | ADRs aceitos (chat base, send/stream, JSON, ports) |
| [clean-architecture-baseline.json](./clean-architecture-baseline.json) | Baseline auditoria CI |
| [presentation-refactor-baseline-jun2026.json](./presentation-refactor-baseline-jun2026.json) | Baseline apresentação declarativa |

---

## Modelo de camadas

```text
interfaces/http/routes/     Handlers finos — delegam a use cases via composition
        │
        ▼
composition/*_composer    Composition root (make_send_chat_message, …)
        │
        ▼
application/
  use_cases/              SendChatMessage, StreamChatMessage, ExecuteExternalAction…
  services/               ChatTurnPreparation*, ChatToolContext*, stream…
        │
        ▼
domain/
  services/               Intent, presenter, SQL, memória, identidade…
  prompt_policies/        Instruções Markdown injetadas no LLM
  ports/                  Contratos (LlmGateway, repos, AssistantContent…)
        │
        ▼
infrastructure/           Postgres, Ollama/vLLM, HTTP api-delpi, loaders JSON
```

**Regra de ouro:** melhorias de inteligência vão em `domain/services` ou `application/services` compartilhados — **nunca** só no prompt de um agente ou só no use case.

Playbook detalhado: [`../roadmap/playbook-11-clean-architecture-chat-api.md`](../roadmap/playbook-11-clean-architecture-chat-api.md).  
Organização dos ~600 services: [`../roadmap/playbook-20-organizacao-services-chat.md`](../roadmap/playbook-20-organizacao-services-chat.md).

---

## Fluxo de um turno (resumo)

```text
POST /chat/sessions/{id}/messages/stream
  │
  ├─► ChatTurnSideEffectsService (efeitos iniciais)
  ├─► ChatSimpleTurnGateService? → resposta direta, sem activity
  ├─► ChatTurnPreparationService.prepare()
  │     ├─ workspace (agente, projeto, capabilities)
  │     ├─ intent / direct answer / pending (missing_product_code, missing_date)
  │     ├─ tools + ExternalActionSelectionService
  │     ├─ RAG
  │     └─ flags skipRag, analysisMode, fastPath
  ├─► ChatTurnLlmAssemblyService (prompt + LLM se necessário)
  ├─► ChatTurnCompletionService (metadata, memória, adminDebug)
  └─► SSE: user_persisted → activity → playback → done
```

Send síncrono usa os **mesmos** serviços de preparação e conclusão — ver [ADR 002](./adr/002-send-stream-turn-parity.md).

---

## Onde implementar cada tipo de mudança

| Mudança | Camada canônica | Não duplicar em |
|---------|-----------------|-----------------|
| Nova intenção / roteamento | `domain/services/*IntentService` | use case, prompt agente |
| Nova rota api-delpi (completa) | [new-api-route-checklist.md](./new-api-route-checklist.md) | endpoint isolado sem perfil/registry |
| Seleção de action existente | `ExternalActionSelectionService` + `api_route_domains.json` | heurística no MFE |
| Formato Automático (tabela/gráfico) | `ChatPresentationViewIntentService` + perfis JSON | MFE, prompt agente |
| Texto PT para usuário | `app/content/pt-BR/assistant/*.json` | Python/TS literal |
| Título/coluna de tabela | `presenter_content.json` + presenter | system_prompt |
| Policy LLM global | `domain/prompt_policies/*.md` | agente individual |
| Novo visual na resposta | `ExternalActionResultPresenter` + metadata | componente MFE isolado |
| Skip de tools | `ChatTurnPreparationToolRoutingService` | flags só no frontend |

Mapa Cursor: `.cursor/rules/centralized-rules-first.mdc`.

---

## Sub-sistemas (entrada no código)

| Sub-sistema | Serviço principal | Doc |
|-------------|-------------------|-----|
| Turno send/stream | `ChatTurnPreparationService` | [chat-intelligence-base § Turno](./chat-intelligence-base.md) |
| Tools & actions | `ChatToolContextService` | [chat-intelligence-base § Roteamento](./chat-intelligence-base.md) |
| Presenter | `ExternalActionResultPresenter` | [chat-assistant-content-presentation](./chat-assistant-content-presentation.md) |
| Conteúdo JSON | `ChatAssistantContentService` | [assistant-content-catalog](./assistant-content-catalog.md) |
| SQL avançado | `ChatAdvancedSqlSpecialistService` | [chat-intelligence-base § SQL](./chat-intelligence-base.md) |
| Anexos & OCR | `ChatDocumentVisionService` | [roadmap onda 13](../roadmap/inteligencia-chat-onda-13-skill-visao-documentos-ocr.md) |
| Memória | `ChatConversationMemoryService` | [session-memory](./session-memory.md) |
| HTTP modular | `interfaces/http/routes/chat/` | [ADR 005](./adr/005-http-routes-modular-facade.md) |

---

## ADRs

| ADR | Decisão |
|-----|---------|
| [001](./adr/001-chat-base-intelligence.md) | Inteligência no chat base |
| [002](./adr/002-send-stream-turn-parity.md) | Paridade send/stream |
| [003](./adr/003-assistant-content-json.md) | Textos em JSON |
| [004](./adr/004-repository-ports-composition-root.md) | Ports e composition root |
| [005](./adr/005-http-routes-modular-facade.md) | HTTP modular |
| [006](./adr/006-hardcoded-pt-strings-baseline-gate.md) | Gate CI strings PT |

---

## Referências externas

- Contrato api-delpi → chat: [`../roadmap/playbook-10-contrato-respostas-api-delpi.md`](../roadmap/playbook-10-contrato-respostas-api-delpi.md)
- **Nova rota (checklist):** [new-api-route-checklist.md](./new-api-route-checklist.md)
- Auditoria rotas: [`../roadmap/api-delpi-chat-intelligence-audit.md`](../roadmap/api-delpi-chat-intelligence-audit.md)
- Guia desenvolvedor: [`../development/guia-desenvolvimento.md`](../development/guia-desenvolvimento.md)
