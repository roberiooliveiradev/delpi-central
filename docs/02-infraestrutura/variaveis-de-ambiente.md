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
| `CORE_API_BASE_URL` | URL interna da Core API (ex.: `http://core-api:8000`) |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | Token para POST `/integrations/app-usage/record` |
| `API_DELPI_INTERNAL_SERVICE_TOKEN` | Token de serviço interno (bypass auth em rotas protegidas) |
| `APP_USAGE_TRACKING_ENABLED` | `true` — middleware registra uso na Core API |
| `APP_USAGE_APP_ID` | Id do app na Core API (default `api-delpi`) |

Homologação **sem TOTVS**: [12-testes-sem-totvs-google-sheets.md](../../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md).

### Core API — presença e uso de apps

| Variável | Default | Descrição |
|----------|---------|-----------|
| `APP_USAGE_ENABLED` | `true` | Rastreamento de apps |
| `APP_USAGE_TTL_SECONDS` | `90` | TTL store ao vivo |
| `APP_USAGE_HISTORY_DAYS` | `30` | Janela ranking / fantasmas |
| `APP_USAGE_STORE` | `memory` | `memory` ou `redis` (futuro) |
| `USER_PRESENCE_ENABLED` | `true` | Presença online |
| `USER_PRESENCE_TTL_SECONDS` | `90` | TTL presença |
| `USER_PRESENCE_STORE` | `memory` | `memory` ou `redis` |
| `CORE_API_INTEGRATIONS_SERVICE_TOKEN` | — | Token integrações (api-delpi, jobs) |

Ver [rastreamento-uso-apps.md](../04-core-api/rastreamento-uso-apps.md).

### Minha DELPI AI API

