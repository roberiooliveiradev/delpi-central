# public-hub — shell público do portal

`public-hub` é o **irmão público do portal Minha DELPI**: um único SPA estático (Vite + React, **sem** Module Federation e **sem** Keycloak) que serve **páginas públicas sem login** de vários apps, roteadas por token.

Ele existe porque o portal (`/portal`) tem gate de autenticação global (`location /` → login). Páginas que precisam ser abertas por qualquer pessoa (ex.: agradecimento por QR, formulários personalizáveis) **não** podem morar dentro do portal — vivem aqui, atrás de um prefixo de gateway próprio.

> **Regra de ouro:** páginas públicas **só leem/gravam por token opaco**. Nunca há sessão, cookie de login ou dado sensível de terceiros. Cada view fala apenas com o endpoint `/public/...` da API do seu app.

---

## Rotas

| Tipo | Formato | Exemplo |
|---|---|---|
| **Canônico** | `/p/{app}/{page}/{token}` | `/p/customer-experience/form/abc123` |
| **Alias legado** | `/welcome/{token}` → `customer-experience/thanks` | mantém QR já impressos |

O gateway (`gateway/nginx.conf` e `nginx.dev.conf`) já encaminha **todo** `^~ /p/` para o container `delpi-public-hub`, **antes** do catch-all `location /` do portal. **Um app novo não precisa mexer no gateway.**

---

## Arquitetura (config-driven)

```
/p/{app}/{page}/{token}
        │
        ▼
  src/shell/routing.ts      resolve → { appId, pageId, token }
        │
        ▼
  src/shell/registry.ts     publicRegistry[appId][pageId] → PublicPageDefinition
        │
        ▼
  src/shell/PublicShell.tsx transversal: marca DELPI, loading, not-found, erro, título
        │
        ▼
  page.load(ctx) → page.render(data, ctx)   (a view do app)
```

- **Shell (transversal)** — `src/shell/`. Cuida de tudo que é comum: fundo/branding (`pub-*` no `shell.css`), spinner, estados de erro/página-não-encontrada, `document.title`, `noindex`. **Não** conhece nenhum app específico.
- **App (view)** — `src/apps/<app>/`. Cada app só fornece: como **carregar** os dados por token (`load`) e como **renderizar** (`render`). CSS da view usa prefixo próprio do app (ex.: `cxp-`, `cxfb-`) e as variáveis de marca `--pub-*`.

### Contrato `PublicPageDefinition` (`src/shell/types.ts`)

```ts
interface PublicPageContext { appId: string; pageId: string; token: string; }

interface PublicPageDefinition {
  documentTitle?: string;          // título do documento
  notFoundMessage?: string;        // texto quando load() retorna null/undefined
  load: (ctx: PublicPageContext) => Promise<unknown>;   // null/undefined => "não encontrado"
  render: (data: unknown, ctx: PublicPageContext) => ReactNode;
}
```

O shell trata `load` retornando `null`/`undefined` como **404 (não encontrado)** e exceções como **erro** — a view não precisa reimplementar esses estados.

---

## Como adicionar uma página pública para um app novo

Exemplo: app `foo` com uma página `status` em `/p/foo/status/{token}`.

### 1. API do app — endpoint público por token

Na API dedicada do app (ex.: `foo-api`), exponha uma rota **sem login** sob `/public/` (bypass de JWT no middleware, como em `customer-experience-api/cx_app/middleware/auth_middleware.py`):

```
GET /apps/foo-api/public/status/{token}
→ 200 { ...campos que a página precisa }
→ 404 se token inexistente/inativo
```

Envelope padrão `{ success, message, data }`. Token opaco (`secrets.token_urlsafe(32)`).

### 2. View do app no public-hub

Crie `src/apps/foo/`:

`src/apps/foo/api.ts`
```ts
const API_BASE = "/apps/foo-api";

export type FooStatus = { title: string; state: string };

type ApiEnvelope<T> = { success: boolean; message?: string; data: T };

export async function fetchFooStatus(token: string): Promise<FooStatus | null> {
  const res = await fetch(`${API_BASE}/public/status/${encodeURIComponent(token)}`, {
    headers: { Accept: "application/json" },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Não foi possível carregar a página.");
  const env = (await res.json()) as ApiEnvelope<FooStatus>;
  return env.success === false ? null : env.data;
}
```

