# ATLAS | P2.2h.2p-r: pacote read-only para journal, release e readiness

**Data:** 16/11/2026. **Estado:** candidato em Pull Request. **Produção:** inalterada; PREPARE e ACT desabilitados.

## Três capacidades conectadas

**P2.2h.2p: inspeção do challenge real.** O módulo it-portal-api/it_portal_app/infrastructure/persistence/atlas_deploy_challenge_inspection.py implementa SELECT parametrizado em it_portal.atlas_deploy_challenges para o requester_subject UUIDv4, ambiente hml/prod, serviço public-hub e hash SHA256 dos 32 bytes do nonce. Valida emissão, TTL máximo 90s, expiração, consumo e clock_timestamp() do PostgreSQL. Trabalha em transação READ ONLY e retorna apenas snapshot observado, sem reserva, consumo, digest ou nonce. Expirado, desconhecido ou consumido recebe a mesma rejeição. A classe ExplicitChallengeReadOnlyReader é desligada por padrão; exige conexão explicitamente configurada pelo backend, não aceita DSN de request nem usa credenciais do MCP. O papel atual it_portal_atlas_journal_reader NÃO possui SELECT na tabela de challenges. Nenhum GRANT foi feito.

**P2.2h.2q: identidade da release assinada.** O módulo atlas_deploy_readiness_review.py usa o OCIReleaseEvidenceReader privado, já existente, que combina gh attestation verify e leitura de manifesto por SHA-256 no GHCR. Verifica repositório, imagem, workflow fixado, ref main, SHA completo do commit, digest OCI, ImageID e hash do statement. Uma instância Python entregue por browser ou MCP não constitui evidência de assinatura e não deve ser injetada como reader.

**P2.2h.2r: confirmação posterior e status sempre bloqueado.** ReadOnlyReleaseReadinessReviewer faz leitura read-only do challenge antes de acionar GitHub/GHCR e novamente depois. Rejeita consumo, expiração, mudança de emissão/TTL, troca de scope ou retrocesso do relógio. Verifica também frescor da release contra o relógio final do banco (120s, tolerância 5s). Mesmo em cenário consistente produz BlockedReadinessReport, status=blocked, prepare_eligible=False, can_execute=False. Bloqueios obrigatórios: host Git/Docker ainda não autenticado pelo backend, identidade do coletor não atestada, arquivos ignorados/atomicidade, rollback/backup, migrações, Core RBAC, challenge não consumido e PREPARE/ACT desabilitados.

## Testes integrados

- Novo it-portal-api/tests/unit/test_atlas_deploy_readiness_review.py: SQL apenas SELECT, formato de nonce, falha de banco, ausência de configuração, requesters diferentes, CI drift, assinaturas/clock/staleness, segunda leitura divergente, concorrência e confirmação de bloqueio permanente.
- it-portal-api/tests/integration/test_atlas_postgres_journal.py ganhou testes com PostgreSQL 16 realmente descartável: múltiplas consultas sem alteração, requester/ambiente isolados, nonce consumido e expirado entre consultas. As simulações DML ocorrem exclusivamente no banco de teste criado pelo GitHub Actions, nunca em HML/PROD.
- .github/workflows/atlas-p22e-integration.yml executa os testes novos no job PostgreSQL e dispara nos arquivos do pacote.

## Fronteiras que permanecem

Duas leituras SELECT não reservam o nonce nem impedem outra sessão de consumi-lo imediatamente após a última observação. O consumo deve ser único na futura transação governada de PREPARE. Nesta fase não há endpoint, alteração de schema, grants, role, secrets, Keycloak, migração, Docker socket, serviço Linux, deploy ou aprovação. A ferramenta GitHub/Sigstore ainda exige teste operacional real em ambiente autorizado, e a prova host não está transportada para o backend.

A futura entrega, sob aprovação do owner, deve reunir identidade de serviço e transporte autenticado do coletor, revisão dos grants do PostgreSQL e Core human RBAC, verificação real de OCI e do estado de backup, rollback e migrações, antes de qualquer POST PREPARE. ACT permanece fase posterior com autorização independente.

## Portões de aceite

- [ ] Cinco checks GitHub Actions verdes, incluindo PostgreSQL real descartável.
- [ ] Revisão independente delpi-verifier por outro agente e revisão humana.
- [ ] Teste operacional com assinatura GitHub/GHCR real, sem deploy ou escrita.
- [ ] Autorização separada para papel SELECT-only e host transport em HML.
- [ ] Verificação que nenhum serviço, script, schema ou grant de produção foi alterado.

**Classificação:** diagnóstico técnico default-off, não candidato aprovado para implantação.
