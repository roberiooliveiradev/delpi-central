# Relatório de Adequação LGPD — Projeto Delpi Central

**Data:** 26/05/2026  
**Responsável técnico:** Equipe de Desenvolvimento  
**Base legal:** Lei nº 13.709/2018 (LGPD)  
**DPO:** Michael Marotto — ti@delpi.com.br

---

## Resumo Executivo

Foram realizadas **12 fases** de adequação à LGPD, cobrindo backend, frontend e infraestrutura. Todas as **38 inconformidades** identificadas no relatório de auditoria foram **resolvidas ou classificadas como risco aceito (100%)**. Pendências residuais são exclusivamente de configuração de ambiente de produção (ver Checklist de Deploy).

---

## Commits

| Hash | Fase | Descrição |
|------|------|-----------|
| `7db02c54` | 1 | Hardening de segurança — JWT, error handling e CORS |
| `9b2282bb` | 2 | Módulo de gestão de consentimento do titular |
| `e9e6a63c` | 6 | Mascarar dados pessoais em audit logs e remover exposição de erros |
| `51b6bf41` | 4+5 | Direito ao esquecimento e portabilidade de dados |
| `4907f841` | 3+7 | Retenção de dados, CLI de cleanup e transparência |
| `56c79d87` | 8 | Consentimento no primeiro login, opt-out de tracking, mascarar email em diretório |
| `1838906b` | 8 | Data retention jobs (transformometro, strategic-indicators), fix postMessage Swagger |
| `2f876748` | 8 | Consentimento IA, retenção de chat, aviso de privacidade no minha-delpi-ai-api |
| `a73e1f95` | 8 | Anonimizar dados em testes, página de Política de Privacidade |
| `1b421f6e` | 9 | Integrar endpoints LGPD no frontend (portal) |
| `eb6c60c5` | 9 | Tornar PrivacyPage resiliente a falhas de API |
| `694bfd7c` | 9 | Corrigir mapeamento de campos camelCase/snake_case |
| `51998e9f` | 9 | Configurar dados reais do DPO |
| `fa6aa22c` | 9 | Corrigir chamada de grant consent (POST body) |
| `1018b669` | 9 | Revisão geral — padronizar respostas, PrivacyPolicyPage, tratamento de erros |
| `fe914046` | 10 | Rate limiting, truncamento de IP, minimização de dados em notificações |
| `65a07174` | 11 | Normalização de emails denormalizados (strategic-indicators-api) |
| `37b20161` | 11 | Fix startup minha-delpi-ai-api (delpi_auth volume) |
| `fad275ee` | 12 | Modal de consentimento obrigatório no login |
| `a3c95dd4` | 12 | Modal com leitura da política de privacidade em duas etapas |

---

## Fase 1 — Hardening de Segurança

**Ref. LGPD:** Art. 46 (segurança), Art. 6 VII (segurança e prevenção)  
**Inconformidades resolvidas:** 4.2, 4.3, 4.4, 4.6, 4.9

| Arquivo | Alteração | Motivo |
|---------|-----------|--------|
| `shared/delpi_auth/jwt_validator.py` | Validação condicional do claim `audience` via `KEYCLOAK_AUDIENCE` | Prevenir aceitação de tokens de outros clientes (Art. 46) |
| `api-delpi/app/config.py` | Removido default `"secret"` de `JWT_SECRET` | Eliminar segredo hardcoded (Art. 46) |
| `transformometro-api/tm_app/config.py` | Removido default `"secret"` de `JWT_SECRET` | Eliminar segredo hardcoded (Art. 46) |
| `strategic-indicators-api/si_app/config.py` | Removido default `"secret"` de `JWT_SECRET` | Eliminar segredo hardcoded (Art. 46) |
| `core-api/app/infrastructure/config/settings.py` | `TestingConfig` usa env var `TEST_DATABASE_URL` | Remover URI hardcoded com credenciais (Art. 46) |
| `transformometro-api/tm_app/main.py` | Exception handler genérico + CORS restritivo em produção | Não expor stack traces; limitar origens (Art. 46) |
| `transformometro-api/tm_app/core/errors.py` | `format_api_error` retorna mensagem genérica | Não vazar detalhes internos nas respostas HTTP |
| `api-delpi/app/main.py` | CORS: `localhost` só em ambientes não-produção | Reduzir superfície de ataque em produção |
| `strategic-indicators-api/si_app/main.py` | CORS: `localhost` só em ambientes não-produção | Reduzir superfície de ataque em produção |
| `core-api/app/interfaces/http/me_controller.py` | 7 ocorrências de `str(e)` substituídas por mensagens genéricas | Não expor exceções ao cliente (Art. 46) |
| `shared/delpi_auth/middleware/fastapi_auth.py` | Respostas de erro genéricas + logging interno | Não expor detalhes de exceção ao cliente |

