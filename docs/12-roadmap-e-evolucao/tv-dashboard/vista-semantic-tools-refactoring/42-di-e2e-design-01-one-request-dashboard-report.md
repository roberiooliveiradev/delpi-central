# 42 — VISTA/TV DI-E2E-DESIGN-01 ONE REQUEST COMPLETE DASHBOARD REPORT

**Data:** 2026-11-02 · **Commit:** `972b22d091` · **Deploy:** `srv-api`
imagem `sha256:dc5096f484de`

## Root causes — `ROOT_CAUSE_PROVEN`

- **RC-A:** heading da recipe não recebia `content`/`contentRuns`
  do briefing → título genérico/ausente.
- **RC-B:** `table_view` entrava em toda composição — scaffold da
  recipe era tratado como prescrição de componentes.
- **RC-D:** ops de recipe criavam visuais sem `data_source` e sem
  `bind_visual` — o contrato canônico (`data_source` block +
  `dataBinding` + `bind_visual{visualId,dataSourceId}`) nunca era
  ligado pela proposta.
- **RC-extra:** tokens de métrica curtos (`oee`, `5s`) nunca viravam
  objetivos (<4 chars); ruído (`vista`,`lab`,`com`) vazava como goal.

## Correção — `EXTEND` (owner: `suggest_change`)

- `_enrich_composition_ops`: título do briefing no heading;
  `upsert_data_source`+`bind_visual` canônicos por bloco quando o
  plano está RESOLVED ou tem **um único** candidato justificado;
  `table_view` sai sem pedido e sem candidatos justificados; params
  de período (`N dias`, granularidade) só se o `paramSchema`
  declarar a chave.
- `_metric_tok`: tokens de 3 chars viram objetivos apenas quando
  segmento inteiro de `operationId` elegível (`oee` ✓, `com` ✗).
- Estado do `bindingPlan` reflete a resolução dos ops; blocos de
  componentes descartados não travam o agregado.

## Evidência — pedido único OEE

```
proposal | recipe THEME_DELPI(+composição) | goals:
  oee COVERED, eficiencia COVERED, meta COVERED
ops: patch_native_config(tema) → upsert_block(heading
  "Painel de Eficiencia") → kpi_view → upsert_data_source
  (si_indicator_production_oee_meta) → bind_visual →
  chart_view → ds(eficiencia_fabril_efficiency_series) → bind
bindingPlan: NEEDS_SOURCE_SELECTION (meta vs realizado =
  ambiguidade legítima preservada)
```

## Antes/depois

| | Antes | Depois |
|---|---|---|
| Título | ausente/genérico | briefing ou objetivo |
| KPI/gráfico | sem dados | ds+bind canônicos quando inequívoco |
| Tabela | sempre incluída | só pedida ou justificada |
| `oee`/`5s` | nunca goal | goal com evidência em oid |
| Pedido OEE | `ready`+patch só | proposal+composição+metas cobertas |

## Testes

**2455/2455 PASS** — 97/97 DI; ambiguidade e 5S preservados.

## Resíduos

- Commit LAB exige PREPARE→CONFIRM autorizado — não executado
  (governança, não código). `VISUAL_VERIFICATION=TEST_NOT_RUN`.
- Meta vs realizado OEE = ambiguidade real → `NEEDS_SOURCE_SELECTION`
  honesto, não pick silencioso.

## Veredito

**`DI_E2E_DESIGN_01 = D — AUTHORIZATION_OR_ENVIRONMENT_GATE`** —
um pedido produz proposta completa (design+fontes+bindings
tipados) em uma interação; a materialização final depende apenas
do confirm governado, não de novo código.
