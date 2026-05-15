# 00 — Visão geral, autenticação e convenções

## Propósito

A **api-delpi** expõe dados e métricas do ERP **TOTVS Protheus** (SQL Server) e de bancos **PostgreSQL** de plugins (Indicadores Estratégicos, Qualidade NC), consumidos pelo portal DELPI e plugins federados.

## Base URL

```text
/apps/api-delpi
```

## Prefixos registrados em `app/main.py`

| Prefixo na aplicação | Módulo |
|---|---|
| `/health` | Health global |
| `/strategic-indicators` | Indicadores Estratégicos |
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

Erro (`400` por padrão, configurável):

```json
{
  "success": false,
  "message": "Descrição do erro"
}
```

Implementação: `app/core/responses.py` — `success_response()` e `error_response()`.

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
| `start_date` / `end_date` / `date_start` / `date_end` | Período; formato conforme integração TOTVS (string). |
| `page` / `page_size` | Paginação (limites variam por rota). |
| `competence` | Competência para Indicadores Estratégicos. |

## CORS e compressão

- **CORS**: origens derivadas de `PUBLIC_BASE_URL`, `VITE_KC_URL` e `http://localhost`.
- **GZip**: respostas acima de 1000 bytes.

## Permissões (RBAC)

| Permissão | Escopo |
|---|---|
| `api-delpi.access` | Produtos, vendas, financeiro, comercial, produção, suprimentos. |
| `api-delpi.access.full` | Equivale a acesso total quando combinada com permissões granulares. |
| `api-delpi.system` | Metadados de tabelas. |
| `api-delpi.data` | `POST /data/sql`. |
| `api-delpi.quality.access` | Rotas em `/quality/*`. |
| `quality-nc.view` / `quality-nc.manage` | NC PostgreSQL (rotas preparadas). |
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
app/composition/               → Injeção de dependências (composers)
```

## Execução SQL (`POST /data/sql`)

- Apenas instruções **SELECT** (inclui CTEs recursivas).
- Tabelas referenciadas devem constar em `app/config/allowed_tables.json`.
- Bloqueio de DDL/DML, `EXEC`, transações e palavras-chave perigosas.
- Validador: `app/application/services/sql_validator.py`.

## Deploy e gateway

Nginx encaminha `/apps/api-delpi/` → container `api-delpi:8000/` (path strip). Socket.IO também exposto em `/apps/api-delpi/socket.io/` para eventos em tempo real, se habilitado.
