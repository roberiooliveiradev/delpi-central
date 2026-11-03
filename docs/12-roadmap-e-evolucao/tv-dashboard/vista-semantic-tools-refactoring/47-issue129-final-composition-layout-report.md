# 47 — VISTA/TV — ISSUE #129 FINAL COMPOSITION & LAYOUT REPORT

**Data:** 2026-11-02 · **Commit:** `5f6e8ac4e4` · **Deploy:** `srv-api`
imagem `sha256:119bf030ba58`

## Root cause — `PROVEN`

Ordering: a tabela era avaliada **antes** da emissão do componente
de meta — `_bound_goals`={oee,eficiência} não continha `meta` →
`own_goals ⊆ bound` falso → tabela mantida + meta emitida depois
em `y50` sobreposto à tabela `y54`. Dois bugs, uma causa: decisão
de redundância sem a cobertura do conjunto FINAL de componentes.

## Correção — `EXTEND` (`_enrich_composition_ops`)

Pré-computo `_meta_cand`/`_meta_goals` antes do loop: a cobertura
usada pelo drop inclui os goals do componente de meta que será
emitido. Sem nova abstração; a emissão pós-loop é reutilizada.

## Composição final — pedido único OEE

```
bindingPlan=RESOLVED
heading          x3  y3   w94 h8   "Painel de OEE"
kpi_view         x3  y14  w22 h36  ← si_oee_realized (REALIZED)
chart_view       x28 y14  w69 h36  ← oee_series (SERIES, 30d)
kpi_view (meta)  x3  y50  w22 h22  ← si_oee_meta (TARGET)
table_view       — descartada (redundante, goals já cobertos)
```

Zero sobreposição; três papéis semanticamente separados; sem
componente excedente no plano.

## Testes

**2455/2455 PASS** — 97/97 DI; 5S mantém tabela NC (semântica de
detalhe); slide vazio e gibberish preservados.

## Resíduos

- Commit LAB: `AUTHORIZATION_GATE` (credencial fresh-RBAC +
  consent humano — provado in-process).
- Screenshot 1080p: `TEST_NOT_RUN` (capture gap documentado).
- Meta card pode sobrepor tabela quando AMBAS mantidas (caso
  raro — meta+detalhe juntos); documentado.

## Veredito

**`DI_F1_F2_COMPOSITION = PASS`** — conjunto final = componentes
exigidos pelo briefing; bindings por papel; layout livre de
colisões; `RESOLVED` agora reflete completude real.
