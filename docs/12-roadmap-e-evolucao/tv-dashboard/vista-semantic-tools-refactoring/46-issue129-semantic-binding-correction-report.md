# 46 — VISTA/TV — ISSUE #129 SEMANTIC BINDING CORRECTION REPORT

**Data:** 2026-11-02 · **Commit:** `ae7f6f2fde` · **Deploy:** `srv-api`
imagem `sha256:b586a06d82e8`

## Root cause — `PROVEN`

Cobertura lexical prevalecia sobre o papel semântico:
`si_oee_meta` (TARGET, goals={oee,meta,eficiência}) vencia o
ranking do KPI de realizado por cobrir mais goals. Papel era
sinal de ranking, não restrição de elegibilidade.

## Correção — `EXTEND` (`_enrich_composition_ops`)

**Papel = elegibilidade, não ranking:**

| Bloco | Papéis elegíveis | Fonte resolvida |
|---|---|---|
| `kpi_view` | realized | `get_si_indicator_production_oee_realized` |
| `chart_view` | series, realized | `get_production_oee_series` (periodDays=30) |
| meta (componente próprio) | target | `get_si_indicator_production_oee_meta` |

Meta pedida → emite `v_meta_view` (KPI dedicado) + ds + bind;
nunca dentro do KPI de realizado. Empate de papel = ambiguidade
honesta (`NEEDS_SOURCE_SELECTION`).

## Evidência — pedido único OEE

`proposal` + tema + "Painel de OEE" + ops tipadas:
`oee_realized`→KPI, `oee_series`→chart(30d), `oee_meta`→meta —
três papéis semanticamente separados.

## Testes

**2455/2455 PASS** — 97/97 DI; 5S/slide-vazio/gibberish
preservados.

## Resíduos

- Commit LAB exige credencial fresh-RBAC + consent humano —
  `AUTHORIZATION_GATE` provado in-process.
- Screenshot: `TEST_NOT_RUN` (capture gap conhecido).
- `bindingPlan=NEEDS_SOURCE_SELECTION` residual para blocos não
  essenciais; papéis essenciais resolvidos.

## Veredito

**`DI_F2_SEMANTIC = PASS`** — realizado/meta/tendência separados
por elegibilidade de papel, não por cobertura lexical; sem falso
RESOLVED para papel incompatível.
