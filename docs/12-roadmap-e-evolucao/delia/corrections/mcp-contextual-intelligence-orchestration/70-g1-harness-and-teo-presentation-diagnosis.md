# Diagnóstico — G1 e apresentação TÉO

**TASK:** `DELIA-C3-I04-G1-HARNESS-AND-TEO-PRESENTATION-DIAGNOSIS-01`  
**DATA:** 2026-10-20  
**CÓDIGO:** vigente em `13ba8e71a7`, sem diff de runtime.

```text
G1_EXISTING_EQUIVALENT=PARTIAL
G1_REUSE_DECISION=EXTEND_AFTER_AUTHORIZATION
G1_SAFE_EVALUATION_PATH=IN_PROCESS_FAKE_PROVIDER_PLUS_REAL_MODEL
G1_CONTRACT_GAPS=NO_REAL_MODEL_BINDING_AND_NO_CATALOG_OVERRIDE

K1_TRUNCATION_STAGE=DETERMINISTIC_GUIDANCE_RENDER_2000
K1_ROOT_CAUSE=PROJECTION_CAP_AFTER_SECTION_JOIN
K2_INCOMPLETE_STAGE=PRIOR_EXCERPT_SPLIT_AND_SYNTHESIS_SELECTION
K2_ROOT_CAUSE=CONTINUATION_PARSES_TRUNCATED_PROSE

MINIMUM_CORRECTION_IF_PROVEN=REUSE_STRUCTURED_GUIDANCE_RECORDS
CODE_CHANGED=NO
I04_ACCEPTED=NO
NEXT_COORDINATION_DECISION=AUTHORIZE_ISOLATED_REAL_MODEL_G1_OR_KEEP_TEST_NOT_RUN
```

## G1

O teste `test_renamed_methodology_provider_same_selection_semantics` já isola um provider falso. O catálogo perturbado troca `get_methodology_guide` por `opaque_method_v9` e não chama MCP de produção. O modelo desse teste é `FakeProposalModel`: a proposta já contém o nome renomeado. Isso prova que o orquestrador obedece a seleção recebida. Não prova que `moonshotai/kimi-k3` escolhe o sibling pelo sentido.

Não há script que ligue o adapter real do LLM a essa superfície. O `POST /interaction/turns` do processo em execução usa o catálogo de produção. Não existe override de catálogo nesse contrato.

O menor teste, se for autorizado depois, reutiliza `_methodology_surface`: o mesmo pedido e o mesmo `InvokeModel` com `kimi-k3`, uma vez com o nome original e outra com o nome opaco e a mesma descrição. Comparar a capability selecionada e se o READ devolve o guia. Os providers de produção ficam de fora. Isso é extensão do teste existente, não um harness novo, e esta tarefa não a implementa.

## K1

A invocação `teo.get_methodology_guide` terminou em 41 ms com `decision=ok`. O turno acabou em 21894 ms, dentro dos 30 s. Não houve chamada de síntese. O texto visível tem 2032 caracteres e termina com `…(resultado parcial — truncado)`.

Esse sufixo é gravado por `_deterministic_guidance_content` quando o corpo projetado passa de `MAX_RENDER_CONTENT_CHARS` (2000). Cada seção já pode ter até 1920 caracteres (`MAX_DESCRIPTION_CHARS * 8`). O corte que o usuário viu é essa projeção, não o timeout do turno e não o teto de tokens da resposta do modelo. O payload bruto do owner não foi capturado; o que se prova é que a resposta publicada foi cortada neste estágio.

## K2

Não houve segunda invocação do TÉO. O log tem `turn_goal` e `grounded_synthesis`. A limitação é `prior_turn_evidence_only`.

`_prior_result_content` usa o texto já publicado, de novo limitado a 2000 caracteres. `_prior_excerpt_records` separa linhas de lista, e o texto que vem depois do item, como o cabeçalho `steps:`, permanece no mesmo trecho. A síntese selecionou dois trechos. `_detail_lines` coloca outro `-` na frente, o que produz `- -`. A resposta curta é essa seleção sobre a prosa já truncada, não uma perda no owner nem um estouro de prazo: a síntese terminou em 4004 ms.

Os registros de seção já existem em `_guidance_section_records`. K2 não os usa. Reaproveitá-los evitaria um parser de domínio novo. A correção mínima, se a coordenação autorizar, é essa reutilização. Não foi feita aqui.
