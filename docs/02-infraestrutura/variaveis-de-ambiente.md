# Minha DELPI — Variáveis de ambiente

> **Arquivo:** `docs/02-infraestrutura/variaveis-de-ambiente.md`  
> **Status:** documentação oficial  
> **Fonte:** `infra/.env`, `infra/docker-compose*.yml`, Compose de cada serviço

---

## 1. Onde configurar

| Arquivo | Uso |
|---|---|
| `infra/.env` | Valores locais/dev (não versionar com secrets reais) |
| `infra/.env.prod` | Referência de produção (proteger) |
| `infra/docker-compose.dev.yml` | Injeta env nos containers |

Crie `infra/.env.example` apenas com chaves e comentários, sem valores de produção.

---

## 2. Segurança

Nunca commitar:

```text
*_PASSWORD, SECRET_KEY, *_CLIENT_SECRET
API_DELPI_JWT_SECRET, TOTVS_DB_PASSWORD
```

Variáveis `VITE_*` são **públicas** (embutidas no build do Portal).

---

## 3. Referência rápida por serviço

### Geral

| Variável | Exemplo dev | Descrição |
|---|---|---|
| `PUBLIC_BASE_URL` | `http://localhost` | URL pública do gateway (issuer, redirects) |
| `TZ` | `America/Sao_Paulo` | Timezone dos containers |

### Postgres Core + Core API

| Variável | Container alvo |
|---|---|
| `POSTGRES_CORE_*` | Criação do `postgres-core` |
| `DB_HOST` | `postgres-core` (rede Docker) |
| `DB_PORT` | `5432` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Conexão SQLAlchemy |
| `SECRET_KEY` | Flask |
| `FLASK_APP` | `app.create_app:create_app` |
| `FLASK_ENV` | `development` / `production` |
| `INITIAL_SUPERADMIN_EMAIL` | Bootstrap do primeiro admin |
| `INITIAL_SUPERADMIN_NAME` | Nome exibido |

### JWT / OIDC (Core API, API DELPI, AI API)

| Variável | Descrição |
|---|---|
| `KEYCLOAK_REALM` | Realm (ex.: `delpi`) |
| `KEYCLOAK_AUDIENCE` | Claim `aud` esperada (ex.: `delpi-central`) |
| `KEYCLOAK_ISSUER` | Issuer **público** — ex.: `${PUBLIC_BASE_URL}/auth/realms/${KEYCLOAK_REALM}` |
| `KEYCLOAK_JWKS_URL` | JWKS **interno** — ex.: `http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs` |
| `KEYCLOAK_ISSUER_INTERNAL` | Opcional, validação interna |
| `JWT_ALGORITHMS` | Ex.: `RS256` |

Regra crítica: o token emitido ao browser usa o issuer **público** (`localhost/auth/...`); containers validam via JWKS na rede Docker (`keycloak:8080/auth/...`).

### Keycloak server

| Variável | Dev típico |
|---|---|
| `KEYCLOAK_ADMIN` / `KEYCLOAK_ADMIN_PASSWORD` | Console admin |
| `POSTGRES_KC_*` | Banco `keycloak-db` |
| `KC_HTTP_RELATIVE_PATH` | `/auth` |
| `KC_HOSTNAME` | `localhost` (dev) / domínio real (prod) |
| `KC_PROXY` | `edge` |
| `KC_PROXY_HEADERS` | `xforwarded` |
| `KC_HOSTNAME_STRICT` | `false` (dev), `true` (prod) |

### Portal (build-time)

| Variável | Descrição |
|---|---|
| `VITE_KC_URL` | `${PUBLIC_BASE_URL}/auth` |
| `VITE_KC_REALM` | Igual `KEYCLOAK_REALM` |
| `VITE_KC_CLIENT_ID` | Client público (ex.: `delpi-central`) |
| `VITE_KC_REDIRECT_URI` | `${PUBLIC_BASE_URL}/` |
| `VITE_FRONT_CHANNEL_LOGOUT_URLS` | CSV opcional de URLs de logout em iframes |

### API DELPI