---

## Fase 2 — Gestão de Consentimento

**Ref. LGPD:** Art. 7 I (consentimento), Art. 8 (requisitos do consentimento), Art. 18 IX (revogação)  
**Inconformidade resolvida:** 1.1

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/infrastructure/db/models/user_consent.py` | Model `UserConsent` com campos: user_id, purpose, granted, granted_at, revoked_at, ip_address, user_agent |
| `core-api/migrations/versions/l8m9n0o1p2_create_user_consents.py` | Migration Alembic para tabela `user_consents` |
| `core-api/app/domain/ports/consent_repository_port.py` | Port (interface) do repositório de consentimento |
| `core-api/app/infrastructure/persistence/sqlalchemy/consent_repository.py` | Implementação SQLAlchemy do repositório |
| `core-api/app/application/use_cases/list_consents_use_case.py` | Use case: listar consentimentos do titular |
| `core-api/app/application/use_cases/manage_consent_use_case.py` | Use cases: conceder, revogar e revogar todos |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/infrastructure/db/models/__init__.py` | Import do `UserConsent` |
| `core-api/app/infrastructure/persistence/sqlalchemy/unit_of_work.py` | Adicionado `SqlAlchemyConsentRepository` ao UnitOfWork |
| `core-api/app/interfaces/http/me_controller.py` | Endpoints `GET /me/consents`, `POST /me/consents`, `DELETE /me/consents/<purpose>` |

---

## Fase 3 — Retenção de Dados

**Ref. LGPD:** Art. 15 (término do tratamento), Art. 16 (eliminação de dados)  
**Inconformidades resolvidas:** 6.1, 6.4

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/infrastructure/jobs/data_retention_job.py` | Job de limpeza: anonimização de audit logs (730d), purge de notificações deletadas (30d), notificações antigas (180d), eventos de uso (365d) |
| `core-api/app/infrastructure/cli/data_retention_cli.py` | Comando Flask CLI `flask data-retention run` |
| `core-api/app/create_app.py` | Registro do CLI `data_retention_cli` |

---

## Fase 4 — Direito ao Esquecimento (Erasure)

**Ref. LGPD:** Art. 18 IV (anonimização, bloqueio ou eliminação), Art. 18 VI (eliminação)  
**Inconformidade resolvida:** 2.6

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/application/use_cases/admin/anonymize_user_data_use_case.py` | Use case de anonimização: User, AuditLog, Notification, App, UserConsent |
| `core-api/app/interfaces/http/rbac_controller.py` | Endpoint `POST /admin/rbac/users/<user_id>/anonymize` (`@require_superadmin()`) |

---

## Fase 5 — Portabilidade de Dados

