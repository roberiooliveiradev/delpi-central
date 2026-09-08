# Responsabilidades transversais canônicas

> **Status:** documentação normativa da Minha DELPI — setembro/2026.

Este documento organiza as diretrizes de engenharia em **oito responsabilidades transversais**. O objetivo é impedir que cada aplicação, plugin ou API interprete arquitetura, segurança, contratos, dados, frontend, testes, operação e observabilidade de forma diferente.

A implementação executável dessas responsabilidades está em `.cursor/rules/platform-*.mdc`. Regras específicas de tecnologia ou domínio são filhas dessas responsabilidades.

## Fluxo de uso

Antes de implementar uma alteração relevante:

```text
pedido
→ evidência e objetivo
→ identificar responsabilidades transversais materiais
→ identificar bounded context/owner do domínio
→ carregar regras técnicas filhas necessárias
→ implementar no ponto canônico
→ validar positive + sibling + negative
→ validar objetivo original
```

Uma tarefa pode envolver várias responsabilidades. Não escolher apenas a camada onde o sintoma apareceu.

---

## 1. Arquitetura e boundaries

**Regra:** `.cursor/rules/platform-architecture-boundaries.mdc`

Responsável por:

- bounded contexts e ownership;
- direção das dependências;
- divisão domain/application/adapters/infrastructure;
- integração entre apps por contrato;
- critérios para `shared/`;
- proibição de regra de negócio/banco compartilhado entre contextos.

Pergunta central:

> Quem é o dono desta regra e qual contrato pode cruzar a fronteira?

Regras técnicas relacionadas incluem `application-bounded-context-decoupling.mdc` e `mfe-own-api-no-direct-api-delpi.mdc`.

---

## 2. Segurança, identidade e autorização

**Regra:** `.cursor/rules/platform-security-identity-authorization.mdc`

Responsável por:

- Keycloak/OIDC;
- validação de JWT;
- autorização efetiva/RBAC;
- permissões e escopos de filial/tenant;
- secrets e credentials;
- proteção de writes/admin/destructive;
- auditoria e testes negativos de acesso.

Invariante:

```text
frontend pode melhorar UX
≠ frontend decide autorização
```

A decisão final é backend-first e usa a governança canônica da plataforma.

---

## 3. APIs, contratos e integrações

**Regra:** `.cursor/rules/platform-api-contracts-integration.mdc`

Responsável por:

- HTTP APIs/OpenAPI;
- DTOs, erros, status codes e `operationId`;
- eventos, webhooks, SSE e manifests;
- paginação/limites;
- idempotência;
- clients/adapters;
- evolução backward-compatible.

Regras técnicas relacionadas:

- `contract-evolution-backward-compatibility.mdc`;
- `http-integration-resilience.mdc`;
- `api-delpi-openapi-route-standards.mdc`;
- `api-delpi-response-contract.mdc`.

---

## 4. Dados e persistência

**Regra:** `.cursor/rules/platform-data-persistence.mdc`

Responsável por:

- ownership do banco;
- schema/constraints/índices;
- repositories e Unit of Work;
- transações e concorrência;
- migrations;
- uploads/arquivos persistentes;
- integridade, retenção e recuperação.

Invariantes:

- migration já versionada/aplicada é imutável;
- produção não usa reset destrutivo como rotina;
- banco de outro bounded context não é API.

---

## 5. Frontend, MFE e experiência

**Regra:** `.cursor/rules/platform-frontend-mfe-experience.mdc`

Responsável por:

- arquitetura de Portal/MFE;
- `@delpi/plugin-ui` e design system;
- responsividade e tema;
- acessibilidade/teclado/focus;
- loading/empty/error/forbidden;
- formulários e writes;
- Module Federation e host containment;
- separação UI × regra de negócio.

Regras técnicas relacionadas incluem:

- `plugins-reusable-components.mdc`;
- `plugins-visual-design-system.mdc`;
- `plugin-mfe-page-excellence.mdc`;
- `plugins-overlay-positioning.mdc`;
- `mf-federation-patch-safety.mdc`.

---

## 6. Qualidade, testes e evidência

**Regra:** `.cursor/rules/platform-quality-testing.mdc`

Responsável por:

- estratégia unit/contract/integration/E2E/live;
- regressão por causa raiz;
- positive + sibling + negative;
- evidência ligada ao commit/config corretos;
- Definition of Done;
- CI e critérios de PASS/INCONCLUSIVE.

Pergunta obrigatória:

> Como esta solução pode continuar errada mesmo com os testes atuais passando?

Para Chat AI, esta responsabilidade é estendida pelo protocolo R1–R11.

---

## 7. Delivery, runtime e operações

**Regra:** `.cursor/rules/platform-delivery-runtime-operations.mdc`

Responsável por:

- Docker/Compose;
- gateway/proxy;
- configuração e secrets por ambiente;
- health/readiness;
- startup e shutdown;
- CI/CD;
- deploy/rollback/roll-forward;
- feature flags, shadow/canary;
- runbooks e operação segura.

Uma alteração não está completa se funciona apenas no source tree mas não é reproduzível no artefato/runtime real.

---

## 8. Confiabilidade e observabilidade

**Regra:** `.cursor/rules/platform-reliability-observability.mdc`

Responsável por:

- logs estruturados e correlation IDs;
- métricas e tracing;
- SLI/SLO quando aplicável;
- timeout/retry/backoff/circuit breaker;
- degradação e fallback explícitos;
- limites de capacidade, fan-out, payload e concorrência;
- alertas e recuperação operacional.

Regras técnicas relacionadas:

- `observability-standards.mdc`;
- `http-integration-resilience.mdc`.

---

# Como uma feature deve ser classificada

Exemplo: **nova tela que cria uma solicitação persistida via API**.

Responsabilidades mínimas:

```text
1 Arquitetura — quem é dono da solicitação?
2 Segurança — quem pode criar/ver?
3 Contrato — request/response/erros/idempotência
4 Dados — schema/transação/constraints
5 Frontend — formulário/states/acessibilidade
6 Qualidade — unit/contract/integration/UI regression
7 Delivery — migration/build/deploy se necessário
8 Confiabilidade — logs/timeout/retry/métricas se material
```

Isso evita o anti-padrão “a tarefa é frontend porque o usuário pediu uma tela”.

# Relação com regras específicas

As regras específicas continuam válidas quando o escopo exige detalhes próprios, por exemplo TOTVS, TV Dashboard, Chat AI, notificações ou Module Federation.

A precedência é:

```text
instruções oficiais
→ constituição global .cursor
→ responsabilidade transversal
→ regra especializada
→ contrato/ADR/schema/implementação vigente
```

Regra de domínio não pode relaxar segurança, quebrar boundaries, substituir contrato canônico ou declarar PASS sem evidência exigida pela responsabilidade transversal.

# Critério de maturidade

Uma responsabilidade transversal é considerada saudável quando:

- possui uma fonte canônica clara;
- regras técnicas filhas não se contradizem;
- o Cursor consegue selecioná-la pela natureza da tarefa;
- critérios de conclusão são verificáveis;
- gaps importantes podem virar gates CI determinísticos;
- não existe regra “legado” concorrente dentro de `.cursor/rules`.
