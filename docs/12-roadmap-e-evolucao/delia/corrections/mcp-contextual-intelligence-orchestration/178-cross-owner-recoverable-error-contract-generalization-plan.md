# 178 — DÉLIA · Generalização governada de contratos de erros entre owners

**Status:** ARCHITECTURE/IMPLEMENTATION_PLAN — OWNER_CONTRACTS_TO_INVENTORY; IMPLEMENTATION_NOT_EXECUTED; DEPLOY_NOT_AUTHORIZED. **Data:** 2026-10-28. **Base HEAD:** 68856d87129081783c47ff855cb3e5359d93c693. Direção: docs 170, 175–177; revisão independente do doc 177; segurança doc 174. Antes de implementação reancorar HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura, Product Spec, temática e ledger; conflito STOP/ARCHITECTURE_DECISION_REQUIRED.

## 1. Decisão de abordagem

**Generalizar o contrato, não o comportamento de negócio.** Definir uma semântica interoperável para erros READ com owner como autoridade. DÉLIA permanece provider-neutral e fail-closed, sem redesenhar planner nem replicar Domain APIs. OpenAPI HTTP, MCP e A2A podem projetar o mesmo **significado canônico** usando adapters legítimos já existentes, mas seus envelopes de transporte NÃO são iguais. Reuse-before-design para cada owner/consumer; não propagar alteração global sem contrato aprovado.

## 2. Inventário inicial comprovado

- `api-delpi/app/core/responses.py` já oferece `error_response(message,status_code,code=None,recoverable=True,fields=None,meta=None)`; **quando code é None, error fica null e recoverable não é emitido**. Isto explica por que o caso product_type não pode ser tratado como reparável pelo adapter seguro do doc 177. O default `recoverable=True` com `code` também exige uso explícito/sensato pelos callers: não é autorização universal do LLM.
- `delia-api/app/infrastructure/openapi/http_invoker.py` faz classificador fail-closed de 400/422; `VALIDATION_ERROR` é código genérico citado em alguns owners, não prova universal de READ argument repairability.
- Demais owner surfaces (Domain API, MCP, A2A e serviços externos): **TO_INVENTORY**. Não inventar que todos têm este helper ou aceitam o mesmo envelope.

## 3. Matriz canônica proposta para READ argument rejection

| Condição do owner | Classificação no adapter | Recuperação semântica |
|---|---|---|
| Erro de argumento tipado + `recoverable:true` explicitamente válido no contrato | `OWNER_ARGUMENT_REJECTED` | Uma tentativa governada possível, sujeito a Policy/budget |
| Erro com código específico formalmente declarado como argument-repairable | Contrato tipado equivalente | Somente se owner confirmar a semântica e o escopo READ |
| `recoverable:false`, erro sem anotação, código genérico ambíguo, resposta inválida | Terminal | Nenhuma tentativa por inferência |
| 401/403/Policy/Decision denied | Denial | Nunca contornar por outra capability |
| 429/5xx/timeout | Erro operacional | Retry técnico existente; nunca autorização semântica implícita |
| WRITE/PREPARE/ACT | Gates próprios | Nunca converter automaticamente em READ-retry |

Mensagem do owner é UNTRUSTED DATA; sanitize, projeção tipada, sem dados sensíveis. Campos/rules do domínio permanecem no owner. `fields` pode oferecer constraints no contrato quando legítimo, mas não é instrução do owner para o LLM.

## 4. Plano fechado de implementação transversal