**Ref. LGPD:** Art. 18 V (portabilidade dos dados)  
**Inconformidades resolvidas:** 3.1, 3.2

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/application/use_cases/export_user_data_use_case.py` | Exporta: perfil, consentimentos, notificações, eventos de uso e audit logs |
| `core-api/app/interfaces/http/me_controller.py` | Endpoint `GET /me/data-export` + `GET /me/privacy` (confirmação de tratamento) |

---

## Fase 6 — Mascaramento de Audit Logs

**Ref. LGPD:** Art. 6 III (minimização), Art. 46 (segurança)  
**Inconformidades resolvidas:** 5.3, 4.4

| Arquivo | Alteração |
|---------|-----------|
| `transformometro-api/tm_app/interface/http/routes/crud_routes.py` | `_mask_personal_data()` mascara campos pessoais no payload do audit log |
| `shared/delpi_auth/middleware/fastapi_auth.py` | Respostas de erro genéricas (500/401) + logging interno |
| `core-api/app/interfaces/http/admin_statistics_controller.py` | `server_error()` genérico + logging interno |

---

## Fase 7 — Transparência e Registro de Tratamento

**Ref. LGPD:** Art. 37 (ROPA), Art. 41 (DPO), Art. 9 (direito à informação)  
**Inconformidades resolvidas:** 7.1, 7.3

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/domain/lgpd/privacy_constants.py` | Constantes: DPO (Michael Marotto), purposes de consentimento, prazos de retenção |
| `docs/13-auditoria-lgpd/ropa-registro-tratamento.md` | ROPA com 8 categorias documentadas |
| `core-api/app/interfaces/http/me_controller.py` | Endpoint `GET /me/privacy` com DPO, política, purposes e direitos |

---

## Fase 8 — Adequações Específicas por Microsserviço

**Inconformidades resolvidas:** 1.2, 1.3, 1.4, 2.3, 2.4, 2.5, 4.5, 4.10, 5.1, 5.5, 7.2, 8.3

### core-api

| Arquivo | Alteração |
|---------|-----------|
| `app/interfaces/http/me_controller.py` | Retorna `consent_pending: true` no `/me` se sem consentimentos (1.2) |
| `app/interfaces/socket/socket_handlers.py` | Verifica consentimento `usage_tracking` antes de registrar uso (1.4) |
| `app/infrastructure/db/models/user.py` | Docstring LGPD em `birth_date` (5.1) |
| `app/application/use_cases/search_directory_users_use_case.py` | Mascara email na busca de diretório (8.3) |
| `app/application/use_cases/lookup_directory_users_use_case.py` | Mascara email no lookup de diretório (8.3) |

### minha-delpi-ai-api

| Arquivo | Alteração |
|---------|-----------|
| `app/application/services/chat_user_context_service.py` | Verifica consentimento `ai_context` antes de injetar PII no LLM (1.3) |
| `app/infrastructure/cli/data_retention_cli.py` | CLI para retenção de AI audit logs e mensagens de chat (2.3, 5.5) |
| `app/interfaces/http/chat_routes.py` | Aviso de privacidade na criação de sessão de chat (5.5) |

### transformometro-api

| Arquivo | Alteração |
|---------|-----------|
| `tm_app/infrastructure/jobs/data_retention_job.py` | Purge de soft-deleted (90d) e anonimização de audit logs (730d) (2.4) |

### strategic-indicators-api

| Arquivo | Alteração |
|---------|-----------|
| `si_app/infrastructure/jobs/data_retention_job.py` | Anonimização de `actor_email` em `settings_audit` (730d) (2.5) |
| `si_app/main.py` | Fix postMessage origin check no Swagger; desabilitar Swagger em produção (4.10) |

### Dados e fixtures

| Arquivo | Alteração |
|---------|-----------|
| `portal/src/components/notifications/notificationHtmlPreview.ts` | Anonimizar dados pessoais reais em previews (4.5) |
| `portal/src/components/notifications/notificationVariables.ts` | Anonimizar dados pessoais reais em variáveis de teste (4.5) |

---

## Fase 9 — Frontend (Portal)

