# Fase 1 — Fundação Backend (Purchase Requests)

> Implementação inicial do módulo **Solicitações de Compras** conforme [01-contrato-api.md](./01-contrato-api.md).

## Arquitetura

```text
Gateway /apps/purchase-requests-api
        ↓
purchase-requests-api (BFF)
  ├── postgres-plugins / schema purchase_requests
  └── DelpiApiClient → api-delpi /supplies/purchase-requests/lines
                              ↓
                         TOTVS SC1 / SC7 / SD1
```

## Migrations

- Pacote: `purchase-requests-api/migrations/`
- Runner: `purchase_requests_app/infrastructure/persistence/migrations_runner.py`
- Schema: `purchase_requests`
- Tabelas: `visibility_scopes`, `visibility_scope_users`, `visibility_scope_cost_centers`, `user_protheus_mappings`

```bash
cd purchase-requests-api
python -m purchase_requests_app.infrastructure.persistence.migrations_runner status
python -m purchase_requests_app.infrastructure.persistence.migrations_runner up
```

## Endpoints públicos (BFF)

| Método | Path |
|--------|------|
| GET | `/purchase-requests` |
| GET | `/purchase-requests/{branch}/{request_number}` |
| GET/POST | `/purchase-requests/admin/visibility-scopes` |
| GET/PUT | `/purchase-requests/admin/visibility-scopes/{id}` |
| PUT | `/purchase-requests/admin/visibility-scopes/{id}/users` |
| PUT | `/purchase-requests/admin/visibility-scopes/{id}/cost-centers` |
| GET/PUT | `/purchase-requests/admin/user-mappings` |

## Rotas internas api-delpi

| Método | Path |
|--------|------|
| GET | `/supplies/purchase-requests/lines` |
| GET | `/supplies/purchase-requests/lines/{branch}/{request_number}` |

## Permissões

- `purchase-requests.access` — módulo (não bypassa CC)
- `purchase-requests.view-all` — bypass CC dentro da filial autorizada
- `purchase-requests.admin` — CRUD escopos/mappings
- `purchase-requests.unit.filial-01|02` — filial

## Execução local

```bash
./infra/scripts/up-dev-sequential.sh --build purchase-requests-api api-delpi
curl http://localhost/apps/purchase-requests-api/health
```

## Testes

```bash
cd api-delpi && pytest tests/test_purchase_request_lines_sql.py tests/test_purchase_request_lines_routes_smoke.py -q
cd purchase-requests-api && pytest tests/ -q
# shared (DelpiApiClient + health público BFF)
docker run --rm -v ./shared:/shared pr-api-test sh -c 'pip install -q -e /shared[fastapi] && pytest /shared/delpi_auth/tests/test_fastapi_auth_public_paths.py /shared/tests/test_delpi_api_client_query_params.py -q'
```

## Homologação — Fase 1.2 (2026-08-26)

Fechamento da fundação backend no stack dev (sem reset de volumes/bancos).

### Migration V001

| Item | Evidência |
|------|-----------|
| Runner | `migrations_runner status` → `V001 \| create_purchase_requests_schema \| APLICADA` |
| Schema | `purchase_requests` |
| Tabelas | `visibility_scopes`, `visibility_scope_users`, `visibility_scope_cost_centers`, `user_protheus_mappings`, `schema_migrations` |
| PKs/FKs/checks/uniques | Constraints presentes (PK por tabela, FK scope→users/CC, checks filial/CC/mapping_status) |
| Índices | `idx_purchase_requests_*` (active, user, branch+CC, protheus_user parcial) |

### Stack dev

| Serviço | Container | Estado |
|---------|-----------|--------|
| postgres-plugins | `delpi-postgres-plugins` | Up (healthy) |
| api-delpi | `delpi-api-delpi` | Up (healthy) |
| purchase-requests-api | `delpi-purchase-requests-api` | Up (healthy) — Docker healthcheck HTTP `/health` |
| gateway | `delpi-gateway` | Up — dev em `:9080` |

