# Runbook — provisionamento DÉLIA MCP no Keycloak de PRODUÇÃO

Escopo: aplicar o contrato IAM DÉLIA/MCP (user-delegated token exchange) no
Keycloak de produção, de forma idempotente, auditável e fail-closed.

Executor: `infra/scripts/keycloak-prod-delia-mcp-provision.sh`
Engine compartilhada: `infra/scripts/delia_mcp_keycloak_state.py`
(mesmo engine usado pelo `keycloak-dev-bootstrap.sh`; estratégia por
versão — PROD usa `KC24_LEGACY`, DEV usa `KC26_STANDARD`).

Contrato provisionado (somente isto, nada mais):

| Recurso | Valor |
|---|---|
| Client scope | `mcp:tools` |
| Resource clients | `mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard` |
| Requester client | `delia-api` (confidential, sem service account, sem DAG; **sem** `standard.token.exchange.enabled` — atributo exclusivo do contrato KC26) |
| Portal audience | `delia-api` como audience no client `delpi-central` — **somente estratégia KC26**; KC24 legacy V1 não exige elegibilidade do subject token (o gate é a permission do target) |
| Policy | `delia-exchange-requester` (client policy → `delia-api`) |
| Permissions | `token-exchange` em cada resource client, associadas à policy |

Audiences de recurso derivadas de `PUBLIC_BASE_URL`:
`{PUBLIC_BASE_URL}/apps/api-delpi/mcp`,
`{PUBLIC_BASE_URL}/apps/transformometro-api/mcp`,
`{PUBLIC_BASE_URL}/apps/tv-dashboard-api/mcp`.

## PRECONDITIONS

- Backup do banco Keycloak de produção confirmado e restaurável.
- Keycloak de produção em versão compatível (ver VERSION CHECK).
- `infra/.env` (gitignored) ou ambiente com credenciais admin **locais**
  (o provisioner usa `KEYCLOAK_ADMIN`/`KEYCLOAK_ADMIN_PASSWORD` ou
  `DELIA_EXCHANGE_ADMIN_TOKEN` — nunca credenciais de produção digitadas
  em chat/log).
- `PUBLIC_BASE_URL` correto (ex.: `https://minhadelpi.com.br`).
- Realm `delpi` e client `delpi-central` **já existem**. Se ausentes o
  provisioner falha fechado — ele nunca cria realm nem o client Portal.

## VERSION CHECK

Target de produção: **Keycloak 24.x** (baseline vigente
`quay.io/keycloak/keycloak:24.0`) — `PROD_TOKEN_EXCHANGE_MODE =
KC24_LEGACY_V1`. Não há upgrade para KC26 neste escopo; a migração
futura é hardening independente (ver FUTURE MIGRATION).

Configuração exigida (já no `docker-compose.yml`):

```text
KC_FEATURES=token-exchange,admin-fine-grained-authz
```

Racional dos flags (provado em servidor real isolado 24.0.5):

- `token-exchange` habilita o grant legado
  `urn:ietf:params:oauth:grant-type:token-exchange` (internal →
  internal; o runtime DÉLIA envia `audience=<client-id>` e
  `scope` com `mcp:tools` — contrato V1).
- `admin-fine-grained-authz` é **obrigatória**: sem ela os endpoints
  `clients/{uuid}/management/permissions` e o resource-server de
  permissões retornam HTTP 500 (NPE `ClientPermissionManagement`) — o
  binding `delia-exchange-requester` → `token-exchange` não pode ser
  materializado.
- **Classificação de estabilidade:** ambas são features *Preview* no
  KC24 — `KC24_TOKEN_EXCHANGE_STABILITY = PREVIEW`. Preview ≠ não
  funciona (runtime confirmado), mas também ≠ supported/stable: pinar a
  versão, manter kill switches e regression tests.
- `standard.token.exchange.enabled` **não existe** no KC24 — a
  estratégia KC24 nunca lê/escreve esse atributo.

`KC24_INTERNAL_INTERNAL_TOKEN_EXCHANGE =
PROVEN_AVAILABLE_IF_OFFICIAL_DOC_AND_RUNTIME_CONFIRM` — doc oficial
KC24 (Securing Applications → token-exchange, preview) + runtime
real isolado 24.0.5: exchange 3/3 OK com subject humano preservado,
`azp=delia-api`, audience resource-bound isolada por especialista.

Mecânica KC24 divergente do KC26 (registrado para o review): o V1
legado **não** exige `delia-api` na audiência do subject token — o
gate efetivo é a permission `token-exchange` do target client atrelada
a `delia-api` (negativo provado: `audience=delpi-central` sem
permission → `403 Client not allowed to exchange`). O mapper de
audience no Portal existe apenas na estratégia KC26.

