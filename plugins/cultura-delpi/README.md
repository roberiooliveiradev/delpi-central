# Cultura DELPI — plugin Minha DELPI

Microfrontend (Module Federation) para exibir e administrar propósito, missão, visão e valores da DELPI.

O conteúdo institucional é persistido na **API DELPI** (`postgres-plugins`, schema `cultura_delpi`).

---

## Rotas

| Rota | Finalidade | Permissão |
|------|------------|-----------|
| `/apps/cultura-delpi` | Painel público de visualização | `cultura-delpi.view` |
| `/apps/cultura-delpi/admin` | Edição do conteúdo institucional | `cultura-delpi.manage` |

Superadmin tem bypass nas permissões da API.

---

## Endpoints consumidos

Base: `/apps/api-delpi/cultura-delpi`

| Método | Path | Uso |
|--------|------|-----|
| GET | `/content` | Carregar conteúdo (painel e admin) |
| PUT | `/content` | Salvar conteúdo (somente admin) |

Envelope padrão da API DELPI: `{ success, message, data, meta }`.

Campos em `data`: `proposito`, `missao`, `visao`, `valores[]`, `updatedAt`, `updatedByUserId`, `updatedByName`.

---

## Permissões necessárias

- **`cultura-delpi.view`** — leitura no painel público (GET).
- **`cultura-delpi.manage`** — edição na rota admin (GET + PUT).

Após registrar o manifesto, associar as permissões às roles desejadas via Admin → RBAC.

---

## Desenvolvimento local

```bash
cd plugins/cultura-delpi
npm install
npm run build
npm run lint
```

Preview local (standalone, sem token do Portal):

```bash
npm run dev
```

> No modo federado, o Portal injeta `getAccessToken` via Module Federation. Em `npm run dev` standalone, as chamadas à API podem falhar por falta de JWT — use o ambiente Docker com Portal logado para testes integrados.

---

## Docker

```bash
cd infra
docker compose -f docker-compose.dev.yml build cultura-delpi --no-cache
docker compose -f docker-compose.dev.yml up -d cultura-delpi gateway api-delpi
```

Validar assets:

```bash
curl -sI http://localhost/apps/cultura-delpi/assets/remoteEntry.js | head -5
```

---

## Registro do manifesto

A versão atual do manifesto é **`0.2.0`** (inclui rota admin e permissão `cultura-delpi.manage`).

Registrar no Portal (requer `apps.manage` ou superadmin):

```bash
export TOKEN="<access_token>"
./scripts/register-manifest.sh
```

Consulte também: `docs/10-guias-operacionais/registrar-plugin-dev-local.md`.

---

## Estrutura relevante

```
src/
  api/
    httpClient.ts       # fetch + Bearer token via getAccessToken
    culturaDelpiApi.ts  # GET/PUT content
  pages/
    PainelCulturaPage.tsx  # visualização
    AdminCulturaPage.tsx   # edição
  types/
    culturaDelpi.ts     # CulturaDelpiContent, UpdateCulturaDelpiContentPayload
```

Textos estáticos de UI (títulos, placeholder) ficam em `src/content/culturaDelpi.ts`.
