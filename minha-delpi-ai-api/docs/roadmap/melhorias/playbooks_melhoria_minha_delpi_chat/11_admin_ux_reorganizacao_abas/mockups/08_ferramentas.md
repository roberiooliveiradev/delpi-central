# Mockup — Ferramentas

> Esqueleto — preencher na revisão da aba 8.

## Estado atual

- `AdminToolsTab` — LLM, health, actions, logs por agente.
- `AdminRbacPanel` embutido na mesma aba (RBAC não é «ferramenta»).

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Ferramentas e integrações           [Atualizar]          │
├─────────────────────────────────────────────────────────┤
│ Provider LLM │ Health actions │ Catálogo rotas          │
├─────────────────────────────────────────────────────────┤
│ Logs de teste por agente (tabela)                        │
└─────────────────────────────────────────────────────────┘
```

## Decisão pendente

- RBAC vai para **Segurança** ou **Plataforma** — não duplicar na implementação final.
