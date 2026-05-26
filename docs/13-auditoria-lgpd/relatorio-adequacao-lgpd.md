# Relatório de Adequação LGPD — Projeto Delpi Central

**Data:** 26/05/2026  
**Responsável técnico:** Equipe de Desenvolvimento  
**Base legal:** Lei nº 13.709/2018 (LGPD)

---

## Resumo Executivo

Foram realizadas **7 fases** de adequação à LGPD, totalizando **30 arquivos alterados** (941 inserções, 159 remoções) em **5 commits** dedicados. As alterações cobrem segurança, consentimento, retenção, direito ao esquecimento, portabilidade, mascaramento de logs e transparência.

---

## Commits

| Hash | Fase | Descrição |
|------|------|-----------|
| `7db02c54` | 1 | Hardening de segurança — JWT, error handling e CORS |
| `9b2282bb` | 2 | Módulo de gestão de consentimento do titular |
| `e9e6a63c` | 6 | Mascarar dados pessoais em audit logs e remover exposição de erros |
| `51b6bf41` | 4+5 | Direito ao esquecimento e portabilidade de dados |
| `4907f841` | 3+7 | Retenção de dados, CLI de cleanup e transparência |

---

## Fase 1 — Hardening de Segurança

**Ref. LGPD:** Art. 46 (segurança), Art. 6 VII (segurança e prevenção)

### Alterações

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

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/infrastructure/db/models/user_consent.py` | Model `UserConsent` com campos: user_id, purpose, granted, granted_at, revoked_at, ip_address, user_agent |
| `core-api/migrations/versions/l8m9n0o1p2_create_user_consents.py` | Migration Alembic para tabela `user_consents` |
| `core-api/app/domain/ports/consent_repository_port.py` | Port (interface) do repositório de consentimento |
| `core-api/app/infrastructure/persistence/sqlalchemy/consent_repository.py` | Implementação SQLAlchemy do repositório |
| `core-api/app/application/use_cases/list_consents_use_case.py` | Use case: listar consentimentos do titular |
| `core-api/app/application/use_cases/manage_consent_use_case.py` | Use cases: conceder, revogar e revogar todos os consentimentos |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/infrastructure/db/models/__init__.py` | Import do `UserConsent` |
| `core-api/app/infrastructure/persistence/sqlalchemy/unit_of_work.py` | Adicionado `SqlAlchemyConsentRepository` ao UnitOfWork |
| `core-api/app/interfaces/http/me_controller.py` | Endpoints `GET /me/consents`, `POST /me/consents/<purpose>`, `DELETE /me/consents/<purpose>` |

### ⚠️ Migration pendente em produção

Executar antes do deploy:

```bash
flask db upgrade
```

---

## Fase 3 — Retenção de Dados

**Ref. LGPD:** Art. 15 (término do tratamento), Art. 16 (eliminação de dados)

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/infrastructure/jobs/data_retention_job.py` | Job de limpeza periódica com 4 operações: anonimização de audit logs (730d), purge de notificações deletadas (30d), purge de notificações antigas (180d), purge de eventos de uso (365d) |
| `core-api/app/infrastructure/cli/data_retention_cli.py` | Comando Flask CLI `flask data-retention run` |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/create_app.py` | Registro do CLI `data_retention_cli` na app factory |

### ⚠️ Configuração em produção

Agendar execução periódica (cron ou scheduler):

```bash
flask data-retention run
```

---

## Fase 4 — Direito ao Esquecimento (Erasure)

**Ref. LGPD:** Art. 18 IV (anonimização, bloqueio ou eliminação), Art. 18 VI (eliminação)

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/application/use_cases/admin/anonymize_user_data_use_case.py` | Use case que anonimiza dados pessoais em: User, AuditLog, Notification, App, UserConsent |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/interfaces/http/rbac_controller.py` | Endpoint `POST /admin/rbac/users/<user_id>/anonymize` protegido por `@require_superadmin()` |

