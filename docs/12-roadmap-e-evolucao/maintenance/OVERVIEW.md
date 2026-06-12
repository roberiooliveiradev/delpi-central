# Visão geral — Manutenção

**Última atualização:** jun/2026 (Fase 0 — documentação)

## O que é

O módulo **Manutenção** (`id`: `maintenance`) centraliza na **Minha Delpi** processos de manutenção industrial. A **primeira entrega** é **ferramentaria — mini-aplicadores**: registro de trocas de peças, contagem de golpes entre reposições e alertas preventivos.

O produto foi desenhado para **escalar**: novos subdomínios (ordens de serviço, ativos, calendário preventivo, etc.) entram no mesmo plugin e API, sem renomear o id público.

Origem histórica: aplicativo desktop **MiniAplicadores** (WinForms + Access local + leitura TOTVS). A migração web segue o padrão de produtos maduros do monorepo:

- **API própria** (`maintenance-api`) — fonte de verdade do **cadastro operacional** no **PostgreSQL**
- **Plugin MFE** (`plugins/maintenance`) — UI oficial
- **Autenticação** via Keycloak (JWT); **autorização/RBAC** via Core API (`GET /core-api/me`, roles e overrides)
- **Dados TOTVS** (ferramentas, peças, golpes, estoque) via **api-delpi** — sem duplicar queries Protheus na API do plugin

## Pergunta de negócio (mini-aplicadores)

> Quando devo trocar a peça de um mini-aplicador antes que quebre na linha?

O sistema responde cruzando:

1. **Histórico de reposições** (Postgres — ex-Access)
2. **Média de golpes entre trocas** (calculada no Postgres)
3. **Golpes desde a última troca** (TOTVS via api-delpi)
4. **Regras de status** configuráveis (CRÍTICO / ATENÇÃO / OK)

## Componentes

| Peça | Pasta | URL (gateway — alvo) |
|------|-------|----------------------|
| API | `maintenance-api/` (`maint_app`) | `/apps/maintenance-api/` |
| Rotas de negócio | prefixo `/maintenance` | `/apps/maintenance-api/maintenance/*` |
| MFE (UI) | `plugins/maintenance/` | `/apps/maintenance/` |
| Banco operacional | schema `maintenance` em `postgres-plugins` | `PLUGINS_DB_*` |
| TOTVS / Protheus | **api-delpi** | `/apps/api-delpi/engineering/mini-applicators/*` |

### Rotas do MFE (proposta inicial)

| Rota | Função |
|------|--------|
| `/apps/maintenance` | Home — seleção de filial / atalhos |
| `/apps/maintenance/mini-aplicadores` | Lista de ferramentas (TOTVS via API plugin → api-delpi) |
| `/apps/maintenance/mini-aplicadores/{codigo}` | Detalhe: reposições, filtros, CRUD |
| `/apps/maintenance/relatorio` | Últimas reposições + alertas preventivos + gráfico |
| `/apps/maintenance/configuracao` | Motivos e regras de status |

## Fluxo do usuário

```text
Portal Minha Delpi
  → Core API (apps, permissões, menu)
  → Carrega MFE maintenance (Module Federation)
  → JWT no Authorization
  → CRUD reposições / motivos / status → maintenance-api → Postgres
  → Listar ferramentas, golpes, componentes → maintenance-api
        → DelpiApiClient → api-delpi → SQL Server TOTVS
  → UI: cadastro + relatório preventivo por filial
```

## Escopo futuro (mesmo plugin)

O id `maintenance` agrupa **todos** os domínios de manutenção industrial. **Mini-aplicadores** (ferramentaria) é o primeiro submódulo. Backlog: ordens de serviço, ativos, calendário preventivo, CMMS, etc.

## O que não é

- **Não** substitui a api-delpi para leitura TOTVS — queries Protheus vivem **uma vez** na api-delpi.
- **Não** expõe SQL Server ao browser nem ao MFE.
- **Não** mantém Access como fonte de verdade após migração (Postgres canônico).

## Permissões (manifesto — proposta)

| Código | Uso |
|--------|-----|
| `maintenance.view` | Abrir módulo, listagens e relatório |
| `maintenance.replacements.manage` | Criar/editar/excluir reposições |
| `maintenance.reasons.manage` | CRUD motivos de troca |
| `maintenance.status.manage` | Editar percentuais de status preventivo |
| `maintenance.view.filial-01` / `filial-02` | Leitura restrita à filial |
| `maintenance.manage.filial-01` / `filial-02` | CRUD operacional na filial |

## Stack alinhada ao monorepo

| Camada | Escolha |
|--------|---------|
| API | Python 3.11+ / FastAPI (`maint_app`) |
| Domínio | entities, services, ports, gateways |
| Persistência | Postgres + migrations SQL versionadas |
| Integração TOTVS | `shared/delpi_api_client` → api-delpi |
| MFE | React 19 + Vite + Module Federation |
| Design | Tokens do portal — ver regra `plugins-visual-design-system` |
