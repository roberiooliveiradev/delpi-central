# Playbook — integração de escrita Minha DELPI → TOTVS Protheus REST

Guia passo a passo para **ampliar a integração** a novas entidades/rotas,
consolidando tudo que foi aprendido e provado nas implementações de
`suppliers` (create/update) e `products` (update). Siga este documento antes
de abrir qualquer nova superfície de escrita.

> Status das superfícies hoje:
> `POST suppliers` · `PUT suppliers/{id}` · `PUT products/{code}` —
> todas feature-gated, default `false`, homologadas em TST01.

---

## 1. Topologia e ambientes

| Peça | Endereço | Observação |
|---|---|---|
| SQL Server TOTVS | `192.168.1.230` | Bases `DELPI` (produção) e `DELPI_TST01` (teste) |
| REST Protheus **produção** | `http://192.168.1.231:8061` | rotas sob `/restall` |
| REST Protheus **teste (TST01)** | `http://192.168.1.233:8061` | rotas sob `/restall`; escreve em `DELPI_TST01`. Transição 2026-11-19: `:8701` (`/rest`, ambiente `api`) segue como REST alternativo de validação funcional |
| Arquivos/log do serviço REST | `192.168.1.232` | deployment Protheus; log lista classes publicadas |
| Tabela de parâmetros | `PARAMETROS_MINHADELPI` no banco Intranet (`INTRANET_DB_*`, default `IntranetDelpiDev`) | owner ERP/Intranet — nunca editar da api-delpi |

A linha `AMBIENTE` da tabela de parâmetros decide o destino:
`INTRANET_PARAMS_AMBIENTE=1` → produção · `=2` → TST01.

**Regra de ouro:** dev e HML vivem pinados a `AMBIENTE=2` +
`PROTHEUS_REST_EXPECTED_BASE_URL=http://192.168.1.233:8061`
(em HML, literais no compose — `env_file` não sobrescreve).
Produção: `AMBIENTE=1` + pin `http://192.168.1.231:8061`.
O pin é fail-closed: se os parâmetros resolverem URL diferente do esperado,
a escrita é bloqueada **antes** de qualquer byte sair.

## 2. O que existe upstream (descobrir antes de codar)

Duas famílias de portas no REST do Protheus:

1. **Rotas custom Delpi** (fontes `DLP*.PRW` no repositório/deploy):
   - `delpi/api/v1/suppliers` — fornecedor (POST/PUT; aceita `codusr`)
   - `delpiproduto/v1/IncProduto/{incluir,alterar}` — produto via `MATA010`/`MSExecAuto`
     (catálogo vivo 19/11: somente `POST_INCPROD`+`PUT_INCPROD`; sem `excluir`)
2. **APIs nativas TOTVS** — ~527 classes publicadas (confirmado via
   `/restall` autenticado com a conta de serviço): `CUSTOMERVENDOR` (CRUD
   cliente+fornecedor), `COSTCENTERS`, `BRANCHES`, `MRPPRODUCT`,
   `RETAILSALESORDERS`, `PURCHASEORDERAPPROVAL`, `RETAILSTOCK`, etc.
   Paths oficiais no catálogo de cada classe (`/restall/index/&lt;CLASSE&gt;`).

**Como mapear o que existe:**
- listagem autenticada: GET `{base}/restall` com credencial Protheus (ou a
  conta de serviço `USR_PROTHEUS` que a api-delpi já usa para OAuth);
- sem login: o **log do serviço** em `192.168.1.232` registra "method
  unimplemented on this URN" para classes existentes vs. silêncio para
  inexistentes;
- **não confie em 404 de path chutado** — a TOTVS usa paths que divergem do
  nome da classe.

### 2.1. Lição obrigatória: ler o fonte do handler antes de projetar o payload

O `delpiproduto` (`DLP04I01.PRW`) lê **todos** os campos `B1_*`
incondicionalmente e aplica `VAL()` nos numéricos: um PUT parcial quebra
(`expected C->U, function val`) e, se passasse, **apagaria campos** no
execauto. Por isso o contrato da façade é **representação completa**
(21 campos + `B1_COD` do path), não merge parcial.

- Antes de cada nova entidade: localizar o `.PRW` do handler (ou a doc da
  classe nativa) e listar **todos** os campos lidos + quais são `VAL()`-ed.
- Respostas upstream podem trazer bytes não-UTF8 em `detailedMessage` —
  `response.json()` falha. Todo 4xx é recusa determinística mesmo sem corpo
  parseável.

## 3. Identidade do ator (nunca do cliente)

```text
JWT Keycloak (Minha DELPI)
  → subject UUID do usuário
  → Core resolve protheus_user_id (exige mapping_status=mapped E verified=true, 6 dígitos)
  → codusr registrado no ledger (e enviado upstream SOMENTE se a rota aceitar)
```

- O cliente **nunca** envia `codusr`/`B1_COD`-equivalente de identidade;
  payloads que tentem são rejeitados (`422`).
