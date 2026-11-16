# ATLAS P2.2g | Imagem final e atestacao assinada do Public Hub

**Data:** 2026-11-16. **Estado atual:** PR #193 mesclada; `CI_SIGNED_RELEASE_PASS / PROD_NOT_PROMOTED / HOST_NOT_VERIFIED`. **Owner:** TI DELPI.

## Objetivo e escopo

A P2.2f testava somente a stage `provenance-contract` e adicionava labels informativas. Agora o GitHub Actions valida o codigo do Public Hub, constrói a **stage final `production`**, publica um artefato de release em `ghcr.io/roberiooliveiradev/delpi-public-hub:sha-<git-sha>` **apenas em push na main** e produz a atestacao SLSA in-toto via `actions/attest@v4` com certificado efemero OIDC/Sigstore. O sujeito criptografico e o **digest do manifesto OCI** retornado pelo build/push, nunca somente a label de Git ou o ID de configuracao da imagem Docker.

A PR executa testes, TypeScript/Vite e lint rigoroso de arquivos TypeScript novos/alterados, com inventario separado de erros de lint preexistentes; testa a Docker stage completa e verifica `nginx -t` + `index.html` **sem login GHCR, push ou atestado**. Em main, CI faz push por digest imutavel e valida o digest publicado e sua assinatura com `gh attestation verify`, impondo repo, workflow assinante, source ref `refs/heads/main`, source digest, SLSA v1, emissor OIDC GitHub e exclusao de runners self-hosted. A assinatura e produzida pelo GitHub Actions, nao por HMAC autoafirmado do host.

**Atenção:** o job tem permissoes de `packages: write` e `attestations: write` somente na main. Ele nao publica automaticamente em HML/PROD. O token do workflow precisa poder gravar no GHCR da conta dona; se houver bloqueio de permissao, o CI falha e a entrega de imagem nao deve ser considerada concluida.

## Verificacao read-only no host (depois da existencia da release)

O script `infra/scripts/verify-public-hub-release.sh` recebe **tres parametros fechados** (Git SHA completo, digest OCI de 64 hex e ambiente prod/hml), nao aceita host, URL, nome de container ou comandos arbitrarios. Ele:

1. Usa `gh attestation verify oci://ghcr.io/roberiooliveiradev/delpi-public-hub@sha256:...` e impõe identidade da assinatura com commit e workflow.
2. Requer a imagem **por digest ja instalada no Docker local**; nao faz `docker pull`, build ou deploy.
3. Compara `docker image inspect ... .Id` com `docker container inspect ... .Image` do container fixo, mais labels OCI, Compose service, Compose project HML e estado running.
4. Em caso de erro de assinatura, digest, imagem nao presente, label, estado ou identidade divergente, falha fechado com `[BLOCKED]`.

A invocacao e ilustrativa, com valores **retirados do run de CI correspondente**, nunca estimados:

```bash
bash infra/scripts/verify-public-hub-release.sh '<SHA_COMMIT_40>' 'sha256:<DIGEST_MANIFESTO_64>' prod
```

**Distincao obrigatoria:** `sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` e o **ImageID Docker atual** relatado pelo operador, e **nao** o digest de um manifesto atestado pelo CI. O deploy anterior foi um rebuild local no host; mesmo que labels/revisao coincidam, nao e permitido reaproveitar assinatura de um build futuro para a imagem antiga. A comprovacao so sera PASS quando o container executar os mesmos bytes identificados pelo artefato assinado. Nenhuma implantacao foi realizada neste incremento.

## Testes e gates

