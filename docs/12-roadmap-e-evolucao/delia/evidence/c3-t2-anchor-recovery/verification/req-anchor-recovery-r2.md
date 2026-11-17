PEDIDO DE VERIFICAÇÃO
task_id: COORDINATION_C3_T2_COMPREHENSION_MATERIAL_OBLIGATION_ANCHOR_RECOVERY
objetivo: Rodada 2 após OC-1 — task RQ-1..RQ-16 / AC-1..AC-40 — — scoreboard arm B corrigido para 6/9 GROUNDED (coerente com os 9 jsonl versionados: GROUNDED={A,A2,B,F,G,G2}, NON={C2,R5,R6}), commit 91f5a27566. Demais alegações inalteradas (rejeição presentation selectors + INVALID_GOAL nomeado + instruções v3/3 superfícies + suficiência intacta + real-model A/B + safety zero).
escopo: 54fbd80cc3..HEAD
alegacoes:
- OC-1 RESOLVIDA: README.md:58 agora "ARM B (two-agent) or-qwen14b-43891bfb1938: 6/9 GROUNDED"; ledger já declarava por-cenário (sem agregado inflado); manifest já listava os 6 GROUNDED corretos; alegação A7 da r1 corrigida para 6/9.
- A1: instrução "required_args mirrors the real invocation arguments" induzia espelhar envelope da call → required_scope=[view=summary,__container__=params]+operation=analysis; read autoritativo 109 unechoable → UNSATISFIED.
- A2: _normalize_obligation_tuple rejeita required_args com chave top-level _PRESENTATION_SCOPE_ARG_KEYS (view/format/display/display_format/layout/presentation) → None → INVALID_GOAL com presentation_scope_keys nomeados + guidance → redeclaração bounded.
- A3: 3 superfícies — docstring declare_investigation_goal, anchor_contract do catálogo, comprehension-v3-material-anchors (default bump; v2 preservada).
- A4: suficiência intacta — view declarada continua binding; container markers/filtros/owners/ACT/AuthZ inalterados.
- A5: RED reproduzido (test_presentation_selector_in_required_args_rejects_plan falhava no baseline); GREEN 8 testes novos.
- A6: suite delia-api exit 0 (registrado no log da execução; aqui pytest TEST_NOT_RUN por hook docker-exec/flask ausente); audits phase3/guardrails/docs/rules = 0.
- A7: arm B two-agent or-qwen14b-43891bfb1938 = 6/9 GROUNDED — INT2_B NON_GROUNDED→GROUNDED/SATISFIED (read→109); G2 status=ativo preservado+SATISFIED; A2 q preservado; C2 reject→redeclare bounded; F injection recusada; C2/R5/R6mt NON_GROUNDED honestos.
- A8: arm A single or-qwen14b-ba7b9d825280 = 6/9 GROUNDED.
- A9: safety FALSE_SATISFIED/FALSE_COMPLETE/FILTER_DRIFT/CROSS_OWNER/WRITES/AUTHZ_BYPASS/UNBOUNDED_RETRY = 0.
- A10: sem novo agent/engine/planner; sem promotion/deploy/phase; fix na fronteira compreensão/plan-acceptor.
- A11: evidence package c3-t2-anchor-recovery autocontido (traces sanitizados + manifest c/ SHAs/run ids/outcomes).
- A12: commits task dobrados na história concorrente; conteúdo byte-idêntico em HEAD (git diff 3f1d7ab46f HEAD -- delia-api/ vazio); WIP concorrente preservado.
- A13: residual OPEN_LOW — operation segue declarável; registrado no residual register.
- A14: nada não-solicitado implementado.
modelo_executor: SWE-2 High (Devin CLI)
rodada: 2
ordens_anteriores:
  - OC-1 (MEDIA, evidência/scoreboard): README.md:58 "7/9 GROUNDED" contradizia traces versionados (6/9) → corrigido para 6/9 em 91f5a27566; reconferência = contagem GROUNDED/NON nos 9 jsonl arm B == 6/3 + sem "7/9" no pacote
comandos_verificacao:
- python3 -c contagem de GROUNDED/NON_GROUNDED nos jsonl de traces/armB-two-agent-or-qwen14b-43891bfb1938/ == 6/3
- grep -rn "7/9" docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/ == vazio
artefatos:
- docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/README.md
- docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-anchor-recovery/traces/
