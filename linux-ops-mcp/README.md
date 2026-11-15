# Delpi Linux Operations MCP — P1 READ-ONLY em operacao; P2 PREPARE em desenvolvimento

**Status atualizado em 2026-11-15:** o operador confirmou login Keycloak OAuth, conexao do plugin ATLAS no ChatGPT e chamada real de leitura de observacao Linux via gateway HTTPS. As notas historicas abaixo documentam o periodo de preparacao anterior ao go-live. O MCP segue com **quatro tools READ apenas**, sem PREPARE/ACT. A evolucao P2.1/P2.2a adiciona somente modulos Python offline nao importados no `server.py`. O repositorio publico nao deve conter secrets, tokens ou logs brutos.

## Scope and reuse

Four typed READ tools; no ACT/PREPARE; no SSH, subprocess, shell, Docker socket, SQL or arbitrary filesystem access:

- `get_host_health`: curated CPU/RAM/swap/root disk and freshness.
- `list_managed_services`: allowlisted systemd unit states and Docker aggregate counts. **No container list**, since collector summary is intentionally limited.
- `get_service_health`: allowlisted systemd unit. Service status is the *last observation*, **not current probe**.
- `get_deployment_revision`: returns **not_available** until there is a canonical attested deployed-SHA source. GitHub HEAD is **never** reported as production revision.

Data owner: existing `it-portal-api` `GET /servers/{server_id}/observations/latest`, permission `it-portal.access` and `it-portal.servers.view`; HTTP GET only. Existing Linux collector owns observation ingestion. No duplicate inventory collector, migrations, API schemas or gateway configuration.

MCP AuthN reuses `delpi_mcp.auth.mcp_transport_auth`, `delpi_auth` JWT validation and RBAC context, `delpi_mcp.resource_contract` metadata/challenge and `delpi_mcp.transport`. The IT Portal backend **independently rechecks** its permissions against the same human bearer. Any unavailable Core RBAC, bad issuer/aud/scope, missing permissions, stale token or service identity fails closed. Stale **observation** is allowed but explicitly labeled stale.

## Configuration (no secret values in Git/chat)

Required runtime env, in approved canonical env storage:
- `LINUX_OPS_IT_PORTAL_URL=http://it-portal-api:8000`: fixed internal service URL. The adapter denies outbound URLs except local IT Portal approved hosts.
- `LINUX_OPS_SERVER_ID=<existing UUID>`: registered srv-api ID (no new server).
- `LINUX_OPS_MCP_RESOURCE_URL=https://.../apps/linux-ops-mcp/mcp`: **exact OAuth audience** for approved transport.
- `KEYCLOAK_ISSUER=https://.../auth/realms/delpi`: real trusted issuer.
- `PUBLIC_BASE_URL=https://...`: transport host/Origin allowlist derivation.

**Do not create arbitrary new compose/env files**: `.cursor/rules/platform-delivery-runtime-operations.mdc` requires use of existing canonical sources. This follow-up introduces an opt-in `linux-ops` profile in the canonical `infra/docker-compose.yml`, but **does not activate** it or modify gateway/Keycloak. Runtime deployment must be a separate, reviewed and authorized change.

## Preflight before ANY runtime deployment

