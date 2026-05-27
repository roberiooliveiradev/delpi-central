# Minha DELPI — Visão geral da API DELPI

> **Arquivo:** `docs/07-api-delpi/visao-geral-api-delpi.md`  
> **Status:** documentação oficial  
> **Código:** `api-delpi/`  
> **Documentação completa de rotas:** [api-delpi/docs/api/README.md](../../api-delpi/docs/api/README.md)

---

## 1. Papel

Backend **FastAPI** para dados operacionais e integração **TOTVS Protheus** (SQL Server), além de módulos em **PostgreSQL** (qualidade NC). **Indicadores Estratégicos** têm API dedicada (`strategic-indicators-api`).

```text
Core API     → governança (usuários, apps, RBAC)
API DELPI    → negócio, TOTVS, métricas, produtos
```

---

## 2. Exposição

| Item | Valor |
|---|---|
| Gateway | `/apps/api-delpi/` |
| `root_path` FastAPI | `/apps/api-delpi` |
| Swagger | `/apps/api-delpi/docs` |
| Health | `GET /apps/api-delpi/health` |

Autenticação: `Authorization: Bearer <JWT>` via `delpi_auth` (mesmo Keycloak da plataforma).

---

## 3. Módulos HTTP (resumo)

| Prefixo | Conteúdo |
|---|---|
| `/products` | Produtos, estrutura, estoque, NF-es |
| `/sales` | Ordens de venda |
| `/system` | Metadados Protheus (SX2/SX3/…) |
| `/data` | SQL somente leitura controlado |
| *(movido)* | Indicadores Estratégicos → `/apps/strategic-indicators-api/strategic-indicators` ([doc](../../strategic-indicators-api/docs/README.md)) |
| `/engineering` | LMPs, Transforma Mais |
| `/quality` | Métricas qualidade (TOTVS) |
| `/commercial`, `/production`, `/supplies`, `/hr` | KPIs departamentais |
| `/financial` e `/finacial` | Financeiro (montagem dupla em `main.py`; preferir `/financial/*`) |

**NC PostgreSQL** (`internal_nc_routes`, `external_nc_routes`): implementadas, **ainda não montadas** em `main.py` — ver [07-qualidade-nc.md](../../api-delpi/docs/api/07-qualidade-nc.md).

---

## 4. Formato de resposta

Maioria dos endpoints legados:

```json
{ "success": true, "message": "...", "data": { } }
```

Strategic Indicators: JSON direto / `HTTPException`.

---

## 5. Permissões frequentes

| Permissão | Uso |
|---|---|
| `api-delpi.access` | Produtos, vendas, KPIs gerais |
| `api-delpi.access.full` | Acesso ampliado |
| `api-delpi.system` / `api-delpi.data` | Sistema + SQL |
| `api-delpi.quality.access` | `/quality/*` |
| `strategic-indicators.*` | Módulo SI |
| `dash-lmps.access` | Plugin LMPs (manifesto iframe) |
| `dashboard-lmps.view` | Legado — preferir `dash-lmps.access` |

Cadastradas na Core API via manifestos de plugin ou seed.

---

## 6. Bancos

| Banco | Uso |
|---|---|
| SQL Server | Protheus / TOTVS |
| PostgreSQL (`postgres-plugins`) | strategic-indicators, quality NC, etc. |

Migrações de plugins: `api-delpi/migrations/plugins/`.

---

## 7. Consumo no Portal

- Plugins chamam `/apps/api-delpi/...` com token do usuário.
- Páginas nativas do shell: `portal/src/data/delpiApi.ts`, rotas `/delpi/products`, `/delpi/health`.

---

## 8. Leitura recomendada

1. [api-delpi/docs/api/00-visao-geral.md](../../api-delpi/docs/api/00-visao-geral.md)
2. [api-delpi/docs/api/10-referencia-rapida-endpoints.md](../../api-delpi/docs/api/10-referencia-rapida-endpoints.md)
3. [api-delpi/docs/api/11-guia-agente-chat.md](../../api-delpi/docs/api/11-guia-agente-chat.md) — agentes Minha DELPI Chat
4. [minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md](../../minha-delpi-ai-api/docs/knowledge/api-delpi-rotas-agente.md) — documento RAG expandido
5. [../04-core-api/visao-geral-core-api.md](../04-core-api/visao-geral-core-api.md)
