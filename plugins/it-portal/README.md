# Portal de TI (it-portal)

Microfrontend do Portal de TI — Minha DELPI.

- **Plugin id:** `it-portal`
- **Base path:** `/apps/it-portal`
- **BFF:** `it-portal-api` (`/apps/it-portal-api`) — única origem de dados
- **Manifesto:** `it-portal.manifest.json` (importado no Core pelo PO)

## Áreas

| Rota | Área | Permissão de entrada |
|---|---|---|
| `/` | Início — hero imersivo com busca (mesma palette do shell), KPIs clicáveis do inventário, servidores recentes, ações que pedem atenção, Saúde do inventário (% sem criticidade alta/crítica — não é uptime), acesso rápido por permissão e próximas ações | `it-portal.access` |
| `/servers` | Inventário com busca, filtros, ordenação e paginação no servidor | `it-portal.servers.view` |
| `/servers/{id}` | Detalhe: identificação, operação, componentes vinculados, serviços hospedados, bancos associados, redes, integrações dos serviços hospedados, notas, planos de ação, histórico | `it-portal.servers.view` (seções conforme `services.view` / `databases.view` / `networks.view` / `integrations.view`) |
| `/services` | Serviços e aplicações com busca, filtros, ordenação e paginação no servidor | `it-portal.services.view` |
| `/services/{id}` | Detalhe: servidores onde executa, bancos utilizados, integrações, dependências operacionais, histórico | `it-portal.services.view` (integrações conforme `integrations.view`) |
| `/databases` | Instâncias de bancos de dados | `it-portal.databases.view` |
| `/databases/{id}` | Detalhe: servidor hospedeiro, serviços consumidores, histórico | `it-portal.databases.view` |
| `/networks` | Redes (CIDR, VLAN, escopo corporativo ou de containers) | `it-portal.networks.view` |
| `/networks/{id}` | Detalhe: endereçamento, servidores conectados, histórico | `it-portal.networks.view` |
| `/integrations` | Integrações entre serviços e com sistemas externos | `it-portal.integrations.view` |
| `/integrations/{id}` | Detalhe: origem, destino, protocolo, direção, histórico | `it-portal.integrations.view` |
| `/action-plans` | Planos de ação de todos os servidores | `it-portal.actions.view` |
| `/help` | Ajuda | `it-portal.access` |

Os controles exibidos seguem `GET /me/capabilities`; a BFF revalida cada
requisição (escritas com revalidação RBAC sem cache). Monitoramento,
descoberta, varredura de rede, GLPI/Zabbix, mapa visual de dependências,
análise de impacto, notificações e anexos estão fora desta etapa.

## Runtime

- React 19 + Vite 7 + `@originjs/vite-plugin-federation`
- `@delpi/plugin-ui` via remote federado, prefixo `itp`, escopo `.dashboard-it-portal` — visual: `PageHero` variant `immersive`, `MetricKpiCard` acionável, `SemicircleProgressGauge`, `NavigationCard` e `Timeline`; no MFE ficam só tokens `--itp-*` e layout de página
- TanStack Query (somente memória — nenhum dado de inventário em `localStorage`)

## Testes

```bash
npm install
npm test        # vitest (rotas, cliente HTTP, manifesto, páginas)
npm run lint
npm run build   # tsc -b && vite build
```
