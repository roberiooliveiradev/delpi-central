# Minha DELPI — Gateway Nginx

> **Arquivo:** `docs/02-infraestrutura/gateway-nginx.md`  
> **Status:** documentação oficial (alinhada a `gateway/nginx.conf` e `gateway/nginx.dev.conf`)  
> **Código:** `gateway/`

---

## 1. Papel

O **Gateway** (`delpi-gateway`) é a única entrada HTTP pública (porta **80**). Ele:

- encaminha tráfego para Portal, Core API, Keycloak, API DELPI, AI API e assets de plugins;
- preserva `Authorization` e headers de proxy (`X-Forwarded-*`);
- suporta **WebSocket** (Socket.IO da Core API e da API DELPI);
- aplica política de cache diferenciada para `remoteEntry.js` vs demais assets.

O navegador **não** acessa portas internas dos containers diretamente.

---

## 2. Arquivos de configuração

| Ambiente | Arquivo | Observação |
|---|---|---|
| Produção | `gateway/nginx.conf` | Embutido em `Dockerfile.prod` |
| Desenvolvimento | `gateway/nginx.dev.conf` | Montado via volume no Compose |

Compose dev (`infra/docker-compose.dev.yml`):

```yaml
gateway:
  volumes:
    - ../gateway/nginx.dev.conf:/etc/nginx/nginx.conf
```

---

## 3. Mapa de rotas (server `minhadelpi.com.br`)

Ordem de precedência no Nginx: locations mais específicas antes do fallback `/`.

| Location | Upstream | Strip / rewrite |
|---|---|---|
| `^~ /socket.io/` | `core-api:8000/socket.io/` | Prefixo mantido no upstream |
| `^~ /core-api/` | `core-api:8000/` | `/core-api/foo` → `/foo` |
| `/auth/` | `keycloak:8080` | Keycloak com path `/auth` |
| `^~ /apps/api-delpi/socket.io/` | `api-delpi:8000/socket.io/` (via `$upstream_api_delpi`) | Socket API DELPI |
| `^~ /apps/minha-delpi-ai/api/` | `delpi-minha-delpi-ai-api:8000/` | AI API |
| `^~ /apps/api-delpi/` | `api-delpi:8000/` (via `$upstream_api_delpi`) | API operacional |
| `~ ^/apps/([^/]+)/assets/remoteEntry\.js$` | `delpi-$1` → `/assets/remoteEntry.js` | **Sem cache** |
| `~ ^/apps/([^/]+)/assets/(.*)$` | `delpi-$1` → `/assets/$2` | Cache 1 ano |
| `/` | `portal:80` | Shell React (SPA) |

### Convenção de nome do container de plugin

Regex captura `plugin-id` da URL:

```text
/apps/strategic-indicators/assets/...  →  http://delpi-strategic-indicators/assets/...
```

O serviço Docker deve se chamar `delpi-<id>` (ex.: `delpi-strategic-indicators` no Compose).

---

## 4. Diagrama de fluxo

```text
Browser
   │
   ├─ /                          → portal:80
   ├─ /core-api/*                → core-api:8000
   ├─ /socket.io/*               → core-api:8000
   ├─ /auth/*                    → keycloak:8080
   ├─ /apps/api-delpi/*          → api-delpi:8000
   ├─ /apps/minha-delpi-ai/api/* → minha-delpi-ai-api:8000
   └─ /apps/{plugin}/assets/*    → delpi-{plugin}:assets
```

---

## 5. Headers e limites

Configuração global relevante:

| Diretiva | Valor | Efeito |
|---|---|---|
| `client_max_body_size` | `20m` | Uploads / manifestos grandes |
| `proxy_buffer_size` | `256k` | JWT e cookies grandes |
| `large_client_header_buffers` | `8 256k` | Evita 494 em headers extensos |
| `proxy_read_timeout` | `86400` em sockets/long poll | SSE/chat |

Headers repassados aos backends:

```text
Host, X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
Authorization (implícito do cliente)
```

