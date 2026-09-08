# Roadmap — Minha DELPI AI

Este diretório contém somente planejamento que ainda é válido para evolução futura. **Roadmap não é fonte canônica de arquitetura nem de critério de testes.**

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
| [`admin-fluxos-revisao.md`](./admin-fluxos-revisao.md) | Veredito manter/melhorar/remover dos fluxos admin do chat (ondas 1–8). |
| [`admin-fluxos-plano-implementacao-restante.md`](./admin-fluxos-plano-implementacao-restante.md) | **Plano executável** do restante do BC admin (ondas 9+: presets, debug, HITL, Studio, kit). |
| [`openapi-first-universal-tool-routing.md`](./openapi-first-universal-tool-routing.md) | Arquitetura vigente e critérios de aceite do roteamento universal de Actions. |
| [`melhorias-futuras.md`](./melhorias-futuras.md) | Backlog de melhorias futuras explicitamente não implementadas. |
| [`melhorias/BACKLOG_ROADMAP.md`](./melhorias/BACKLOG_ROADMAP.md) | Backlog priorizado quando aplicável. |

## Política de limpeza documental

Documento técnico concluído, substituído ou contraditório **não permanece no repositório como guia histórico**.

```text
decisão antiga útil apenas para auditoria
→ histórico do Git

decisão ainda válida
→ incorporar na fonte canônica atual

documento substituído/contraditório
→ remover do working tree
```

Regras:

- não manter playbook concluído que ensine arquitetura diferente da vigente;
- não manter redirecionamento, aviso “legado”, “histórico” ou “use o novo” como substituto da remoção;
- não deixar links para documentos removidos;
- não duplicar a arquitetura vigente em vários roadmaps;
- decisões ainda válidas devem ser absorvidas pelas fontes canônicas antes da remoção do documento antigo;
- Git history é a fonte para investigação histórica, não o working tree indexável pelo Cursor.

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
