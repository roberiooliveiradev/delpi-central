# Minha DELPI Copilot

Este diretório é o ponto de entrada da iniciativa **Minha DELPI Copilot** dentro do monorepo `delpi-central`.

O Copilot é a evolução da Minha DELPI para uma plataforma em que a IA funciona como uma segunda interface operacional: explica, consulta, analisa, navega e executa capabilities autorizadas usando os mesmos contratos de negócio da UI.

## Documentação canônica

[`../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md`](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/README.md)

## Estado executável

```text
PROGRAM = PLANNED / NOT_STARTED
NEXT_STEP = C0.S0 — Rebaseline e inventário real
```

Arquivos principais:

- [Plano Mestre C0–C7](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/16-execution-master-plan.md)
- [Matriz de apps AI-ready](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/18-app-onboarding-matrix.md)
- [Rollout e migrações](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/19-rollout-and-migrations.md)
- [Testes e aceite](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/20-testing-and-acceptance-matrix.md)
- [Protocolo do Cursor](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/22-cursor-execution-protocol.md)
- [Prompt mestre do Cursor](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md)
- [Especificação completa do produto](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/24-product-specification.md)
- [Rastreabilidade CP-001…CP-060](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/25-requirements-traceability.md)
- [Execution ledger](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/evidence/execution-ledger.md)

## Estratégia de implementação

Não será criado um runtime independente aqui por padrão. A implementação deve evoluir os owners existentes:

- `minha-delpi-ai-api` — inteligência, planner, Action Catalog, RAG, policies, memory, presentation e orchestration;
- `plugins/minha-delpi-chat` — experiência conversacional, activity, confirmation e rendering;
- `portal` — CopilotBridge, Router, Workspace Context e Platform Actions;
- Core API — apps, rotas, permissões e governança;
- `api-delpi` e demais APIs — Business Actions por OpenAPI/use cases;
- MFEs — contexto, deep links e view capabilities especializadas.

Não criar um segundo motor de IA desconectado do chat base.

## Primeira ação do Cursor

Não começar implementando UI.

```text
C0.S0
→ capturar HEAD/working tree
→ inventariar Portal/Core/AI/MFEs/APIs/manifests
→ provar producer/consumer/owner
→ atualizar matriz de apps
→ registrar evidence
→ somente então liberar C0.S1
```

Use o [prompt mestre](../docs/12-roadmap-e-evolucao/minha-delpi-copilot/23-prompt-cursor-execucao.md).