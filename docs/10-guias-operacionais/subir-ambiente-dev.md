# Guia: subir ambiente de desenvolvimento

> **Arquivo:** `docs/10-guias-operacionais/subir-ambiente-dev.md`  
> **Status:** documentação oficial  
> **Compose:** `infra/docker-compose.dev.yml`

---

## 1. Pré-requisitos

- Docker e Docker Compose v2
- Repositório clonado (`delpi-central`)
- Arquivo `infra/.env` configurado (copiar de exemplo interno ou `.env.prod` como referência de chaves)
- Portas livres: **80**, **5432**, **5433** (e **11434** se usar Ollama direto do host)
- Acesso de rede ao **SQL Server TOTVS** e demais DBs externos configurados em `.env` (API DELPI falha sem TOTVS se rotas Protheus forem usadas)

---

## 2. Estrutura mínima do monorepo

```text
delpi-central/
  api-delpi/
  core-api/
  minha-delpi-ai-api/
  portal/
  gateway/
  plugins/
  infra/
    .env
    docker-compose.dev.yml
```

---

## 3. Subir a stack

```bash
cd infra
docker compose -f docker-compose.dev.yml up --build -d
```

Primeira subida pode levar vários minutos (build de plugins + portal).

Acompanhar logs:

```bash
docker compose -f docker-compose.dev.yml logs -f
```

---

## 4. Containers esperados

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

Lista típica:

```text
delpi-gateway
delpi-portal
delpi-core-api
delpi-keycloak
delpi-keycloak-db
delpi-postgres-core
delpi-postgres-plugins
delpi-api-delpi
delpi-minha-delpi-ai-api
delpi-ollama
delpi-strategic-indicators
delpi-minha-delpi-chat
delpi-dashboard-lmps
delpi-dashboard-delpi
delpi-auditoria-5s
delpi-central-agendamento
```

---

## 5. Ollama (chat / IA)

O serviço `minha-delpi-ai-api` depende do **Ollama** em dev. Após os containers estarem up:

```bash
docker exec -it delpi-ollama ollama pull qwen2.5:1.5b
docker exec -it delpi-ollama ollama pull bge-m3
```

Verificar:

```bash
curl http://localhost:11434/api/tags
```

Sem modelos, o chat retorna erro de LLM indisponível.

---

## 6. Migrations da Core API

Com banco core vazio ou após `down -v`:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db upgrade
```

Estado atual:

```bash
docker compose -f docker-compose.dev.yml exec core-api flask db current
```

---

## 7. Validar endpoints

### Gateway e Portal

```text
http://localhost/
```

### Core API

```bash
curl -s http://localhost/core-api/health
```

Resposta:

```json
{"status": "Api rodando!"}
```

### Keycloak

```text
http://localhost/auth
```

### API DELPI

```bash
curl -s http://localhost/apps/api-delpi/health
```

### Minha DELPI AI API

```bash
curl -s http://localhost/apps/minha-delpi-ai/api/health
```

(Paths exatos podem variar — conferir `minha-delpi-ai-api/docs/api/01-health-status-capabilities.md`.)

### Login no Portal

1. Abrir `http://localhost`
2. Login Keycloak
3. DevTools → Network: `GET /core-api/me` e `/core-api/me/apps` com **200**

---

## 8. Registrar plugins (primeira vez)

Se o menu não mostrar apps, registrar manifestos na Core API (usuário com `apps.manage`):

```http
POST http://localhost/core-api/admin/apps/register
Authorization: Bearer <token>
Content-Type: application/json

{ ... conteúdo do delpi.manifest.json ... }
```

Ou usar a aba **Apps** em `http://localhost/admin`.

Guia: [registrar-plugin.md](./registrar-plugin.md).

---

## 9. Portas locais

| Porta | Uso |
|---:|---|
| 80 | Toda a plataforma via gateway |
| 5432 | `psql` no Postgres Core |
| 5433 | `psql` no Postgres Plugins (pgvector) |
| 11434 | API Ollama (debug) |

Exemplo:

