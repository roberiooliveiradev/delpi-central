# Etapa 02 — Relatório de implementação: intenção e coerência semântica

**Task:** `DELIA-C3-CONVERSATIONAL-INTELLIGENCE-GAP-CLOSURE-01-STAGE-02`
**Data:** 2026-10-16
**Autorização:** prompt bounded da coordenação (este documento não se autoaceita)
**BASE_HEAD:** `6ab302be59f228b1b452cd0dce77d6f171436907` (main, sync `origin/main`, pós-review §6.172)
**Escopo executado:** somente finalidade do pedido + coerência semântica de seleção. Nada das Etapas 03–05.

## 1. Gate de entrada

- Revisão independente localizada: [06](./06-stage-01-independent-review.md), ledger §6.172 — veredicto `ACCEPT_WITH_RESIDUAL`.
- Residuais avaliados contra esta etapa: nenhum bloqueante. A condição pré-implementação do review (sem novo enum / reorder / branch-por-provider / segunda camada) foi respeitada no diff.
- HEAD, branch e remoto revalidados; alterações concorrentes do usuário em `plugins/*`, `requests-api`, `helpdesk-api` e `docs/12-roadmap-e-evolucao/bpmn-modeler` preservadas e não staged.
- Authorities reancoradas na ordem canônica 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → 24 → specs temáticas → ledger.

## 2. Diagnóstico e root cause

Causa raiz estrutural comprovada na Etapa 01 e confirmada nesta etapa:

1. `_select_target` (grupo → capability) executa **antes** de `_understand_goal`; a seleção não dispõe de nenhuma finalidade interpretada.
2. `goal_class` (v7) era consumido apenas por avaliação nativa, projeção de argumentos e comparabilidade — **nunca** como gate sobre a classe da capability selecionada.
3. A instrução de seleção sugeria "crie → prefer PREPARE" sem distinguir pedir *sobre* a ação de pedir *a* ação.

Consequência observável (RED): uma pergunta de orientação podia selecionar e invocar capability PREPARE quando o modelo assim propunha.

## 3. Inventário e Reuse Gate

Inspecionados: `handle_interactive_turn.py`, `instruction.py`, `orchestration.py` (`_attempt`, `_select_target`, `_select_group`, `_select_capability`, `_understand_goal`, `_assess_native_path`, `_propose`, `_attempt_prepare`, `_effective_confirmation_policy`, `_clarification_content`), `model_invocation/` (`InvokeModel`, contratos, lineage).

- `EXISTING_EQUIVALENT = YES` — a orquestração já possui: interpretação de objetivo validada (`_understand_goal`), enum de classe owner (`operation_class`), estágio de seleção reutilizável (`_select_capability`), status de ask-back (`CLARIFICATION_REQUIRED`), fallback fechado (`NOT_APPLICABLE`).
- `REUSE_DECISION = EXTEND` — extensão mínima dos contratos de instrução existentes + gate determinístico de compatibilidade dentro de `_attempt`. Nenhum novo planner, registry, agente, camada ou prompt por provider.
- Enum `goal_class` **não alterado** (`_GOAL_CLASSES` mantém `read|analyze|compare|create_or_modify|clarify`); ordem do pipeline preservada; nenhuma decisão congelada afetada → `ARCHITECTURE_DECISION_REQUIRED` não acionado.

## 4. Implementação (menor diff)

Arquivo funcional único: `delia-api/app/application/capability_provision/orchestration.py` (+119 linhas).

1. **Instruções versionadas 7 → 8** (`SELECTION_INSTRUCTION_VERSION`; lineage `content_hash` cobre os textos alterados):
   - `CAPABILITY_SELECTION_INSTRUCTION`: PREPARE/ACT só quando o usuário pede a mudança em si; perguntas "como criar / quais etapas / me explique" são pedidos de informação e nunca devem ser roteados a classe de escrita.
   - `GOAL_INSTRUCTION`: `read` cobre explicitamente pedidos de explicação/orientação sobre como algo é feito; `create_or_modify` só quando o usuário quer a mudança preparada/executada; `clarify` só para ambiguidade genuína orientação↔ação.
2. **Gate determinístico de finalidade** em `_attempt`, após `_understand_goal` e antes de qualquer estágio de escrita:
   - `descriptor.operation_class ∈ {PREPARE, ACT}` + `goal.declared` + `goal_class ≠ create_or_modify` → incompatível.
   - `goal_class = clarify` → `CLARIFICATION_REQUIRED` com conteúdo fixo (`_INTENT_CLARIFICATION_CONTENT`), sem nomes de capability/campos.
   - demais classes não-ação → **demote**: uma única reseleção bounded reutilizando `_select_capability` sobre a visão filtrada do grupo sem classes de escrita (`dataclasses.replace` sobre o `CapabilityGroup` congelado — catálogo owner intocado). Sem alternativa → `NOT_APPLICABLE` (`error_code=intent_target_incompatible`).
3. **`_TurnGoal.declared`**: `True` somente quando uma proposta de objetivo validada declarou a classe. O default neutro (proposta ausente/inválida) **não** é interpretação declarada — uma falha do estágio de objetivo não pode desabilitar silenciosamente escritas legítimas (fail-open deliberado e documentado; ver §8).

