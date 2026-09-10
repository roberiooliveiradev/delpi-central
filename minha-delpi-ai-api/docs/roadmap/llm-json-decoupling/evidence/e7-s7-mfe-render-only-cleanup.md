# E7.S7 — MFE render-only e cleanup

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Harness:** `plugins/minha-delpi-chat/.../presentationRenderOnly.test.ts`

## Veredito

```text
MFE_RENDER_ONLY = PASS
DEAD_JSON_REMOVED = PASS
PROFILE_KEY_OVER_PATH = PASS
UNKNOWN_PATH_GENERIC = PASS
LEGACY_FALLBACK_GATE = PASS
```

## Feito

1. **DELETE** `plugins/minha-delpi-chat/src/content/product_operational_content.json` (espelho morto; zero imports runtime).
2. **DELETE** `scripts/sync-product-operational-content.mjs` + npm script.
3. **README** MFE: owner de títulos/framing = contrato API materializado.
4. **Testes** E7.S7: stubs genéricos + ausência do JSON + profileKey > path + unknown → `other`.

## Diferido (contrato incompleto / risco legado)

| Residual | Motivo |
|----------|--------|
| `routeKeyFromPath` | Fallback quando metadata sem `presentationProfileKey` |
| `PROFILE_KEY_TO_ROUTE` / `ROUTE_SHOW_IN` | Adapter de chrome; `showIn` ainda não materializado |
| `SECTION_UX_STATIC_TITLES` (Escopo/Ficha/…) | Copy UX local até `sectionTitles` sempre presente |

## Paridade send/stream/reload

Títulos estáveis garantidos no backend (E7.S6 write-once). MFE só lê `routeTitle` / `stackPresentationPlan` — sem reinferir semântica.

## Próximo

Plano **08** (skills residual) ou Onda H cleanup, conforme ledger.
