# ATLAS P2.2f | Rastreabilidade OCI do Public Hub (sem deploy)

**Data inicial:** 2026-11-15 · **Retomada:** 2026-11-16
**Status atual:** P2.2f em `main`, **CI Docker de metadados confirmado PASS**. P2.2f.1 do guard incluida nesta entrega em main, testada; tentativa de revisao independente INCONCLUSIVE registrada, sem alegar ACCEPT; CI novo confirmado PASS no commit `65ece2215e83c182269bdfbf1f2e93ce255ba30f` (secao 6.6). Imagem final/assinatura/HML pendentes. Nao executado build ou restart no srv-api; PREPARE/ACT inativos.

As secoes 1–5 registram o corte de 15/11; a secao 6 e a atualizacao de continuidade e prevalece sobre os estados historicos de CI pendente.

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


## 6. Retomada em 16/11/2026: CI confirmado e correcao local P2.2f.1

### 6.1 Evidencia GitHub consultada diretamente

| Workflow | SHA verificado | Run / jobs | Resultado |
| --- | --- | --- | --- |
| P2.2e PostgreSQL/Docker | `5f7c4a1d65eebaee43c2479ea339dd13f81920d1` | [43719312596](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43719312596); Docker `132827643651`, PostgreSQL `132827643802` | Run e dois jobs `completed/success`; logs Docker mostram 2 PASS, PostgreSQL sete pontos de teste `[100%]` e step success |
| P2.2f OCI | `1ac5b10f8ef6b4677cdcd5f736ca9020908a2d41` | [43721625404](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43721625404); OCI `132834655829` | Run/job `completed/success`; build de metadados e negativos success |

A consulta permitida `GET /repos/{owner}/{repo}/actions/runs?head_sha={sha}` resolveu a limitacao anterior; os endpoints por nome de workflow nao eram aceitos pelo conector. Nao e preciso repetir os testes antigos no servidor para continuar a revisao de codigo. Os runs acima pertencem aos SHAs historicos, **nao** ao candidate local desta retomada, nem provam a imagem final ou o ambiente HML.

### 6.2 Causa confirmada e delta local

