# TV Dashboard API

API dedicada do plugin **Painéis TV** — programações rotativas, slides e link público via `public-hub`.

Documentação completa: [`docs/12-roadmap-e-evolucao/tv-dashboard/README.md`](../docs/12-roadmap-e-evolucao/tv-dashboard/README.md)

---

## Endpoints

### Público (sem JWT)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/public/present/{token}` | Payload completo da apresentação (+ view count) |
| `POST` | `/public/present/{token}/heartbeat` | Sinal «TV online» para o admin |

Gateway: `/apps/tv-dashboard-api/public/present/{token}`

### Admin (JWT + RBAC)

| Grupo | Prefixo |
|---|---|
| Programações | `/playlists` |
| Telas | `/playlists/{id}/slides` |
| Catálogo nativo | `/native-screens` |
| Conteúdo UI / presets | `/content/ui`, `/content/slide-presets`, `/content/branch-scope` |

Operações extras: ativar/desativar link, regenerar token, QR, reorder slides, duplicate.

---

## Link público gerado

```
{PUBLIC_BASE_URL}{TV_DASHBOARD_PUBLIC_PATH}/{publicToken}
```

Default: `http://localhost/p/tv-dashboard/present/{token}`

Variáveis: `PUBLIC_BASE_URL`, `TV_DASHBOARD_PUBLIC_PATH` (`tv_app/config.py`).

---

## Dados e integrações

- **Postgres:** schema `tv_dashboard` (`postgres-plugins`)
- **Migrations:** `TV_DASHBOARD_RUN_MIGRATIONS_ON_STARTUP=true` (default)
- **KPIs nativos:** `DelpiProductionGateway` → api-delpi (service token)
- **Conteúdo PT-BR:** `tv_app/content/tv_dashboard_content.json`
- **Catálogo telas:** `tv_app/content/native_screens.json`, `dashboard_slide_presets.json`

---

## Desenvolvimento

```bash
cd tv-dashboard-api
pip install -r requirements.txt
pip install -e ../shared[fastapi]
pytest tests/ -q
```

Com Compose dev, código montado em volume (`../tv-dashboard-api:/app`).

---

## Testes

```bash
pytest tests/ -q
# smoke público: tests/test_public_present.py
# conteúdo UI: tests/test_content_routes.py
```

---

## Container

- Compose: `tv-dashboard-api` → `delpi-tv-dashboard-api`
- Depende: `postgres-plugins`, `keycloak`, `api-delpi`
