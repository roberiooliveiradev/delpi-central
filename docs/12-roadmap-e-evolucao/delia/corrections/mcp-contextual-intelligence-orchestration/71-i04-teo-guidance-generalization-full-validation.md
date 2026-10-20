# I04 — correção K1/K2 e generalização G1 com modelo real isolado

**TASK:** `DELIA-C3-I04-TEO-GUIDANCE-GENERALIZATION-FULL-VALIDATION-01`  
**DATA:** 2026-10-20  
**BASE:** `2891f5f5f87268dcabf2e1cec40f5d7fd381383b`  
**MODELO:** `moonshotai/kimi-k3`, provider `openai_compatible`  
**AMBIENTE DO MODELO:** processo local, catálogo falso em memória. Nenhum MCP de produção foi chamado. Nenhum deploy.

```text
I04_EXECUTOR_STATUS=FUNCTIONAL_EVIDENCE_READY
I04_ACCEPTED=NO_PENDING_COORDINATION
C3_EXECUTED=NO
Q01_Q03=CLOSED_WITH_RESIDUAL
PRODUCTION_READINESS=NOT_PROVEN
GLOBAL_TURN_BUDGET_SECONDS=30
POST_ORCHESTRATION_FALLBACK_CAP_SECONDS=12
MAX_RENDER_CONTENT_CHARS=2000
AUTOMATIC_RETRIES=OFF
MATERIAL_ACT=0
```

Este relatório não aceita I04 nem C3.

## Contrato

Os registros de `_guidance_section_records` existem só dentro de uma tentativa. O contexto HTTP continua limitado a `kind`, `content` e `epistemic_class`. Um turno seguinte não recebe esses registros. Não foi criado campo novo, memória nem estado global.

A alteração de contrato que ficaria por fazer, e não foi feita, seria um eco não-FACT da lista de seções já admitida, devolvido pelo cliente no turno seguinte. A continuidade usa o texto publicado. Esse texto agora leva seções inteiras e, quando algo não cabe, o nome do que ficou de fora.

## K1

Causa: `_deterministic_guidance_content` juntava as seções e cortava o bloco em 2000 caracteres, acrescentando o sufixo de truncamento. O owner não era o defeito.

Mudança: `_pack_guidance_sections` inclui seções inteiras até o mesmo teto de 2000. O que não entra é nomeado. Uma seção maior que o teto ainda é cortada em quebra de linha e marcada como parcial. O teto não mudou. Não há parser de KPI.

Avaliação isolada, um pedido operacional, provider falso com guia longo:

```text
CASE_ID=K1
MODEL_ID=moonshotai/kimi-k3
OWNER=in_process_fake
CAPABILITY=get_methodology_guide
AUTHZ=NO_DENIAL
CONTRACT_VALID=YES
MODEL_CALL_COUNT=3
LATENCY_MS=5978
GROUNDING=OWNER_READ_THEN_DETERMINISTIC_PROJECTION
LIMITATIONS=
CONTENT_CHARS=1806
DESTRUCTIVE_SUFFIX=NO
QUESTIONS_PRESENT=YES
TASK_OUTCOME=PASS
FAILURE_OWNER=
REAL_PROVIDER_INVOKED=NO
```

O corpo de 1806 caracteres coube no teto, então a linha de omissão não apareceu. O caso em que seções sobram está no teste `test_long_guide_keeps_whole_sections_and_names_the_rest`.

Um pedido consultivo anterior, na mesma superfície, terminou `NOT_APPLICABLE` em 2214 ms, com uma chamada de modelo e sem invocação. Não foi repetido. O resultado acima usa o pedido operacional de leitura do guia.

## K2

Causa: a continuidade lia a prosa já cortada. O divisor de trechos grudava o cabeçalho `steps:` no item anterior. A lista de síntese prefixava `- ` em um valor que já era item de lista.

Mudança: cada item de lista é uma unidade. O cabeçalho seguinte fica de fora. A renderização em lista não acrescenta outro marcador quando o trecho já tem um. Não há segunda chamada de modelo só para reescrever. Não há reconsulta quando a evidência anterior basta.

