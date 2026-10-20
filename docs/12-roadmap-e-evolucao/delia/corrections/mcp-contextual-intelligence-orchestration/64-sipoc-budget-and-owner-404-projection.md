# Correção pontual pós-smoke — SIPOC e HTTP 404

**TASK:** `DELIA-C3-I04-REAL-MODEL-TARGETED-RESIDUAL-REMEDIATION-01`  
**DATA:** 2026-10-20  
**BASE:** `80ac8b6c7fd6db4422e6518aea6d877484506cdd`

## R1 — SIPOC

**Causa comprovada.** A admissão conversacional devolve `NOT_APPLICABLE` depois de uma proposta (~2 s) e não consulta owner. O handler aplica `CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS=12` a todo `NOT_APPLICABLE`, inclusive a esse atalho. A resposta conceitual recebe no máximo 12 s, mesmo quando o `TurnDeadline` global de 30 s ainda tem saldo. O teto existe desde G0-02 para o fallback não virar HTTP 504. Não há etapa redundante cuja remoção faça a explicação caber em 12 s: a admissão só classifica; a resposta é a segunda chamada, e ela é interrompida pelo teto.

**Smoke S01** no runtime `80ac8b6c7`, modelo `moonshotai/kimi-k3`, 2026-10-20T16:43:48Z. HTTP 200. Latência 14167 ms. Uma proposta de admissão em 2149 ms, decisão `conversational`. Limitação `turn_budget_limited`. `grounding_status=NON_GROUNDED`. Sem capability e sem confirmação. Outcome `FAIL`.

**Mudança de código:** nenhuma. Aumentar o teto de 12 s, ou deixar essa resposta usar o saldo dos 30 s, muda a decisão congelada do G0-02.

**Proposta contratual, não executada:** aplicar os 12 s só ao `NOT_APPLICABLE` que chega depois de seleção de owner, e deixar a resposta da admissão conversacional antecipada sob `TurnDeadline.stage_timeout` do orçamento global, sem passar de 30 s. Alternativa equivalente: autorizar explicitamente um teto maior só para essa resposta. As duas exigem decisão da coordenação. Q03 não fica autorizado por esta proposta.

## R2 — HTTP 404

**Contrato do owner.** `get_product_summary` responde 404 somente por `not_found_response`: `success=false`, `error.code` preenchido, `error.recoverable=false`, mensagem do owner. Exceção no handler dessa rota cai em `error_response` (HTTP 400). 401 e 403 já são acesso negado. Um 404 sem esse envelope continua falha de invocação.

**Mudança.** O invoker OpenAPI reconhece só esse envelope em HTTP 404 e emite `owner_record_not_found` com a mensagem do owner. A projeção deixa de pedir nova tentativa e deixa de usar `delpi_source_unverified`. O texto diz que não há registro e reproduz a frase da fonte. 404 sem envelope, 404 recuperável e o mesmo envelope em HTTP 500 permanecem `openapi_invocation_failed`.

**Smoke S02 ao vivo:** `TEST_NOT_RUN`. O runtime em execução não contém o código novo (`OWNER_RECORD_NOT_FOUND` ausente) e não houve autorização para deploy. A distinção está nos testes de invoker e de apresentação.

## Testes

Focados: `test_openapi_capability_provider.py`, `test_interaction_presentation.py`, `test_execution_ceiling_turn_budget.py` — PASS.  
Suíte `delia-api`: 1678 passed, 0 failed.  
Orçamentos 30 s e 12 s inalterados. B1, gate tipado de comparação e selection-only inalterados. `MATERIAL_ACT=0`. `Q03_AUTHORIZED=NO`.
