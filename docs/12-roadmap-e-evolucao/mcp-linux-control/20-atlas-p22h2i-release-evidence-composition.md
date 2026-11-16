# ATLAS | P2.2h.2i: evidencia de release OCI por duas fontes independentes

**Data:** 16/11/2026. **Estado:** candidato em branch e Pull Request. **PREPARE_DISABLED / ACT_DISABLED**.

## Objetivo e fonte de verdade

A PR #209 criou `GitHubOCIProvenanceReader`, que exige uma assinatura GitHub com SLSA v1 e dados fixados para o Public Hub. A PR #210 criou `GHCRImageIdentityReader`, que usa SHA-256 dos bytes de manifesto e identifica o `config.digest` do Docker sem presumir plataforma de um manifesto direto. O hash de **manifesto** não equivale ao ImageID e uma única dessas fontes não valida uma release inteira.

O novo `it_portal_app.infrastructure.persistence.atlas_deploy_oci_release_evidence.OCIReleaseEvidenceReader` chama as duas fontes e só compõe `CIReleaseEvidence` quando ambas se referem ao mesmo commit SHA e digest de manifesto imutável. Não há fonte adicional, token, endpoint ou ferramenta de deploy.

## Contrato de correlação e rejeições

1. Entrada restrita a `commit_sha` hexadecimal minúsculo completo (40 caracteres) e `manifest_digest` SHA-256 do manifesto (64 hex); tags, URLs e abreviações são rejeitadas antes de qualquer leitura.
2. O leitor de proveniência GitHub executa de forma isolada em thread (para não bloquear o event loop). São exigidos os campos e identidades canônicas: `REPOSITORY`, `IMAGE`, `WORKFLOW`, `SOURCE_REF`, SHA do commit, digest OCI, `statement_sha256` de 64 hex e timestamp aware. Se a fonte falhar ou discordar, **não** se lê o registro OCI.
3. GHCR lê novamente o mesmo digest; valida `image` e `manifest_digest` exatos, `image_manifest_digest` e `image_config_id` completos. Apenas `platform=linux/amd64`, confirmada por índice OCI não ambíguo, pode passar. Manifests diretos continuam utilizáveis para observação no módulo anterior, porém não são promovidos a `CIReleaseEvidence` pela etapa atual porque retornam `platform=unverified`.
4. As duas provas devem ter sido observadas nos últimos 120 segundos, com tolerância de no máximo 5 segundos de relógio no futuro. A leitura GHCR não pode ser anterior à prova GitHub por mais de 5 segundos. A saída `CIReleaseEvidence.verified_at` usa o **timestamp mais antigo** para evitar ganho artificial de frescor.
5. Nenhum retorno de exceção de CLI, HTTP, token ou resposta remota é exposto. Todos os erros retornam códigos finitos `OCI_RELEASE_*` fail-closed.
6. `signature_verified=True` é atribuído exclusivamente no adaptador backend após a chamada real do verificador de proveniência, e **não** através de uma flag fornecida pelo solicitante. Ainda assim, a forma de um objeto Python não prova autenticidade: as instâncias dos leitores precisam ser criadas exclusivamente no backend confiável. Não usar a injeção de testes para obter validação produtiva.

## Testes

- Novo `tests/unit/test_atlas_deploy_oci_release_evidence.py` exercita alvos inválidos, derivações de identidade (repo/workflow/source/digest/SHA), respostas de tipo incorreto, erro de verificador, inconsistência do registry, plataformas ambíguas/não verificadas, timestamps obsoletos/futuros, ordenação e falta de timezone, preservação do timestamp mais antigo e repetição de leituras.
- Teste hermético de integração instancia **os leitores de verdade**, mas substitui GitHub CLI e HTTP por retornos falsos: o manifesto index e seu filho são re-hashados, a assinatura DSSE é representada por fixture sintética e a saída é comparada byte a byte. Isso **não é teste de assinatura real**.
- O workflow `.github/workflows/atlas-p22e-integration.yml` roda o novo arquivo junto com os testes já existentes usando PostgreSQL descartável (sem conexão a bancos empresariais).
- CI verde, verificação independente `delpi-verifier` e revisão humana devem ser confirmados separadamente; a integração end-to-end com release real assinada e GHCR ainda não foi demonstrada.

## Restrição de autorização e deploy

A saída não contém permissão para PREPARE, aprovação humana, integridade do checkout de host, migrações, prontidão de rollback ou autorização ACT. Nenhuma API POST, migrations, grants, mudança de infraestrutura ou acesso de escrita ao PostgreSQL são introduzidos. `linux-ops-mcp` mantém `checkout_clean=False`, `migrations_safe=False`, `rollback_ready=False` por projeto. Não modificar esses valores a partir de inferências. O deploy manual e workflows de outros usuários continuam independentes.

## Critérios antes do próximo estágio

- [ ] CI API, PostgreSQL e Docker descartáveis, arquitetura e governança aprovados.
- [ ] Verificador independente `delpi-verifier` executado por outro agente (não comprovável apenas por CI).
- [ ] Realidade do `gh attestation verify` e do read-back GHCR comprovada com release assinada e token de menor privilégio em ambiente autorizado.
- [ ] Evidência independente do host: challenge assinado consumível one-shot, saúde real, rollback/backup e checkout íntegro, ainda não implementada.
- [ ] RBAC Core human + grant de PREPARE e writer DB separado e menor privilégio antes de qualquer rota mutante.

**Próximo incremento proposto:** projetar e validar o caminho **host proof read-only** e os gates de rollback/checkout sem criar endpoints de execução. O ACT permanecerá desabilitado e dependerá de autorização operacional futura.
