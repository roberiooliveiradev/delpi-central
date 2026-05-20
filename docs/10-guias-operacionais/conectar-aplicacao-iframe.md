# Tutorial — Conectar uma aplicação iframe na Minha DELPI

> **Público:** times que integram sistemas web existentes ao portal  
> **Referência em produção:** Controle MP (`controle-mp`)  
> **Última revisão:** maio/2026

Este guia cobre o fluxo completo: manifesto no portal, SSO, notificações com deep link e checklist de deploy.

---

## 1. Visão geral

```text
┌─────────────────────────────────────────────────────────────┐
│  Portal (minhadelpi.com.br)                                  │
│  /controle-mp  ──iframe──►  https://controle-mp.../         │
│       │                              ▲                       │
│       │ postMessage                  │ DELPI_AUTH_READY      │
│       ├─ DELPI_AUTH (token Keycloak) │ DELPI_NAVIGATE (path) │
│       └─ DELPI_LOGOUT                │                       │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│  Core API — POST /integrations/notifications                 │
│  (apps externos enviam alertas para o sino)                  │
└─────────────────────────────────────────────────────────────┘
```

| Peça | Responsável |
|------|-------------|
| Manifesto + rotas + permissões | Admin Minha DELPI (Core API) |
| App hospedada em HTTPS | Time do produto (ex.: Controle MP) |
| Bridges SSO + navegação no filho | Front do app iframe |
| Envio de notificações | Backend do app → Core API |

---

## 2. Pré-requisitos

- [ ] Aplicação web em **HTTPS** (ex.: `https://meu-app.minhadelpi.com.br`)
- [ ] Headers que **permitem iframe** (`X-Frame-Options` / CSP `frame-ancestors` incluindo o domínio do portal)
- [ ] Usuários cadastrados na Minha DELPI (Keycloak) com **e-mail igual** ao do app filho, se houver notificações por e-mail
- [ ] Permissão `apps.manage` para registrar o plugin (superadmin)
- [ ] Token `CORE_API_INTEGRATIONS_SERVICE_TOKEN` na Core API e no backend que envia notificações

---

## 3. Passo 1 — Manifesto do plugin

Registre via Admin → Apps ou `POST /admin/apps/register`.

### Exemplo real (Controle MP)

```json
{
  "schemaVersion": "1.0.0",
  "id": "controle-mp",
  "name": "Controle MP",
  "description": "Cadastro e fluxo de matérias-primas",
  "icon": "messages-square",
  "version": "1.0.0",
  "type": "iframe",
  "basePath": "/controle-mp",
  "entry": "https://controle-mp.minhadelpi.com.br",
  "permissions": [
    {
      "code": "controle-mp.access",
      "name": "Acesso ao Controle MP",
      "description": "Abrir o módulo",
      "module": "controle-mp"
    }
  ],
  "routes": [
    {
      "path": "/controle-mp",
      "label": "Abrir",
      "permission": "controle-mp.access",
      "icon": "external-link",
      "entry": null,
      "order": 1,
      "showInMenu": true
    }
  ],
  "ui": {
    "renderMode": "embedded"
  }
}
```

### Regras importantes

| Campo | Regra |
|-------|--------|
| `type` | `iframe` |
| `basePath` | Rota no portal (ex.: `/controle-mp`). **Use o mesmo valor** em notificações (`action.target`) |
| `entry` | URL **absoluta** HTTPS da aplicação filha |
| `ui.renderMode` | `embedded` (iframe no portal) ou `external` (nova aba) |
| `routes[].path` | Deve começar com `basePath` |

Detalhes do contrato: [manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md), [iframe.md](../05-plugin-system/iframe.md).

Runbook de registro: [registrar-plugin.md](./registrar-plugin.md).

---

## 4. Passo 2 — SSO no iframe (recomendado)

O portal repassa o **access token Keycloak** ao filho. O app troca por sessão local (JWT próprio).

### 4.1 No portal (já implementado)

`AppHost.tsx` escuta `DELPI_AUTH_READY`, envia `DELPI_AUTH` com token, e `DELPI_LOGOUT` no logout global.

### 4.2 No front do app filho

Implemente três bridges (padrão Controle MP):

| Arquivo (referência) | Função |
|----------------------|--------|
| `DelpiSsoBridge.jsx` | Pede token (`DELPI_AUTH_READY`), chama API `sso-login`; no iframe **não** redireciona para home após SSO |
| `DelpiNavigateBridge.jsx` | Escuta `DELPI_NAVIGATE` e navega no React Router |
| `DelpiRouteSyncBridge.jsx` | Envia `DELPI_EMBEDDED_ROUTE` ao pai quando a rota interna muda |

**Origens permitidas** no filho (validar `event.origin`):

```text
https://minhadelpi.com.br
https://www.minhadelpi.com.br
```

Variável de build: `VITE_DELPI_PARENT_ORIGIN=https://minhadelpi.com.br`

