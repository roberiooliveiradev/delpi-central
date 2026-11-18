# Delpi Linux Operations MCP — P1 READ-ONLY multisservidor; P2 PREPARE em desenvolvimento

**Status atualizado em 2026-11-18:** o ATLAS opera com **oito tools READ** (quatro legadas de host unico + quatro multisservidor). Continua sem PREPARE/ACT. A evolucao P2.x de deploy/HML permanece em modulos Python **nao importados no `server.py`**, isolada desta capacidade de monitoramento. O repositorio publico nao deve conter secrets, tokens ou logs brutos.

## Scope and reuse

Eight typed READ tools; no ACT/PREPARE; no SSH, subprocess, shell, Docker socket, SQL or arbitrary filesystem access.

### Legacy single-host tools (compatibilidade)

- `get_host_health`: curated CPU/RAM/swap/root disk and freshness for `LINUX_OPS_SERVER_ID`.
- `list_managed_services`: allowlisted systemd unit states and Docker aggregate counts. **No container list**, since collector summary is intentionally limited.
- `get_service_health`: allowlisted systemd unit. Service status is the *last observation*, **not current probe**.
- `get_deployment_revision`: returns **not_available** until there is a canonical attested deployed-SHA source. GitHub HEAD is **never** reported as production revision.

### Multiserver tools (inventario dinamico do Portal de TI)

- `list_servers`: lista servidores do inventario oficial com filtros e paginacao (nao para no primeiro page_size=25).
- `get_server_health`: saude de um servidor por UUID ou hostname (Linux e Windows); hostnames ambiguos devolvem candidatos.
- `get_infrastructure_health`: consolidado de saude com concorrencia limitada e isolamento de falhas por servidor.
- `get_server_services`: servicos Windows via `host-services` / dashboard; Linux via systemd allowlist da observacao.

Arquitetura detalhada: [docs/06-multiserver-health.md](./docs/06-multiserver-health.md).

Data owner: `it-portal-api` (`/servers`, `/observations/latest`, `/host-services`, `/dashboard/windows-services-health`), permissions `it-portal.access` + `it-portal.servers.view`; HTTP GET only. Coletores Linux/Windows existentes permanecem donos da ingestao. Sem segundo inventario, migrations ou schemas paralelos.

MCP AuthN reuses `delpi_mcp.auth.mcp_transport_auth`, `delpi_auth` JWT validation and RBAC context, `delpi_mcp.resource_contract` metadata/challenge and `delpi_mcp.transport`. The IT Portal backend **independently rechecks** its permissions against the same human bearer. Any unavailable Core RBAC, bad issuer/aud/scope, missing permissions, stale token or service identity fails closed. Stale **observation** is allowed but explicitly labeled stale.

## Configuration (no secret values in Git/chat)

Required runtime env, in approved canonical env storage:
- `LINUX_OPS_IT_PORTAL_URL=http://it-portal-api:8000`: fixed internal service URL. The adapter denies outbound URLs except local IT Portal approved hosts.
- `LINUX_OPS_SERVER_ID=<existing UUID>`: ainda exigido pelas **tools legadas** de host unico; as tools multisservidor descobrem servidores dinamicamente pelo inventario.
- `LINUX_OPS_MCP_RESOURCE_URL=https://.../apps/linux-ops-mcp/mcp`: **exact OAuth audience** for approved transport.
- `KEYCLOAK_ISSUER=https://.../auth/realms/delpi`: real trusted issuer.
- `PUBLIC_BASE_URL=https://...`: transport host/Origin allowlist derivation.

Optional tuning (defaults seguros): `LINUX_OPS_STALE_AFTER_HOURS`, `LINUX_OPS_INFRA_CONCURRENCY`, `LINUX_OPS_INFRA_MAX_SERVERS`, thresholds `LINUX_OPS_{MEMORY,DISK,CPU}_{ATTENTION,CRITICAL}_PCT`.

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


## P2.2b — Leitores backend GitHub / Core (2026-11-15)

