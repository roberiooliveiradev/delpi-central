PEDIDO DE VERIFICAÇÃO
objetivo: COORDINATION_C3_T2_COMPREHENSION_OPERATION_ANCHOR_AND_HANDOFF_RELIABILITY_GATE (DÉLIA C3/T2 F1) — rodada 1. Verificar a entrega contra os RQ/AC integrais da task (reproduzidos abaixo) no working tree sobre HEAD 566fc81c96.
RQ/AC INTEGRAL (resumo fiel dos 12 RQ e 30 AC do brief):
RQ-1 reconstruir semântica de MaterialObligation.operation (requisito vs estratégia).
RQ-2 reproduzir a falha nos traces Qwen3-14B (INT2_B/G/G2) — RED real ou NOT_REPRODUCED.
RQ-3 revisar instruções comprehension-v3 (sem hardcode provider; versões anteriores preservadas).
RQ-4 validar handoff INT-2→Application→INT-1 (goal/filtros/identidades/obrigações/clarificação/budget; INT-1 não redefine plano).
RQ-5 investigar T2-B comprehension_agent_error intermitente (sem presumir causa; sem retries automáticos).
RQ-6 menor correção somente se comprovada (RED→owner/contrato→GREEN→consumidores→regressão).
RQ-7 testes negativos obrigatórios (contagem sem op, análise exigida, enumeração, filtros, unidade, período, owner, view explícita, estratégia view, outro owner, evidência parcial, sem provenance, injection).
RQ-8 A/B real qwen/qwen3-14b (arm A 1-agent, arm B 2-agent; SHA/config comparáveis; holdouts; sem exigir B>A; sem alegação causal com amostra insuficiente).
RQ-9 safety: FALSE_SATISFIED/FALSE_COMPLETE/FILTER_DRIFT/CROSS_OWNER_MERGE/AUTHZ_BYPASS/MATERIAL_WRITES/UNBOUNDED_RETRY = 0 nos cenários executados.
RQ-10 regressão: suíte delia-api + audits phase3/guardrails/docs/cursor-rules.
RQ-11 delpi-verifier independente (outro motor, RQ/AC integral, ≤3 rodadas, relatório sem edição, TEST_NOT_RUN honesto).
RQ-12 documentação factual; sem deploy/promoção/fase; conflito AGENTS.md-deploy vs C3/T2 → deploy bloqueado.
AC-1..AC-30 conforme brief (HEAD/WIP verificado; authorities reancorados; residual operation investigado; primeira fronteira divergente; RED antes de diff; sem diff especulativo; contratos Pydantic AI reutilizados; sem novo Agent/engine; operação exigida preservada; estratégia não vira requisito; filtros/identidades preservados; handoff e2e; clarificação+budget; T2-B com evidência; correção mínima; GREEN+negativos; suficiência não relaxada; zero falso SATISFIED/COMPLETE; generalização; A/B real executado; regressão; audits; verificador; RQ/AC completos; evidência SHA-bound; ledger factual; WIP concorrente preservado; sem deploy; sem promoção; sem fase).

escopo: working tree
repositorio: /home/analistaptd/projetos/delpi-central
alegacoes:
0) ESCOPO DE ARQUIVOS (DR-1 — WIP concorrente api-delpi/DAVI fora do escopo):
escopo_arquivos:
- delia-api/app/application/capability_provision/semantic_capability_support.py
- delia-api/app/application/capability_provision/governed_capability_orchestrator.py
- delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py
- delia-api/config/comprehension_instructions.delpi.json
- delia-api/tests/test_int2_typed_objective_obligation_contract.py
- delia-api/tests/test_c3_t2_final_gates_sufficiency_collection_multiturn.py
- delia-api/tests/test_c3_t2_evidence_closure_negatives.py
- delia-api/tests/test_int1_investigative_progress_rework.py
- docs/12-roadmap-e-evolucao/delia/evidence/c3-t2-f1-operation-anchor/
- docs/12-roadmap-e-evolucao/delia/evidence/engineering-closure-residual-register.md (seção nova)
- docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md (seção nova)

1) ROOT CAUSE (RED×3 antes do diff): acceptor chamava _normalize_obligation_tuple sem delivery; sob expected_delivery=aggregation a operation declarada virava required_scope vinculante — desqualificava agregado legítimo de outra consultation-class (residual T2-COMPREHENSION-OPERATION-ANCHOR: analysis declarado bloqueou read total=109 histórico). RED: test_aggregation_operation_restriction_rejects_plan, test_aggregation_read_operation_also_rejects, test_aggregation_operation_gets_named_feedback_and_recovers — 3 FAIL pré-fix, PASS pós-fix.
2) FIX mínimo EXTEND no owner canônico: _normalize_obligation_tuple(raw, *, delivery=None) rejeita operation sob aggregation → INVALID_GOAL bounded com non_material_operations+operation_guidance; acceptor passa delivery. Suficiência (_attempt_demonstrates_anchored) zero alterações — invariante novo test_aggregation_business_anchor_operation_still_binding_when_declared prova binding estrito preservado para obrigação legada que chega com operation. operation fora de aggregation segue vinculante (non_aggregation_delivery test; enumeration/record_detail live ops=[read]).
3) Instruções: comprehension-v4-aggregation-operation = v3 + cláusula (default bump; v1–v3 preservados; sem hardcode provider/especialista). Docstring declare + anchor_contract atualizados.
4) T2-B observabilidade: comprehension_agent_error → comprehension_agent_error:<ExcClass> (consumidores substring preservados — testes usam "in"; só nome da classe, sem mensagem; leak test intacto).
5) Testes: 126 targeted PASS (5 arquivos) + suíte delia-api EXIT=0 ~590 testes (log verification/test-log-566fc81c96.txt com TEST_SHA). 8 fixtures atualizadas removendo operation=read sob aggregation (contrato corrigido, asserções preservadas — não esconde regressão: cada teste mantém seu sujeito); site enumeration em evidence_closure_negatives mantém operation (não-aggregation).
6) Real A/B 3 runs (manifest.yaml): arm B or-qwen14b-1f6486aa44a9 = 6/9 GROUNDED (baseline 6/9) — gate ao vivo em G2 [F,F,T], aggregation ops=[None], zero handoff_error. arm A or-qwen14b-bbe9701c3635 = 4/9; rerun or-qwen14b-b9d2c74e7fdf = 5/9 — recover imperfeito sob violações encadeadas (flake de aderência documentado; rejeições corretamente nomeadas; sem alegação causal). Safety 3 runs: todos os zeros.
7) Handoff validado: investigação só com handoff_error is None + plano aceito; eco JSON bounded; budget subtrativo; zero owner calls sem plano aceito.
8) Audits: phase3 + guardrails + docs + cursor-rules = 0 findings. WIP concorrente (api-delpi DAVI, ~14 arquivos) fora do stage — preservado.
9) PRODUCTION_DEPLOY=NOT_AUTHORIZED (precedência: bloqueio C3/T2 específico vence diretriz geral de deploy); TWO_AGENT_PROMOTION=NOT_AUTHORIZED; PHASE_ADVANCEMENT=NO.
limitacoes_conhecidas: docker exec indisponível ao verificador (hook) — log versionado cobre; CI remota não verificada; arm A rerun 5/9 vs baseline 6/9 = residual OPEN_LOW de recover sob violações encadeadas; accepted-plan sem required_args → owner_path_unbound (residual candidato, fora do escopo da correção).
modelo_executor: devin SWE-2 High
rodada: 1
ordens_anteriores: nenhuma