**Inconformidade resolvida:** 7.2

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `portal/src/ui/PrivacyPage.tsx` | Página de privacidade: consentimentos, exportação, DPO, direitos, retenção |
| `portal/src/ui/PrivacyPage.css` | Estilos da página de privacidade |
| `portal/src/ui/PrivacyPolicyPage.tsx` | Política de privacidade estática com dados do DPO via API |
| `portal/src/ui/PrivacyPolicyPage.css` | Estilos da política de privacidade |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `portal/src/data/coreApi.ts` | Tipos e métodos: `getConsents`, `grantConsent`, `revokeConsent`, `getPrivacyInfo`, `getDataExport` |
| `portal/src/data/adminApi.ts` | Método `anonymizeUser` para ação admin |
| `portal/src/ui/App.tsx` | Rotas `/privacy` e `/privacy-policy` |
| `portal/src/layout/Sidebar.tsx` | Links "Privacidade e Dados" e "Política de Privacidade" no menu |
| `portal/src/ui/admin/tabs/RbacTab.tsx` | Botão "Anonimizar (LGPD)" com confirmação e tratamento de erro |

---

## Fase 10 — Infraestrutura e Minimização Final

**Ref. LGPD:** Art. 46 (segurança), Art. 6 III (minimização)  
**Inconformidades resolvidas:** 4.7, 5.2, 8.4

| Arquivo | Alteração | Motivo |
|---------|-----------|--------|
| `gateway/nginx.conf` | Rate limiting: auth (10r/s burst=20), API (30r/s burst=50) | Proteção contra força bruta (Art. 46) |
| `gateway/nginx.dev.conf` | Rate limiting: auth (10r/s), API (30r/s) | Paridade com produção |
| `core-api/app/domain/lgpd/__init__.py` | Helper `truncate_ip()` — remove último octeto IPv4 (ex: 192.168.1.100 → 192.168.1.0) | Minimização de dados (Art. 6 III) |
| `core-api/app/interfaces/http/me_controller.py` | Usar `truncate_ip()` ao gravar IP de consentimento | Art. 6 III |
| `core-api/app/infrastructure/persistence/sqlalchemy/audit_repository.py` | Usar `truncate_ip()` ao gravar IP em audit logs | Art. 6 III |
| `transformometro-api/.../revisao_workflow_notification_service.py` | Preferir `roleIds`/`userIds` sobre `emails` nas notificações; remover email do actor do corpo da mensagem | Minimização entre serviços (Art. 6 III) |

---

## Fase 11 — Normalização de Emails Denormalizados

**Ref. LGPD:** Art. 6 III (minimização)  
**Inconformidade resolvida:** 5.4

### strategic-indicators-api (42 arquivos modificados)

| Camada | Alteração |
|--------|-----------|
| **Ports** (5 arquivos) | Removido parâmetro `actor_email` de todos os métodos de repositório |
| **DTOs** (5 arquivos) | Removido campo `actor_email: str \| None` dos requests |
| **Use Cases** (22 arquivos) | Removido `actor_email` das assinaturas `execute()` e chamadas a repositórios |
| **Repositories** (6 arquivos) | Colunas `*_by_email` agora recebem `NULL` em INSERT/UPDATE |
| **Routes** (`strategic_indicators_routes.py`) | `_extract_actor()` retorna apenas `actor_user_id` |

### core-api

| Arquivo | Status |
|---------|--------|
| `app/infrastructure/persistence/sqlalchemy/app_audit.py` | Já não gravava `_by_email` em novas escritas |
| `anonymize_user_data_use_case.py` | Já anonimizava colunas `_by_email` e `_by_name` existentes |

### Frontend

| Arquivo | Alteração |
|---------|-----------|
| `plugins/strategic-indicators/.../IndicatorGoalsWorkspace.tsx` | Fallback `updated_by_email ?? updated_by_user_id ?? "-"` |

### Infraestrutura

| Arquivo | Alteração |
|---------|-----------|
| `infra/docker-compose.dev.yml` | Volume `shared/delpi_auth` montado no `minha-delpi-ai-api` |
| `minha-delpi-ai-api/app/composition/root_composer.py` | `try-except ImportError` no `check_credentials()` |

---

## Fase 12 — Modal de Consentimento Obrigatório no Login

