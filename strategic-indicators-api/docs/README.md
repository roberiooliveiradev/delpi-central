# Documentação — Indicadores Estratégicos (SI)

Documentação técnica do módulo **Strategic Indicators**: API dedicada, MFE e integrações.

## Índice

| Documento | Conteúdo |
|-----------|----------|
| [../README.md](../README.md) | Visão geral do serviço, env, dev local, Docker |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Arquitetura, gateway, fontes de dados, cache |
| [API.md](./API.md) | Rotas HTTP, filtros, permissões, `?include=` |
| [PERFORMANCE_IMPLEMENTATION.md](./PERFORMANCE_IMPLEMENTATION.md) | Plano de performance (fases 0–5), benchmark, env |
| [../migrations/README.md](../migrations/README.md) | Migrations Postgres (`strategic_indicators`) |

## MFE (plugin)

| Recurso | Caminho |
|---------|---------|
| Código | `plugins/strategic-indicators/` |
| Doc do plugin | [plugins/strategic-indicators/README.md](../../plugins/strategic-indicators/README.md) |
| Base URL HTTP | `/apps/strategic-indicators-api/strategic-indicators` (via gateway) |
| Assets | `/apps/strategic-indicators/assets/` |

## Referência legada

O arquivo `api-delpi/docs/api/05-indicadores-estrategicos.md` aponta para esta pasta. As rotas **não** são mais servidas pela api-delpi.

## Swagger

Com a API no ar (dev):

```text
http://localhost/apps/strategic-indicators-api/docs
```

`SI_API_ROOT_PATH=/apps/strategic-indicators-api` — OpenAPI gerado com prefixo correto atrás do Nginx.
