# Guia: reset de banco em desenvolvimento

> **Arquivo:** `docs/10-guias-operacionais/reset-banco-dev.md`  
> **Status:** documentação oficial  
> **Escopo:** reset destrutivo dos volumes Docker locais

---

## 1. Objetivo

Recriar do zero os dados locais quando migrations, RBAC, Keycloak ou plugins ficaram inconsistentes.

**Não usar em produção nem em ambientes com dados que precisam ser preservados.**

---

## 2. O que é apagado com `down -v`

| Volume / dado | Conteúdo perdido |
|---|---|
| `postgres-core` | Usuários, apps, RBAC, favoritos, notificações |
| `keycloak-db` | Realm, clients, usuários Keycloak |
| `postgres-plugins` | Dados do AI API / pgvector (se existirem) |
| Volume Ollama | Modelos baixados localmente |

O **código** e as **migrations versionadas** em `core-api/migrations/` **não** são apagados pelo Compose.

---

## 3. Caminho recomendado (padrão)

Na maioria dos casos, **não** apague a pasta `core-api/migrations`. O entrypoint da Core API já executa `flask db upgrade` ao subir.

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build -d
```

Aguardar containers saudáveis (Keycloak pode levar 1–2 min na primeira subida).

Validar:

```bash
curl -s http://localhost/core-api/health
# {"status":"Api rodando!"}
```

Depois:

1. [configurar-keycloak.md](./configurar-keycloak.md) — realm, client, audience
2. Login no Portal com usuário cujo e-mail = `INITIAL_SUPERADMIN_EMAIL` (promoção a superadmin no primeiro `/me`)
3. [registrar-plugin.md](./registrar-plugin.md) — manifestos dos plugins

---

## 4. Migrations

### Automático (normal)

`core-api/docker-entrypoint.sh`:

```text
aguarda DB → flask db upgrade → inicia app
```

Conferir:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db current
docker compose -f docker-compose.dev.yml logs core-api | tail -20
```

### Manual (se o entrypoint falhou)

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

---

## 5. Recriar Alembic do zero (só emergência local)

Use **apenas** se a pasta `migrations/` foi corrompida ou revisions estão irreconciliáveis — e **nunca** em produção.

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v

cd ..
rm -rf core-api/migrations

cd infra
docker compose -f docker-compose.dev.yml up --build -d

docker compose -f docker-compose.dev.yml exec core-api sh -c "
  flask db init &&
  flask db migrate -m 'initial schema' &&
  flask db upgrade
"
```

O repositório já versiona `migrations/versions/7aa51b680332_*.py`; prefira sempre `flask db upgrade` sem apagar migrations.

---

## 6. Validar Postgres Core

Use credenciais de `POSTGRES_CORE_*` no `infra/.env`:

```bash
docker exec -it delpi-postgres-core psql -U "$POSTGRES_CORE_USER" -d "$POSTGRES_CORE_DB" -c '\dt'
```

Tabelas esperadas (entre outras): `users`, `roles`, `permissions`, `apps`, `app_routes`, `app_manifests`, `app_versions`, `notifications`, `audit_logs`.

---

## 7. Postgres Plugins (pgvector)

O init script só garante extensão básica:

```sql
-- infra/docker/postgres/plugins-init.sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

Schema do **Minha DELPI AI API** pode exigir migrations próprias após reset — ver documentação em `minha-delpi-ai-api/`.

Teste de conexão:

```bash
docker exec -it delpi-postgres-plugins psql -U plugins_user -d plugins_hub -c '\dx'
```

---

## 8. Ollama após reset

Modelos precisam ser baixados de novo:

```bash
docker exec -it delpi-ollama ollama pull qwen2.5:1.5b
docker exec -it delpi-ollama ollama pull bge-m3
```

---

## 9. Keycloak

Volumes apagados = realm, client `delpi-central`, mappers e usuários sumiram.

Siga [configurar-keycloak.md](./configurar-keycloak.md).

Checklist mínimo:

- [ ] Realm `delpi` (ou valor do `.env`)
- [ ] Client público + redirect `http://localhost/*`
- [ ] Audience `delpi-central` no token
- [ ] Usuário com e-mail do superadmin

---

## 10. Registrar plugins novamente

Registros em `apps` / `app_manifests` foram perdidos. Exemplos com manifestos do monorepo (token de superadmin ou role com `apps.manage`):

```bash
TOKEN="<access_token>"

curl -s -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @../plugins/strategic-indicators/strategic-indicators.manifest.json

curl -s -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @../plugins/minha-delpi-chat/delpi.manifest.json

curl -s -X POST http://localhost/core-api/admin/apps/register \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d @../plugins/dashboard-delpi/dashboard-delpi.manifest.json
```

Inventário completo: [../08-plugins/README.md](../08-plugins/README.md).

Associar permissões a roles em `/admin` ou via API RBAC (`/core-api/admin/rbac/*`).

---

## 11. Checklist pós-reset

- [ ] `docker compose ps` — containers Up
- [ ] `/core-api/health` → `Api rodando!`
- [ ] `/auth` abre Keycloak
- [ ] Login Portal OK
- [ ] `GET /core-api/me` → 200
- [ ] `GET /core-api/me/apps` → plugins (após registro + RBAC)
- [ ] `remoteEntry.js` de um MFE retorna JS
- [ ] Ollama com modelos (se usar chat)
- [ ] AI API health OK (se habilitada)

---

## 12. Comando rápido (resumo)

```bash
cd infra
docker compose -f docker-compose.dev.yml down -v
docker compose -f docker-compose.dev.yml up --build -d

# aguardar; depois Keycloak + login + registrar plugins
curl -s http://localhost/core-api/health
```

---

## 13. Documentos relacionados

- [subir-ambiente-dev.md](./subir-ambiente-dev.md)
- [configurar-keycloak.md](./configurar-keycloak.md)
- [registrar-plugin.md](./registrar-plugin.md)
- [troubleshooting.md](./troubleshooting.md)
- [../02-infraestrutura/docker-compose.md](../02-infraestrutura/docker-compose.md)
- [../04-core-api/migrations.md](../04-core-api/migrations.md)