```bash
psql -h localhost -p 5432 -U <POSTGRES_CORE_USER> -d <POSTGRES_CORE_DB>
```

---

## 10. Rebuild seletivo

```bash
# Só Portal
docker compose -f docker-compose.dev.yml up --build -d portal

# Só Core API
docker compose -f docker-compose.dev.yml up --build -d core-api

# Só plugin chat (obrigatório após mudanças no admin/MFE — nginx serve dist da imagem)
docker compose -f docker-compose.dev.yml up --build -d minha-delpi-chat
```

O serviço `minha-delpi-chat` publica `remoteEntry.js` estático; alterar só o código no host **não** atualiza a UI até rebuild. Admin novo: 6 seções no topo + rótulo `admin-v2-6secoes`.

---

## 11. Parar e resetar

```bash
# Parar, manter volumes
docker compose -f docker-compose.dev.yml down

# Apagar bancos e ollama (CUIDADO)
docker compose -f docker-compose.dev.yml down -v
```

Após `down -v`: rodar migrations, reconfigurar Keycloak (realm/clients) e registrar plugins novamente.

Detalhes: [reset-banco-dev.md](./reset-banco-dev.md).

---

## 12. Problemas comuns

| Problema | Ação |
|---|---|
| Porta 80 ocupada | `sudo lsof -i :80` ou alterar mapeamento no Compose |
| Core API crash loop | Ver logs; conferir `DB_HOST=postgres-core` no `.env` |
| Keycloak lento no 1º boot | Aguardar 1–2 min; ver `docker logs delpi-keycloak` |
| 502 no gateway | Container alvo down — `docker compose ps` |
| 502 em `/auth/.../token` (login/smokes) | Keycloak parado — `docker compose -f docker-compose.dev.yml up -d keycloak keycloak-db` e aguardar realm responder 200 |
| Atalhos do chat enviam código fixo | Rebuild `minha-delpi-chat`; atalhos operacionais usam `{{productCode}}` / `{{searchQuery}}` e abrem diálogo de preenchimento no MFE |
| Modal «Pesquisa na web» ainda mostra WEG/CFW500 | Rebuild `minha-delpi-chat` — placeholder do campo é **DELPI Conexões Elétricas** (`SEARCH_QUERY_PLACEHOLDER`); hard refresh no navegador |
| Console: `WebSocket … socket.io` / `NS_ERROR_WEBSOCKET_CONNECTION_REFUSED` | Gateway dev: `proxy_pass` do `/socket.io` deve ser **estático** (`http://core-api:8000`), não com variável `$upstream` — ver `gateway/nginx.dev.conf`. Depois: `docker compose -f docker-compose.dev.yml restart gateway` |
| Plugin 404 em assets | Container `delpi-<id>` rodando? Id na URL = id do manifesto |
| Chat sem resposta | Modelos Ollama não baixados (passo 5) |
| Portal login loop | Conferir `VITE_KC_*` e redirect URI no client Keycloak |
| TOTVS timeout | VPN/rede; variáveis `TOTVS_DB_*` no `.env` |

Mais cenários: [troubleshooting.md](./troubleshooting.md).

---

## 13. Checklist

- [ ] `infra/.env` preenchido
- [ ] `docker compose ... up -d` sem erro fatal
- [ ] `/core-api/health` OK
- [ ] `/auth` abre Keycloak
- [ ] `flask db upgrade` aplicado
- [ ] Modelos Ollama baixados (se usar chat)
- [ ] Login Portal OK
- [ ] `/core-api/me/apps` retorna plugins
- [ ] Pelo menos um `remoteEntry.js` acessível (ex. strategic-indicators)

---

## 14. Documentos relacionados

- [../02-infraestrutura/docker-compose.md](../02-infraestrutura/docker-compose.md)
- [../02-infraestrutura/gateway-nginx.md](../02-infraestrutura/gateway-nginx.md)
- [configurar-keycloak.md](./configurar-keycloak.md)
- [../08-plugins/README.md](../08-plugins/README.md)
