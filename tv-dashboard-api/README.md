# TV Dashboard API

API dedicada do plugin **Painéis TV** — programações rotativas, slides, mídia, WebSocket e link público via `public-hub`.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)

---

## Endpoints

### Público (sem JWT)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/public/present/{token}` | Payload completo da apresentação (+ view count) |
| `WS` | `/public/present/{token}/ws` | Push `presentation_updated` para a TV |
| `GET` | `/public/present/{token}/media/{assetId}` | Mídia de comunicado (imagem/vídeo) |
| `POST` | `/public/present/{token}/heartbeat` | Sinal «TV online» para o admin |

### Admin (JWT + RBAC)

| Grupo | Prefixo |
|---|---|
| Programações | `/playlists` |
| Telas | `/playlists/{id}/slides` |
| Mídia | `/playlists/{id}/media` |
| Tempo real | `WS /playlists/{id}/presentation-ws?access_token=…` |
| Catálogo nativo | `/native-screens` |
| Conteúdo UI / presets | `/content/ui`, `/content/slide-presets`, `/content/branch-scope` |

Operações extras: ativar/desativar link, regenerar token, QR, reorder slides, duplicate.

---

## Mídia persistente

| Variável | Container | Host |
|---|---|---|
| `TV_DASHBOARD_MEDIA_UPLOAD_DIR` | `/app/data/tv-dashboard/media` | `${DELPI_DATA_HOST_DIR}/tv-dashboard/media` |

Migration: `V002__media_assets.sql`

---

## WebSocket

Salas por `playlist_id`. Evento típico:

```json
{ "type": "presentation_updated", "reason": "slide_updated", "revision": "…" }
```

Disparado após CRUD de slides, upload de mídia, alterações na programação e exclusão.

---

## Desenvolvimento

```bash
cd tv-dashboard-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest tests/ -q
```

---

## Testes

```bash
pytest tests/ -q
# público: tests/test_public_present.py
# realtime: tests/test_presentation_realtime.py
# comunicado/mídia: tests/test_comunicado_media.py
```

---

## Container

- Compose: `tv-dashboard-api` → `delpi-tv-dashboard-api`
- Depende: `postgres-plugins`, `keycloak`, `api-delpi`
- Gateway: requer headers WebSocket (`Upgrade`, `Connection`) em `/apps/tv-dashboard-api/`
