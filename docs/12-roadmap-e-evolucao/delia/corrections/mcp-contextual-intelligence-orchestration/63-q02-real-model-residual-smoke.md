# Q02 — smoke com LLM real dos resíduos A/B/C

**TASK:** `DELIA-C3-I04-REAL-MODEL-RESIDUAL-SMOKE-TESTS-01`  
**DATA:** 2026-10-20  
**MODE:** avaliação somente leitura. Nenhum código, prompt, orçamento ou runtime foi alterado por esta tarefa.

## Ambiente

```text
SOURCE_SHA=4d7f71423e67b4721ea376d50d6bd7feac1360dc
DEPLOYED_HOST_SHA=4d7f71423e67b4721ea376d50d6bd7feac1360dc
DEPLOYED_IMAGE_CREATED=2026-10-20T16:28:26Z
MODEL_ID=moonshotai/kimi-k3
MODEL_CONFIGURATION=openai_compatible openrouter timeout_seconds=30 max_output_tokens=2048 turn_budget_seconds=30
B2_SYMBOL=_selected_proven_differences PRESENT
HEADER_GATE=_typed_compare_outcome_content ABSENT
B1_SYMBOLS=classify_result_intent AND unique_structural_ticket_list_capability PRESENT
```

A imagem em execução no início da sessão ainda tinha o gate textual. Ela foi substituída às 16:28:26Z, antes de qualquer pergunta desta bateria. As seis perguntas rodaram na imagem nova, que já contém o rework B2. Identidade de teste oficial, comando `MESSAGE`, sem confirmação e sem ACT.

## Resultado

| Teste | Outcome | Latência | Chamadas de modelo logadas | Causa |
|---|---|---|---|---|
| T01 SIPOC | FAIL | 13981 ms | 1 admissão | BUDGET comprovado |
| T02 formatos | PASS | 18066 ms | 2 + resposta conversacional | limitação honesta |
| T03 hipóteses | PASS | 10857 ms | 1 + resposta conversacional | — |
| T04 comparação | PASS | 14210 ms | 1 + resposta conversacional | caminho conversacional |
| T05 paráfrase | PASS | 14723 ms | 5 | owner GROUNDED |
| T06 identificador | PARTIAL | 13440 ms | 4 | 404 apresentado como fonte indisponível |

`TESTS_EXECUTED=6`. `PASS=4`. `PARTIAL=1`. `FAIL=1`. `INCONCLUSIVE=0`. `BLOCKED=0`. `MATERIAL_ACT=0`.

## T01 — FAIL / BUDGET

Pergunta conceitual «O que é SIPOC?». HTTP 200. Admissão em 1957 ms decidiu `conversational`. A resposta chegou 12,0 s depois dessa decisão, com `limitations=turn_budget_limited` e o texto padrão de tempo esgotado. `grounding_status=NON_GROUNDED`. Nenhuma capability operacional foi selecionada e nenhum dado da DELPI foi inventado. A explicação não foi produzida. O orçamento global de 30 s não foi o limite que encerrou o turno: a latência total foi 14,0 s, alinhada ao teto conversacional de 12 s depois da admissão.

## T02 — PASS

«Quais formatos de dados estão disponíveis?» foi admitido como superfície operacional. `select_group` voltou `none` e a seleção ficou `not_applicable`. O catálogo declarado nesse runtime não publica formatos de dados. A resposta, em classe `HYPOTHESIS`, diz que não há lista verificada e não inventa formatos. Isso cumpre a limitação honesta. A classificação operacional inicial gastou duas propostas e não mudou o resultado.

## T03 — PASS

Três melhorias de separação, marcadas como hipotéticas e sem dados da operação. `epistemic_class=HYPOTHESIS`. Admissão conversacional. Nenhuma capability e nenhuma confirmação. Dentro do orçamento.

## T04 — PASS

Na mesma conversa, «Agora compare a primeira e a segunda.» A resposta compara slotting e ondas/zonas, não repete a lista e declara que a comparação é conceitual, sem dados da DELPI. Sem `turn_budget_limited`. A admissão permaneceu conversacional: o gate tipado de diferenças de Q02-C/B2 não entrou nesse turno. A comparação de hipóteses livres continua sendo prosa do modelo, não evidência de owner.

## T05 — PASS

Paráfrase que não copia o nome «Buscar produtos DELPI». Seleção `openapi:delpi` / `delpi.search_products`, classe READ. Argumento `description` preenchido, `missing=0`. Owner respondeu em 176 ms. Síntese `GROUNDED`, quatro registros cujo nome contém o termo consultado. Sem veto lexical e sem confirmação.

## T06 — PARTIAL / SYNTHESIS

Consulta READ com código sintético `ZZ-SMOKE-0000`. Seleção `delpi.get_product_summary`, argumento `code`. O owner respondeu HTTP 404 em 75 ms. A DÉLIA não transformou o código em registro existente e não abriu escrita. O texto ao usuário, porém, classifica o caso como `SOURCE_UNAVAILABLE` / `delpi_source_unverified` e pede para tentar de novo. O trace mostra ausência do item, não falha transitória da fonte.

## Resíduos

Um defeito material, reproduzido: explicação conceitual encerra no teto conversacional de 12 s. Não há, nesta amostra, motivo para aumentar o orçamento. O menor passo é a coordenação decidir se esse teto continua aceitável antes de Q03.

Um defeito menor, reproduzido: 404 de READ vira texto de fonte indisponível. O menor passo é apresentar ausência comprovada pelo owner como insuficiência de registro, se a coordenação quiser essa distinção. Não é um validador de domínio novo.

Não exercido ao vivo: o sinal tipado de comparação de dois registros de owner. T04 não precisou dele. B1 não foi alterado e não apareceu nesta bateria.

`Q03_AUTHORIZED=NO`. `I04_ACCEPTED=NO`. `Q02_C_REWORK_REMAINING=0`.