Migração rehearsal documentada (histórico, não prerequisite): KC24.0.5
+ postgres:15 com estado prod-like → start 26.8.0 no mesmo DB →
migração automática, realm/clients/users/mappers preservados, OIDC OK,
provisioner `KC26_STANDARD` converge, exchange 3/3 OK.

## CHECK COMMAND

```bash
cd infra
./scripts/keycloak-prod-delia-mcp-provision.sh --check
```

`--check` é somente leitura: zero writes, compara o estado desejado,
reporta `[OK]/[DRIFT]/[MISSING]` por elemento.

## EXPECTED CHECK OUTPUT

- Realm/contrato não provisionado: `[delia-mcp-provision] DRIFT_DETECTED`,
  exit `2`.
- Contrato já materializado: `[delia-mcp-provision] NO_DRIFT`, exit `0`.
- Precondição ausente/versão incompatível: `FAIL_CLOSED`, exit `1`.

## APPLY COMMAND

```bash
./scripts/keycloak-prod-delia-mcp-provision.sh --apply
```

`--apply` cria somente recursos ausentes do escopo bounded, associa a
policy e habilita permissions; reexecutar é idempotente
(`NO writes` quando já convergido). Nunca cria/edita usuários, nunca
reseta senhas, nunca executa SQL, nunca deleta clients/policies
desconhecidas (legacy `delia-mcp-requester` é migrado somente se for a
R1A conhecida; policies desconhecidas são preservadas).

## SECRET INSTALLATION

`--apply` imprime/instala o `client-secret` de `delia-api` **somente** via
`--install-secret-to <path>`:

```bash
./scripts/keycloak-prod-delia-mcp-provision.sh --apply --install-secret-to infra/.env
```

- O arquivo deve ser gitignored (o script verifica `git check-ignore` e
  falha fechado se o path for tracked).
- O valor **nunca** vai para stdout/stderr; a linha é atualizada
  atomicamente (`DELIA_EXCHANGE_CLIENT_SECRET=<valor>`), preservando o
  restante do arquivo.
- O secret não é rotacionado se já existir no Keycloak; ele é lido e
  reinstalado no env file.

## SERVICE RESTART ORDER

Após `--apply` + instalação do secret em `infra/.env`:

```bash
docker compose -f docker-compose.yml up -d delia-api
```

(somente `delia-api` — nenhum outro serviço depende do contrato).

## TOKEN EXCHANGE SMOKE

O subject token é **sempre** um token humano obtido pelo fluxo normal do
Portal — `delpi-central` é public client com authorization code flow
(+PKCE). O smoke canônico de produção é:

1. Login humano real no Portal (`https://<host>`) — o Portal conclui o
   authorization code flow em `delpi-central` e obtém o subject token.
2. No servidor, usar a sessão/token do Portal já emitido (o mesmo mecanismo
   que o runtime DÉLIA usa via `subject_bearer` da request autenticada)
   como `subject_token` — nunca `grant_type=password`, nunca senha em
   history/log, nunca service account.
3. Exchange por especialista:

```bash
curl -s -X POST $PUBLIC_BASE_URL/auth/realms/delpi/protocol/openid-connect/token \
  -d grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  -d client_id=delia-api -d client_secret=<DELIA_EXCHANGE_CLIENT_SECRET> \
  -d subject_token=<portal-user-access-token> \
  -d subject_token_type=urn:ietf:params:oauth:token-type:access_token \
  -d audience=mcp-api-delpi \
  -d scope='openid profile email mcp:tools' | jq -r .access_token
```

Alternativa igualmente canônica quando o Portal não puder fornecer o token:
um `authorization_code` obtido via login browser real pode ser trocado em
`.../protocol/openid-connect/token` (`grant_type=authorization_code`,
`client_id=delpi-central`, `code`, `redirect_uri`, `code_verifier`) — é o
mesmo mecanismo user-session do Portal.

`grant_type=password` (Direct Access Grant) permanece **apenas** como
evidência local/dev do migration rehearsal — não é mecanismo canônico de
smoke de produção.

Decodificar o JWT e verificar, por especialista:
`sub` == subject humano, `azp` == `delia-api`, `aud` contém a resource URL
do alvo e **não** contém as URLs dos outros especialistas, `scope`
contém `mcp:tools`.

## TOOLS/LIST DAVI · TÉO · VISTA

Executar `delia-api/scripts/real_mcp_interop_eval.py` (com envs PROD no
contexto apropriado) — esperado discovery PASS para os 3 especialistas e
invocable apenas `DISCOVERY`/`READ` permitidos.

## NEGATIVE TESTS