### 4.3 Na API do app filho (ex.: Controle MP)

Validar token Keycloak via JWKS:

```env
CENTRAL_JWKS_URL=http://host.docker.internal/auth/realms/delpi/protocol/openid-connect/certs
CENTRAL_JWT_ISSUER=https://minhadelpi.com.br/auth/realms/delpi
CENTRAL_JWT_AUDIENCE=delpi-central
```

No Docker de produção no mesmo host do portal, `host.docker.internal` costuma ser mais estável que URL pública para JWKS (ver [keycloak-sso.md](../03-autenticacao-autorizacao/keycloak-sso.md)).

Mais contexto SSO iframe: [keycloak-sso.md §22](../03-autenticacao-autorizacao/keycloak-sso.md).

---

## 5. Passo 3 — Notificações no sino (opcional)

Apps externos enviam alertas para a Core API; o portal exibe no sino e, ao clicar, pode abrir uma **rota interna** do iframe.

### 5.1 Enviar notificação (backend do app)

```http
POST https://minhadelpi.com.br/core-api/integrations/notifications
X-Delpi-Service-Token: <CORE_API_INTEGRATIONS_SERVICE_TOKEN>
Content-Type: application/json
```

```json
{
  "title": "Meu App — Nova atividade",
  "message": "Fulano enviou uma mensagem.",
  "type": "info",
  "category": "controle_mp",
  "emails": ["usuario@delpi.com.br"],
  "sourceApp": "controle_mp",
  "action": {
    "type": "portal_route",
    "label": "Abrir",
    "target": "/controle-mp"
  },
  "metadata": {
    "source": "controle_mp",
    "event": "message:new",
    "deepPath": "/conversations/109",
    "dedupeKey": "meu-app:msg:109"
  }
}
```

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `action.target` | Sim | **Igual** ao `basePath` do manifesto |
| `metadata.deepPath` | Para deep link | Rota interna do app (ex.: `/conversations/109`) |
| `metadata.source` | Recomendado | Id lógico (`controle_mp`, `meu_app`) |
| `category` | Sim | Deve existir em `notification_constants` da Core API |

A Core API só entrega a notificação a usuários que **tenham permissão para abrir o app** no portal (ex.: `controle-mp.access` no RBAC). Quem não tem acesso ao módulo não recebe alerta no sino.

API completa: [notificacoes.md](../04-core-api/notificacoes.md).

### 5.2 Variáveis no backend (ex.: Controle MP)

```env
DELPI_NOTIFICATIONS_ENABLED=true
DELPI_CORE_API_INTERNAL_URL=http://host.docker.internal/core-api
DELPI_CORE_API_URL=https://minhadelpi.com.br/core-api
CORE_API_INTEGRATIONS_SERVICE_TOKEN=<mesmo valor do infra/.env da Core API>
DELPI_PORTAL_CONTROLE_MP_ROUTE=/controle-mp
```

O token de integração deve ser **idêntico** em `delpi-central/infra/.env` e no app emissor.

### 5.3 Deep link no clique (portal + filho)

1. Usuário clica em **Abrir** no card da notificação.
2. Portal navega para `/controle-mp/conversations/109` (rota wildcard `basePath/*`).
3. Portal envia `DELPI_NAVIGATE` com `path: metadata.deepPath`.
4. Filho navega para a tela (ex.: conversa 109).
5. Ao mudar de tela no filho, `DELPI_EMBEDDED_ROUTE` mantém a URL do portal sincronizada.

**Rota pendente após SSO:** `sessionStorage` (`delpi.child.pending_navigate`); no iframe o SSO **não** deve sobrescrever com a home.

Detalhe técnico: [embedded-app-deep-links.md](../05-portal/embedded-app-deep-links.md).

### 5.4 Nova categoria de notificação

Se o app usar categoria nova (ex.: `meu_app`):

1. Adicionar em `core-api/app/domain/notifications/notification_constants.py`
2. Adicionar label/ícone no portal (`NotificationCard`, preferências, Admin)
3. Rebuild Core API + Portal

---

## 6. Passo 4 — Variáveis de ambiente (resumo)

### Minha DELPI (`infra/.env`)

```env
CORE_API_INTEGRATIONS_SERVICE_TOKEN=<segredo compartilhado>
PUBLIC_BASE_URL=https://minhadelpi.com.br
VITE_FRONT_CHANNEL_LOGOUT_URLS=...,https://meu-app.minhadelpi.com.br/sso/logout-from-parent
```

### App filho (produção Docker no mesmo servidor)

```env
# SSO
CENTRAL_JWKS_URL=http://host.docker.internal/auth/realms/delpi/protocol/openid-connect/certs
CENTRAL_JWT_ISSUER=https://minhadelpi.com.br/auth/realms/delpi

# Notificações (se aplicável)
DELPI_CORE_API_INTERNAL_URL=http://host.docker.internal/core-api
CORE_API_INTEGRATIONS_SERVICE_TOKEN=<igual ao infra>
DELPI_PORTAL_*_ROUTE=/controle-mp   # mesmo basePath do manifesto
```

