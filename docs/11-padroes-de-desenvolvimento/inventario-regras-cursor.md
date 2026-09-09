# Inventário das regras Cursor por responsabilidade

> **Status:** documentação normativa de governança — setembro/2026.

Este inventário classifica cada regra especializada sob **um único owner transversal primário**. Uma regra pode referenciar outras responsabilidades, mas não pode possuir dois owners primários nem ficar órfã.

A fonte executável desta classificação é `.cursor/rules/responsibility-map.json`.

## Regras fora do inventário especializado

As cinco regras globais formam a constituição mínima e não pertencem a um único owner especializado:

- `development-standards-index.mdc`
- `evidence-driven-execution.mdc`
- `centralized-rules-first.mdc`
- `clean-code-architecture-guardrails.mdc`
- `english-code-identifiers.mdc`

As oito regras `platform-*.mdc` são os próprios owners e também não são listadas como filhas.

---

## 1. Arquitetura e boundaries

Owner: `platform-architecture-boundaries.mdc`

- `application-bounded-context-decoupling.mdc`
- `assistant-content-json.mdc`
- `chat-intelligence-base.mdc`
- `clean-architecture-chat-api.mdc`
- `llm-stack-centralized.mdc`
- `mfe-own-api-no-direct-api-delpi.mdc`
- `presentation-operational-decoupling.mdc`
- `schema-first-presentation-delivered.mdc`

Racional: ownership, fonte de verdade, direção de dependências e divisão de responsabilidades.

**Gate implementado:** `MFE_OWN_API_BYPASS` deriva o bounded context pela existência de `plugins/<app>` + `<app>-api` e bloqueia novo acesso direto do MFE a `/apps/api-delpi`.

**Gap ainda aberto:** imports backend entre bounded contexts precisam de modelagem por ports/adapters antes de bloquear CI; não criar allowlist manual de cada par de apps sem necessidade.

## 2. Segurança, identidade e autorização

Owner: `platform-security-identity-authorization.mdc`

- `ai-external-tools-security.mdc`

### Gates implementados

- `JWT_VERIFY_DISABLED` — bloqueia downgrade de assinatura/audience/issuer;
- `JWT_VALIDATOR_DUPLICATION` — bloqueia novo `jwt.decode` local em API de domínio;
- `AUTHZ_PRIMITIVE_DUPLICATION` — bloqueia cópia de primitives genéricas `require_*`;
- `FASTAPI_WRITE_AUTHZ_EVIDENCE_REQUIRED` — write FastAPI novo/alterado precisa evidenciar onde a autorização ocorre;
- `FASTAPI_PUBLIC_ROUTE_AUTH_DRIFT` — `/public/...` não pode divergir do contrato real do `auth_middleware`;
- `FASTAPI_AUTHZ_PARSE_ERROR` — fonte alterada que não pode ser analisada não é aprovada silenciosamente.

### P0 de JWT — corrigido

`shared/delpi_auth/jwt_validator.py` foi endurecido para fail-closed:

```text
KEYCLOAK_AUDIENCE obrigatório
KEYCLOAK_ISSUER obrigatório
assinatura validada
issuer validado
audience validada
algoritmos explícitos
configuração inválida não vira refresh/retry de JWKS
```

A configuração foi auditada em `docker-compose.dev.yml`, `docker-compose.yml`, `.env.dev.example` e `.env.prod.example` antes da mudança. O teste dedicado roda no `Architecture Enforcement`.

### Modelo atual de AuthZ FastAPI

Para writes, o gate reconhece os padrões reais da plataforma:

```text
decorator canônico
OU guarda explícita no handler
OU contexto do usuário entregue ao application/use case que autoriza
OU rota pública efetivamente declarada no middleware
```

Isso evita impor `@require_permission` a bounded contexts que corretamente mantêm autorização contextual no application layer.

**Gap restante:** reads (`GET`) ainda não têm exigência equivalente de business AuthZ. Primeiro separar authenticated-only, permission-protected, resource-scoped, public e service-to-service.

## 3. APIs, contratos e integrações

Owner: `platform-api-contracts-integration.mdc`

