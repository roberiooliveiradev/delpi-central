# Correção pontual pós-smoke — SIPOC e HTTP 404

**TASK:** `DELIA-C3-I04-REAL-MODEL-TARGETED-RESIDUAL-REMEDIATION-01`  
**DATA:** 2026-10-20  
**BASE:** `80ac8b6c7fd6db4422e6518aea6d877484506cdd`

## R1 — SIPOC

**Causa comprovada.** A admissão conversacional devolve `NOT_APPLICABLE` depois de uma proposta (~2 s) e não consulta owner. O handler aplica `CONVERSATIONAL_FALLBACK_STAGE_CAP_SECONDS=12` a todo `NOT_APPLICABLE`, inclusive a esse atalho. A resposta conceitual recebe no máximo 12 s, mesmo quando o `TurnDeadline` global de 30 s ainda tem saldo. O teto existe desde G0-02 para o fallback não virar HTTP 504. Não há etapa redundante cuja remoção faça a explicação caber em 12 s: a admissão só classifica; a resposta é a segunda chamada, e ela é interrompida pelo teto.

**Smoke S01** no runtime `80ac8b6c7`, modelo `moonshotai/kimi-k3`, 2026-10-20T16:43:48Z. HTTP 200. Latência 14167 ms. Uma proposta de admissão em 2149 ms, decisão `conversational`. Limitação `turn_budget_limited`. `grounding_status=NON_GROUNDED`. Sem capability e sem confirmação. Outcome `FAIL`.

**Mudança de código:** nenhuma. Aumentar o teto de 12 s, ou deixar essa resposta usar o saldo dos 30 s, muda a decisão congelada do G0-02.

**Proposta contratual, registrada em 2026-10-20 e depois autorizada:** aplicar os 12 s só ao `NOT_APPLICABLE` que chega depois de seleção de owner, e deixar a resposta da admissão conversacional antecipada sob `TurnDeadline.stage_timeout` do orçamento global, sem passar de 30 s. O Product Master autorizou exatamente essa distinção na task `DELIA-C3-I04-CONVERSATIONAL-BUDGET-AND-MODEL-CONTINUATION-01`. A execução está na seção seguinte. Q03 continua sem autorização.

## R2 — HTTP 404

**Contrato do owner.** `get_product_summary` responde 404 somente por `not_found_response`: `success=false`, `error.code` preenchido, `error.recoverable=false`, mensagem do owner. Exceção no handler dessa rota cai em `error_response` (HTTP 400). 401 e 403 já são acesso negado. Um 404 sem esse envelope continua falha de invocação.

**Mudança.** O invoker OpenAPI reconhece só esse envelope em HTTP 404 e emite `owner_record_not_found` com a mensagem do owner. A projeção deixa de pedir nova tentativa e deixa de usar `delpi_source_unverified`. O texto diz que não há registro e reproduz a frase da fonte. 404 sem envelope, 404 recuperável e o mesmo envelope em HTTP 500 permanecem `openapi_invocation_failed`.

**Smoke S02 ao vivo:** `TEST_NOT_RUN`. O runtime em execução não contém o código novo (`OWNER_RECORD_NOT_FOUND` ausente) e não houve autorização para deploy. A distinção está nos testes de invoker e de apresentação.

## Testes

Focados: `test_openapi_capability_provider.py`, `test_interaction_presentation.py`, `test_execution_ceiling_turn_budget.py` — PASS.  
Suíte `delia-api`: 1678 passed, 0 failed.  
Orçamentos 30 s e 12 s inalterados. B1, gate tipado de comparação e selection-only inalterados. `MATERIAL_ACT=0`. `Q03_AUTHORIZED=NO`.

## Orçamento conversacional — decisão executada

O Product Master autorizou a distinção. O retorno da admissão conversacional antecipada passa a levar `admission_outcome=early_conversational_admission`. Só esse marcador dispensa o teto de 12 s. O handler então usa o saldo de `TurnDeadline`. `NOT_APPLICABLE` sem o marcador, inclusive seleção posterior com `applicable=false`, continua limitado a 12 s. Erro de owner e confirmação não chamam o modelo livre. Timeout continua no soft-land, sem inventar dado. Os números 12 e 30 não mudam.

Smoke «O que é SIPOC?» neste runtime: `TEST_NOT_RUN`. Não houve autorização de deploy.

Suíte após o diff: `delia-api` 1685 passed, 0 failed.

## Continuidade entre chamadas — inventário, sem implementação

```text
EXISTING_EQUIVALENT=YES
REUSE_DECISION=EXTEND
AUTOMATIC_RETRY_IMPLEMENTED=NO
```

O que já existe:

- `prior_turns` atravessa turnos do usuário como contexto não autoritativo. Não é fato e não autoriza owner.
- `TurnDeadline` é único no turno. Cada estágio recebe `min(teto do estágio, saldo)`. Nenhuma tentativa zera o relógio.
- Propostas tipadas são consumidas no estágio que as pediu. Não há depósito de proposta parcial para uma segunda chamada.
- Evidência de owner bem-sucedida entra uma vez na síntese selection-only. Timeout do modelo descarta o corpo: o adapter levanta `TIMEOUT` e não devolve texto parcial.
- Chamadas no mesmo turno já são sequenciais (admissão, seleção, argumentos, síntese), cada uma com o mesmo deadline.

Distinção:

1. Chamada concluída com resultado parcial aproveitável: não há contrato. `finish_status` só aparece em conclusão.
2. Chamada interrompida sem resultado: timeout atual. Soft-land conversacional ou erro governado. Nada a reaproveitar.
3. Continuidade entre turnos: `prior_turns` já faz isso, sem promover o texto a fato.
4. Continuação dentro do turno: estágios seguintes reutilizam o deadline e, quando houve owner, a evidência já obtida. Não há segunda tentativa da mesma chamada.

Proposta para decisão posterior, não executada: se um timeout conversacional ocorrer com saldo acima do mínimo viável, o adapter precisaria devolver um texto parcial delimitado, sem chain-of-thought. Uma única continuação usaria esse texto como hipótese não autoritativa, no mesmo `TurnDeadline`, sem nova listagem nem nova invocação de capability. Gatilho: timeout da resposta conversacional e saldo restante. Limite: uma continuação, sem reiniciar 30 s, sem ACT. Consumidor: o mesmo `_invoke`. Lacuna de contrato: `ModelInvocationError` não carrega parcial. Segurança: o parcial não vira fato, provenance nem autorização.
