# TV Dashboard API

API dedicada do plugin **Painéis TV** — programações rotativas com link público via `public-hub`.

## Endpoints principais

- Admin (JWT): `/playlists`, `/playlists/{id}/slides`, `/native-screens`
- Público: `GET /public/present/{token}`

## Desenvolvimento

```bash
cd tv-dashboard-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest tests/ -q
```

## Link público

`{PUBLIC_BASE_URL}/p/tv-dashboard/present/{token}`
