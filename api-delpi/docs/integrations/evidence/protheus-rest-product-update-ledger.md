# Ledger — PUT produto Protheus via `delpiproduto` (API DELPI)

| Campo | Valor |
|-------|--------|
| TASK | Superfície `PUT /integrations/protheus/products/{product_code}` — alteração de cadastro de produto (SB1) via rota upstream `delpiproduto` (`DLP04I01.PRW` → `MATA010`/`MSExecAuto` op 4) |
| Branch | `main` (working tree; sem commit/deploy) |
| `EXISTING_EQUIVALENT` | `YES` (OAuth/gateway/token/params/Core identity/tracker — padrão suppliers) |
| `REUSE_DECISION` | `EXTEND` |
| Chamado / aceite | revisão independente `delpi-verifier` — **sem autoaceite** |

## AC

| ID | Resultado |
|----|-----------|
| AC-01 operationId estável `update_protheus_product` | PASS |
| AC-02 identidade só via Core (`codusr` backend) | PASS |
| AC-03 unmapped/não verified bloqueados | PASS (testes) |
| AC-04 permissão própria `api-delpi.integrations.protheus.products.update` | PASS |
| AC-05 contrato full-representation (21 campos `B1_*` + `B1_COD` do path) | PASS — ver "Contrato upstream" |
| AC-06 `B1_COD`/`codusr`/unknown/null rejeitados | PASS (testes) |
| AC-07 erros normalizados; 4xx→REJECTED, 5xx/timeout→UNKNOWN | PASS |
| AC-08 sem retry automático pós-timeout | PASS |
| AC-09 feature gate `PROTHEUS_PRODUCT_UPDATE_ENABLED` default `false` | PASS |
| AC-10 zero escrita em produção | PASS (live — ver abaixo) |
| AC-11 testes automatizados | PASS (32 novos + 369 regressão `-k protheus`) |
| AC-12 `ROUTE_CONTRACTS` + completeness | PASS |
| AC-13 live write→verify→restore→verify em TST01 | **PASS (executado 2026-11-17)** |
| AC-14 ledger no banco com ator/codusr/ambiente | **PASS (rows abaixo)** |

## Contrato upstream (descoberto em live test)

O handler `delpiproduto` (`DLP04I01.PRW`) lê **todos** os 22 campos `B1_*` incondicionalmente e chama `VAL()` nos numéricos: um PUT parcial quebra com 400 (`expected C->U, function val`) e, se passasse, apagaria campos no execauto. Por isso a façade exige a **representação completa**: o cliente envia os 21 campos `B1_*` (exceto `B1_COD`, injetado do path pelo backend) e o body upstream é plano (`{"B1_COD": ..., "B1_DESC": ..., ...}`), sem `codusr` (o upstream não aceita — identidade fica no ledger local).

Campos exigidos: `B1_GRUPO`, `B1_DESC`, `B1_REFEREN`, `B1_REFCANT`, `B1_CODDES`, `B1_TIPO`, `B1_YHOHS`, `B1_POSIPI`, `B1_LOCPAD`, `B1_UM`, `B1_SEGUM`, `B1_TE`, `B1_TS`, `B1_PICMRET`, `B1_CONV`, `B1_TIPCONV`, `B1_TPMAT`, `B1_ESPECIE`, `B1_EX_NCM`, `B1_EX_NBM`, `B1_ORIGEM`.

Segundo achado live: `detailedMessage` upstream traz bytes não-UTF8 → `response.json()` falha; gateway corrigido para classificar qualquer 4xx como `PROTHEUS_PRODUCT_UPDATE_REJECTED` (determinístico), não erro indeterminado.

## Homologação live — 2026-11-17 (TST01, autorizada pelo usuário)

