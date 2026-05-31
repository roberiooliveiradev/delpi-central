# Mockup — Métricas

> **Status (31/05/2026):** Ver [STATUS_ROADMAP_MELHORIAS.md](../../STATUS_ROADMAP_MELHORIAS.md) (mockups 01–10 implementados; 11 aguardando aprovação).


## Estado atual

- `AdminMetricsTab` — KPIs, custo LLM, séries e distribuições (somente observabilidade).
- `ChatIntelligenceSettingsPanel` movido para a aba **Ferramentas** (configuração global).
- Cabeçalho com seletor de janela e **Atualizar** (`mdc-chat-ws-outline-btn`).

## Wireframe (somente observabilidade)

```
┌─────────────────────────────────────────────────────────┐
│ Métricas                    [Janela ▼] [Atualizar]       │
├─────────────────────────────────────────────────────────┤
│ Cards KPI │ Gráfico custo │ Distribuições │ Série hist.  │
└─────────────────────────────────────────────────────────┘
```

## Fora de escopo

- Toggles de inteligência → aba **Ferramentas** (seção «Inteligência do chat») até mockup 11.

## Implementado (incremental, 10 abas planas)

- MFE: métricas sem painel de config; refresh no cabeçalho.
- Ferramentas: bloco `ChatIntelligenceSettingsPanel` com lead explicativo.

## Critérios de aceite

- [x] Aba Métricas não exibe toggles de inteligência global.
- [x] Atualizar recarrega resumo via `loadAdminData`.
- [ ] Gráficos interativos — fora do escopo desta fase.
