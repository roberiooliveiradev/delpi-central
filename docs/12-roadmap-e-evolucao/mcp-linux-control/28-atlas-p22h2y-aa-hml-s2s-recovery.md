# ATLAS P2.2h.2y-aa | Identidade de coletor S2S, recuperacao e diagnostico HML

**Data:** 16/11/2026. **Estado:** candidato em PR, revisoes pendentes. **PROD/HML:** nao alterados.
**Operacoes:** PREPARE e ACT desabilitados, sem deploy, permissionamento ou grants.

## Objetivo e escopo integrado

PR #218 concluiu a leitura de Core humano fresca antes/depois do diagnostico HML. Este pacote entrega tres responsabilidades conectadas, sem fragmentar em novas micro-PRs:

### Y. Vinculo Keycloak S2S por client e host

O modulo it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_hml_s2s_collector.py utiliza o ServiceTokenValidator compartilhado da Delpi: valida assinatura/JWKS, emissor, audience, expiracao e scope do JWT sob a configuracao oficial de autenticacao. Exige cliente exato allowlisted sob configuracao interna, audience especifica, scope candidato it-portal.atlas.hml.observe, HML/Public Hub, projeto Compose delpi-hml, container delpi-hml-public-hub e host_id fixado. Rejeita token invalido, ambiguidade, escopo do coletor generico, token com vida superior a 15 minutos e deriva do alvo.

**Significado da prova:** um token validado identifica um cliente Keycloak autorizado, NAO autentica isoladamente o processo do host, o sistema operacional, o transporte mTLS, a arvore Git nem o Docker. Host process attested e transport mutual auth attested ficam False. O modulo nao cria clientes, scopes, secrets ou rotas. Testes usam o validador de politica real com decoder JWT simulado; nao sao ensaio criptografico contra Keycloak ao vivo.

### Z. Checklist tecnico de recuperacao sem promover provas

O modulo atlas_deploy_hml_recovery_review.py aceita apenas metadados curtos: referencia de inventario de backup, referencia e data do ensaio restore, referencia/data/ImageID do rollback, referencia/data/hash SHA-256 do review de migracao e dois IDs de pessoas para separacao de papeis. Faz checagens de formato e janela de 72 horas; ImageID de rollback deve corresponder exatamente ao ImageID da base vinda do backend. Referencias nao podem ser URLs ou caminhos arbitrarios.

**Limite:** consistencia documental NAO implica que restauracao, rollback e migracao foram efetivamente testados. Mesmo com metadados completos, os quatro campos de validacao independente continuam False. Nenhum backup e aberto, nenhum binario e executado, nenhum banco ou container e alterado.

### AA. Consolidacao tecnica do HML, sempre bloqueada

O modulo atlas_deploy_hml_technical_admission.py recebe o token S2S somente pelo futuro transporte de backend confiavel (nao por request de usuario), valida a identidade tecnica antes do processamento caro, aciona HMLReadOnlyAdmissionReviewer existente (Core humano fresco 2x, release CI/Sigstore/GHCR, receipt Docker+Git HMAC e challenge PostgreSQL read-only), confere que o JWT do client tecnico nao expirou durante a verificacao e agrega a analise dos metadados de recuperacao.

A saida HMLTechnicalAdmissionBlocked nunca inclui JWT, nonce, senhas, body de receipt ou comandos. Sempre status blocked, prepare_eligible False e can_execute False. A existencia de todos os metadados e provas de cliente permanece insuficiente para PREPARE/ACT.

## Testes e Definition of Done

- tests/unit/test_atlas_deploy_hml_s2s_recovery.py executa validacao S2S por client, audience, scope, token expirado, host nao autorizado, identidade humana e cliente separados, metadados inconsistentes, token expirando durante o Core e resultado upstream adulterado.
- .github/workflows/atlas-p22e-integration.yml inclui os novos arquivos e a suite no job de PostgreSQL descartavel; workflow Docker do pacote anterior preservado.
- CI nao acessa servidor DELPI, Keycloak verdadeiro, GHCR autenticado ou Docker PROD. O decoder JWT e simulado em teste, embora o modulo real use o validador oficial.
- Obrigatorios antes de merge: checks verdes, revisao de seguranca humana e delpi-verifier independente por outro agente.

## Runbook futuro de autorizacao HML, nao executar nesta PR

1. Owner aprova um cliente Keycloak unico itp-atlas-hml-*, audience especifica, scope it-portal.atlas.hml.observe e politica de token curto. Nao reutilizar o client generico de observations nem token humano. Nenhum dos objetos e provisionado por esta PR.
2. TI/Seguranca estabelece identidade OS exclusiva para o coletor (sem sudo, grupo docker, credencial de deploy), com proxy allowlisted estritamente GET de inspect Docker e transporte autenticado separado por host. A validacao JWT de cliente S2S nao substitui seguranca do host ou mTLS.
3. DBA aprova um role SELECT-only novo para challenges, mantendo o role atual it_portal_atlas_journal_reader SEM SELECT nessa tabela. Writer transacional e grants para PREPARE exigem aprovacao separada.
4. Core humano precisa de grant nominativo novo it-portal.deploy.prepare, sem heranca de superadmin. Ainda nao provisionado; os testes nao criam grant.
5. Testes operacionais: restaurar um backup real em ambiente isolado, exercitar rollback por digest ImageID-base e avaliar migrações/compatibilidade reversivel. Gerar evidencias e revisao independente: metadados de referencia nao constituem prova.
6. Piloto HML somente com autorizacao: coletar JWT real validado contra JWKS, comprovar canal S2S/OS, assinar e revalidar nonce em banco, comparar CI + GHCR + runtime. Exercitar negativos (token expirado, grant revogado, Core offline, drift, cliente cruzado, restauracao ausente).
7. Nao habilitar PREPARE ou ACT ate existir writer de nonce one-shot, autorizacao humana fresca, rollback auditado e executor isolado, com revisao independente.

**Conclusao:** contrato de autenticacao S2S + recuperacao + decisao integrada default-off. Nao e deploy, nao e um coletor instalado e nao autoriza uma alteracao no Public Hub.
