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
| 7.3 | Regressão ampliada | CPV, OTD, compras produto (+ seleção heurística) | Parcial (3 casos novos) |
| 7.4 | Calibração RAG | `RAG_CONTEXT_MIN_SCORE` por ambiente | Pendente |
| 7.5 | Homologação latência | Estoque por código &lt; 15s em CPU prod | Pendente (validação) |

---

## 7.1 — Templates no builder

No **Construtor de agentes** (`ChatAgentBuilderPage`), o campo **Modelo de instruções** aplica um texto base e sugere **estilo de resposta** (`objetivo`, `detalhado`, etc.).

Confirmação antes de substituir instruções já preenchidas.

**Boas práticas após aplicar template operacional:**

1. Anexar `docs/knowledge/api-delpi-rotas-agente.md` à base do agente.
2. Configurar provider OpenAPI `api-delpi` e reimportar schema após deploy da API.
3. Habilitar actions permitidas na especialização do agente.

---

## Próximos passos (7.2–7.5)

1. Estender `openapi_agent_metadata.py` para rotas de compras/vendas/CPV.
2. Adicionar casos em `chat_intelligence_regression_cases.py`.
3. Documentar valores recomendados de `RAG_CONTEXT_MIN_SCORE` em homologação.
4. Medir latência p95 em produção CPU e registrar em `status-atual.md`.

---

## Referências

- [api-delpi-rotas-agente.md](../knowledge/api-delpi-rotas-agente.md)
- [11-guia-agente-chat.md](../../../api-delpi/docs/api/11-guia-agente-chat.md)
- [status-atual.md](../../../docs/12-roadmap-e-evolucao/minha-delpi-chat/status-atual.md)
