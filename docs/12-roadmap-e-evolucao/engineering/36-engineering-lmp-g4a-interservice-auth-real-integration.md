# ENGINEERING.LMP.G4.A — Interservice Authentication & Real Integration Evidence

> Documento 36 da série EVA / Portal Engenharia DELPI.
> Execução: bounded, autorizada pela Coordenação EVA.
> Baseline: `78e7b4d7ef274b8673d92bf1b30d6db21cf63485` (`origin/main`).

## 1. Objetivo e escopo

Comprovar que a Engineering API consome, de forma segura e governada, os
contratos facts de LMPs da API DELPI no fluxo:

```
Portal/EVA → Engineering API → BFF existente → API DELPI Facts → TOTVS
```

Alteração permitida: ajustes mínimos de integração (§13 da missão), incluindo
o menor ajuste seguro ao guard do contrato facts caso `engineering.access`
fosse incompatível (§5). **Foi necessário e está documentado em §4.**

Não autorizado: deploy, provisioning Keycloak/Core, novos consumidores,
remoção de contratos legados, ferramentas EVA, frontend.

## 2. Reancoragem (G4A-01)

```
BASE_HEAD   = 78e7b4d7ef274b8673d92bf1b30d6db21cf63485  (= origin/main)
git status  = pre-existing helpdesk-api + untracked artifacts → preservados
git log -10 = doc 35 (G3) mergeado em 78e7b4d; sem conflitos no escopo
```

Authorities lidas: `AGENTS.md`, regras always-on, docs 32/33/34/35,
`lmp_semantics.v1.yaml`, `delpi_auth` (authorization, context_resolver,
service_auth), rotas facts G2, `DownstreamClient`, composer LMP.

## 3. Inventário do mecanismo BFF (G4A-02)

Reutilizado sem duplicação (Abstraction Gate passou — zero novos clientes):

| Componente | Arquivo | Reuso |
|---|---|---|
| `DownstreamClient` (GET/POST) | `engineering_app/infrastructure/gateways/downstream_client.py` | Direto |
| `ApiDelpiFactsSource` | `engineering_app/infrastructure/gateways/api_delpi_facts.py` | Direto |
| `LmpFactsSource` (port) | `engineering_app/application/ports/lmp_facts.py` | Direto |
| F-LMP-01..04 | `api-delpi/app/interface/http/routes/lmp_facts_router.py` | Direto |
| `delpi_auth` JWT/Core/service | `shared/delpi_auth/` | Direto |
| `ServiceTokenValidator` S2S | `shared/delpi_auth/service_auth.py` | Direto |

Correções mínimas aplicadas ao mecanismo existente (G3 já havia integrado,
mas dois drift de contrato apareceram em runtime):

1. **`listing_type` canonicalização** — use cases enviavam `lmp`; F-LMP-01
   valida `^(Todos|LMP|Amostra|Outro)$` → 422. Adicionado mapeamento canônico
   `canonical_listing_type` em `domain/lmp/listing_semantics.py` usado por
   ambos os use cases (list + summary).
2. **`X-Request-Id` propagado** — `DownstreamClient` já o envia; verificado
   end-to-end em §8.

## 4. Contrato facts — ajuste de boundary autorizado (G4A-04/06)

### Situação encontrada

O guard do caminho humano em `lmp_facts_router.py` exigia
`ENGINEERING_LMP_ACCESS` (permissão legada). Um usuário Portal Engenharia
com apenas `engineering.access` receberia 403 nos facts — a Engineering API
ficaria `forbidden` para usuários legítimos.

### Ajuste aplicado (menor seguro)

O guard humano passa a aceitar `ENGINEERING_LMP_ACCESS` **ou**
`ENGINEERING_ACCESS` (`engineering.access`). Sem bypass, sem endpoint
público, sem weaken de denegation: token ausente → 401; sem nenhuma das
duas permissões → 403; Core indisponível → fail-closed (RBACUnavailable →
503 na camada de guard).