Decisão semântica implementada: *seleção não é autorização*. Pedir ajuda para fazer algo ≠ autorizar que seja feito. O gate compara a finalidade interpretada com a classe owner-declared; a governança de escrita (PREPARE/§6.140, confirmação, ACT) permanece intacta a jusante.

## 5. Testes RED → GREEN

Harness reutilizado (`test_conversational_intelligence_baseline.py`, `FakeProposalModel`/`InvokeModel` seam, provider neutro fictício `acme-flow`/`acme-records`).

RED antes da implementação — 6 casos de defeito reproduzidos:

| Caso | Comportamento RED |
|---|---|
| Orientação ("Como criar…?") | selecionava/invocava PREPARE |
| Superfície só-escrita + intenção informativa | alcançava escrita |
| Pedido ambíguo | alcançava escrita sem esclarecer |
| Turno anterior de ação | escalava orientação seguinte para escrita |
| Provider/entidade renomeados | invariante quebrada |
| Objetivo ausente + seleção de escrita | escrita sem qualquer interpretação |

GREEN após implementação — 9 testes novos, todos PASS:

1. `test_s2_orientation_demotes_write_selection_to_read`
2. `test_s2_write_only_surface_never_writes_on_information_goal`
3. `test_s2_ambiguous_request_clarifies_without_writing`
4. `test_s2_explicit_create_keeps_governed_write_path`
5. `test_s2_prepare_only_request_stops_at_confirmation`
6. `test_s2_prior_action_turns_do_not_escalate_guidance`
7. `test_s2_intent_gate_is_name_invariant`
8. `test_s2_uninterpreted_goal_preserves_governed_write_path` (residual documentado)
9. `test_s2_ineligible_or_invented_selection_rejected` (controle negativo)

**Regressão:** suíte `delia-api` integral — **1078/1078 PASS** (1069 baseline + 9 novos; exit 0). Fixtures de escrita em `test_specialist_capability_orchestration.py` e `test_execution_ceiling_turn_budget.py` atualizadas para declarar `goal_class="create_or_modify"` (helper `_select` ganhou parâmetro `goal_class`) — era exigência semântica nova: caminho de escrita agora requer intenção de ação *declarada*. Nenhum expected enfraquecido.

## 6. Métricas baseline → candidate (harness scripted; sem LLM real)

| Métrica | Baseline (v7) | Candidate (v8) |
|---|---|---|
| Seleção semanticamente correta (casos de defeito) | 0/6 | 6/6 |
| Orientação → PREPARE com objetivo declarado não-ação | alcançava escrita | 0 (demote/clarify/fail-closed) |
| Escritas legítimas recusadas (suíte inteira) | — | 0 adicionais |
| Clarificações | só por input faltante | +1 caminho bounded (clarify + escrita) |
| Model calls por turno | inalterado | +0 (clarify/fail-closed) ou +1 (demote→reseleção) |
| Latência/tokens reais | — | TEST_NOT_RUN (sem LLM real) |

Denominadores: casos scripted do harness; **não** representam frequência em modelo real.

## 7. Segurança e revisão adversarial do diff

- Gate consome somente `operation_class` (enum owner-declared) + `goal_class`/`declared` validados — **zero** branch por nome de provider/capability/entidade.
- Conteúdo de clarificação fixo, sem nomes internos, handles ou metadata → sem vazamento.
- Propostas permanecem HYPOTHESIS; `_propose` (allowed_keys, lineage sha256, fail-closed) inalterado.
- Cadeia PREPARE→confirmação→ACT (§6.140) intocada; testes de ceiling/confirmação/reclassificação ao vivo preservados.
- Nenhum write real, secret, deploy ou `MODEL_AUTHORED_FACTUAL_PROSE` liberado.
- Residual search no diff: sem termos provider/entity-específicos, sem novos mecanismos de discovery, sem mudanças fora do escopo (`git diff --check` limpo).

## 8. Residuais e limitações (para revisão independente)

1. **Falha do estágio de objetivo → gate inerte** (`declared=False`): decisão deliberada — não transformar indisponibilidade do modelo de objetivo em bloqueio silencioso de escritas. A escrita permanece na cadeia governada.
2. **Misclassificação do modelo** (`create_or_modify` declarado para pedido de orientação): o gate confia no objetivo validado; instrução v8 mitiga, mas não elimina — frequência em modelo real = `TEST_NOT_RUN`.
3. **Generalização real**: `TEST_NOT_RUN` — todos os resultados são com harness `FakeProposalModel` scripted; nenhum claim de comportamento de LLM real.
4. **Fixture OpenAPI**: superfície OpenAPI dedicada não existe no harness; `FakeProvider` é provider-neutro — cobertura estrutural apenas.
5. Demote adiciona ≤1 model call quando acionado; clarify/fail-closed adiciona 0.

## 9. Estado

`IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW`; `INDEPENDENT_REVIEW=PENDING`; nenhuma mudança de fase declarada. Histórico 04, alinhamento 05 e review 06 preservados.

NEXT = STOP → RETURN_TO_ARCHITECTURE_COORDINATION
