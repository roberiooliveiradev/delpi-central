# Documentação — transformometro-api

Índice da documentação da API do Transformômetro. Product/roadmap de negócio fica em [`docs/12-roadmap-e-evolucao/transformometro-app/`](../../docs/12-roadmap-e-evolucao/transformometro-app/).

## Estrutura

| Pasta | Conteúdo |
|-------|----------|
| [`operations/`](./operations/) | Deploy, desenvolvimento local, backup JSON |
| [`architecture/`](./architecture/) | Contratos de integração, ADRs, realtime |
| [`domain/`](./domain/) | Regras de cálculo e categorias de benefício |
| [`schemas/`](./schemas/) | JSON Schemas canônicos (flowchart, WBS, matriz) |
| [`gpt-actions/`](./gpt-actions/) | Custom GPT OpenAI · persona **TÉO** (OAuth, OpenAPI, instructions) |
| [`chat/`](./chat/) | Snapshot OpenAPI read-only do Chat Minha DELPI |
| [`meeting-minutes/`](./meeting-minutes/) | Atas Transforma+ / Kimi |
| [`archive/`](./archive/) | Status de playbooks entregues e histórico (não é fonte vigente) |

## Começar por

| Objetivo | Documento |
|----------|-----------|
| Subir / deployar a API | [operations/DEPLOYMENT.md](./operations/DEPLOYMENT.md) · [operations/DEVELOPMENT.md](./operations/DEVELOPMENT.md) |
| Fórmulas oficiais | [domain/regras-de-calculo.md](./domain/regras-de-calculo.md) |
| Custom GPT (**TÉO**) | [gpt-actions/custom-gpt-actions.md](./gpt-actions/custom-gpt-actions.md) · [gpt-actions/specialist-instructions.md](./gpt-actions/specialist-instructions.md) |
| Chat Minha DELPI (read-only) | [chat/agent-openapi.md](./chat/agent-openapi.md) |
| Atas + Kimi | [meeting-minutes/kimi.md](./meeting-minutes/kimi.md) |
| Contratos S2S / api-delpi | [architecture/integration-contracts.md](./architecture/integration-contracts.md) |
| Export/import JSON | [operations/json-backup.md](./operations/json-backup.md) |

## Artefatos gerados

```bash
# OpenAPI do Custom GPT (≤30 ops)
PYTHONPATH=.:../shared python scripts/sync_gpt_actions_openapi.py
# → docs/gpt-actions/openapi-gpt-actions.json
```

## O que não fica aqui

- Tutorial de usuário, OPERATIONS e playbooks de produto → `docs/12-roadmap-e-evolucao/transformometro-app/`
- Docs do MFE → `plugins/transformometro/docs/`
- Status histórico de sprints (PB18–21) → [`archive/playbooks/`](./archive/playbooks/)
