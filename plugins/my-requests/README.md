# Minhas Solicitações (MFE)

Microfrontend federado do módulo **Minhas Solicitações**.

- Tile: `/apps/my-requests`
- Rotas internas: `/mine`, `/work-queue`, `/new`, `/requests/:id`
- API: **somente** `/apps/requests-api` (`X-Delpi-Caller-App: my-requests`)
- **Proibido** chamar api-delpi no browser
- Ações no detalhe: render-only de `allowed_actions` (sem state machine no TS)
- Ajuda: `src/content/helpTooltips.ts` · Manual: [MANUAL-USUARIO.md](../../docs/12-roadmap-e-evolucao/my-requests/MANUAL-USUARIO.md)

## Desenvolvimento

```bash
cd plugins/my-requests
npm install
npm test
npm run build
```

Rebuild na stack: `./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui` e depois `--fase mfe --build my-requests`.

## Manifesto

`my-requests.manifest.json` — registrar na Core API (`POST /core-api/admin/apps/register`).

Roadmap: [PLAYBOOK.md](../../docs/12-roadmap-e-evolucao/my-requests/PLAYBOOK.md).