1. Review status of PR #184 and the P1 PR, run local tests/CI with shared repo packages and `mcp>=2,<3`, static security scanners and type/import checks. These tests are **not executed** by a code-only GitHub commit.
2. Resolve unclean production checkout without `restore`/`reset` by automation. Check local git SHA against verified remote; do not assume modified `shared/delpi_auth.egg-info/SOURCES.txt` is safe to overwrite.
3. Check Linux collector S2S installation, latest observation populated, freshness/sections. A missing observation must return `unavailable`, never fabricated live host data.
4. Select transport after verify of Secure MCP Tunnel entitlement, or use canonical OAuth via gateway; this repo does not deploy or configure tunnel-client.
5. Register Keycloak dedicated client and exact redirect (from ChatGPT), resource audience, `mcp:tools` and Core permissions using existing onboarding runbook. No secret in Git.
6. Deploy MCP process as non-root/non-docker, read-only root filesystem, no host namespace, no SSH agent, no bind of `/var/run/docker.sock`, no `infra/.env` mount, no arbitrary network egress, bounded CPU/RAM, healthchecks, stdout redaction and HTTPS/tunnel.
7. Test negative cases: no/invalid token, wrong audience, missing scope, wrong principal, revoked Core permission, Core outage, upstream 401/403/503, malicious observation fields, stale data, invalid service name, URL spoofing and no-capability to run commands.
8. Prove a real authenticated ChatGPT `tools/list`/`tools/call` against `srv-api`, with timestamps and sanitized evidence. Only then mark P1 runtime verified.

## Development checks (local only, not srv-api)

Install the pre-existing shared packages from the checkout's package files in a **temporary venv**, together with `requirements.txt`; do not use `pip` global or change production packages.

```bash
cd linux-ops-mcp
PYTHONPATH=. pytest -q tests/test_reader.py
python -m compileall -q linux_ops_mcp
```

The package is intentionally not wired into Docker or the public gateway until security review. **Do not deploy this service globally or assume production OAuth is configured. For the opt-in local-only pilot, follow `docs/03-private-tunnel-oauth-go-live.md` and its gates.**

## Decision and documentation log

| Date | Event | Status |
|---|---|---|
| 2026-11-14 | Host inventory: Ubuntu 24.04.4, 16 CPU, 47 GiB RAM, 135 running containers, health filters empty | OPERATOR_REPORTED |
| 2026-11-14 | Local `origin/main` SHA differs from running checkout SHA, working tree has 1 tracked changed file | DRIFT_TO_INVESTIGATE |
| 2026-11-14 | Source candidate with 4 read-only MCP tools and pure tests | CODE_CANDIDATE / TEST_NOT_RUN |
| 2026-11-14 | Agent installed, token connected, tunnel created, host touched | NOT_DONE |

Next step is evidence of `it-portal-api` Linux observation ingested + authenticated smoke in a non-production environment.


## P1-R2: runtime opcional e testes (2026-11-14)

