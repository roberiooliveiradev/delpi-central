# Mockup — Auditoria

> **Status (31/05/2026):** Ver [STATUS_ROADMAP_MELHORIAS.md](../../STATUS_ROADMAP_MELHORIAS.md) (mockups 01–10 implementados; 11 aguardando aprovação).


## Estado atual

- `AdminAuditTab` — filtros, timeline, tabela, export JSON/CSV, detalhe por trace/promptHash.
- `AuditSummaryStrip` no topo (total filtrado, página, ações/usuários distintos, dias na timeline).
- Botões no padrão workspace (Aplicar filtros, exportar, Atualizar).

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Auditoria                           [Atualizar]          │
├─────────────────────────────────────────────────────────┤
│ KPI strip │ Filtros │ Timeline │ Tabela │ Detalhe      │
└─────────────────────────────────────────────────────────┘
```

## Implementado (incremental, 10 abas planas)

- MFE: `AuditSummaryStrip`, toolbar unificada.
- Smoke: `GET /admin/audit-logs` em `smoke_admin_endpoints.py`.

## Critérios de aceite

- [x] KPI strip com total do filtro (paginação).
- [x] Exportar JSON/CSV nos filtros (com RBAC).
- [ ] Drawer lateral para detalhe — futuro mockup 11.
