# Plugin PAC Qualidade — Planos de Ação

Microfrontend federado para **acompanhamento e gestão** de planos de ação (PAC Qualidade DELPI).

## Arquitetura

| Camada | Responsabilidade |
|--------|------------------|
| **Este plugin (MFE)** | UI: dashboard, listagem, cadastro, detalhe e edição |
| **api-delpi** | **Todas** as chamadas HTTP do plugin — leitura e escrita |
| **api-pac-quality** | Agente GPT (Actions + API key) — mesma base Postgres; **não** usado pelo MFE |
| **PostgreSQL plugins** | Schema `quality.*` — migrations em `api-delpi/migrations/plugins/quality-action-plans/` |

```
Portal → gateway → /apps/api-delpi/quality/action-plans/*
Plugin → /apps/quality-action-plans/* (rotas internas do MFE)
```

## Rotas do plugin (UI)

| Path | Tela |
|------|------|
| `/apps/quality-action-plans` | Resumo executivo (filtro por filial) |
| `/apps/quality-action-plans/lista` | Listagem com filtros + **Novo plano** |
| `/apps/quality-action-plans/novo` | Formulário de criação |
| `/apps/quality-action-plans/atrasados` | Planos com ações vencidas (filtro filial) |
| `/apps/quality-action-plans/plano/{id}` | Detalhe editável: status, Ishikawa, 5 Porquês, ações, eficácia, histórico |
| `/apps/quality-action-plans/recorrencia` | Painel de reincidência |
| `/apps/quality-action-plans/solucoes-testadas` | Padrões de solução |
| `/apps/quality-action-plans/minha-fila` | Ações do usuário logado |

Balões de ajuda (`?`) em campos do detalhe e demais telas: `src/content/helpTooltips.ts`.

**Nota:** vínculos com Kaizen ou Auditoria 5S foram removidos da UI e do modelo (migration V016); integrações futuras usarão tabelas auxiliares.

## API consumida (api-delpi)

Base: `/apps/api-delpi/quality/action-plans`

| Operação | Método | Rota relativa |
|----------|--------|---------------|
| Dashboard | GET | `/dashboard?branch_code=01` |
| Listar | GET | `/?status=&severity=&branch_code=&page_size=` |
| Atrasados | GET | `/overdue?branch_code=` |
| Detalhe | GET | `/{id}` |
| Criar plano | POST | `/` |
| Identificação | PATCH | `/{id}` (status via `/{id}/status`) |
| Status | PATCH | `/{id}/status` |
| Reabrir | POST | `/{id}/reopen` |
| Ishikawa | PUT | `/{id}/ishikawa` |
| 5 Porquês | PUT | `/{id}/five-whys` |
| Criar ações | POST | `/{id}/actions` |
| Atualizar ação | PATCH | `/{id}/actions/{action_id}` |
| Remover ação | DELETE | `/{id}/actions/{action_id}` |
| Eficácia | POST | `/{id}/effectiveness-review` (+ submit/approve/reject) |
| Relatório 8D | PUT | `/{id}/rnc-8d` |
| Export 8D | GET | `/{id}/export/rnc-8d` |
| Evidências | GET/POST/DELETE | `/{id}/evidences` |

Documentação completa: [`api-delpi/docs/api/quality-action-plans-pac.md`](../../api-delpi/docs/api/quality-action-plans-pac.md)

## HTTP client

Todas as chamadas usam:

- `Authorization: Bearer <JWT>`
- `X-Delpi-Caller-App: quality-action-plans`
- Envelope `{ success, message, data }` — ver `src/api/httpClient.ts`

## Permissões RBAC

As permissões são **atribuídas e verificadas pelo core-api** (não diretamente no Keycloak). O portal repassa o JWT; a api-delpi valida os códigos abaixo.

| Código | Uso |
|--------|-----|
| `quality-action-plans.access` | Base do plugin |
| `quality-action-plans.read` | Dashboard, listagem, detalhe |
| `quality-action-plans.write` | Criar/editar planos, Ishikawa, ações, eficácia |
| `quality-action-plans.manage` | Leitura + escrita |
| `api-delpi.quality.action-plans.read` | Leitura via api-delpi (opcional no perfil) |

Atribua **`.read`** para liderança (somente consulta) e **`.write`** ou **`.manage`** para analistas que registram planos — via **core-api** / perfis de aplicação.

## Desenvolvimento local

```bash
cd plugins/quality-action-plans
npm install
npm run dev
```

Build:

```bash
npm run ci
```

Stack DELPI (plugin + api-delpi):

```bash
cd infra
docker compose up -d --build api-delpi quality-action-plans gateway
```

## Registro no Core API

```bash
TOKEN="<jwt-admin>" ./plugins/quality-action-plans/scripts/register-manifest.sh
```

## Migrations

```bash
docker exec delpi-api-delpi python scripts/run_plugins_migrations.py up --plugin quality-action-plans
```

| Versão | Conteúdo resumido |
|--------|-------------------|
| V001–V005 | Core, sequência PAC, knowledge layer, filial, escopo NC |
| V006–V007 | Template RNC 8D, evidências com arquivo, vínculo evidência↔ação |
| V008–V011 | Audit log, notificações, workflow eficácia, pgvector |
| V012–V013 | Vínculos Kaizen/5S (experimentais — revertidos na V016) |
| V014–V015 | Ishikawa e 5 Porquês em JSONB |
| V016 | Remove colunas de vínculo externo; integrações futuras via tabelas auxiliares |

## Documentação relacionada

| Documento | Conteúdo |
|-----------|----------|
| [`api-delpi/docs/api/quality-action-plans-pac.md`](../../api-delpi/docs/api/quality-action-plans-pac.md) | Contrato HTTP api-delpi |
| [`docs/12-roadmap-e-evolucao/quality-action-plans/status-atual.md`](../../docs/12-roadmap-e-evolucao/quality-action-plans/status-atual.md) | Status e débitos |
| [`api-pac-quality/playbook_pac_qualidade_delpi.md`](../../../api-pac-quality/playbook_pac_qualidade_delpi.md) | Playbook do domínio PAC |
| [`api-pac-quality/docs/chatgpt-especialista-qualidade.md`](../../../api-pac-quality/docs/chatgpt-especialista-qualidade.md) | Agente GPT (só API PAC) |
| [`api-pac-quality/README.md`](../../../api-pac-quality/README.md) | API transacional GPT + inteligência |
