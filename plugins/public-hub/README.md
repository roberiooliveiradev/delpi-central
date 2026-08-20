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
  src/shell/PublicShell.tsx           transversal: marca, splash, fallback not-found/erro, título
  src/shell/PublicLoadingSplash.tsx   wrapper fino de `@delpi/plugin-ui` `ScreenLoading`
  src/shell/PublicFallback.tsx        not-found / erro (marca em destaque no chrome kiosk)
        │
        ▼
  page.load(ctx) → page.render(data, ctx)   (a view do app)

**Assinatura pública (`/p/transformometro/sign/…`):** o painel vem de `@delpi/signature-kit`
(source do `plugin-ui` **bundled** no hub). Não usa o remote MF `./signature` — evita
crash de `createPortal`/HelpTooltip no share `react-dom`.

No Docker, o `Dockerfile` copia só `plugin-ui/src/components/signature` + `overlayLayers.ts`
(contexto `plugins/`). Não é `COPY plugin-ui` completo.
```

- **Shell (transversal)** — `src/shell/`. Cuida de tudo que é comum: fundo/branding (`pub-*` no `shell.css`), spinner, estados de erro/página-não-encontrada, `document.title`, `noindex`. **Não** conhece nenhum app específico.
- **App (view)** — `src/apps/<app>/`. Cada app só fornece: como **carregar** os dados por token (`load`) e como **renderizar** (`render`). CSS da view usa prefixo próprio do app (ex.: `cxp-`, `cxfb-`) e as variáveis de marca `--pub-*`.

### Contrato `PublicPageDefinition` (`src/shell/types.ts`)

```ts
interface PublicPageContext { appId: string; pageId: string; token: string; }

