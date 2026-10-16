# Etapa 02R1 — Relatório de rework: intenção não interpretada e limite explícito de execução

**Task:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02R1`
**Data:** 2026-10-16
**MODE:** `BOUNDED_REWORK` — somente os bloqueios B1 e B2 do veredicto §6.174
**REVIEWED IMPLEMENTATION:** `4a9f05e5b9bd2b40332638d5bec49678de050bdd`
**BASE_HEAD:** `a6196637ea84984db7689a259dac0907d6d45218` (main, sync `origin/main`, pós-review §6.174 + commits remotos subsequentes)
**Escopo executado:** somente B1 (intenção não interpretada → escrita) e B2 (restrição textual "não aplique" com owner direct). Nada da Etapa 03.

## 1. Gate de entrada

- Revisão independente localizada: [08](./08-stage-02-independent-review.md), ledger §6.174 — veredicto `REWORK`, dois bloqueios nomeados (B1 `UNINTERPRETED_INTENT_WRITE_CONTINUATION`, B2 `PREPARE_ONLY_USER_BOUND_NOT_PROVEN`).
- HEAD, branch e remoto revalidados; alterações concorrentes do usuário em `plugins/*`, `requests-api` e `docs/12-roadmap-e-evolucao/bpmn-modeler` preservadas e não staged.
- Authorities reancoradas na ordem canônica 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24 → specs temáticas → ledger (§§6.126/6.130/6.133/6.140/6.141/6.145/6.171/6.172/6.173/6.174).
- Estado vigente confirmado: `STAGE_02_REVIEW=REWORK`; `C3_EXECUTED=NO`; `NEXT=RETURN_TO_ARCHITECTURE_COORDINATION`. Sem `EXECUTION_DRIFT`.

## 2. Root cause dos bloqueios

**B1 — intenção não interpretada podia promover escrita.** O gate da Etapa 02 exigia `goal.declared AND goal_class != create_or_modify` para intervir; quando nenhuma interpretação válida existia (`declared=False`), a seleção de escrita anterior prosseguia. Ausência de interpretação não é prova de pedido de ação — mas também não era tratada como incapacidade de prová-lo.

**B2 — restrição textual não virava teto de execução.** `max_execution_stage` é reduction-only e vem do `InteractiveTurnRequest`; o texto do usuário ("prepare, mas não aplique") não tinha representação no contrato validado do turno, então com ceiling `None` e owner `explicit_user_confirmation=False` a continuação direta governada podia alcançar ACT contra a restrição explícita.

## 3. Inventário e Reuse Gate

Inspecionados: `_TurnGoal`, `_understand_goal` (allowed_keys, `_GOAL_CLASSES`), `_attempt` (gate de finalidade), `InteractiveTurnRequest.max_execution_stage` → `prepare_only`, `_attempt_prepare`, `_attempt_direct_act`, `evaluate_write_continuation`, `confirmation_requirement`, consumers do teto (três fronteiras ACT), `_propose` (rejeição fail-closed de chaves desconhecidas).

- `EXISTING_EQUIVALENT = YES` — interpretação de objetivo validada, enum de classe owner, `CLARIFICATION_REQUIRED`, teto reduction-only `prepare_only` já consumido em todas as fronteiras ACT.
- `REUSE_DECISION = EXTEND` — estender o contrato de objetivo existente com um campo bounded e reforçar o gate existente. Nenhum novo planner, engine, registry, agente, parser de frases ou prompt por provider. `_GOAL_CLASSES` inalterado. Nenhum contrato congelado alterado → `ARCHITECTURE_DECISION_REQUIRED` não acionado.

## 4. Implementação (menor diff)

Arquivo funcional único: `delia-api/app/application/capability_provision/orchestration.py` (~163 linhas de diff, contra o HEAD da Etapa 02).

1. **B1 — gate reforçado:** a condição passa a ser `descriptor.operation_class ∈ {PREPARE, ACT}` com `not goal.declared OR goal_class == "clarify"` → `CLARIFICATION_REQUIRED` (`_INTENT_CLARIFICATION_CONTENT`, conteúdo fixo de negócio). Interpretação ausente/inválida agora é ask-back proporcional, nunca continuação de escrita. Objetivo declarado não-ação (`read|analyze|compare`) continua a demote via reseleção bounded; `create_or_modify` declarado preserva o caminho governado.
2. **B1 — classe inválida não é "read" declarado:** `goal_class` fora de `_GOAL_CLASSES` retorna o `_TurnGoal` neutro (`declared=False`) em vez de coagir para `read` declarado — uma proposta ininterpretável não vira intenção inventada.
3. **B2 — `execution_bound` no contrato de objetivo:** novo campo bounded `_EXECUTION_BOUNDS = {unrestricted, prepare_only}` em `_TurnGoal`, validado em `_understand_goal` (allowed_keys + whitelist; valor inválido → `unrestricted`). `GOAL_INSTRUCTION` descreve semanticamente a restrição ("prepare, mas não aplique", "apenas uma prévia", "sem executar", "do not apply") — nenhuma lista de keywords hardcoded no código.
4. **B2 — composição reduction-only:** `prepare_only = prepare_only or (goal.execution_bound == "prepare_only")` em `_attempt` — o bound textual só pode reduzir o teto efetivo, nunca ampliá-lo, e compõe com `max_execution_stage` do request (o mais restritivo vence). Cobre PREPARE→continuação direta E seleção fria de ACT.
5. **Instruções 8 → 9:** `SELECTION_INSTRUCTION_VERSION` bump; `GOAL_INSTRUCTION` ganhou o campo `execution_bound`; `CAPABILITY_SELECTION_INSTRUCTION` corrigida — "ACT only after explicit confirmation" → "ACT only through the governed continuation of a prepared proposal under the owner-declared confirmation policy", alinhando a instrução à política estrutural §6.140 (inconsistência residual apontada pelo review).

## 5. Testes RED → GREEN

Harness reutilizado (`test_conversational_intelligence_baseline.py`, `FakeProposalModel`/`InvokeModel`, providers neutros fictícios).

RED antes do diff — bloqueios reproduzidos no código da Etapa 02:

| Caso | Comportamento RED |
|---|---|
| B1-01 "Você consegue criar?" + objetivo ausente + PREPARE selecionada | PREPARE invocado (teste antigo da Etapa 02 chegava a afirmar isso) |
| B1-02 "Como criar um processo?" + proposta de objetivo inválida | caminho de escrita prosseguia |
| B1-05 superfície só-escrita + objetivo ausente | escrita por eliminação |
| B1 renomeado (provider/capability) | mesma promoção indevida |
| B2-01 "Prepare, mas não aplique" + owner `confirmation=False` + ceiling `None` | ACT invocado — restrição textual ignorada |

GREEN após implementação — 8 testes novos, todos PASS:

1. `test_s2r1_uninterpreted_goal_never_promotes_write` (B1-01)
2. `test_s2r1_invalid_goal_guidance_never_writes` (B1-02)
3. `test_s2r1_uninterpreted_write_only_surface_never_writes` (B1-05)
4. `test_s2r1_uninterpreted_gate_is_name_invariant` (B1 renomeado)
5. `test_s2r1_prepare_only_bound_blocks_direct_act` (B2-01)
6. `test_s2r1_execution_bound_semantic_variants` (B2-06: cinco formulações equivalentes)
7. `test_s2r1_unrestricted_create_keeps_direct_continuation` (B2-03 controle: continuação direta governada preservada)
8. `test_s2r1_prepare_only_bound_blocks_cold_act_selection` (B2 sibling: seleção fria de ACT → `WRITE_REJECTED execution_ceiling`)

Cobertura existente preservada para os demais casos exigidos: B1-03 (`test_s2_explicit_create_keeps_governed_write_path`), B1-04 (`test_s2_ambiguous_request_clarifies_without_writing`), B2-02/B2-04/B2-05 (suíte `test_execution_ceiling_turn_budget.py` — ceiling do request, confirmação obrigatória e `owner_policy_invalid`).

O teste `test_s2_uninterpreted_goal_preserves_governed_write_path` da Etapa 02 — que a revisão citou como evidência do bloqueio — foi substituído pelos casos s2r1: sua expectativa anterior codificava o defeito corrigido (mudança de expectativa justificada pelo veredicto §6.174, não mascaramento).

**Regressão:** suíte `delia-api` integral — **1085/1085 PASS** (exit 0); arquivo de baseline 31/31. Fixtures de escrita sem objetivo declarado em `test_generic_multistep_orchestration.py`, `test_intelligence_loop_evals.py`, `test_provider_neutral_orchestration.py` e `test_semantic_path_composition_evals.py` passaram a declarar `goal_class="create_or_modify"` — exigência semântica nova (caminho de escrita requer intenção de ação *declarada*). Testes de clarificação por input faltante também declararam o objetivo para continuar exercendo a camada de argumentos/§6.144, não para contornar o gate. Nenhum expected de negócio enfraquecido.

## 6. Métricas (harness scripted; sem LLM real)

| Métrica | Antes (Etapa 02) | Depois (R1) |
|---|---|---|
| Objetivo ausente/inválido + seleção de escrita → escrita | alcançava PREPARE | 0 — `CLARIFICATION_REQUIRED` |
| "Prepare, mas não aplique" + owner direct + ceiling None → ACT | ACT invocado | 0 — teto respeitado |
| Continuação direta governada sem restrição (B2-03) | funcionava | preservada |
| Goal misclassification residual (`create_or_modify` em orientação) | instrução-mitigado | inalterado (residual) |
| Model calls por turno | inalterado | +0 (clarify/fail-closed) ou +1 (demote→reseleção) — inalterado vs Etapa 02 |
| Latência/tokens reais | — | TEST_NOT_RUN |

## 7. Segurança e revisão adversarial do diff

- Gate consome somente `operation_class` (enum owner) + campos validados de `_TurnGoal` — zero branch por nome de provider/capability/entidade; invariância de renomeação testada.
- `execution_bound`: whitelist de dois valores; valor inválido/ausente → `unrestricted` (nunca inventa restrição nem autoridade); composição `or` garante reduction-only — nenhum caminho pode elevar prepare→ACT.
- Chave `execution_bound` adicionada a `allowed_keys` — rejeição fail-closed de `_propose` preservada; propostas permanecem HYPOTHESIS.
- Nenhuma alteração em `confirmation_requirement`, owner policy, `evaluate_write_continuation` ou nas três fronteiras ACT existentes — o bound reutiliza o teto `prepare_only` já consumido, não duplica o ceiling nem cria segunda autoridade.
- `MODEL_AUTHORED_FACTUAL_PROSE=NONE` preservado; conteúdo de clarificação fixo; nenhum write real, secret ou deploy.
- `git diff --check` limpo nos arquivos da etapa; sem termos provider/entity-específicos no diff.

## 8. Residuais e limitações (para revisão independente)

1. **Dependência do objetivo validado:** B1 e B2 confiam na interpretação de objetivo do modelo — um `create_or_modify` declarado para orientação, ou `unrestricted` para um pedido prepare-only, não é detectável deterministicamente. Instrução v9 mitiga; frequência real = `TEST_NOT_RUN`.
2. **Ask-back em vez de demote para não-declarado:** objetivo ausente + escrita selecionada resulta em clarificação, não em reseleção não-mutante — deliberado: sem interpretação válida não há base semântica para provar que uma capability não-mutante é a resposta certa ("menor caminho seguro": esclarecer).
3. **`execution_bound` reduz, nunca amplia:** um bound `prepare_only` espúrio pode impedir ACT legítimo no turno — direção fail-safe; o usuário pode reinvocar a continuação.
4. **Generalização real:** `TEST_NOT_RUN` — todos os resultados são com `FakeProposalModel` scripted; nenhum claim de comportamento de LLM real, tokens, custo ou latência.
5. Fixture OpenAPI dedicada continua ausente; `FakeProvider` cobre estrutura provider-neutra.

## 9. Estado

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`; `INDEPENDENT_REVIEW=PENDING`; `STAGE_02_ACCEPTED=NO` até nova revisão independente; nenhuma mudança de fase declarada. Relatórios 04/06/07/08 preservados como histórico.

NEXT = STOP → RETURN_TO_ARCHITECTURE_COORDINATION
