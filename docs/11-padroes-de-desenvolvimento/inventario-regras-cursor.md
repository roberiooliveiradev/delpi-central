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

## 2. Segurança, identidade e autorização

Owner: `platform-security-identity-authorization.mdc`

- `ai-external-tools-security.mdc`

**Gap ainda aberto:** a plataforma possui documentação forte de Keycloak/RBAC, porém múltiplos stacks válidos de enforcement (`shared/delpi_auth`, decorators locais, dependencies, service token e serviços de policy). Não criar regex genérica de rota sem `@require_permission` antes de modelar essas variantes.

**Gate já implementado:** `JWT_VERIFY_DISABLED` bloqueia nova desativação explícita da verificação de assinatura/certificado JWT em código de produção.

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

**Gate já implementado:** `IMMUTABLE_MIGRATION_MUTATION` permite nova `VNN__*.sql`, mas bloqueia modificação, rename ou remoção de migration SQL já versionada.

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

**Gates já implementados:**

- `MFE_GLOBAL_CSS` bloqueia novos seletores globais perigosos em CSS de MFE;
- `MFE_PLUGIN_UI_OVERRIDE` bloqueia estilização local de classes `.delpi-ui-*`, preservando `plugins/plugin-ui` como owner do CSS do kit.

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

O `Architecture Enforcement` executa o scanner Phase 3 e `scripts/ci/audit_platform_guardrails.py`, ambos com testes próprios.

## 7. Delivery, runtime e operações

Owner: `platform-delivery-runtime-operations.mdc`

- `infra-sequential-container-startup.mdc`
- `plugins-frontend-build.mdc`

**Gap identificado:** existem várias práticas operacionais documentadas em `docs/02-infraestrutura` e scripts, mas poucas regras especializadas de deploy/rollback/health. O owner transversal cobre o contrato geral e deve receber novos detalhes apenas quando houver responsabilidade realmente distinta e recorrente.

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

Não são duplicatas completas:

- reusable components governa **onde o componente compartilhado vive**;
- visual design system governa **tokens/CSS/tema/responsividade**;
- page excellence governa **composição e qualidade da página**.

Podem referenciar-se, mas não devem repetir blocos extensos. Se a mesma proibição aparecer substantivamente nos três, manter a formulação detalhada apenas na regra dona e referenciar nas outras.

### `migrations-immutable-checksum` × `plugins-migrations-no-reset-prod`

- a primeira protege a **imutabilidade de migrations versionadas/aplicadas**;
- a segunda protege a **operação de produção contra reset destrutivo**.

São riscos diferentes e permanecem separadas.

### `api-delpi-openapi-route-standards` × `api-delpi-response-contract`

- uma governa qualidade/descrição das operações OpenAPI;
- outra governa envelope/semântica de resposta da API DELPI.

Permanecem separadas enquanto os contratos forem distintos.

## Candidatos a consolidação futura

### `presentation-operational-decoupling` × `schema-first-presentation-delivered`

Existe sobreposição relevante de objetivo: impedir apresentação específica por rota e garantir contrato schema-driven. Antes de fundir, inventariar consumidores/referências e preservar todos os gates. **Não criar terceira regra de apresentação.**

### `new-api-route-checklist` × regras OpenAPI específicas

Há interseção de checklist com `api-delpi-openapi-route-standards` e com o fluxo OpenAPI-first do Chat AI. O checklist deve continuar sendo ponto de entrada operacional, mas não repetir contrato detalhado: deve apontar para a regra técnica dona.

### regras `tv-dashboard-*`

São específicas e pequenas, porém devem ser revisadas quando o TV Dashboard estabilizar. Regras temporárias de incidente não devem permanecer indefinidamente; conhecimento durável deve migrar para owner transversal ou documentação do domínio.

---

# Gaps prioritários para enforcement

## Implementados

1. **Migrations imutáveis** — `IMMUTABLE_MIGRATION_MUTATION`.
2. **MFE sem CSS global novo** — `MFE_GLOBAL_CSS`.
3. **MFE sem override do kit** — `MFE_PLUGIN_UI_OVERRIDE`.
4. **JWT sem verificação explicitamente desabilitada** — `JWT_VERIFY_DISABLED`.
5. **HTTP/retry/secrets** — gates já existentes do Architecture Enforcement.

## Próximos, após modelagem segura

1. **AuthZ backend-first:** modelar os mecanismos válidos por stack e permitir rotas públicas/health/service-token explicitamente antes de bloquear ausência de autorização.
2. **Boundaries entre apps:** modelar bounded contexts e imports permitidos para bloquear import de `domain`/`application` entre apps irmãos e bypass HTTP indevido.
3. **Contratos:** aproveitar OpenAPI/schema existentes para detectar drift e mudanças breaking sem classificação, evitando regex textual.
4. **MFE federation/build:** ampliar gates a configuração de federation apenas com base nos helpers/contratos vigentes.
5. **Delivery:** health/readiness, rollback e configuração devem ganhar gates quando houver sinal determinístico comum entre stacks.

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