`src/apps/foo/StatusPage.tsx`
```tsx
import type { FooStatus } from "./api";
import "./status.css"; // opcional; use prefixo próprio (ex.: foo-) + variáveis --pub-*

export function StatusView({ status }: { status: FooStatus }) {
  return (
    <div className="foo-card">
      <h1>{status.title}</h1>
      <p>{status.state}</p>
    </div>
  );
}
```

`src/apps/foo/pages.tsx`
```tsx
import type { AppPublicPages } from "../../shell/types";
import { fetchFooStatus, type FooStatus } from "./api";
import { StatusView } from "./StatusPage";

export const fooPages: AppPublicPages = {
  status: {
    documentTitle: "Status — DELPI",
    notFoundMessage: "Este link não está mais disponível.",
    load: ({ token }) => fetchFooStatus(token),
    render: (data) => <StatusView status={data as FooStatus} />,
  },
};
```

### 3. Registrar no shell

`src/shell/registry.ts`
```ts
import { fooPages } from "../apps/foo/pages";

export const publicRegistry: PublicRegistry = {
  "customer-experience": customerExperiencePages,
  foo: fooPages,            // ← novo app
};
```

### 4. QR / link

Gere o QR na API do app apontando para a URL pública canônica:

```
{PUBLIC_BASE_URL}/p/foo/status/{token}
```

Pronto. **Não** é preciso: novo container, nova `location` no gateway, nem manifesto no core-api. O `public-hub` já serve a rota.

---

## O que fica no shell vs no app

| Responsabilidade | Onde |
|---|---|
| Fundo/branding, spinner, not-found, erro, título, `noindex` | **shell** (`src/shell/`, classes `pub-*`) |
| Carregar dados por token e renderizar a view | **app** (`src/apps/<app>/`) |
| Endpoint público `/public/...` + token opaco | **API do app** |
| Roteamento `/p/{app}/{page}/{token}` e alias | **shell** (`routing.ts`) + gateway (`^~ /p/`) |

### Não faça
- Colocar login/sessão/cookie de autenticação aqui — é superfície pública.
- Criar um SPA/container novo por app público (o modelo antigo `*-public`); registre uma view no shell.
- Reimplementar loading/erro/branding na view — use os estados do shell.
- Adicionar `location` no gateway para cada app — `^~ /p/` já cobre.
- Expor dados de terceiros ou listagens no endpoint público — só o registro do token.

---

## Exemplo de referência: `customer-experience`

Páginas **públicas separadas e independentes**, cada uma com seu QR próprio:

| Página | Rota | `load` |
|---|---|---|
| Agradecimento | `/p/customer-experience/thanks/{token}` (alias `/welcome/{token}`) | `GET /apps/customer-experience-api/public/participants/{token}` |
| Formulário | `/p/customer-experience/form/{token}` | `GET /apps/customer-experience-api/public/forms/{token}` |

Ver `src/apps/customer-experience/` (`api.ts`, `ThanksPage.tsx`, `FormPage.tsx`, `pages.tsx`).

### Painéis TV (`tv-dashboard`)

Apresentação rotativa em modo **kiosk** (sem logo DELPI):

| Página | Rota | `load` |
|---|---|---|
| Apresentação TV | `/p/tv-dashboard/present/{token}` | `GET /apps/tv-dashboard-api/public/present/{token}` |

Ver `src/apps/tv-dashboard/` (`api.ts`, `PresentationView.tsx`, `pages.tsx`).  
Motor compartilhado: `plugins/tv-dashboard-presentation/`.  
Doc: `docs/12-roadmap-e-evolucao/tv-dashboard/README.md`.

**Rebuild obrigatório** do `public-hub` após alterações na view ou no pacote de apresentação.

---

## Build e deploy

```bash
npm install
npm run build      # tsc -b && vite build (base "/p/")
npm run lint
```

- Container: serviço `public-hub` / `delpi-public-hub` no `infra/docker-compose.yml` e `docker-compose.dev.yml`.
- Nginx do container (`nginx.conf`) serve `/p/` (base dos assets) e `/welcome/` (alias) apontando para o mesmo `index.html`.
- Recriar em dev: `docker compose -f infra/docker-compose.dev.yml --env-file infra/.env up --build -d --force-recreate public-hub` e recarregar o gateway (`docker exec delpi-gateway nginx -s reload`).

Playbook e contexto: `docs/12-roadmap-e-evolucao/customer-experience/PLAYBOOK-EXCELENCIA.md` (§5).