**Antes:** `git status --porcelain` nao reportava `.env.local`, logs e outros arquivos ignorados pelo Git dentro dos paths de `COPY`. `plugins/.dockerignore` nao estava entre os inputs protegidos. Uma politica Dockerfile-specific pode substituir a politica do contexto, conforme a [documentacao oficial Docker](https://docs.docker.com/build/concepts/context/#dockerignore-files).

**Depois, no candidate local:**

- `atlas_public_hub_revision` inclui `plugins/.dockerignore` nos inputs; exige arquivo regular nao symlink e as tres exclusoes existentes (`**/node_modules`, `**/dist`, `**/.git`). Aceita linhas vazias/comentarios, recusa outros padroes e negacoes. Esta e uma politica deliberadamente restrita, nao um parser generico de `.dockerignore`; mudar exclusoes exige evoluir contrato, implementacao e testes juntos.
- Recusa qualquer `plugins/public-hub/Dockerfile.dockerignore`, inclusive symlink pendente, pois esse arquivo prevaleceria sobre o contexto.
- `git ls-files --others --ignored --exclude-standard` verifica arquivos ignorados nos inputs; so dispensa os paths comprovadamente excluidos pela politica Docker. `node_modules/dist` locais continuam permitidos, arquivos locais fora dos inputs tambem. Nao apaga arquivos nem imprime nomes/conteudos.
- Workflow OCI observa mudancas no `.dockerignore` do contexto e no override especifico; executa o helper no checkout real, compara a revisao ao `GITHUB_SHA` e so depois segue ao build leve ja existente.
- Nenhuma mudanca em Dockerfile, Compose, frontend Engineering, modulo MCP, journal, API, permissao ou migration.

**Limites:** este guard reduz erros de build local; nao prova confianca contra operador privilegiado, alteracao concorrente apos a checagem, flags Git que ocultem mudancas, dependencia npm/base image mutavel ou build manual fora dos scripts canonicos. A proveniencia assinada da imagem final segue obrigatoria; o guard nao desbloqueia PREPARE/ACT.

### 6.3 Requisitos e validacao

| Requisito | Evidencia | Estado |
| --- | --- | --- |
| RQ-01 retomar fonte atual e CI | Checkout inicial limpo em `main`, HEAD `e18ee9a31c08ed29092962c524bba95434d5255f`; runs acima | ATENDIDO |
| RQ-02 corrigir contexto Git/Docker | Baseline: 9 novos FAIL / 14 PASS; depois 23 PASS; ignored `.env/log`, nome com newline, politica/override, artefatos excluidos e arquivos fora dos inputs | ATENDIDO_LOCAL |
| RQ-03 manter runtime READ e sem operacao em servidor | Diff so helper, teste, workflow e documentos; sem Docker local; sem chamadas de escrita ao host | ATENDIDO |
| RQ-04 tentar revisao e publicar com evidencia fiel | `verify.py` exit 3, sem Devin/Cursor; INCONCLUSIVE aceito por `GATE_PASS_VERDICTS`, sem afirmar ACCEPT; entrega de codigo em main | CODIGO_PUBLICADO / REVIEW_INCONCLUSIVE |
| RQ-05 assinatura/imagem final e piloto HML | Fora desta correcao; gates do P2.2g ainda nao satisfeitos | FORA_DO_ESCOPO_COM_JUSTIFICATIVA |

Comandos locais efetivos (Python 3.12):

```bash
python -m pytest -q -p no:cacheprovider infra/scripts/tests/test_public_hub_provenance.py
# 23 PASS
PYTHONPATH=linux-ops-mcp python -m pytest -q -p no:cacheprovider \
  linux-ops-mcp/tests/test_deploy_policy.py \
  linux-ops-mcp/tests/test_deploy_attestation.py \
  linux-ops-mcp/tests/test_deploy_host_receipt.py \
  linux-ops-mcp/tests/test_deploy_journal_policy.py \
  linux-ops-mcp/tests/test_deploy_host_source_signer.py \
  infra/scripts/tests/test_public_hub_provenance.py
# 163 PASS (inclui os 23 do guard; nao somar)
bash -n infra/scripts/public-hub-provenance.sh infra/scripts/up-hml-sequential.sh infra/scripts/up-prod-sequential.sh
python -m unittest scripts/ci/test_audit_architecture_phase3.py scripts/ci/test_audit_platform_guardrails.py -q
# 48 PASS dos proprios scanners
python scripts/audit_documentation_structure.py
git diff --check
```

Aviso nao bloqueante do plugin pytest de anyio: `PytestRemovedIn10Warning`. O parse YAML e a chamada do helper no checkout real tambem passaram localmente. Na primeira execucao os comandos canonicos de enforcement com `--base e18ee9a31c08ed29092962c524bba95434d5255f` comparavam um diff vazio, nao validando o candidate local. Antes de mover `main` remota, os dois comandos foram reexecutados sobre o commit candidato completo `65ece2215e83c182269bdfbf1f2e93ce255ba30f`: ambos exit 0, zero findings. Nenhum scanner foi alterado; ver fechamento/CI na secao 6.6.

Responsabilidades materiais: **1 arquitetura** (helper operacional, sem novo owner), **2 seguranca** (falha fechada e nao revelar arquivos locais), **6 qualidade** (baseline/regressao), **7 delivery/runtime** (contexto Docker e CI). Sem alteracao de contratos HTTP, banco, UI ou telemetria.

### 6.4 EXECUTION REPORT e verificador

`verify.py` do kit versionado foi executado diretamente (`agent-kit/scripts/verify.py`) porque nao existe instalacao em `~/.delpi-agent-kit`; o runner suporta a fonte original. Pedido em `<git-dir>/delpi-verifier/requests/atlas-public-hub-context-r1.md`, fora do working tree. Sem alterar o runner, modelos ou gates.

Saida original do verificador, sem edicao:

````text
# Relatório do delpi-verifier

motor: none · modelo: n/a

veredito: INCONCLUSIVE

motivo: verificador indisponível

## Saída bruta

```
Nenhum motor headless disponível (devin/agent).
```
````

| Rodada | Veredito | OCs abertas / fechadas |
| --- | --- | --- |
| 1 | INCONCLUSIVE | Nenhuma emitida; motor indisponivel, nao houve revisao independente |
| 2 | INCONCLUSIVE | Nova tentativa antes da publicacao, mesmo codigo e 163 testes PASS; nenhuma OC, motor ainda indisponivel |

**Entrega:** codigo implementado/testado nesta entrega em main; CI novo confirmado PASS no commit `65ece2215e83c182269bdfbf1f2e93ce255ba30f` (secao 6.6). **REVIEW_RESULT=INCONCLUSIVE**, sem alegar aprovacao independente ou homologacao. A leitura completa de `agent-kit/hooks/verifier_hooks.py`, constante `GATE_PASS_VERDICTS`, confirmou que `INCONCLUSIVE` e um resultado admitido para encerrar a tentativa registrada. A indisponibilidade foi inicialmente interpretada como bloqueio absoluto de publicacao; essa interpretacao foi corrigida, sem mudar o kit, emitir ACCEPT ou habilitar runtime. Nenhuma nova operacao HML/PROD.

### 6.5 Retomada e recuperacao

1. CI desta entrega confirmado PASS conforme secao 6.6; manter a evidencia vinculada ao SHA. Qualquer alteracao de codigo posterior requer novos testes; CI nao habilita runtime por si.
2. Concluir revisao independente em ambiente Devin/Cursor disponivel. O INCONCLUSIVE registrado permite o encerramento desta tentativa, mas nao e ACCEPT nem prova de seguranca/HML. Corrigir OCs conforme AGENTS; nao alterar o kit para simular revisao.
3. P2.2g continua sendo build da **imagem final** + comprovacao assinada do pipeline, separada do release record de host e das chaves. Nao emitir HMAC de release a partir de labels autoafirmadas.
4. Antes de rebuild HML: ownership/janela do Public Hub, plano de recuperacao, proxy restrito e aceite. Engineering de Roberto segue excluido. PREPARE/ACT, DB e grants permanecem inativos.

**Rollback desta entrega:** nao houve operacao de runtime remota a desfazer. Se houver regressao de codigo/CI, criar commit corretivo ou reversao somente dos arquivos desta entrega; sem force push, reset/clean ou descarte de alteracoes concorrentes; nenhuma instrucao para apagar `.env` ou reetiquetar imagem antiga. A imagem HML historica nao foi modificada.


### 6.6 Publicacao direta pelo GitHub e CI observado

**Commit de codigo:** [65ece2215e83c182269bdfbf1f2e93ce255ba30f](https://github.com/roberiooliveiradev/delpi-central/commit/65ece2215e83c182269bdfbf1f2e93ce255ba30f), diretamente na `main`, com expected-head e sem force push. Base `e18ee9a31c08ed29092962c524bba95434d5255f`. A arvore publicada `8fbe0a8213a2ad85bb7edb69f3ae7bc82a360cb1` foi comparada a arvore local exata testada; read-back do helper confirmou blob `dac742ec18259c37847a99040f001f0874f3c0a2`. O checkout local e a branch remota ficaram sincronizados, sem arquivos de escopo pendentes.

| Evidencia do SHA de codigo | Run | Resultado observado |
| --- | --- | --- |
| ATLAS Public Hub OCI Revision Contract | [43849195548](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195548) | `completed/success` |
| Linux Ops MCP Readonly Tests | [43849195553](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195553) | `completed/success` |
| Architecture Enforcement | [43849195523](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195523) | `completed/success` |
| Cursor Rules Governance | [43849195596](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43849195596) | `completed/success` |

**Gates locais do diff real:** `audit_architecture_phase3.py --check --base e18ee9a31c08ed29092962c524bba95434d5255f` e `audit_platform_guardrails.py` com mesma base: exit 0 / zero findings no commit candidato, antes de atualizar a ref remota. Suite selecionada: 163 PASS, incluindo 23 do guard. Tentativas independentes 1 e 2: INCONCLUSIVE, sem motor e sem OCs; nao alegar ACCEPT. O kit permaneceu intacto.

Este fechamento altera apenas documentacao de evidencias; dispensa nova tentativa de verificador por ser somente texto, conforme `agent-kit/verifier/project-contract.md` parte A, item 1. Nenhum efeito de runtime, Docker ou banco foi executado no srv-api. Build/signature da imagem final, HML real, migration e ferramentas PREPARE/ACT continuam pendentes de seus gates. O pacote ZIP de handoff anterior tornou-se desnecessario: a fonte de codigo atual e a main.


### 6.7 Confirmacao posterior de deploy manual em producao (16/11/2026)

**Fonte:** escolha explicita do operador para usar producao e resposta **"Feito, podemos prosseguir no desenvolvimento"** apos receber `git pull --ff-only` e `./infra/scripts/up-prod-sequential.sh --build public-hub`. Registrar como `PROD_PUBLIC_HUB_DEPLOY_OPERATOR_CONFIRMED`. O erro anterior de `.env.hml` ocorreu no checkout produtivo e interrompeu aquela tentativa HML; nao orientamos criar outra configuracao de homologacao no checkout produtivo.

A confirmacao cobre a execucao manual informada, nao comprova por si a revisao OCI, `ImageID`, health ou SHA efetivamente instalado. Esses campos exigem consulta filtrada ao container `delpi-public-hub` e a imagem por ele referenciada; nao consultar Env, mounts, redes ou inspect bruto. Nenhuma nova operacao de deploy foi executada pelo assistente para este registro.

O deploy manual autorizado de metadados nao habilita PREPARE/ACT, nao equivale ao piloto automatizado P3/P4 e nao conclui homologacao dos controles ATLAS. Os registros anteriores de ausencia de deploy sao historicos ao momento daquela entrega. O proximo incremento P2.2g deve comprovar imagem final e origem assinada do pipeline; uma recompilacao no host pode produzir outro artefato mesmo a partir do mesmo commit, logo assinatura de imagem CI nao pode ser atribuida automaticamente a imagem recompilada em producao.

Este registro altera somente documentacao e dispensa nova tentativa de verificador conforme o contrato do kit, parte A, item 1.


### 6.8 Resultado OCI PROD informado pelo operador (16/11/2026)

Saida recebida apos consultas filtradas de container e imagem:

```text
Nome=/delpi-public-hub Estado=running Imagem=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb
Imagem=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb RevisaoGit=03cecb7ed90946c799a66ca9b22b45beb221282e Origem=https://github.com/roberiooliveiradev/delpi-central
```

**Classificacao:** `PUBLIC_HUB_PROD_OCI_METADATA_OPERATOR_REPORTED_PASS`. Nome, estado running, igualdade dos dois ImageIDs, revisao Git completa e origem canonica estao coerentes. SHA `03cecb7ed90946c799a66ca9b22b45beb221282e` corresponde ao fechamento documental posterior ao codigo `65ece2215e83c182269bdfbf1f2e93ce255ba30f`, publicado antes do deploy. Esta e evidencia operacional **informada pelo operador**, sem acesso autonomo ao Docker.

**Limites:** os rotulos OCI sao metadados autoafirmados; nao equivalem a verificacao criptografica. Estado `running` nao comprova health/readiness nem resposta HTTP. O job OCI atual constroi somente `provenance-contract`, nao a imagem `production` completa. O build produtivo foi feito pelo script local no host; uma imagem futura de CI pode ter outro ImageID mesmo com o mesmo SHA por diferencas de dependencias/base. Nao assinar retrospectivamente a imagem do host usando apenas estes rotulos.

**Proximo incremento P2.2g:** CI da imagem final com comprovacao assinada do artefato e validacao do vinculo commit->artefato->imagem em execucao; separar identificador de imagem Docker, digest de manifesto OCI e checksum de arquivo exportado. O comprovante deve corresponder ao artefato efetivamente consumido, sem tratar recompilacao local como o mesmo build. Assinatura, verificador confiavel, journal/migrations, Core grants e aprovacao ainda nao implementados para runtime. Nenhum novo deploy, secret, endpoint ou permissao foi aplicado neste registro. Mudanca apenas documental, dispensando nova tentativa de verificador conforme contrato parte A, item 1.
