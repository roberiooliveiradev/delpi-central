# Roadmap — Minha DELPI AI

Este diretório contém **apenas planejamento ainda válido** e um arquivo histórico organizado.  
**Roadmap não é fonte canônica de arquitetura nem de critério de testes.**

Para implementar no estado atual:

| Responsabilidade | Fonte vigente |
|------------------|---------------|
| Arquitetura do chat | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) |
| OpenAPI-first (roteamento) | [`../architecture/openapi-first-universal-tool-routing.md`](../architecture/openapi-first-universal-tool-routing.md) |
| Nova API/action | [`../architecture/new-api-route-checklist.md`](../architecture/new-api-route-checklist.md) |
| Actions OpenAPI | [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md) |
| Evals da IA | [`../testing/chat-ai-flow-families.md`](../testing/chat-ai-flow-families.md) |
| Desenvolvimento | [`../development/guia-desenvolvimento.md`](../development/guia-desenvolvimento.md) |

## Estrutura

```text
roadmap/
  active/                 # planejamento ainda executável
  llm-json-decoupling/    # iniciativa aberta (evidence preservada)
  archive/                # playbooks/ondas/melhorias fechados — NÃO SoT
  README.md               # este arquivo
```

## Ativos

| Documento | Conteúdo |
|-----------|----------|
| [`llm-json-decoupling/README.md`](./llm-json-decoupling/README.md) | Remover catálogos técnicos / NLU hardcoded → OpenAPI + LLM |
| [`active/admin-fluxos-revisao.md`](./active/admin-fluxos-revisao.md) | Veredito fluxos admin |
| [`active/admin-fluxos-plano-implementacao-restante.md`](./active/admin-fluxos-plano-implementacao-restante.md) | Plano restante BC admin |
| [`active/BACKLOG_ROADMAP.md`](./active/BACKLOG_ROADMAP.md) | Backlog priorizado (desenho/OCR etc.) |
| [`active/melhorias-futuras.md`](./active/melhorias-futuras.md) | Itens explicitamente futuros |
| [`active/inteligencia-chat-onda-12-*.md`](./active/) …14 | Ondas desenho/OCR ainda parciais |

## Arquivo histórico

Playbooks numerados, ondas 1–11, pacote `melhorias/` concluído e audits datados vivem em [`archive/`](./archive/README.md).

Use `archive/` só para auditoria. Implementação segue `architecture/` + `.cursor/rules`.

## Política

```text
decisão ainda válida → absorver em architecture/api/testing
iniciativa aberta → active/ ou llm-json-decoupling/
fechado / contraditório → archive/ (evidência) ou Git history
```

Não indexar `archive/` como guia de implementação.
