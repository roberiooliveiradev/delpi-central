# ATLAS | P2.2h.2d: V016, RBAC Core e habilitação de consulta

**Data:** 2026-11-16.  
**Status:** `PREPARED_IN_PR`, **sem migração em HML/PROD, sem concessão Core, sem ativar flag nem ACT**.  
**Owner:** TI / PostgreSQL / Core.

## Evidência de produção informada pelo operador

- `delpi-it-portal-api` saudável, endpoints `/atlas/deployments` e `/atlas/deployments/{proposal_id}` presentes na OpenAPI após merge da PR #205.
- `settings.ATLAS_JOURNAL_READ_ENABLED=False` comprovado no container.
- Consulta somente leitura ao banco atual retornou `None` para `it_portal.atlas_deploy_proposals`, `it_portal.atlas_deploy_oci_bindings` e `it_portal.atlas_deploy_events`. Não há journal instalado; o frontend intencionalmente não oferece menu até a permissão e flag estarem ativas.

## Artefatos preparados

1. `it-portal-api/migrations/V016__atlas_deploy_oci_journal.sql`: migração versionada, baseada nos DDLs candidatos `05-atlas-p22d-candidate-schema.sql` e `12-atlas-p22h2b-disposable-oci-bindings.sql`. Cria **quatro** tabelas (challenges, proposals, events, OCI bindings), índices e guards OCI imutáveis. Não cria contas nem concede privilégios; revoga permissões públicas.
2. `migrations_runner.py` só executa V016 quando `IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED=true`. O nome exato é protegido; se a flag estiver ausente ou `false`, o runner continua aplicando migrações normais e **não marca V016 como aplicada**. Checksums de migrações anteriores seguem verificados. Compose atual inicia migrações convencionais por padrão, portanto esta segunda trava é indispensável.
3. `plugins/it-portal/it-portal.manifest.json` versão `0.3.5`: publica o código `it-portal.deploy.view` e a rota interna `/apps/it-portal/atlas-deployments`, `showInMenu=false` no Core (navegação interna é dinâmica). **Manifesto em Git não é cadastro nem concessão de permissão em produção**.
4. `infra/docker-compose.yml` e `infra/.env.prod.example`: propagam quatro variáveis de ativação; ambas flags `false` por padrão. `IT_PORTAL_ATLAS_JOURNAL_READ_DB_USER` e `...PASSWORD` ficam vazias até provisionamento.
5. O BFF usa **somente a identidade PostgreSQL dedicada para SELECT**. Se login/pwd estão ausentes ou se o login é igual à conta de escrita da API, a consulta falha com 503, sem fallback. A conexão exige `default_transaction_read_only=on`; as queries também abrem transação READ ONLY.

## Ordem para liberação, somente após revisão e autorização

**Fase 0.** Obter revisão independente `delpi-verifier`, CI da API/UI/PostgreSQL, validação de conflitos com roadmap Delpi Remote e aceite explícito dos owners Core/PostgreSQL. Verificar `main` e estado do checkout antes de qualquer deploy. Não executar SQL de `docs/...` no banco real.

**Fase 1: preflight PostgreSQL (somente leitura).** Confirmar última versão registrada (V015 ou superior), schema `it_portal`, role da API, estado do cluster, janela de mudança e ausência de V016; produzir backup seguro `pg_dump -Fc -n it_portal` e verificar o inventário do dump com `pg_restore -l`. A V016 só deve ser executada pelo **runner versionado** na janela aprovada; evitar copiar e colar os DDLs de teste.

**Fase 2: aplicar V016 conscientemente.** Sob plano de mudança revisado, habilitar temporariamente `IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED=true` em conjunto com o procedimento já aprovado do runner, **apenas** para a execução versionada. Confirmar registro do checksum V016 e existência das quatro tabelas/triggers. Restabelecer a flag como `false` após o procedimento. Se falhar, interromper sem reexecutar scripts de teste e preservar logs/backup. Migração aditiva permanece sem `DROP` automático como rollback; recuperação deve seguir plano do DBA.

**Fase 3: role DB somente leitura.** DBA cria login PostgreSQL específico, com credencial forte em armazenamento de segredos do ambiente (nunca no Git ou chat). Exemplo de GRANTs **para revisão pelo DBA**, NÃO executar automaticamente:

```sql
-- Executar SOMENTE com role de administração aprovada e V016 já aplicada.
-- Nome ilustrativo; não colocar senha ou CREATE ROLE em código da aplicação.
GRANT USAGE ON SCHEMA it_portal TO it_portal_atlas_journal_reader;
GRANT SELECT ON
  it_portal.atlas_deploy_proposals,
  it_portal.atlas_deploy_oci_bindings,
  it_portal.atlas_deploy_events
TO it_portal_atlas_journal_reader;
-- Não conceder SELECT em it_portal.atlas_deploy_challenges.
```

O DBA valida com usuário leitor que os três SELECTs passam, challenges negam, tentativas INSERT/UPDATE/DELETE são negadas, e a role não pertence à API. Só então configurar `IT_PORTAL_ATLAS_JOURNAL_READ_DB_USER` e `...PASSWORD` em `infra/.env` protegido, no servidor aprovado.

**Fase 4: Core RBAC.** No Portal Admin, ir em **Aplicações → Portal de TI → Manifesto → Publicar nova versão**. Registrar o manifesto estrutural `0.3.5` via fluxo oficial (não um PUT cosmético). Conferir que `it-portal.deploy.view` foi registrado e conceder **somente ao perfil/usuário autorizado**, associado a `it-portal.access`. O código não concede permissões a todos nem atribui aprovação/execução.

**Fase 5: habilitar consulta.** Somente depois da V016, login read-only, Core e smoke de 403/503: configurar `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED=true` e fazer deploy controlado **apenas** de `it-portal-api` conforme runbook aprovado. Verificar `GET /me/capabilities` para usuário com e sem `deploy.view`, 403 sem grant e listagem `GET /atlas/deployments` com grant. A nova área **Implantações ATLAS** aparecerá no menu interno quando `can_view_atlas_deployments=true`; uma lista vazia é correta até existirem propostas assinadas registradas (API PREPARE ainda inativa).

**Fase 6: rollback operacional.** Se houver regressão, desligar imediatamente `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED` e reiniciar **apenas API**; revogar o grant Core quando necessário. Não realizar DROP no journal como rollback rotineiro, pois o schema é aditivo e poderá conter evidências auditáveis.

## Controles que não mudam

- `git pull`, Docker Compose, `up-prod-sequential.sh` e `up-hml-sequential.sh` dos outros desenvolvedores continuam independentes.
- Permitir que a mesma pessoa solicite e aprove no fluxo **futuro** continua sendo a regra; esta release é apenas VIEW e exige consentimento real futuro. Nenhum `POST approve`, PREPARE ou ACT.
- Nenhum `CREATE ROLE`, `GRANT SELECT`, mudança de banco, usuário Keycloak ou deploy é executado pelo ChatGPT nesta preparação.
- Revisão independente de código é um gate separado de aprovação operacional do único administrador.

## Checklist de aceitação posterior

- [ ] Revisão independente aprovada e CI totalmente verde
- [ ] Backup verificado e V016 aplicada pelo runner controlado
- [ ] V016 registrada com checksum, quatro tabelas e triggers existentes
- [ ] Role específica com SELECT mínimo e negação de challenges/escrita
- [ ] Manifesto 0.3.5 registrado e VIEW atribuído explicitamente
- [ ] UI visível ao autorizado, oculta aos demais e GET negando não autorizados
- [ ] ATLAS permanece sem ACT e scripts manuais inalterados
