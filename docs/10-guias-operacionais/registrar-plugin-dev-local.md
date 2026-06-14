# Guia: registrar manifesto de plugin (dev local)

> **Arquivo:** `docs/10-guias-operacionais/registrar-plugin-dev-local.md`  
> **Status:** documentação operacional (dev)  
> **Complementa:** [registrar-plugin.md](./registrar-plugin.md)

Passo a passo para **registrar ou atualizar** um manifesto na Core API em ambiente de desenvolvimento, usando o token JWT do Portal **sem colar credenciais no terminal** a cada execução.

---

## 1. O que este guia cobre

| Etapa | Onde |
|---|---|
| Credenciais dev (gitignored) | `infra/.env.local` |
| Modelo para copiar | `infra/env.local.example` |
| Obter JWT automaticamente | `infra/scripts/get-dev-token.sh` |
| Registrar manifesto | `plugins/<id>/scripts/register-manifest.sh` |
| Endpoint | `POST /core-api/admin/apps/register` |

**Credenciais não ficam neste documento nem no Git.** Elas vivem somente em `infra/.env.local` (ignorado por `infra/.gitignore`).

---

## 2. Configuração única (primeira vez)

Na raiz do repositório:

```bash
cp infra/env.local.example infra/.env.local
```

Edite `infra/.env.local` e preencha:

| Variável | Descrição |
|---|---|
| `DEV_BASE_URL` | URL do gateway dev (padrão: `http://localhost`) |
| `DEV_KC_REALM` | Realm Keycloak (padrão: `delpi`) |
| `DEV_KC_CLIENT_ID` | Client público do Portal (padrão: `delpi-central`) |
| `DEV_PORTAL_USERNAME` | Usuário Keycloak com `apps.manage` ou superadmin |
| `DEV_PORTAL_PASSWORD` | Senha desse usuário no realm dev |

O usuário precisa existir no Keycloak **e** ter permissão de registrar apps (`apps.manage`) ou ser superadmin na Core API.

---

## 3. Pré-requisitos antes de registrar

```bash
cd infra
docker compose -f docker-compose.dev.yml ps core-api gateway keycloak
curl -s http://localhost/core-api/health
```

Esperado: Core API **200** (`{"status":"Api rodando!"}`).

Para MFEs, o container do plugin também deve estar no Compose e acessível, por exemplo:

```bash
curl -sI http://localhost/apps/<plugin-id>/assets/remoteEntry.js | head -5
```

Guia de stack: [subir-ambiente-dev.md](./subir-ambiente-dev.md).

---

## 4. Obter token (dev)

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
```

O script:

1. Lê `infra/.env.local`
2. Chama Keycloak (`password grant`)
3. Imprime **somente** o `access_token` (para usar em `TOKEN=`)

**Não commitar** o valor retornado. Tokens expiram — gere outro quando receber 401.

Alternativa manual: login no Portal → DevTools → Network → copiar `Authorization` de `GET /core-api/me` (ver [registrar-plugin.md](./registrar-plugin.md) §5).

---

## 5. Registrar manifesto

Cada plugin costuma ter um script em `plugins/<id>/scripts/register-manifest.sh`.

Exemplo — **Cultura DELPI**:

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/cultura-delpi/scripts/register-manifest.sh
```

Outros plugins (mesmo padrão):

| Plugin | Manifesto | Script |
|---|---|---|
| Cultura DELPI | `plugins/cultura-delpi/cultura-delpi.manifest.json` | `plugins/cultura-delpi/scripts/register-manifest.sh` |
| Eficiência Fabril | `plugins/eficiencia-fabril/eficiencia-fabril.manifest.json` | `plugins/eficiencia-fabril/scripts/register-manifest.sh` |
| Central de Agendamento | `plugins/central-agendamento/central-agendamento.manifest.json` | `plugins/central-agendamento/scripts/register-manifest.sh` |
| Auditoria 5S | `plugins/auditoria-5s/auditoria-5s.manifest.json` | `plugins/auditoria-5s/scripts/register-manifest.sh` |

Lista completa de manifestos: [registrar-plugin.md](./registrar-plugin.md) §3.

**Sucesso:** HTTP **201** e corpo `{"ok": true}`.

---

## 6. Validar após o registro

Com o mesmo `TOKEN`:

```bash
# Manifesto vigente
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost/core-api/admin/apps/cultura-delpi/manifest | python3 -m json.tool

# Rotas persistidas
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost/core-api/admin/apps/cultura-delpi/routes | python3 -m json.tool

# Permissões criadas (ajuste o query q=)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost/core-api/admin/rbac/permissions?q=cultura-delpi" | python3 -m json.tool

# Apps visíveis ao usuário logado
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost/core-api/me/apps | python3 -m json.tool
```

Substitua `cultura-delpi` pelo `id` do plugin.

---

## 7. RBAC (obrigatório para usuários comuns)

O registro **cria** permissões no catálogo; **não** libera acesso automaticamente.

1. Admin → RBAC → associar permissões do plugin (ex.: `cultura-delpi.view`) às roles
2. Ou usar superadmin (vê todos os apps em `/me/apps`)

Detalhes: [registrar-plugin.md](./registrar-plugin.md) §9 e [rbac.md](../03-autenticacao-autorizacao/rbac.md).

---

## 8. Atualizar manifesto existente

| Tipo de mudança | Ação |
|---|---|
| Nome, ícone, labels de rota, `showInMenu` | `PUT /core-api/admin/apps/<id>/manifest` |
| Nova `version`, `basePath`, permissões ou rotas | Novo `POST /register` com SemVer maior no JSON |

Bump de versão no arquivo `*.manifest.json` antes de registrar de novo.

---

## 9. Erros comuns (dev)

| Sintoma | Causa provável | Ação |
|---|---|---|
| `[ERRO] infra/.env.local não encontrado` | Arquivo local não criado | `cp infra/env.local.example infra/.env.local` |
| Keycloak `invalid_grant` | Usuário/senha errados no `.env.local` | Corrigir `DEV_PORTAL_*` |
| 401 no register | Token expirado | Rodar `get-dev-token.sh` de novo |
| 403 no register | Usuário sem `apps.manage` / superadmin | Usar conta admin ou ajustar RBAC |
| 400 `version_already_exists` | Mesma versão já registrada | Incrementar `version` no manifesto |
| Plugin não no menu | RBAC não configurado | Associar permissão à role |

---

## 10. Checklist rápido

- [ ] `infra/.env.local` existe (não versionado) com `DEV_PORTAL_USERNAME` / `DEV_PORTAL_PASSWORD`
- [ ] Stack dev up (`core-api`, `gateway`, `keycloak`)
- [ ] `export TOKEN="$(bash infra/scripts/get-dev-token.sh)"`
- [ ] `bash plugins/<id>/scripts/register-manifest.sh` → 201
- [ ] Validar manifesto, rotas e permissões via API admin
- [ ] RBAC para usuários finais (se necessário)
- [ ] `remoteEntry.js` acessível (se MFE)

---

## 11. Documentos relacionados

- [registrar-plugin.md](./registrar-plugin.md) — contrato, endpoints, Portal Admin
- [subir-ambiente-dev.md](./subir-ambiente-dev.md) — subir stack
- [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md) — schema JSON
- [../08-plugins/README.md](../08-plugins/README.md) — inventário de plugins
