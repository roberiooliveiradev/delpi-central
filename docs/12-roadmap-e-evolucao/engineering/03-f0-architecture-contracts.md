# F0 — Arquitetura e Contratos — EVA / Portal Engenharia DELPI

> **Documento:** `03-f0-architecture-contracts.md`
> **Fase:** F0 — preparação arquitetural; nenhum contrato foi implementado
> **Regra:** candidatos aqui não são runtime; são `TARGET`/`PLANNED` até implementação + teste

---

## 1. Boundaries canônicos

```text
plugins/engineering  ──HTTP──►  engineering-api  ──HTTP──►  Domain APIs oficiais
      │                            │                       (api-delpi, SI, requests,
      │                            │                        transformometro, FILESERVER)
      │                            ├──► Core API (identity, effective RBAC, apps/routes)
      │                            └──► mcp-engineering? — não. EVA consome engineering-api/domain via ports
      │
   @delpi/plugin-ui (kit federado — única dependência visual permitida além do BFF)
```

Regras verificadas (`platform-architecture-boundaries.mdc`, `mfe-own-api-no-direct-api-delpi.mdc`, `application-bounded-context-decoupling.mdc`):

- `engineering-api` **não substitui** `api-delpi` e não assume ownership de LMP/TOTVS, products, SI, Control MP, TRANSFORMA+, RBAC ou FILESERVER;
- o MFE **não** chama `api-delpi` diretamente (o legado `dashboard-*` viola isso — ver §7 de `02-f0-factual-inventory.md`);
- cross-context apenas via HTTP/event contracts estáveis + anti-corruption DTOs no BFF — nunca import de domain/use case nem FK/banco cruzado;
- `mcp-engineering` é **adapter de interoperabilidade**, não domínio, não authority, não proxy genérico;
- EVA Application/Domain → ports → adapters (MCP é um adapter; LLM provider é outro);
- nenhuma runtime dependency de EVA em `minha-delpi-ai-api` (Chat) — referência `delia-api` como specialist standalone.

### O que `engineering-api` realmente é (e não é)

**É:** BFF do Portal Engenharia — composição read-only inicial, owner de estado próprio do Portal (futuras interaction rooms, settings, preferências de biblioteca), tradutor de provider errors, orquestrador de fan-out controlado com provenance/degradation explícitas.

**Não é:** fonte de verdade de LMP/produto/indicador/NC/estoque/preço; reimplementação de TOTVS rules; proxy pass-through de payload cru (`INTEGRACOES.md` §4); serviço de chat compartilhado (`PLAYBOOK` proíbe `commercial-api` como chat provider para Engineering — simetricamente Engineering não é provider de outros portais).

---

## 2. Matriz de ownership

| Responsabilidade | Owner | Fonte canônica | Consumer | Contrato | AuthZ | Evidência | Status |
|---|---|---|---|---|---|---|---|
| Identidade/SSO | Keycloak | OIDC/JWT | todos | token Bearer | — | `delpi_auth/jwt_validator.py` | `PROVEN` |
| Apps/rotas/RBAC efetivo | Core API | `core-api/app/interfaces/http/me_controller.py` | Portal, `delpi_auth` middleware | `GET /me`, `GET /me/apps` | backend-first | código + Portal `AuthContext` | `PROVEN` |
| Host/navegação | Portal | `portal/src/ui/AppHost.tsx`, `consumo-de-plugins.md` | usuário | `/me/apps` + manifests | route permission | código | `PROVEN` |
| Kit visual | `plugins/plugin-ui` | `component-catalog.md`, `src/components/*` | MFEs | `@delpi/plugin-ui` exports | — | código | `PROVEN` |
| LMP/NC/produtos/desenhos/TOTVS | `api-delpi` | `routes/engineering/*`, `product*_routes.py` | BFF futuro (hoje: legados direto) | OpenAPI + `api_delpi_success` envelope | `ENGINEERING_*`, `METALOGRAPHY_*`, product perms | código | `PROVEN` |
| Indicadores Engenharia | `strategic-indicators-api` | `si_app/.../engineering_metrics_helpers.py` | BFF futuro | SI contracts | SI perms | código+testes | `PROVEN` |
| Controle MP | `requests-api`/`my-requests` | `raw-material-creation` type + perms | BFF (resumo) + deep link | requests contracts | `my-requests.raw-material-creation.*` | código+testes | `PROVEN` |
| TRANSFORMA+ | `transformometro-api` | via gateways em `api-delpi` hoje | BFF futuro | transformometro contracts | — | `engineering_composer.py` | `PROVEN` |
| FILESERVER/desenhos | storage/api-delpi | `product_drawing_routes.py` | BFF (via api-delpi) | drawing routes | product perms | código | `PROVEN` (desenhos); `NOT_READY` libs genéricas |
| Composição Portal Engenharia | `engineering-api` (futuro) | este doc + `API-ROUTES.md` | `plugins/engineering` | `GET /v1/*` candidatos | `engineering.*` | docs | `TARGET` |
| Interaction rooms Engenharia | `engineering-api` (futuro) | `ADR-004` | MFE | `/v1/rooms` candidato | `engineering.*` + membership | docs | `TARGET` — P-01..P-05 `NOT_READY` |
| Interpretação/inteligência técnica | EVA (futuro specialist) | `DESIGN-IA-ENGENHARIA.md`; forma: `delia-api` | MFE/API | EVA contracts | EVA user parity | referência | `TARGET` |
| Interoperabilidade MCP | `mcp-engineering` (futuro adapter) | `shared/delpi_mcp` + `openai-plugin-mcp-integration.mdc` | consumers MCP autorizados | MCP streamable-http | Bearer + resource audience + scopes transport + app AuthZ | `shared/delpi_mcp` | `TARGET` — Abstraction Gate pendente |
| Revisão/aprovação técnica | Engineering owners | processo | — | — | — | — | `PLANNED` |

