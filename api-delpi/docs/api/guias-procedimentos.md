# Guias e Procedimentos — API

Base (gateway): `/apps/api-delpi/guias-procedimentos`

## Permissões

| Código | Uso |
|--------|-----|
| `guias-procedimentos.access` | Leitura pública + download de mídias/anexos de procedimentos **publicados** |
| `guias-procedimentos.manage` | Administração (inclui rascunhos) + leitura completa |

Sem novas permissões nesta etapa.

## Estados

**Departamentos:** `active` true/false. Públicos só com `active=true`.

**Procedimentos:** `draft` · `published` · `archived`. Públicos só `published` com departamento ativo.

**Mídias/anexos:** soft-archive via `archived_at` (metadado some das listagens; arquivo permanece no volume até limpeza operacional futura). Sem exclusão física de procedimentos.

## Leitura (`.access` ou `.manage`)

| Método | Path | Notas |
|--------|------|-------|
| GET | `/departments` | |
| GET | `/departments/{slug}` | |
| GET | `/procedures/{slug}` | |
| GET | `/procedures/{procedure_id}/media` | Publicado+dept ativo (ou `.manage`) |
| GET | `/procedures/{procedure_id}/attachments` | Idem |
| GET | `/media/{id}/file` | JWT; Range habilitado para `video_file` |
| GET | `/attachments/{id}/file` | JWT download |

## Administração (somente `.manage`)

### Departamentos / procedimentos

| Método | Path |
|--------|------|
| GET/POST/PUT | `/admin/departments` … |
| GET/POST/PUT | `/admin/procedures` … |
| POST | `/admin/procedures/{id}/publish\|unpublish\|archive\|restore` |

### Mídias e anexos

| Método | Path |
|--------|------|
| GET | `/admin/procedures/{id}/media` |
| GET | `/admin/procedures/{id}/attachments` |
| POST | `/admin/procedures/{id}/media/images` (multipart) |
| POST | `/admin/procedures/{id}/media/videos` (multipart) |
| POST | `/admin/procedures/{id}/media/external-videos` (JSON) |
| POST | `/admin/procedures/{id}/attachments` (multipart) |
| PUT | `/admin/media/{id}` |
| POST | `/admin/media/{id}/archive` |
| PUT | `/admin/attachments/{id}` |
| POST | `/admin/attachments/{id}/archive` |

Campos multipart opcionais: `title`, `alt_text` (imagens), `order_index`.

Vídeo externo (JSON):

```json
{
  "url": "https://www.youtube.com/watch?v=…",
  "title": "Demonstração",
  "order_index": 1
}
```

Provedores permitidos: **YouTube**, **Vimeo** e **Google Drive** (HTTPS).

Google Drive: apenas links públicos de **arquivo** (`/file/d/{id}/view` ou `open?id={id}`); a API normaliza para `/file/d/{id}/view`. Pastas e a home do Drive são rejeitadas. Sem iframe HTML arbitrário.

## Storage persistente

| Variável | Default container | Volume host |
|----------|-------------------|-------------|
| `GUIAS_PROCEDIMENTOS_UPLOAD_DIR` | `/app/data/guias-procedimentos` | `${DELPI_DATA_HOST_DIR}/guias-procedimentos` |

Layout:

```text
{base}/procedures/<procedure_uuid>/images|videos|attachments/<uuid><ext>
```

Nomes no disco = UUID (cliente não controla path). Path traversal rejeitado via `resolve()` + prefixo do base.

## Validação

| Tipo | MIME | Extensões | Limite |
|------|------|-----------|--------|
| imagem | jpeg/png/webp/gif | .jpg/.jpeg/.png/.webp/.gif | 5 MB |
| vídeo arquivo | mp4/webm/quicktime | .mp4/.webm/.mov | 20 MB |
| anexo | pdf/office/texto/imagem | pdf, doc(x), xls(x), txt, csv, jpg/png/webp | 20 MB |

Limites alinhados ao `client_max_body_size 20m` do gateway.

## HTTP Range

`GET /media/{id}/file` para `video_file` responde `Accept-Ranges: bytes` e `206 Partial Content` quando o cliente envia `Range`. Imagens/anexos usam `FileResponse` sem Range obrigatório.

## Sanitização HTML

Todo `content_html` passa por `GuideHtmlSanitizer` (allowlist) antes de persistir e na resposta. Mídias **não** são injetadas automaticamente no HTML — o admin insere blocos controlados (`figure.guide-media`, `img`/`video` com `src` protegido, `p.guide-attachment`).

Allowlist adicional (etapa mídias): `figure`, `figcaption`, `img`, `video` + classes `guide-media*`, `guide-attachment*`. `iframe` continua bloqueado no HTML persistido (embed externo é montado no MFE a partir da URL HTTPS validada).

## Envelope

`{ success, message, data, meta }` — campos em **snake_case**.

## Fora do escopo (próximas etapas)

Rich text visual, drag-and-drop no HTML, thumbnails, transcodificação, antivírus, multipart chunked, S3/MinIO, exclusão física.

## Migrations

```bash
python scripts/run_plugins_migrations.py up --plugin guias-procedimentos
```

V004 cria `procedure_media` e `procedure_attachments`.
