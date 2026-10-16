# 10 — Revisão independente da Etapa 02R1 (B1/B2)

**TASK:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02R1-INDEPENDENT-REVIEW`
**DATA:** 2026-10-16
**REVIEWED_SHA:** `9fd3a7bc959686a6c4828f46b7d292c81a96938c`
**REVIEW_BASE_HEAD:** `9fd3a7bc959686a6c4828f46b7d292c81a96938c` (GitHub main remoto; working tree local TO_INVENTORY)
**MODE:** revisão estática de código, testes scripted, contratos e autoridades; nenhuma suíte executada pelo revisor, nenhum write real, nenhum deploy.
**VERDICT:** `REWORK` — B1 corrigido estruturalmente; B2 parcial, com fail-open sob interpretação semanticamente incorreta ou ausente do bound. `STAGE_02_ACCEPTED=NO`. `ARCHITECTURE_DECISION_REQUIRED` se a mitigação pretendida necessitar de novo contrato/gate, pois o reviewer não autoriza redesign.

## 1. Reancoragem e autoridade

HEAD remoto confirmado. Revalidadas cláusulas pertinentes de Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → 02 → 24 → specs 60/69/70, personality/02 e ledger §§6.126/6.130/6.133/6.140/6.141/6.145/6.171–6.175; plano 02/03/05, review 08 e relatório 09 da pasta. A ordem/phase/NEXT vem de 16+ledger no HEAD; não inferir do texto deste review.

Congelados: DÉLIA única e provider-neutral, MCP/owner = interoperabilidade e Domain authority, modelo output=HYPOTHESIS (nunca autorização), same-owner bounded resolver, PREPARE != ACT, `max_execution_stage='prepare'` reduction-only, confirmação estrutural selada do PREPARE (§6.140), `MODEL_AUTHORED_FACTUAL_PROSE=NONE` (§6.145).

## 2. Entrega efetivamente demonstrada

- `orchestration.py` instruction v8→v9; alinha wording ACT com owner-sealed confirmation. Nenhum novo planner/registry/engine/branch por provider.
- **B1 PASS estrutural**: ausência ou erro do objetivo agora significa `declared=False`, e write selection leva a `CLARIFICATION_REQUIRED` antes de PREPARE/ACT. Classe inválida deixa de ser forçada a `read` declarado. Casos `test_s2r1_uninterpreted_goal_never_promotes_write`, `test_s2r1_invalid_goal_guidance_never_writes`, write-only surface e owner renomeado inspecionados; provam o caminho sob propostas fakes.
- **B2 PASS somente condicional**: `_TurnGoal.execution_bound='prepare_only'` validado e `prepare_only = prepare_only or (goal.execution_bound=='prepare_only')` utiliza o teto existente; sob esse campo recebido, owner `explicit_user_confirmation=False` não faz ACT direto. Testes com provider fake verificam essa propriedade e o controle positivo `unrestricted`.
- O executor reporta 31/31 testes do arquivo baseline e 1085/1085 suite completa PASS. **INDEPENDENT_REEXECUTION=TEST_NOT_RUN**; código e test assertions revisados pelo GitHub. Relatório 09 e ledger §6.175 conservados como evidência do executor.

## 3. Bloqueio residual material — B2 (PROVEN code path, scenario replay TEST_NOT_RUN)

Na versão revisada, `execution_bound` é um campo da proposta **do modelo**, não uma restrição extraída por mecanismo determinístico com prova independente. Em `_understand_goal`, a ausência, valor inválido ou resposta errada normaliza o bound para `'unrestricted'`. O path ACT direto é escolhido em `_attempt_prepare` quando owner PREPARE sela `explicit_user_confirmation=False` e `prepare_only=False`, sujeito aos demais gates.

Contraprova de contrato que falta no harness:

    input_text = 'Prepare um cadastro, mas não aplique.'
    max_execution_stage = None
    model_goal = {'goal_class':'create_or_modify','execution_bound':'unrestricted'}
    selected_target = PREPARE
    owner_preview = READY, explicit_user_confirmation=False
    owner_act = available

Nessas premissas, nenhuma validação posterior coteja o bound com a restrição explícita da mensagem; o path de execução direta permanece elegível, apesar da frase 'não aplique'. É um **caminho de risco demonstrado pela leitura do código**; frequência de classificação errada e ACT real são `TEST_NOT_RUN`, não alegar reprodução ao vivo.

Os testes `test_s2r1_prepare_only_bound_blocks_direct_act` e `test_s2r1_execution_bound_semantic_variants` sempre fornecem ao FakeProposalModel **`execution_bound='prepare_only'`** para as frases testadas. Logo não validam que o modelo reconheça cada formulação nem que o sistema resista ao erro contrário; apenas testam que o teto já reconhecido é aplicado. `test_s2r1_unrestricted_create_keeps_direct_continuation` confirma separadamente o caminho ACT sob `'unrestricted'` em frase de ação sem limite.

Este risco é especialmente importante porque §6.140 permite continuação direta governada sem confirmação adicional (decisão que não pode ser silenciosamente substituída por confirmação universal). A segurança da restrição negativa do usuário não deve depender exclusivamente de uma classificação otimista do LLM.

### Observação complementar — structured confirmation bypass (TO_INVENTORY)

`_attempt` trata `confirmation is not None` antes da seleção e da chamada `_understand_goal`; nesse caminho o bound textual novo não é calculado. O ceiling estruturado do request continua aplicável, mas uma mensagem atual com 'não aplique' e payload de confirmação divergente exige exame do contrato de precedência. Não presumir bypass explorável nem mudar fluxo de confirmação sem teste/decisão. Tratar separadamente como test candidate se aplicável ao mesmo B2.

## 4. Reuse Gate e critérios da menor ação seguinte

`EXISTING_EQUIVALENT=YES`: modelo de goal, instruction stages, `max_execution_stage` request-scoped reduction-only, governança owner-sealed, capability orchestrator, `CLARIFICATION_REQUIRED`, `TurnDeadline`, existing test harness. `REUSE_DECISION=REUSE/EXTEND`, sem autorização de NEW.

- Reproduzir RED **contradictory-bound**: texto proíbe ACT, proposta modelada `create_or_modify + unrestricted`, owner READY/direct e request ceiling None → provar calls ao fake ACT ou seu bloqueio. Sem real writes.
- Incluir missing/invalid `execution_bound` com `goal_class=create_or_modify`, e proteção do teto explícito do request. Os testes devem verificar a intenção expressa no input, não apenas repetir a proposta que o modelo fictício recebeu.
- Propor o menor mecanismo legítimo que preserve instrução explícita de não-ação sem dar autoridade ao modelo ou criar confirmação universal. Inspecionar os contratos atuais de request, guardrails e ceiling. Se exigir contrato adicional, extração/validação semântica material ou outro gate, **STOP → ARCHITECTURE_DECISION_REQUIRED**, documentando 2–3 alternativas e custos, sem implementar por conveniência.
- Não duplicar Domain owner policy, não hardcode por MCP/entidade, não assumir que regex/nova classe de goal/segundo modelo resolverá. Preserve controle positivo de governança direta sem restrição.
- Rever também a interação do texto da mensagem com payload de confirmação quando aplicável; não ampliar Stage 02 para as Etapas 03–06.
- Executar teste RED/GREEN, suíte completa, holdout/metamorphic e avaliações de modelo real segura se autorizadas; registrar SHA/config/model/latência/tokens/resultados separados de fakes.

## 5. Veredicto e estado

**B1=ACCEPT_WITH_RESIDUAL** (estrutural e com fake, não certifica taxa de erro com modelo real).
**B2=REWORK** (teto reconhecido corretamente aplicado; contraexemplo de bound não reconhecido permanece sem gate).
**STAGE_02R1_OVERALL=REWORK**, sem aceite de Etapa 02, sem liberação de Etapa 03. A revisão não executou testes nem alterou runtime.

NEXT=RETURN_TO_ARCHITECTURE_COORDINATION: discutir explicitamente a segurança de restrição textual versus owner-direct continuation; somente depois autorizar correção bounded ou registrar ADR necessária. `C3_EXECUTED=NO`, `C4_AUTHORIZED=NO`, `C5_AUTHORIZED=NO`, `PRODUCTION_READINESS=NOT_PROVEN` neste snapshot.