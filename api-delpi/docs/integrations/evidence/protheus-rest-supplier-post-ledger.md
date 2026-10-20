# Ledger — POST fornecedor Protheus (API DELPI)

| Campo | Valor |
|-------|--------|
| TASK | Implementação POST fornecedores Protheus via API DELPI |
| Branch | `feat/protheus-rest-supplier-post` |
| `EXISTING_EQUIVALENT` | `YES` (OAuth/gateway/token/params/Core identity) |
| `REUSE_DECISION` | `EXTEND` |
| Chamado / aceite | revisão independente — **sem autoaceite** |

## AC

| ID | Resultado |
|----|-----------|
| AC-01 operationId estável | PASS |
| AC-02 identidade só via Core | PASS |
| AC-03 unmapped/não verified bloqueados | PASS (testes) |
| AC-04 permissão create específica | PASS |
| AC-05 payload objeto `fornecedor` + `codusr` backend | PASS |
| AC-06 matriz REST→SA2 | PASS (doc) |
| AC-07 erros normalizados | PASS (testes) |
| AC-08 sem retry automático pós-timeout | PASS |
| AC-09 feature gate default off | PASS |
| AC-10 sem escrita real em produção | PASS (gate + sem deploy live) |
| AC-11 testes automatizados | PASS (55 testes Protheus create+regressão) |
| AC-12 docs/ledger | PASS |
| AC-13 main integration | PASS (`21a8fe185d` em `origin/main`) |
| AC-14 lacunas documentadas | PASS |

## Lacunas TO_INVENTORY

- Shape de sucesso POST / retorno `A2_COD`
- Idempotência nativa
- Equivalência formal `codusr` ≡ `SYS_USR.USR_ID`
- Obrigatoriedade efetiva MATA020

## Produção

`PRODUCTION_DEPLOY=PASS` (código do POST presente na imagem em execução; gate default) · `LIVE_POST_HOMOLOGATION=BLOCKED`

## Homologação operacional — 2026-10-20 (`srv-api`)

| Gate | Resultado |
|------|-----------|
| Código implantado | PASS — use case e `operationId=create_protheus_rest_supplier` presentes; `PROTHEUS_SUPPLIER_CREATE_ENABLED` ausente no env → `false` |
| Sem autenticação | PASS — HTTP 401, sem escrita |
| Usuário autenticado sem vínculo Core | PASS — HTTP 422 `PROTHEUS_IDENTITY_UNMAPPED`, sem escrita |
| Usuário mapped+verified com gate off | PASS — `PROTHEUS_SUPPLIER_CREATE_DISABLED` (503) antes de qualquer POST upstream |
| Ambiente de homologação dedicado | PENDING — alvo observado é o runtime de produção |
| Owner operacional / dados fiscais de teste / empresa-filial / reversão | PENDING — não fornecidos nesta execução |
| Equivalência `codusr` ≡ `SYS_USR.USR_ID` | TO_INVENTORY |
| POST real no Protheus | **não executado** (0 chamadas) |

**STOP:** gates obrigatórios de escrita real não comprovados. Feature gate de criação permanece desligado.

## PUT — implementação (sem live write)

| Item | Resultado |
|------|-----------|
| Código `update_protheus_rest_supplier` | implementado; gate `PROTHEUS_SUPPLIER_UPDATE_ENABLED` default `false` |
| Permissão | `api-delpi.integrations.protheus.suppliers.update` (manifest 1.0.3) |
| POST live | inalterado — homologação continua BLOCKED |
| PUT live | TEST_NOT_RUN / NOT_AUTHORIZED |

## Hardening — ordem do feature gate (2026-10-20)

`EXISTING_EQUIVALENT=YES` · `REUSE_DECISION=EXTEND`

A resolução de identidade no Core passou a ocorrer **somente** com o gate da operação aberto. Payload inválido continua precedendo o gate. Gate fechado não chama Core, parâmetros Intranet, OAuth nem Protheus. POST e PUT seguem independentes e default `false`. Escrita sem retry automático.

A sonda anterior «sem vínculo → HTTP 422 com gate fechado» fica `STALE_EVIDENCE` para o código desta entrega: com gate fechado a resposta passa a ser o erro do gate, sem consultar o Core. Equivalência `codusr` ≡ `SYS_USR.USR_ID` permanece `TO_INVENTORY`.

| Item | Resultado |
|------|-----------|
| POST gate antes do Core | PASS (teste) |
| PUT gate antes do Core | PASS (teste) |
| Suíte local | PASS — 63 testes (`pytest` create/update use case, rotas, gateway, payload, Core S2S, GET) |
| Live POST/PUT | não executado |
| Código na `main` | `a2933514a5` |
| Deploy desta revisão | PENDING — sem janela, responsável e rollback confirmados nesta execução |