| Passo | Resultado | Evidência |
|-------|-----------|-----------|
| Runtime | `delpi-api-delpi` local: `AMBIENTE=2`, `EXPECTED_BASE_URL=http://192.168.1.233:8701/rest`, `PROTHEUS_PRODUCT_UPDATE_ENABLED=true` | `docker inspect` |
| Ator | UUID `3bfdd634-a3a5-41af-b6b3-607025c2bdf5` → `protheus_user_id=000311` (mapped+verified via Core) | resolução Core |
| Tentativa 1 (body parcial) | upstream **400** `Erro Log` / `expected C->U, function val` → ledger `74b81fa0-0ff5-4cdd-9548-8c5b983db0be` = `UNKNOWN` | ledger + response |
| Snapshot completo + `B1_DESC` alterada | **200** `{"code":"200","message":"OK","detailedMessage":"Registro integrado com sucesso!"}` | response upstream |
| Verify TST01 | `B1_DESC = 'PESO PARA TESTE 6KG - HML APIDELPI'` (persistiu) | SQL `DELPI_TST01.SB1010` |
| Verify produção | `B1_DESC = 'PESO PARA TESTE 6KG'` — **intocada** | SQL `DELPI.SB1010` |
| Restore via façade (full use case) | **200**, `operation_id=6e38bfc7-84eb-4dd5-b706-5e32c15c5f00`, `update_acknowledged=true`, `update_confirmed=false`, `persistence_proven=false` | response use case |
| Verify pós-restore | `B1_DESC = 'PESO PARA TESTE 6KG'` (TST e prod idênticos ao original) | SQL confirmado 2026-11-17 |

### Linhas do ledger (`plugins_hub.integration_tracking`)

```text
operation_id                           | resource | action | resource_key | status       | protheus_user_id | environment_key               | http_status | upstream_error_code    | created_at
6e38bfc7-84eb-4dd5-b706-5e32c15c5f00   | product  | update | 10450043     | ACKNOWLEDGED | 000311           | ambiente:2@192.168.1.233:8701 | 200         | (null)                 | 2026-11-17 18:23:40 -03
74b81fa0-0ff5-4cdd-9548-8c5b983db0be   | product  | update | 10450043     | UNKNOWN      | 000311           | ambiente:2@192.168.1.233:8701 | (null)      | PROTHEUS_UPSTREAM_ERROR| 2026-11-17 18:21:06 -03
```

### Eventos (`integration_operation_events`)

```text
6e38bfc7… | 1 operation_created   → CREATED      | 18:23:40.425
6e38bfc7… | 2 send_started        → SENDING      | 18:23:40.431
6e38bfc7… | 3 upstream_response   → ACKNOWLEDGED | 18:23:41.014
74b81fa0… | 1 operation_created   → CREATED      | 18:21:06.754
74b81fa0… | 2 send_started        → SENDING      | 18:21:06.896
74b81fa0… | 3 upstream_response   → UNKNOWN      | 18:21:07.421
```

A tentativa `74b81fa0…` ficou `UNKNOWN` corretamente sob o mapeamento anterior (400 com `detailedMessage` malformado não parseável → `UPSTREAM_ERROR`); o write foi de fato recusado pelo upstream. Com o mapeador corrigido, esse caso passa a `REJECTED`.

### Estado pós-teste (SQL read-back, 2026-11-17)

```text
DELPI_TST01.SB1010 B1_COD='10450043' → B1_DESC='PESO PARA TESTE 6KG'   (restaurado)
DELPI.SB1010      B1_COD='10450043' → B1_DESC='PESO PARA TESTE 6KG'   (produção intacta)
```

## Ambientes pinados

| Ambiente | `INTRANET_PARAMS_AMBIENTE` | `PROTHEUS_REST_EXPECTED_BASE_URL` | gate |
|---|---|---|---|
| dev/local | `2` | `http://192.168.1.233:8701/rest` | `true` no `.env` local (TST) |
| HML | `"2"` literal (deny-list) | `http://192.168.1.233:8701/rest` literal | `false` literal |
| prod | `1` | `http://192.168.1.231:8061` | `false` |

## Lacunas conhecidas

- Sem read-after-write canônico no fluxo: resposta é `ACKNOWLEDGED`, nunca `CONFIRMED` (`persistence_proven=false` declarado).
- Carimbo dentro do Protheus sai como conta de serviço (`delpiproduto` não recebe `codusr`); ator real fica no ledger local (`protheus_user_id`, `actor_subject`, payload request/outbound).
- ~~Sem teste automatizado dedicado a `_map_product_write_response`~~ — FECHADO: `tests/test_protheus_rest_gateway_product_update.py` (7 testes: 4xx com/sem detalhe→REJECTED, non-UTF8→REJECTED, 5xx→UPSTREAM_ERROR, 401→TOKEN_INVALID, timeout single-attempt, 2xx não declara persistência).
- HML ainda precisa de acesso ao banco de parâmetros (`INTRANET_DB_*`) e da permissão liberada a usuário de teste antes de ligar a gate.