Keycloak recebe ainda: `X-Forwarded-Host`, `X-Forwarded-Port`, `Forwarded`.

---

## 6. WebSocket / Socket.IO

### Core API

```nginx
location /socket.io/ {
  proxy_pass http://core-api:8000/socket.io/;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection $connection_upgrade;
}
```

Portal conecta em `io("/", { path: "/socket.io" })` — mesma origem do gateway.

**Dev (`nginx.dev.conf`):** use `location ^~ /socket.io` com `proxy_pass http://core-api:8000;` **sem** variável dinâmica (`set $upstream …`). Com variável, o Engine.IO responde 400 (*unsupported version*) ou o WS cai no Portal (Vite) → `CONNECTION_REFUSED` no Firefox.

### API DELPI

Path dedicado: `/apps/api-delpi/socket.io/` → `api-delpi:8000/socket.io/`.

HTTP e Socket usam `set $upstream_api_delpi` + `proxy_pass http://$upstream_api_delpi` para o `resolver 127.0.0.11` re-resolver o container após `docker compose up --force-recreate api-delpi`. Com hostname fixo em `proxy_pass`, o Nginx guarda o IP na subida do gateway e devolve **502** até reiniciar `delpi-gateway`.

---

## 7. Cache de microfrontends

| Arquivo | Política |
|---|---|
| `remoteEntry.js` | `Cache-Control: no-store` — força reload após deploy de plugin |
| Demais `/assets/*` | `max-age=31536000, immutable` — chunks com hash no build |

---

## 8. Segurança no edge

Bloqueio de dotfiles sensíveis:

```nginx
location ~ /\.(env|git|htaccess|htpasswd|docker|npmrc) {
  deny all;
  return 404;
}
```

Em produção, HTTPS e HSTS ficam tipicamente na camada anterior (load balancer) ou em extensão futura deste `nginx.conf`.

---

## 9. Server block adicional (helpdesk)

`server_name helpdesk.centraldelpi.com.br` → proxy para `inventario-ti-glpi-1:80` (GLPI). Independente da stack Minha DELPI.

---

## 10. Serviços Docker relacionados (dev)

Containers que o gateway espera na rede `delpi-network`:

```text
portal, core-api, keycloak, api-delpi
delpi-minha-delpi-ai-api
delpi-strategic-indicators, delpi-dashboard-lmps, delpi-minha-delpi-chat
delpi-dashboard-delpi (se assets servidos por /apps/dashboard-delpi)
```

`depends_on` do gateway no Compose lista os principais; plugins adicionais precisam existir na rede com nome `delpi-<manifest-id>`.

---

## 11. Troubleshooting rápido

| Sintoma | Causa provável |
|---|---|
| 502 em `/apps/api-delpi/*` após recreate da API | Gateway com IP antigo do container; rebuild/restart do `delpi-gateway` ou confirme upstream dinâmico (`$upstream_api_delpi`) |
| 502 em `/core-api` | `core-api` down ou fora da rede |
| 404 em `/apps/X/assets/remoteEntry.js` | Container `delpi-X` inexistente ou id do manifesto ≠ segmento URL |
| Login Keycloak errado | `KC_HOSTNAME` / `VITE_KC_URL` divergentes da URL pública |
| Socket não conecta | Falta token em `socket.auth`; path errado |
| Plugin antigo em cache | Só `remoteEntry` é no-store; hard refresh ou versão no build |

---

## 12. Checklist

- [ ] `GET /core-api/health` responde via gateway
- [ ] Portal carrega em `/`
- [ ] `/auth/` abre Keycloak
- [ ] `remoteEntry.js` do plugin retorna 200
- [ ] Socket.IO conecta após login
- [ ] `Authorization` chega na Core API (testar `/me`)

---

## 13. Documentos relacionados

- [docker-compose.md](./docker-compose.md)
- [ambientes-dev-prod.md](./ambientes-dev-prod.md)
- [../06-portal-frontend/consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md)
- [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md)
