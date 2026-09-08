# Minha DELPI AI API — documentação técnica

**Status:** vigente  
**Base URL:** `/apps/minha-delpi-ai/api`

Este índice aponta somente para fontes atuais de arquitetura, API, desenvolvimento e avaliação. Documentos de roadmap/changelog não devem ser usados como regra de implementação.

## Comece por aqui

| Ordem | Documento | Uso |
|------:|-----------|-----|
| 1 | [`architecture/chat-intelligence-base.md`](./architecture/chat-intelligence-base.md) | Arquitetura vigente do chat base |
| 2 | [`api/04-actions-openapi.md`](./api/04-actions-openapi.md) | Providers e Actions OpenAPI |
| 3 | [`architecture/new-api-route-checklist.md`](./architecture/new-api-route-checklist.md) | Nova API/action exposta ao chat |
| 4 | [`testing/chat-ai-flow-families.md`](./testing/chat-ai-flow-families.md) | **Protocolo canônico de avaliação R1–R11** |
| 5 | [`development/guia-desenvolvimento.md`](./development/guia-desenvolvimento.md) | Onde implementar e Definition of Done |
| 6 | [`flows/README.md`](./flows/README.md) | Fluxos HTTP → inteligência → tools/RAG → apresentação |
| 7 | [`api/README.md`](./api/README.md) | Referência HTTP por domínio |

## Fontes canônicas

```text
instruções oficiais do projeto
→ .cursor/rules/development-standards-index.mdc
→ regra especializada aplicável
→ architecture/api docs vigentes
→ testing/chat-ai-flow-families.md
→ código/contrato atual
```

### Inteligência e Actions

```text
mensagem
→ decomposição/contexto
→ allowed capabilities/actions
→ Action Catalog OpenAPI
→ retrieval top-K
→ planner estruturado
→ validação OpenAPI
→ RBAC/policy/confirmation
→ executor genérico
→ RAG quando aplicável
→ schema-driven presentation
→ resposta
```

### Avaliação

Mudanças de inteligência seguem:

```text
BASELINE imutável
→ bug + sibling + negative
→ implementação canônica
→ CANDIDATE no mesmo corpus/config
→ R1–R11
→ trials quando necessário
→ live/surface validation
→ decisão
```

R1–R11 cobrem routing, trajectory, arguments, content, presentation, grounding, parity, latency, outcome, safety e efficiency.

Live composto/UI exige ainda as camadas **L1–L4** (R-tools / R-facts / R-ui / R-ask) — ver `testing/chat-ai-flow-families.md` §16.1 e `testing/smoke-complex-consolidated-turns.md`. Harness estrutural verde ≠ PASS de release.

## Regra para documentação datada

Arquivos em `roadmap/`, `changelog/` e evidências anteriores podem existir para registro de evolução, mas **não são fonte de instrução atual**. Se um documento datado contradizer uma fonte canônica vigente, ele deve ser corrigido/removido; o Cursor não deve reconciliar as duas arquiteturas.

## Regras Cursor principais

- `.cursor/rules/development-standards-index.mdc`
- `.cursor/rules/chat-intelligence-base.mdc`
- `.cursor/rules/openapi-first-universal-tool-routing.mdc`
- `.cursor/rules/ai-intelligence-evaluation.mdc`
- `.cursor/rules/ai-external-tools-security.mdc`
- `.cursor/rules/ai-context-and-tool-budget.mdc`
- `.cursor/rules/architecture-ci-enforcement.mdc`

## Regra de ouro

Uma API OpenAPI externa desconhecida deve funcionar após import/index + agent binding sem código/configuração técnica por endpoint no core do chat.

Uma melhoria de IA só está concluída quando o protocolo R1–R11 comprova o objetivo real — não porque um smoke isolado ou um único prompt passou.
