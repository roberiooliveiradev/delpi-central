# ATLAS P2.2f | Rastreabilidade OCI do Public Hub (sem deploy)

**Data:** 2026-11-15
**Status:** alteracoes versionadas em `main`, testes estaticos/guard local PASS; **CI Docker real pendente de confirmacao**. Nao executado build ou restart no srv-api. Nenhuma ferramenta PREPARE/ACT do ATLAS foi habilitada.

## 1. Motivacao e fato observado

O operador selecionou **somente READ** do container `delpi-hml-public-hub` em vez de Engenharia, que pertence a Roberto e estava sendo modificada por ele. Validou manualmente em `srv-api` `Name=/delpi-hml-public-hub`, Compose `project=delpi-hml`, `service=public-hub`, `environment=homologation`, `running=true`, `healthy` e a imagem:

- `sha256:63ad3152e179d4a75e3cc1823a4062b300786fe841a635c4bbb8086e38e1112d`
- Criada em `2026-11-14T13:14:11.039760926Z`.
- Etiquetas OCI `org.opencontainers.image.revision` e `org.opencontainers.image.source`: **ausentes**, observadas como `<no value>`.

A etiqueta ausente **nao significa servico com falha**; significa que o SHA de origem da imagem historica nao pode ser comprovado. Nao reetiquetar a imagem antiga nem inferir um commit pela data ou HEAD atual.

## 2. Entrega de codigo

- `plugins/public-hub/Dockerfile` agora tem quatro stages e mantem **production como o stage final/default**:
  1. `builder`: construicao frontend anterior preservada;
  2. `development`: nginx + frontend para DEV, sem rotulo de release (permite trabalho local em andamento);
  3. `provenance-contract`: nginx leve com `ARG SOURCE_REVISION` que falha se nao receber **exatamente 40 caracteres hexadecimais minusculos**; LABEL OCI `revision` e `source`;
  4. `production`: herda o stage `provenance-contract` e agrega os arquivos finais do builder. As etiquetas estao no container final por heranca.
- `infra/docker-compose.yml`: apenas service `public-hub` recebe `build.args.SOURCE_REVISION: ${PUBLIC_HUB_SOURCE_REVISION:-}`. O default vazio evita impedir `docker compose config` de outras aplicacoes, mas um **build de public-hub** vazio falha deliberadamente no Dockerfile.
- `infra/docker-compose.hml.yml`: continua estendendo service de base, herdando o novo build arg. HML continua isolado sem ports, volumes nem depends_on neste service.
- `infra/docker-compose.dev.yml`: target de **public-hub somente** alterado para `development`, preservando a rotina local de trabalho sem inventar SHA.
- `infra/scripts/public-hub-provenance.sh`: funcao `atlas_public_hub_revision(root)` le SHA completo de `git rev-parse HEAD` e recusa alteracoes rastreadas, staged e arquivos nao versionados nos caminhos de build realmente copiados pelo Dockerfile. Nao aceita revisao curta, `unknown` ou HEAD ausente.
- `infra/scripts/up-hml-sequential.sh` e `up-prod-sequential.sh`: **somente quando `--build public-hub` esta no plano**, exportam a variavel especifica `PUBLIC_HUB_SOURCE_REVISION` obtida do checkout correspondente via helper; scripts mantem `SOURCE_REVISION` historico para os demais servicos. Nenhum outro container e forçado a receber o novo arg.
- `infra/scripts/tests/test_public_hub_provenance.py`: **11 casos PASS local** (Python3.13/pytest), cobrindo SHA de 40, worktree dirty, staged, untracked, diretoria fora de Git, contrato OCI, heranca HML, DEV sem release e ambos scripts. `bash -n` do helper PASS.
- [Workflow OCI](../../../.github/workflows/atlas-public-hub-oci.yml): testa helper/contrato e usa **Docker Engine apenas no GitHub Actions runner efemero** para construir **somente o stage `provenance-contract`**, conferir as labels do `GITHUB_SHA` pinado e demonstrar falha em revisoes ausentes/curtas/invalidas. Nao executa npm build do Public Hub, nao envia imagens ao registry e nao realiza deploy.

## 3. Fonte de autoridade e limites

**A etiqueta OCI e METADADO, NAO ATESTACAO CRIPTOGRAFICA.** Um operador com permissao Docker ou env var de build consegue produzir outra imagem com uma etiqueta de SHA arbitraria. Esta etapa reduz erro operacional no fluxo canonico (revisao completa + arquivos relevantes limpos), mas nao atribui legitimidade automatica a qualquer release.

O ATLAS so podera aceitar `commit_sha` como evidência de release apos:
1. CI vincular o commit a um build comprovado, verificando `ImageID` e as labels na **imagem final**, nao so stage de metadados;
2. executor independente registrar e autenticar `commit_sha + ImageID + execution_id + ambiente + target`;
3. leitor restrito ao host conferir que o **container rodando** utiliza o mesmo `ImageID`, com nonce e recibo HMAC fresco;
4. Core conceder permissoes, migrations/rollback obterem evidencia independente e aprovacao humana ficar fora do chat.

Sem esses quatro gates, P2.1/P2.2a continua DENY. **Nenhum novo MCP tool, executor, migration, relatorio falso de SHA instalado ou socket Docker foi criado.**

## 4. Compatibilidade operacional

- Build manual `docker compose build public-hub` sem `PUBLIC_HUB_SOURCE_REVISION` (ou com SHA curto) agora **falha por projeto**, para nao publicar etiqueta `dev` em HML/PROD. Usar scripts canonicos depois de homologacao e autorizacao do owner.
- Para desenvolvimento local com arquivos alterados, `infra/docker-compose.dev.yml` usa o target `development`, que **nao possui etiquetas de release** e nao e candidato a ATLAS PREPARE.
- Etapas HML e PROD mantidas separadas. **Nenhuma reconstrucao ou restart automatico foi efetuado** e o Public Hub HML historico continua com labels ausentes ate um build explicitamente autorizado.
- P2.2f nao corrige a imagem historica e nao valida a origem do SHA por assinaturas. Abrir a pagina do Public Hub ou ver 200/healthy nao prova release provenance.

## 5. Proximos gates

1. Confirmar o workflow OCI **verde** nos jobs do GitHub Actions; hoje o estado esta **NAO VERIFICADO** no plugin.
2. Executar `pytest` estatico e revisar `docker compose config` (somente leitura) no checkout HML real; confirmar que `public-hub` herda SOURCE_REVISION e que DEV manteve target development.
3. Obter aceite do owner do Public Hub para um futuro build HML unico, com rollback/health/sem conflito de trabalho. Nao executar build antes disso.
4. Em nova fatia do roadmap, ligar pipeline confiavel a manifest assinado (ou atestacao verificavel OCI) e ao signer isolado. Somente depois testar `ImageID` final HML.
5. `delpi-verifier` independente e revisao do Dockerfile em CI permanecem pendentes. **ACT/PREPARE continuam inativos**.

**Estado:** `P22F_CODE_MAIN`, `LOCAL_STATIC_TESTS_PASS_11`, `CI_REAL_DOCKER_UNVERIFIED`, `PUBLIC_HUB_HML_OLD_IMAGE_UNMODIFIED`, `PROVENANCE_TRUST_PENDING`, `ATLAS_READ_ONLY`.
