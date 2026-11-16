# ATLAS P2.2h | Plano de promoção por digest OCI e comprovação de runtime

**Data:** 2026-11-16  
**Status:** `RUNTIME_DRIFT_OPERATOR_CONFIRMED / PROMOTION_NOT_IMPLEMENTED / PROD_UNTOUCHED`  
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