Mesma conversa do K1 acima. O contador de chamadas é cumulativo no processo (3 no K1 e mais 3 no K2).

```text
CASE_ID=K2
MODEL_ID=moonshotai/kimi-k3
PRIOR_EVIDENCE_SOURCE=published_delia_result
PRIOR_EVIDENCE_AUTHORITY=NON_FACT
OWNER_REINVOKED=NO
MODEL_CALL_COUNT=3
LATENCY_MS=16586
EXTRACTION_COMPLETE=YES
DOUBLE_DASH=NO
ENDS_WITH_STEPS=NO
LIMITATIONS=prior_turn_evidence_only
TASK_OUTCOME=PASS
FAILURE_OWNER=
```

A primeira execução operacional, antes do ajuste do renderizador de lista, ainda mostrou `- -`. O ajuste foi feito e esta conversa foi executada uma vez em seguida. G1 não foi repetido.

## G1

O teste antigo com `FakeProposalModel` permanece. A extensão opt-in, `DELIA_I04_REAL_MODEL=1`, liga o adapter real à superfície `_methodology_surface`. O nome técnico muda. A descrição, a classe READ, o schema e o resultado funcional não mudam. O prompt não contém o nome esperado. Sem a variável, os dois testes são ignorados e a suíte não chama o modelo.

```text
CASE_ID=G1-A
CATALOG_ORIGINAL=get_methodology_guide
MODEL_SELECTED_CAPABILITY=get_methodology_guide
SCHEMA_VALID=YES
FAKE_PROVIDER_INVOKED=YES
REAL_PROVIDER_INVOKED=NO
MODEL_CALL_COUNT=3
LATENCY_MS=6787
CONTENT_CHARS=49
TASK_OUTCOME=PASS

CASE_ID=G1-B
CATALOG_RENAMED=opaque_method_v9
MODEL_SELECTED_CAPABILITY=opaque_method_v9
SCHEMA_VALID=YES
FAKE_PROVIDER_INVOKED=YES
REAL_PROVIDER_INVOKED=NO
MODEL_CALL_COUNT=3
LATENCY_MS=7505
CONTENT_CHARS=49
TASK_OUTCOME=PASS
```

`G1_GENERALIZATION_OUTCOME=PASS` na execução isolada única pretendida. Os dois catálogos selecionaram o guia pela descrição publicada, validaram o READ no provider falso e devolveram o texto do guia.

Uma segunda passagem aconteceu sem querer, porque a suíte completa herdou `DELIA_I04_REAL_MODEL=1` do processo anterior. Nos dois catálogos o resultado foi `NOT_APPLICABLE`, sem invocação. Não houve divisão entre o nome original e o nome opaco. Essa passagem não foi usada como nova tentativa até obter PASS e não substitui a execução acima.

Negativos no modelo falso, na mesma suíte: seleção inaplicável não invoca; capability ACT não é executada como READ. Histórico forjado, schema incompatível e metadata maliciosa já tinham testes irmãos e continuam na suíte.

## K3 e K4

A seleção e o discovery não foram alterados. A projeção de guia é compartilhada, então um payload no formato de orientação passa pelo mesmo empacotador. O guia VISTA observado no relatório 69 tinha 1050 caracteres e caberia inteiro. Os testes de guia aninhado e de discovery permaneceram na suíte. Não houve novo turno em produção: esta tarefa não autoriza deploy. A evidência ao vivo de K3 e K4 continua a do relatório 69, em SHA anterior.

```text
K3_REGRESSION=UNIT_GREEN_LIVE_NOT_RERUN
K4_REGRESSION=UNIT_GREEN_LIVE_NOT_RERUN
```

## Suíte

A contagem abaixo é a da suíte `delia-api` completa depois do diff, sem `DELIA_I04_REAL_MODEL`. Os três testes de modelo real ficam ignorados nesse modo. Eles foram executados à parte, uma vez, com o resultado das seções K1, K2 e G1.

```text
TESTS_COLLECTED=1696
TESTS_PASSED=1693
TESTS_FAILED=0
TESTS_SKIPPED=3
```