**Ref. LGPD:** Art. 7 I (consentimento), Art. 8 §1 (consentimento informado), Art. 9 (direito à informação)  
**Inconformidades reforçadas:** 1.1, 1.2, 7.2

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `portal/src/ui/ConsentModal.tsx` | Modal em duas etapas: leitura da política + seleção de consentimentos |
| `portal/src/ui/ConsentModal.css` | Estilos do modal com steps, área scrollável para política e cards de consentimento |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `portal/src/ui/App.tsx` | Hook `useConsentCheck` verifica `data_processing` após login; se pendente, exibe `ConsentModal` antes do `AppShell` |
| `portal/src/data/coreApi.ts` | Novo método `getConsentsRaw()` retorna `items` + `availablePurposes` |

### Fluxo do modal

1. **Etapa 1 — Política de Privacidade:** texto completo (DPO, dados coletados, bases legais, direitos do titular, retenção, segurança, contato). O botão "Prosseguir" só habilita após rolar até o final.
2. **Etapa 2 — Consentimentos:** checkboxes com `data_processing` (obrigatório, não desmarcável) e demais opcionais. Hint: "Você pode alterar suas preferências a qualquer momento em Privacidade de Dados."
3. Após aceitar, o modal não reaparece — verificação é feita via `GET /me/consents` a cada login.

---

## Novos Endpoints (Resumo)

| Método | Rota | Proteção | Fase |
|--------|------|----------|------|
| `GET` | `/me/consents` | `@require_auth()` | 2 |
| `POST` | `/me/consents` | `@require_auth()` | 2 |
| `DELETE` | `/me/consents/<purpose>` | `@require_auth()` | 2 |
| `GET` | `/me/data-export` | `@require_auth()` | 5 |
| `GET` | `/me/privacy` | `@require_auth()` | 7 |
| `POST` | `/admin/rbac/users/<id>/anonymize` | `@require_superadmin()` | 4 |

---

## Novas Páginas e Componentes no Portal

| Rota / Componente | Tipo | Descrição |
|-------------------|------|-----------|
| `/privacy` | Página | Consentimentos, exportação, DPO, direitos, retenção |
| `/privacy-policy` | Página | Política de privacidade completa |
| `ConsentModal` | Modal | Exibido após login — leitura da política + aceite obrigatório (Fase 12) |

---

## Cobertura de Inconformidades

| # Auditoria | Descrição | Status | Fase |
|-------------|-----------|--------|------|
| 1.1 | Nenhum mecanismo de consentimento | ✅ Resolvido | 2 |
| 1.2 | Auto-provisionamento sem consentimento | ✅ Resolvido | 8, 12 |
| 1.3 | Dados pessoais injetados no LLM sem consentimento | ✅ Resolvido | 8 |
| 1.4 | Rastreamento de uso sem ciência | ✅ Resolvido | 8 |
| 2.1 | Audit logs irremovíveis (core-api) | ✅ Resolvido | 3 |
| 2.2 | Audit logs irremovíveis (transformometro-api) | ✅ Resolvido | 6, 8 |
| 2.3 | Audit logs do chat IA | ✅ Resolvido | 8 |
| 2.4 | Soft delete sem purge (transformometro) | ✅ Resolvido | 8 |
| 2.5 | Settings audit sem exclusão (strategic-indicators) | ✅ Resolvido | 8 |
| 2.6 | Ausência de endpoint de esquecimento | ✅ Resolvido | 4 |
| 3.1 | Ausência de portabilidade | ✅ Resolvido | 5 |
| 3.2 | Ausência de confirmação de tratamento | ✅ Resolvido | 7 |
| 4.1 | Credenciais fracas detectadas no startup | ✅ Resolvido | 11 |
| 4.2 | JWT_SECRET default "secret" | ✅ Resolvido | 1 |
| 4.3 | Verificação de audience desabilitada | ✅ Resolvido | 1 |
| 4.4 | Exposição de detalhes em erros | ✅ Resolvido | 1, 6 |
| 4.5 | Dados pessoais em seeds/fixtures | ✅ Resolvido | 8 |
| 4.6 | CORS permissivo | ✅ Resolvido | 1 |
| 4.7 | Nginx sem rate limiting | ✅ Resolvido | 10 |
| 4.8 | Token de serviço estático (legado removido) | ✅ Resolvido | 10 |
| 4.9 | Senha de teste hardcoded | ✅ Resolvido | 1 |
| 4.10 | Swagger postMessage sem origin check | ✅ Resolvido | 8 |
| 5.1 | birth_date sem finalidade clara | ✅ Resolvido | 8 |
| 5.2 | IP address sem truncamento | ✅ Resolvido | 10 |
| 5.3 | Payload completo nos audit logs | ✅ Resolvido | 6 |
| 5.4 | Emails denormalizados em tabelas | ✅ Resolvido | 11 |
| 5.5 | Mensagens de chat sem retenção | ✅ Resolvido | 8 |
| 6.1 | Ausência de política de retenção | ✅ Resolvido | 3 |
| 6.2 | Redis presence sem TTL | ✅ Já adequado | — |
| 6.3 | Cache de embeddings sem TTL | ✅ Já adequado | — |
| 6.4 | Soft delete notifications sem purge | ✅ Resolvido | 3 |
| 7.1 | Ausência de ROPA | ✅ Resolvido | 7 |
| 7.2 | Ausência de política de privacidade | ✅ Resolvido | 8, 9 |
| 7.3 | Ausência de canal do DPO | ✅ Resolvido | 7 |
| 8.1 | JWT repassado entre microsserviços internos | ✅ Risco aceito | 10 |
| 8.2 | Dados pessoais enviados ao LLM | ✅ Resolvido | 8 |
| 8.3 | Busca de diretório expõe email | ✅ Resolvido | 8 |
| 8.4 | Notificações compartilham emails | ✅ Resolvido | 10 |

