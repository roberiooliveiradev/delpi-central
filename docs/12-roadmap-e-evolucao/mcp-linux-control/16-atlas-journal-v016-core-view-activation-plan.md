# ATLAS | P2.2h.2d: V016, RBAC Core e habilitação de consulta

**Data:** 2026-11-16.  
**Status atualizado em 2026-11-16:** `VIEW_ONLY_PROD_OPERATOR_CONFIRMED`. V016 aplicada, conexão PostgreSQL dedicada validada e tela de consulta visível ao operador. **PREPARE, aprovação nominativa e ACT permanecem não implementados/desabilitados.** O histórico de preparação abaixo foi preservado para rastreabilidade.  
**Owner:** TI / PostgreSQL / Core.

## Evidência inicial de produção antes da ativação (histórico)

- `delpi-it-portal-api` saudável, endpoints `/atlas/deployments` e `/atlas/deployments/{proposal_id}` presentes na OpenAPI após merge da PR #205.
- `settings.ATLAS_JOURNAL_READ_ENABLED=False` comprovado no container.
- Consulta somente leitura ao banco atual retornou `None` para `it_portal.atlas_deploy_proposals`, `it_portal.atlas_deploy_oci_bindings` e `it_portal.atlas_deploy_events`. Não há journal instalado; o frontend intencionalmente não oferece menu até a permissão e flag estarem ativas.

## Aceite de produção: consulta ATLAS somente leitura (16/11/2026)

**Fonte de evidência:** saídas de terminal e captura de tela fornecidas pelo operador nesta data. Este registro não substitui acesso independente ao host, ao Core ou ao PostgreSQL; não contém credenciais, nomes de usuários, IPs ou logs brutos.

1. **PR [#206](https://github.com/roberiooliveiradev/delpi-central/pull/206) integrada à `main`**: migration versionada V016, guardas default-off, role PostgreSQL separada e manifesto 0.3.5. A etapa de CI API/UI/PostgreSQL descartável passou antes da integração; execução independente do `delpi-verifier` **não foi demonstrada**.
2. **Backups antes das migrations:** o operador gerou backup do schema `it_portal` e backup completo do banco `plugins_hub` com `pg_dump -Fc`; confirmou arquivo não vazio e `pg_restore -l` sem erro. Isso verifica **formato/catálogo**, **não é prova de restauração completa**.
3. **Migrations V012–V015 aplicadas:** `run_migrations()` retornou exatamente V012, V013, V014 e V015; `schema_migrations` confirmou versões 1–15, sem lacunas. As estruturas de workstation foram criadas, **sem ativar controle remoto**.
4. **Migration V016 aplicada de forma opt-in:** o operador executou `run_migrations()` em processo isolado com `IT_PORTAL_ATLAS_JOURNAL_SCHEMA_APPLY_ENABLED=true` e `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED=false`. Resultado confirmado: `V016__atlas_deploy_oci_journal.sql`, versão 16 registrada e as quatro tabelas `it_portal.atlas_deploy_challenges`, `atlas_deploy_proposals`, `atlas_deploy_events` e `atlas_deploy_oci_bindings` presentes. A execução pontual não alterou permanentemente a flag de migração no container.
5. **Identidade de leitura:** conta `it_portal_atlas_journal_reader` criada inicialmente com `NOLOGIN`, `NOINHERIT` e `NOSUPERUSER`; somente `SELECT` nas tabelas proposals/bindings/events, com negação explícita de `SELECT` em challenges. O operador habilitou login depois da auditoria de privilégios (resultado informado como satisfatório, sem transcrição dos contadores) e validou a API com `atlas_journal_read_db_configured() == True`, `current_user` igual à role dedicada, `default_transaction_read_only=on`, `COUNT(proposals)=0`.
6. **Core/UI:** o operador foi instruído a publicar o manifesto `0.3.5` e atribuir `it-portal.access` + `it-portal.deploy.view`. A captura final mostra a opção **Implantações ATLAS** no menu, título da página, filtros **Ambiente** e **Situação**, aviso **Consulta somente leitura**, contagem **0 solicitação(ões)** e estado vazio **Nenhuma solicitação encontrada**. Isso comprova a **disponibilização visual ao operador** e é compatível com concessão de VIEW e leitura habilitada; a publicação do manifesto e o valor final da flag não foram confirmados por consulta administrativa independente.
7. **Segregação preservada:** essa página consulta registros reais e não fabrica propostas; nenhuma ação de solicitar, aprovar, executar, reiniciar container ou promover imagem OCI por digest foi demonstrada ou habilitada.

**Pendências de aceite/segurança ainda abertas:** revisor independente `delpi-verifier`; teste de restauração do backup completo em banco isolado; revisão de trigger/constraint V016 em runtime, além de tabelas; teste HTTP negativo `403` para usuário sem `it-portal.deploy.view`, revogação Core e `503` com leitor indisponível; verificação da configuração final da flag/manifesto pela fonte administrativa; observação de HML quando exigida pelo gate do projeto. Não marcar essas pendências como PASS com base apenas na captura.

**Risco operacional separado:** o PostgreSQL `plugins_hub` reportou divergência de versão de collation (versão registrada 2.41; fornecida pelo sistema 2.36). O operador optou por postergar a manutenção. **Não** foram executados `REINDEX` nem `REFRESH COLLATION VERSION` nesta implantação; manter avaliação e janela DBA separadas.

**Próxima fase ATLAS:** criar uma API de PREPARE autenticada e auditada para produzir propostas OCI reais e vínculos assinados no journal, depois implementar decisão nominativa no Portal do TI e somente por último o executor isolado com verificações de CI, assinatura, host proof, health e rollback. Manter ACT default-off e scripts manuais independentes.

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

## Checklist: validado pelo operador vs. pendente

- [x] CI API/UI/PostgreSQL descartável aprovado na PR #206, antes do merge
- [x] Backup completo existente com formato/catálogo `pg_restore -l` validado; **restauração de teste ainda pendente**
- [x] V012–V016 registradas no histórico pelo runner; quatro tabelas V016 existentes
- [x] Role dedicada: `SELECT` nas três tabelas de leitura, `challenges` negado e conexão read-only comprovada
- [x] UI de consulta visível ao operador com 0 propostas e aviso de somente leitura (captura de 16/11/2026)
- [x] Sem PREPARE/ACT, sem mudança nos scripts manuais pelo incremento de VIEW
- [ ] `delpi-verifier` independente, teste de restauração e validação de triggers/constraints em runtime
- [ ] Confirmar configuração Core 0.3.5 e grants por fonte administrativa, e realizar testes negativos 403/503, incluindo usuário sem VIEW
- [ ] Avaliar e corrigir mismatch de collation em janela DBA própria
