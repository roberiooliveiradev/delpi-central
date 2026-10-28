# F2a — Engineering Home: Inventário, Contrato e Implementação

Ledger de execução da primeira rota de negócio da `engineering-api`:
`GET /v1/home` — composição autorizada da página Início do Portal
Engenharia. Baseline: F1-FINAL (`7a95095ccc`), reancoragem em
`6350355338` (origin/main no início da F2a).

---

## 1. F2a.G0 — Inventário das fontes oficiais

Verificação por leitura de código/contrato — nenhuma fonte foi
inferida por existência de arquivo, tela ou use case.

| Seção | Owner | Endpoint oficial | AuthZ downstream | Contrato | Status |
|---|---|---|---|---|---|
| `tasks` | `requests-api` (Minhas Solicitações) | `GET /requests/work-queue` | escopo server-side por usuário; acesso ao módulo `my-requests.*` verificado no use case (403 se ausente) | `{"success","data":{"items":[serialize_request],"total","page","page_size"}}` — item: `id, request_number, type_code, status, status_alias, priority, branch_code, created_at, updated_at, allowed_actions` | `PROVEN` |
| `requests` | `requests-api` | `GET /requests/mine` | idem — apenas solicitações criadas pelo usuário | idem | `PROVEN` |
| `lmps` | `api-delpi` (TOTVS) | `GET /engineering/lmps` | `@require_any_permission(ENGINEERING_LMP_ACCESS)` → 403 sem permissão | `api_delpi_success` → `{"success","data":{"items":[LMP],"total","total_pages"},"meta":{"operationId":"list_lmps"}}` — item: `sale_number, sale_description, engineering_status, branch, start_date, end_date, reference_revision, measurement_revision, costumer_name` | `PROVEN` |
| `attention` | — | — | — | sem fonte dedicada comprovada | `no_official_source` |
| `activity` | — | — | — | sem fonte dedicada comprovada | `no_official_source` |
| `collaboration` | — | — | — | ADR-004 (salas) pendente de decisão funcional; sem backend oficial de Engenharia | `not_implemented` |

Fontes avaliadas e **não elegíveis** na F2a:

- `strategic-indicators-api` — métricas de engenharia existem
  (`engineering_metrics_helpers.py`) mas não há endpoint HTTP público
  user-scoped comprovado para a Home; consumo atual é interno via
  api-delpi/dashboard. `TO_INVENTORY` para fase futura.
- `commercial-api` (interaction rooms) — proibida como provider do
  Engineering por decisão documental; apenas referência de protocolo.
- `transformometro-api` — consumida **pela api-delpi** (composer);
  a Home lê LMPs/séries via api-delpi, nunca diretamente.
- Core `/me` — já consumida por `delpi_auth` para AuthZ efetiva
  (não é fonte de dados de negócio).

### Mecanismo oficial de delegação (G3)

Canônico, igual a supplies/comercial/`delpi_api_client`:
`Authorization: Bearer <JWT do usuário>` + `X-Delpi-Caller-App:
engineering-api` + `apply_internal_service_headers` (service token
interno quando configurado — complementa, não substitui, a autorização
do usuário) + `X-Request-Id` propagado. Mesma audiência/issuer; o owner
downstream revalida identidade e autorização do recurso.

**Sem service token privilegiado como bypass**: se o usuário não tem
acesso a LMP (`ENGINEERING_LMP_ACCESS` na api-delpi) ou ao módulo
`my-requests` (na requests-api), a seção retorna `forbidden` — nunca
dados.

### Gaps de autoridade registrados

- `attention`: não existe fonte oficial dedicada de "itens que exigem
  atenção" — exige decisão funcional (quais regras o owner aplicaria).
- `activity`: não existe feed oficial de atividade de engenharia.
- `collaboration`: ADR-004 pendente.
- Escopo de unidade/filial: `requests-api` aplica escopo por usuário
  internamente; api-delpi aceita `branch` opcional — a Home **não**
  filtra por unidade porque o contrato de unidades do usuário pertence
  à Core/`/me` e não foi materializado na F2a. Dado exibido = o que o
  owner autorizou para o usuário.

