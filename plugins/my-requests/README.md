# Minhas Solicitações (MFE)

Microfrontend federado do módulo **Minhas Solicitações**.

- Tile: `/apps/my-requests`
- API: **somente** `/apps/requests-api` (`X-Delpi-Caller-App: my-requests`)
- **Proibido** chamar api-delpi no browser

## Desenvolvimento

```bash
cd plugins/my-requests
npm install
npm run build
npm test
```

Rebuild na stack: `./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui` e depois `--fase mfe --build my-requests`.

## Manifesto

`my-requests.manifest.json` — registrar na Core API (`POST /core-api/admin/apps/register`).

Roadmap: [docs/12-roadmap-e-evolucao/my-requests/PLAYBOOK.md](../../docs/12-roadmap-e-evolucao/my-requests/PLAYBOOK.md).
