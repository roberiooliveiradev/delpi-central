# Mockup — Segurança

> **Status (31/05/2026):** Ver [STATUS_ROADMAP_MELHORIAS.md](../../STATUS_ROADMAP_MELHORIAS.md) (mockups 01–10 implementados; 11 aguardando aprovação).


## Estado atual

- `AdminSecurityTab` — anti-injection, scan, eventos 24h, **RBAC** e link para Auditoria.
- `SecuritySummaryStrip` (bloqueios, sinalizados, scans, total).

## Wireframe

```
┌─────────────────────────────────────────────────────────┐
│ Segurança          [Ver auditoria] [Atualizar]           │
├─────────────────────────────────────────────────────────┤
│ KPI strip │ Scan │ Config │ Eventos │ RBAC               │
└─────────────────────────────────────────────────────────┘
```

## Implementado (incremental, 10 abas planas)

- MFE: toolbar, KPI strip, botões workspace, `onOpenAudit` → aba Auditoria.
- `AdminRbacPanel` embutido ao final da aba.

## Critérios de aceite

- [x] KPI strip visível no topo.
- [x] Ver auditoria troca para aba Auditoria.
- [x] Matriz RBAC na mesma aba.