Lista completa: [variaveis-de-ambiente.md](../02-infraestrutura/variaveis-de-ambiente.md).

---

## 7. Passo 5 — Deploy e testes

### Checklist de deploy

- [ ] Manifesto registrado com `basePath` definitivo
- [ ] Permissões atribuídas aos usuários/grupos
- [ ] App filho em HTTPS com CORS/iframe ok
- [ ] Bridges SSO + `DELPI_NAVIGATE` no front
- [ ] Token de integração alinhado (se notificações)
- [ ] Rebuild portal + app filho

### Testes manuais

| # | Teste | Resultado esperado |
|---|--------|-------------------|
| 1 | Menu → abrir app | Iframe carrega, usuário logado via SSO |
| 2 | Logout no portal | Sessão do iframe encerra |
| 3 | Enviar notificação de teste | Card no sino |
| 4 | Clicar **Abrir** na notificação | URL `/controle-mp/conversations/{id}` e chat correto |
| 5 | Chat aberto: outro usuário envia | Mensagem aparece **sem** precisar enviar outra |
| 6 | E-mail destinatário = Keycloak | `createdCount >= 1` nos logs |

### URL na barra do navegador

No modo embedded (maio/2026), a URL do portal inclui a rota interna, como no chat IA:

| Portal | Iframe (domínio do app) |
|--------|-------------------------|
| `/controle-mp/conversations/110` | `/conversations/110` |

---

## 8. Implementação mínima no front (novo app)

Copie e adapte do Controle MP:

```text
src/app/sso/
  DelpiSsoBridge.jsx           # DELPI_AUTH / DELPI_LOGOUT
  DelpiNavigateBridge.jsx      # DELPI_NAVIGATE
  DelpiRouteSyncBridge.jsx     # DELPI_EMBEDDED_ROUTE → URL do portal
  delpiEmbeddedNavigation.js   # sessionStorage rota pendente
```

Monte os bridges no router raiz (como em `AppRouter.jsx`).

Snippet `DelpiNavigateBridge` (essência):

```javascript
window.addEventListener("message", (event) => {
  if (!ALLOWED_ORIGINS.includes(event.origin)) return;
  if (event.data?.type !== "DELPI_NAVIGATE") return;
  const path = event.data.path;
  sessionStorage.setItem("delpi.child.pending_navigate", path);
  navigate(path, { replace: true });
});
```

Após SSO, consuma `delpi.child.pending_navigate` antes de redirecionar para a home.

---

## 9. Troubleshooting

| Sintoma | Causa comum | Ação |
|---------|-------------|------|
| App não aparece no menu | Sem permissão / manifesto | Conferir RBAC e registro |
| Iframe em branco | CSP / X-Frame-Options | Liberar frame do portal |
| SSO 500 | JWKS inacessível do container | `CENTRAL_JWKS_URL` via `host.docker.internal` |
| Sino vazio | Token ou e-mail errado | Logs `grep DELPI`; igualar e-mails |
| Abre app mas não a conversa | SSO sobrescreve rota / portal sem wildcard | Rebuild portal + 3 bridges no filho |
| Mensagem só aparece ao enviar outra | Socket antes do `commit` no DB | Rebuild API + front Controle MP |
| `createdCount=0` | E-mail não existe na Core API | Cadastrar usuário Keycloak |
| `action.target` com `_` vs `-` | Legado `/controle_mp` | Usar `/controle-mp` igual ao manifesto |

Mais diagnósticos: [troubleshooting.md](./troubleshooting.md).

---

## 10. Documentos relacionados

| Documento | Conteúdo |
|-----------|----------|
| [embedded-app-deep-links.md](../05-portal/embedded-app-deep-links.md) | Contrato `deepPath` + postMessage |
| [iframe.md](../05-plugin-system/iframe.md) | Regras de plugins iframe |
| [consumo-de-plugins.md](../06-portal-frontend/consumo-de-plugins.md) | AppHost, Module Federation |
| [notificacoes.md (portal)](../06-portal-frontend/notificacoes.md) | UI do sino |
| [notificacoes.md (Core API)](../04-core-api/notificacoes.md) | API e integrações |
| Repositório `controle_mp` → `docs/integracao-notificacoes-delpi.md` | Exemplo completo Controle MP |

---

## 11. Apps federated (outro modelo)

Microfrontends (`renderMode: federated`) usam **Module Federation**, não iframe. Fluxo diferente: [microfrontends.md](../05-plugin-system/microfrontends.md).

Para novos módulos nativos no monorepo DELPI, prefira MFE; use **iframe** para legado ou apps hospedadas fora do build do portal.
