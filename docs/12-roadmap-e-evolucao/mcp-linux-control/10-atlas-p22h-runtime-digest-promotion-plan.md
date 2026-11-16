# ATLAS P2.2h | Plano de promoção por digest OCI e comprovação de runtime

**Data:** 2026-11-16  
**Status:** `RUNTIME_DRIFT_OPERATOR_CONFIRMED / PREFLIGHT_CODE_PASS / COMPOSE_PIN_OPTION_READY / ACT_DISABLED / PROD_UNTOUCHED`  
**Owner:** TI DELPI.  
**Escopo deste incremento:** plano de pré-implantação, sem script de execução, aprovação, alteracao de Compose, container, banco ou gateway.

## 1. Evidência operacional e decisão

O operador executou duas consultas `docker inspect` em produção e forneceu o retorno abaixo. É evidência de leitura humana enviada ao ATLAS, e não observação independente do coletor:

```text
Nome=/delpi-public-hub Estado=running ImageID=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb
RevisaoGit=03cecb7ed90946c799a66ca9b22b45beb221282e
```

O CI `main` em [run 43863936825](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43863936825) publicou e atestou o artefato final:

| Propriedade | Valor aprovado no CI |
|---|---|
| Commit de origem | `f81ddd0075de1e4ef8bb68ca58791e9c43e70759` |
| Imagem | `ghcr.io/roberiooliveiradev/delpi-public-hub` |
| Manifest digest (sujeito atestado) | `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a` |
| Docker image config ID | `sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9` |
| Prova | [Sigstore/SLSA attestation #68104175](https://github.com/roberiooliveiradev/delpi-central/attestations/68104175) |

**Conclusão comprovada:** o container rodando usa `ImageID` diferente do artefato assinado, e sua label aponta para commit antigo. A resposta do Docker informa `running`, mas **não prova** health/readiness/HTTP, nem autoriza substituição. A imagem CI não foi instalada pelo ATLAS.

## 2. Por que o mecanismo atual não promove uma imagem assinada

O serviço `public-hub` em `infra/docker-compose.yml` é **build-only** (`build.context=../plugins`, `target=production`) e não declara `image:` pinada. O `infra/scripts/up-prod-sequential.sh --build public-hub` executa `docker compose build` localmente e depois `up -d --no-deps`. Esse fluxo **reconstrói bytes diferentes** do artefato do CI, mesmo quando `org.opencontainers.image.revision` coincide. Não usar `--build` como substituto de promoção.

**Risco de execução direta:** `docker run` avulso ou `docker stop/rm` manual desfaz a gestão Compose, produz drift e não estabelece rollback, dependências ou smoke. Também não se pode criar um quarto Compose/overlay temporário: o inventário de Compose/env é fechado.

## 3. Mudança mínima proposta para o próximo incremento de código (não implementada)

1. Evoluir **o Compose canônico** para suportar duas modalidades explícitas no serviço existente: build local legado como default e consumo da **imagem CI por manifesto digest fixo** somente sob uma configuração de release **validada e versionada**. Nunca criar um segundo serviço com o mesmo `container_name`, um arquivo Compose paralelo ou tag flutuante `latest`.
2. Evoluir `up-prod-sequential.sh` **sem alterar os serviços restantes**, adicionando modo específico de promoção `public-hub` que desabilita build, valida inputs SHA/digest e versão base aprovada, verifica CI/Sigstore e impede efeito em outros serviços. Rejeitar qualquer alargamento de alvo/ambiente/argumentos. O modo padrão `--build` dos outros serviços fica preservado.
3. Fazer **preflight de leitura** no host, com conferência de estado atual, serviço Compose, disponibilidade de credenciais GHCR de leitura, integridade do digest e atestação OIDC GitHub. Nunca permitir variáveis com comandos/shell nem ler/imprimir token de autenticação.
4. Criar **plano selado**, identidade e autorização nominativa externa ao ChatGPT, janela, avaliação de risco, registro da imagem anterior para rollback e bloqueio em caso de drift desde o preflight; verificar também que `main` contém o commit autorizado. Permissões Core, journal e executor isolado permanecem pré-requisitos para ACT automatizado.
5. Somente depois de aprovação e implementação validada: pull por digest, ativação de **um único serviço** sem rebuild, readback da configuração do Docker em uso, resultado de `infra/scripts/verify-public-hub-release.sh` PASS e smoke HTTP da rota real. Conferir saúde de gateway e dependências, não inferir health só de `running`.
6. Se falhar antes da ativação, **não alterar container**; se falhar depois, bloquear novos deploys, preservar logs mínimos sanitizados, reconciliar estado e executar apenas rollback aprovado e comprovadamente compatível. Preservar a imagem anterior antes de qualquer troca.

**Requisitos não negociáveis:** não editar `infra/.env` diretamente por agente, não executar pull/build/deploy via MCP READ, não ligar PREPARE/ACT, não emitir aprovação por chat. Configuração de release precisa respeitar `.cursor/rules/local-first-deploy.mdc` e `platform-delivery-runtime-operations.mdc`.

## 4. Gate de testes para a implementação

- **No-op/dry-run:** produzir plano sem tocar Docker, banco, rede produtiva ou arquivo de runtime.
- **Caminho positivo isolado:** em CI descartável, provar que o Compose usa o digest exato ao ativar um serviço sintético, com `docker inspect` por digest e sem construir outra imagem.
- **Negativos obrigatórios:** SHA abreviado, digest inválido, assinatura do workflow errado, repo ou ref divergente, sem permissão GHCR, tag móvel, imagem fora da allowlist, containers diferentes, serviço Compose indevido, HEAD sujo, drift de ImageID, falta de rollback, health insuficiente, conflito de concorrência, aprovação ausente/expirada, erro de pull, timeout e troca parcial.
- **Integridade:** não tratar `manifest digest` como `ImageID`; não herdar assinatura de rebuild local; não usar status `running` como smoke.
- **Transversal:** testes do script e Compose, `docker compose config`, gates de arquitetura/segurança, verificação independente `delpi-verifier`, evidência de aprovação e revisão da configuração de rollback.
- **Prova operacional futura:** comparar `sha256:1a4cfd...` com o `ImageID` realmente em uso, não apenas com uma imagem baixada no cache do host. O verificador P2.2g é READ e falha até essa igualdade ser comprovada.

## 5. Estado agora

`P2.2g: CI_SIGNED_RELEASE_PASS`; `P2.2h: READBACK_DRIFT_CONFIRMED / PROMOTION_PENDING_GATES`. A única mudança atual é **documentação**. Sem CI de código novo, sem operação de container, sem update do ATLAS MCP ou de permissões. A etapa subsequente é o desenvolvimento do modo de promoção e seu teste isolado, seguido de revisão e aprovação **antes** do primeiro uso real em produção.

## 6. Incremento P2.2h.1: seleção opcional do artefato e preflight fail-closed (16/11/2026)

### Codigo integrado em `main`

- `infra/docker-compose.yml`: `public-hub.image=${PUBLIC_HUB_RELEASE_IMAGE:-${COMPOSE_PROJECT_NAME:-infra}-public-hub}`. Sem override, mantém o nome local equivalente ao padrão `projeto-serviço` do Compose. Com override **somente por executor autorizado no futuro**, aceita referência de imagem por digest; `build`, `container_name`, rede e dependências permanecem os mesmos.
- `infra/docker-compose.hml.yml`: `image=${PUBLIC_HUB_HML_RELEASE_IMAGE:-delpi-hml/public-hub:local}`, preservando a identidade local de HML. Producao e HML mantêm nomes diferentes e perfis isolados.
- Scripts canônicos `up-prod-sequential.sh` e `up-hml-sequential.sh`: **forçam as variáveis de override vazias** ao lidar com Public Hub. Portanto, o deploy sequencial legado não pode habilitar implicitamente uma release assinada. Os arquivos de exemplos canônicos documentam valores vazios por padrão. Nenhum novo Compose ou `.env` alternativo foi criado.
- `infra/scripts/public-hub-release-preflight.sh`: novo comando **somente leitura**, com enum fixo `prod|hml`, SHA Git completo, digest OCI completo e `ImageID` esperado do estado anterior. Verifica atestação do GitHub com issuer, signer workflow, ref main e SHA, compara `ImageID` real do container, estado `running`, labels Compose e revisão OCI; imprime um hash de plano **apenas informativo**, sem aprovar ações. `--apply` é rejeitado antes de qualquer chamada. Nenhum `docker pull`, `build`, `tag`, `up`, `stop`, `rm` ou SSH.
- `infra/scripts/tests/test_public_hub_release_preflight.py`: **22 testes** de caminho positivo simulado, assinatura negada, drift de ImageID, arquivo de contrato Compose, projeto inadequado, container parado, SHA/digest malformado e tentativa de `--apply`.
- `.github/workflows/atlas-public-hub-p22h-preflight.yml`: CI offline dedicado. Executa os testes via mocks e usa `docker compose config` em runner GitHub para renderizar **PROD e HML**, cada um com imagem local padrão e override imutável por digest, sem criar contêiner, pull ou deploy. Requer explicitamente `--profile public-hub` em HML (descoberto e corrigido na primeira execução).

### Evidências

- **Local isolado:** `pytest -q` dos 22 testes em ambiente sem Docker/GH real: 22 PASS, com stubs do contrato Compose. `bash -n` do novo script PASS. Confere lógica do pré-verificador, mas não é evidência de assinatura acessível ao host.
- **GitHub Actions:** [ATLAS P2.2h run 43871507381](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43871507381) concluiu com `success`: job de 22 testes e regressão de proveniência, mais renderização real de Compose PROD/HML, local e pinado.
- **Architecture Enforcement:** verificar o status final do run [43871507384](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43871507384). Não confundir aprovação do CI com revisão independente do `delpi-verifier`.
- **Verificador independente:** não disponível no ambiente do executor desta sessão; **não executado**. A revisão deve ser feita antes de autorizar execução do novo caminho produtivo.
- O workflow de release original para o commit de configuração `3869d8db846ed320d492b79cd9c71fcf7383a56e` falhou em um teste Vitest preexistente e intermitente `PostActivity.test.tsx` (139/140); a imagem anteriormente assinada para `f81ddd...` permanece válida. Nenhuma nova assinatura foi presumida.

### Consulta futura somente leitura, no checkout atualizado

```bash
bash infra/scripts/public-hub-release-preflight.sh --plan prod \
  f81ddd0075de1e4ef8bb68ca58791e9c43e70759 \
  sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a \
  sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb
```

Esse comando **não altera** containers, baixa imagem, nem consome credenciais com permissão de escrita, mas requer `gh` autenticado para ler as attestations e Docker CLI/inspect. `[PLAN_OK_NO_DEPLOY]` apenas indica que a proveniência no GHCR foi validada e o estado local não mudou desde a leitura enviada pelo operador; **não significa** `PROMOTION_APPROVED`, `HOST_PROVENANCE_PASS`, health ou readiness. Se o ImageID tiver mudado, bloquear, nunca ajustar silenciosamente o valor esperado.

### Próximos gates

`P2.2h.2`: integrar backend Core, journal com aprovação nominativa fora do ChatGPT e executor isolado. Validar rollback, smoke e `verify-public-hub-release.sh` no **container realmente ativado**. Somente com gates externos, verificador independente e aprovação do owner se poderá implementar/usar ACT. O estado continua `ACT_DISABLED`; o código atual **não oferece execução de deploy**.


## 7. Validacao real em PROD pelo operador (16/11/2026)

**Fonte:** retorno do terminal de producao enviado pelo operador; nao equivale a uma observacao assinada e fresca pelo backend. A execucao real de `public-hub-release-preflight.sh --plan prod` retornou **[PLAN_OK_NO_DEPLOY]**:

- Ambiente `prod`, container `delpi-public-hub`, projeto Compose `infra`, status running durante a verificacao.
- `current_ImageID=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` e `current_revision=03cecb7ed90946c799a66ca9b22b45beb221282e`.
- Origem CI verificada: commit `f81ddd0075de1e4ef8bb68ca58791e9c43e70759`, manifest digest `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`.
- Checksum informativo do plano: `17f1730c4b5798168ca35c215b3e66f3947fdb998b82328219f03ed0d1e07110`. **Nao e aprovacao, segredo, token, proposta persistida nem prova host assinada.**
- Resultado de seguranca exato: `promotion=BLOCKED approval=NOT_IMPLEMENTED readiness=NOT_VERIFIED rollback=NOT_VERIFIED`.

**Conclusao:** `PREFLIGHT_PROD_PASS_OPERATOR_REPORTED`. A assinatura da release foi validada e nao houve drift do ImageID observado. A imagem atual ainda difere do ImageID da release assinada, `sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9`. **Nao declarar HOST_PROVENANCE_PASS, readiness, implantacao ou rollback testado. Nenhum deploy foi feito.**

## 8. Lacuna de seguranca a resolver em P2.2h.2

Inspecao do codigo existente em `main`:

- `linux-ops-mcp/linux_ops_mcp/deploy_policy.py`: politica pura/deny-by-default, preview e TTL de 10 min, sem tool ACT.
- `linux-ops-mcp/linux_ops_mcp/deploy_host_source.py` + `deploy_host_receipt.py`: leitura de observacao e verificacao de recibo com challenge; nao substituem assinatura da release nem aprovacao.
- `it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_journal.py`: PREPARE transacional inerte e idempotente, sem API ativa.
- `docs/12-roadmap-e-evolucao/mcp-linux-control/05-atlas-p22d-candidate-schema.sql`: DDL candidato, **nao aplicado em producao**.

**Gap confirmado:** o contrato `PrepareIntent` e o DDL candidato contêm `target_sha`, `base_sha`, `proposal_hash` e challenge, mas **nao vinculam explicitamente digest de manifesto OCI assinado, ImageID anterior esperado, ImageID da release nem identidade de atestacao CI**. O checksum informativo do preflight nao deve ser reutilizado como autorizacao. Antes de qualquer ACT:

1. Revalidar a identidade de solicitante/aprovador e RBAC separado via owner Core/IT Portal, sem aceitar evidencias fornecidas pelo modelo como autoridade.
2. Incorporar SHA completo, digest assinado, ImageID atual esperado, ImageID da release e evidencia CI/host fresca **no hash canonico e journal transacional**; negar replay ou campos divergentes, inclusive sob concorrencia.
3. Obter autorizacao nominativa no portal fora do ChatGPT, com expiracao/revogacao e verificacao de permissao no ato de execucao.
4. Construir executor isolado, primeiro em HML, que revalide todos os gates, preserve rollback e use somente digest imutavel, com readback e smoke reais. Nao habilitar PREPARE/ACT antes da revisao independente e teste de rollback.

**Proximo incremento de codigo sugerido:** atualizar o contrato de proposta e testes de politica/journal, com PostgreSQL descartavel no CI, **sem publicar endpoint ou migracao PROD** ate alinhamento de ownership. Este registro e apenas documental, sem mutacao de runtime ou codigo.