- `api-delpi-openapi-route-standards.mdc`
- `api-delpi-response-contract.mdc`
- `contract-evolution-backward-compatibility.mdc`
- `new-api-route-checklist.mdc`
- `openapi-first-universal-tool-routing.mdc`
- `operational-api-routing.mdc`
- `tv-dashboard-optional-data-filters.mdc`

Racional: identidade/semântica de operações, request/response, parâmetros, evolução e integração por contrato.

### Gates OpenAPI/FastAPI implementados

- `OPENAPI_OPERATION_ID_REQUIRED`;
- `OPENAPI_OPERATION_ID_DUPLICATE`;
- `OPENAPI_CHANGE_CLASS_INVALID`;
- `OPENAPI_BREAKING_UNCLASSIFIED`;
- `FASTAPI_OPERATION_ID_REQUIRED`;
- `FASTAPI_OPERATION_ID_DUPLICATE`;
- `FASTAPI_ROUTE_PARSE_ERROR`.

Breaking estrutural atualmente detectado em snapshot OpenAPI versionado:

```text
operação removida
operationId alterado
parâmetro obrigatório novo
parâmetro opcional → obrigatório
parâmetro local via $ref que introduz required
requestBody opcional → obrigatório
resposta 2xx documentada removida
```

O parser FastAPI também cobre o padrão `APIRouter(prefix="...")` + `@router.<method>("")`, evitando falso negativo em rota de prefixo puro.

**Gap restante:** compatibilidade profunda de schemas compartilhados (`type`, enum narrowing, required aninhado, `oneOf/allOf/anyOf`, `$ref` externo e schema usado em request+response) exige resolver estrutural mais completo antes de virar gate.

## 4. Dados e persistência

Owner: `platform-data-persistence.mdc`

- `migrations-immutable-checksum.mdc`
- `persistent-upload-storage.mdc`
- `plugins-migrations-no-reset-prod.mdc`
- `si-consolidated-department-idd.mdc`
- `sql-query-development.mdc`
- `totvs-product-patterns.mdc`
- `totvs-warehouse-cost-standards.mdc`
- `tv-dashboard-persist-local-edits.mdc`

Racional: schema, migration, persistência durável, consulta e invariantes de dados.

**Gate implementado:** `IMMUTABLE_MIGRATION_MUTATION` permite nova `VNN__*.sql`, mas bloqueia modificação, rename ou remoção de migration SQL já versionada.

## 5. Frontend, MFE e experiência

Owner: `platform-frontend-mfe-experience.mdc`

- `chat-prose-rendering.mdc`
- `feature-help-sync.mdc`
- `mf-federation-patch-safety.mdc`
- `mfe-modal-host-contained.mdc`
- `notification-catalog-preferences.mdc`
- `plugin-mfe-page-excellence.mdc`
- `plugins-overlay-positioning.mdc`
- `plugins-reusable-components.mdc`
- `plugins-visual-design-system.mdc`
- `tv-dashboard-editor-pasteboard.mdc`
- `tv-dashboard-presentation-parity.mdc`

Racional: composição visual, integração federada, design system, estados, acessibilidade e comportamento de UI.

**Gates implementados:**

- `MFE_GLOBAL_CSS`;
- `MFE_PLUGIN_UI_OVERRIDE`;
- `MFE_OWN_API_BYPASS`.

## 6. Qualidade, testes e evidência

Owner: `platform-quality-testing.mdc`

- `ai-intelligence-evaluation.mdc`
- `architecture-ci-enforcement.mdc`
- `cursor-rules-governance.mdc`
- `plan-construction.mdc`
- `plan-execution.mdc`
- `plugins-documentation.mdc`
- `root-cause-generalized-fix.mdc`
- `test-and-commit.mdc`

Racional: investigação, planejamento, execução controlada, evidência, regressão, generalização, desacoplamento, CI, documentação e Definition of Done.

`plan-construction.mdc` governa **como construir/revisar** planos. `plan-execution.mdc` governa **como executar e avaliar** cada subetapa e o verify-final, incluindo os gates `OBJECTIVE_RESOLVED`, `GENERALIZATION`, `DECOUPLING` e `REGRESSION_SAFETY`.

`Architecture Enforcement` executa:

```text
audit_architecture_phase3.py
audit_platform_guardrails.py
audit_openapi_contracts.py
audit_fastapi_authz.py
shared/delpi_auth/tests/test_jwt_validator.py
```

