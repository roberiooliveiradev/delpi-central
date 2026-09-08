# Minhas Solicitações (MFE)

Microfrontend federado do módulo **Minhas Solicitações**.

- Tile: `/apps/my-requests`
- Rotas internas: `/mine`, `/work-queue`, `/new`, `/requests/:id`, `/admin`
- API: **somente** `/apps/requests-api` (`X-Delpi-Caller-App: my-requests`)
- **Proibido** chamar api-delpi no browser
- Ações no detalhe: render-only de `allowed_actions` (label PT na UI; código canônico na chamada)
- Shell: **TopBar** canônica (`createDashboardTopBar`) + PageHeader contextual — padrão commercial
- Labels PT-BR: [`src/content/presentationLabels.ts`](src/content/presentationLabels.ts)
- Ajuda: [`src/content/helpTooltips.ts`](src/content/helpTooltips.ts) · Manual: [MANUAL-USUARIO.md](../../docs/12-roadmap-e-evolucao/my-requests/MANUAL-USUARIO.md)
- **E19 (Nova por cards):** [PROMPT-nova-solicitacao-type-cards.md](../../docs/12-roadmap-e-evolucao/my-requests/PROMPT-nova-solicitacao-type-cards.md)
- **E20 (TopBar + PT-BR + Ajuda):** [PROMPT-ui-excelencia-topbar-ptbr-help.md](../../docs/12-roadmap-e-evolucao/my-requests/PROMPT-ui-excelencia-topbar-ptbr-help.md)

## UI — kit-first (`@delpi/plugin-ui`)

**Obrigatório:** consumir o remote `@delpi/plugin-ui` via Module Federation. **Proibido** criar botões, cards, tabelas, campos ou banners primitivos no MFE.

| Superfície | Módulo canônico |
|------------|-----------------|
| Factories (TopBar, PageHeader, SectionCard, TextField, …) | [`src/ui/mrUi.tsx`](src/ui/mrUi.tsx) |
| Contratos DataTable | [`src/ui/mrUiContracts.ts`](src/ui/mrUiContracts.ts) |
| CSS do MFE | Só tokens `--my-requests-*` → `--delpi-ui-*` + layout de página (`index.css`) |
| CSS de componente | **Só** em `plugins/plugin-ui/src/styles/**` |

Anti-padrão (já corrigido): `button`/`table`/`panel` com BEM `dashboard-my-requests__btn|__panel|__table`. Regressão coberta por `src/ui/mrUi.kitFirst.test.ts`.

**Wireframes + catálogo de componentes:**  
[docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md](../../docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md)

Diretrizes: `.cursor/rules/plugins-reusable-components.mdc`, `plugins-visual-design-system.mdc`, `plan-construction.mdc`.

## Desenvolvimento

```bash
cd plugins/my-requests
npm install
npm test
npm run typecheck
npm run build
```

Rebuild na stack: `./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui` (só se o kit mudar) e depois `--fase mfe --build my-requests`.

## Manifesto

`my-requests.manifest.json` — registrar na Core API (`POST /core-api/admin/apps/register`).

Roadmap: [PLAYBOOK.md](../../docs/12-roadmap-e-evolucao/my-requests/PLAYBOOK.md).
