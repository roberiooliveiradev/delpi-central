# Minha DELPI — Docker Compose

> **Arquivo:** `docs/02-infraestrutura/docker-compose.md`  
> **Status:** documentação oficial (alinhada a `infra/docker-compose*.yml`)  
> **Execução:** sempre a partir da pasta `infra/`

---

## 1. Arquivos

| Arquivo | Uso |
|---|---|
| `infra/docker-compose.dev.yml` | Desenvolvimento local |
| `infra/docker-compose.yml` | Produção (imagens prod, sem volumes de código) |
| `infra/.env` | Variáveis compartilhadas (não versionar segredos) |

Comando base:

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build -d
```

---

## 2. Serviços (visão completa)

### Núcleo da plataforma

| Serviço Compose | Container | Imagem / build | Função |
|---|---|---|---|
| `postgres-core` | `delpi-postgres-core` | `postgres:15` | Banco Core API |
| `keycloak-db` | `delpi-keycloak-db` | `postgres:15` | Banco Keycloak |
| `keycloak` | `delpi-keycloak` | Keycloak 24 | SSO / OIDC |
| `core-api` | `delpi-core-api` | `core-api/Dockerfile.*` | Governança Flask |
| `portal` | `delpi-portal` | `portal/Dockerfile.*` | Shell React |
| `gateway` | `delpi-gateway` | `gateway/Dockerfile.*` | Nginx :80 |

### APIs e dados operacionais

| Serviço | Container | Função |
|---|---|---|
| `postgres-plugins` | `delpi-postgres-plugins` | PostgreSQL **pgvector** — plugins + AI |
| `api-delpi` | `delpi-api-delpi` | FastAPI TOTVS / domínios |
| `strategic-indicators-api` | `delpi-strategic-indicators-api` | API Indicadores Estratégicos (`/strategic-indicators`) |
| `minha-delpi-ai-api` | `delpi-minha-delpi-ai-api` | Chat, agentes, RAG |

### IA local (dev/prod)

| Serviço | Container | Função |
|---|---|---|
| `ollama` | `delpi-ollama` | LLM/embeddings locais (`:11434`) |
| `vllm` | `delpi-vllm` | Opcional, profile `gpu` (produção) |

### Plugins frontend (microfrontends)

| Serviço | Container | Pasta |
|---|---|---|
| `strategic-indicators` | `delpi-strategic-indicators` | `plugins/strategic-indicators` |
| `minha-delpi-chat` | `delpi-minha-delpi-chat` | `plugins/minha-delpi-chat` |
| `dashboard-lmps` | `delpi-dashboard-lmps` | `plugins/dashboard-lmps` |
| `dashboard-delpi` | `delpi-dashboard-delpi` | `plugins/dashboard-delpi` |

O Nginx resolve plugins como `http://delpi-<id>/` quando a URL é `/apps/<id>/assets/...`.

---

## 3. Rede e volumes

```yaml
networks:
  delpi-network:

volumes:
  postgres_core_data
  keycloak_data
  postgres_plugins_data
  ollama_data          # dev + prod
  vllm_cache           # prod, profile gpu
```

Comunicação interna por **nome do serviço** (`core-api`, `postgres-plugins`, etc.).

---

## 4. Portas expostas (desenvolvimento)

| Porta host | Serviço |
|---:|---|
| `80` | Gateway (única entrada HTTP da plataforma) |
| `5432` | Postgres Core |
| `5433` | Postgres Plugins (pgvector) |
| `11434` | Ollama (opcional, acesso direto ao modelo) |

Em **produção**, apenas o gateway expõe `80`; bancos ficam na rede interna.

---

## 5. Diferenças dev vs prod

| Aspecto | Dev | Prod |
|---|---|---|
| Keycloak | `start-dev` | `start` |
| Código montado | Sim (`../core-api:/app`, etc.) | Não |
| `postgres-plugins` | `pgvector/pgvector:pg15` | `pgvector/pgvector:pg15` |
| Gateway config | Volume `nginx.dev.conf` | Embutido na imagem |
| Ollama | Sim, porta 11434 | Sim |
| Logs rotacionados | Parcial | `json-file` 10m×3 em serviços críticos |

---

## 6. Serviços em detalhe

### `core-api`

- **Dev:** `Dockerfile.dev`, volume `../core-api:/app`
- **Env:** `DB_*` → `postgres-core`, `KEYCLOAK_*` JWT, `INITIAL_SUPERADMIN_*`
- **Migrations:** `flask db upgrade` dentro do container

### `minha-delpi-ai-api`

