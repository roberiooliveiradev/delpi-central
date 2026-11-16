# ATLAS P2.2e | Integracao descartavel PostgreSQL/Docker e gates de homologacao

> Atualizacao de continuidade em 2026-11-16: **CI P2.2e confirmado PASS** no run [43719312596](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43719312596), SHA `5f7c4a1d65eebaee43c2479ea339dd13f81920d1`, jobs PostgreSQL/Docker `completed/success`. As secoes abaixo preservam o historico de 15/11. Revisao independente, imagem final e HML real continuam pendentes; [estado atual P2.2f](./08-atlas-p22f-public-hub-oci-revision.md#6-retomada-em-16112026-ci-confirmado-e-correcao-local-p22f1). Nenhuma alteracao em containers, banco ou Keycloak produtivos.

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


## 7. Mudanca do piloto de leitura por ownership (2026-11-15)

O operador informou explicitamente que **nao autoriza utilizar `delpi-hml-engineering` como piloto**, pois pertence ao desenvolvedor Roberto e esta em alteracao. Este servico esta excluido do escopo atual do ATLAS, assim como componentes de Engenharia associados que estejam sob o trabalho do mesmo owner.

**Novo candidato de leitura READ-ONLY:** `delpi-hml-public-hub`, container observado no inventario humano como `Up 24 hours (healthy)`. A configuracao versionada `infra/docker-compose.hml.yml` define `service=public-hub`, `project=delpi-hml`, `container_name=delpi-hml-public-hub`, `ports: !override []`, `depends_on: !override {}`, `volumes: !override []`, rede HML isolada e healthcheck `wget` em `http://127.0.0.1/`.

**Gate de aceite do novo candidato:** proprietario e janela de alteracoes ainda precisam ser confirmados antes de qualquer deploy, restart, build ou atestacao operante; no momento **somente** `docker inspect --type container --format` filtrado para campos Name, labels Compose, ImageID, ContainerID e State/Health. Nao executar comando de escrita no Public Hub e nao presumir que o seu status healthy prove seguranca de implantar. O teste READ pode ser realizado sem intervir nos trabalhos de outros times.


## 8. Resultado do piloto READ de Public Hub (2026-11-15)

**Fonte:** saida fornecida pelo operador do comando filtrado `docker inspect --type container --format` em srv-api, nao leitura direta do ChatGPT, contendo somente os identificadores autorizados.

| Campo | Valor informado |
| --- | --- |
| Nome | `/delpi-hml-public-hub` |
| Compose project | `delpi-hml` |
| Compose service | `public-hub` |
| Ambiente | `homologation` |
| ImageID | `sha256:63ad3152e179...` (prefixo exibido; hash completo informado na conversa) |
| ContainerID | `6d380d466c88...` (prefixo exibido; ID completo informado na conversa) |
| Running | `true` |
| Health | `healthy` |

**Resultado:** `PUBLIC_HUB_IDENTITY_AND_HEALTH_READ_PASS`. Nome, labels de Compose, formato de ImageID e ContainerID, ambiente, estado running e saude estao coerentes com o `infra/docker-compose.hml.yml`. Nao houve alteracao do container.

**Nao validado:** existencia de label OCI `org.opencontainers.image.revision`, provenance assinada de imagem->commit GitHub, manifest HMAC de release, transporte Docker isolado para signer, lock/journal em banco HML, permissoes/aprovacao. Nenhum desses dados pode ser inferido de `ImageID`. `preview_deployment` e ACT continuam bloqueados.

**Proxima observacao READ:** consultar apenas as labels OCI de revisao e os metadados da imagem efetivamente apontada pelo contêiner via `docker image inspect --format`; nao imprimir JSON completo, Env, mounts nem secrets. Se label OCI nao estiver presente, registrar como `REVISION_LABEL_UNAVAILABLE` e manter o bloqueio de provenance. Mesmo presente, a label e informativa, nao prova assinatura de build; requer vinculo assinado do pipeline.


## 9. Resultado READ do OCI provenance no Public Hub (2026-11-15)

**Evidencia de execucao fornecida pelo operador:** comando filtrado `docker image inspect --format` na imagem real de `delpi-hml-public-hub`: `ImageID=sha256:63ad3152e179d4a75e3cc1823a4062b300786fe841a635c4bbb8086e38e1112d`, `Created=2026-11-14T13:14:11.039760926Z`, `org.opencontainers.image.revision=<no value>`, `org.opencontainers.image.source=<no value>`. A imagem esta saudavel como container, mas **nao ha binding verificavel com commit GitHub**, portanto `REVISION_LABEL_UNAVAILABLE`, `HOST_RELEASE_PROVENANCE=BLOCKED`. Data de criacao e SHA do checkout atual nao comprovam release historica.

**Causa de build confirmada no codigo versionado:** `plugins/public-hub/Dockerfile` (estagio `production`) nao declara `ARG SOURCE_REVISION`, `LABEL org.opencontainers.image.revision` ou `LABEL org.opencontainers.image.source`. `infra/docker-compose.yml`, service `public-hub`, usa `build.context: ../plugins`, `build.dockerfile: public-hub/Dockerfile` e `target: production`, **sem build.args SOURCE_REVISION**. `infra/docker-compose.hml.yml` estende esse build sem inserir essa evidencia. O script HML calcula `SOURCE_REVISION` curto, mas apenas exporta variavel de ambiente, nao torna-a automaticamente um argumento para esse Dockerfile.

**Atualizacao de execucao (P2.2f):** a parte de **metadados OCI, SOURCE_REVISION completo e verificacao de SHA invalido** foi implementada em codigo na `main` para **futuros builds**, sem tocar na imagem historica. Um workflow de CI para stage leve foi publicado, mas **seu resultado ainda nao esta comprovado**. Continuam **NAO IMPLEMENTADOS** o registro de release assinado do executor, a atestacao criptografica de CI para imagem final e a verificacao real da imagem reconstruida em HML. Ver [runbook P2.2f](./08-atlas-p22f-public-hub-oci-revision.md). Rotulos OCI isolados nao substituem attestation do pipeline nem registro assinado; nao colar etiqueta arbitraria em imagem historica para simular prova.

**Restricoes operacionais:** nao houve rebuild, restart, deploy ou migration. Public Hub permanece como candidato apenas READ ate confirmar ownership/janela; excluir componentes Engineering sob alteracao de Roberto. Gate de PREPARE/ACT nao habilitado.