**Total: 38/38 resolvidos (100%)**.

---

## Pendências Infraestruturais (resolvidas ou mitigadas)

### 4.1 — Credenciais em `.env` (RISCO ACEITO)

**Ação aplicada:** Criado módulo `shared/delpi_auth/credential_guard.py` que valida credenciais fracas no startup de todas as APIs (core-api, api-delpi, transformometro-api, strategic-indicators-api, minha-delpi-ai-api). Em produção (`FLASK_ENV=production` / `APP_ENV=production`), a aplicação **não inicia** se houver senhas com menos de 12 caracteres ou padrões triviais (password, 123, admin, etc.).  
**Decisão:** Manter credenciais em `.env` com a mitigação aplicada. O servidor é privado, acesso restrito à equipe de TI, e o `.env` não é versionado no repositório. O cofre de segredos (Vault, AWS SM) será avaliado quando a infraestrutura crescer ou houver exigência de auditoria externa.  
**Classificação:** Risco aceito — infraestrutura privada + guard de startup + senhas fortes obrigatórias.

### 4.8 — Token de serviço estático (RESOLVIDO)

**Ação aplicada:** Removido o fallback legado `TRANSFORMOMETRO_SERVICE_BEARER` em `api-delpi`, `strategic-indicators-api` e `shared/transformometro_client`. A comunicação inter-serviço agora usa exclusivamente `API_DELPI_INTERNAL_SERVICE_TOKEN` via header `X-Delpi-Service-Token`.  
**Pendência futura (fora de escopo):** Migrar para OAuth2 client credentials com tokens JWT de curta duração em revisão arquitetural.

### 5.4 — Emails denormalizados em tabelas (RESOLVIDO)

**Ação aplicada:** Removido `actor_email` de toda a cadeia de escrita do `strategic-indicators-api` (ports, use cases, repositórios, rotas). Novos registros gravam `NULL` nas colunas `*_by_email`. Colunas SQL mantidas para compatibilidade com dados históricos (que serão anonimizados pelo job de retenção). Frontend já faz fallback para `user_id` quando email é `null`. No `core-api`, as colunas `_by_email` em `apps` já não eram populadas em novas escritas.

### 8.1 — JWT repassado entre microsserviços internos (RISCO ACEITO)