- **Migrations:** `docker-entrypoint.sh` → `flask db upgrade` no boot (como a Core API)
- **DATABASE_URL:** `postgres-plugins` (mesmo banco dos plugins, com pgvector)
- **CORE_API_BASE_URL:** `http://core-api:8000`
- **LLM (dev):** `OLLAMA_BASE_URL=http://ollama:11434`, modelo default `qwen2.5:1.5b`
- **Gateway público:** `/apps/minha-delpi-ai/api/`
- Doc de rotas: `minha-delpi-ai-api/docs/api/`

Após primeiro `up`, pode ser necessário puxar modelos no Ollama:

```bash
docker exec -it delpi-ollama ollama pull qwen2.5:1.5b
docker exec -it delpi-ollama ollama pull bge-m3
```

### `api-delpi`

- **env_file:** `infra/.env`
- **TOTVS:** `TOTVS_DB_*` mapeados para `DB_*` no container
- **Plugins DB:** `PLUGINS_DB_*`
- **Portal RH (opcional):** `PORTAL_RH_DB_*`
- Volume dev: `../api-delpi:/app`

### `strategic-indicators-api`

- **env_file:** `infra/.env`
- **TOTVS:** `TOTVS_DB_*` → `DB_*` (mesmo padrão da api-delpi)
- **Plugins DB:** `PLUGINS_DB_*` (catálogo, metas, settings)
- **Portal RH (opcional):** `PORTAL_RH_DB_*`
- **Performance (Compose):** `SI_WARMUP_ON_STARTUP=true` (padrão), `SI_WARMUP_TRENDS_MONTHS=6`, `SI_SNAPSHOT_CACHE_TTL_SECONDS=600`, `TOTVS_POOL_*`
- Volume dev: `../strategic-indicators-api:/app`
- Migrations: `migrations/` + `scripts/run_migrations.py` (`SI_RUN_MIGRATIONS_ON_STARTUP=true` em dev)
- Warm-up manual: `docker exec delpi-strategic-indicators-api python3 scripts/warmup_si_snapshots.py`

### `postgres-plugins`

Imagem **pgvector** (não Postgres plain) — necessário para embeddings do chat/RAG.

Init: `infra/docker/postgres/plugins-init.sql`

### `gateway` (dev `depends_on`)

```text
portal, core-api, keycloak, strategic-indicators, strategic-indicators-api, api-delpi,
dashboard-lmps, minha-delpi-ai-api, minha-delpi-chat
```

`dashboard-delpi` não está no `depends_on` do gateway dev, mas o container deve existir se o plugin for usado.

---

## 7. Ordem lógica de subida

```text
postgres-core, keycloak-db, postgres-plugins
  → keycloak
  → core-api, ollama
  → minha-delpi-ai-api, api-delpi
  → portal, plugins
  → gateway
```

`depends_on` não garante readiness — aguardar ~30–60s após primeiro boot ou reiniciar APIs se falharem conexão.

---

## 8. Variáveis essenciais (grupos)

Ver também [variaveis-de-ambiente.md](./variaveis-de-ambiente.md).

| Grupo | Exemplos |
|---|---|
| Core DB | `POSTGRES_CORE_*`, `DB_HOST=postgres-core` |
| Keycloak | `POSTGRES_KC_*`, `KC_HOSTNAME`, `KEYCLOAK_ADMIN_*` |
| JWT | `KEYCLOAK_JWKS_URL`, `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE` |
| Portal | `VITE_KC_URL`, `VITE_KC_REALM`, `VITE_KC_CLIENT_ID` |
| TOTVS | `TOTVS_DB_HOST`, … |
| Plugins DB | `PLUGINS_DB_*` |
| AI (prod) | `LLM_PROVIDER`, `OLLAMA_*`, `VLLM_*` |

---

## 9. Comandos úteis

```bash
# Subir dev
docker compose -f docker-compose.dev.yml up --build -d

# Logs
docker compose -f docker-compose.dev.yml logs -f core-api

# Parar (manter dados)
docker compose -f docker-compose.dev.yml down

# Reset total dos bancos locais
docker compose -f docker-compose.dev.yml down -v

# Migrations Core API
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

---

## 10. Validação rápida

| URL | Esperado |
|---|---|
| `http://localhost/` | Portal |
| `http://localhost/core-api/health` | `{"status":"Api rodando!"}` |
| `http://localhost/auth` | Keycloak |
| `http://localhost/apps/api-delpi/health` | API DELPI online |
| `http://localhost/apps/minha-delpi-ai/api/health` | AI API (se habilitada) |

---

## 11. Documentos relacionados

- [gateway-nginx.md](./gateway-nginx.md)
- [ambientes-dev-prod.md](./ambientes-dev-prod.md)
- [bancos-de-dados.md](./bancos-de-dados.md)
- [../10-guias-operacionais/subir-ambiente-dev.md](../10-guias-operacionais/subir-ambiente-dev.md)