- `linux_ops_mcp/deploy_evidence_readers.py` possui `GithubReleaseReader` e `CorePermissionReader`, **nao importados no server.py, sem tools MCP publicadas**.
- `GithubReleaseReader.read(commit_sha)` so consulta o endpoint oficial `api.github.com` do repositorio canonico. Verifica `main`, ancestry do commit por compare com SHA HEAD pinado e lista de runs de Actions `push`. Timeout 5s, Content-Type JSON, 256 KB max, sem seguir redirect, `trust_env=False`; sem erro com token/body. Provas passam a validacao pura P2.2a, mas **nao provam autorizacao de deploy** por si.
- `CorePermissionReader.read` recebe identidade e access token do **contexto autenticado no backend**; usa `load_user_rbac(token, force_refresh=True)` e aceita grants explicitos de deploy. Nao confia em `is_superadmin` como grant. Ainda nao possui API de producao ou Keycloak/Core scopes novos.
- Testes isolados: `PYTHONPATH=linux-ops-mcp python -m pytest -q linux-ops-mcp/tests/test_deploy_evidence_readers.py` → **32 PASS local** (Python 3.13, `httpx.MockTransport`, sem rede). Full-suite GitHub CI e revisao independente **pendentes**.
- Dependencias bloqueadoras: producer `HostProof` com SHA realmente implantado por servico, catalogo de workflow IDs por ambiente, grants Core, journal SQL e API PREPARE. Ver [roadmap mestre](../docs/12-roadmap-e-evolucao/mcp-linux-control/README.md) e [journal proposto](../docs/12-roadmap-e-evolucao/mcp-linux-control/03-atlas-deploy-journal-p2b.md). Nada de deploy em HML/PROD nesta entrega.


## P2.2c — Recibo de release local e idempotencia (2026-11-15)

- `linux_ops_mcp/deploy_host_receipt.py`: validador offline de um futuro **comprovante HMAC-SHA256 do host**, vinculando challenge, host, repo, ambiente, servico, SHA e IDs de imagem registrada/em execucao. Verifica integridade, campos exatos e frescor (90s). **Nao le Docker**, nao gera assinatura/chaves, nao assina sem trust boundary. O produtor host ainda precisa ser implementado fora do MCP, entao nenhuma evidencia real esta disponivel. Mesmo valido, seu `HostProof` mantem `migrations_safe=False` e `rollback_ready=False` ate atestacoes independentes.
- `linux_ops_mcp/deploy_journal_policy.py`: decisao inerte para candidatos PREPARE, UUID/idempotency key, SHA, hash, TTL de ate dez minutos e replay identico. **Sem Postgres/lock/transacao/API/ACT**. Persistencia e nonce one-shot exigem tabela e repository backend autorizados e coordenacao de migration.
- `tests/test_deploy_host_receipt.py` **30 PASS** + `tests/test_deploy_journal_policy.py` **17 PASS** (47 PASS local, Python 3.13, sem rede/host/DB); `compileall` local PASS. GitHub CI e revisao independente pendentes de evidencia.
- [Roadmap mestre](../docs/12-roadmap-e-evolucao/mcp-linux-control/README.md) e [runbook P2.2c](../docs/12-roadmap-e-evolucao/mcp-linux-control/04-atlas-p22c-host-receipt-journal-contract.md) mantem status, riscos e proximo gate. P2.2d: emissor local real em HML, registro imutavel de release, atestacao separada de rollback/migration e journal PostgreSQL com concorrencia. Sem deploy de qualquer componente desta fase em HML/PROD.


## P2.2d — Fonte Docker isolada e signer de release (2026-11-15)

