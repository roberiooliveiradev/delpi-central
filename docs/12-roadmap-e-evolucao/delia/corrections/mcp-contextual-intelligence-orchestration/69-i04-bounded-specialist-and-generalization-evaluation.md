# I04 — avaliação bounded de especialistas

**TASK:** `DELIA-C3-I04-BOUNDED-SPECIALIST-AND-GENERALIZATION-EVALUATION-01`  
**DATA:** 2026-10-20  
**HOST:** `55983c3e0d54b166e1b0f3a89dffb84806dc2547`  
**PROCESSO:** `delpi-delia-api` iniciado em `2026-10-20T17:18:18Z`, imagem `sha256:a1fe196c994b`, marcador `early_conversational_admission` presente. `delia-api` inalterado desde `a9f5f8d3c2`.  
**MODELO:** `moonshotai/kimi-k3`, provider `openai_compatible`, orçamento 30 s.  
**SUJEITO:** identidade de teste já usada nesta trilha. MCPs DAVI, TÉO e VISTA habilitados. Nenhuma capability nova. Nenhum deploy. Nenhum retry.

G1 não rodou. Não existe mecanismo autorizado de catálogo perturbado com LLM real que deixe o provider de produção intacto. A suíte de fixture não conta como generalização ao vivo.

## K1 — TÉO — PARTIAL

Orientação metodológica, sem números da operação. HTTP 200 em 21894 ms. Admissão operacional. Seleção `mcp:teo` / `get_methodology_guide`, classe READ, depois de `get_catalog`. Invocação ok em 41 ms. `GROUNDED` / `OBSERVATION`. Limitação `result_truncated`. Sem confirmação.

O texto é o guia de desenho de KPI, com propósito, quando usar, perguntas, regras de evidência e seção de origem. A apresentação é o bloco estruturado do owner, cortado no fim. O README pede orientação útil e rastreável, não dump bruto. A capability e a rastreabilidade estão corretas; a forma não cumpre o critério inteiro.

```text
MODEL_CALLS=5 propostas ok + 2 invokes
FAILURE_OWNER=DELIA_PROJECTION
CONTRACT_VALID=YES
AUTHZ=NO_DENIAL
```

## K2 — TÉO — PARTIAL

Mesma conversa. Pedido para extrair as perguntas da orientação, sem repetir o guia. HTTP 200 em 15482 ms. A admissão estourou o estágio de 6 s e seguiu para o caminho de owner; não houve nova invocação de TÉO. Síntese com `prior_turn_evidence_only`. `NON_GROUNDED` / `HYPOTHESIS`.

A resposta recupera as duas perguntas do guia e termina cortada em `steps:`. Não repete o guia inteiro. A continuidade sem reconsulta está comprovada. A lista pedida não ficou utilizável.

```text
MODEL_CALLS=1 admissão em timeout + 2 propostas ok
FAILURE_OWNER=DELIA_SYNTHESIS
CONTRACT_VALID=NOT_APPLICABLE
AUTHZ=NO_OWNER_CALL
```

## K3 — VISTA — PASS

Critérios de formato de exibição, sem execução e sem playlist. HTTP 200 em 27967 ms. A admissão estourou 6 s e a seleção continuou. `mcp:vista` / `get_product_guide`: uma leitura de índice e uma leitura com `topic`. `GROUNDED` / `OBSERVATION`. Sem limitação de orçamento e sem confirmação.

O guia devolvido explica formato de exibição, quando usar, como aplicar e quando não usar. Declara cobertura parcial. Não afirma que uma playlist foi inspecionada nem que um formato foi aplicado.

```text
MODEL_CALLS=1 admissão em timeout + 4 propostas ok + 2 invokes
FAILURE_OWNER=NONE
CONTRACT_VALID=YES
AUTHZ=NO_DENIAL
```

## K4 — DAVI — PASS

Possibilidades de consulta de item, sem executar busca. HTTP 200 em 22486 ms. Admissão operacional. `mcp:davi` / `discover_delpi_information`, classe DISCOVERY, argumentos `query` e `top_k`, 180 ms. Não houve `execute_delpi_information`. `GROUNDED` / `OBSERVATION`.

A resposta diz que a busca semântica não achou uma ação correspondente, que a fonte declara 95 leituras elegíveis e que resultado vazio não prova ausência. Diz também que discovery não autoriza execução. Isso separa descoberta, ausência e execução. Não lista os tipos de consulta de produto; o índice do owner não devolveu candidato para esse enunciado, e a projeção não transformou isso em catálogo vazio.

```text
MODEL_CALLS=5 propostas ok + 1 invoke
FAILURE_OWNER=NONE
CONTRACT_VALID=YES
AUTHZ=NO_DENIAL
```

## G1 — TEST_NOT_RUN

Renomear sibling no catálogo de produção foi proibido. Não há harness autorizado com catálogo perturbado e modelo real.

## Fecho

```text
MATERIAL_ACT=0
READ_ONLY=YES
AUTOMATIC_RETRIES=OFF
CRITICAL_FAILURES=NONE
I04_ACCEPTED=NO
```

O conjunto TÉO/VISTA/DAVI deixou de ser lacuna total. O gate I04 continua sem o sibling renomeado e com K1/K2 aquém do critério de apresentação. Nenhuma correção foi feita durante a avaliação.
