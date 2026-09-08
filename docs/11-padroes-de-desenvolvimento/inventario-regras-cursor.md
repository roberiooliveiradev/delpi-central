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

Racional: essas regras definem ownership, fonte de verdade, direção de dependências ou divisão de responsabilidades dentro de um contexto.

**Gate implementado:** `MFE_OWN_API_BYPASS` deriva o bounded context pela existência de `plugins/<app>` + `<app>-api` e bloqueia novo acesso direto do MFE a `/apps/api-delpi`.

**Gap ainda aberto:** imports entre bounded contexts backend precisam de modelagem por estrutura/ports antes de virar gate; não manter allowlist manual de cada par de apps sem necessidade.

## 2. Segurança, identidade e autorização

Owner: `platform-security-identity-authorization.mdc`

- `ai-external-tools-security.mdc`

### Gates implementados

- `JWT_VERIFY_DISABLED` — bloqueia nova desativação ou condicionamento opcional de assinatura/audience/issuer;
- `JWT_VALIDATOR_DUPLICATION` — bloqueia novo `jwt.decode` local em API de domínio fora de `shared/delpi_auth`/Core;
- `AUTHZ_PRIMITIVE_DUPLICATION` — bloqueia nova cópia local das primitives genéricas `require_auth`, `require_permission`, `require_any_permission`, `require_all_permissions` e `require_superadmin`.

### Dívida P0 confirmada no runtime compartilhado

`shared/delpi_auth/jwt_validator.py` ainda:

```text
- torna verificação de audience dependente da existência de KEYCLOAK_AUDIENCE;
- não passa KEYCLOAK_ISSUER ao jwt.decode.
```

O padrão normativo é fail-closed para assinatura + issuer + audience + expiração. Essa dívida precisa de correção controlada após auditar variáveis de ambiente e consumidores; o comportamento atual não pode ser copiado para serviços novos.

### Gap ainda aberto

A plataforma possui múltiplos stacks válidos de proteção de rotas (`shared/delpi_auth`, decorators Core, dependencies, service token e policies). Não criar regex “sem `@require_permission` = vulnerável”. Primeiro materializar classificação uniforme:

```text
PROTECTED | PUBLIC_INTENTIONAL | SERVICE_TO_SERVICE
```

Depois implementar detector por stack com casos públicos/health legítimos.

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

**Próximo gap:** aproveitar schemas/OpenAPI reais para detectar operação sem `operationId`, duplicidade de `operationId` e mudanças breaking quando o produtor possui contrato estável. Evitar regex de documentação.

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

- `MFE_GLOBAL_CSS` — bloqueia novos seletores globais perigosos em CSS de MFE;
- `MFE_PLUGIN_UI_OVERRIDE` — bloqueia estilização local de `.delpi-ui-*`;
- `MFE_OWN_API_BYPASS` — preserva o BFF/API dona quando o plugin possui API própria.

## 6. Qualidade, testes e evidência

Owner: `platform-quality-testing.mdc`

- `ai-intelligence-evaluation.mdc`
- `architecture-ci-enforcement.mdc`
- `cursor-rules-governance.mdc`
- `plan-construction.mdc`
- `plugins-documentation.mdc`
- `root-cause-generalized-fix.mdc`
- `test-and-commit.mdc`

Racional: processo de investigação, planejamento, evidência, regressão, CI, documentação de entrega e Definition of Done.

O `Architecture Enforcement` executa o scanner Phase 3 e `scripts/ci/audit_platform_guardrails.py`, ambos com testes próprios. O `Cursor Rules Governance` valida também ownership das regras via `responsibility-map.json`.

## 7. Delivery, runtime e operações

Owner: `platform-delivery-runtime-operations.mdc`

- `infra-sequential-container-startup.mdc`
- `plugins-frontend-build.mdc`

**Gap identificado:** existem várias práticas operacionais em `docs/02-infraestrutura` e scripts, mas poucos gates comuns de health/readiness/rollback. Só promover a gate quando houver contrato determinístico compartilhado entre stacks.

## 8. Confiabilidade e observabilidade

Owner: `platform-reliability-observability.mdc`

- `ai-context-and-tool-budget.mdc`
- `http-integration-resilience.mdc`
- `observability-standards.mdc`

Racional: limites, latência, timeout/retry, degradação, logs, métricas, tracing e capacidade.

O scanner Phase 3 já bloqueia novas chamadas HTTP Python detectáveis sem timeout, retry inseguro de writes e exposição óbvia de secrets.

---

# Sobreposições revisadas

## Permanecem separadas

### `plugins-reusable-components` × `plugins-visual-design-system` × `plugin-mfe-page-excellence`

- reusable components governa **onde o componente compartilhado vive**;
- visual design system governa **tokens/CSS/tema/responsividade**;
- page excellence governa **composição e qualidade da página**.

Se a mesma proibição aparecer substantivamente nos três, manter a formulação detalhada apenas na regra dona e referenciar nas outras.

### `migrations-immutable-checksum` × `plugins-migrations-no-reset-prod`

- uma protege imutabilidade da migration versionada;
- outra protege operação de produção contra reset destrutivo.

### `api-delpi-openapi-route-standards` × `api-delpi-response-contract`

- uma governa metadata/qualidade de operação OpenAPI;
- outra governa envelope/semântica de resposta da API DELPI.

## Candidatos a consolidação futura

### `presentation-operational-decoupling` × `schema-first-presentation-delivered`

Há sobreposição relevante. Antes de fundir, inventariar referências e preservar gates. **Não criar terceira regra de apresentação.**

### `new-api-route-checklist` × regras OpenAPI específicas

O checklist deve continuar ponto de entrada operacional, mas contrato detalhado vive na regra técnica dona.

### regras `tv-dashboard-*`

Revisar após estabilização. Regra criada por incidente não deve permanecer indefinidamente se o conhecimento puder migrar para owner transversal ou documentação do domínio.

---

# Gaps prioritários para enforcement

## Implementados

1. migrations imutáveis — `IMMUTABLE_MIGRATION_MUTATION`;
2. MFE sem CSS global — `MFE_GLOBAL_CSS`;
3. MFE sem override do kit — `MFE_PLUGIN_UI_OVERRIDE`;
4. MFE com API própria sem bypass — `MFE_OWN_API_BYPASS`;
5. JWT sem downgrade de signature/audience/issuer — `JWT_VERIFY_DISABLED`;
6. centralização de validator JWT — `JWT_VALIDATOR_DUPLICATION`;
7. centralização de primitives AuthZ — `AUTHZ_PRIMITIVE_DUPLICATION`;
8. HTTP/retry/secrets — gates existentes do Architecture Enforcement.

## Próximos, após modelagem segura

1. corrigir dívida P0 de issuer/audience no `shared/delpi_auth` com rollout controlado;
2. classificar rotas `PROTECTED | PUBLIC_INTENTIONAL | SERVICE_TO_SERVICE` para então medir cobertura AuthZ;
3. boundaries backend entre contexts por imports/ports permitidos;
4. contratos OpenAPI: `operationId`, schema drift e breaking changes com parser real;
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
