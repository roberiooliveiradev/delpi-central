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
| `/servers/{id}` | Detalhe: identificação, operação, componentes vinculados, serviços hospedados, bancos associados, notas, planos de ação, histórico | `it-portal.servers.view` (seções E2A conforme `services.view` / `databases.view`) |
| `/services` | Serviços e aplicações com busca, filtros, ordenação e paginação no servidor | `it-portal.services.view` |
| `/services/{id}` | Detalhe: servidores onde executa, bancos utilizados, histórico | `it-portal.services.view` |
| `/databases` | Instâncias de bancos de dados | `it-portal.databases.view` |
| `/databases/{id}` | Detalhe: servidor hospedeiro, serviços consumidores, histórico | `it-portal.databases.view` |
| `/action-plans` | Planos de ação de todos os servidores | `it-portal.actions.view` |
| `/help` | Ajuda | `it-portal.access` |

Os controles exibidos seguem `GET /me/capabilities`; a BFF revalida cada
requisição. Monitoramento, descoberta, GLPI/Zabbix, redes, integrações,
mapa de dependências, notificações e anexos estão fora desta etapa.

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