| Variável | Descrição |
|---|---|
| `TOTVS_DB_*` | SQL Server Protheus (mapeado para `DB_*` no container) |
| `PLUGINS_DB_*` | PostgreSQL plugins (`postgres-plugins`) |
| `PORTAL_RH_DB_*` | PostgreSQL RH (opcional) |
| `API_DELPI_PORT` | Porta interna (8000) |
| `API_DELPI_ENV` | `development` |
| `API_DELPI_JWT_SECRET` | Legado/auxiliar — validação principal é Keycloak |
| `GOOGLE_SHEETS_*`, `TRANSFORMA_MAIS_*`, `QUALITY_*`, `FINANCIAL_*`, etc. | Integrações planilhas (indicadores) |

### Minha DELPI AI API

Definidas no Compose (dev) — ver também `minha-delpi-ai-api` settings:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | Montada no Compose → `postgres-plugins` |
| `CORE_API_BASE_URL` | `http://core-api:8000` |
| `LLM_PROVIDER` | `ollama` ou `vllm` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` |
| `OLLAMA_MODEL` | Default **`qwen2.5:3b`** (CPU, bom equilíbrio qualidade/velocidade). Alternativas: `qwen2.5:7b` (GPU/16GB RAM), `qwen2.5:1.5b` (mínimo) |
| `OLLAMA_NUM_CTX` | Janela de contexto. **Recomendado:** `2048` (permite coexistência 3b + bge-m3 em 8GB); com 16GB+: `4096` |
| `OLLAMA_NUM_THREAD` | Threads CPU. Usar = nº de cores reais. **Prod 4 vCPU:** `4` |
| `OLLAMA_MAX_LOADED_MODELS` | Modelos simultâneos em RAM. **Prod 8 GB:** `2` (chat + embeddings coexistem com ctx=2048) |
| `OLLAMA_NUM_PARALLEL` / `OLLAMA_KEEP_ALIVE` | Serviço `ollama` no Compose |
| `LLM_MAX_TOKENS` | `num_predict` Ollama. **Recomendado:** `1536`; mínimo: `384` |
| `LLM_TEMPERATURE` | Criatividade das respostas. **Recomendado:** `0.4` (natural); `0.2` (mais determinístico) |
| `CHAT_SESSION_TITLE_LLM_ENABLED` | `true` recomendado — títulos automáticos melhoram UX |
| `CHAT_FAST_PATH_ENABLED` | `true` — pula RAG/tools em cumprimentos curtos (`olá`, `oi`). Max chars: `30` |
| `CHAT_TOOL_ROUTER_ENABLED` | `true` recomendado — LLM sugere ferramentas (melhora assertividade) |
| `CHAT_RAG_HYBRID_ENABLED` | `true` recomendado — busca vetorial + keyword combinados |
| `CHAT_RAG_RERANK_ENABLED` | `true` recomendado — boost por overlap de keywords |
| `CHAT_RAG_PREFER_KEYWORD_SEARCH` | `true` — usa FTS como busca principal |
| `CHAT_HISTORY_SUMMARY_ENABLED` | `true` recomendado — sumariza conversas longas para manter contexto |
| `CHAT_OPERATIONAL_FAST_PATH_ENABLED` | `true` — pula RAG pesado em perguntas operacionais curtas |
| `CHAT_EXTERNAL_ACTION_DIRECT_RESPONSE_ENABLED` | `true` — resposta formatada sem LLM após action |
| `EXTERNAL_ACTION_SEMANTIC_RANK_ENABLED` | `true` recomendado — ranking semântico de actions via embeddings |
| `MAX_CONTEXT_CHUNKS` | Chunks RAG máximos. **Recomendado:** `8` |
| `MAX_CONTEXT_CHARS` | Chars máximos de contexto RAG. **Recomendado:** `12000` |
| `RAG_CONTEXT_MIN_SCORE` | Default `0.35` (fallback `RAG_ASSERTIVENESS_MIN_SCORE`). Prod operacional: `0.40`–`0.45`. Ver [rag-context-min-score-calibracao.md](../../minha-delpi-ai-api/docs/roadmap/rag-context-min-score-calibracao.md) |
| `CHAT_FAST_PATH_MAX_CHARS` | Máximo de caracteres para fast path (sem LLM). **Recomendado:** `30` |
| `CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS` | Chars por chunk no streaming de respostas diretas. **Recomendado:** `4` |
| `CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS` | Delay em ms entre chunks de streaming direto. **Recomendado:** `20` (efeito de escrita natural) |
| `RAG_ASSERTIVENESS_MIN_SCORE` | Score mínimo em fluxos de assertividade (default `0.35`) |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` | Ex.: `bge-m3` |
| `RATE_LIMIT_*` | Limites por janela |
| `KNOWLEDGE_*` | Limites de ingestão RAG |
| `VLLM_*` | Produção com profile GPU |

