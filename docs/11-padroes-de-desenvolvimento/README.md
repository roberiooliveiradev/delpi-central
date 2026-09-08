# Padrões de desenvolvimento

> **Status:** documentação oficial — revisada em setembro/2026

Convenções transversais para contribuir no monorepo **Minha DELPI**.

## Fonte normativa principal

Antes de decisões arquiteturais ou alterações relevantes, aplicar:

1. [instrucoes-oficiais-gpt-arquiteto-delpi-central.md](./instrucoes-oficiais-gpt-arquiteto-delpi-central.md) — constituição arquitetural do projeto;
2. [responsabilidades-transversais.md](./responsabilidades-transversais.md) — oito responsabilidades canônicas de engenharia;
3. `.cursor/rules/development-standards-index.mdc` — roteamento executável das regras;
4. contratos, schemas, OpenAPI, ADRs e implementação vigente do domínio afetado.

A pasta `docs/14-documentacao-geral/` contém material de referência e não substitui estas fontes normativas nem contratos vigentes.

---

## Oito responsabilidades transversais

| # | Responsabilidade | Regra `.cursor` |
|---|---|---|
| 1 | Arquitetura e boundaries | `platform-architecture-boundaries.mdc` |
| 2 | Segurança, identidade e autorização | `platform-security-identity-authorization.mdc` |
| 3 | APIs, contratos e integrações | `platform-api-contracts-integration.mdc` |
| 4 | Dados e persistência | `platform-data-persistence.mdc` |
| 5 | Frontend, MFE e experiência | `platform-frontend-mfe-experience.mdc` |
| 6 | Qualidade, testes e evidência | `platform-quality-testing.mdc` |
| 7 | Delivery, runtime e operações | `platform-delivery-runtime-operations.mdc` |
| 8 | Confiabilidade e observabilidade | `platform-reliability-observability.mdc` |

Detalhes, limites e exemplos de composição: [responsabilidades-transversais.md](./responsabilidades-transversais.md).

---

## Documentos

| Padrão | Arquivo |
|---|---|
| Instruções arquiteturais oficiais | [instrucoes-oficiais-gpt-arquiteto-delpi-central.md](./instrucoes-oficiais-gpt-arquiteto-delpi-central.md) |
| Responsabilidades transversais | [responsabilidades-transversais.md](./responsabilidades-transversais.md) |
| Rotas HTTP | [padrao-de-rota.md](./padrao-de-rota.md) |
| Use cases | [padrao-de-use-case.md](./padrao-de-use-case.md) |
| Repositories / ports | [padrao-de-repository.md](./padrao-de-repository.md) |
| Erros API | [padrao-de-erro.md](./padrao-de-erro.md) |
| Eventos de domínio | [padrao-de-evento.md](./padrao-de-evento.md) |
| Code review | [checklist-code-review.md](./checklist-code-review.md) |

---

## Referências por camada

| Camada | Documentação |
|---|---|
| Core API rotas | [../04-core-api/controllers-e-rotas.md](../04-core-api/controllers-e-rotas.md) |
| Core API erros | [../04-core-api/erros-api.md](../04-core-api/erros-api.md) |
| Core API UoW | [../04-core-api/unit-of-work.md](../04-core-api/unit-of-work.md) |
| API DELPI | [../../api-delpi/docs/api/README.md](../../api-delpi/docs/api/README.md) |
| Manifesto plugin | [../05-plugin-system/manifesto-plugin.md](../05-plugin-system/manifesto-plugin.md) |

---

## Regra de precedência

```text
instruções oficiais
→ constituição global .cursor
→ responsabilidade transversal aplicável
→ regra especializada
→ contrato/ADR/schema/OpenAPI/implementação vigente
```

Roadmap, changelog, homologação datada ou plano do Cursor não substituem esta hierarquia.