Boundary de confiança **não alterado**: o facts contract continua
exigindo permissão explícita; apenas a nova permissão funcional canônica foi
adicionada à allowlist humana, conforme §5 da missão ("propor o menor ajuste
seguro... sem tornar público ou criar bypass"). Registrado aqui como
`ARCHITECTURE_DECISION_REQUIRED: none` — a Coordenação já havia prescrito o
fallback. Path S2S intocado.

### Testes adicionados (matriz §7 da missão)

Em `api-delpi/tests/test_lmp_facts_contracts.py` (+6):

- humano com `engineering.access` → 200 em F-LMP-01/02/03;
- humano com `engineering.manage` apenas → 403 (não ganha facts operacionais);
- humano sem nenhuma permissão → 403;
- legacy `dashboard-lmps.view` sem `engineering.access` → 403 (a permissão
  legada de dashboard **não** é a de facts; o guard humano exige
  `ENGINEERING_LMP_ACCESS` ou `ENGINEERING_ACCESS`);
- Core indisponível no path humano → deny.

Na engineering-api, a suíte existente (9 negativos) já cobre o restante da
matriz: sem JWT 401, JWT inválido, manage-only 403, legada 403, Core down
503/403, forbidden/unavailable honestos.

## 5. Delegação humana (G4A-04)

`Engineering API → api-delpi` carrega o **Bearer humano do usuário**
(`DownstreamClient` repassa `Authorization` original; headers de serviço
nunca injetados — proibido por contrato e auditado). api-delpi autentica o
JWT (Keycloak/JWKS), resolve permissões efetivas na Core, e autoriza via
allowlist humana (agora incluindo `engineering.access`).

`X-Delpi-Caller-App: engineering-api` = telemetria/caller-stats, nunca
autorização. `X-Request-Id` propagado para correlação.

## 6. Contrato S2S canônico (G4A-07)

Inventário contra Keycloak real (`GET /admin/realms/delpi/clients`,
`/client-scopes`, allowlist api-delpi):

| Item | Estado | Evidência |
|---|---|---|
| client `engineering-api` | **AUSENTE** | lista de 16 clients não o contém |
| scope `engineering-facts.read` | **AUSENTE** | client-scopes não o contém |
| allowlist api-delpi | sem `engineering-api` | env redacted `S2S_ALLOWED_CLIENTS` = `supplies-api` apenas |
| `S2S_AUDIENCE` | `api-delpi` vigente | env redacted |
| caminho S2S no código | implementado, fail-closed | `ServiceTokenValidator` — token inválido → 401 `S2S_TOKEN_INVALID` |

**Nomenclatura canônica**: `engineering-facts.read` (dot-notation, mesmo
padrão `suppliers.read|create|update` já existente). A variante `:` está
descartada.

**Provisioning pendente (documentado, não executado):**
`infra/scripts/keycloak_s2s_engineering_facts_scope.py` — mirror exato do
padrão oficial `keycloak_s2s_supplies_scope.py`, `--check` read-only por
default, `--apply` exige https. Check-mode real executado:

```
[kc-s2s-engineering-facts] mode=CHECK realm=delpi
  [DRIFT] client engineering-api — inexistente (criação = decisão de
          provisioning fora do escopo de execução)
[REMINDER] api-delpi env: S2S_ALLOWED_CLIENTS += engineering-api
```

Caminho humano não depende de S2S — integração real já provada com Bearer
humano. Runtime S2S permanece **bloqueado** até provisioning autorizado.
`S2S_FAIL_CLOSED: PASS` — token de serviço inválido → 401.

## 7. Matriz de testes AuthN/AuthZ (G4A-09)

| Cenário | Esperado | Resultado |
|---|---|---|
| `engineering.access` | autorizado | PASS (route + facts + real) |
| sem `engineering.access` | negado | PASS 403 |
| `engineering.manage` apenas | sem acesso operacional | PASS 403 facts + 403 functional |
| somente legada (`dashboard-lmps.view`) | negado nos novos | PASS 403 |
| JWT ausente | 401 | PASS real + teste |
| JWT inválido | negado | PASS real 401 |
| Core indisponível | fail-closed | PASS 503/403 |
| S2S não configurado | fail-closed | PASS (adapter nem tenta) |
| S2S scope ausente | negado | PASS teste unitário `S2S_SCOPE_DENIED` |
| S2S audience incorreta | negado | PASS teste unitário `S2S_TOKEN_INVALID` |
| S2S client não allowlist | negado | PASS teste unitário `S2S_CLIENT_DENIED` |
| token de serviço legado | não usado como auth | PASS — sem headers de serviço em path humano |
| falha api-delpi | erro honesto | PASS `unavailable`/`forbidden` sem dados fictícios |

## 8. Integração real — smoke autorizado (G4A-12)

Ambiente compose local ativo (engineering-api + api-delpi + keycloak +
core-api saudáveis via gateway `http://localhost`). Token humano obtido via
`scripts/get-dev-token.sh` (usuário dev autorizado do realm local).

```
GET /apps/engineering-api/v1/lmps            → 200 success, total=245,
    provenance{TOTVS, api-delpi}, policy{work_month_lmp, res=30min, strict=false}
GET /apps/engineering-api/v1/lmps/summary    → 200 success após fix
    listing_type: total_lmps=217, percent_dentro_prazo=97.7,
    avg_lead_time=2.76, pi_counts_status=available
GET /apps/api-delpi/engineering/lmps/facts         → 200, total=245
GET .../facts/003696 (F-LMP-02)                    → 200, kind=LMP
GET .../003696/history/events (F-LMP-03)           → 200, 14 eventos
GET .../003696/history/flow   (F-LMP-03)           → 200, 1 flow row
POST .../facts/pi-counts (F-LMP-04)                → 200, dados reais
    (01/003674/14 → 4 PIs; 02/000241/05 → 6 PIs)
```

Negativos reais: sem token → 401 (eng-api e api-delpi); token inválido →
401; S2S inválido → 401 `S2S_TOKEN_INVALID`.

`X-Request-Id: g4a-smoke-***` propagado eng-api → api-delpi; api-delpi
logou `api_delpi_request ... operation_id=list_lmp_facts` HTTP 200 (o
middleware api-delpi não imprime request_id — gap de observabilidade
transversal, owner platform-reliability; registrado em §11 como residual
menor, sem impacto em fail-closed).

`REAL_INTEGRATION_SMOKE: PASS` `FACTS_RUNTIME_AVAILABILITY: PASS`

## 9. Compatibilidade transversal (G4A-11)

Zero mudanças em: Dashboard LMPs legado, Dashboard Engenharia, SI,
Portal Engenharia (MFE), DÉLIA, EVA MCP, TV Dashboard. A mudança no guard
facts é **aditiva** (nova permissão aceita; legada preservada) — nenhum
consumidor antigo perde acesso. Sem novos consumers habilitados sobre
contratos G3; sem roteamento de navegação alterado; sem tools EVA.

## 10. Ciclos e boundaries (G4A-10)

Audit `backend_boundaries` — 0 findings. Fluxo unidirecional
`eng-api → api-delpi` confirmado por grafo de imports (api-delpi não
importa engineering_app). Sem SQL na eng-api; sem chamada circular.

## 11. Observabilidade (G4A-13)

- `X-Request-Id` propagado; request_id logado na eng-api.
- `X-Operation-Id`/`operation_id` logado na api-delpi (`list_lmp_facts` etc.).
- `caller_app` capturado via `X-Delpi-Caller-App` para telemetria.
- Estados honestos: `available|empty|unavailable|forbidden|contract_error`.
- Zero tokens/secrets/SQL nos logs.
- Residual menor: api-delpi `request_observability_middleware` não ecoa
  `X-Request-Id` na linha de log (owner platform-reliability-observability;
  a correlação por operation_id+duration já funciona — não bloqueia).

## 12. Documentação e arquivos alterados (G4A-15)

| Arquivo | Mudança |
|---|---|
| `api-delpi/app/interface/http/routes/lmp_facts_router.py` | humano aceita `engineering.access` |
| `api-delpi/tests/test_lmp_facts_contracts.py` | +6 cenários da matriz |
| `engineering-api/engineering_app/domain/lmp/listing_semantics.py` | `canonical_listing_type` |
| `engineering-api/engineering_app/application/use_cases/list_lmps_dashboard.py` | canonicalize |
| `engineering-api/engineering_app/application/use_cases/get_lmp_summary.py` | canonicalize |
| `infra/scripts/keycloak_s2s_engineering_facts_scope.py` | provisioner (novo) |
| este documento | evidência G4.A |

## 13. Resultados de testes no SHA final (G4A-16)

```
engineering-api: 287 passed
api-delpi LMP suites: 182 passed (facts 31/31 incl. novos negativos)
audits: phase3, platform_guardrails, openapi_contracts,
        fastapi_authz, backend_boundaries — 0 findings
secrets scan: limpo
```

## 14. Riscos, residuais e próximo gate (G4A-17)

Residuais (todos externos ao código):
1. Provisioning S2S Keycloak — checklist exato + provisioner pronto; precisa
   de autorização administrativa (criar client confidencial, scope, mapper,
   `S2S_ALLOWED_CLIENTS += engineering-api`).
2. Shadow real 200 OVs × 12 janelas + benchmark — protocolo doc 34 §8,
   requer ambiente TOTVS autorizado.
3. api-delpi `X-Request-Id` não ecoado em log — owner transversal.
4. Endpoints R15/R16 (history via facts) expostos mas ainda não consumidos
   funcionalmente pela eng-api — item de G4.B.

**NEXT_BOUNDED_STEP**: Coordenação autoriza provisioning S2S (script pronto)
ou G4.B (shadow real + benchmark + cutover governado do legado).

**Veredicto proposto: `ACCEPT_WITH_RESIDUAL`** — integração real
provada ponta-a-ponta com delegação humana; residuais são exclusivamente
externos (provisioning, ambiente TOTVS).