- `delpiproduto` não aceita `codusr`: dentro do ERP o carimbo sai como
  "conta de serviço"; o ator real fica garantido no ledger local
  (`protheus_user_id`, `actor_subject`, payloads request/outbound + hashes).
- Rotas custom futuras devem aceitar `codusr` quando quisermos o carimbo
  nominal também dentro do Protheus (padrão já usado em suppliers).

## 4. Receita da superfície (camadas — copiar do padrão existente)

| Camada | Arquivo (padrão a espelhar) | Regras |
|---|---|---|
| Payload builder | `app/application/services/integrations/protheus_{entity}_payload.py` | allowlist de campos; rejeita identidade, unknown, `null`; `B1_COD` vem do path; erro `…_FULL_REPRESENTATION_REQUIRED` quando upstream exige ficha completa |
| URL upstream | resolver dentro do payload/service | derivar prefixo REST de `suppliers_path` resolvido; fail-closed se o marcador não existir; **nunca hardcodar host** |
| Gateway | `ProtheusRestGateway.update_{entity}` + `_map_{entity}_write_response` | **1 tentativa** (timeout é indeterminado — write pode ter chegado); 401→`PROTHEUS_TOKEN_INVALID`; 4xx→`…_REJECTED` (400); 5xx→`PROTHEUS_UPSTREAM_ERROR` (502); timeout→`PROTHEUS_TIMEOUT`; tolerar corpo não-JSON |
| Use case | `update_{entity}_use_case.py` | ordem fail-closed: **valida código → payload → GATE → identidade Core → params → pin destino → token → tracking CREATED→SENDING → 1 PUT → ACK** |
| Tracking | `ProtheusWriteTracker.begin(..., resource="…")` | novo `resource` por entidade; registrar `operation_id`, ator, codusr, payload, env key; ledger em `plugins_hub.integration_tracking` |
| Rota | `protheus_router.py` | `require_s2s_or_any_permission`; permissão própria `api-delpi.integrations.protheus.{entity}.{action}` (não herda read nem de outra entidade); envelope `api_delpi_success`/`error_response`; `operation_id` único |
| Registry | `route_contract_registry.py` | entrada `ROUTE_CONTRACTS[operation_id]` — senão o gate de completeness reprova |
| Permissão | `api_delpi_permissions.py` | constante da permissão |
| Gate | `config.py` + env examples | `PROTHEUS_{ENTITY}_{ACTION}_ENABLED=false` default em dev/hml/prod |
| Composição | `protheus_rest_composer.py` | wiring do use case |

### Ordem exata do use case (não reordenar)

1. validar `resource_key` (formato) — falha barata primeiro;
2. validar payload (identidade/unknown/null/missing) — 422 antes de I/O;
3. **gate** desligado → erro antes de Core/params/token;
4. resolver `codusr` via Core — attribution antes de decidir envio;
5. resolver parâmetros Protheus (Intranet) → `base_url`, `auth_path`, paths;
6. **pin de destino** (`assert_protheus_write_target`) — mismatch ⇒ aborta;
7. token OAuth (cache in-memory, fingerprint `user|auth_url|sha256(pwd)`);
8. `tracker.begin()` → `mark_sending()` — **antes** do byte sair;
9. **um** PUT; mapear resposta; `ack`/`reject`/`unknown` no tracker;
10. responder honesto: `update_acknowledged=true`,
    `update_confirmed=false`, `persistence_proven=false`
    (só vira CONFIRMED com read-after-write real — ainda não implementado
    para product).

## 5. Semântica de erro (tabela de decisão)

| Situação upstream | Status ledger | HTTP ao cliente |
|---|---|---|
| 2xx | `ACKNOWLEDGED` | 200 + `persistence_proven:false` |
| 4xx (com ou sem detalhe parseável) | `REJECTED` | 400 + código `…_REJECTED` |
| 401/403 | token inválido → invalida cache | 502 `PROTHEUS_TOKEN_INVALID` |
| 5xx / indisponível / timeout | `UNKNOWN` (indeterminado — pode ter gravado) | 502 `PROTHEUS_UPSTREAM_ERROR` |
| gate off / pin mismatch / payload inválido / identidade não resolvida | nada enviado, `FAILED_PRE_SEND` ou nem cria | 422/503 conforme caso |

Nunca retry automático em escrita. `UNKNOWN` exige reconciliação manual
(read-after-write) — não reenviar cegamente.

## 6. Configuração por ambiente

| Var | dev/local | HML | prod |
|---|---|---|---|
| `INTRANET_PARAMS_AMBIENTE` | `2` | `"2"` literal | `1` |
| `PROTHEUS_REST_EXPECTED_BASE_URL` | `http://192.168.1.233:8061` | literal TST | `http://192.168.1.231:8061` |
| `PROTHEUS_{ENTITY}_…_ENABLED` | `true` só durante homologação | `false` literal até janela autorizada | `false` |

