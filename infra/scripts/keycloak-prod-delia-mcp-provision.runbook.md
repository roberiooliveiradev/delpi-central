# Runbook — provisionamento DÉLIA MCP no Keycloak de PRODUÇÃO

Escopo: aplicar o contrato IAM DÉLIA/MCP (user-delegated token exchange) no
Keycloak de produção, de forma idempotente, auditável e fail-closed.

Executor: `infra/scripts/keycloak-prod-delia-mcp-provision.sh`
Engine compartilhada: `infra/scripts/delia_mcp_keycloak_state.py`
(mesmo engine usado pelo `keycloak-dev-bootstrap.sh` — DEV e PROD não
divergem).

Contrato provisionado (somente isto, nada mais):

| Recurso | Valor |
|---|---|
| Client scope | `mcp:tools` |
| Resource clients | `mcp-api-delpi`, `mcp-transformometro`, `mcp-tv-dashboard` |
| Requester client | `delia-api` (confidential, sem service account, sem DAG, `standard.token.exchange.enabled=true`) |
| Portal audience | `delia-api` adicionada como audience no client `delpi-central` (subject token elegível para exchange) |
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

O modelo exige o contrato provado em DEV: Keycloak **26.0.7** com
`KC_FEATURES=token-exchange,admin-fine-grained-authz`.

- Se o runtime alvo não suportar `standard.token.exchange.enabled` ou os
  endpoints `authz/resource-server` de `realm-management`, o provisioner
  **falha fechado**.
- Keycloak 24 usa o token-exchange legado (endpoints/contrato diferentes).
  Não existe fallback específico de KC24: se a versão for 24, tratar a
  migração de versão **separadamente** antes do `--apply`.

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

Com um usuário de teste (subject token via `delpi-central`):

```bash
# subject token
SUBJECT=$(curl -s -X POST $PUBLIC_BASE_URL/auth/realms/delpi/protocol/openid-connect/token \
  -d grant_type=password -d client_id=delpi-central \
  -d username=<test-user> -d password=<test-pass> \
  -d scope='openid profile email' | jq -r .access_token)

# exchange por especialista — trocar audience por cada resource client
curl -s -X POST $PUBLIC_BASE_URL/auth/realms/delpi/protocol/openid-connect/token \
  -d grant_type=urn:ietf:params:oauth:grant-type:token-exchange \
  -d client_id=delia-api -d client_secret=<DELIA_EXCHANGE_CLIENT_SECRET> \
  -d subject_token=$SUBJECT \
  -d subject_token_type=urn:ietf:params:oauth:token-type:access_token \
  -d audience=mcp-api-delpi \
  -d scope='openid profile email mcp:tools' | jq -r .access_token
```

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
6. **Versão Keycloak** — downgrade 26→24 requer restore do backup de DB
   (Keycloak não suporta downgrade in-place); por isso BACKUP é
   PRECONDITION.

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

1. Confirmar backup Keycloak DB restaurável.
2. Confirmar versão suportada (>= 26.0.7 ou migração separada).
3. `--check` → revisar drift humano.
4. `--apply`.
5. Instalar `DELIA_EXCHANGE_CLIENT_SECRET` via `--install-secret-to`.
6. Restart controlado de `delia-api`.
7. READ flags permanecem OFF.
8. Smoke token exchange (3 especialistas).
9. `tools/list` DAVI/TÉO/VISTA.
10. Habilitar DAVI bounded READ → positivo + negativo.
11. Habilitar TÉO bounded READ → positivo + negativo.
12. VISTA permanece discovery-only.
13. Registrar evidence real no ledger.
14. Só então `PRODUCTION_MCP_RUNTIME` pode deixar de ser `NOT_PROVEN`.