- **Execucao simulada local:** testes unitarios de verificador com mock GH CLI/Docker, cobrindo casos positivos PROD/HML e negativos de assinatura, digest, SHA, drift de ImageID, labels, projeto Compose e status. O workflow CI ainda deve confirmar resultado da PR.
- **Gates restantes:** GitHub CI de build real e assinatura na main, permissao GHCR, verificacao no host real com digest da release, smoke HTTP, health/readiness e revisao independente (verificador `delpi-verifier`).
- **Nao alterado:** Dockerfile do Public Hub, Compose, Keycloak, PostgreSQL, scripts de deploy sequencial, gateway, Core, MCP READ, allowlist de deploy, PREPARE/ACT ou a imagem de producao.
- **Risco residual:** a build continua sujeita a dependencias base/npm variaveis. Imagens com mesmo SHA fonte podem ser distintas; a assinatura do digest publicado, e nao a reproducibilidade por si, identifica os bytes aprovados. GHCR package pode ser privado dependendo da configuracao, exigindo autenticacao para verificar.

## Rollback e proximo passo

Esta PR nao altera runtime. Se CI falhar, corrigir com commit novo na branch, sem editar servidor ou assinar imagem local. Uma vez testada e aprovada, o merge pode produzir uma imagem assinada no GHCR; a promocao por **digest fixo** exigira gate futuro, revisao do Compose/fluxo canonico e autorizacao propria. Nao substituir o script de `--build public-hub` atual por um `pull` silencioso. Prosseguir com ownership, restricao do proxy READ, journal/approval e somente entao PREPARE/ACT governados. 

## Correcao do check CI da PR #193 (16/11/2026)

**Diagnostico pelo log da primeira execucao:** [run 43855607278](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43855607278), job de frontend falhou em `npm run lint` com 47 erros e 2 avisos ja existentes no repositorio. Como o script `npm run ci` executava `lint && test && build`, o job abortou antes de qualquer teste Vitest ou compilacao do frontend. A PR so introduz CI, verificador READ, testes de verificador e documentos; **nenhum arquivo de codigo frontend foi modificado** para gerar esse inventario.

**Correcao segura e localizada no workflow da PR:**

1. Executar `npm ci`, `npm run test` e `npm run build` como **gates obrigatorios separados**, bloqueando a release em qualquer falha.
2. Exigir `eslint --max-warnings=0` para **cada TS/TSX adicionado/modificado em `plugins/public-hub`** entre GitHub `base.sha` e o commit testado (PR) ou `before` e o commit testado (push em main). Validar os SHA e a existencia dos objetos Git; negar em erro de diff, arquivo ausente ou lint. Nao excluir fontes alterados dessa verificacao.
3. Executar ESLint global somente para inventario da divida anterior, publicar contagens no resumo do GitHub Actions e falhar se o proprio ESLint nao puder executar/produzir JSON valido. O passivo preexistente **nao desapareceu e nao e classificado como corrigido**.
4. O build Docker final continua condicionado a todos os gates obrigatorios. A publicacao/assinatura permanece exclusiva de `push` em `main`.

**Risco e limite:** a P2.2g nao soluciona os 47 erros anteriores em componentes React. Corrigi-los exige task propria de frontend, regressao visual e review de owners, sem misturar refatoracao com este pipeline de seguranca. O lint global completo continua disponivel por `cd plugins/public-hub && npm run lint` e suas contagens ficam visiveis no CI. Aceite real depende de novo run da PR, e nao de evidencia isolada da etapa antiga. Nenhuma alteracao de producao foi realizada.

### Segunda rodada de CI: contrato dos testes de interface (16/11/2026)

Na [execucao 43857596008](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43857596008), o job OCI de SHA/contexto concluiu PASS, mas a primeira execucao real do Vitest expos **8 falhas / 132 PASS** (140 testes), todas em duas suites preexistentes do Cockpit do Operador. O job interrompeu corretamente o build; **nao** se decidiu dispensar os testes.