---

## 2. F2a.S1 — Contrato HTTP

`GET /v1/home` (gateway futuro: `GET /apps/engineering-api/v1/home`)
`operationId: get_engineering_home`

Envelope canônico: `{"success","message","data","meta":{"operationId"}}`.

`data` (schema_version `1.0`):

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-10-28T12:00:00+00:00",
  "status": "partial",
  "sections": {
    "attention":     {"status": "unavailable", "reason": "no_official_source", "items": []},
    "tasks":         {"status": "available", "source": {"system": "requests-api", "endpoint": "GET /requests/work-queue"}, "items": [...], "total": 3},
    "lmps":          {"status": "forbidden", "items": []},
    "requests":      {"status": "empty", "items": [], "total": 0},
    "activity":      {"status": "unavailable", "reason": "no_official_source", "items": []},
    "collaboration": {"status": "not_implemented", "items": []}
  }
}
```

### Estados de seção

| Estado | Semântica |
|---|---|
| `available` | fonte respondeu com itens |
| `empty` | fonte respondeu sucesso com zero itens (ausência legítima) |
| `unavailable` | timeout / transporte / 5xx / contrato incompatível / sem fonte |
| `forbidden` | owner downstream negou acesso ao usuário (401/403 downstream) |
| `not_implemented` | seção prevista sem backend oficial — nunca finge dados |

`reason` (opcional, machine-readable): `timeout`, `transport_error`,
`upstream_error`, `contract_error`, `no_official_source`.

### Status agregado

Calculado **somente** sobre fontes elegíveis (`tasks`, `requests`,
`lmps`): `available` (todas responderam), `partial` (misto),
`unavailable` (nenhuma utilizável). Seções estáticas
(`no_official_source`/`not_implemented`) não entram no cálculo.

### HomeItem

`{id, kind, title, status, status_label, date, href, source, meta}`

- `kind`: `task` | `request` | `lmp`
- `status`/`status_label`: valores oficiais do owner, sem tradução
- `href`: rota existente no Portal (`/apps/my-requests`,
  `/apps/dashboard-lmps`) — sem deep-links inventados
- `meta`: whitelist de campos do owner (`request_number`, `type_code`,
  `priority`, `branch_code`, `allowed_actions`; `sale_number`, `branch`,
  `costumer_name`, `reference_revision`, `measurement_revision`,
  `start_date`, `end_date`)

### Política de evolução (F3+)

Compatibilidade **aditiva**: novos campos/seções podem entrar sem bump;
mudanças de semântica/estados exigem nova `schema_version`. Frontend
deve ignorar campos desconhecidos.

---

## 3. F2a.S2 — Adapters (Clean Architecture)

```text
interface/http/routes/home_routes.py
    ↓ resolve_user_context + principal_type=="user" + @require_any_permission
application/use_cases/get_engineering_home.py   (sem FastAPI/httpx)
    ↓ HomeSectionSource (Protocol)
infrastructure/gateways/{requests_api,api_delpi}_gateway.py
    ↓ DownstreamClient (httpx async, timeout explícito, sem retry)
