# Mockup — Simulação

## Estado atual

- `AdminSimulateTab` — sandbox, preview de prompt, RAG, tools e comparação de contexto.
- KPI strip (`SimulateSummaryStrip`): agentes, sessões, estado do resultado.
- Toolbar com **Limpar** (`mdc-chat-ws-outline-btn`) e CTA **Simular** no padrão workspace.

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Simulação                         [Nova sessão]        │
├─────────────────────────────────────────────────────────┤
│ Config agente/sessão │ Chat sandbox │ Fontes/tool trace │
└─────────────────────────────────────────────────────────┘
```

## Nota de agrupamento (futuro)

- Candidata a sub-aba de **Agentes** na navegação final (mockup 11).

## Implementado (incremental, 10 abas planas)

- MFE: `SimulateSummaryStrip`, toolbar unificada, botões workspace.
- Smoke: `scripts/smoke_admin_endpoints.py` (login + simulate + listagens admin).

## Critérios de aceite

- [x] KPI strip visível no topo da aba (desktop).
- [x] Limpar reseta pergunta e painéis de resultado.
- [ ] Layout 3 colunas (config | sandbox | trace) — futuro mockup 11.
