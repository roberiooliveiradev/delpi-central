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
- ~~Carimbo dentro do Protheus sai como conta de serviço (`delpiproduto` não recebe `codusr`); ator real fica no ledger local~~ — **FECHADO 2026-11-19**: `codusr` viaja no body upstream (meta-campo fora do catálogo) e o build `dlp-v056-m283-codusr` grava `AIF_ZCDUSR` pós-commit MATA010. Prova live TST01: PUT `10100057` com `"codusr":"000461"` → linha `AIF010` `15:21` (`AIF_CODPRO=10100057`, campo `B1_DESC`) com `AIF_ZCDUSR='000461'`. Bug corrigido no caminho: janela `AIF_HORA` exige `Left(Time(),5)` (`AIF_HORA` é `HH:MM`, `Time()` traz segundos). Verifier r3 `ACCEPT_WITH_RESIDUAL`.
- ~~Sem teste automatizado dedicado a `_map_product_write_response`~~ — FECHADO: `tests/test_protheus_rest_gateway_product_update.py` (7 testes: 4xx com/sem detalhe→REJECTED, non-UTF8→REJECTED, 5xx→UPSTREAM_ERROR, 401→TOKEN_INVALID, timeout single-attempt, 2xx não declara persistência).
- ~~HML precisa de `INTRANET_DB_*` e gate~~ — PROVISIONADO 2026-11-17: `.env.hml` no checkout `~/projetos-teste/delpi-central` com `INTRANET_DB_*` reais + `PROTHEUS_PRODUCT_UPDATE_ENABLED=true`; `delpi-hml-api-delpi` healthy, rota live no OpenAPI, params resolvendo `URL_REST=http://192.168.1.233:8701/rest` (TST01). Pendente só: permissão `api-delpi.integrations.protheus.products.update` para usuário de teste.

## Homologação live — 2026-11-19 (TST01, autorizada pelo usuário) — reparo de combo legado

Contexto: PUT `10080025` (MP) rejeitado `FWNOLIST` em `B1_YVLPC='N'` — SX3 combo hoje exige `1=Sim;2=Não`, mas ~55k produtos têm literal legado `S`/`N`. O ExecAuto revalida TODO campo da representação completa → round-trip impossível.

Fix implementado (api-delpi, sem recompile): `repair_legacy_combo_values()` + `get_x3_combo_map()` — traduz literal Sim/Não para a ÚNICA chave de rótulo equivalente do combo X3, só quando inequívoco; o restante segue p/ validação oficial. Auditado em `legacy_combo_repairs` + `outbound_payload` + log.

| Passo | Resultado | Evidência |
|-------|-----------|-----------|
| UPDATE `10080025` (MP, c/ reparo) | `B1_YVLPC` enviado como `'2'` no outbound; ainda **REJECTED** — mas por `U_A010TOK` (PE PosVld): `RetCodUsr()` (conta técnica REST) ∉ `MV_ZUSMPLB` (`000105;000294;000159;000166;000102;000008;000210;000406`). Bloqueio oficial correto de matéria-prima — decisão de inclusão da conta técnica é do time TOTVS | `error_details` ledger + `detailedMessage` `VLDDATA_POST` + fonte `A010TOK.prw` |
| UPDATE `70010015` (MC, `B1_CONTA=''`) | **REJECTED** `VLDDATA_OBRIGAT` — `B1_CONTA` obrigatória | `detailedMessage` direto do REST |
| UPDATE `60330049` (MC) `B1_DESC` → `'MULTIMETRO DIGITAL - E2E DELPI'` | **200 CONFIRMED** — `confirmation=CONFIRMED`, `legacy_combo_repairs={B1_YVLPC: S→1}` (este produto gravava `'S'`) | response + `outbound_payload` `B1_YVLPC='1'` |
| Read-back SQL TST01 | `B1_DESC='MULTIMETRO DIGITAL - E2E DELPI'`, `B1_YVLPC='1'` (valor canônico persistido — semântica preservada) | SQL `SB1010` |
| Restore via façade | **200 CONFIRMED** — `B1_DESC='MULTIMETRO DIGITAL'` restaurado | response + SQL |
| CREATE `TSTE2E001` (MC, 7 campos) | **REJECTED** `VLDDATA_OBRIGAT` `B1_COD` — modelo Delpi exige ~273 campos OBRIGAT; include "mínimo" não passa | `detailedMessage` |
| CREATE replay c/ 283 campos | **REJECTED** `FWRULES` — "Regra de dependencia nao respeitada (Forn. Canal / B1_PROC)", origem `B1_MONO`. `B1_MONO`∈{`S`,`N`,`''`} × `B1_PROC='000011'` × `B1_LOJPROC='01'` → mesma rejeição. Regra custom do modelo não decodificada (não está em `MATA010M_DLP` nem SX3/SX7) — aguarda `console.log` do serviço REST | `detailedMessage` direto |

### Linhas do ledger (`plugins_hub.integration_tracking`)

```text
825f3856-… | update | 10080025 | REJECTED     | 000000 | ambiente:2@192.168.1.233:8701 | 400 | PROTHEUS_PRODUCT_UPDATE_REJECTED
911acb53-… | update | 10080025 | REJECTED     | 000000 | (idem, pós-reparo — FWRULES U_A010TOK)
d9411f30-… | update | 70010015 | REJECTED     | 000000 | OBRIGAT B1_CONTA
1a9e66bc-… | update | 60330049 | ACKNOWLEDGED | 000000 | 200 — CONFIRMED c/ reparo S→1
26daf41f-… | update | 60330049 | ACKNOWLEDGED | 000000 | 200 — restore CONFIRMED
5e95afc7-… | create | TSTE2E001| REJECTED     | 000000 | OBRIGAT/FWRULES cadeia
```

### Estado pós-teste (SQL read-back, 2026-11-19)

```text
DELPI_TST01.SB1010 B1_COD='60330049' → B1_DESC='MULTIMETRO DIGITAL'  (restaurado)
                                    B1_YVLPC='1'                   (reparo persistido — era 'S', semântica idêntica)
DELPI_TST01.SB1010 B1_COD='TSTE2E001'→ inexistente                  (create rejeitado, nada gravado)
```

### Lacunas atualizadas 2026-11-19

- **MP bloqueado por regra oficial** (`U_A010TOK`+`MV_ZUSMPLB`): fluxo real de matéria-prima exige conta técnica REST no parâmetro OU mudança do PE — decisão PO/TOTVS, não de código.
- **CREATE ainda não provado em TST01**: OBRIGAT ~273 campos (include precisa de representação quase completa — contrato atual envia só campos informados) + dependência custom `B1_MONO→B1_PROC` opaca sem `console.log`. Opções: ficha completa no PRC, merge c/ defaults SX3, ou template por tipo de produto.
- `confirmation=CONFIRMED` já existe no read-back do use case; `update_confirmed`/`persistence_proven` upstream seguem `false` honestamente (são flags do envelope Protheus, não da nossa verificação).
