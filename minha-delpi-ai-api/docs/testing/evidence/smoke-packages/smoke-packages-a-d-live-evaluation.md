# Avaliação live — pacotes A–D

Data: 2026-08-31 · agente `4f9c225b-…` · script `scripts/eval_packages_a_d_live.py`  
Artefato bruto: `smoke-packages-a-d-live-evaluation.json`

## Tabela (critérios do plano)

| # | Critério | Pacote | Veredito | Evidência |
|---|----------|--------|----------|-----------|
| 1 | Typo identity → direct rápido, sem notice dados | B | **FAIL** (conteúdo ok, latência) | «como u posso te chamar?» → «Minha DELPI», 0 tools, sem «dados consultados», mas **52,4 s** (não foi shortcut rápido; stage/skipRag nulos no envelope) |
| 2 | Comum operacional → guidance agente | A | **PASS** | «qual o rol filial 01» → guidance agente em **237 ms**, sem `/financial/rol` |
| 2b | Resume período com pending | A | **PARCIAL** | Após «qual o rol» + «agosto de 2026» → clarificação genérica de tema (não guidance de agente / pending operacional) |
| 3 | Agente ROL filial 01 → só 01; título/prosa | A | **PASS** | path `/financial/rol`, `branch=01`; prosa ROL R$ 711.977,25; sem título de estoque; sem by-branch |
| 4 | Prompt contexto; dataAnswer; síntese | C | **FAIL** | Tools rodaram; prosa KPI presente; **sem `dataAnswer`/`dataCommentary`** no metadata; consolidado veio R$ 0,00 |
| 5 | previous_period dual | D | **PASS*** | Dual fetch (`baseline`+`prior`); prosa de variação. *Label do prior ainda diz «ano anterior» em vez de «período anterior» |
| 5b | filial×filial dual + chips | D | **FAIL** | Após ROL agosto: «comparar filial 01 com filial 02» → pediu esclarecimento («o que é ROL?»), **sem dual branches** |
| 6 | YoY sem regressão | herança | **PASS** | Dual tools; prosa 2026 vs 2025 com variação |

## Resumo

- **PASS sólido:** guidance no comum (A), ROL scalar filial 01 (A), previous_period dual (D), YoY (herança).
- **Falhas a corrigir:** (B) identity ainda lento (~52 s); (C) `dataAnswer` ausente no envelope live; (D) comparação filial×filial não reexecuta no follow-up live.
- **Qualidade fina:** resume de período no comum ainda vira clarify genérico; label prior do previous_period herda texto de YoY.

## Trechos de prosa

1. Identity: *Você pode me chamar de **Minha DELPI**…*
2. Comum: *Dados operacionais exigem um agente…*
3. ROL 01: *ROL: R$ 711.977,25 / Receita bruta: R$ 872.589,10*
5. Período anterior: comparação ago/2026 vs jul/2026 com variação (label prior incorreto)
5b. Filiais: *Ainda não tenho dados suficientes… O que é "ROL"?*
6. YoY: comparação ago/2026 vs ago/2025 com variação
