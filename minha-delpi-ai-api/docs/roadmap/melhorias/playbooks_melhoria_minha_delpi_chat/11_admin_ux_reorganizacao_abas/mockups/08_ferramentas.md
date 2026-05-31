# Mockup — Ferramentas

## Estado atual

- `AdminToolsTab` — LLM, health, actions, logs por agente, inteligência global do pipeline.
- `ToolsSummaryStrip` no topo (LLM, saúde, actions globais/chat).
- **RBAC** movido para a aba **Segurança** (não duplicar aqui).

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Ferramentas e integrações           [Atualizar]          │
├─────────────────────────────────────────────────────────┤
│ KPI strip │ Health │ Catálogo actions │ Logs por agente │
├─────────────────────────────────────────────────────────┤
│ Inteligência do chat (config global)                     │
└─────────────────────────────────────────────────────────┘
```

## Implementado (incremental, 10 abas planas)

- MFE: `ToolsSummaryStrip`, toolbar workspace, remoção do card LLM duplicado.
- RBAC: `AdminRbacPanel` na aba Segurança.

## Critérios de aceite

- [x] KPI strip no topo sem rolar (desktop).
- [x] RBAC não aparece em Ferramentas.
- [ ] Reorganização em sub-abas — mockup 11.
