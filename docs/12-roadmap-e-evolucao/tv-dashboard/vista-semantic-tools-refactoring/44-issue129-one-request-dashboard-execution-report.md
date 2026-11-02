# 44 — VISTA/TV EXECUTION REPORT — Issue #129 (F0–F5)

**Data:** 2026-11-02 · **Commit:** `555fb44173` · **Deploy:** `srv-api`
imagem `sha256:a847998a16f7` · **Issue:** #129 (F0–F5)

## F0 — Diagnóstico causal — `PROVEN`

Cadeia `message→intent→goals→recipe→ops→bindingPlan→enrich→ops`:

- `FIX_LAYOUT`("organiz") precedia COMPOSE_SLIDE → falso `ready`+patch.
- Palavras de instrução/qualificadores viravam goals (sem papéis).
- Heading sem `content`/`contentRuns` do briefing.
- Ops de recipe sem `data_source`/`bind_visual` (contrato existia,
  nunca ligado).
- Binding por presença de goal, não por PAPEL (meta vs realizado
  tratados como equivalentes de KPI).
- Ferramentas visuais: zero Playwright/screenshot no HEAD —
  `VISUAL_CAPTURE_GAP` (DI-VISUAL-01 mantido).

## F1 — Contrato funcional — `PASS`

Três dimensões preservadas (business/design/execution):
título do briefing (ou primeiro objetivo por posição), componentes
por briefing (tabela só pedida ou justificada), gibberish
`unsupported`, slide-vazio preservado, goals semânticos
(`oee`/`eficiência`/`meta`).

## F2 — Binding por papel — `PASS` (parcial honesto)

Seleção = menor contaminação de goals (`goals ⊆ pedido`, menos
extraneous), desempate por score. Empate de papel = ambiguidade
contratual real → `NEEDS_SOURCE_SELECTION` (ex.: OEE realizado
api-delpi vs si_indicator — decisão de owner de métrica, não
heurística).

## F3 — Execução governada — `AUTHORIZATION_GATE` `PROVEN`

`suggest_change` → proposta completa in-process;
`semantic_execute(phase=prepare)` → `GptActionsError: Credencial
do usuário indisponível para autorização fresh` — fresh-RBAC +
consent são o gate real; sem credencial nesta execução, commit LAB
não executado. Não foi gap de código: o boundary recusou
corretamente.

## F4 — Qualidade visual — `TEST_NOT_RUN`

Nenhum mecanismo de captura no produto (F0). `VISUAL_VERIFICATION`
não declarado.

## F5 — Regressão/deploy

**2455/2455 PASS** · imagem `a847998a16f7` · 6 `vista_*` ·
rollback: `git revert 555fb44173`.

## Reproduções (HEAD)

| Pedido | Resultado |
|---|---|
| OEE completo (A) | `proposal`+composição+goals{oee,eficiência,meta}+"Painel de OEE"; ds/bind quando papel inequívoco |
| desenvolva (B) | `proposal`+ds/bind kpi+goals limpos |
| título explícito (C) | `ready`+ops+"Painel de Eficiência Industrial" |
| slide vazio (D) | `ready`+`add_blank_slide` |
| gibberish | `unsupported` |

## Veredito

**`ACCEPT_WITH_RESIDUAL` — decisão D: `AUTHORIZATION_OR_ENVIRONMENT_GATE`**
Uma solicitação gera proposta completa com design, goals, fontes
e bindings tipados por papel; o commit LAB depende apenas de
credencial fresh-RBAC + confirmação humana — gate provado
in-process, sem bloqueador de código. `VISUAL_VERIFICATION`
pendente de capability de captura (gap conhecido, não ocultado).
