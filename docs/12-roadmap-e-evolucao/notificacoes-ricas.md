# Roadmap — Notificações ricas (Minha DELPI)

> **Status:** Fase 1 em implementação (maio/2026)  
> **Escopo:** Core API + Portal

---

## 1. Problema atual

Hoje a notificação é um **texto plano** (`title` + `message` + `type` visual). Não há:

- redirecionamento para apps ou rotas do Portal;
- categorias semânticas (boas-vindas, aniversário, evento);
- conteúdo rico (HTML seguro) ou templates visuais;
- ícone/imagem por tipo de comunicação.

---

## 2. Modelo conceitual (duas dimensões)

| Dimensão | Campo | Exemplos | Uso |
|----------|--------|----------|-----|
| **Severidade visual** | `type` | `info`, `success`, `warning`, `error` | Cor, destaque na UI |
| **Categoria** | `category` | `welcome`, `birthday`, `company_event`, `system`, `announcement`, `custom` | Ícone, template, filtros futuros |
| **Apresentação** | `presentation` | `text`, `html` | Texto simples vs HTML sanitizado |
| **Ação (CTA)** | `action` | ver abaixo | Botão “Abrir app”, “Ver evento” |

### Ação (`action`)

```json
{
  "type": "portal_route",
  "label": "Abrir Minha DELPI Chat",
  "target": "/apps/minha-delpi-ai"
}
```

| `action.type` | `target` | Comportamento no Portal |
|---------------|----------|-------------------------|
| `none` | — | Só marca como lida |
| `portal_route` | `/admin`, `/apps/crm` | `navigate(target)` |
| `external_url` | `https://...` | Nova aba (`noopener`) |

---

## 3. Conteúdo HTML personalizado

- Campo `htmlContent` (persistido como `html_content`).
- **Sanitização obrigatória no backend** (`bleach`) antes de gravar.
- Tags permitidas: `p`, `br`, `strong`, `em`, `ul`, `ol`, `li`, `a`, `h3`, `h4`, `span`.
- Proibido: `script`, `iframe`, `on*` handlers, `javascript:`.
- `message` continua obrigatório como **fallback** (preview, push, leitores simples).

---

## 4. Templates (Fase 2)

Catálogo fixo no Portal (componentes React, sem HTML arbitrário):

| Template | `category` | Variáveis (`metadata`) |
|----------|------------|-------------------------|
| Boas-vindas | `welcome` | `userName` |
| Aniversário | `birthday` | `userName`, `years` |
| Evento empresa | `company_event` | `eventName`, `eventDate`, `location` |

Admin escolhe template + variáveis → backend grava `presentation: "template"` + `metadata` (Fase 2).

---

## 5. API (evolução)

### Resposta `GET /me/notifications`

```json
{
  "id": "uuid",
  "title": "Bem-vindo à Minha DELPI",
  "message": "Sua conta está pronta.",
  "type": "success",
  "category": "welcome",
  "presentation": "html",
  "htmlContent": "<p>Olá, <strong>Rob</strong>!</p>",
  "icon": "sparkles",
  "action": {
    "type": "portal_route",
    "label": "Explorar aplicativos",
    "target": "/"
  },
  "read": false,
  "createdAt": "2026-05-18T12:00:00Z"
}
```

### Envio `POST /admin/notifications` e `/integrations/notifications`

Campos adicionais opcionais: `category`, `presentation`, `htmlContent`, `icon`, `action`, `metadata`, `expiresAt`.

---

## 6. UI Portal (Fase 1)

- **Sidebar:** card por notificação (título, cor por `type`, ícone por `category`, HTML ou texto, botão CTA).
- **Admin → Notificações:** formulário com categoria, modo texto/HTML, ação e preview.
- **Home:** cards enriquecidos (mesmo componente).

---

## 7. Fases

| Fase | Entrega |
|------|---------|
| **1** (atual) | Migration, sanitização HTML, action, category, UI Portal + admin |
| **2** | Templates React (`welcome_v1`, `birthday_v1`, `company_event_v1`) — **implementado** |
| **3** | Agendamento, expiração automática, auditoria de envios |
| **4** | Preferências do usuário (opt-out por categoria) |
| **5** | Centro `/notifications` com histórico paginado |

---

## 8. Segurança

1. HTML sempre sanitizado na Core API.
2. `portal_route` só aceita paths relativos (`/...`), sem `//` externo.
3. `external_url` só `https:`.
4. Integrações externas: rate limit (pendente).

---

## 9. Referências

- [Notificações Core API](../04-core-api/notificacoes.md)
- [Roadmap notificações (base)](../../minha-delpi-ai-api/docs/roadmap/notificacoes-minha-delpi.md)
