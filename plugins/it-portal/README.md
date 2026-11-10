# Portal de TI (it-portal)

Microfrontend do Portal de TI — Minha DELPI.

- **Plugin id:** `it-portal`
- **Base path:** `/apps/it-portal`
- **BFF:** `it-portal-api` (`/apps/it-portal-api`) — única origem de dados
- **Manifesto:** `it-portal.manifest.json` (importado no Core pelo PO)

## Áreas

| Rota | Área | Permissão de entrada |
|---|---|---|
| `/` | Início — KPIs reais do inventário, servidores recentes, ações que pedem atenção | `it-portal.access` |
| `/servers` | Inventário com busca, filtros, ordenação e paginação no servidor | `it-portal.servers.view` |
| `/servers/{id}` | Detalhe: identificação, operação, notas, planos de ação, histórico | `it-portal.servers.view` |
| `/action-plans` | Planos de ação de todos os servidores | `it-portal.actions.view` |
| `/help` | Ajuda | `it-portal.access` |

Os controles exibidos seguem `GET /me/capabilities`; a BFF revalida cada
requisição. Monitoramento, descoberta, GLPI, notificações e anexos estão
fora desta etapa e aparecem apenas como «indisponível».

## Runtime

- React 19 + Vite 7 + `@originjs/vite-plugin-federation`
- `@delpi/plugin-ui` via remote federado, prefixo `itp`, escopo `.dashboard-it-portal`
- TanStack Query (somente memória — nenhum dado de inventário em `localStorage`)

## Testes

```bash
npm install
npm test        # vitest (rotas, cliente HTTP, manifesto, páginas)
npm run lint
npm run build   # tsc -b && vite build
```
