# 07 — Qualidade: Não Conformidades (PostgreSQL)

Módulo de gestão de NC em banco **PostgreSQL** (schema `quality`), separado das consultas analíticas TOTVS em `/quality/*` ([06-modulos-departamentais.md](./06-modulos-departamentais.md)).

## Status de exposição

As rotas estão implementadas em:

- `app/interface/http/routes/internal_nc_routes.py`
- `app/interface/http/routes/external_nc_routes.py`

Porém **ainda não estão registradas** em `app/main.py`. Para ativá-las, incluir algo como:

```python
from app.interface.http.routes import internal_nc_routes, external_nc_routes

app.include_router(
    internal_nc_routes.router,
    prefix="/quality/internal-nc",
    tags=["Qualidade — NC Interna"],
)
app.include_router(
    external_nc_routes.router,
    prefix="/quality/external-nc",
    tags=["Qualidade — NC Externa"],
)
```

**URLs previstas** (após montagem):

```text
/apps/api-delpi/quality/internal-nc/...
/apps/api-delpi/quality/external-nc/...
```

Alinhado ao padrão do monorepo (`docs/11-padroes-de-desenvolvimento/padrao-de-rota.md` e especificações em `documentos/`).

## Permissões

| Permissão | Uso |
|---|---|
| `quality-nc.view` | Leitura de NC, listagens, dashboards. |
| `quality-nc.manage` | Criação, edição, transições, ações, anexos. |

Várias rotas aceitam `@require_any_permission(["quality-nc.view"])` ou combinações com `manage`.

## Formato de resposta

Modelos Pydantic (`response_model=...`) — JSON direto, sem envelope `success`/`data`.

Erros: `HTTPException` com status HTTP apropriado.

---

## NC Interna — prefixo previsto `/quality/internal-nc`

### Não conformidades

| Método | Rota | Permissão | Descrição |
|---|---|---|---|
| POST | `/nonconformities` | manage | Cria NC interna (`201`). |
| GET | `/nonconformities` | view | Lista paginada. |
| GET | `/nonconformities/{nonconformity_id}` | view | Detalhe. |
| PATCH | `/nonconformities/{nonconformity_id}` | manage | Atualiza campos. |
| POST | `/nonconformities/{nonconformity_id}/transition` | manage | Transição de status. |
| GET | `/nonconformities/{nonconformity_id}/full-details` | view | Agregado completo. |

### Causas raiz

| Método | Rota |
|---|---|
| GET | `/nonconformities/{id}/root-causes` |
| POST | `/nonconformities/{id}/root-causes` |

### Ações corretivas

| Método | Rota |
|---|---|
| GET | `/nonconformities/{id}/actions` |
| POST | `/nonconformities/{id}/actions` |
| PATCH | `/actions/{action_id}` |
| POST | `/actions/{action_id}/complete` |

### Eficácia, equipe, comentários, anexos

| Método | Rota |
|---|---|
| GET/POST | `/nonconformities/{id}/effectiveness-checks` |
| GET/POST | `/nonconformities/{id}/team-members` |
| DELETE | `/nonconformities/{id}/team-members/{member_id}` |
| GET/POST | `/nonconformities/{id}/comments` |
| POST | `/nonconformities/{id}/attachments` |
| POST | `/actions/{action_id}/attachments` |

Schemas de request: `app/interface/http/schemas/internal_nc_schemas.py`.

---

## NC Externa — prefixo previsto `/quality/external-nc`

Inclui o mesmo conjunto de recursos da NC interna, mais:

| Método | Rota | Descrição |
|---|---|---|
| POST | `/nonconformities/{id}/supplier-status` | Atualiza status com fornecedor. |
| GET | `/nonconformities/{id}/export` | Exportação do dossiê. |
| GET | `/dashboard/summary` | Resumo do dashboard. |
| GET | `/dashboard/by-supplier` | Agrupado por fornecedor. |
| GET | `/dashboard/by-cause` | Agrupado por causa. |
| GET | `/dashboard/overdue-actions` | Ações em atraso. |
| GET | `/nonconformities/{id}/full-details` | Detalhe completo. |

Schemas: `app/interface/http/schemas/external_nc_schemas.py`.

---

## Migrações

Scripts Flyway-style em `migrations/plugins/quality/` (tabelas `quality.internal_nc_*`, `quality.external_nc_*`, fornecedores, índices e triggers).

---

## Relação com `/quality/nonconformities`

A rota **ativa** `GET /quality/nonconformities` consulta NC no **Protheus** (leitura analítica). O módulo documentado neste arquivo é o **workflow completo** persistido em PostgreSQL para o plugin de qualidade.