Definidas no Compose (dev) — ver também `minha-delpi-ai-api` settings:

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | Montada no Compose → `postgres-plugins` |
| `CORE_API_BASE_URL` | `http://core-api:8000` |
| `LLM_PROVIDER` | `ollama` ou `vllm` |
| `OLLAMA_BASE_URL` | `http://ollama:11434` |
| `OLLAMA_MODEL` | Default **`qwen2.5:3b`** (CPU, bom equilíbrio qualidade/velocidade). Alternativas: `qwen2.5:7b` (GPU/16GB RAM), `qwen2.5:1.5b` (mínimo) |
| `OLLAMA_NUM_CTX` | Janela de contexto. **Recomendado:** `2048` (permite coexistência 3b + bge-m3 em 8GB); com 16GB+: `4096`. Perfil `operational_cpu`: `1536` |
| `OLLAMA_NUM_THREAD` | Threads CPU. Usar = nº de cores reais. **Prod 4 vCPU:** `4` |
| `OLLAMA_MAX_LOADED_MODELS` | Modelos simultâneos em RAM. **Prod 8 GB:** `2` (chat + embeddings coexistem com ctx=2048) |
| `OLLAMA_NUM_PARALLEL` / `OLLAMA_KEEP_ALIVE` | Serviço `ollama` no Compose |
| `LLM_MAX_TOKENS` | `num_predict` Ollama. **Recomendado:** `1536`; mínimo: `384`. Ou use `CHAT_LLM_LATENCY_PROFILE=operational_cpu` (384) |
| `CHAT_LLM_LATENCY_PROFILE` | Preset de latência quando `LLM_MAX_TOKENS`/`OLLAMA_NUM_CTX` não estão explícitos: `operational_cpu` (384/1536), `balanced` (1536/2048), `documental` (768/4096). **Homolog CPU:** `operational_cpu` |
| `CHAT_RESPONSE_MODES_ENABLED` | `true` — modos **Rápida / Normal / Pensador** no composer (`responseMode` no POST stream/send). Ver `GET /chat/response-modes` |
| `CHAT_RESPONSE_MODE_FAST_MODEL` | Modelo Ollama/vLLM do modo rápida (ex.: `qwen2.5:1.5b`). Requer `ollama pull` |
| `CHAT_RESPONSE_MODE_FAST_MAX_TOKENS` / `FAST_NUM_CTX` | Limites do modo rápida (default 384 / 1536) |
| `CHAT_RESPONSE_MODE_THINKER_MODEL` | Opcional — modelo maior; vazio = mesmo `OLLAMA_MODEL` com mais contexto |
| `CHAT_RESPONSE_MODE_THINKER_MAX_TOKENS` / `THINKER_NUM_CTX` | Modo pensador (default 1536 / 4096) |
| `LLM_TEMPERATURE` | Criatividade das respostas. **Recomendado:** `0.4` (natural); `0.2` (mais determinístico) |
| `CHAT_SESSION_TITLE_LLM_ENABLED` | `true` recomendado — títulos automáticos melhoram UX |
| `CHAT_FAST_PATH_ENABLED` | `true` — pula RAG/tools em cumprimentos curtos (`olá`, `oi`). Max chars: `30` |
| `CHAT_TOOL_ROUTER_ENABLED` | `true` (default) — LLM sugere ferramentas (melhora assertividade) |
| `CHAT_AGENTIC_LOOP_ENABLED` | `true` (default) — loop agentic com catálogo de actions |
| `CHAT_AGENTIC_CATALOG_MAX_ACTIONS` | `12` (default) — teto de actions no planner agentic |
| `CHAT_MULTI_ACTION_ENABLED` | `true` (default) — múltiplas external actions por turno |
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` (default) — consolida páginas quando o usuário pede total/completo |
| `CHAT_DEFAULT_SQL_AUTHORING_SKILL` | `true` (default) — skill `sql` herdada no chat sem agente |
| `CHAT_DEFAULT_COMPANY_KNOWLEDGE_SKILL` | `true` (default) — skill `company-knowledge` (RAG documental global) |
| `CHAT_WEB_SEARCH_ENABLED` | `true` (default no Docker) — pesquisa web; requer SearXNG ou API key |
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
| `CHAT_ASSISTANT_IDENTITY_DIRECT_ENABLED` | `true` (default) — «quem te criou» etc. usam `identity.json` sem RAG/LLM; `false` para homologar RAG+LLM |
| `CHAT_UTILITY_DIRECT_ENABLED` | `true` (default) — «que horas são?», «que dia é hoje?» etc. usam `utility_answers.json` com hora real, sem LLM. Typos (`que hors são?`, `q horas`) são corrigidos por `ChatMessageNormalizationService` antes do match |
| `CHAT_UTILITY_TIMEZONE` | Herda `TZ` (ex.: `America/Sao_Paulo`) — fuso para respostas de hora/data |
| `CHAT_PERSIST_BEFORE_PLAYBACK` | `true` (default) — stream grava **pergunta cedo** (`user_persisted`), placeholder assistant (`assistant_pending`) e resposta final antes do SSE `playback`; commits incrementais em checkpoints. O plugin anima com escrita natural (`naturalTextReveal`). Reload mid-stream mantém a pergunta no histórico. Use `false` só se priorizar primeiro `token` SSE em CPU muito lenta (modo legado, sem `user_persisted`) |
| `CHAT_PAGINATION_AUTO_FETCH_ENABLED` | `true` (default) — quando o usuário pede total/completo ou confirma continuação, o chat busca várias páginas da API e consolida (tabela, árvore, listagem) |
| `CHAT_PAGINATION_MAX_PAGES_PER_TURN` | `5` (default, máx. 8) — páginas buscadas por turno antes de perguntar «deseja continuar?» |
| `CHAT_DIRECT_RESPONSE_STREAM_CHUNK_CHARS` | Só quando `CHAT_PERSIST_BEFORE_PLAYBACK=false`: chars por chunk no streaming SSE legado. **Recomendado:** `4` |
| `CHAT_DIRECT_RESPONSE_STREAM_DELAY_MS` | Só quando `CHAT_PERSIST_BEFORE_PLAYBACK=false`: delay entre chunks SSE. **Recomendado:** `0`–`45` |
| `RAG_ASSERTIVENESS_MIN_SCORE` | Score mínimo em fluxos de assertividade (default `0.35`) |
| `EMBEDDING_PROVIDER` / `EMBEDDING_MODEL` | Ex.: `bge-m3` |
| `RATE_LIMIT_*` | Limites por janela |
| `KNOWLEDGE_*` | Limites de ingestão RAG |
| `LGPD_REQUIRE_AI_CONSENT` | `true` (default maio/2026) — exige consentimento `ai_context` antes de injetar PII no LLM |

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
| API DELPI online, rotas 500 | TOTVS fora — testar rotas Google Sheets; ver [12-testes-sem-totvs-google-sheets.md](../../api-delpi/docs/api/12-testes-sem-totvs-google-sheets.md) |
| Chat sem LLM | `OLLAMA_BASE_URL`, modelos baixados no container |

---

## 7. Documentos relacionados

- [docker-compose.md](./docker-compose.md)
- [../03-autenticacao-autorizacao/jwt.md](../03-autenticacao-autorizacao/jwt.md)
- [../03-autenticacao-autorizacao/keycloak-sso.md](../03-autenticacao-autorizacao/keycloak-sso.md)
- [../10-guias-operacionais/configurar-keycloak.md](../10-guias-operacionais/configurar-keycloak.md)