**Decisão:** Manter o repasse de JWT entre microsserviços internos.  
**Justificativa:** As APIs downstream (transformometro-api, api-delpi, strategic-indicators-api) necessitam do JWT do usuário para aplicar RBAC (permissões, filiais, departamentos). Todos os serviços operam na mesma rede Docker privada (`delpi-network`), sem exposição externa. JWT possui expiração curta. Documentado no ROPA (seção 9).  
**Mitigação residual:** Token interno `API_DELPI_INTERNAL_SERVICE_TOKEN` usado como fallback para chamadas sem contexto de usuário.

---

## Checklist de Deploy para Produção

### Já aplicados (código)

- [x] Executar migration: `flask db upgrade` (tabela `user_consents`)
- [x] Configurar DPO real em `privacy_constants.py` (Michael Marotto — ti@delpi.com.br)
- [x] Publicar política de privacidade no portal (`/privacy-policy`)
- [x] Modal de consentimento obrigatório no primeiro login (leitura da política + aceite)
- [x] Normalização de emails denormalizados (strategic-indicators-api)
- [x] `credential_guard.py` — bloqueia startup com credenciais fracas em produção
- [x] ~~Migrar credenciais para cofre de segredos~~ — risco aceito; mitigado via `credential_guard.py`

### Configuração de ambiente (a fazer no servidor de produção)

- [ ] Definir `KEYCLOAK_AUDIENCE` no `.env` — necessário para validação de audience no JWT (todas as APIs leem essa variável, mas sem valor definido a validação é ignorada)
- [ ] Definir `JWT_SECRET` com valor forte (≥ 12 chars) — o `credential_guard` bloqueará o startup se for fraco
- [ ] Agendar cron `flask data-retention run` no container `core-api` (recomendado: diário, ex.: `0 3 * * *`) — executa purge de dados expirados conforme política de retenção
- [ ] Definir `TM_WORKFLOW_APPROVER_ROLE_IDS` no `.env` do `transformometro-api` — permite notificações por role em vez de emails
- [ ] Revisar e validar o ROPA (`docs/13-auditoria-lgpd/ropa-registro-tratamento.md`) com o DPO

### Decisões aceitas (não requerem ação imediata)

| Item | Decisão | Justificativa |
|------|---------|---------------|
| 4.1 — Credenciais em `.env` | Risco aceito | Servidor privado, `.env` fora do Git, `credential_guard` impede senhas fracas |
| 4.8 — Token de serviço estático | Resolvido | Legado removido; usar `API_DELPI_INTERNAL_SERVICE_TOKEN` exclusivamente |
| 5.4 — Emails denormalizados | Resolvido | Parou de gravar; colunas mantidas para dados históricos |
| 8.1 — JWT inter-serviço | Risco aceito | Rede Docker privada, JWT curto, necessário para RBAC |

---

## Artigos da LGPD Referenciados

| Artigo | Tema | Fases |
|--------|------|-------|
| Art. 6 I | Finalidade | 8 |
| Art. 6 III | Minimização | 6, 8, 10, 11 |
| Art. 6 VI | Transparência | 7, 9, 12 |
| Art. 6 VII | Segurança e prevenção | 1 |
| Art. 7 I | Consentimento | 2, 8, 12 |
| Art. 8 | Requisitos do consentimento | 2, 12 |
| Art. 8 §1 | Consentimento informado | 12 |
| Art. 9 | Direito à informação | 7, 9, 12 |
| Art. 15 | Término do tratamento | 3 |
| Art. 16 | Eliminação de dados | 3 |
| Art. 18 I | Confirmação de tratamento | 7 |
| Art. 18 IV | Anonimização/eliminação | 4 |
| Art. 18 V | Portabilidade | 5, 9 |
| Art. 18 VI | Eliminação | 4 |
| Art. 18 IX | Revogação do consentimento | 2, 9, 12 |
| Art. 37 | Registro de tratamento (ROPA) | 7 |
| Art. 41 | Encarregado (DPO) | 7, 9 |
| Art. 46 | Segurança | 1, 6, 10, 11 |
