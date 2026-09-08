# Roadmap — Minha DELPI AI

Este diretório registra evolução e planejamento. **Roadmap não é fonte canônica de arquitetura nem de critério de testes.**

Para implementar no estado atual, consultar primeiro:

| Responsabilidade | Fonte vigente |
|------------------|---------------|
| Arquitetura do chat | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |
| Nova API/action | [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md) |
| Actions OpenAPI | [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md) |
| Evals da IA | [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md) |
| Desenvolvimento | [`../development/guia-desenvolvimento.md`](../development/guia-desenvolvimento.md) |
| Regras Cursor | `.cursor/rules/development-standards-index.mdc` |

## Roadmaps ativos

| Documento | Conteúdo |
|-----------|----------|
| [`openapi-first-universal-tool-routing.md`](./openapi-first-universal-tool-routing.md) | Arquitetura vigente e critérios de aceite do roteamento universal de Actions. |
| [`melhorias-futuras.md`](./melhorias-futuras.md) | Backlog de melhorias futuras explicitamente não implementadas. |
| [`melhorias/BACKLOG_ROADMAP.md`](./melhorias/BACKLOG_ROADMAP.md) | Backlog priorizado quando aplicável. |

## Regra para documentos concluídos/datados

Arquivos de ondas, playbooks concluídos e changelogs podem permanecer como registro de decisões/entregas, mas:

- não devem ser usados pelo Cursor como instrução atual;
- não prevalecem sobre arquitetura/docs/regras vigentes;
- não devem ser copiados para novas implementações sem validação no código atual;
- se contradisserem fonte vigente, a fonte antiga deve ser corrigida/removida, não conciliada silenciosamente.

## Antes de iniciar uma implementação

```text
instruções oficiais
→ development-standards-index.mdc
→ regra especializada
→ arquitetura/API vigentes
→ protocolo de eval R1–R11
→ código/contrato atual
```

Para mudanças de inteligência, o fluxo obrigatório é baseline → implementação → candidate → R1–R11 → live/surface validation.
