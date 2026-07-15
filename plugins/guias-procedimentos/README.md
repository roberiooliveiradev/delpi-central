# Guias e Procedimentos

Microfrontend (Module Federation) da Minha DELPI para consulta e administração de guias e procedimentos.

## Manifesto

Arquivo: `guias-procedimentos.manifest.json`

| Campo | Valor |
|-------|--------|
| id | `guias-procedimentos` |
| version | `1.2.0` |
| type | `microfrontend` |
| entry | `/apps/guias-procedimentos/assets/remoteEntry.js` |
| renderMode | `federated` |

### Permissões

- `guias-procedimentos.access` — consultar conteúdo público + download de mídias/anexos de procedimentos publicados
- `guias-procedimentos.manage` — área administrativa (`/admin`), incluindo rascunhos e upload

### Rotas

| Path | Menu | Permissão |
|------|------|-----------|
| `/apps/guias-procedimentos` | sim | `.access` |
| `/apps/guias-procedimentos/guias/emissao-nota-fiscal` | não | `.access` |
| `/apps/guias-procedimentos/admin` | não | `.manage` |

Rotas filhas de admin (`/admin/departamentos`, `/admin/procedimentos`, …) são internas ao plugin (pathname + `pushState`); não precisam de registro individual no manifesto.

### Registro (pendente)

Após deploy do MFE, registrar o manifesto se a versão no portal estiver desatualizada:

```bash
TOKEN="$(bash infra/scripts/get-dev-token.sh)" \
  bash plugins/guias-procedimentos/scripts/register-manifest.sh
```

## Origem dos dados

- Fonte principal: API DELPI em `/apps/api-delpi/guias-procedimentos` (envelope oficial, snake_case, JWT).
- Cliente: `src/api/guiasProcedimentosApi.ts` (sem `fetch` espalhado nas páginas).
- Fallback temporário: catálogo TypeScript local (`src/data/catalogFallback.ts`) **somente** em falha de rede ou HTTP 5xx. **Não** há fallback em 401/403/404.

## Área administrativa

- Entrada discreta na home: **Administrar conteúdo** (só com `.manage`).
- Departamentos: criar/editar (sem exclusão física).
- Procedimentos: criar (sempre draft), editar com abas **Conteúdo / Mídias / Anexos / Prévia**, publicar / despublicar / arquivar / restaurar.
- Upload (após existir `procedure_id`):
  - imagem (≤ 5 MB; JPEG/PNG/WebP/GIF);
  - vídeo arquivo (≤ 20 MB; MP4/WebM/MOV);
  - vídeo externo (HTTPS YouTube / Vimeo / Google Drive público);
  - anexo (≤ 20 MB; PDF/Office/texto/CSV/imagem).
- Inserção no artigo: HTML controlado (`guide-media` / `guide-attachment`), sem iframe no HTML persistido.
- Editor: textarea HTML + prévia sanitizada (`dompurify`, allowlist alinhada ao `GuideHtmlSanitizer` da API).
- Proteção frontend é UX; a API continua como barreira definitiva.

### Endpoints de mídia/anexo consumidos

| Método | Path |
|--------|------|
| GET | `/admin/procedures/{id}/media` |
| GET | `/admin/procedures/{id}/attachments` |
| POST | `/admin/procedures/{id}/media/images` |
| POST | `/admin/procedures/{id}/media/videos` |
| POST | `/admin/procedures/{id}/media/external-videos` |
| POST | `/admin/procedures/{id}/attachments` |
| PUT | `/admin/media/{id}` |
| POST | `/admin/media/{id}/archive` |
| PUT | `/admin/attachments/{id}` |
| POST | `/admin/attachments/{id}/archive` |
| GET | `/procedures/{id}/media` |
| GET | `/procedures/{id}/attachments` |
| GET | `/media/{id}/file` |
| GET | `/attachments/{id}/file` |

Doc API: `api-delpi/docs/api/guias-procedimentos.md`.

## Artigo público

- HTML sanitizado + hidratação JWT de `img`/`video` protegidos (blob URL).
- Seção **Anexos para download** a partir da listagem pública.
- Vídeo externo: embed gerado no cliente a partir da URL HTTPS cadastrada (sem iframe persistido).

## Fora do escopo (próximas etapas)

- Editor rich text visual / drag-and-drop no HTML
- Transcodificação, thumbnails, upload em partes
- Exclusão física / restauração de mídia arquivada
- Remoção definitiva do catálogo TypeScript

## Desenvolvimento standalone

```bash
cd plugins/plugin-ui && npm install && npm run dev
cd plugins/guias-procedimentos && npm install && VITE_PLUGIN_UI_DEV=1 npm run dev
```

## Testes

```bash
cd plugins/guias-procedimentos && npm test
```

## Infra

Compose: `guias-procedimentos` → `delpi-guias-procedimentos`. Gateway: assets via `/apps/{id}/assets/`.

Rebuild após alterações de front (ordem segura):

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build guias-procedimentos
```
