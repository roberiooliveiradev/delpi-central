# Dashboard Qualidade

Microfrontend (Module Federation) para visualização de **métricas de qualidade** expostas pela **api-delpi** (dados TOTVS / Protheus).

## Documentação principal

**[docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md)** — visão geral, rotas, filtros, impressão, permissões, deploy e estrutura.

| Arquivo | Conteúdo |
|---------|----------|
| [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md) | Guia completo do plugin |
| [docs/API_MAPPING.md](./docs/API_MAPPING.md) | Rotas api-delpi consumidas |
| [docs/TESTING.md](./docs/TESTING.md) | Build, Docker, registro Core API e checklist |
| [docs/ROADMAP.md](./docs/ROADMAP.md) | Fases de desenvolvimento |
| [docs/IMPROVEMENTS_ROADMAP.md](./docs/IMPROVEMENTS_ROADMAP.md) | Ondas de melhorias (UX, performance) |
| [docs/STRUCTURE.md](./docs/STRUCTURE.md) | Árvore de pastas e convenções |

## Escopo

| Incluído | Excluído |
|----------|----------|
| PPM interno/externo (resumo, série, comparativo) | Workflow de NC em PostgreSQL (removido da api-delpi) |
| Kaizens e auditoria 5S (resumo) | Cadastro/workflow de NC fora do TOTVS |
| NC analítica Protheus (`/quality/nonconformities`) | Indicadores estratégicos (outra API) |

## Rotas

| URL | Módulo |
|-----|--------|
| `/apps/dashboard-quality` | Visão geral |
| `/apps/dashboard-quality/ppm` | PPM |
| `/apps/dashboard-quality/nonconformities` | NC TOTVS |
| `/apps/dashboard-quality/kaizen` | Kaizens |
| `/apps/dashboard-quality/audit-5s` | Auditoria 5S |

## Backend

```text
/apps/api-delpi/quality/*
```

Permissões: `dashboard-quality.view` ou `api-delpi.quality.access`.

## Início rápido

```bash
cd plugins/dashboard-quality
npm install && npm run ci
```

Monorepo: `./scripts/ci/build-dashboard-quality.sh`  
Testes: [docs/TESTING.md](./docs/TESTING.md)

## Status

Fases 0–5 e ondas de melhorias 1–5 concluídas (exceto NC PostgreSQL — produto separado).  
Filtros persistentes entre abas (URL + sessionStorage) e impressão com layout dedicado.