APIs oficiais (requests-api, api-delpi)
```

- `DownstreamClient` reutiliza `delpi_api_client.envelope.parse_envelope`
  e `format_error_message` (fonte canônica do envelope) e
  `delpi_auth.service_token.apply_internal_service_headers`.
- Zero retries no BFF (não repetir chamadas indiscriminadamente).
- Erros classificados: `timeout`, `transport_error`, `http` (→
  `upstream_error` ou `forbidden` em 401/403), `contract_error`.

## 4. F2a.S3 — Caso de uso

`GetEngineeringHome`: fan-out com `asyncio.gather` sobre as 3 fontes
elegíveis, `asyncio.Semaphore(HOME_MAX_CONCURRENT_SOURCES=3)` e
`asyncio.wait_for` por fonte (`HOME_SOURCE_TIMEOUT_SECONDS=5.0`).
Limite por seção `HOME_MAX_SECTION_ITEMS=10` propagado como `page_size`
ao owner (nunca coleção completa truncada no BFF).

## 5. F2a.S4 — AuthN/AuthZ

- Keycloak JWT via `delpi_auth` (inalterado).
- `require_any_permission(["engineering.access"])` — **permissão ainda
  não registrada na Core** → 403 fail-closed até registro pelo manifest
  oficial. Nenhum fallback por claims/grupo/papel local.
- `principal_type == "user"` obrigatório — service principal → 403.
- `rbac_unavailable` → 503 (semântica canônica do shared).

## 6. F2a.S5 — Testes (156 no total)

Novos: `tests/test_home.py` (20) + `tests/test_home_gateways.py` (8).

- AuthN: sem JWT, JWT inválido, assinatura errada → 401.
- AuthZ: sem `engineering.access` → 403; permissão irmã → 403; Core
  indisponível → 503; claims forjados não concedem acesso; service
  principal → 403.
- Contrato: schema, estados, provenance, OpenAPI (`operationId`).
- Resiliência: falha parcial (partial), todas falham (unavailable),
  timeout por fonte, erro inesperado, fan-out limitado (semáforo=1 →
  máximo in-flight 1), isolamento de usuários, propagação de
  `X-Request-Id` e delegação do Bearer do usuário.
- Adapters (MockTransport): normalização de itens, headers de
  delegação, mapeamento 403→forbidden, 5xx→unavailable,
  ConnectTimeout→timeout, envelope incompatível→contract_error.
- Guards atualizados: `domain/` proibido (BFF); superfície OpenAPI
  = health/ready + `/v1/home`.

## 7. Ativação (G5)

`engineering.access` **não está registrada** na Core →
`PENDING_AUTHORITY_REGISTRATION`. A rota está implementada, testada e
publicada de forma segura: sem a permissão efetiva todo request
recebe 403. Nenhum manifest, grant ou bypass ad-hoc foi criado.

## 8. Residuais

- Seções `attention`/`activity`/`collaboration` aguardam fontes/decisões.
- Indicadores (si-api): `TO_INVENTORY` para fase futura.
- Filtro de unidade/filial: hoje delegado integralmente aos owners.
- `engineering.access` pending — ver §7.

## 9. Próximo bounded step

F2b ou manifest/permission registration (coordenação EVA) — o que vier
primeiro sob autorização. F3 (`plugins/engineering`) não iniciada.

---

## F2a.R1 — Security Rework / Human Identity Downstream Delegation

### Achado e causa raiz

O `DownstreamClient` aplicava `apply_internal_service_headers(headers)`
em **todas** as chamadas personalizadas. Com
`API_DELPI_INTERNAL_SERVICE_TOKEN` configurado no serviço (presente no
Compose), isso injetava `X-Delpi-Service-Token` em cada leitura da Home.

No middleware compartilhado (`delpi_auth.middleware.fastapi_auth`),
`request_has_valid_internal_service_token(request)` é avaliado **antes**
da validação do JWT humano. Token interno válido short-circuita o fluxo
e estabelece `principal_type="service"` + `is_superadmin=True` —
o Bearer humano nunca é validado. Como `requests-api` e `api-delpi`
delegam ao mesmo `_base_jwt_middleware` nas rotas de dados
(`requests_app/middleware/auth_middleware.py`,
`app/middleware/auth_middleware.py`), a precedência é idêntica nos dois
owners.

Impacto anterior: toda leitura da Home era processada pelo owner como
**service principal superadmin** — em `api-delpi` o `is_superadmin`
bypassa `require_any_permission(ENGINEERING_LMP_ACCESS)` e o
user-scoping; em `requests-api` a identidade efetiva era
`internal-service`, não o usuário. As seções `forbidden` por recurso
nunca se materializavam. O smoke fail-closed na entrada (401/403 por
`engineering.access`) não detectava o problema porque a elevação
ocorria depois da AuthZ da Home.

### Fluxo anterior → fluxo corrigido

```text
ANTES: Bearer humano + X-Delpi-Service-Token
       → owner: service token válido → principal service/superadmin
       → autorização por recurso e user-scoping ignorados