- **Decisao do operador:** coleta Linux ja funcional, aceita como evidencia operacional do owner. Nao solicitar nova prova de ingestao para continuar o desenvolvimento. Isso **nao** representa smoke OAuth/MCP concluido.
- **Imagem isolada:** `linux-ops-mcp/Dockerfile` (usuario numerico 10001, codigo na imagem, sem dados host, sem SSH ou Docker CLI).
- **Compose produtivo canonico:** servico `linux-ops-mcp` sob profile `linux-ops`, **nao iniciado por padrao**. Porta publicada **somente em loopback** `127.0.0.1:${LINUX_OPS_MCP_LOOPBACK_PORT:-18765}:8000` (introduzida na PR #187), sem portas LAN/públicas, `volumes` ou `docker.sock`; FS read-only, todas capabilities removidas, no-new-privileges, 0.25 CPU, 256 MiB, log limitado e health local.
- **CI proprio:** `.github/workflows/linux-ops-mcp-readonly.yml` executa testes isolados, contratacao de 4 tools, compilacao e Docker build no runner GitHub. Nao executa deploy.
- **RBAC fortalecido:** cada chamada MCP faz refresh Core `/me` `force_refresh=True`, sem fallback stale; subject do response deve coincidir com o JWT autenticado. A API do Portal TI tambem aplica RBAC a leitura.
- **Protecao de ativo:** a observacao retornada deve ter `server_id` igual ao UUID configurado; nao aceita amostra de outro servidor.
- **OAuth:** `LINUX_OPS_MCP_RESOURCE_URL` deve usar origem HTTPS de `PUBLIC_BASE_URL` e path exato `/apps/linux-ops-mcp/mcp`. CORS/Host allowlist dependem da origem.

### Sequencia operacional futura (NAO EXECUTAR AGORA)

1. Aguardar PR aprovado e CI verde. Inspecionar `docker compose config` somente com saida sanitizada para evitar vazar `.env`.
2. Tratar o checkout produtivo sujo por estrategia conservadora, sem alterar o arquivo modificado automaticamente.
3. Configurar o Keycloak dedicado com client OAuth PKCE e audience URL MCP exata, conforme `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`. Nunca usar service token no MCP conversacional.
4. Escolher o transporte (**Secure MCP Tunnel** isolado ou rota HTTPS com revisao separada); esta PR nao abre rota externa nem instala tunnel-client.
5. Somente apos teste do SDK e do contrato, acionar a imagem opcional via compose com `--profile linux-ops --no-deps`, sem iniciar/stopping outros containers; confirmar health e permissoes.
6. Testar 401 sem token, 401 com audience errada, revogacao de RBAC, metadata, initialize, tools/list e tools/call autenticado no ChatGPT. Sem esses testes `RUNTIME_NOT_VERIFIED`.

### Status de evidencia

```text
HOST_COLLECTOR: OPERATOR_CONFIRMED_WORKING
MCP_CODE: IMPLEMENTED_IN_PR (NOT_MERGED at creation time)
MCP_CI: PR_186_PASS / PR_187_TO_VERIFY
MCP_RUNTIME: NOT_DEPLOYED
MCP_OAUTH: NOT_CONFIGURED
MCP_PUBLIC_CONNECTION: NOT_CONNECTED
DEPLOY_WRITE: NOT_IMPLEMENTED
```


### P1.3: endpoint privado via loopback (PR #187)

O serviço opt-in anuncia apenas `127.0.0.1:${LINUX_OPS_MCP_LOOPBACK_PORT:-18765}:8000`; não existe acesso público à porta. Confira a porta real com `docker compose --profile linux-ops port linux-ops-mcp 8000`, sempre no contexto canônico do Compose. Não assuma `18765` quando o operador personalizar a configuração. O Secure MCP Tunnel é um serviço separado, ainda não instalado nem cadastrado. OAuth e autorização no Core continuam obrigatórios. O procedimento detalhado e o rollback isolado estão em `linux-ops-mcp/docs/03-private-tunnel-oauth-go-live.md`.


## P2.1 / P2.2a — base de governanca de deploy, offline (2026-11-15)

- Fonte de continuidade: [roadmap mestre ATLAS](../docs/12-roadmap-e-evolucao/mcp-linux-control/README.md) e [contrato P2-P4](../docs/12-roadmap-e-evolucao/mcp-linux-control/02-atlas-deploy-control-plane-p2.md).
- `linux_ops_mcp/deploy_policy.py`: politica pura de preview deny-by-default integrada pela PR #191, com allowlist, SHA exato, gates de evidencia, TTL e hash de proposta **nao autorizativa**.
- `linux_ops_mcp/deploy_attestation.py`: gate puro P2.2a em `main`, validando o formato de provas independentes de GitHub Workflow/commit, host deploy revision/saude e Core principal humano com permissoes `linux_ops.deploy.view` + `linux_ops.deploy.prepare`. Ainda nao busca dados verdadeiros: futuramente a API backend busca, atesta e monta os objetos, sem aceitar provas da chamada MCP. **Nao** importado por `server.py`.
- Testes locais em 2026-11-15 (Python 3.13): `PYTHONPATH=linux-ops-mcp pytest -q linux-ops-mcp/tests/test_deploy_attestation.py linux-ops-mcp/tests/test_deploy_policy.py` -> **76 PASS**. GitHub CI do novo commit e verificador independente a validar; nao equivale a teste de API real, HML ou PROD.
- Nenhuma migration, journal persistente, recurso Core registrado, provider HTTP GitHub, leitor local de SHA, endpoint PREPARE, ferramenta de ACT, executor privilegiado ou deploy do host foi criado nesta entrega. A politica em memoria de producao continua nao habilitada.