---

## 3. Fluxos de integração

### 3.1. Início (RQ-ENG-002 / RQ-PORTAL-002) — TARGET

```text
plugins/engineering → GET /apps/engineering-api/v1/home
  engineering-api:
    ├── Core /me (via delpi_auth middleware — effective permissions)
    ├── fan-out read-only controlado:
    │     ├── api-delpi /engineering/lmps/summary (candidato — revalidar contrato exato)
    │     ├── SI indicators (engineering-projects-on-time, engineering-transforma-plus)
    │     ├── requests-api raw-material-creation summary (se contrato existir)
    │     └── transformometro summary (via api-delpi hoje — revalidar)
    └── resposta: blocos com { status: ok|partial|unavailable|forbidden, provenance: {source, sha_version}, data }
```

Regras (de `INTEGRACOES.md`, canonical): nunca mascarar mutação como sucesso; composições de leitura podem ser `partial`; MFE não recalcula IDD; nenhum `allowed_actions` inventado sem owner.

### 3.2. AuthN/Z pipeline — PROVEN como padrão

```text
Bearer JWT (Keycloak)
→ delpi_auth.middleware.fastapi_auth.jwt_middleware
→ validate_token
→ Core GET /me (cache TTL; force_refresh em writes sensíveis)
→ require_any_permission("engineering.access", ...)
→ handler
```

Fail-closed: Core lookup failure → authorization error. Sem JWT local próprio, sem RBAC local, sem bypass de superadmin app-specific (superadmin é primitiva compartilhada de `delpi_auth`).

### 3.3. MCP (RQ-EVA-001) — TARGET

```text
MCP client ──► /apps/mcp-engineering/mcp  (streamable-http)
  └── delpi_mcp.mcp_transport_auth:
        Bearer obrigatório; service tokens internos rejeitados em user-data paths;
        validate_token; resource audience exata; scopes de transporte;
        DNS rebinding protection; /mcp→/mcp/ rewrite sem redirect
  └── business AuthZ delegada à app (não ao transporte)
  └── tools mínimos → ports application/domain → adapters HTTP (não domain import)
```

**Abstraction Gate obrigatório** (`openai-plugin-mcp-integration.mdc`) antes de qualquer código MCP: consumer real, owner, capability, contrato, reuso application/domain, benefício vs HTTP. Status: `NOT_READY` — gate não foi satisfeito em F0.

### 3.4. Sala (futura) — TARGET condicional

`ADR-004` + `INTEGRACOES.md` §10: canal próprio de `engineering-api`; handshake autenticado; Core-first; subscribe/unsubscribe `room:{id}`; persist-before-publish; anti-eco; menção offline → Notification Catalog/Core quando aprovado. `commercial-api` interaction rooms = referência de protocolo/UX, **não** provider. Realtime tech em Flask: `NOT_READY` (P-05).

---

## 4. Contratos candidatos (TARGET — não implementados)

