# ATLAS | P2.2h.2g: verificador de proveniencia OCI de assinatura GitHub

**Data:** 16/11/2026. **Estado:** candidato em Pull Request, verificacao CI e revisao independente pendentes. **Sem PREPARE/ACT.**

## Motivacao

A PR #208 integrou a verificacao do nonce one-shot no journal. A V016 e a tela de consulta do journal estao visiveis em producao conforme evidencia do operador, mas nao existe fonte independente que gere `CIReleaseEvidence` autentica. Afirmar `signature_verified=True` numa dataclass nao comprova assinatura nem autoriza implantar. Este incremento cria a primeira fonte real, limitada a **verificacao de proveniencia de manifesto OCI**.

## Implementacao proposta

- Modulo privado `it_portal_app.infrastructure.persistence.atlas_deploy_oci_attestation` com `GitHubOCIProvenanceReader`; nenhuma rota, tarefa ou comando MCP registra ou chama este modulo.
- Executa **`gh attestation verify`** como processo independente (argv estatico, `shell=False`), exigindo GitHub CLI **2.97.0 ou superior**. O binario deve ser instalado e administrado pelo owner; ausencia, versao antiga, comando com retorno diferente de zero, timeout e erro sao **fail-closed**.
- Autoridades **fixas em codigo**: `roberiooliveiradev/delpi-central`, `ghcr.io/roberiooliveiradev/delpi-public-hub`, workflow de build OCI, `refs/heads/main`, issuer OIDC da GitHub Actions, predicate SLSA v1 e proibicao de self-hosted runner.
- Apenas dois parametros de selecao: SHA de commit com 40 hexadecimais minusculos e digest imutavel `sha256:<64hex>`; os dois sao validados antes de executar o processo. As flags `--bundle` e `--bundle-from-oci` nao sao aceitas, priorizando a prova recuperada pelo GitHub.
- Credencial deve vir de segredo de **backend**, nunca de request/ChatGPT; ambiente do subprocesso e restrito para nao aceitar `GH_HOST`, `PATH` e configuracao arbitrarios. Sem logs de stdout/stderr. Timeout, limite de saida e validacao JSON estrita.
- Exige um resultado de verificacao, certificado, timestamps, `verificationResult.statement` coerente com DSSE assinado, subject OCI e digest exatos. Retorna `VerifiedOCIStatement` contendo o SHA-256 dos bytes originais da declaracao e o horario da verificacao. **Nao** retorna `CIReleaseEvidence`, pois o campo `image_config_id` requer uma segunda leitura confiavel do registro OCI.
- Testes unitarios usam somente runner falso, validando o comando de verificacao, negacoes, assinaturas/subjects divergentes, formatos invalidos, duplicidade JSON, limites e ausencia de execucao.

## Limites de confianca

A verificacao criptografica e feita por `gh attestation verify`, nao pelo parser Python. O parser apenas confere se os **bytes originais declarados como verificados** correspondem ao documento retornado e ao alvo fixo. O `predicate` do SLSA pode conter dados controlados pelo workflow e nao comprova por si so o estado do host. Exigir CI de pipeline confiavel e complementar com read-back do registro OCI.

O comprovante atual `linux-ops-mcp/deploy_host_signer.py` mantem `checkout_clean=False` propositadamente; `deploy_host_receipt.py` tambem preserva `migrations_safe=False` e `rollback_ready=False`. **Nao elevar essas garantias por inferencia.** Precisamos de prova independente de workspace limpo, prontidao de rollback, estado real da aplicacao e grants do Core antes do POST PREPARE.

## Testes e requisitos de revisao

- CI de `.github/workflows/atlas-p22e-integration.yml` deve rodar os testes unitarios novos dentro do job PostgreSQL descartavel, sem acesso a PROD.
- Revisor independente `delpi-verifier` com outro modelo continua obrigatorio antes de considerar a entrega totalmente aprovada. Os checks do GitHub nao substituem essa revisao.
- Ainda sem teste end-to-end com CLI instalado e manifesto OCI real. Antes de conectar ao backend, testar com uma assinatura real usando identidade/credencial do servidor governadas e versao de CLI corrigida.
- Nenhuma migracao, permissao, segredo, endpoint POST, deploy Docker, ACT, alteracao dos scripts `up-*` ou mudanca na `main` por esta PR.

## Proxima etapa

Verificar o `image_config_id` real do manifesto assinado com leitura de registro confiavel (image manifest != image config digest), integrar comprovante host com verificacao independente e challenge DB, criar RBAC `it-portal.deploy.prepare` nominativo, papel DB de escrita de menor privilegio, gates e logs de auditoria. Depois projetar o POST PREPARE default-off; **ACT somente em fase posterior com autorizacao explicita**.
