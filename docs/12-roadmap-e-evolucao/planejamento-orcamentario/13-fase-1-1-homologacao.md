# 13 — Fase 1.1 — Estabilização, integração e homologação

**Branch:** `feat/planejamento-orcamentario`  
**Data:** 2026-08-04  
**Escopo:** revisão da Fase 1, migration real, testes, upload UI, picker de usuários, Compose/Gateway/scripts, smoke técnico.  
**Fora:** Receita, Pessoal, CAPEX, TOTVS, Excel/PDF, Fase 2.  
**Commit:** nenhum (conforme brief).

---

## Status

```text
STATUS: BLOQUEADO
```

Bloqueios externos comprovados:

1. **Token Keycloak de desenvolvimento** — `infra/scripts/get-dev-token.sh` falhou (`Falha ao obter token em http://localhost/auth/realms/delpi/...`). Realm responde HTTP 200; credenciais em `infra/.env.local` existem, mas o grant não emitiu JWT. Sem token: manifesto, RBAC, menu e smoke autenticado não puderam ser concluídos.
2. **Smoke E2E autenticado** (login → menu → fluxo admin/confirmação) — dependente do item 1.

Itens técnicos de fundação (migration, API, build MFE, container, Gateway, testes unitários) foram executados e passaram.

---

## 1. Revisão da Fase 1

### Problemas encontrados

| Item | Achado |
|------|--------|
| Ambiente | Docker ok fora do sandbox; `npm` ausente no PATH do host; `node_modules`/`dist` do MFE owned by `root` (build anterior via Docker) |
| Upload UI | API multipart existia; UI admin sem upload |
| Escopos | UI exigia digitação manual de `user_sub` |
| Infra | Serviço MFE, volume de upload, `FASE_MFE` e `gateway.depends_on` ausentes |
| Endpoint listagem admin de documentos | Faltava `GET /admin/guidance/{id}/documents` |
| Loading admin sem permissão | `useEffect` retornava cedo e deixava `loading=true` |

### Problemas corrigidos

- UI upload multipart + progresso (XHR) + listar/editar metadados/arquivar/baixar
- `UserDirectoryPicker` + `GET /core-api/me/directory/users`
- Compose dev/prod + volume `PLANEJAMENTO_ORCAMENTARIO_UPLOAD_DIR`
- Scripts sequenciais (dev/prod)
- Contrato `list_planejamento_orcamentario_admin_documents`
- Testes backend/MFE ampliados
- Loading liberado quando sem permissão administrativa

### Decisões preservadas

- Schema `planejamento_orcamentario` na api-delpi
- Estados `draft|open|closing|locked|archived`
- Catálogo org interno (sem TOTVS)
- Confirmação por `user_sub + guidance_version_id`
- Um rascunho simultâneo por exercício (índice parcial)
- Auditoria append-only com trigger

### Divergências

- Versão do manifesto permanece `0.1.0` (não registrada)
- `~/.delpi` no host é owned by `root`; volume de upload foi criado pelo Docker no mount

---

## 2. Migration e banco

### Revisão V001 (já aplicada — **não editada**)

Confirmação no PostgreSQL real (`postgres-plugins` via `delpi-api-delpi`):

| Requisito | Evidência |
|-----------|-----------|
| Ack → versão imutável | FK `reading_acknowledgements.guidance_version_id` + `UNIQUE (user_sub, guidance_version_id)` (`uq_po_ack_user_version`) |
| Um draft simultâneo | `uq_po_guidance_one_draft_per_exercise … WHERE status='draft'` |
| Um exercício ativo | `uq_po_budget_exercises_one_active … WHERE is_active=true` |
| Versões publicadas | `uq_po_guidance_version_number` + check `published` exige `version_number`/`published_at` |
| Auditoria append-only | trigger `trg_po_audit_no_update` |

**Alterações na V001 nesta fase:** nenhuma (imutável após apply).

### Comandos

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin planejamento-orcamentario
# Resultado: V001 | create_budget_planning_core | APLICADA