Inspecao cruzada de testes, codigo real e output do Testing Library:
- `ProductionRunHandoff.test.tsx` procurava o titulo antigo `Por que a produção parou?`; o componente `DowntimeReasonModal.tsx` realmente renderiza `Informar motivo da parada`. Os cinco seletores legados (incluindo uma assercao negativa) foram alinhados com o titulo existente, **sem mudar o produto** ou remover fluxos de classificacao.
- `CockpitHandoff.test.tsx` verificava somente a existencia da tela de detalhes, o que nao identifica a OP nem demonstra readback coerente. Os positivos agora exigem a identidade da OP B na rota; os cenarios de drift e GET falho exigem a permanencia na OP A. A rotina de montagem de teste limpa o `?view=` herdado, e a recuperacao de run orfao explicita a abertura do detalhe pela fila quando a interface nao navega automaticamente.
- **Nenhum teste foi ignorado, removido ou marcado como `skip`, e nenhuma logica runtime, API, politica de qualidade ou assinatura foi alterada**.

O novo CI da PR deve ainda demonstrar que os 140 testes e a build TypeScript/Vite passam; o merge nao esta autorizado por esta documentacao. Revisao independente, release assinada e validacao de runtime continuam pendentes.

### Fechamento do CI de codigo da PR #193, sem merge (16/11/2026)

**Evidencia no GitHub:** [run 43859759666](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43859759666) no commit `675b5147e53dcc86d00baf6bcb8dd4baaade99f4`, workflow `ATLAS Public Hub OCI Revision and Signed Release`, `completed/success`. Jobs:
- `Full Git SHA label, clean input and negative build gates`: PASS.
- `Public Hub tests, production build and changed-source lint`: PASS, com **140 testes Vitest**, `tsc -b tsconfig.node.json` para configuracao Vite, `vite build` (comando identico ao Dockerfile) e ESLint estrito dos arquivos TypeScript alterados. O inventario global de ESLint permanece separado e nao elimina erros historicos.
- `Build final production image without publishing`: PASS, imagem `production` construida no runner descartavel, com label SHA, `index.html` e `nginx -t` verificados.
- `Build, publish and sign immutable final image (main only)`: SKIPPED por ser PR, conforme isolamento esperado. **Assinatura GHCR ainda nao existe** e imagem de producao nao foi alterada.

**Limite explicito do TypeScript:** `npm run build` do pacote Public Hub inclui `tsc -b` de uma configuracao que resolve codigo de outros projetos, sem as respectivas dependencias instaladas no runner. Foram registrados 1.410 erros de resolucao/tipagem de workspace no log da tentativa (nao demonstram erros novos desta PR), portanto o gate da P2.2g verifica o tsconfig de build e o bundle Vite real, além do build Docker final. **Nao afirmar que typecheck completo de todos os pacotes passou.** O TypeScript integral exige preparacao do workspace e saneamento proprio fora deste incremento.

**Enforcement transversal paralelo:** [run 43859759564](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43859759564) de arquitetura marcou `IMMUTABLE_MIGRATION_MUTATION` para `api-delpi/migrations/plugins/engineering/V024__prc_record_flags.sql`, sem qualquer modificacao nesse arquivo no diff da PR. O checkout do job era um merge virtual do commit `675b...` com `main` em `e76018eea9191b11e64eac3cb43b7839ce72480c`. Essa revisao de main mudou a migration (blob `70cdd37c...` versus `bd11a049...` na base da PR), mas em `3ba6c292f64c82e318a2b4be73c91c4a0e633bfe` ela voltou ao blob `bd11a049...`, confirmado por consulta GitHub. **Nenhum guardrail foi alterado/desativado; reexecutar CI sobre merge virtual atualizado.**

O verificador independente `delpi-verifier`, emissao assinada apos `main`, verificacao no runtime, grants e PREPARE/ACT **ainda nao estao concluidos**. Mesmo com CI verde, a PR permanece rascunho e nao autoriza deploy automatico nem promocao do host.

## P2.2g encerramento no CI: release assinada comprovada (16/11/2026)

