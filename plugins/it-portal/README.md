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
| `/workstations` | Computadores corporativos com busca, filtros, paginação e cadastro manual | `it-portal.computers.view` |
| `/workstations/{id}` | Ficha do computador, histórico, edição/arquivamento/restauração por permissão | `it-portal.computers.view` (`computers.manage` para escrita) |
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


## Delpi Remote - G1-UI (código preparado, não implantado)

- Rotas internas `/workstations` e `/workstations/{id}` com menu e acesso rápido por `can_view_computers`.
- Inventário manual (sem status online), filtros de unidade, tipo, situação, cadastro e busca; edição e arquivamento conforme `can_manage_computers`.
- Histórico auditado em ficha; formulários exibem erros de validação da BFF; edição versionada por `revision`.
- Não existe botão Conectar, agente nem controle remoto nesta etapa.
- Manifesto estrutural `0.3.4`: nova rota visível no menu interno e permissão `it-portal.computers.view` preservada; registrar via versão estrutural no Core durante deploy, não somente PUT cosmético.
- Testes de UI: `npm test -- --run src/app/routes.test.ts src/features/workstations/WorkstationsPage.test.tsx`, depois `npm run lint && npm run build`. Testes completos e deploy ainda pendentes.
- Plano e evidências: `docs/12-roadmap-e-evolucao/it-portal/delpi-remote/G1-UI.md`.


## Delpi Remote - G1-OWNER (nao implantado)

- Migration V010 adiciona `workstations.responsible_user_id UUID NULL`; coluna `responsible` preserva nome historico, sem FK entre os bancos Core/Portal.
- BFF valida nova atribuicao/troca de responsavel no Core via `POST /me/directory/users/lookup`, usando o JWT do usuario com permissao fresh. Config: `DELPI_AUTH_CORE_API_URL` ja presente no Compose.
- ID inexistente/inativo responde 422, Core indisponivel responde 503, sem gravacao. Alteracoes usam audit_events transacional. Edição com cliente antigo nao apaga o ID atual.
- Rotas e permissoes continuam iguais ao G1; manifesto do MFE permanece 0.3.4.
- Testes a executar antes de deploy: `python -m pytest -q tests/test_workstation_owner.py tests/test_workstations_http.py tests/test_workstations_domain.py`, e em banco descartavel `tests/test_postgres_integration.py`; nunca testar com DSN de producao.
- [Documentacao G1-OWNER](../docs/12-roadmap-e-evolucao/it-portal/delpi-remote/G1-OWNER.md).
