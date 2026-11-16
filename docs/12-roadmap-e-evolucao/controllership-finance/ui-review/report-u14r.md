# Report U14R — hotfix Panorama + rework (parcial)

Data: 2026-11-15/16. Âncora: `3a364728`+.

## H1 — CRÍTICO · Panorama em PROD — DONE

| Item | Valor |
|---|---|
| SHA | `a0556b0d35` |
| Tag | `rollback-ui-review-u14r-controllership-finance` |
| Verifier | ACCEPT_WITH_RESIDUAL (r1) |
| HML | rebuild MFE healthy |
| PROD | MFE `--no-cache` · início `2026-11-15T23:58:33Z` · fim `2026-11-15T23:59:26Z` |

**Causa:** F4 (`92d25b1385`) aplicou `min-height: 220px` via `[class*="semicircle"]` / `[class*="distribution-donut"]`, casando com `__legend-dot`, `__center`, `__value`, etc.

**Diff:** remove as regras attribute-selector; `size={200}` nos dois Cf*; `align-items: start` na row (Evolução sem vazio); testes estrutural + Playwright de geometria.

**Geometria HML depois (1440):**

```json
{
  "panoramaCardHeight": 305,
  "legendDotMaxHeight": 9,
  "centerOutsideChart": 0,
  "elementsOutsideCard": 0
}
```

Antes (PROD, Claude): 40+ nós com min-height 220px; coluna Panorama >890px.

### Veredito H1 (sem edição)

```text
veredito: ACCEPT_WITH_RESIDUAL
rodada: 1
```

## H2–H6 — PARADA · DECISION_REQUIRED

Código local preparado (não commitado / não publicado): prefs `columns:v2` + `field:false`; chave abreviada + Copiar; `CfBarSeriesChart`; KPI «Pendentes»; `formatDocumentTypes` canônico; e2e `u14r-table-width`.

### Verifier H2–H6 r1 (sem edição)

```text
veredito: REWORK
rodada: 1
```

- **OC-1:** AC visual sem medição HML anexada (bloqueia commit pela regra H6 do pedido).
- **DR-1 (DECISION_REQUIRED):** `BarSeriesChart` não expõe clique por ponto; o drill-down `day` do `ComparativeAreaChart` foi removido. Opções do verificador:
  - **(a)** aceitar residual (filtro `day` só via URL/chip);
  - **(b)** estender o kit (proibido sem dispensa);
  - **(c)** affordance alternativa de dia (aprovação PO).

**Owner:** escolher (a)/(b)/(c). Com (a), retomar: medir tabela em HML após commit → r2 do verificador → HML → PROD (`rollback-ui-review-u14r2-controllership-finance`) + axe.
