# Playbook — Contrato de respostas para IA (índice api-delpi)

Este arquivo é o **ponto de entrada no repositório api-delpi** para o roadmap de padronização de respostas.

**Documento completo (roadmap, fases, compatibilidade com consumidores):**

[`minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md`](../../../minha-delpi-ai-api/docs/roadmap/playbook-10-contrato-respostas-api-delpi.md)

**Fase 0 (inventário + fixtures):**

[`fase-0-inventario-contrato-respostas.md`](./fase-0-inventario-contrato-respostas.md)

---

## Consumidores HTTP que devem ser considerados

| Consumidor | Integração |
|------------|------------|
| **strategic-indicators-api** | `shared/delpi_api_client` → `/financial`, `/commercial`, `/production`, `/supplies`, `/quality`, `/engineering` |
| **12 plugins MFE** (HTTP direto) | `dashboard-supplies`, `dashboard-commercial`, `dashboard-production`, `dashboard-quality`, `dashboard-financial`, `dashboard-engineering`, `dashboard-hr`, `dashboard-lmps`, `dashboard-delpi`, `central-agendamento`, `auditoria-5s`, `eficiencia-fabril` |
| **Portal** | `portal/src/data/delpiApi.ts` — health, products, status |
| **minha-delpi-ai-api** | Actions OpenAPI — presenter + LLM (não é plugin browser) |
| **strategic-indicators** (plugin) | Só via `strategic-indicators-api` — não chama api-delpi no frontend |
| **minha-delpi-chat** (plugin) | Só via `minha-delpi-ai-api` — não chama api-delpi no frontend |

**Regra:** `meta` e `error` no root são aditivos. Alterações em **`data`** exigem migração coordenada (ver § 4.4 do playbook completo).

---

## Fases com trabalho principal em api-delpi

| Fase | Resumo | Quebra consumidores? |
|------|--------|----------------------|
| **0** | Inventário + matriz rota × consumidor | Não |
| **1** | `operationId` + `agent_route()` | Não |
| **2** | Envelope de erro unificado | Coordenar SI + MFEs (handler) |
| **3** | `meta` semântico | Não (aditivo) |
| **4** | OpenAPI `response_model` | Não |
| **5** | Normalização Protheus | **Sim** — `?legacy=true` + smoke SI/MFE |
| **6** | `?view=summary` opt-in | Não se default `full` mantido |
| **7** | Presenter chat por perfil | Não (só chat base) |

---

## Arquivos a alterar (referência rápida)

- `app/core/responses.py`
- `app/interface/http/openapi_agent_metadata.py`
- `shared/delpi_api_client/client.py` (SI)
- `plugins/dashboard-*/src/api/*.ts` (MFEs)
- `docs/api/00-visao-geral.md`, `11-guia-agente-chat.md`

Após mudança de OpenAPI: reimport no `minha-delpi-ai-api`. Após mudança em `data`: smoke SI + dashboards afetados.