interface PublicPageDefinition {
  documentTitle?: string;          // título do documento
  chrome?: "default" | "kiosk" | "fullpage";
  notFoundTitle?: string;          // título quando load() retorna null (TV: «Programação indisponível»)
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
| Fundo/branding, splash (`ScreenLoading` do kit), not-found, erro, título, `noindex` | **shell** (`src/shell/`, classes `pub-*`) |
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
| Assinatura de ata Transforma+ | `/p/transformometro/sign/{token}` | `GET/POST /apps/transformometro-api/public/meeting-minutes/sign-invites/{token}` |

O formulário público (jul/2026) inclui modo wizard (`oneQuestionPerPage`), páginas com fundo/ilustração, barra de progresso, layout centralizado, fundo em viewport e modo escuro. Ver `FormPage.tsx` + `form.css`.

Ver `src/apps/customer-experience/` (`api.ts`, `ThanksPage.tsx`, `FormPage.tsx`, `pages.tsx`).

### Código de Ética (`codigo-etica`)

Leitura do PDF institucional (token estático `aberto`) para quem **não tem conta** no Minha DELPI:

| Página | Rota | Conteúdo |
|---|---|---|
| Código | `/p/codigo-etica/codigo/aberto` | PDF `/apps/codigo-etica/documents/codigo-de-etica.pdf` |

Sem API e sem login. O link também aparece no MFE autenticado `codigo-etica` para copiar.

Ver `src/apps/codigo-etica/` · doc: [plugins/codigo-etica/README.md](../codigo-etica/README.md).

### Canal de Denúncia (`canal-denuncia`)

Formulário aberto (token estático `aberto`) para quem **não tem conta** no Minha DELPI:

| Página | Rota | `load` / submit |
|---|---|---|
| Denúncia | `/p/canal-denuncia/denuncia/aberto` | `POST /apps/api-delpi/public/canal-denuncia/denuncias` |

O relato continua anônimo. O link também aparece no MFE autenticado `canal-denuncia` para copiar.

Ver `src/apps/canal-denuncia/` · doc: [plugins/canal-denuncia/README.md](../canal-denuncia/README.md).

### Central de Agendamento (`central-agendamento`)

| Página | URL | API |
|--------|-----|-----|
| Solicitar reserva | `/p/central-agendamento/book/{token}` | `GET/POST /apps/api-delpi/public/scheduling/resources/{token}…` |

Token opaco por recurso (`public_booking_enabled`). Sem login. O admin do MFE gera/copia o link.

Ver `src/apps/central-agendamento/` · doc: [api-delpi/docs/api/central-agendamento.md](../../api-delpi/docs/api/central-agendamento.md).

### Mural de Acessos (`mural-acessos`)

Menu estilo smartphone por mural (token na URL):

| Página | Rota | `load` |
|---|---|---|
| Menu | `/p/mural-acessos/menu/{token}` | `GET /apps/api-delpi/public/mural-acessos/menu/{token}` |

O mural inicial usa o token `mural`. Cadastro, novos murais e QR imprimível ficam no MFE autenticado `mural-acessos`.

Ver `src/apps/mural-acessos/` · doc: [plugins/mural-acessos/README.md](../mural-acessos/README.md).

### Kaizen — sugestão pública (`kaizen`)

Formulário aberto (token estático `aberto`) para colaboradores enviarem ideias:

| Página | Rota | `load` / submit |
|---|---|---|
| Sugestão | `/p/kaizen/sugestao/aberto` | `POST /apps/api-delpi/public/kaizen/suggestions` |

Wizard **2 etapas** (Identificação → Melhoria), barra de **% preenchimento** e tela de conclusão. Tokens de marca `--pub-*` em `kaizen-form.css`.

Compartilhamento (QR/link/PNG) fica no MFE autenticado `kaizometro` (botão **Compartilhar sugestão**).

Ver `src/apps/kaizen/` · doc: [plugins/kaizometro/README.md](../kaizometro/README.md).

### Fila de produção — cockpit do operador (`production-control`)

Link aberto para o chão de fábrica acompanhar a carga máquina do próprio posto:

| Página | Rota | `load` |
|---|---|---|
| Cockpit | `/p/production-control/cockpit/aberto?branch=01` | `GET /apps/production-control-api/public/machine-load/aberto?branch=01` |

- **Filial na query** (`branch=01` SC, `02` ES); ausente ou inválida cai em `01`.
- **Seleção de posto** na primeira abertura; a escolha fica em `localStorage` por filial, com botão **Trocar posto** no cabeçalho.
- **Tempo real:** `WS /apps/production-control-api/public/machine-load/{token}/ws?branch=…` avisa (`machine_load_updated`) quando o PCP reordena a fila ou atualiza do TOTVS; o cliente refaz a leitura HTTP. Fallback de polling a cada 90s e reconexão a cada 5s.
- **Somente leitura:** sem drag-and-drop, sem PATCH — o sequenciamento é exclusivo do PCP. A resposta pública omite `refreshed_by` e `sequence_updated_by`.
- **Copiar OP:** botão ao lado de cada ordem, com fallback `execCommand` para tablet em HTTP (sem Clipboard API).
- **Layout:** barra de marca DELPI fixa no topo (gradiente, logo, nome do centro de trabalho em destaque, chips de contagem e selo *Ao vivo*) e fila em linhas alinhadas por colunas, com cabeçalho de rótulos único. A largura do palco é liberada por app (`.pub-content--fullpage:has(.pcp-pub)`), mesmo padrão do Código de Ética. Abaixo de 900px cada linha volta ao formato empilhado (rótulo + valor) para tablet em retrato.
- **Desenho do PA:** botão **Ver desenho** no cartão quando há `pa_product_code`. O hub chama `GET /apps/production-control-api/public/machine-load/{token}/drawings/{pa}/pdf?branch=…`; o próprio BFF lê o arquivo da pasta do FILESERVER montada no container (`/drawing-pdfs`) e só entrega se o PA estiver na fila publicada. A api-delpi **não** participa desse fluxo. Pré-requisito de infra: `PC_DRAWING_PDF_HOST_PATH` apontando para o share ([infra/README-ambiente.md](../../infra/README-ambiente.md) § Biblioteca PDF de desenhos).

O PCP copia o link pelo botão **Link do operador** na página Carga máquina do MFE `production-control`.

Ver `src/apps/production-control/` · doc: [plugins/production-control/README.md](../production-control/README.md).

### Painéis TV (`tv-dashboard`)

Apresentação rotativa em modo **kiosk** (sem logo DELPI):

| Página | Rota | `load` |
|---|---|---|
| Apresentação TV | `/p/tv-dashboard/present/{token}` | `GET /apps/tv-dashboard-api/public/present/{token}` |

**Fit na TV:** `presentationFitPolicy` — contain + **`zoom` no kiosk** (para Adeus Pendrive medir scrollWidth = tamanho visual; `transform: scale` deixava 1920px e deslocava o slide). Pin do viewport sem offset (documento = área útil).

Ver `src/apps/tv-dashboard/` (`api.ts`, `PresentationView.tsx`, `pages.tsx`).  
Motor: `plugins/tv-dashboard-presentation/` (`DesignViewportStage`, `presentationFitPolicy`).  

**Rebuild obrigatório** do `public-hub` + pacote de apresentação após alterações.

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
