# INTEGRACOES — Portal Suprimentos

## 1. Diagrama

```text
MFE supplies
  → /apps/supplies-api/*
      Authorization: Bearer
      X-Request-Id
        → supplies-api
            → Core /me (effective permissions)
            → api-delpi
            → purchase-requests-api (C1)
            → strategic-indicators-api
            → contexto Qualidade, quando autorizado
```

O JWT Keycloak identifica e autentica. **Authorization efetiva vem do Core API**; não confiar em `permissions`/`is_superadmin` dos claims como decisão final.

Não copiar os middlewares compartilhados:

- `shared/delpi_auth/middleware/flask_auth.py` — AuthZ a partir de claims;
- `shared/delpi_auth/middleware/fastapi_auth.py` — Core `/me` com fallback `rbac_lookup_unavailable_using_token_claims` / `_rbac_from_claims` e possível stale cache.

Detalhe e GATE-AUTHZ: [ADR-001](./adr/ADR-001-supplies-api.md).

## 2. Authz

Fluxo canônico:

```text
JWT válido
→ resolver effective permissions no Core
→ capability mínima (ADR-007)
→ allowedUnits (ADR-006)
→ ownership/resource scope
→ business rule
```

Falha do Core ao comprovar autorização de uma operação protegida = fail-closed **na fronteira da supplies-api** (503/401), não “seguir autenticado e esperar o decorator”. Cache/stale só pode ser usado se o mecanismo compartilhado da plataforma tiver política canônica explícita **e** a E2 a citar nos testes do GATE-AUTHZ.

## 3. Observabilidade

Alinhar `observability-standards.mdc`:

- request/correlation id em todos os hops;
- log estruturado com `request_id`, `user_id`, `branch`, `operation_id`, downstream e duração;
- nunca logar Authorization, cookies, secrets ou payload sensível integral;
- métricas: latência BFF, downstream, 403 por capability/unidade, 502/504, partial response, cache hit/stale;
- tracing quando houver padrão canônico compartilhado.

## 4. HTTP resilience

Todo client HTTP deve ter timeout explícito.

- retry somente em operação idempotente e quando política permitir;
- nenhum retry cego em POST/PATCH;
- circuit breaker somente se já houver padrão compartilhado ou evidência que o justifique;
- cancelamento/disconnect quando aplicável;
- `X-Delpi-Caller-App: supplies-api` nas chamadas internas que seguem esse contrato.

## 5. Composição e falha parcial

BFFs compostos (`/analytics/overview`, Supplier 360, Product 360) devem ter budget global e timeout por dependência.

Política base:

```text
falha de bloco auxiliar
→ resposta parcial utilizável
→ bloco marcado unavailable
→ erro observável

falha de authz ou recurso principal
→ não mascarar como partial success
```

Exemplo:

```text
CPV OK
OTD OK
stock timeout
SI OK
→ 200 parcial + stock unavailable
```

A forma exata de metadata deve ser congelada no contrato antes da implementação.

## 6. Multi-unidade

`allowedUnits` é derivado das **permissions efetivas do Core** intersectadas com o catálogo `supplies.unit.filial-{TOTVS}`.

- branch fora do conjunto → 403;
- branch omitido → união somente das units autorizadas;
- consolidado nunca significa empresa inteira implicitamente;
- nova filial exige um code de unidade, não permission por tela.

## 7. Strategic Indicators

Metas e snapshots continuam no SI. O Portal pode compor leitura, mas deve respeitar o recorte de unidades autorizado ao usuário.

Quando o SI oferecer consolidado corporativo e o usuário tiver somente subconjunto de units, a supplies-api não deve expor o consolidado irrestrito como se estivesse autorizado.

## 8. Qualidade e Financeiro

- Qualidade: projeção no Supplier 360 somente com autorização do contexto de Qualidade; processo continua fora de Suprimentos.
- Financeiro/frete: deep link ou projeção controlada; regra financeira permanece no owner.

## 9. Notificações

Hoje, notificações de Solicitações pertencem ao fluxo existente de `purchase-requests-api`. Na C2, jobs migram para supplies-api mantendo categoria/contrato enquanto consumidores ainda dependem dele.

Não criar canal paralelo sem necessidade.

## 10. Chat / OpenAPI

Nova rota TOTVS só nasce na api-delpi quando houver gap comprovado. Se a nova operation for utilizável pelo chat, seguir import/index e governança OpenAPI-first. Portal Suprimentos não assume tool routing.

## 11. Compose / Gateway quando autorizado

Deploy seguro:

```text
supplies-api saudável
→ gateway conhece target sem redirect legado
→ MFE supplies saudável
→ manifest + RBAC
→ smoke URL nova
→ somente depois redirects de cutover
```

Usar scripts sequenciais canônicos. Não ativar redirect para target ainda não homologado.
