# 32 — VISTA/TV DI-3.2 AUTONOMOUS COMPOSITION RECOVERY REPORT

**Data:** 2026-10-31 · **Commit:** `c9d86365b9` · **Deploy:** `srv-api`
imagem `sha256:a024d1e09f97`

## Root cause — `ROOT_CAUSE_PROVEN`

Duas lacunas reais em `PresentationRecipeService.resolve_from_nl`
(owner canônico da resolução recipe):

1. **IDs explícitos não resolviam** — só `markers` eram comparados;
   `TV_KPI_PLUS_CHART` literal na mensagem → `None` (teste C ChatGPT).
2. **Markers eram exclusivamente layout-phrasing** — sinais de negócio
   ("produtividade", "vendas e metas", "situação geral", "desvios de
   qualidade") sem match → `unsupported`+`compositionHints` sem
   materialização (teste B ChatGPT).

## Correção — `REUSE_DECISION = EXTEND`

- `resolve_from_nl`: IDs de recipe normalizados (`_`/espaço/`-`
  equivalentes) resolvem com score > marcador — contrato canônico,
  sem alias inventado.
- `presentation_recipes.json`: markers de recipes de composição
  recebem sinais de negócio declarados — a própria recipe declara a
  cobertura semântica que seus `ops` atendem (registry canônico, sem
  segundo intérprete).

## Benchmark A–E — `SERVICE_TESTED` E2E

| Cenário | Recipe | Status | Ops |
|---|---|---|---|
| A Produção | `TV_KPI_SERIES_TABLE` | `ready` | 5 |
| B Estoque | `TV_TABLE_FOCUS` | `ready` | 3 |
| C Comercial | `TV_KPI_PLUS_CHART` | `ready` | 4 |
| D Qualidade | `TV_KPI_SERIES_TABLE` | `ready` | 5 |
| E Executiva | `TV_KPI_SERIES_TABLE` | `ready` | 5 |
| C recipe explícita | `TV_KPI_PLUS_CHART` | `ready` | 4 |
| genérico sem sinal | — | `unsupported`+hints | 0 |

## Testes

**2404→2409+11 focos** — `test_design_intelligence_di32.py` 11 casos;
B1/B2/B3 stale assertions `VALIDATION_ERROR`→`ARGUMENT_VALIDATION`
(drift upstream `3bf75b7e94`, mesmo fix documentado no doc 31).

## CHATGPT MCP REVALIDATION CONTRACT

```json
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```

Esperado: `status="ready"`, `ops` tipadas reais (sem persistência —
suggest é read-only). Recipe explícita: `"crie um painel com recipe
TV_KPI_PLUS_CHART"`. Falha legítima: sem sinal → `unsupported` +
`compositionHints`.

## Veredito

**`DI32_ACCEPTANCE = PASS`** — revalidação ChatGPT pendente do lado
do operador (canal externo, mesma condição de DI-3.1); service path
E2E provado, sem engines/verbs novos.
