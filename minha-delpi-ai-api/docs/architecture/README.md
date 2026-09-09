# Arquitetura — Minha DELPI AI API

**Status:** vigente  
**Público:** backend, revisores e agentes Cursor

Este diretório contém somente fontes arquiteturais atuais. Implementação deve começar pelo documento principal e pelas regras `.cursor` aplicáveis, não por playbooks ou changelogs datados.

## Leitura principal

| Ordem | Fonte | Responsabilidade |
|------:|-------|------------------|
| 1 | [`chat-intelligence-base.md`](./chat-intelligence-base.md) | Pipeline transversal do chat, contexto, tools, RAG, segurança e apresentação |
| 1b | [`presentation-intelligence.md`](./presentation-intelligence.md) | Profile, labels PT-BR, PresentationSpec, validator/compiler, optional composer |
| 2 | [`new-api-route-checklist.md`](./new-api-route-checklist.md) | Nova API/Action OpenAPI |
| 3 | [`assistant-content-catalog.md`](./assistant-content-catalog.md) | Conteúdo declarativo do assistente sem duplicar contrato técnico |
| 4 | [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md) | Protocolo canônico R1–R11 |
| 5 | [`../flows/README.md`](../flows/README.md) | Fluxos operacionais vigentes |

## Arquitetura do turno

```text
mensagem
→ preparação + workspace context
→ entendimento/decomposição
→ contexto/memória estruturados
→ direct / no-tool / Actions / RAG / mixed
→ allowed Actions + Action Catalog
→ retrieval top-K
→ planner estruturado
→ OpenAPI validation
→ RBAC/policy/confirmation
→ executor genérico
→ RAG quando necessário
→ schema-driven presentation
→ síntese
→ metadata/observabilidade
→ send/stream
```

## Actions OpenAPI

```text
OpenAPI provider
→ import/index
→ Action Catalog
→ agent binding + allowed_action_ids
→ retrieval/planner/validator
→ policy/RBAC/confirmation
→ generic HTTP executor
→ schema-driven presentation
```

Nova API não exige intent, marker, selector, registry técnico paralelo, parameter strategy ou presenter por endpoint.

## Apresentação

```text
response schema + payload + metadata
→ ChatSchemaDrivenPresentationService
→ presentationDecision
→ renderPlan
→ MFE render-only
```

Perfis e extensões proprietárias são enriquecimento opcional. O fallback genérico deve funcionar para API externa desconhecida.

## Camadas

| Camada | Responsabilidade |
|--------|------------------|
| `domain` | modelos, regras e ports sem infrastructure/interfaces |
| `application` | orquestração de turno, retrieval, planner, RAG, policies e use cases |
| `infrastructure` | persistence, OpenAPI importer/index, LLM, HTTP/auth |
| `interfaces/http` | endpoints REST/SSE finos |
| `composition` | wiring/DI |
| `content/pt-BR` | linguagem/UX/config declarativa |

## Regras Cursor relacionadas

- `.cursor/rules/chat-intelligence-base.mdc`
- `.cursor/rules/clean-architecture-chat-api.mdc`
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
- `.cursor/rules/schema-first-presentation-delivered.mdc`
- `.cursor/rules/presentation-operational-decoupling.mdc`
- `.cursor/rules/ai-intelligence-evaluation.mdc`
- `.cursor/rules/ai-external-tools-security.mdc`
- `.cursor/rules/ai-context-and-tool-budget.mdc`

## Evals

Mudanças de inteligência usam baseline × candidate e R1–R11. Mudanças no motor de tools exigem API externa desconhecida + teste metamórfico.

## Política documental

Documento de arquitetura que descreva pipeline substituído deve ser removido do working tree depois que qualquer decisão ainda válida for absorvida pela fonte canônica. Histórico técnico permanece no Git, não em arquivos indexáveis pelo Cursor.
