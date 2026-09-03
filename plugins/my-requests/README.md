# Minhas Solicitações (MFE)

Microfrontend federado do módulo **Minhas Solicitações**.

- Tile: `/apps/my-requests`
- Rotas internas: `/mine`, `/work-queue`, `/new`, `/requests/:id`
- API: **somente** `/apps/requests-api` (`X-Delpi-Caller-App: my-requests`)
- **Proibido** chamar api-delpi no browser
- Ações no detalhe: render-only de `allowed_actions` (sem state machine no TS)
- Ajuda: `src/content/helpTooltips.ts` · Manual: [MANUAL-USUARIO.md](../../docs/12-roadmap-e-evolucao/my-requests/MANUAL-USUARIO.md)

## UI — kit-first (`@delpi/plugin-ui`)

**Obrigatório:** consumir o remote `@delpi/plugin-ui` via Module Federation. **Proibido** criar botões, cards, tabelas, campos ou banners primitivos no MFE.

| Superfície | Módulo canônico |
|------------|-----------------|
| Factories (PageHeader, SectionCard, TextField, …) | [`src/ui/mrUi.tsx`](src/ui/mrUi.tsx) |
| Contratos DataTable | [`src/ui/mrUiContracts.ts`](src/ui/mrUiContracts.ts) |
| CSS do MFE | Só tokens `--my-requests-*` → `--delpi-ui-*` + layout de página (`index.css`) |
| CSS de componente | **Só** em `plugins/plugin-ui/src/styles/**` |

Anti-padrão (já corrigido): `button`/`table`/`panel` com BEM `dashboard-my-requests__btn|__panel|__table`. Regressão coberta por `src/ui/mrUi.kitFirst.test.ts`.

**Wireframes + catálogo de componentes** (em uso P0 e previstos E7/filtros/upload/modal):  
[docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md)

Diretrizes: `.cursor/rules/plugins-reusable-components.mdc`, `plugins-visual-design-system.mdc`, `plan-construction.mdc`.

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
