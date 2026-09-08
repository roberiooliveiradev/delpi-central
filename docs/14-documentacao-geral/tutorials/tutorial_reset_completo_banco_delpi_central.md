# 🔄 Tutorial Oficial — Reset Completo do Banco (DELPI Central)

Este documento serve como **material de consulta permanente** para reinicializar completamente o banco de dados da DELPI Central em ambiente de desenvolvimento.

⚠️ **ATENÇÃO:**
Este procedimento apaga completamente:
- Banco PostgreSQL (Core)
- Banco PostgreSQL (Keycloak)
- Histórico de migrations
- Realm e configurações do Keycloak

Nunca utilizar em produção.

---

# 📍 Quando usar este procedimento?

Use quando ocorrer:

- ❌ Erro do Alembic: "Can't locate revision identified by ..."
- ❌ Banco dessincronizado com migrations
- ❌ Histórico de migrations corrompido
- ❌ Alterações estruturais grandes no schema
- ❌ Ambiente de desenvolvimento precisa ser limpo

---

# 🧨 ETAPA 1 — Derrubar todos os containers e volumes

Dentro da pasta `infra`:

```bash
docker compose down -v
```

O que isso faz:
- Remove containers
- Remove redes
- Remove volumes (postgres_core_data, keycloak_data)
- Apaga completamente os bancos

---

# 🧹 ETAPA 2 — Apagar pasta de migrations

Volte para a raiz do projeto:

```bash
cd ..
```

Remova a pasta de migrations da Core API:

```bash
rm -rf core-api/migrations
```

⚠️ Isso é essencial para evitar conflito de revisions antigas.

---

# 🏗 ETAPA 3 — Subir containers novamente

Volte para a pasta infra:

```bash
cd infra
```

Suba novamente os serviços:

```bash
docker compose up --build
```

Espere todos os containers iniciarem corretamente.

---

# 🔐 ETAPA 4 — Entrar no container da Core API

```bash
docker exec -it delpi-core-api sh
```

---

# 🧱 ETAPA 5 — Recriar Alembic do ZERO

Dentro do container:

```bash
flask db init
```

Depois:

```bash
flask db migrate -m "initial full schema"
```

Depois:

```bash
flask db upgrade
```

Se tudo estiver correto, aparecerá:

```
INFO  [alembic.runtime.migration] Running upgrade
```

---

# 🔎 ETAPA 6 — Validar estrutura do banco

Abra outro terminal e entre no PostgreSQL:

```bash
docker exec -it delpi-postgres-core psql -U delpi -d delpi_core
```

Liste as tabelas:

```sql
\dt
```

Você deve ver tabelas como:

- users
- roles
- permissions
- groups
- apps
- app_routes
- user_favorite_apps
- audit_logs
- etc

Digite para sair:

```sql
\q
```

---

# 🔐 ETAPA 7 — Reconfigurar Keycloak

Como os volumes foram apagados, o Keycloak perdeu:

- Realm
- Client
- Usuários

Você deve recriar:

1. Realm: `delpi`
2. Client: `delpi-central`
3. Authorization Code + PKCE
4. Audience: `delpi-central`
5. Usuário inicial (superadmin)

---

# 📌 ETAPA 8 — Testar a API

Teste o healthcheck:

```bash
curl http://localhost/core-api/health
```

Deve retornar:

```json
{"status":"ok"}
```

---

# 🧠 Checklist Final

Após reset completo, o ambiente deve estar:

- ✅ Banco sincronizado com migrations
- ✅ Alembic sem erro de revision
- ✅ Containers rodando
- ✅ Keycloak acessível
- ✅ Core API respondendo
- ✅ Plugin pode ser registrado novamente

---

# 🚀 Dica Arquitetural

Durante fases estruturais do projeto (RBAC, Plugins, Favorites, etc):

✔ É aceitável resetar banco frequentemente

Após entrar em produção:

❌ Nunca utilizar `docker compose down -v`

---

# 📚 Comando Rápido (Resumo)

```bash
# 1
cd infra
docker compose down -v

# 2
cd ..
rm -rf core-api/migrations

# 3
cd infra
docker compose up --build

# 4
docker exec -it delpi-core-api sh

# 5
flask db init
flask db migrate -m "initial full schema"
flask db upgrade
```

---

Documento oficial de consulta — Reset de Ambiente DELPI Central 🚀

