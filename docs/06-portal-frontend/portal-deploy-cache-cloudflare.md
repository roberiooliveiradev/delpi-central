# Portal — deploy, cache Cloudflare e tela escura no login

> **Status:** documentação oficial (jul/2026)  
> **Incidente:** após deploy do portal, `/login` exibia tela escura/preta em produção (`minhadelpi.com.br`)  
> **Commits:** `37be685d2` · `5271adf75` · `ac5814af6`

---

## 1. Sintoma

- URL: `https://minhadelpi.com.br/login` (ou com `?_recover=…` após tentativa automática de recuperação).
- Tela **preta** — CSS carrega (~45 kB), mas a UI React não monta.
- DevTools → Network → `index-*.js`:
  - Tamanho **~0,6–0,7 kB** (errado)
  - Esperado: **~1,4 MB** e `Content-Type: application/javascript`

O hash do arquivo pode estar **correto** (`index-DvFfb1Q9.js`) e mesmo assim o browser recebe conteúdo inválido.

---

## 2. Causa raiz

Cadeia que gerou o problema:

```text
1. Deploy novo do portal → Vite gera index.html com hash JS novo
2. Browser ou Cloudflare mantém index.html antigo (cache)
3. Pedido ao chunk JS antigo/inexistente
4. nginx do portal (antes do fix): try_files → fallback /index.html em /assets/*
5. Resposta HTML (~0,7 kB) com Content-Type text/html
6. Cloudflare cacheia essa URL como JS (max-age=14400, ~4 h)
7. Browser executa HTML como module script → React não sobe → tela escura
```

**Não foi bug de Module Federation nem alteração funcional do gateway de plugins** — foi **cache envenenado** na borda (Cloudflare) + **SPA fallback indevido** em `/assets/*`.

---

## 3. Correções implementadas

### 3.1 `portal/nginx.conf` (`37be685d2`, refinado em `5271adf75`)

| Regra | Comportamento |
|-------|----------------|
| `location /assets/` | `try_files $uri =404` — **nunca** devolve `index.html` para chunk ausente |
| 404 em `/assets/` | `Cache-Control: no-store` + `CDN-Cache-Control: no-store` |
| Chunks existentes | `Cache-Control: public, max-age=31536000, immutable` |
| `index.html` e rotas SPA | `no-cache` + `CDN-Cache-Control: no-store` |

### 3.2 Gateway `gateway/nginx.conf` (`5271adf75`, `ac5814af6`)

| Location | Efeito |
|----------|--------|
| `^~ /assets/` | Proxy explícito para `portal:80`; repassa `Cache-Control` / `CDN-Cache-Control` da origem |
| `/` (shell) | `CDN-Cache-Control: no-store` — HTML do portal não deve ficar stale no edge |

### 3.3 `portal/index.html` + meta tags (`5271adf75`)

- `<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">` como reforço no HTML.

### 3.4 Plugin Vite `portal/vite/cacheBustEntryPlugin.ts` (`ac5814af6`)

Substitui o `<script type="module" src="/assets/index-HASH.js">` por **import dinâmico** com query string:

```javascript
// Sem _recover na URL (deploy normal):
import("/assets/index-HASH.js?v=TIMESTAMP_BUILD")

// Com ?_recover=… (segunda tentativa após falha):
import("/assets/index-HASH.js?cb=TIMESTAMP")
```

Cada **build** gera `?v=` novo → URL distinta no Cloudflare → contorna entrada cacheada envenenada **sem depender só de purge manual**.

Recuperação automática: se o `import()` falhar, redireciona uma vez com `?_recover=` no query string da página.

Registrado em `portal/vite.config.ts`.

---

## 4. Arquivos alterados (referência)

| Arquivo | Papel |
|---------|--------|
| `portal/nginx.conf` | Política de cache e 404 em `/assets/` |
| `portal/index.html` | Template Vite (meta no-cache) |
| `portal/vite/cacheBustEntryPlugin.ts` | import() com `?v=` / `?cb=` |
| `portal/vite.config.ts` | Registra o plugin no build prod |
| `gateway/nginx.conf` | Locations `/assets/` e `CDN-Cache-Control` no shell |
| `infra/README-ambiente.md` | Checklist pós-deploy portal |
| `docs/02-infraestrutura/gateway-nginx.md` | §7 cache + §11 troubleshooting |

---

## 5. Deploy em produção

```bash
git pull
./infra/scripts/up-prod-sequential.sh --fase core --build portal gateway
```

**Recomendado após o primeiro deploy com este fix:** purge no Cloudflare para limpar entradas envenenadas já existentes.

---

## 6. Purge Cloudflare (quando necessário)

Dashboard → site `minhadelpi.com.br` → **Caching** → **Purge Everything**

Ou purge seletivo: `/login`, `/`, `/assets/*`

Depois: hard refresh (Ctrl+Shift+R) ou aba anônima.

---

## 7. Validação

### curl (substitua HASH pelo valor do HTML atual)

```bash
# HTML do login — deve referenciar import com ?v=
curl -s https://minhadelpi.com.br/login | grep -E 'import|/assets/'

# Chunk JS (sem query — origem)
curl -sI "https://minhadelpi.com.br/assets/index-HASH.js" \
  | grep -iE 'content-type|content-length'
# Esperado: application/javascript e content-length ~1428458

# Chunk inexistente — deve ser 404, não HTML
curl -sI "https://minhadelpi.com.br/assets/nao-existe.js" | grep HTTP
# Esperado: HTTP/2 404
```

### DevTools (browser)

| Recurso | OK | Problema |
|---------|-----|----------|
| `index-*.js` | ~1 MB+, type `script` / `javascript` | ~0,7 kB |
| URL do JS | contém `?v=` ou `?cb=` (após fix `ac5814af6`) | só `/assets/index-….js` sem query |
| Console | sem erro de parse no module | `Unexpected token '<'` (HTML no JS) |

---

## 8. O que NÃO fazer

- Redeploy **só** do gateway esperando corrigir bundle do portal.
- Assumir que hard refresh basta se o Cloudflare ainda serve HTML na URL do chunk (purge ou aguardar TTL ~4 h **antes** do fix `?v=`).
- Reintroduzir `try_files … /index.html` dentro de `location /assets/` no portal.

---

## 9. Documentos relacionados

- [gateway-nginx.md](../02-infraestrutura/gateway-nginx.md) — roteamento e cache MFE
- [infra/README-ambiente.md](../../infra/README-ambiente.md) — checklist deploy produção
- [autenticacao-frontend.md](./autenticacao-frontend.md) — fluxo Keycloak / login
