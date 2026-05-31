# Mockup — Métricas

> Esqueleto — preencher na revisão da aba 6.

## Estado atual

- `AdminMetricsTab` — KPIs, custo LLM, séries.
- **Problema histórico:** `ChatIntelligenceSettingsPanel` misturava **config** com observabilidade.

## Wireframe (somente observabilidade)

```
┌─────────────────────────────────────────────────────────┐
│ Métricas                          [Janela ▼] [Atualizar] │
├─────────────────────────────────────────────────────────┤
│ Cards KPI │ Gráfico custo │ Distribuições │ Série hist.  │
└─────────────────────────────────────────────────────────┘
```

## Fora de escopo

- Toggles de inteligência → mockup 11 (Plataforma) ou Ferramentas, conforme decisão final.
