# ATLAS P2.2h.2d | Consulta autenticada do journal OCI no Portal do TI

**Data:** 2026-11-16.  
**Estado atualizado (16/11/2026):** PR #205 integrada; API e frontend publicados pelo operador, endpoints presentes, mas consulta desativada e sem tabelas no banco; revisão independente e ativação controlada ainda pendentes. Próxima preparação: [V016 e Core](./16-atlas-journal-v016-core-view-activation-plan.md).

## Objetivo

Disponibilizar leitura de propostas OCI do Public Hub no Portal do TI, com autenticacao humana Keycloak, autorizacao Core consultada novamente antes de cada leitura, dados originados do journal PostgreSQL e interface somente informativa. **Nenhuma operacao de aprovar, rejeitar, PREPARE ou ACT foi criada.**

## API

- `GET /apps/it-portal-api/atlas/deployments`: lista paginada (maximo 50 por pagina), filtro de ambiente `prod|hml` e situacao. Expõe exclusivamente propostas com vinculo OCI correspondente ao pai por identity/hash/commit/timestamps. Propostas legadas sem binding ficam ocultas.
- `GET /apps/it-portal-api/atlas/deployments/{proposal_id}`: detalhe e eventos de auditoria ordenados, com identidade do requisitante, commit, digest de manifesto assinado, ImageIDs de base/novo/rollback, binding e validade. Campos sensiveis de challenges/attestation proofs nao sao retornados.
- Ambos exigem JWT valido de **usuario humano** mais `it-portal.access` e **grant Core explicito** `it-portal.deploy.view`, revalidados via `force_refresh=True`. Mesmo `is_superadmin` sem o grant explicito nao autoriza a consulta. Identity drift entre token e Core revalidado nega o request.
- Restritos a `service_id='public-hub'`, SQL parametrizado, JOIN com invariantes de identidade OCI, transacao `REPEATABLE READ READ ONLY`. Sucesso vazio = tabela instalada mas sem propostas; banco ou esquema ausentes = **503 fail-closed**, nunca sucesso vazio.
- Feature flag `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED` vem **false** por padrao, e a API verifica o estado ao receber cada GET. A flag nao cadastra usuario, grant, schema ou aprovacao e nao deve ser habilitada apenas por ter CI verde.
- S2S, usuario sem grant, grant revogado em consulta fresh, Core indisponivel, environment nao permitido e inputs invalidos negados; sem API POST/PUT/PATCH/DELETE para o journal.

## Frontend

- A nova pagina `/apps/it-portal/atlas-deployments` aparece no menu somente se a BFF emitir `can_view_atlas_deployments=true` com flag ligada e grant de leitura explicito. A BFF ainda revalida permissoes no GET, portanto esconder menu nao e barreira de seguranca.
- UI responsiva com filtros, tabela, paginacao, detalhe da identidade OCI e eventos, estados carregando/vazio/erro; utiliza so GET ao BFF, sem dados ficticios e sem qualquer acao de aprovacao ou execucao.
- O componente visual candidato anterior (P2.2h.2c) continua separado e inerte; a nova pagina e a de consulta real quando o backend puder oferecer dados.

## Dependencias e gates antes de habilitar leitura

1. Owner PostgreSQL aprova os DDLs candidatos, resolve numeracao de migration com Delpi Remote, prepara migration versionada e roles SELECT minimo no schema `it_portal`. **Nenhuma migration foi adicionada ou executada nesta PR.**
2. Owner Core provisiona o grant `it-portal.deploy.view` no catalogo e somente aos usuarios autorizados. O mesmo usuario pode solicitar e aprovar sua propria proposta no fluxo FUTURO, mediante aprovacao explicita; este GET so exige VIEW.
3. Testar integracao GET no HML com schema real sob identidade valida, grant, revogacao, conexao indisponivel e isolamento. So apos esses passos, habilitar `IT_PORTAL_ATLAS_JOURNAL_READ_ENABLED=true` no ambiente autorizado.
4. Concluir testes CI API/HTTP, PostgreSQL descartavel e UI + gates de arquitetura/governanca, e revisao obrigatoria `delpi-verifier` por agente independente antes do merge.
5. Continuam pendentes: fonte de attestation GitHub/host real, criacao governada de proposta, API POST de aprovacao, auditoria de decisao, executor isolado, rollback e gates PROD.

## Compatibilidade com deploy manual

Os comandos `git pull`, `docker compose`, `infra/scripts/up-prod-sequential.sh` e `up-hml-sequential.sh` **nao foram alterados**. A integracao de leitura do ATLAS e aditiva: nao bloqueia outros desenvolvedores nem identifica a leitura como sinal de aprovacao.

**Status sem ambiguidades:** `GET_CODE_READY_IN_PR` / `READ_FLAG_DEFAULT_OFF` / `CORE_GRANT_NOT_PROVISIONED` / `ATLAS_SCHEMA_NOT_MIGRATED` / `PREPARE_API_DISABLED` / `ACT_DISABLED` / `PROD_UNTOUCHED`.