# up idempotente (já aplicada — não recria)
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin planejamento-orcamentario
```

### Tabelas inspecionadas

`audit_events`, `budget_exercises`, `guidance_premises`, `guidance_schedule_items`, `guidance_versions`, `org_areas`, `org_cost_centers`, `org_units`, `reading_acknowledgements`, `schema_migrations`, `support_documents`, `user_org_scopes`

---

## 3. Backend

| Comando | Resultado |
|---------|-----------|
| `docker exec delpi-api-delpi python -m pytest tests/unit/planejamento_orcamentario -q` | **17 passed** |
| Lint/format/typecheck Python local | Não há toolchain host (sem venv); testes no container |
| API health pós-recreate | `healthy` |
| GET context/guidance sem auth | **401** (esperado) |

Cobertura unitária ampliada: multi-versão/ack por `guidance_version_id`, unicidade de ano + um ativo, documento sem `storage_key` na resposta/auditoria, download sem permissão.

---

## 4. Frontend

| Item | Resultado |
|------|-----------|
| Upload admin | Implementado (multipart + progresso + estados) |
| Pesquisa usuários | `UserDirectoryPicker` + Core directory |
| Lint | 0 errors / warnings pré-existentes `set-state-in-effect` |
| Typecheck | OK (`tsc`) |
| Vitest | **11 passed** |
| Build | OK — `dist/assets/remoteEntry.js` |
| Toolchain | `docker run node:20-alpine` (host sem `npm`) |

---

## 5. Infraestrutura

| Item | Ação |
|------|------|
| `infra/docker-compose.dev.yml` | Serviço `planejamento-orcamentario` + env/volume upload |
| `infra/docker-compose.yml` | Idem + `gateway.depends_on` |
| `up-dev-sequential.sh` / `up-prod-sequential.sh` | `FASE_MFE` += `planejamento-orcamentario` |
| Gateway nginx | Genérico `/apps/<id>/assets/*` — **sem bloco novo** |
| `nginx -t` (container) | OK |
| Container MFE | `delpi-planejamento-orcamentario` Up |
| `remoteEntry.js` | **HTTP 200** `application/javascript` |

Deploy usado:

```bash
./infra/scripts/up-dev-sequential.sh --fase mfe --build planejamento-orcamentario
# recreate api-delpi (volume upload)
cd infra && docker compose -f docker-compose.dev.yml -f docker-compose.minimal.yml up -d --force-recreate --no-deps api-delpi
```

---

## 6. Manifesto e RBAC

### Manifesto

- Arquivo: `plugins/planejamento-orcamentario/planejamento-orcamentario.manifest.json`
- Versão: `0.1.0`
- Permissões: access, guidance.view, guidance.manage, scopes.manage, admin
- Registro: **BLOCKED** (sem JWT)

Comando para execução posterior:

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
export BASE_URL=http://localhost
bash plugins/planejamento-orcamentario/scripts/register-manifest.sh
```

### Matriz RBAC (planejada — não aplicada)

| Perfil | Permissões |
|--------|------------|
| Gestor | `access`, `guidance.view` |
| Admin planejamento | `access`, `guidance.view`, `guidance.manage`, `scopes.manage`, `admin` |

Pesquisa de usuários usa `/core-api/me/directory/users` (permissão Core do diretório do usuário autenticado). Sem bypass Keycloak. Remoção pós-homologação: retirar roles/grupos atribuídos no Keycloak/Core — não `is_superadmin`.

---

## 7. Smoke test

| # | Passo | Resultado |
|---|-------|----------|
| 1 | login Minha DELPI | BLOCKED (token) |
| 2 | plugin no menu (autorizado) | BLOCKED |
| 3 | invisível sem acesso | BLOCKED |
| 4 | rota sem novo login | BLOCKED |
| 5 | `remoteEntry.js` 200 | **PASS** |
| 6 | contexto API autenticado | BLOCKED |
| 7–12 | fluxo admin (exercício→docs→publish) | BLOCKED |
| 13–16 | gestor lê/confirma | BLOCKED (unitário PASS) |
| 17–18 | módulos + nova versão | BLOCKED (unitário PASS) |
| 19–20 | admin oculto / IDOR download | BLOCKED (unitário PASS p/ download) |
| — | API sem auth → 401 | **PASS** |
| — | Gateway `nginx -t` | **PASS** |
| — | Migration APLICADA + schema | **PASS** |

---

## 8. Segurança

| Tema | Situação |
|------|----------|
| JWT | Endpoints exigem auth (401 sem token) |
| Autorização | `@require_any_permission` por rota |
| IDOR download | Sem permissão → `BudgetUserNotAuthorizedError` (teste) |
| Arquivos | Validação MIME/extensão/tamanho; path traversal bloqueado; `storage_key` não na API pública |
| Logs | Amostra pós-recreate sem JWT/binários |
| Escopos | CC só do catálogo; UI sem `user_sub` livre |

---

## 9. Arquivos principais (Fase 1.1)

**Criados:** `13-fase-1-1-homologacao.md`, `directoryApi.ts`, `documentUpload.ts`(+test), testes admin guidance/scopes.

**Alterados:** use cases/router/registry; AdminGuidance/Scopes/Exercises; httpClient/API; compose; scripts sequenciais; `env.local.example`; `README-ambiente.md`; `12-fase-1-implementacao.md`.

**Migrations:** V001 intacta (já aplicada).

---

## 10. Pendências reais

1. Corrigir grant Keycloak/`get-dev-token.sh` e registrar manifesto `0.1.0`.
2. Atribuir RBAC (roles/grupos) conforme matriz.
3. Smoke E2E autenticado completo (checklist §7).
4. Ajustar ownership de `~/.delpi` (root) se uploads precisarem de escrita por UID do processo — hoje o mount Docker criou o path.
5. Warnings ESLint `set-state-in-effect` (não bloqueantes).

---

## 11. Rollback operacional

```bash
# Parar só o MFE (não apaga schema/dados)
cd infra && docker compose -f docker-compose.dev.yml stop planejamento-orcamentario

# NÃO executar reset de migration em ambiente com dados
# docker exec delpi-api-delpi python scripts/run_plugins_migrations.py reset --plugin planejamento-orcamentario  # PROIBIDO
```

Desregistro de manifesto (após registro bem-sucedido): fluxo admin Core / versão nova — não editar tabelas Core à mão.