> Origem: `API-ROUTES.md`, `MANIFEST-DRAFT.md`, `INTEGRACOES.md`. Revalidar contra OpenAPI vigente em F1.

| Candidato | Verbo/Path | Owner da semântica | Bloco Início | Risco |
|---|---|---|---|---|
| Home | `GET /v1/home` | engineering-api (composição) | todos | fan-out/provenance — mitigável com contract tests |
| Overview | `GET /v1/overview` | engineering-api + SI | — (pós-Início) | fórmulas P-15 abertas |
| Tarefas | `GET /v1/my-tasks` | engineering-api agregador | worklist preview | P-06/P-07 — sources/ações `NOT_READY` |
| Salas | `/v1/rooms*` | engineering-api | CTA apenas | P-01..P-05 `NOT_READY` |
| Bibliotecas | `/v1/document-libraries*` | engineering-api + storage | atalho | P-12/P-13 `NOT_READY` (desenhos via api-delpi OK) |
| Integrações | `/v1/integrations/raw-material-control/summary`, `/v1/integrations/transforma-plus/summary` | engineering-api adapter | cards | contratos exatos `TO_INVENTORY` |

Convenções herdadas (PROVEN na plataforma): paths kebab-case inglês; `operationId` estruturado; envelope de sucesso/erro canônico do serviço (ver `api-delpi-response-contract.mdc` e `platform-api-contracts-integration.mdc`); OpenAPI-first.

### DTO anti-corruption

`INTEGRACOES.md` §4: BFF cria DTOs próprios, **não** repassa payload TOTVS/api-delpi cru. Cada dimensão preserva semântica do owner (§5: ficha 360° de produto pode compor, sem reescrever regra).

---

## 5. AuthN/AuthZ

| Camada | Fato | Status |
|---|---|---|
| JWT Keycloak | `delpi_auth.jwt_validator.validate_token` | `PROVEN` |
| Effective RBAC via Core `/me` | `delpi_auth.middleware.fastapi_auth` (cache normal/stale; `force_refresh` em writes) | `PROVEN` |
| Permission helpers | `require_any_permission`, `has_any_permission` | `PROVEN` |
| Service tokens | `delpi_auth.service_token*` — server-to-server quando contrato exigir; proibidos em MCP user-data paths | `PROVEN` |
| Permissions Engineering alvo | `engineering.access`, `engineering.analytics.access`, `engineering.lmps.access`, `engineering.products.access`, `engineering.documents.access`, `engineering.nonconformities.write`, `engineering.costs.view` (+ futura `engineering.administration.manage`) | `PLANNED` — revalidar catálogo Core; legados `dashboard-engineering.view`, `dashboard-lmps.view`, `dashboard-lmps.nc.write` a mapear em coexistência |
| Propagação downstream | token de usuário só quando downstream espera user context; service credential só quando contrato exige; nunca elevar acesso por credencial técnica sem policy no BFF (`INTEGRACOES.md` §11) | regra canonical — aplicação `PLANNED` |

---

## 6. Dados e evidência

- `engineering-api` sem persistência própria no bootstrap mínimo do Início (composição stateless é suficiente para RQ-ENG-002). Persistência entra quando Sala/settings/bibliotecas exigirem — `DATA-MODEL.md` é `PLANNED`; escolha de DB/runner `NOT_READY`.
- Resposta `GET /v1/home` deve carregar `provenance` por bloco: `{ source: "api-delpi"|"si"|"requests"|"transformometro", status, observed_at, version_hint }` — suporte a `partial` sem mascaramento (RQ-ENG-002).
- Timeout/retry por gateway explícito (`http-integration-resilience.mdc`); fan-out controlado; orçamento total < timeout do gateway externo.
- Erros traduzidos para semântica Portal: 401/403/404/422/5xx-timeout; sem stack/SQL/hostname/path físico (`INTEGRACOES.md` §13).
- Observabilidade por gateway: `provider, operation, status_class, latency_ms, timeout, partial_source` + correlation/request id (`observability-standards.mdc`).

---

## 7. Decisões arquiteturais pendentes (`ARCHITECTURE_DECISION_REQUIRED`)

