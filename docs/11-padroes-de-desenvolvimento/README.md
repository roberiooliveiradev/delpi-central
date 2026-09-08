# Padrões de desenvolvimento

> **Status:** documentação oficial — revisada em setembro/2026

Convenções transversais para contribuir no monorepo **Minha DELPI**.

## Fonte normativa principal

Antes de decisões arquiteturais ou alterações relevantes, aplicar:

1. [instrucoes-oficiais-gpt-arquiteto-delpi-central.md](./instrucoes-oficiais-gpt-arquiteto-delpi-central.md) — constituição arquitetural do projeto;
2. `.cursor/rules/development-standards-index.mdc` — roteamento das regras especializadas;
3. contratos, schemas, OpenAPI, ADRs e implementação vigente do domínio afetado.

A pasta `docs/14-documentacao-geral/` contém material de referência migrado da antiga raiz documental e **não substitui** estas fontes normativas nem contratos vigentes.

---

## Documentos

| Padrão | Arquivo |
|---|---|
| Instruções arquiteturais oficiais | [instrucoes-oficiais-gpt-arquiteto-delpi-central.md](./instrucoes-oficiais-gpt-arquiteto-delpi-central.md) |
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
