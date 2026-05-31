# Mockup — Habilidades (Skills)

## Estado atual

- `AdminSkillsTab` — catálogo global, policy Markdown, editor lateral.

## Jobs do administrador

1. Ver quantas habilidades estão ativas vs inativas.
2. Criar ou editar policy de uma habilidade.
3. Desativar habilidade sem apagar histórico.
4. Filtrar catálogo por status antes de editar.

## Wireframe

```
┌─────────────────────────────────────────────────────────────┐
│ Habilidades                                                 │
│ KPI: Total │ Ativas │ Inativas          [Atualizar] [Nova]  │
├─────────────────────────────────────────────────────────────┤
│ Catálogo (filtrado) │ Editor policy + preview execução      │
└─────────────────────────────────────────────────────────────┘
```

## Notas

- Rótulo na UI: **Habilidades** (slug/rota interna: `skills`).
- Execução de APIs permanece em **Actions** / builder do agente.

## Critérios de aceite

- [x] KPI strip + filtro por status (maio/2026).
- [x] Título «Habilidades» (não «Skills do chat»).
- [x] Botões Atualizar e Nova habilidade no topo.
- [x] Mensagem de lista vazia contextual por filtro.

## Implementado (10 abas planas)

- `SkillsSummaryStrip` + `skillsSummary.ts`.
