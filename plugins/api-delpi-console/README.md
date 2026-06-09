# Console API DELPI

Microfrontend para explorar rotas da **api-delpi**, executar requests de teste e inspecionar envelopes de resposta.

## Rotas do app

| Path | Descrição |
|------|-----------|
| `/apps/api-delpi-console` | Início — saúde da API |
| `/apps/api-delpi-console/documentacao` | Documentação interativa (`/apps/api-delpi/docs`) com JWT automático |
| `/apps/api-delpi-console/explorer` | Explorador OpenAPI com executor de requests |
| `/apps/api-delpi-console/spec` | Inventário OpenAPI + download JSON |
| `/apps/api-delpi-console/history` | Histórico local de chamadas |

## Permissão

- `api-delpi-console.view`

## Desenvolvimento

```bash
cd plugins/api-delpi-console
npm install
npm run dev
```

Build de produção:

```bash
npm run build
```

## Docker

```bash
cd infra
docker compose up -d --build api-delpi-console
```

## Registro na Core API

```bash
curl -X POST "http://localhost/core-api/admin/apps/register" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @api-delpi-console.manifest.json
```

## Documentação interativa

O console embute a documentação oficial da api-delpi (`/docs`) e envia o JWT do portal via `postMessage` (`DELPI_AUTH`), o mesmo contrato usado em iframes do portal. Ver `api-delpi/app/main.py`.

## Header de rastreamento

Todas as chamadas à api-delpi enviam:

```http
X-Delpi-Caller-App: api-delpi-console
```

## Playbook e roadmap

Ver `api-delpi/docs/roadmaps/playbook-api-delpi-console.md`.
