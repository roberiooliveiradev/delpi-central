# 55 — VISTA/TV — ISSUE #129 RESIDUAL CLOSURE — EXECUTION REPORT

Data: 2026-11-03 | Task: VISTA-TV-129-RESIDUAL-CLOSURE
Base HEAD: b9b73bd7e1 (observado a2c2020e31 + 1 commit public-hub não relacionado)

## Reanchor

- DOCUMENTATION_REANCHOR = PASS — doc 51 deletado no index foi recuperado do
  HEAD; docs 52–54 lidos; capability surface, contracts e ownership
  revalidados contra o código.
- WORKTREE = DIRTY (198 entradas) — contamination pré-existente de sessões
  concorrentes (delia-api, docs, EOL-CRLF em tv-dashboard-api). Nenhum
  conteúdo real alterado nos arquivos do owner pelo changeset staged;
  trabalho isolado por path no commit.
- OWNER = tv-dashboard-api (GptActionsDispatchService.suggest_change +
  _enrich_composition_ops) — confirmado.
- CONTRACT_IMPACT = NONE — mesmos campos/enum; apenas classificação
  correta de falhas (erro interno sobe como erro; ausência tipada
  preservada).
- SECURITY_IMPACT = nenhum — assert_permission/AccessService/consent
  gate inalterados; delete_block continua confirm-gated
  (CONFIRM_OPS_PREFIXES).
- PARITY_IMPACT = nenhum — renderer/stage/preview não tocados.
- EXISTING_EQUIVALENT = YES — delete_block no catálogo canônico;
  sweep de redesign já existia; nenhum mecanismo novo criado.
- REUSE_DECISION = REUSE — correção de ordem/semântica no mecanismo
  canônico existente.

## Root causes (PROVEN)

| Resíduo | Sintoma | Causa raiz | Evidência |
|---|---|---|---|
| R1a | Falha de leitura → "slide vazio" | `except Exception: existing_blocks = []` colapsava not-found, authz, infra e defeitos; `_sl` via `locals().get` | E01/E02/E05 RED |
| R1b | Defeito de programação → PREVIEW_UNAVAILABLE | `except Exception` no bloco visualEvidence fabricava status operacional | E06/E08 RED |
| R2a | Tabela antiga sobrevive ao redesign | `_take_existing` consumia o bloco persistido ANTES do drop do scaffold `table_view` → escapava do sweep delete_block | C01 RED |
| R2b | Sweep destrutivo em pedido de criação | regex `_redesign` incluía `desenvolva\|design` (vocabulário de qualidade/criação) | acoplamento C01↔C02 |
| R2c | "remova a tabela" mantinha a tabela | `want_table` por keyword tratava pedido de remoção como presença; drop ainda exigia redundância de goals | runtime smoke no container |

## Fix mínimo (dispatch_service.py)

1. Leitura do slide: UUID parse isolado (malformado → ausência),
   `PresentationWriteError(RESOURCE_NOT_FOUND)` → ausência legítima,
   demais `PresentationWriteError`/`GptActionsError`/inesperado →
   propagam com `logger.exception` sanitizado (playlist_id/slide_id,
   sem tokens/URLs). `_sl`/`_slide_missing` explícitos — sem
   `locals().get`.
2. visualEvidence: `except GptActionsError: raise`; demais exceções
   → log sanitizado + raise. Sem PREVIEW_UNAVAILABLE fabricado.
3. `_enrich_composition_ops`: `_take_existing` movido para depois do
   drop de scaffold (só consome quando o op entra na composição);
   `_redesign` restrito a intenção de substituição
   (`redesenh|reorganiz|refaz|refazer|rework|redesign|substitua|substituir`);
   `_table_removed` (menção de tabela em contexto de remoção) descarta
   o scaffold incondicionalmente.
4. `test_vista_execute._writes_mock` spec += `get_slide` (o serviço
   real possui — o spec incompleto era mascarado pelo bug R1a).

## Evidência

- RED→GREEN: 18 testes novos (E01–E10, C01–C12) —
  tests/test_issue129_residual_integrity.py. Antes do patch: E01, E02,
  E05, E06, E08, C01 falhavam; depois: 18/18.
- Regressão: 2473 testes do pacote PASS.
- Runtime local (container, catálogo real 591 rotas, fixture
  E2E-TV-026-LOCAL):
  - REDESIGN §9 → proposal com delete_block dos 8 blocos obsoletos,
    zero table_view no upsert.
  - CREATE §9 → zero delete_block; heading+kpi+chart+kpi(meta).
  - Slide inexistente → SLIDE_NOT_FOUND; repo quebrado → RuntimeError
    propagado com log sanitizado.
  - visualEvidence available + basisRevision=836 + rendered
    EDITOR_NOT_OPEN + designAudit com findings reais (low_contrast).

## Resíduos honestos

- F3 live capture: EDITOR_CAPTURE_PENDING — pipeline completo testado
  por contrato (test_canonical_rendered_preview), mas captura real
  exige sessão de editor autorizada (credenciais TV_E2E_PASS_* não
  provisionadas) e fixture LAB existe em homolog, não no banco local.
- F4 pixel evaluation: ARCHITECTURE_DECISION_REQUIRED — avaliação
  multimodal por pixels não existe no domínio TV (doc 51: VLM só em
  minha-delpi-ai-api, outro bounded context). Structural QA entregue.
- test_vista_execute_delete.py (untracked WIP pré-existente): falha
  por drift de contrato em semantic_delete — fora do escopo.
- Deploy em homolog + MCP smoke autenticado + read-back da fixture
  LAB: pendente de autorização/credenciais.
<<<<<<< HEAD
=======

## Addendum — C04 semantic binding (2º commit b73110cbcb)

Pós-deploy smoke na fixture LAB (produção) revelou resíduo semântico:
no REDESIGN, o KPI de realizado ligava `get_kaizen_summary`. Causas:
tokens de instrução/remoção viravam goals (remova/antiga/preserve/
sobreposição → kaizen tinha 4 goals-lixo); o cap de 6 do goal_map por
ordem de set excluía "oee"; elegibilidade por papel era soft.

Correções: stop-words de instrução/componente; _metric_tok prioritário
no budget; papel = restrição (pool+fallback respeitam _ROLE_ELIGIBLE).

Smoke pós-deploy em produção (b73110cbcb):
- CREATE → realized=oee_realized, chart=oee_series, meta=oee_meta,
  RESOLVED, zero deletes.
- REDESIGN → delete_block(blk_95a53a164d), chart=oee_series,
  meta=oee_meta, realized KPI NEEDS_SOURCE_SELECTION com 3 candidatos
  realized elegíveis (ambiguidade honesta, sem pick silencioso, sem
  kaizen). evidence available + basisRevision=3 + EDITOR_NOT_OPEN.
>>>>>>> origin/main
