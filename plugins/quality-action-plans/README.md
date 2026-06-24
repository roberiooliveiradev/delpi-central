# Plugin PAC Qualidade — Planos de Ação

Microfrontend federado para **acompanhamento de planos de ação** (PAC Qualidade DELPI) pela liderança.

| Camada | Responsabilidade |
|--------|------------------|
| **Este plugin** | Dashboard, listagem, cadastro e edição PAC |
| **api-delpi** | `GET/POST/PATCH/PUT /quality/action-plans/*` |
| **api-pac-quality** | Agente GPT (Actions + API key) — mesma base Postgres |

## Rotas internas

| Path | Tela |
|------|------|
| `/apps/quality-action-plans` | Resumo executivo |
| `/apps/quality-action-plans/lista` | Listagem com filtros |
| `/apps/quality-action-plans/atrasados` | Planos com ações vencidas |
| `/apps/quality-action-plans/plano/{id}` | Detalhe (Ishikawa, 5 Porquês, ações, histórico) |

## Desenvolvimento local

```bash
cd plugins/quality-action-plans
npm install
npm run dev
```

Build de produção:

```bash
npm run ci
```

## Deploy (stack DELPI)

O serviço `quality-action-plans` está no `infra/docker-compose.yml`. Após build:

```bash
cd infra
docker compose up -d --build quality-action-plans
```

## Registro no Core API

```bash
TOKEN="<jwt-admin>" ./plugins/quality-action-plans/scripts/register-manifest.sh
```

Permissões: `quality-action-plans.access`, `.read`, `.write`, `.manage`.

Atribua `quality-action-plans.read` (e `api-delpi.quality.action-plans.read` se usada no perfil) aos usuários de liderança/qualidade.

## HTTP client

Todas as chamadas usam:

- `Authorization: Bearer <JWT>`
- `X-Delpi-Caller-App: quality-action-plans`
- Base: `/apps/api-delpi/quality/action-plans`

## Documentação relacionada

- Playbook: `api-pac-quality/playbook_pac_qualidade_delpi.md`
- Agente GPT: `api-pac-quality/docs/chatgpt-especialista-qualidade.md`
- Migrations: `api-delpi/migrations/plugins/quality-action-plans/`
