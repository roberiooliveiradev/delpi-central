# Mockup — Agentes

> **Status (31/05/2026):** Ver [STATUS_ROADMAP_MELHORIAS.md](../../STATUS_ROADMAP_MELHORIAS.md) (mockups 01–10 implementados; 11 aguardando aprovação).


## Estado atual

- `AdminAgentsTab` — especialização, presets, escopo RAG/tools, estatísticas de uso.
- Builder: `ChatAgentBuilderPage` em `/agentes/:id/configurar`.

## Jobs do administrador

1. Ver quantos agentes estão ativos e com especialização.
2. Filtrar catálogo e configurar RAG/tools por agente.
3. Abrir builder para identidade, prompt, skills e actions.
4. Salvar especialização admin sem sair da aba.

## Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Agentes especializados                                      │
│ KPI: Total │ Ativos │ Especializados │ Inativos             │
│                              [Atualizar] [Abrir builder]    │
├─────────────────────────────────────────────────────────────┤
│ Lista (filtrada) │ Painel especialização + stats de uso     │
└─────────────────────────────────────────────────────────────┘
```

## Fora de escopo

- Simulação sandbox → 05_simulacao.

## Critérios de aceite

- [x] KPI strip + filtro no catálogo (maio/2026).
- [x] Botão «Abrir builder» (habilitado com agente selecionado).
- [x] Lista vazia contextual por filtro.
- [ ] Deep link `/admin/agentes/:id` mantido via `initialAgentId`.

## Implementado (10 abas planas)

- `AgentsSummaryStrip` + `agentsSummary.ts`.
- Navegação para `buildChatAgentConfigHref`.
