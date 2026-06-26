# Guia: registrar plugin

> **Arquivo:** `docs/10-guias-operacionais/registrar-plugin.md`  
> **Status:** documentação oficial  
> **API:** Core API `POST /admin/apps/register`

---

## 1. Objetivo

Persistir na Core API um plugin a partir do manifesto JSON: app, manifesto vigente, versão, permissões e rotas.

O registro **não** concede acesso aos usuários — é necessário RBAC depois.

---

## 2. Pré-requisitos

- Stack up ([subir-ambiente-dev.md](./subir-ambiente-dev.md))
- `flask db upgrade` aplicado (automático no boot da Core API)
- Keycloak configurado; usuário autenticado
- Permissão `apps.manage` **ou** `is_superadmin=true`
- Container do plugin no Compose (para MFE/iframe com assets)
- Gateway roteando `/apps/<id>/` para o container

---

## 3. Manifestos no monorepo

O nome do arquivo **varia**; o campo `id` no JSON é a chave estável.

| Plugin | Arquivo |
|---|---|
| Indicadores Estratégicos | `plugins/strategic-indicators/strategic-indicators.manifest.json` |
| Minha DELPI Chat | `plugins/minha-delpi-chat/delpi.manifest.json` |
| Dashboard LMPs | `plugins/dashboard-lmps/dash-lmps.manifest.json` |
| Dashboard Qualidade | `plugins/dashboard-quality/dashboard-quality.manifest.json` |
| Eficiência Fabril | `plugins/eficiencia-fabril/eficiencia-fabril.manifest.json` |
| Auditoria 5S | `plugins/auditoria-5s/auditoria-5s.manifest.json` |
| Central de Agendamento | `plugins/central-agendamento/central-agendamento.manifest.json` |
| Cultura DELPI | `plugins/cultura-delpi/cultura-delpi.manifest.json` |
| API DELPI (app admin) | `api-delpi/api-delpi.manifest.json` |

Contrato: [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md).  
Inventário: [../08-plugins/README.md](../08-plugins/README.md).

Campos obrigatórios no schema `1.0.0`: `schemaVersion`, `id`, `name`, `version`, `type`, `basePath`, `permissions` (com `code`, `name`, `module`).

Tipos: `microfrontend` | `iframe` | `backend-only`.

---

## 4. Endpoints

| Método | Path (Core API) | Path público (gateway) | Permissão |
|---|---|---|---|
| `POST` | `/admin/apps/register` | `/core-api/admin/apps/register` | `apps.manage` |
| `PUT` | `/admin/apps/<plugin_id>/manifest` | `/core-api/admin/apps/<id>/manifest` | `apps.manage` |
| `GET` | `/admin/apps/<plugin_id>/manifest` | idem | `apps.view` |

Superadmin ignora checagem de permissão nos decorators.

---

## 5. Registrar (curl)

**Dev local (token via `infra/.env.local`):** ver [registrar-plugin-dev-local.md](./registrar-plugin-dev-local.md).

Na raiz do repositório, com token do Portal (DevTools → rede → header `Authorization`):

```bash
export TOKEN="<access_token>"

curl -s -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @plugins/strategic-indicators/strategic-indicators.manifest.json
```

Resposta de sucesso: **201** `{"ok": true}`.

Erros de validação: **400** com `{"errors": [...]}`.

---

## 6. Via Portal Admin

Com superadmin ou `apps.manage`:

1. `http://localhost/admin` → área **Apps**
2. Upload ou colar JSON do manifesto
3. Confirmar registro

Útil quando não quiser montar curl manualmente.

---

## 7. Fluxo interno (register)

```text
JSON → ManifestValidator → RegisterPluginUseCase
  → app + app_manifests + app_versions
  → permissions + app_routes
  → audit plugin_registered
```

**Plugin novo:** insert completo.  
**Mesmo `id`, nova `version`:** atualiza manifesto vigente, histórico de versão, recria permissões/rotas do módulo.  
**Versão já existente:** erro `plugin.version_already_exists`.

---

## 8. Atualização sem nova versão

Alterações **não estruturais** (nome, ícone, `showInMenu`, labels de rota):

```http
PUT /core-api/admin/apps/<plugin_id>/manifest
```

Não use este endpoint para mudar `version`, `basePath`, lista de permissões ou rotas — isso exige novo `POST /register` com versão SemVer maior.

---

## 9. RBAC após registro

```text
register cria permissions
  → associar permission à role (/admin/rbac)
  → associar role ao usuário ou grupo
  → GET /me/apps passa a listar o plugin
```

Superadmin vê todos os apps ativos em `/me/apps` sem precisar de cada permission.

---

## 10. Validar carregamento

1. `GET /core-api/me/apps` — plugin na lista
2. Menu do Portal — item visível (`showInMenu`, permissão)
3. Assets MFE:

```bash
curl -sI http://localhost/apps/strategic-indicators/assets/remoteEntry.js | head -5
```

Deve retornar `200` e `Content-Type` JavaScript, não HTML do Portal.

4. Module Federation: export `mount` / `unmount` no remote.

---

## 11. Erros comuns

| Sintoma | Causa provável | Ação |
|---|---|---|
| 401 | Token ausente/expirado | Renovar login |
| 403 | Sem `apps.manage` | Role ou superadmin |
| 400 `schema_validation_error` | JSON fora do schema | Conferir manifesto |
| 400 `version_already_exists` | Bump `version` ou PUT não estrutural | |
| Menu vazio | Plugin não registrado ou sem RBAC | Register + roles |
| 404 em `remoteEntry.js` | Container `delpi-<id>` down ou id ≠ manifesto | Compose + gateway |
| HTML no lugar de JS | URL errada ou gateway 502 | Logs do plugin |

---

## 12. Checklist

- [ ] Manifesto válido (`schemaVersion: "1.0.0"`)
- [ ] `id` = nome do serviço Docker / location Nginx
- [ ] `basePath` e `entry` coerentes com build Vite
- [ ] `POST /register` → 201
- [ ] Permissões em roles (ou superadmin)
- [ ] `/me/apps` lista o plugin
- [ ] `remoteEntry.js` acessível (se MFE)

---

## 13. Documentos relacionados

- [registrar-plugin-dev-local.md](./registrar-plugin-dev-local.md) — token dev + script `register-manifest.sh`
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md)
- [../05-plugin-system/registro-de-plugin.md](../05-plugin-system/registro-de-plugin.md)
- [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)
- [../03-autenticacao-autorizacao/rbac.md](../03-autenticacao-autorizacao/rbac.md)
- [reset-banco-dev.md](./reset-banco-dev.md)