**WP0 — Inventário de owners e consumers:** listar todas capabilities ativas via superfícies reais, contratos OpenAPI/MCP/A2A, callers de `error_response`, status/códigos, histórico de 400/422 e caminhos de adapter DÉLIA. Para cada um: `OWNER`, `CANONICAL_SOURCE`, `CONTRACT`, `CONSUMERS`, `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, `READ|WRITE`. Ausência em busca não prova inexistência.

**WP1 — API DELPI owner contract:** incluir anotação explícita nas **rejeições demonstradamente reparáveis de argumento READ** em chamadas como product search, sem alterar códigos de regra empresarial, AuthZ, schemas de entrada, ranking ou status indevidamente. Preferir `error_response(..., code=<owner-approved typed-code>, recoverable=True, fields=...)`; para erros não recuperáveis declarar false. Se código `VALIDATION_ERROR` cobrir erros terminais, não allowlistar o código genericamente; usar flag explícita ou código especializado legitimamente aprovado. Aprovação do Domain owner antes de mudança.

**WP2 — Outros owners:** aplicar somente a owners com contrato equivalente e owner ratificado; quando MCP/A2A ou fornecedor externo não puder declarar reparabilidade, adaptar somente a projeção de erros contratualmente explícitos e manter terminal o desconhecido. Não editar serviços externos por conveniência. Nenhum branch por provider no planner.

**WP3 — DÉLIA adapter/generalização:** revisar allowlist genérica `VALIDATION_ERROR` para não tratar erro terminal como reparável. Reusar `HttpOpenApiInvoker` e `CapabilityProviderError`; projetar significado canonical no adapter existente, sem outro registry/engine; toda recuperação governada mantém validação, live AuthZ, dedup, deadline, prover de resultados e final Outcome.

**WP4 — Testes RED/GREEN e compatibilidade:** matriz negativa/positiva por owner e protocolo, campo opcional, product_type, recuperação real, não recuperável com code válido, 403, 429/500, metadata maliciosa, idempotência, schema, paginacao. Teste em contrato existente primeiro. Regressão completa dos owners alterados e DÉLIA. Revisão de backward compatibility, OpenAPI/operationId, status, security, audit, rollback. Nenhum `PASS` sem postcondition.

**WP5 — E2E e promoção:** congelar corpus diverso com várias Domain APIs e MCPs, compare B0/B1 mesma versão de modelo, contratos, owner data, budgets; indicadores first-pass Business Outcome, falsos positivos, recuperabilidade útil, 400 evitáveis, tokens/latência, incidentes de segurança. Owner-by-owner gated rollout, rollback e independent review; deploy somente com owners explicitamente aprovados e liberação do security gate (doc 174). Alterações sem contrato aprovado permanecem `PENDING`, não precisam bloquear owners independentes.

## 5. Arquivos candidatos, não escopo inventado

- `api-delpi/app/core/responses.py` — helper já existente; alteração apenas se seu contrato precisar ser tornado mais explícito/compatível.
- Rotas que chamam `error_response` (product route citada no doc 177, caminho físico a localizar); mudanças específicas de declaração de contrato, não semântica de busca.
- `delia-api/app/infrastructure/openapi/http_invoker.py` — validação e tradução estrita dos erros declarados.
- Adapters MCP/A2A existentes — **TO_INVENTORY**; não editar sem owner contract.
- `delia-api/app/application/capability_provision/contracts.py` e `orchestration.py` — manter arquitetura e recuperação existentes; alterar apenas se prova de incompatibilidade.
- Testes das APIs, OpenAPI/integration/adapter, testes de segurança e harnesses já existentes.
- Doc temático seguinte e Execution Ledger após factual execution.

## 6. Gates e decisões

**G0 INVENTORY_CONFIRMED:** owner/contract/consumer/authorization reais. **G1 CONTRACT_APPROVED:** Domain owner aprova code/recoverable sem default perigoso. **G2 TESTED:** RED/GREEN + owner/API e DÉLIA regressions, negatives, no bypass. **G3 OUTCOME:** ganho/correção demonstrada em E2E com provedor real quando autorizado. **G4 SECURITY:** credential exposure owner decision (doc 174), audit e deploy gates válidos. Falha = owner-local `BLOCKED`, sem rollback de outro owner sem evidência. Não declarar alteração produtiva pela criação deste plano.

## 7. Resultado esperado

Uma única task multiowner bounded com matriz de owners e contratos, diffs mínimos apenas em owners autorizados, tests/rollback independentes por owner e relatório consolidado. Nenhuma tabela de palavras-chave ou motor de recuperação novo. Documento de plano: `PLANNED`, código não alterado, phase não avançada, deploy não autorizado.
