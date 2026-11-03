# 41 — VISTA/TV DI-3.7.1 BUSINESS GOAL PRESERVATION REPORT

**Data:** 2026-11-02 · **Commit:** `981cb9bcc5` · **Deploy:** `srv-api`
imagem `sha256:788c2a816d34`

## Root causes — `ROOT_CAUSE_PROVEN`

- **RC-A:** "produtividade" single-token retornava 0 sugestões e
  o pairing único (`produtividade auditorias`) resolvia audit, não
  produção → `ignoredGoals=["produtividade"]`.
- **RC-B:** `fábrica` (contexto) era promovida a objetivo `COVERED`.
- **RC-C:** séries de produção fora dos opIds do objetivo →
  `servesGoals=[]` no chart com fontes válidas.
- **RC-D:** `metas` aceitava Kaizen/system por categoria compartilhada.

## Correção — `EXTEND` (owner: `suggest_change` goal pipeline)

- Pairing: single-token → **union de TODOS os parceiros** em
  `_all_tok` (contexto incluído como parceiro de busca).
- Contexto ≠ objetivo: `fabrica/filial/unidade/setor/planta/
  empresa/período/televisão` → stop set; não viram goals.
- `_goals_of`: opIds OU token-no-oid OU categoria de **dono único
  com afinidade etimológica** (`produtividade~production` ✓;
  `auditorias~quality` ✗ → Kaizen não cobre auditorias).
- `_goal_ok`: opIds de cada objetivo filtrados por own-cats +
  âncoras + bare-score ≥0.5×top — metas não cobrem Kaizen.
- Goal floor: cada objetivo reconhecido mantém ≥1 representante.

## Evidência

| Cenário | Antes | Depois |
|---|---|---|
| Produtividade isolada | `ignoredGoals=["produtividade"]`, chart `servesGoals=[]` | `produtividade`+`problemas` COVERED, chart serve produtividade |
| Prod+5S | produtividade ignorada | ambos COVERED, kaizen fora |
| Vendas+metas | metas coberta por kaizen | metas+vendas COVERED (comercial) |
| 3-intent | produtividade ignorada | 3 objetivos COVERED |

## Testes

**2455/2455 PASS** — 97/97 DI; association por categoria exige
prefixo etimológico.

## Resíduos

- `kaizen_savings` persiste como candidato não-goal no chart
  multi-intent quando `justified` não cobre o bloco — fronteira
  documentada, não falso positivo de goal.
- Binding de campo exige `data_block_preview`/DataModel — pendente
  contratual, não ocultado.

## CHATGPT MCP REVALIDATION CONTRACT

```
analyze(analysis="intent_materialization",
  subject_refs={"playlistId":"<id>","slideId":"<id>"},
  parameters={"message":"crie um painel para acompanhar
    produtividade e problemas da fábrica","dry_run":true})
```
→ `interpretedGoals` inclui `produtividade` COVERED;
`ignoredGoals=[]`; `servesGoals` por bloco; sem persistência.

## Veredito

**`DI371_ACCEPTANCE = PASS`** — `GOAL_PRESERVATION_VERIFIED` +
`CONTEXT_SEPARATION_VERIFIED` + `COVERAGE_INTEGRITY_VERIFIED`;
produtividade nunca mais em `ignoredGoals` quando solicitada.
