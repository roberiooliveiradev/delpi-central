# Mockup — Avaliações

> **Status (31/05/2026):** Ver [STATUS_ROADMAP_MELHORIAS.md](../../STATUS_ROADMAP_MELHORIAS.md) (mockups 01–10 implementados; 11 aguardando aprovação).


## Estado atual

- `AdminEvaluationsTab` — notas 1–5, sugestões LLM, candidatos.
- `EvaluationsSummaryStrip` no topo (total, média, úteis, 24h).
- Toolbar com **Atualizar**; lista de candidatos no padrão de linhas do workspace.

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Avaliações de respostas             [Atualizar]          │
├─────────────────────────────────────────────────────────┤
│ KPI strip │ Lista feedback │ Detalhe + sugestões LLM    │
└─────────────────────────────────────────────────────────┘
```

## Implementado (incremental, 10 abas planas)

- MFE: `EvaluationsSummaryStrip`, `evaluationsSummary.ts`, botões workspace.
- Smoke: `GET /admin/responses/evaluations/summary` em `smoke_admin_endpoints.py`.

## Critérios de aceite

- [x] KPI strip visível sem rolar (desktop).
- [x] Atualizar recarrega resumo e candidatos.
- [ ] Filtros por agente/sessão — futuro.
