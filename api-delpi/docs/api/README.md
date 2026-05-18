# API DELPI — Documentação da API

Documentação técnica em Markdown da **api-delpi**, API REST FastAPI para integração com o **TOTVS Protheus** e módulos analíticos do ecossistema DELPI Central.

## Base URL

Em produção e desenvolvimento, o portal e os plugins consomem a API pelo gateway:

```text
/apps/api-delpi
```

Exemplos:

```text
GET  /apps/api-delpi/health
GET  /apps/api-delpi/products/search?code=010101
GET  /apps/strategic-indicators-api/strategic-indicators/executive-summary
POST /apps/api-delpi/data/sql
```

A aplicação define `root_path="/apps/api-delpi"` para geração correta do OpenAPI/Swagger atrás do proxy reverso.

## Documentação interativa

| Recurso | URL (via gateway) |
|---|---|
| Swagger UI customizado | `/apps/api-delpi/docs` |
| OpenAPI JSON | `/apps/api-delpi/openapi.json` |

O Swagger aceita token JWT via `postMessage` (`DELPI_AUTH`) a partir do portal, com refresh automático em respostas `401`.

## Autenticação

A maioria dos endpoints exige:

```http
Authorization: Bearer <access_token>
```

O middleware `jwt_middleware` (pacote `delpi_auth`) valida o JWT emitido pelo Keycloak e popula `request.state.user`. Decorators `@require_permission` e `@require_any_permission` aplicam RBAC por rota.

## Arquivos deste pacote

| Arquivo | Conteúdo |
|---|---|
| [00-visao-geral.md](./00-visao-geral.md) | Convenções, autenticação, formato de resposta, permissões e arquitetura. |
| [01-health.md](./01-health.md) | Health checks globais e do módulo Strategic Indicators. |
| [02-produtos.md](./02-produtos.md) | Busca, estrutura, estoque, NF-es, vendas e analisador de produto. |
| [03-vendas.md](./03-vendas.md) | Listagem de ordens de venda. |
| [04-sistema-e-dados.md](./04-sistema-e-dados.md) | Metadados Protheus (SX2/SX3/SIX/SX9) e execução SQL controlada. |
| [05-indicadores-estrategicos.md](./05-indicadores-estrategicos.md) | Redirecionamento → API dedicada SI ([doc oficial](../../strategic-indicators-api/docs/README.md)). |
| [06-modulos-departamentais.md](./06-modulos-departamentais.md) | Financeiro, comercial, produção, suprimentos, engenharia e qualidade (métricas). |
| [07-qualidade-nc.md](./07-qualidade-nc.md) | NC interna/externa (implementado, **ainda não montado** em `main.py`). |
| [10-referencia-rapida-endpoints.md](./10-referencia-rapida-endpoints.md) | Tabela consolidada de todos os endpoints ativos. |

## Permissões principais

| Permissão | Finalidade |
|---|---|
| `api-delpi.access` | Acesso padrão a produtos, vendas e módulos departamentais gerais. |
| `api-delpi.access.full` | Acesso ampliado (sistema + dados SQL). |
| `api-delpi.system` | Consulta de metadados de tabelas Protheus. |
| `api-delpi.data` | Execução de SQL somente leitura (`POST /data/sql`). |
| `api-delpi.quality.access` | Métricas de qualidade (PPM, kaizen, 5S, NC listagem TOTVS). |
| `quality-nc.view` | Leitura de não conformidades (módulo PostgreSQL). |
| `quality-nc.manage` | Gestão de NC (criação, transições, ações). |
| `dashboard-lmps.view` | LMPs e Transforma Mais (alternativa a `api-delpi.access`). |
| `strategic-indicators.view` | Leitura do plugin Indicadores Estratégicos. |
| `strategic-indicators.trends.view` | Tendências históricas. |
| `strategic-indicators.settings.manage` | Configurações, metas, departamentos e change requests. |

## Stack e integrações

| Componente | Uso |
|---|---|
| **FastAPI** | Framework HTTP, OpenAPI, validação Pydantic. |
| **SQL Server (Protheus)** | Consultas operacionais (produtos, vendas, métricas). |
| **PostgreSQL** | Plugins (`quality` NC); schema `strategic_indicators` via **strategic-indicators-api**. |
| **delpi_auth** | JWT + decorators de permissão. |
| **Nginx (gateway)** | Proxy em `/apps/api-delpi/`. |

## Observações importantes

- O prefixo financeiro em `main.py` está registrado como `/finacial` (typo). Os endpoints reais são `/finacial/financial/*` — ver [06-modulos-departamentais.md](./06-modulos-departamentais.md).
- Rotas `internal_nc_routes` e `external_nc_routes` existem no código mas **não** estão incluídas em `app/main.py` até o momento.
- Respostas da maioria dos módulos legados usam envelope `{ success, message, data }`; Strategic Indicators e NC usam JSON direto ou `HTTPException`.
