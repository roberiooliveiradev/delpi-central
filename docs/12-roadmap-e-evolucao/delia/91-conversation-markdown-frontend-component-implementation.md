# 91 — Implementação frontend `ConversationMarkdown` (CP-333)

**Task:** `DELIA-UX-CONVERSATION-MARKDOWN-FRONTEND-COMPONENT-IMPLEMENTATION-01`  
**Tipo:** FRONTEND IMPLEMENTATION + TESTS + FEDERATION — **sem** producer backend `presentation.v2`, **sem** binding L1, **sem** deploy, **sem** ACT.  
**Data:** 2026-10-16

## Estado factual

```text
PLUGIN_UI_COMPONENT = IMPLEMENTED
DELIA_FRONTEND_IMPORT = IMPLEMENTED
DELIA_INTEGRATION = IMPLEMENTED
LEGACY_V1_BEHAVIOR = PRESERVED
RUNTIME_MARKDOWN_ACTIVATION = OFF (sem emitter v2 real)
BACKEND_V2_PRODUCER = NOT_IMPLEMENTED
L1_BINDING = NOT_PROVEN
NAVIGABLE_LINK_EMISSION = BLOCKED_UNTIL_CONTRACT
CP_333 = PLANNED_NOT_PASS
PHASE_PROGRESSION = NONE
```

## Reuse

| Recurso | Decisão |
|---|---|
| `marked.lexer` | REUSE |
| Primitives/CSS kit | REUSE (`conversation-markdown.css`) |
| Renderers HTML (`MarkdownDocument`, rich-text) | DO_NOT_REUSE (conversa) |
| `ConversationMarkdown` | NEW em `plugin-ui` |
| DÉLIA MFE | Consumidor |

## Entrega

- `plugins/plugin-ui/.../ConversationMarkdown.tsx` + `conversationMarkdownModel.ts` (token→React, bounds, links fail-closed, copy plain).
- Export público + gate `verify-host-exports` (`ConversationMarkdown`, `conversationMarkdownToPlainText`).
- `plugins/delia/.../presentation.ts`: `parsePresentationV2` parse-only (schema proposal doc 84).
- `DeliaAssistantMessage`: ativa Markdown **somente** com `contentFormat=markdown_safe` + `markdownSource` admitidos; v1 permanece literal; fault → erro neutro.
- Links: `authorizedLinks` vazio no App até contrato L1; fixtures cobrem navegável vs inerte.

## Evidência de testes (executor)

| Superfície | Resultado |
|---|---|
| plugin-ui `ConversationMarkdown.test.tsx` | **20 PASS** |
| delia `presentation` + `DeliaAssistantMessage` + suite | **202 PASS** (16 files) |
| plugin-ui `vite build` + verify-host-exports | **PASS** |
| delia `vite build` + `verify:federation` | **PASS** |
| delia `tsc` | **PASS_WITH_PREEXISTING_DEBT** (InitialsAvatar / UnifiedAvatar / TaskDetailCard — fora do escopo) |
| Browser QA full-page/dock | **TEST_NOT_RUN** (runtime Markdown OFF; sem deploy) |
| SSH read-only | REMOTE SHA/topology/health; v1 producer; `DEPLOY_NOT_AUTHORIZED` |

## Não-claims

Não promove CP-333. Não autoriza G3 end-to-end. Não emite links. Não altera backend/Core/AuthZ/Domain. Aceite independente pendente.
