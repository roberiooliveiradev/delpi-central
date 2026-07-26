# 00 — Visão geral, autenticação e convenções

## Propósito

A **api-delpi** expõe dados e métricas do ERP **TOTVS Protheus** (SQL Server) e de bancos **PostgreSQL** de plugins (Qualidade NC), consumidos pelo portal DELPI e plugins federados. **Indicadores Estratégicos** usam a API dedicada `strategic-indicators-api` (ver [05-indicadores-estrategicos.md](./05-indicadores-estrategicos.md)).

## Base URL

```text
/apps/api-delpi
```

## Prefixos registrados em `app/main.py`

| Prefixo na aplicação | Módulo |
|---|---|
| `/health` | Health global |
| `/finacial` + `/financial` (router) | Financeiro — ver nota do typo |
| `/supplies` | Suprimentos |
| `/commercial` | Comercial |
| `/production` | Produção |
| `/engineering` | Engenharia (LMP, Transforma Mais) |
| `/quality` | Qualidade (métricas TOTVS) |
| `/products` | Produtos |
| `/sales` | Ordens de venda |
| `/system` | Metadados Protheus |
| `/data` | SQL controlado |

## Autenticação

```http
Authorization: Bearer <access_token>
```

Fluxo:

```
Request HTTP
      ↓
jwt_middleware (delpi_auth) — valida JWT Keycloak
      ↓
request.state.user
      ↓
@require_permission / @require_any_permission
      ↓
Use case → repositório (TOTVS / PostgreSQL)
```

Rotas sem decorator ainda passam pelo middleware; endpoints públicos explícitos são apenas os health checks documentados.

## Dois formatos de resposta

### Envelope padrão (produtos, vendas, módulos departamentais, sistema, dados)

Sucesso (`200`):

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": { }
}
```

Erro (`4xx`/`5xx`):

```json
{
  "success": false,
  "message": "Descrição do erro",
  "data": null,
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "recoverable": false
  }
}
```

`error` é opcional em respostas legadas; novas rotas e handlers devem preencher `code` quando possível. HTTP 404 não usa mais `{ "detail": "..." }` solto nas rotas de produto — envelope acima.

Implementação: `app/core/responses.py` — `success_response()`, `error_response()`, `not_found_response()`. Rotas HTTP devem usar `api_delpi_success()` (`app/interface/http/route_response_helpers.py`), que monta `meta` via `ResponseMetaBuilder` e `route_contract_registry.py`. Regra Cursor: `.cursor/rules/api-delpi-response-contract.mdc`.

Sucesso com metadados semânticos (obrigatório em rotas com envelope — Playbook 10):

```json
{
  "success": true,
  "message": "Operação realizada com sucesso",
  "data": { },
  "error": null,
  "meta": {
    "dataVersion": "2026-07",
    "operationId": "get_product_stock",
    "entity": "product_stock",
    "shape": "paged_list"
  }
}
```

**Exceções remanescentes (migração Fase 2):**

| Caso | Formato atual | Prazo |
|------|---------------|-------|
| `GET /products/{code}/structure/excel` erro 500 | `{ "error": "..." }` legado | Migrar para envelope |
| Plugins qualidade NC / rotas sem envelope | JSON direto ou `HTTPException` | Fora do escopo produtos/KPIs |
| Respostas 401/403 do middleware JWT | Corpo do Keycloak / middleware | Não padronizado nesta fase |

Após deploy com mudanças OpenAPI: [12-procedimento-reimport-openapi.md](./12-procedimento-reimport-openapi.md).

### Strategic Indicators e NC (quando montadas)

- Retornam objetos JSON diretamente ou `{"items": [...]}`.
- Erros de validação/negócio: `HTTPException` com `detail` (FastAPI padrão).

```json
{
  "detail": "Mensagem de erro"
}
```

## Códigos HTTP comuns

| Código | Uso |
|---|---|
| `200` | Sucesso com corpo. |
| `201` | Recurso criado (NC, quando ativo). |
| `204` | Remoção sem corpo (ex.: membro de equipe NC). |
| `400` | Validação, SQL inválido, parâmetros incorretos. |
| `401` | Token ausente, inválido ou expirado. |
| `403` | Permissão insuficiente. |
| `404` | Recurso não encontrado (ex.: departamento SI). |
| `500` | Erro interno não tratado. |

## Parâmetros de filtro recorrentes

| Parâmetro | Descrição |
|---|---|
| `branch` | Filial Protheus (geralmente 2 caracteres, ex.: `01`, `02`). |
| `start_date` / `end_date` | **Canônico** para período HTTP (YYYY-MM-DD ou formato TOTVS da rota). |
| `date_start` / `date_end`, `dataInicio` / `dataFim`, … | Aliases **legado** (dual-read); remoção planejada **2027-01**. Preferir o canônico. |
| `issue_date_*`, `modified_*`, `from`/`to` | Nomes **semânticos** — fora da padronização de período genérico. |
| `page` / `page_size` | Paginação (limites variam por rota). |
| `competence` | Competência para Indicadores Estratégicos. |

Gate: `scripts/audit_period_param_pairs.py --report` (inventário); `--check --strict-active` (CI / pós-migração — aliases só com `deprecated=True`). Remoção dos aliases: **2027-01**.

## CORS e compressão

- **CORS**: origens derivadas de `PUBLIC_BASE_URL`, `VITE_KC_URL` e `http://localhost`.
- **GZip**: respostas acima de 1000 bytes.

