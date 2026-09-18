# Documentação — transformometro-api

Índice da documentação da API do Transformômetro. Product/roadmap de negócio fica em [`docs/12-roadmap-e-evolucao/transformometro-app/`](../../docs/12-roadmap-e-evolucao/transformometro-app/).

## Estrutura

| Pasta | Conteúdo |
|-------|----------|
| [`operations/`](./operations/) | Deploy, desenvolvimento local, backup JSON |
| [`architecture/`](./architecture/) | Contratos, ADRs e realtime. Alvos não implementados: [ciclo](./architecture/adr-ciclo-inteligencia-processo.md) · [Portal Transforma+](./architecture/adr-portal-transforma-plus.md) |
| [`domain/`](./domain/) | Regras de cálculo e categorias de benefício |
| [`schemas/`](./schemas/) | JSON Schemas canônicos (flowchart, WBS, matriz) |
| [`gpt-actions/`](./gpt-actions/) | Custom GPT OpenAI · persona **TÉO** (OAuth, OpenAPI, instructions) — **LEGACY_TRANSITIONAL_BRIDGE** |
| [`integrations/`](./integrations/) | Plugin/MCP TÉO FULL CRUD (`mcp-transformometro`) — **TARGET** agentes |
| [`chat/`](./chat/) | Snapshot OpenAPI read-only do Chat Minha DELPI |
| [`meeting-minutes/`](./meeting-minutes/) | Atas Transforma+ / Kimi |
| [`archive/`](./archive/) | Status de playbooks entregues e histórico (não é fonte vigente) |

## Começar por

| Objetivo | Documento |
|----------|-----------|
| Subir / deployar a API | [operations/DEPLOYMENT.md](./operations/DEPLOYMENT.md) · [operations/DEVELOPMENT.md](./operations/DEVELOPMENT.md) |
| Fórmulas oficiais | [domain/regras-de-calculo.md](./domain/regras-de-calculo.md) |
| Custom GPT (**TÉO**) Actions bridge | [gpt-actions/custom-gpt-actions.md](./gpt-actions/custom-gpt-actions.md) · [gpt-actions/specialist-instructions.md](./gpt-actions/specialist-instructions.md) |
| Plugin/MCP (**TÉO**) FULL CRUD | [integrations/openai-plugin-mcp.md](./integrations/openai-plugin-mcp.md) · [integrations/keycloak-mcp-client-runbook.md](./integrations/keycloak-mcp-client-runbook.md) |
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
- Ciclo de inteligência (TARGET, sem implementação) → [CICLO-INTELIGENCIA-DE-PROCESSO.md](../../docs/12-roadmap-e-evolucao/transformometro-app/CICLO-INTELIGENCIA-DE-PROCESSO.md)
- Experiência Portal Transforma+ (TARGET, sem rename técnico) → [PORTAL-TRANSFORMA-PLUS.md](../../docs/12-roadmap-e-evolucao/transformometro-app/PORTAL-TRANSFORMA-PLUS.md)
- Ordem de implementação (não autoriza código) → [ARCHITECTURE-RUNWAY.md](../../docs/12-roadmap-e-evolucao/transformometro-app/ARCHITECTURE-RUNWAY.md)
- Docs do MFE → `plugins/transformometro/docs/`
- Status histórico de sprints (PB18–21) → [`archive/playbooks/`](./archive/playbooks/)
