# ATLAS P2.2e | Integracao descartavel PostgreSQL/Docker e gates de homologacao

> Atualizado: 2026-11-15. **Codigo de CI criado na main. Resultado dos novos jobs do GitHub Actions NAO CONFIRMADO. Nenhuma alteracao em containers, banco ou Keycloak produtivos.**

## 1. Evidencia operacional recente

O operador confirmou no srv-api que os 35 testes de P2.2d passaram em venv Python 3.12, sem falha (com avisos nao bloqueantes do FastAPI/Starlette). Confirmou, sem transcrever os logs, que a verificacao seguinte encontrou os containers `linux-ops-mcp` / `it-portal-api` funcionando, metadata OAuth disponivel (resultado esperado HTTP 200) e recurso MCP sem bearer recusado (esperado HTTP 401). Registrar como **confirmacao do operador**, nao como leitura autonoma de runtime.

Isso valida o ambiente de consulta do ATLAS **READ**, nao uma ferramenta de deploy.

## 2. Correção P2.2e no journal

Arquivo: `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_journal.py`.

Foi identificado um gap do FakePg: na versao anterior, o SQL tentava inserir a proposta ANTES de comprovar se o challenge existia e estava valido, o que poderia produzir erro de FK no PostgreSQL em vez de bloqueio seguro; duas requisicoes simultaneas podiam concorrer pela mesma idempotency key.

O fluxo corrigido dentro de uma transacao PostgreSQL:

1. Obtem um `pg_advisory_xact_lock` indexado em requester+request UUID.
2. Reconsulta o relogio do banco APOS adquirir o lock e busca a proposta ja existente com `FOR UPDATE`.
3. Se houver proposta idêntica e vigente no estado `pending_approval`, retorna o mesmo id sem novo consumo de challenge/evento; payload divergente ou encerrado bloqueia.
4. Se nao houver proposta, **consome challenge validado primeiro**, insere a proposta com chave unica e em seguida o evento, tudo na mesma transacao.
5. Falta de challenge, concorrencia inesperada ou erro cancela a transacao integralmente; nunca aprova ou executa.

O indice `UNIQUE(requester_subject,request_id)` e a unicidade do digest continuam sendo a barreira persistente; o lock reduz a ambiguidade da concorrencia. Os dados de solicitante, alvo e evidencias ainda precisam ser obtidos exclusivamente do backend autenticado antes de chamar esse adapter, que **nao possui endpoint**.

## 3. CI real, separado do servidor DELPI

Workflow: [`.github/workflows/atlas-p22e-integration.yml`](../../../.github/workflows/atlas-p22e-integration.yml).

**Job 1: `disposable-postgres`**

- GitHub-hosted `ubuntu-latest` e container descartavel `postgres:16-alpine` com banco/usuario exclusivamente de CI.
- Teste `it-portal-api/tests/integration/test_atlas_postgres_journal.py`, 7 casos para create/replay, erro em nonce, payload diferente, desafio reutilizado, expirado, concorrencia de duas conexoes reais e evento transacional.
- O teste exige `GITHUB_ACTIONS=true`, `ATLAS_DISPOSABLE_PG=true`, banco com nome `atlas_ci_disposable` e host loopback. Recusa qualquer alvo inesperado, schema ja existente e nenhuma migration produtiva e aplicada.
- DDL revisavel de [P2.2d](./05-atlas-p22d-candidate-schema.sql) aplicado **somente no banco efemero de CI**.

**Job 2: `disposable-docker`**

- Roda no runner descartavel, criando um unico container Alpine com nome e labels de teste, removido com `if: always()`.
- Teste `linux-ops-mcp/tests/test_atlas_docker_engine_ci.py`, 2 cenarios que consultam o Docker Engine real no **runner CI**, verificam labels/ID da imagem e validam assinatura de um registro de release **sintetico de teste**.
- O teste exige `GITHUB_ACTIONS=true` + `ATLAS_DISPOSABLE_DOCKER=true`; nunca roda o Docker Engine do srv-api.
- **Nao** e homologacao do proxy de leitura de Docker, nem comprovacao de provenance de uma imagem DELPI.

GitHub workflow tem `permissions: contents: read`, sem segredo de producao, e nao executa deploy. O Docker socket e acessado apenas pelo processo de teste no runner efemero, **nunca** montado no MCP do ATLAS.

## 4. Evidencias e limites, sem marcar aceite prematuro