- `linux_ops_mcp/deploy_host_source.py`: somente `GET /containers/{nome_static}/json` com transporte HTTP injetado, validacao de labels Compose, nome, IDs da imagem/container e estado; nenhum `docker.sock` ou processo privilegiado no MCP. **O acesso ao Docker e de alto privilegio mesmo para GET; qualquer piloto HML exige proxy de leitura isolado e review.**
- `linux_ops_mcp/deploy_host_signer.py`: valida manifest HMAC selado pelo futuro executor com chave de release, compara imagem do runtime e emite `SignedHostReceipt` assinado com chave diferente/challenge do backend. Nao ha emissor de manifests, secret store ou signer host instalado; `checkout_clean` permanece False e `migrations_safe/rollback_ready` seguem False para nao conceder falsa autorizacao.
- `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_journal.py`: camada **interna ao owner do banco**, com SQL parametrizado para desafio unico e proposta PREPARE idempotente, ainda nao importada por rotas. Seu [DDL review-only](../docs/12-roadmap-e-evolucao/mcp-linux-control/05-atlas-p22d-candidate-schema.sql) esta **fora** de `it-portal-api/migrations/`; nenhuma tabela foi criada em HML/PROD.
- Suite local cumulativa P2.1-P2.2d: **190 PASS** (Python 3.13, mock Docker e DB FakePg), compilacao PASS. Novos testes: 17 source/signer, 15 SQL fake e 3 guardas estaticas. GitHub CI, verificacao independente e PostgreSQL/Docker real **pendentes**.
- [Runbook completo da P2.2d](../docs/12-roadmap-e-evolucao/mcp-linux-control/06-atlas-p22d-runtime-attestation-and-journal.md). Proximo P2.2e e homologacao segura do emissor real em um unico alvo HML, testes DB descartavel e aprovacao do owner da migration. `server.py` segue com quatro READ; nenhuma tool PREPARE/ACT foi habilitada.


## P2.2e — CI PostgreSQL e Docker descartaveis (2026-11-15)

- `it_portal_app.infrastructure.persistence.atlas_deploy_journal.store_prepared`: ordenacao correta sob `pg_advisory_xact_lock`, `SELECT ... FOR UPDATE`, validacao de replay e consumo de nonce antes da insercao FK. SQL parametrizado, transacao de rollback em erro, sem endpoint MCP ou rota ativa.
- [`.github/workflows/atlas-p22e-integration.yml`](../.github/workflows/atlas-p22e-integration.yml): **jobs em runners GitHub hospedados e efemeros**, um com PostgreSQL 16 descartavel e outro com contêiner Docker Alpine temporario, nenhum com credencial/rota de PROD.
- `it-portal-api/tests/integration/test_atlas_postgres_journal.py` somente roda com flags CI + DSN explicitamente no loopback de banco `atlas_ci_disposable`; testa transacoes/replay/concorrencia em DB real. `tests/test_atlas_docker_engine_ci.py` exige flags CI de Docker e testa apenas Engine do runner, com comprovante HMAC sintético; o socket Docker nunca e entregue ao MCP.
- Validacao local do incremento: **16 testes de journal fake PASS**, integrações com PostgreSQL e Docker ausentes foram ignoradas como previsto; workflow de dois jobs analisado. **A conclusao dos jobs novos no GitHub Actions, `delpi-verifier` e a homologação HML real permanecem PENDENTES**.
- [Runbook P2.2e](../docs/12-roadmap-e-evolucao/mcp-linux-control/07-atlas-p22e-disposable-ci-and-hml-gates.md), [roadmap mestre](../docs/12-roadmap-e-evolucao/mcp-linux-control/README.md). O codigo ATLAS em producao **continua com quatro ferramentas READ**; nao implementar ACT nem montar Docker sock no MCP.


## Continuidade P2.2f.1 (2026-11-16)

CI existente P2.2e PostgreSQL/Docker e P2.2f OCI confirmado `completed/success` (runs `43719312596` e `43721625404`). Gate de contexto Public Hub corrigido **nesta entrega em main**, com 23 testes guard / 163 de regressao selecionada PASS; tentativa de verificador **INCONCLUSIVE** por motores Devin/Cursor indisponiveis, registrada conforme `GATE_PASS_VERDICTS` sem alegar aprovacao independente. Novo CI desta entrega a confirmar. [Evidencias, limitacoes e pedido de retomada](../docs/12-roadmap-e-evolucao/mcp-linux-control/08-atlas-p22f-public-hub-oci-revision.md#6-retomada-em-16112026-ci-confirmado-e-correcao-local-p22f1). MCP/host/DB sem alteracoes; PREPARE/ACT continuam desligados.
