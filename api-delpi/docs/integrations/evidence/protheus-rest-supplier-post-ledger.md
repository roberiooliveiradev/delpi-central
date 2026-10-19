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

`PRODUCTION_DEPLOY=NOT_AUTHORIZED` · `LIVE_POST_HOMOLOGATION=PENDING`
