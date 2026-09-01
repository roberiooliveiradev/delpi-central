# ADR-001 — Layout do modo operador (tablet)

**Status:** aceito (set/2026)  
**Contexto:** operador usa tablet no chão de fábrica; precisamos decidir chrome do Portal.

---

## Decisão

**MVP:** modo operador **dentro do shell do Portal** (sidebar visível), rota dedicada `/operator` com `dashboard-page--operator` — BrandBar domínio + conteúdo centralizado.

**P1 (quiosque):** query `?kiosk=1` ou manifest flag `operatorFullscreen: true` oculta sidebar via contrato Portal (se disponível) ou CSS host `.dashboard-page--operator-kiosk` documentado no MFE.

---

## Motivos

| Opção | Pró | Contra |
|-------|-----|--------|
| Com sidebar (MVP) | Zero dependência Portal; ship rápido | Menos área útil no tablet |
| Quiosque fullscreen (P1) | Máximo touch target | Exige hook Portal / rota isolada |

---

## Consequências

- Wireframes WF-PP-OP mostram sidebar **opcional** (tracejada).
- BrandBar `.pp-operator-brandbar` sempre presente — identidade em quiosque e normal.
- Link «Painel administrativo» só se `devices.view`.

---

## Referências

- [DESIGN-FRONTEND.md §9](./DESIGN-FRONTEND.md)
- [WIREFRAMES.md WF-PP-OP-HUB](./WIREFRAMES.md)
