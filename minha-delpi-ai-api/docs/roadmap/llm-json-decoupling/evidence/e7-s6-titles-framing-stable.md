# E7.S6 — Titles/framing estáveis (history/F5)

**Status:** `ATENDIDO` (2026-09-10)  
**Onda:** G (plano 07)  
**Harness:** `tests/unit/domain/services/test_e7_s6_titles_framing_stable.py`

## Veredito

```text
TITLE_WRITE_ONCE = PASS
PATH_RENAME_KEEPS_TITLE = PASS
SUMMARY_RESOLVE_ONCE = PASS
FRAMING_NOT_TITLE = PASS
POLICY_FALLBACK_OVER_REINFER = PASS
```

## Feito

1. **`_materialize_display_titles` write-once** — se `title`/`routeTitle` + `titleSource` ∈ `{SLOT_TITLE, PRESENTATION_TITLE, ACTION_DISPLAY_LABEL}`, rematerialize (F5) **não** reinfervia catálogo/path.
2. **`titleSource` persistido em `metadata`** (além do plan) para reload.
3. **Title normalization** — `fallbackTitle` da policy vence reinferência path/shape; source estável não sobrescreve título válido.
4. **`_infer_items_title(..., metadata=)`** — propaga cascata do resolver quando disponível.

## Cascata canônica

```text
slot / presentation.title / metadata.title
→ ActionDisplayLabel (summary)
→ routeTitles UX_COPY (fallback)
→ framing (routeFraming/sectionFraming) separado — não vira título
```

## Residuais

- `titlesByItemShape` / playbook `tableTitle` ainda existem como fallback de view (não owner de route title).
- Framing contextual via síntese de turno (R07-05) permanece fora deste cutover.
- MFE render-only profundo → **E7.S7**.

## Próximo

**E7.S7** — MFE render-only + cleanup — **ATENDIDO** (`e7-s7-mfe-render-only-cleanup.md`).
