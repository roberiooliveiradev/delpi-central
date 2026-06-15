# Dashboard LMPs

Microfrontend (Module Federation) para **acompanhamento de LMPs** (engenharia), com KPIs, gráficos e tabela alimentados pela **api-delpi** (`/engineering/lmps`).

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| **[docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md)** | Guia completo do plugin |
| [docs/API_MAPPING.md](./docs/API_MAPPING.md) | Endpoints e tipos |
| [docs/TESTING.md](./docs/TESTING.md) | Build, Docker, registro e checklist |
| [docs/STRUCTURE.md](./docs/STRUCTURE.md) | Árvore de pastas |

## Identificação

| Item | Valor |
|------|--------|
| ID | `dashboard-lmps` |
| URL | `/apps/dashboard-lmps` |
| Manifesto | `dash-lmps-microfrontend.manifest.json` |
| Permissão | `dashboard-lmps.view` (ou `api-delpi.access`) |

## API

```text
GET /apps/api-delpi/engineering/lmps/dashboard/summary
GET /apps/api-delpi/engineering/lmps/dashboard/charts
GET /apps/api-delpi/engineering/lmps/dashboard/items
GET /apps/api-delpi/engineering/lmps/{sale_number}
GET /apps/api-delpi/engineering/lmps
```

Detalhe da OV: rota única `get_lmp_by_sale_number` — ver [docs/API_MAPPING.md](./docs/API_MAPPING.md).

## Início rápido

```bash
cd plugins/dashboard-lmps
npm install && npm run build
```

Docker (em `infra/`):

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build \
  gateway core-api dashboard-lmps
```

Testes e registro na Core API: [docs/TESTING.md](./docs/TESTING.md).

## Funcionalidades

- KPIs: % dentro do prazo, lead time médio, total de propostas
- Gráficos: nível, status, lead por nível, evolução temporal
- Tabela detalhada das LMPs filtradas (clique na linha → detalhe da OV)
- Atualização automática a cada 2 minutos (aba visível)
- Fallback de agregação no cliente se `charts` não vier da API

## Referência

Padrão de MFE alinhado a `plugins/dashboard-quality`. Backend: `api-delpi/docs/api/06-modulos-departamentais.md` (Engenharia).