Health HTTP:

- Interno BFF: `GET /health` → 200 `{"status":"online","service":"purchase-requests-api"}`
- Gateway: `GET http://localhost:9080/apps/purchase-requests-api/health` → 200
- Rota autenticada sem JWT: `GET /purchase-requests` → 401 (esperado)

### Paginação (correção crítica)

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Grão api-delpi | linha SC1 (`branch+request_number+request_item`) | cabeçalho SC (`branch+request_number`) |
| `total` / `total_pages` | contagem de linhas | contagem de solicitações SC |
| Fluxo | paginar linhas → BFF agregava página | CC/item → SCs visíveis → paginar SCs → linhas autorizadas → SC7/SD1 batch |

Ordenação default: `request_issue_date DESC`, `request_number DESC`, `branch` (desempate).

Testes adicionados:

- `api-delpi/tests/test_purchase_request_lines_sql.py` — builders de cabeçalho
- `purchase-requests-api/tests/test_header_pagination.py` — casos 1–4 (SC 50 itens = 1 solicitação; CC parcial; total por SC; sem split entre páginas)

Smoke TOTVS filial `02` (jul–ago/2026): `total=1050` SCs; `page_size=2` → 2 SC na página com 4 linhas agregadas.

### Integração

| Trecho | Resultado |
|--------|-----------|
| Gateway → BFF health | 200 em `:9080` |
| BFF → api-delpi | `DelpiApiClient.get_path` + `X-Delpi-Caller-App=purchase-requests-api` + service token → 200, campos reais |
| api-delpi → TOTVS | Leitura SC1/SC7/SD1; joins canônicos preservados |
| Caso âncora (validação adicional) | Filial `02`, SC `164708` → PC `041446` |

Correção SQL em homologação: `ISNULL(a,b,c)` inválido no SQL Server → `COALESCE` para `requester_name`.

### OpenAPI / gates (api-delpi)

| Gate | Resultado |
|------|-----------|
| `audit_openapi_operation_ids.py --check` | OK |
| Smoke meta | `test_purchase_request_lines_routes_smoke.py` — `list_supplies_purchase_request_lines`, `get_supplies_purchase_request_lines` |
| `route_contract_registry` | Entradas `paged_list` / `list` registradas |
| Permissões api-delpi | `PURCHASE_REQUESTS_*` + gate filial |

### RBAC Core API

**Cenário B:** permissões de plugin (`purchase-requests.access`, `.admin`, `.view-all`, `.export`, `.unit.filial-01|02`) **aguardam registro do manifesto na Fase do MFE** via `UpdatePluginManifestUseCase` — Core API não faz seed manual de permissões de plugin.

Nomenclatura filial alinhada à convenção vigente: `purchase-requests.unit.filial-01` / `filial-02`.

### Testes finais (Fase 1.2)

| Pacote | Passed | Observação |
|--------|--------|------------|
| api-delpi | 12 | SQL + smoke rotas |
| purchase-requests-api | 29 | domínio, segurança, paginação cabeçalho |
| shared | 5 | DelpiApiClient query params + health público BFF |

### Problemas encontrados e correções

1. Paginação por linha dividia SC entre páginas → paginação por cabeçalho SC na api-delpi.
2. Health BFF retornava 401 no gateway → path público `/apps/*/health` em `fastapi_auth`.
3. SQL Server `ISNULL` com 3 argumentos → `COALESCE`.
4. Gateway WSL mount → recreate container.
5. Healthcheck Docker ausente em prod → adicionado em `docker-compose.yml`.

## Pendências (fora desta fase)

- MFE / manifesto (provisionamento RBAC no Core)
- `/purchase-requests/filters` e `/indicators`
- Validação administrativa de CC via api-delpi
- `mine=true` e job de mapping automático
- Smoke JWT ponta a ponta Gateway → `/purchase-requests` (requer permissões provisionadas no manifesto)