### Keycloak Admin (Core API backend)

```env
KEYCLOAK_ADMIN_CLIENT_ID=
KEYCLOAK_ADMIN_CLIENT_SECRET=
KEYCLOAK_ADMIN_REALM=
KEYCLOAK_ADMIN_URL=http://keycloak:8080
```

---

## 4. Armadilha: dois significados de `DB_*`

| Serviço | `DB_HOST` aponta para |
|---|---|
| **Core API** | `postgres-core` |
| **API DELPI** (via Compose) | `TOTVS_DB_HOST` → mapeado para `DB_*` = SQL Server |

Sempre conferir o **serviço** antes de alterar `DB_HOST`.

---

## 5. Exemplo `.env.example` (estrutura)

```env
# Geral
PUBLIC_BASE_URL=http://localhost
TZ=America/Sao_Paulo

# Keycloak
KEYCLOAK_REALM=delpi
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=change-me
KC_HTTP_RELATIVE_PATH=/auth
KC_HOSTNAME=localhost
KC_PROXY=edge
KC_PROXY_HEADERS=xforwarded

# Postgres Core
POSTGRES_CORE_DB=delpi_core
POSTGRES_CORE_USER=delpi
POSTGRES_CORE_PASSWORD=change-me
DB_HOST=postgres-core
DB_PORT=5432
DB_NAME=delpi_core
DB_USER=delpi
DB_PASSWORD=change-me
SECRET_KEY=change-me

# JWT
KEYCLOAK_AUDIENCE=delpi-central
KEYCLOAK_ISSUER=http://localhost/auth/realms/delpi
KEYCLOAK_JWKS_URL=http://keycloak:8080/auth/realms/delpi/protocol/openid-connect/certs
JWT_ALGORITHMS=RS256

# Portal
VITE_KC_URL=http://localhost/auth
VITE_KC_REALM=delpi
VITE_KC_CLIENT_ID=delpi-central
VITE_KC_REDIRECT_URI=http://localhost/

# TOTVS + Plugins DB (preencher conforme ambiente)
TOTVS_DB_HOST=
PLUGINS_DB_HOST=postgres-plugins
PLUGINS_DB_NAME=plugins_hub
PLUGINS_DB_USER=plugins_user
PLUGINS_DB_PASSWORD=change-me
```

---

## 6. Troubleshooting por variável

| Sintoma | Verificar |
|---|---|
| Core API não conecta | `DB_HOST=postgres-core`, credenciais = `POSTGRES_CORE_*` |
| 401 após login | `KEYCLOAK_ISSUER` = `iss` do token; `KEYCLOAK_AUDIENCE` no `aud` |
| JWKS timeout | `KEYCLOAK_JWKS_URL` usa hostname `keycloak`, não `localhost` |
| Portal redirect | `VITE_KC_*` + Valid Redirect URIs no client |
| API DELPI TOTVS | VPN, `TOTVS_DB_*`, firewall 1433 |
| Chat sem LLM | `OLLAMA_BASE_URL`, modelos baixados no container |

---

## 7. Documentos relacionados

- [docker-compose.md](./docker-compose.md)
- [../03-autenticacao-autorizacao/jwt.md](../03-autenticacao-autorizacao/jwt.md)
- [../03-autenticacao-autorizacao/keycloak-sso.md](../03-autenticacao-autorizacao/keycloak-sso.md)
- [../10-guias-operacionais/configurar-keycloak.md](../10-guias-operacionais/configurar-keycloak.md)
