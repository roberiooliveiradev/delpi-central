# Mural de Acessos

Centraliza QR Codes da fábrica em **um ou mais murais**. Cada mural tem o próprio QR, URL e lista de acessos — útil para separar públicos (RH, qualidade, portaria).

```text
QR na parede (um por mural)
  → /p/mural-acessos/menu/{token}   (public-hub, sem login)
      → GET /apps/api-delpi/public/mural-acessos/menu/{token}
          → ícones daquele mural

Portal (admin)
  → /apps/mural-acessos
      → lista de murais
  → /apps/mural-acessos/{id}
      → CRUD dos acessos + QR imprimível
```

O mural inicial (token `mural`) preserva o QR já impresso e os acessos cadastrados antes desta evolução.

## Rotas da UI

| Path | Quem | Descrição |
|------|------|-----------|
| `/apps/mural-acessos` | autenticado | Lista e cria murais |
| `/apps/mural-acessos/{id}` | autenticado | Textos, token, QR e acessos do mural |
| `/p/mural-acessos/menu/{token}` | público | Menu daquele mural |

## API

Base: `/apps/api-delpi` — doc: [api-delpi/docs/api/mural-acessos.md](../../api-delpi/docs/api/mural-acessos.md)

| Método | Endpoint | Permissão |
|--------|----------|-----------|
| GET/POST | `/mural-acessos/hubs` | access / manage |
| GET/PUT/DELETE | `/mural-acessos/hubs/{id}` | access / manage |
| GET | `/mural-acessos/hubs/{id}/qr.png` | access |
| GET/POST | `/mural-acessos/hubs/{id}/links` | access / manage |
| PUT | `/mural-acessos/hubs/{id}/links/reorder` | manage |
| PUT/DELETE | `/mural-acessos/links/{id}` | manage |
| POST/DELETE | `/mural-acessos/links/{id}/image` | manage |
| GET | `/public/mural-acessos/menu/{token}` | público |
| GET | `/public/mural-acessos/links/{id}/image` | público |

`X-Delpi-Caller-App: mural-acessos`

## Permissões

| Código | Uso |
|--------|-----|
| `mural-acessos.access` | Abrir o app, ver QR e listas |
| `mural-acessos.manage` | Criar murais, cadastrar, editar, ordenar e anexar imagens |

## Dev

```bash
cd plugins/mural-acessos && npm install && npm run build
TOKEN=$(bash infra/scripts/get-dev-token.sh) bash plugins/mural-acessos/scripts/register-manifest.sh
./infra/scripts/up-dev-sequential.sh --fase api --build api-delpi
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build mural-acessos public-hub
```

Migrations (só `up` em ambientes com dados):

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py status --plugin mural-acessos
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin mural-acessos
```

## Smoke

```bash
curl -fsSI http://localhost/apps/mural-acessos/assets/remoteEntry.js | head -3
curl -fsS http://localhost/apps/api-delpi/public/mural-acessos/menu/mural
```

## Estrutura

```text
src/
  api/           httpClient + muralAcessosApi
  pages/         lista de murais + detalhe (QR + acessos)
  ui/            factories @delpi/plugin-ui
  content/       textos PT-BR
```
