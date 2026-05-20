# Inteligência do chat — Onda 7

**Status:** em andamento (maio/2026)  
**Pré-requisitos:** [Onda 6](./inteligencia-chat-onda-6.md)

## Objetivo

Facilitar a **configuração de agentes** no builder (templates de instruções) e ampliar cobertura operacional (OpenAPI + regressão), sem depender de modelo maior.

---

## Entregas da onda

| # | Entrega | Descrição | Status |
|---|---------|-----------|--------|
| 7.1 | Templates de system prompt | Modelos “Operacional TOTVS”, “Documental/RH”, “Documental geral”, “Híbrido” no builder | Concluído (`plugins/minha-delpi-chat/src/domain/agentSystemPromptTemplates.ts`) |
| 7.2 | OpenAPI ampliado | CPV, OTD, giro, compras/vendas produto, listagem OVs | Concluído (`openapi_agent_metadata.py`) |
| 7.3 | Regressão ampliada | Giro, dashboard LMP, vendas produto, OVs, suprimentos diretos | Concluído (+10 casos) |
| 7.4 | Calibração RAG | Guia `rag-context-min-score-calibracao.md` + tabela em `variaveis-de-ambiente.md` | Concluído |
| 7.5 | Homologação latência | Checklist em guia RAG; medição em prod | Pendente (validação manual) |
| 7.6 | Seleção OVs vs LMP | Heurística `list_sale_orders` sem confundir com LMP | Concluído |

---

## 7.1 — Templates no builder

No **Construtor de agentes** (`ChatAgentBuilderPage`), o campo **Modelo de instruções** aplica um texto base e sugere **estilo de resposta** (`objetivo`, `detalhado`, etc.).

Confirmação antes de substituir instruções já preenchidas.

**Boas práticas após aplicar template operacional:**

1. Anexar `docs/knowledge/api-delpi-rotas-agente.md` à base do agente.
2. Configurar provider OpenAPI `api-delpi` e reimportar schema após deploy da API.
3. Habilitar actions permitidas na especialização do agente.

---

## Próximos passos

1. Medir latência p95 em produção CPU (checklist em [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md)) e registrar em `status-atual.md`.
2. Reimportar OpenAPI e reindexar `api-delpi-rotas-agente.md` após deploy.
3. Opcional: resposta direta dedicada para `list_sale_orders` e mais rotas comerciais no OpenAPI.

---

## Referências

- [api-delpi-rotas-agente.md](../knowledge/api-delpi-rotas-agente.md)
- [11-guia-agente-chat.md](../../../api-delpi/docs/api/11-guia-agente-chat.md)
- [rag-context-min-score-calibracao.md](./rag-context-min-score-calibracao.md)
- [status-atual.md](../../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md)