Todos os auditores possuem testes próprios. `Cursor Rules Governance` valida ownership via `responsibility-map.json`.

## 7. Delivery, runtime e operações

Owner: `platform-delivery-runtime-operations.mdc`

- `infra-sequential-container-startup.mdc`
- `plugins-frontend-build.mdc`

**Gap identificado:** health/readiness/rollback possuem documentação e scripts, mas ainda faltam contratos comuns suficientemente determinísticos para gates transversais seguros.

## 8. Confiabilidade e observabilidade

Owner: `platform-reliability-observability.mdc`

- `ai-context-and-tool-budget.mdc`
- `http-integration-resilience.mdc`
- `observability-standards.mdc`

Racional: limites, latência, timeout/retry, degradação, logs, métricas, tracing e capacidade.

O scanner Phase 3 bloqueia novas chamadas HTTP Python detectáveis sem timeout, retry inseguro de writes e exposição óbvia de secrets.

---

# Sobreposições revisadas

## Permanecem separadas

### `plan-construction` × `plan-execution`

- `plan-construction` governa evidência, decisões, rastreabilidade e receita **antes da implementação**;
- `plan-execution` governa preflight, drift, escopo, diff review, avaliação pós-execução e verify-final **durante/depois da implementação**.

Não duplicar arquitetura de domínio nessas regras; ambas referenciam os owners transversais aplicáveis.

### `plugins-reusable-components` × `plugins-visual-design-system` × `plugin-mfe-page-excellence`

- reusable components governa **onde o componente compartilhado vive**;
- visual design system governa **tokens/CSS/tema/responsividade**;
- page excellence governa **composição e qualidade da página**.

### `migrations-immutable-checksum` × `plugins-migrations-no-reset-prod`

Uma protege imutabilidade de migration; outra protege operação de produção contra reset destrutivo.

### `api-delpi-openapi-route-standards` × `api-delpi-response-contract`

Uma governa metadata/qualidade da operação; outra governa envelope/semântica da resposta.

## Candidatos a consolidação futura

### `presentation-operational-decoupling` × `schema-first-presentation-delivered`
Há sobreposição relevante. Antes de fundir, inventariar referências e preservar gates. **Não criar terceira regra de apresentação.**

### `new-api-route-checklist` × regras OpenAPI específicas
O checklist continua ponto de entrada operacional; contrato detalhado fica na regra técnica dona.

### regras `tv-dashboard-*`
Revisar após estabilização. Regra criada por incidente não deve permanecer indefinidamente se conhecimento puder migrar para owner transversal ou documentação do domínio.

---

# Gaps prioritários para enforcement

## Implementados

1. migrations imutáveis;
2. CSS global/override de `plugin-ui` em MFE;
3. boundary MFE → BFF próprio;
4. JWT fail-closed e prevenção de downgrade/duplicação;
5. centralização de primitives AuthZ;
6. ownership de autorização para writes FastAPI;
7. coerência de rotas públicas FastAPI;
8. `operationId` explícito/único;
9. breaking estrutural OpenAPI selecionado;
10. HTTP timeout/retry/secrets;
11. protocolo de execução de planos com avaliação explícita de objetivo, generalização, desacoplamento e regressão.

## Próximos, após modelagem segura

1. ampliar drift de rota pública para qualquer método HTTP sem ampliar ainda business AuthZ de GET;
2. classificar reads para decidir cobertura AuthZ de GET;
3. boundaries backend entre contexts por imports/ports;
4. compatibilidade profunda de schema OpenAPI;
5. MFE federation/build usando helpers vigentes como contrato;
6. delivery: health/readiness/rollback quando houver convenção comum verificável.

Gates permanecem incrementais/diff-aware quando existe dívida histórica. Não tornar CI vermelho por todo o passado para depois criar exceções genéricas.

# Regra de manutenção

Ao criar nova `.mdc` especializada:

```text
responsabilidade nova realmente existe?
    não → estender regra existente
    sim → owner transversal continua o mesmo
→ adicionar ao responsibility-map.json
→ atualizar este inventário se a regra for durável
→ executar audit_cursor_rules.py
```

Uma regra não classificada é erro de governança.
