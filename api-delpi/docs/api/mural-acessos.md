# Mural de Acessos

Vários murais de links, cada um com QR e menu público próprios. Admin no portal; leitura pública sem JWT.

**Plugin:** [plugins/mural-acessos/README.md](../../../plugins/mural-acessos/README.md)  
**Página pública:** `/p/mural-acessos/menu/{token}` (public-hub; o mural inicial usa o token `mural`)

## Contrato

Envelope `{ success, message, data, meta }` via `api_delpi_success`.  
Schema Postgres: `mural_acessos` (plugins). Imagens no volume `MURAL_ACESSOS_UPLOAD_DIR`.

| operationId | entity | shape |
|-------------|--------|-------|
| `list_mural_acessos_hubs` | `mural_access_hub` | paged_list |
| `create_mural_acessos_hub` / `get_*` / `update_*` / `delete_*` | `mural_access_hub` | scalar |
| `list_mural_acessos_links` / `reorder_mural_acessos_links` | `mural_access_link` | paged_list |
| `create_mural_acessos_link` / `update_*` / `delete_*` / `upload_*` | `mural_access_link` | scalar |
| `list_public_mural_acessos_menu` / `list_public_mural_acessos_menu_by_token` | `mural_access_menu` | paged_list |

Binários (`qr.png`, imagens) saem do envelope — `FileResponse` / `image/png`.

## Admin (JWT)

Prefixo: `/mural-acessos`

| Método | Path | operationId | Perm. |
|--------|------|-------------|-------|
| GET | `/hubs` | `list_mural_acessos_hubs` | access |
| POST | `/hubs` | `create_mural_acessos_hub` | manage |
| GET | `/hubs/{id}` | `get_mural_acessos_hub` | access |
| PUT | `/hubs/{id}` | `update_mural_acessos_hub` | manage |
| DELETE | `/hubs/{id}` | `delete_mural_acessos_hub` | manage |
| GET | `/hubs/{id}/qr.png` | `get_mural_acessos_hub_qr` | access |
| GET | `/hubs/{id}/links` | `list_mural_acessos_links` | access |
| POST | `/hubs/{id}/links` | `create_mural_acessos_link` | manage |
| PUT | `/hubs/{id}/links/reorder` | `reorder_mural_acessos_links` | manage |
| PUT | `/links/{id}` | `update_mural_acessos_link` | manage |
| DELETE | `/links/{id}` | `delete_mural_acessos_link` | manage |
| POST | `/links/{id}/image` | `upload_mural_acessos_link_image` | manage |
| DELETE | `/links/{id}/image` | `delete_mural_acessos_link_image` | manage |
| GET | `/links/{id}/image` | `get_mural_acessos_link_image` | access |

Body do mural: `title`, `subtitle`, `publicToken` (slug único, 2–40, letras/números/hífen).  
Body do link: `title`, `url` (`http`/`https`), `description`, `active`.  
Upload: `multipart/form-data` campo `file` (JPEG/PNG/WebP/GIF, máx. 5 MB).

## Público (sem JWT)

Liberado em `auth_middleware` pelo prefixo `/public/mural-acessos/`.

| Método | Path | operationId |
|--------|------|-------------|
| GET | `/public/mural-acessos/menu` | `list_public_mural_acessos_menu` (alias do token `mural`) |
| GET | `/public/mural-acessos/menu/{token}` | `list_public_mural_acessos_menu_by_token` |
| GET | `/public/mural-acessos/links/{id}/image` | `get_public_mural_acessos_link_image` |

O menu público devolve só itens `active=true` daquele mural. Imagem de item inativo retorna 404.

```bash
curl -fsS http://localhost/apps/api-delpi/public/mural-acessos/menu/mural
```

## Persistência

| Peça | Onde |
|------|------|
| Metadados | schema `mural_acessos` (postgres-plugins) |
| Ícones | `${DELPI_DATA_HOST_DIR}/mural-acessos` → `/app/data/mural-acessos` |

Não resetar o schema em produção. Aplicar só `up`.