HML precisa de acesso ao banco de parâmetros — os `DB_*`/`TOTVS_DB_*` de
HML são deny-listed (`totvs-disabled.hml.invalid`), então a integração só
resolve com `INTRANET_DB_*` reais no `.env.hml` do servidor (checkout HML:
`~/projetos-teste/delpi-central`, NÃO `~/projetos/delpi-central` — este é o
checkout de produção). Sem `INTRANET_DB_*` a integração falha fechada.
Provisionado em 2026-11-17: `.env.hml` com `INTRANET_DB_*` +
`PROTHEUS_PRODUCT_UPDATE_ENABLED=true` + pins TST; container
`delpi-hml-api-delpi` healthy com a rota live e params resolvendo
`URL_REST=http://192.168.1.233:8061` (+ `BASE_PATH=/restall`).

## 7. Receita de homologação live (TST01)

1. Container com `AMBIENTE=2` + pin TST + gate `true` (só no env do
   container/servidor; examples continuam `false`).
2. Escolher **entidade de teste** segura (produto `10450043` funcionou —
   artigo de teste, não bloqueado).
3. **Snapshot completo** antes (SQL read-only `SELECT` nos campos).
4. Executar o fluxo pela façade (não só direto no upstream — queremos
   provar gate+identidade+pin+tracking).
5. Verificar persistência (read-only) no `DELPI_TST01` **e** confirmar
   `DELPI` (prod) intacta.
6. Conferir ledger: `resource`, `action`, `resource_key`,
   `protheus_user_id`, `environment_key=ambiente:2@…`, status + eventos.
7. **Restaurar** o valor original via a própria superfície (2ª prova).
8. Gravar artefato em `docs/integrations/evidence/` com operation_ids,
   status, SQL before/after (padrão `protheus-rest-product-update-ledger.md`).

## 8. Checklist para uma nova entidade/rota

- [ ] Localizei o handler upstream (.PRW custom ou classe nativa) e li o
      contrato real (campos lidos, `VAL()`, shape do body, respostas)?
- [ ] Decidi partial vs full-representation **com base no fonte**, não em suposição?
- [ ] Payload builder: allowlist + rejeita identidade/unknown/null?
- [ ] `B1_COD`/chave primária injetada pelo backend (path), nunca do body?
- [ ] Gateway: 1 tentativa, mapper com 4xx→REJECTED tolerante a corpo inválido?
- [ ] Use case na ordem da seção 4 (gate antes de Core; pin antes do PUT;
      tracking antes do envio)?
- [ ] Permissão própria `…{entity}.{action}` + scope + rota com
      `operation_id` único + `ROUTE_CONTRACTS`?
- [ ] Gate `…_ENABLED=false` nos 3 env examples?
- [ ] Tracker com `resource` novo; ledger vai a `plugins_hub`?
- [ ] Resposta honesta (ACK ≠ CONFIRMED)?
- [ ] Testes: payload (missing/null/unknown/identidade), use case
      (ordem/gates/pin/tracking), gateway (4xx/5xx/401/timeout/2xx),
      rotas (permissão errada → Forbidden), OpenAPI (operation_id único)?
- [ ] Evidência live em TST01 com restore + artefato em `docs/integrations/evidence/`?
- [ ] Verificação independente (`delpi-verifier`) antes de considerar pronto?

## 9. Limitações conhecidas (estado atual)

- **Carimbo no ERP = conta de serviço** em rotas que não aceitam `codusr`
  (delpiproduto). Ator real garantido no ledger local. Para carimbo nominal
  dentro do Protheus: pedir campo `codusr` na rota custom ou usar rota que
  já aceita (suppliers).
- **`ACKNOWLEDGED` ≠ persistência provada.** CONFIRMED exige read-after-write
  canônico (ex.: GET na mesma entidade) — pendente para products.
- **HTTPS**: REST interno é HTTP (decisão do solicitante — intranet +
  firewall); fica como backlog de segurança.
- **APIs nativas**: não testadas para escrita ainda — homologar igual ao
  padrão acima quando ativadas; o carimbo nativo tende a ser também o da
  conta técnica.
- Gates transversais de CI (`--base HEAD`) só olham `base..HEAD`: working
  tree não commitado não é auditado por eles — verificar sempre com
  `delpi-verifier` + testes.

## 10. Referências

- Evidência live product: `docs/integrations/evidence/protheus-rest-product-update-ledger.md`
- Tracking: `docs/integrations/protheus-write-execution-tracking.md`
- Contrato supplier: `docs/integrations/protheus-rest-supplier-api-contract.md`
- Desbloqueio de homologação: `docs/integrations/protheus-rest-homologation-unblock.md`
- Leitura/status: `docs/integrations/protheus-rest-read.md`
- Fonte upstream produto: `DLP04I01.PRW` (`delpiproduto` → `MATA010`)
