# Mockup — Segurança

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