- Teste simulado `test_atlas_deploy_journal.py` atualizado: **16 PASS** no ambiente isolado local Python 3.13.
- Testes de integracao real: **7 PostgreSQL + 2 Docker** criados; nao puderam rodar localmente porque o ambiente do assistente nao possui PostgreSQL/Docker, e ficam `skip` por seguranca.
- `python -m compileall` local PASS, YAML de dois jobs analisado.
- Testes GitHub Actions dos novos jobs: **PENDING/NAO CONFIRMADOS** (ferramenta GitHub disponivel nao lista runs de `push`); revisar na aba Actions antes de aceitar a entrega.
- Revisao independente `delpi-verifier`: **PENDENTE**, indisponivel nesta sessao.
- Nenhum `it-portal-api/migrations/V*.sql` foi adicionado; nenhuma migration, grant Core, API PREPARE, approval, executor ACT, novo MCP tool ou deploy foi aplicado.

## 5. Gate seguinte: HML real de um alvo, sem tocar PROD

1. Operador/owner seleciona UM servico nao critico do `docker-compose.hml.yml` realmente existente em HML. Confirmar nome do container, Compose project/service, health e independencia de PROD, sem presumir o ID.
2. Definir canal de observacao Docker *estritamente read-only* com proxy/ACL testada, isolado do MCP ChatGPT. O socket Docker de host nunca deve ficar no container MCP nem em endpoint web.
3. Implementar release manifest assinado pelo executor autorizado e segredo de signer em secret store, com prova de que o `ImageID` provem do SHA aprovado. Hoje o CI usa registro **sintetico**, nao valida provenance de build.
4. Coordenar owner de banco/migration com Portal TI/Delpi Remote; aprovar DDL e executar teste de migracao/rollback em DB de HML antes de versionar migration para runtime.
5. Provisionar grants Core de PREPARE com separacao entre solicitante e aprovador e testá-los com revogacao; `checkout_clean`, `migrations_safe` e `rollback_ready` continuam false/sem atestacao independente.
6. Somente apos evidencias e revisao independente considerar publicar `preview_deployment` (PREPARE). `ACT` permanece bloqueado ate P3.

**Estado:** `P22E_CODE_MAIN_POSTED`, `P22E_EPHEMERAL_CI_SUBMITTED_NOT_VERIFIED`, `P22E_REAL_HML_NOT_EXECUTED`, `PROD_READ_CONFIRMED_BY_OPERATOR`, `DEPLOY_ACT_DISABLED`.


## 6. Inventario HML confirmado pelo operador e piloto de leitura selecionado (2026-11-15)

**Evidencia manual fornecida pelo operador no terminal de srv-api:** `docker ps --format '{{.Names}}  {{.Status}}' | grep -Ei 'hml|homolog|teste' || true`. Resultado: **23 containers delpi-hml ativos, todos com status (healthy)** na amostra. Entre eles: `delpi-hml-engineering`, `delpi-hml-engineering-api`, `delpi-hml-gateway`, `delpi-hml-keycloak`, `delpi-hml-postgres-plugins` e outros do ambiente HML. O comando nao demonstra isolamento de redes/dados sozinho.

**Candidato escolhido apenas para observacao READ:** `delpi-hml-engineering` (frontend Engineering, sem alterar containers). Fonte do catalogo: `infra/docker-compose.hml.yml`, service `engineering`, project `delpi-hml`, container_name `delpi-hml-engineering`, healthcheck HTTP local, `ports: !override []`, `depends_on: !override {}`, `volumes: !override []`, labels `delpi.environment: homologation` e `delpi.project: delpi-hml`. Nao selecionar banco, Keycloak, Core API ou gateway para piloto.

**Gate de inspeção de runtime ainda pendente:** ler com `docker inspect --type container --format` apenas Name, ID, ImageID, labels Compose project/service e State/Health; nunca imprimir Env, Mounts, NetworkSettings, volumes, credenciais ou JSON completo. Confirmar labels reais (nao inferir do Compose), image ID valido, nome exato e comportamento do healthcheck. Se divergirem, negar selecao do piloto e revisar catalogo. Tambem verificar que o SHA da imagem ainda **nao prova provenance do commit**.

**Efeitos operacionais registrados:** usuario executou somente `docker ps`; nao ha relato de build, restart, deploy, schema, habilitacao de tools, Docker socket no MCP ou autorizacao ACT. Nenhum emissor signer ou proxy read-only foi instalado. O proximo passo e consulta filtrada com `docker inspect` + evidencia de status do workflow GitHub, mantendo HML e PROD intactos.