## Permissões (RBAC)

Constantes para decorators (`@require_permission`, `@require_any_permission`): `app/application/security/api_delpi_permissions.py`. Rotas importam dali — não usar strings literais nos routers.

Consumidores TypeScript (plugins MFE): tipos em `shared/api-delpi-envelope/types.ts`; usar `unwrapApiDelpiEnvelope()` ao ler `data` e validar `success === false`.

| Permissão | Escopo |
|---|---|
| `api-delpi.access` | Produtos, vendas, financeiro, comercial, produção, suprimentos. |
| `api-delpi.access.full` | Equivale a acesso total quando combinada com permissões granulares. |
| `api-delpi.system` | Metadados de tabelas. |
| `api-delpi.data` | `POST /data/sql`. |
| `api-delpi.quality.access` | Rotas em `/quality/*`. |
| `dashboard-lmps.view` | Engenharia LMP (alternativa). |
| `strategic-indicators.view` | Leitura SI. |
| `strategic-indicators.trends.view` | Tendências. |
| `strategic-indicators.settings.manage` | Admin SI. |

Superadmin do Keycloak bypassa verificações conforme política do `delpi_auth`.

## Arquitetura interna (resumo)

```
app/interface/http/routes/     → Controllers FastAPI
app/application/use_cases/     → Casos de uso
app/application/dto/           → Requests/responses tipados
app/domain/ports/              → Interfaces de repositório
app/infrastructure/persistence/  → TOTVS (SQL Server) e PostgreSQL
app/infrastructure/providers/totvs/ → Pool de conexões e acesso ao banco
app/composition/               → Injeção de dependências (composers)
```

## Conexão TOTVS (SQL Server)

### Connection pool

A API usa um pool thread-safe de conexões pyodbc (`app/infrastructure/providers/totvs/connection_pool.py`). Requisições concorrentes reutilizam conexões, reduzindo overhead de abertura/fechamento.

| Variável | Default | Descrição |
|---|---|---|
| `TOTVS_POOL_ENABLED` | `true` | Ativa o pool; `false` cria conexão descartável por request |
| `TOTVS_POOL_MAX_SIZE` | `10` | Máx. conexões simultâneas no pool |
| `TOTVS_CONNECT_TIMEOUT` | `10` | Timeout de abertura de conexão (segundos) |
| `TOTVS_QUERY_TIMEOUT` | `120` | Timeout de execução de query (segundos) |

**Dimensionamento:** o `strategic-indicators-api` faz ~30 requests paralelas durante o snapshot. O pool deve comportar esse burst; se o tamanho for insuficiente, requests em espera recebem `TimeoutError` (→ HTTP 500) após 60s.

### BaseRepository

Classe base para repositórios TOTVS (`app/infrastructure/persistence/totvs/base_repository.py`). Uso como context manager:

```python
with self as repo:
    rows = repo.execute_query(sql, params)
```

Métodos disponíveis:

| Método | Uso |
|---|---|
| `execute_query(sql, params)` | SELECT simples, retorna `list[dict]` |
| `execute_nonquery(sql, params)` | DDL/DML sem retorno (CREATE TABLE, INSERT, DROP) |
| `execute_batch_query(sql, params)` | Batch multi-statement (navega result sets via `cursor.nextset()`) |

### Batch queries (LMP)

As queries de engenharia LMP usam **batch SQL** — um único `cursor.execute()` com múltiplos statements (`SET NOCOUNT ON`, `SELECT INTO #TempTable`, ..., `SET NOCOUNT OFF`, `SELECT final`). Isso é necessário porque o pyodbc usa `sp_executesql` internamente, que escopa temp tables localmente; combinar tudo num batch mantém as temp tables visíveis até o SELECT final.

Implementação: `_build_staged_batch()` em `lmp_query_repository.py`.

## Logging

| Destino | Nível | Configuração |
|---|---|---|
| Arquivo `logs/api_YYYYMMDD.log` | INFO+ | `app/utils/logger.py` |
| stderr (docker logs) | WARNING+ | StreamHandler automático |
| Pool TOTVS (stderr) | WARNING+ | Logger `totvs.pool` |

## Execução SQL (`POST /data/sql`)

- Apenas instruções **SELECT** (inclui CTEs recursivas).
- Tabelas referenciadas devem constar em `app/config/allowed_tables.json`.
- Bloqueio de DDL/DML, `EXEC`, transações e palavras-chave perigosas.
- Validador: `app/application/services/sql_validator.py`.

## Contrato OpenAPI e rotas novas

Toda rota nova deve seguir o padrão canônico (operationId estável, locale EN/pt-BR, enums em `query_param_enums`, labels em JSON, sync TV):

→ **[openapi-bilingue-catalogo-canonico.md](./openapi-bilingue-catalogo-canonico.md)** § *Como construir uma rota futura*

Diretriz Cursor: `.cursor/rules/api-delpi-openapi-route-standards.mdc` + `new-api-route-checklist.mdc`.

## Deploy e gateway

Nginx encaminha `/apps/api-delpi/` → container `api-delpi:8000/` (path strip). Socket.IO também exposto em `/apps/api-delpi/socket.io/` para eventos em tempo real, se habilitado.
