# Documentação — Indicadores Estratégicos (SI)

Documentação técnica oficial do módulo **Strategic Indicators** no monorepo Delpi Central.

## Por onde começar

| Perfil | Documento |
|--------|-----------|
| Novo no módulo | [OVERVIEW.md](./OVERVIEW.md) |
| Backend / API | [API.md](./API.md) + [CODE_STRUCTURE.md](./CODE_STRUCTURE.md) |
| DevOps / infra | [DEPLOYMENT.md](./DEPLOYMENT.md) + [OPERATIONS.md](./OPERATIONS.md) |
| Frontend | [MFE.md](./MFE.md) |
| DBA / migrations | [DATABASE.md](./DATABASE.md) |
| Performance | [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md) |

## Índice completo

| # | Documento | Conteúdo |
|---|-----------|----------|
| 1 | [OVERVIEW.md](./OVERVIEW.md) | Propósito, componentes, conceitos, permissões |
| 2 | [ARCHITECTURE.md](./ARCHITECTURE.md) | Fluxos, cache, filial vs consolidado, metas |
| 3 | [API.md](./API.md) | Referência HTTP (todas as rotas) |
| 4 | [DATABASE.md](./DATABASE.md) | Schema Postgres, migrations |
| 5 | [DATA_SOURCES.md](./DATA_SOURCES.md) | TOTVS, Sheets, Portal RH |
| 6 | [CODE_STRUCTURE.md](./CODE_STRUCTURE.md) | Pacote `si_app`, scripts |
| 7 | [MFE.md](./MFE.md) | Plugin React, manifesto, rótulos de visão, breakpoints, prefetch |
| 8 | [DEVELOPMENT.md](./DEVELOPMENT.md) | Setup local, Docker, bench |
| 9 | [DEPLOYMENT.md](./DEPLOYMENT.md) | Variáveis, gateway, produção |
| 10 | [OPERATIONS.md](./OPERATIONS.md) | Logs, troubleshooting, warm-up |
| 11 | [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md) | Plano de performance (fases 0–5) |
| — | [INDICATOR_GOALS_SCOPE.md](./INDICATOR_GOALS_SCOPE.md) | Metas consolidado / filial 01 / 02 |
| — | [ADMIN_GOALS_AND_CONFIG.md](./ADMIN_GOALS_AND_CONFIG.md) | Modo Padrão/Curva, export/import, ciclos anuais |
| — | [HR_INDICATORS.md](./HR_INDICATORS.md) | Catálogo e fontes RH |
| — | [QUALITY_INDICATORS.md](./QUALITY_INDICATORS.md) | Metas Qualidade por filial |

## Repositórios e paths

| Peça | Caminho |
|------|---------|
| API | [strategic-indicators-api/](../) |
| Migrations | [migrations/](../migrations/) |
| MFE | [plugins/strategic-indicators/](../../plugins/strategic-indicators/) |
| Compose | [infra/docker-compose.dev.yml](../../infra/docker-compose.dev.yml) |
| Env exemplo | [infra/env.strategic-indicators.example](../../infra/env.strategic-indicators.example) |

## URLs (gateway dev)

```text
UI:     http://localhost/apps/strategic-indicators
API:    http://localhost/apps/strategic-indicators-api/strategic-indicators
Docs:   http://localhost/apps/strategic-indicators-api/docs
Health: http://localhost/apps/strategic-indicators-api/health
```

## Legado api-delpi

Rotas SI **não** são mais servidas por `/apps/api-delpi/strategic-indicators`.  
Redirecionamento: [api-delpi/docs/api/05-indicadores-estrategicos.md](../../api-delpi/docs/api/05-indicadores-estrategicos.md).

Dados diretos (ex.: ROL) continuam na api-delpi: `GET /apps/api-delpi/finacial/financial/rol`.