DEPOIS: Bearer humano somente (+ X-Delpi-Caller-App, X-Request-Id)
        → owner: valida JWT → Core /me → principal user → AuthZ recurso
        → 401/403 do owner → seção forbidden; falha → unavailable
```

`X-Delpi-Caller-App` é identificação de consumidor, nunca autorização.
`X-Request-Id` continua propagado. Sem fallback: identidade humana
inválida produz `forbidden`/`unavailable` — nunca troca por token
privilegiado.

### Contratos reais dos owners

Ambos aceitam o JWT humano diretamente — é o mesmo fluxo das chamadas
do Portal (browser) a `/requests/*` e `/engineering/lmps`: validação
JWKS Keycloak → resolução RBAC via Core `/me` → AuthZ de recurso do
endpoint → user-scoping server-side do owner. Nenhum endpoint consumido
pela Home exige credencial de serviço; o contrato distingue superfícies
S2S (`api-delpi` `/integrations/*`, que validam o token interno no
handler) das superfícies de usuário — a Home só consome estas últimas.

### Correção implementada (menor diff)

`engineering-api/engineering_app/infrastructure/gateways/downstream_client.py`
— removidos o import e a chamada de `apply_internal_service_headers`;
docstring passa a documentar o contrato de delegação humana e a
proibição do token interno em chamadas personalizadas. Nenhuma mudança
transversal: `delpi_auth`, requests-api e api-delpi não foram
modificados — a precedência interna do shared permanece correta para
suas superfícies S2S legítimas.

### Testes com token interno configurado

Com `API_DELPI_INTERNAL_SERVICE_TOKEN=svc-internal-test` (sintético):

- `test_adapters_never_send_internal_service_token` — os 3 adapters
  (work-queue, mine, lmps) enviam somente Bearer do usuário +
  Caller-App + Request-Id; `X-Delpi-Service-Token` ausente.
- `test_work_queue_maps_items_and_delegation` — agora executa com o
  token configurado e afirma a ausência do header.
- `test_client_reaches_owner_as_user_principal_with_service_token_configured`
  — `DownstreamClient` → `ASGITransport` → middleware REAL
  `delpi_auth.jwt_middleware` → `resolve_user_context()` devolve
  `principal_type="user"`, `is_superadmin=False`, com JWT válido e
  token interno configurado no ambiente.
- `test_service_token_would_elevate_but_client_never_sends_it` —
  controle negativo: enviando `X-Delpi-Service-Token` manualmente ao
  mesmo middleware real, o principal vira `service`/`is_superadmin=True`
  (comprova a superfície de risco); o cliente corrigido não o envia.
- `test_requests_401_maps_to_forbidden_without_fallback` — 401 do owner
  → seção `forbidden`, sem dados e sem fallback.

`test_home_service_principal_denied` (F2a) permanece: service token na
ENTRADA da Home continua → 403.

### Compatibilidade, limitações e ativação

- `engineering.access` continua governada pela Core; nenhum registro
  ad-hoc. Ativação funcional permanece `PENDING_AUTHORITY_REGISTRATION`.
- Limitação: a precedência `service-token > JWT` do shared é
  comportamento vigente da plataforma — qualquer futuro cliente que
  reaplique `apply_internal_service_headers` em chamada personalizada
  reintroduz o risco; o docstring + residual search + testes de
  isolamento são o guardrail local. Um hardening transversal (ex.:
  owner recusar ambos os headers em superfícies de usuário) é decisão
  arquitetural da plataforma, fora do escopo R1.
- Evidências: suite 160/160 (128 F1 + 9→13 gateway tests + novos);
  audits `audit_backend_boundaries`, `audit_fastapi_authz`,
  `audit_openapi_contracts`, `audit_architecture_phase3`,
  `audit_platform_guardrails` — 0 findings. Residual: zero
  `X-Delpi-Service-Token`/`apply_internal_service_headers` fora de
  testes e docstring em `engineering_app/`.