- Exchange com `audience` de outro especialista no token de um target →
  audience isolada (provar que cross-audience não vaza).
- `tools/call` de tool classificada `ANALYSIS`/`PREPARE`/`ACT`/unknown →
  bloqueada por DÉLIA.
- Request sem subject token → `MCP_AUTHENTICATION_FAILED`.

## ENABLE DAVI READ

`DELIA_C4_DAVI_PRODUCT_READ_ENABLED=true` em `infra/.env` + restart
`delia-api`. Habilita somente `execute_delpi_information → search_products`
(DAVI).

## VERIFY DAVI

Executar `delia-api/scripts/real_governed_read_eval.py` — esperado
provenance verdadeira (DAVI real) e consulta de controle não-grounded
rejeitada.

## ENABLE TÉO READ

`DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED=true` + restart. Habilita somente
`analyze → gpt_analyze` com `view=summary`.

## VERIFY TÉO

Mesmo eval; esperado KPI summary real do Transformômetro.

## ROLLBACK

Separado por camada — nenhum rollback exige apagar clients ou banco:

1. **C4 read flags** — voltar para `false` + restart `delia-api`
   (efeito imediato, menor blast radius).
2. **MCP specialist switches** — `DELIA_MCP_{DAVI,TEO,VISTA}_ENABLED=false`
   + restart — kill switch total da integração.
3. **Secret** — esvaziar `DELIA_EXCHANGE_CLIENT_SECRET` em `infra/.env`
   + restart — exchange passa a falhar fechado (`MCP_AUTHENTICATION_FAILED`).
4. **Compose/config** — reverter `docker-compose.yml` para a revisão
   anterior (reintroduz `*_USER_TOKEN` apenas se o runtime legado ainda
   for suportado — caso contrário manter flags OFF).
5. **IAM** — opcional: remover permissões `token-exchange` via
   provisioner futuro ou console admin; **não** deletar clients a frio.
6. **KC_FEATURES** — reverter o flag `token-exchange` requer restart do
   Keycloak; não há mudança de versão neste escopo (qualquer futura
   migração KC24→26 exige restore de backup para rollback).

## EMERGENCY DISABLE

Kill switch instantâneo, sem deletar nada:

```bash
# em infra/.env
DELIA_MCP_DAVI_ENABLED=false
DELIA_MCP_TEO_ENABLED=false
DELIA_MCP_VISTA_ENABLED=false
DELIA_C4_DAVI_PRODUCT_READ_ENABLED=false
DELIA_C4_TEO_DASHBOARD_ANALYZE_ENABLED=false

docker compose -f docker-compose.yml up -d delia-api
```

## FUTURE REAL-PROD SEQUENCE (documentada — NÃO executar sem revisão)

Nenhum apply em produção sem aprovação humana; este task não tocou PROD
real (`REAL_PRODUCTION_APPLY = TEST_NOT_RUN`).

1. Verificar que PROD roda o patch KC24 esperado
   (`/admin/serverinfo` → `systemInfo.version` major 24).
2. Confirmar backup Keycloak DB restaurável.
3. Conferir `KC_FEATURES=token-exchange,admin-fine-grained-authz` no env
   real; restart do Keycloak **somente** se o flag ainda não estiver
   ativo (janela controlada).
4. Verificar login Portal/OIDC antes de qualquer apply de IAM.
5. `--check` → revisar drift humano (esperado: `DRIFT_DETECTED` antes do
   primeiro apply).
6. `--apply` → `--check` = `NO_DRIFT`.
7. Instalar `DELIA_EXCHANGE_CLIENT_SECRET` via `--install-secret-to`.
8. Restart controlado de `delia-api`.
9. READ flags permanecem OFF.
10. Smoke token exchange com **sessão humana real do Portal** (3
    especialistas) — nunca password grant.
11. `tools/list` DAVI/TÉO/VISTA.
12. Habilitar DAVI bounded READ → positivo + negativo.
13. Habilitar TÉO bounded READ → positivo + negativo.
14. VISTA permanece discovery-only.
15. Registrar evidence real no ledger.
16. Só então `PRODUCTION_MCP_RUNTIME` pode deixar de ser `NOT_PROVEN`.

## FUTURE MIGRATION (deferred hardening — não implementar agora)

Task candidata: `KEYCLOAK-LEGACY-TO-STANDARD-TOKEN-EXCHANGE-MIGRATION`.

KC24 legacy V1 → Standard Token Exchange (KC26+): envolve upgrade de
versão (irreversível sem restore), mudança para
`standard.token.exchange.enabled` + permission model standard e
revalidação do contrato de scope/audience (V2 altera semântica de
`audience`/`scope`). Não bloqueia a validação MCP bounded atual.
