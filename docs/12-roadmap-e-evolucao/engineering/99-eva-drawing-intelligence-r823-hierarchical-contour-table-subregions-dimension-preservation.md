# 99 — EVA Drawing Intelligence R8.2.3: Hierarchical Contour Selection, Table Subregions & Dimension Preservation

**Status:** CORRIGIDO + DEPLOYED (runtime verificado) — defeitos semânticos remanescentes resolvidos nos dois desenhos de regressão; E2E MCP autenticado `TEST_NOT_RUN` (sem sessão OAuth). **SHA:** `b01eaa8b21`. **Data:** 2026-11-02. Refs: docs 93–98.

## 1. Correções (causa raiz)

| Defeito R8.2.2 | Correção R8.2.3 |
|---|---|
| `18702881`/`CLIENTE`/`003086`/`RESUMO` nas células | `_has_admin_word` (prefixo contextual) + colunas conectadas à coluna de códigos (gap >15% rompe a faixa) — campos administrativos fora das células |
| `90264161` fronteira = página quase inteira | `unreliable_boundary` — união >60% da página rejeitada; tokens não reivindicados |
| `COMPARED_PARTIAL` sem estrutura | fronteira rejeitada → `NOT_COMPARABLE` fail-closed |
| `15550±50`/`10000±50` sumiram | região ampla rejeitada → cotas restauradas como candidatos |

## 2. Evidência real — regressão

**`90264302` (92 toks):** `title_block` + `component_table [41,31,2295,262]` (gb=True), 4 rows, admin cells **[]** — `18702881`/`CLIENTE`/`003086`/`RESUMO` removidos; `rev:`→`00`; dims `643±2`/`663±2`; BOM `COMPARED_PARTIAL` matched `[50226113,50226114]` + `uncl[10080106,10020033]` — sem falsa ausência.

**`90264161` (126 toks):** `title_block` + `unreliable_boundary=True` — fronteira `[25,7,2282,1638]` (~página) **rejeitada**; admin=[]; BOM `NOT_COMPARABLE` fail-closed; **dims restauradas** `15550±50`,`10000±50`,`10±1`,`6±1`,`100±10`,`240±10`; produto pai fora (nib=[]).

## 3. Residuais honestos

- `revh.candidate=false` — histórico não forma cluster ≥2 próprio (honesto).
- `90264161`: cotas restauradas como candidatos textuais, associação geométrica não verificada (limitação do escopo).
- Multipage coverage por página — PENDING.
- OpenCV line-detection continua sendo a evidência gráfica; hierarquia de contornos RETR_TREE = próxima etapa bounded.
- E2E autenticado `TEST_NOT_RUN`; GT owner Engenharia pendente.