**Confirmacoes observadas no GitHub (autoridade CI, nao host):**
- PR [#193](https://github.com/roberiooliveiradev/delpi-central/pull/193) mesclada em `main`, merge commit `139b1eab2cbe95480f95c79c53f52b8ec2e0a791`. O primeiro [run pos-merge 43860978683](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43860978683) bloqueou corretamente a release: 139/140 testes, com um teste intermitente de restauracao do CT-99. Nenhuma imagem assinada foi produzida por esse run.
- Correcao restrita ao **teste** `plugins/public-hub/src/apps/production-control/CockpitHandoff.test.tsx`, commit direto `f81ddd0075de1e4ef8bb68ca58791e9c43e70759`: a assercao antiga checava a ausencia de CT-99 no picker **antes de a enumeracao assíncrona finalizar**, podendo passar prematuramente e deixar CT-63 visivel. A nova assercao aguarda estado positivo `.pcp-pub__hero-code = CT-99`, exige picker CT-63 ausente e confirma que nao aparece botao de detalhes de OP inexistente. Nenhuma funcao runtime modificada ou teste removido.
- [GitHub Actions 43863936825](https://github.com/roberiooliveiradev/delpi-central/actions/runs/43863936825), evento `push`, ref `main`, SHA **`f81ddd0075de1e4ef8bb68ca58791e9c43e70759`**: workflow **completed/success**, jobs `Full Git SHA label...`, `Public Hub tests...`, `Build, publish and sign immutable final image (main only)` com **success**. Os 140 testes Vitest, Vite bundle, lint estrito dos fontes alterados e testes do gate OCI passaram. `Build final production image without publishing` = skipped esperado, pois reservado a PR.
- Publicacao efetiva **GHCR tag `ghcr.io/roberiooliveiradev/delpi-public-hub:sha-f81ddd0075de1e4ef8bb68ca58791e9c43e70759`**. **Digest do manifesto (sujeito assinado): `sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a`**. **Docker image config digest/ID da imagem publicada: `sha256:1a4cfd5d0370e35739cb679d3c0170845e55213488c2c5f7c7d249afba5365a9`**. O manifesto e o ID Docker sao identificadores diferentes e nao podem ser permutados.
- `actions/attest@v4` emitiu atestacao com certificado publico Sigstore, incluiu registro no Rekor e publicou a atestacao em [GitHub Attestation #68104175](https://github.com/roberiooliveiradev/delpi-central/attestations/68104175) e no registry. O step `gh attestation verify` do **mesmo run** concluiu **success**, com `--repo`, `--signer-workflow`, `--source-ref refs/heads/main`, `--source-digest f81ddd...`, emissor OIDC oficial, SLSA v1 e `--deny-self-hosted-runners`.

**Estado operacional separado:** existe evidencia de release publicada/assinada/validada pelo CI, mas **nao existe evidencia de promocao desta release ao srv-api**. A unica leitura de runtime PROD informada anteriormente foi `ImageID=sha256:7ef60f87eb35e004ab5af8d95289a3836e20757d3fba626e14b98c2ad0a48cfb` na revisao `03cecb7ed90946c799a66ca9b22b45beb221282e`. E diferente do ImageID da release assinada. Esse readback anterior nao e observacao atual, e **nao** permite afirmar que a versao produtiva foi alterada, corresponde ao digest assinado ou esta saudavel. Nenhum deploy PROD/HML foi executado pelo assistente neste incremento.

**Gate seguinte P2.2h, ainda nao implementado:** preparar plano versionado, aprovado e fail-closed de **promocao por digest fixo** (sem `docker compose build` local), owner/rollback, readback OCI da imagem efetivamente ativa no container `delpi-public-hub`, health e smoke, verificacao independente `delpi-verifier` e auditoria. O verificador read-only existente pode ser exercitado **apos** a promocao aprovada com:

```bash
bash infra/scripts/verify-public-hub-release.sh f81ddd0075de1e4ef8bb68ca58791e9c43e70759 sha256:4689d4538134e5d9cb9de421569a132f733423f031300f160174e65e9853385a prod
```

**Esperado antes de promocao:** `[BLOCKED]` por ausencia de imagem local vinculada ao digest ou ImageID do container divergente. Isso nao e falha do CI; e bloqueio seguro do gate de runtime. **Nao fazer `docker pull`/deploy como efeito implicito desta verificacao.** PREPARE/ACT, grants Core, migracoes e executor continuam inativos.