---

## Fase 5 — Portabilidade de Dados

**Ref. LGPD:** Art. 18 V (portabilidade dos dados)

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/application/use_cases/export_user_data_use_case.py` | Use case que exporta: perfil, consentimentos, notificações, eventos de uso e audit logs |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/interfaces/http/me_controller.py` | Endpoint `GET /me/data-export` protegido por `@require_auth()` |

---

## Fase 6 — Mascaramento de Audit Logs

**Ref. LGPD:** Art. 6 III (minimização), Art. 46 (segurança)

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `transformometro-api/tm_app/interface/http/routes/crud_routes.py` | Adicionados `_PERSONAL_DATA_FIELDS` e `_mask_personal_data()` que mascara campos pessoais no payload do audit log |
| `shared/delpi_auth/middleware/fastapi_auth.py` | Respostas de erro genéricas (500/401) + logging interno |
| `core-api/app/interfaces/http/admin_statistics_controller.py` | `server_error()` genérico + logging interno |

---

## Fase 7 — Transparência e Registro de Tratamento

**Ref. LGPD:** Art. 37 (ROPA), Art. 41 (DPO), Art. 9 (direito à informação)

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| `core-api/app/domain/lgpd/privacy_constants.py` | Constantes centralizadas: DPO, purposes de consentimento, prazos de retenção |
| `core-api/app/domain/lgpd/__init__.py` | Pacote Python |
| `docs/13-auditoria-lgpd/ropa-registro-tratamento.md` | ROPA (Registro de Operações de Tratamento) com 8 categorias documentadas |

### Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `core-api/app/interfaces/http/me_controller.py` | Endpoint `GET /me/privacy` com info do DPO, política, purposes e direitos do titular |

---

## Novos Endpoints (Resumo)

| Método | Rota | Proteção | Fase |
|--------|------|----------|------|
| `GET` | `/me/consents` | `@require_auth()` | 2 |
| `POST` | `/me/consents/<purpose>` | `@require_auth()` | 2 |
| `DELETE` | `/me/consents/<purpose>` | `@require_auth()` | 2 |
| `GET` | `/me/data-export` | `@require_auth()` | 5 |
| `GET` | `/me/privacy` | `@require_auth()` | 7 |
| `POST` | `/admin/rbac/users/<id>/anonymize` | `@require_superadmin()` | 4 |

---

## Checklist de Deploy para Produção

- [ ] Executar migration: `flask db upgrade` (tabela `user_consents`)
- [ ] Definir variável de ambiente `KEYCLOAK_AUDIENCE` em todos os serviços
- [ ] Definir variável `JWT_SECRET` real (não usar default vazio)
- [ ] Agendar cron para `flask data-retention run` (recomendado: diário)
- [ ] Configurar DPO real em `privacy_constants.py`
- [ ] Publicar política de privacidade na URL configurada
- [ ] Revisar e validar o ROPA (`docs/13-auditoria-lgpd/ropa-registro-tratamento.md`)

---

## Artigos da LGPD Referenciados

| Artigo | Tema | Fases |
|--------|------|-------|
| Art. 6 III | Minimização | 6 |
| Art. 6 VII | Segurança e prevenção | 1 |
| Art. 7 I | Consentimento | 2 |
| Art. 8 | Requisitos do consentimento | 2 |
| Art. 9 | Direito à informação | 7 |
| Art. 15 | Término do tratamento | 3 |
| Art. 16 | Eliminação de dados | 3 |
| Art. 18 IV | Anonimização/eliminação | 4 |
| Art. 18 V | Portabilidade | 5 |
| Art. 18 VI | Eliminação | 4 |
| Art. 18 IX | Revogação do consentimento | 2 |
| Art. 37 | Registro de tratamento (ROPA) | 7 |
| Art. 41 | Encarregado (DPO) | 7 |
| Art. 46 | Segurança | 1, 6 |
