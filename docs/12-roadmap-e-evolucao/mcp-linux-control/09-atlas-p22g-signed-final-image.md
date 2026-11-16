# ATLAS P2.2g | Imagem final e atestacao assinada do Public Hub

**Data:** 2026-11-16. **Estado:** candidato em branch/PR; producao nao alterada. **Owner:** TI DELPI.

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
