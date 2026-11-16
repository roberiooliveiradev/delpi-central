# ATLAS | P2.2h.2s-u: evidencias completas entre Linux e Portal TI

**Data:** 16/11/2026. **Status:** candidato em Pull Request. **PROD:** nao alterada.

## Objetivo

As PRs #215 e #216 entregaram os recibos assinados de Git/Docker e a verificacao da release OCI com o challenge do journal, mas esses dois conjuntos estavam separados por uma fronteira de processo. O pacote atual implementa um contrato de interoperabilidade para o BFF e um diagnostico combinado. Nao cria transporte HTTP, worker, credenciais, novo Core grant ou acao de implantacao.

## S. Contrato e verificacao independente no Portal TI

Modulo: it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_host_receipt_bridge.py.

- Valida HMAC-SHA256 nos bytes exatos dos recibos Docker v2 e Git v1 emitidos pelo Linux. Exige dominios criptograficos diferentes, chaves de ao menos 32 bytes, distintas e administradas pelo backend e coletor confiaveis. Atestacao de quem detem a chave precisa ser provada independentemente antes de uso operacional.
- Valida JSON com campos estritos e sem duplicatas, limite de 3072 bytes, SHA completo, ImageID completo, nonce de 32 bytes, campos de estado booleanos, timestamp UTC ate 90 segundos e tolerancia de 5 segundos.
- Exige alvo backend-owned. Public Hub em HML usa container delpi-hml-public-hub no projeto delpi-hml; em PROD usa container delpi-public-hub no projeto infra. Host, servico, ambiente e nonce sao verificados por ambas as assinaturas.
- A imagem do Docker tem que coincidir com o release record assinado e com a base OCI informada por autoridade do backend. Detecta commit Git diferente do runtime, branch Git diferente de main, checkout sujo, runtime nao saudavel e distancia temporal das provas acima de 15 segundos.
- VerifiedWireHostPair registra apenas hashes de receipts, observacoes e motivos de bloqueio. Nao leva segredos nem nonce bruto. A integridade HMAC nao comprova identidade OS, integridade de arquivos ignorados ou snapshot atomico do checkout, por isso collector_identity_attested, checkout_integrity_attested e prepare_eligible ficam falsos.

## T. Diagnostico completo, permanentemente bloqueado

Modulo: atlas_deploy_full_readiness.py.

- Reaproveita ReadOnlyReleaseReadinessReviewer da PR #216: SELECT antes/depois do nonce, proveniencia verificada GitHub/Sigstore, digest imutavel e ImageID extraido do GHCR.
- Exige alvo OCI diferente da base e coerencia de ambiente e servico. Valida os comprovantes HMAC do Linux sob o relogio obtido do PostgreSQL.
- Executa terceira leitura SELECT do challenge depois da verificacao dos recibos, exigindo que continue ativo com o mesmo TTL. Essa terceira leitura reduz algumas corridas, mas nao impede o consumo do nonce por outro processo logo depois.
- FullReadinessBlocked sempre devolve status blocked, prepare_eligible=False, can_execute=False, core_permission_verified=False, host_collector_identity_attested=False, one_shot_challenge_consumed=False, backup_and_rollback_verified=False e migrations_safe=False. Sem proposal_id, sem escrita, sem habilitacao de PREPARE/ACT.
- Diagnostico desligado por padrao, sem rota, job, MCP tool, DB writer, secret, grant ou migration. O codigo nao acessa host por SSH, Docker socket ou shell.

## U. Testes de interoperabilidade e gates

- it-portal-api/tests/unit/test_atlas_deploy_full_readiness.py cobre assinatura, troca de chaves, adulteracao, replay, identidade host, ImageID, SHA, envelhecimento de prova, clocks, mudancas em nonce e falhas da terceira leitura.
- linux-ops-mcp/tests/test_atlas_cross_context_host_contract.py cria repositório Git temporario, usa assinadores REAIS do Linux (issue_git_checkout_witness e issue_host_runtime_receipt_v2, com Docker simulado) e passa os bytes diretamente ao verificador real do Portal TI. Rejeita replay, stale e base divergente. Nao toca servidor da DELPI.
- Workflow atlas-p22e-integration.yml aciona novos testes em PostgreSQL descartavel, Docker efemero e suites existentes. Revisao independente delpi-verifier e revisao humana continuam gates separados do CI.

## Roteiro operacional necessario antes de qualquer ativacao (NAO EXECUTAR NESTA PR)

1. **Responsabilidade:** owner do Portal TI, seguranca e responsavel pelo Linux aprovam o desenho da autoridade e um segundo agente faz revisao independente. Confirmar alvos hml e prod, sem modificar apps de terceiros.
2. **Coletor do host:** processo dedicado com identidade OS de leitura minima; sem sudo, chaves de deploy, acesso Docker irrestrito ou tokens de escrita. Se Docker for necessario, aprovar proxy que exponha somente GET de inspect para container fixado. Nenhum socket bruto deve ser montado em MCP/API.
3. **Transporte:** canal autenticamente ligado ao host/coletor, com identidade de maquina revisada e allowlist. HMAC sozinho so prova conhecimento da chave. Nunca receber chaves, DSN, target ou codigo de origem de HTTP/MCP/browser.
4. **Banco:** papel existente it_portal_atlas_journal_reader continua SEM SELECT na tabela de challenges. Qualquer credencial SELECT nova precisa de aprovacao DBA; writer de PREPARE exige role separado, grant minimo, transacao one-shot e idempotencia testada. Nada sera configurado nesta PR.
5. **Core:** grant it-portal.deploy.view nao basta. Futuro it-portal.deploy.prepare nominativo precisa de revisao de RBAC fresca, auditoria e autorizacao do owner. O executor ACT requer permissao e etapa operativa separadas.
6. **Recuperacao:** backup/restauracao real, rollback a ImageID anterior, evidencia de compatibilidade de migracoes e plano de contingencia devem ser verificados por autoridade independente; health Docker nao e prova de recuperacao.
7. **Validacao HML:** teste negativo de chave errada, replay, Git sujo, falha GHCR, target desviado, challenge expirado, usuario sem grant, indisponibilidade do coletor e rollback sem evidencia. Nenhum caso deve persistir proposta ou acionar deploy.

## Portoes da PR e riscos remanescentes

- [ ] 5 checks GitHub Actions aprovados.
- [ ] delpi-verifier independente e revisao humana com veredito, sem confundir com CI.
- [ ] Compatibilidade de HMAC confirmada com os assinadores reais em fixtures descartaveis.
- [ ] Identidade OS e canal entre Portal TI e Linux seguem nao implementados: nao habilitar recebimento de provas reais.
- [ ] Testes de rollback/restore, migracoes, autorizações Core e policy final aprovados antes da futura API PREPARE.
- [ ] ACT continua desabilitado ate aprovacao expressa, mesmo depois de PREPARE.

**Escopo entregue:** contrato backend, diagnostico read-only inerte, testes e roteiro de seguranca. **Escopo ausente:** integracao produtiva com host, reserva/consumo de challenge, proposta persistida, habilitacao de PREPARE ou ACT.
