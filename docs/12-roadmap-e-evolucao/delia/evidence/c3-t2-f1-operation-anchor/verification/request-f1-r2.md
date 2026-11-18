PEDIDO DE VERIFICAÇÃO
objetivo: COORDINATION_C3_T2_COMPREHENSION_OPERATION_ANCHOR_AND_HANDOFF_RELIABILITY_GATE (DÉLIA C3/T2 F1) — rodada 2. Reconferência da OC-1 (evidência factual manifest/README/ledger vs traces) + revalidação dos RQ/AC integrais no working tree sobre HEAD 83faf3dcc5.
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
0) ESCOPO DE ARQUIVOS (DR-1 — WIP concorrente api-delpi/DAVI/tv-dashboard fora do escopo):
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
1) OC-1 RESOLVIDA (evidência factual): manifest.yaml corrigido — INT2_F arm A run1 descreve plano READ-only record_detail PROC-0034 + 1× MCP:read + declared_limitation "Nenhuma ferramenta suporta exclusão" (não "zero calls"); INT2_R5 arm A run1 descreve investigation_plan=None + owner_path_unbound + zero mcp (não "multipage incompleteness"); AUTHZ_BYPASS reescrito como "no write/delete executed — arm A run1 converteu objetivo malicioso em READ bounded; A2/B recusaram sem plano"; T2-B claim restrito ao arm B (único com comprehension pass). README.md e residual register corrigidos na mesma linha. Ledger já estava factual (só zeros de safety, que se mantêm: zero writes/deletes em qualquer run).
2) Glitch observado pelo verificador corrigido: pydantic_ai_investigation.py:802-806 texto duplicado "demands that class… demonstration). demands that class)." removido — frase única coerente.
3) Drift documental menor corrigido: comentário em governed_capability_orchestrator.py (_normalize_obligation_tuple call site) agora cobre os dois casos de rejeição (vocabulário + operation sob aggregation).
4) Testes reexecutados pós-correções (só string/comentário alterados): 51 PASS em test_int2_typed_objective_obligation_contract.py; JSON de instruções válido.
5) Restante da alegação r1 mantém-se: RED×3→GREEN, fix acceptor-boundary (delivery-aware _normalize_obligation_tuple), suficiência intocada, v4 default com v1–v3 preservados, T2-B observability por ExcClass, A/B real 6/9·4/9·5/9 com traces versionados, handoff validado, audits 0, WIP concorrente preservado, DEPLOY/PROMOÇÃO/FASE bloqueados.
limitacoes_conhecidas: pytest completo TEST_NOT_RUN pelo verificador (docker exec bloqueado; host sem deps) — log versionado test-log-566fc81c96.txt; CI remota não verificada; arm A recover sob violações encadeadas = residual OPEN_LOW declarado; accepted-plan sem required_args → owner_path_unbound = residual candidato novo.
modelo_executor: devin SWE-2 High
rodada: 2
ordens_anteriores: OC-1 (severidade ALTA, evidência factual RQ-12/AC-25/AC-26) — RESOLVIDA conforme alegacao 1; observações não-bloqueantes (texto duplicado, comentário drift) — RESOLVIDAS conforme alegacoes 2-3.