| ID | Decisão | Estado | Bloqueia | Fonte |
|---|---|---|---|---|
| ADR-REQ-01 | Persistência própria de `engineering-api` (DB, migration runner) — necessária? quando? | `NOT_READY` | E1 bootstrap se houver state; Sala certamente | `DATA-MODEL.md` |
| ADR-REQ-02 | Permission codes `engineering.*` finais + mapeamento legado `dashboard-*` coexistência | `NOT_READY` | manifest/Core seed | `PERFIS-E-PERMISSOES.md` |
| ADR-REQ-03 | Consumer real + contrato do `mcp-engineering` (Abstraction Gate) | `NOT_READY` | qualquer código MCP | `openai-plugin-mcp-integration.mdc` |
| ADR-REQ-04 | Contratos exatos downstream para `/v1/home` (LMP summary, SI, requests, TRANSFORMA+) | `TO_INVENTORY` | RQ-ENG-002 | `INTEGRACOES.md` §4–8 |
| ADR-REQ-05 | Naming/estrutura do serviço (`app/` vs `<svc>_app/`; Flask confirmado?) — inconsistente no repo (delia `app/`, commercial `commercial_app/`) | `NOT_READY` | scaffold F1 | §2.5 do inventory |
| ADR-REQ-06 | Realtime Flask-compatible da Sala | `NOT_READY` (P-05) | Sala | `INTEGRACOES.md` §10 |
| ADR-REQ-07 | Deep links exatos `my-requests` (request types, query params, rotas `/new`,`/mine`,`/work-queue`) | `READY_BOUNDED` (P-19) | CTA Controle MP | `DECISOES-FUNCIONAIS-PENDENTES.md` |
| ADR-REQ-08 | Escopo por filial/unidade (P-08) | `NOT_READY` | RBAC operacional/worklist | idem |
| ADR-REQ-09 | Forma EVA standalone vs. composição (nova API specialist própria? dentro de engineering-api?) | `NOT_READY` | RQ-EVA-* | `DESIGN-IA-ENGENHARIA.md` + `delia-api` precedent |
| ADR-REQ-10 | Gateway/nginx path + container name + Compose do serviço | `TO_INVENTORY` | deploy F1 | padrão `/apps/<svc>-api/` |

P-01..P-20 de `DECISOES-FUNCIONAIS-PENDENTES.md` permanecem autoridade funcional — esta tabela cruza apenas o que afeta contratos/arquitetura.

---

## 8. Riscos e recomendações

| Risco | Justificativa | Recomendação |
|---|---|---|
| Carregar anti-padrão legado MFE→api-delpi para o target | 6 arquivos `dashboard-*` provados com base URL direta | Estrutural CI audit restringindo `plugins/engineering` a `/apps/engineering-api` + contract test negativo |
| MCP virar proxy genérico/segunda RBAC | regra canônica proíbe; `delpi_mcp` é transporte puro | Satisfazer Abstraction Gate com consumer/contrato reais antes de qualquer código |
| Fan-out do `/v1/home` sem orçamento | 4+ downstreams possíveis | timeouts por gateway + `partial` explícito + contract tests com downstream fake (AC-ENG-002) |
| Permissions `engineering.*` divergirem do catálogo Core | codes em draft, catálogo real não consultado | Revalidar catálogo Core antes do seed; mapear legados em coexistência |
| EVA depender do Chat | regra explícita do usuário + boundaries | Specialist standalone seguindo forma `delia-api` (ports/adapters, `ModelInvocationPort`-like) |
| Sala sem decisões P-01..P-05 | membership/realtime/storage/retention abertos | Sala fora do escopo Início; CTA degradável |
| Naming `app/` vs `<svc>_app/` | divergência real entre delia/commercial/requests | Decisão em F1 (ADR-REQ-05); seguir convenção majoritária de serviços Flask recentes ou documentar escolha |
| Inflar inventário com plano | Foundation 001 é intenção | Manter `PLANNED`/`TARGET` separado de `PROVEN` em todos os artefatos |

---

## 9. Precedência em conflito registrado

1. Regras `.cursor/rules` (8 responsabilidades + `mfe-own-api-no-direct-api-delpi` + `openai-plugin-mcp-integration`) > docs Engineering > legado `dashboard-*`.
2. `105118dd` (baseline pedida) vs `23613bd1f1`/`b886664da` (main real): divergência registrada; inspeção feita no HEAD real.
3. `delia-api` usa `app/interfaces/`; maioria usa `interface/` — registrado como inconsistência factual, não reconciliado.
4. Legados `dashboard-*` chamam api-delpi direto — registrado como anti-padrão factual; target segue a regra.
