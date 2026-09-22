# Playbook 02 — Roteamento Inteligente de Intenção

**Projeto:** Minha DELPI Chat IA  
**Status (30/05/2026):** Implementado (Fases 1–5; Fase 4 mixed compound básico; UI desambiguação + admin métricas)  
**Código:** `ChatIntentRouterService`, `ChatIntentRouterMetricsService`  
**Arquitetura:** [`docs/architecture/intent-routing.md`](../../architecture/intent-routing.md)  
**Validação:** `scripts/run_intent_routing_validation.sh`, regressão R1–R15 em `tests/fixtures/intent_router_regression_cases.py`

---

## 1. Objetivo

Decidir a intenção do usuário **antes** de acionar LLM, action, RAG, web search, SQL ou lousa — evitando rotas erradas (texto tratado como consulta ERP, autoajuda disparando action, follow-up sem memória, etc.).

**Regra principal:** entenda a intenção antes de escolher ferramenta.

---

## 2. Intenções suportadas (classify)

| Intent | Exemplos | Rota |
|--------|----------|------|
| `small_talk` | obrigado, bom dia | resposta direta |
| `identity` | quem é você? | identidade |
| `self_help` | o que você pode fazer? | catálogo (sem action) |
| `text_task` / `email_task` | corrija, traduza, e-mail | LLM textual, `skip_tools` |
| `mixed_task` | consulte estoque e escreva e-mail | steps operacional + texto |
| `attachment_task` | resuma o PDF | anexo / RAG |
| `canvas_task` | coloque na lousa | lousa |
| `web_search` | pesquise na web | `web_search` |
| `operational_query` | estoque, fornecedor | actions/API |
| `rag_question` | o que diz a norma? | RAG interno |
| `sql_task` | monte/revise/explique SQL | skill SQL |
| `follow_up` | agora fornecedores | memória + operacional |
| `clarification` | sim, 01, filial | `activePending` |
| `presentation_task` | mostre em gráfico | presenter |
| `security` | SQL destrutivo | bloqueio |

---

## 3. Prioridade (ordem no `classify`)

1. Segurança  
2. Clarificação (`activePending`)  
3. Tarefa textual (incl. SQL explícito antes de «monte» genérico)  
4. Lousa  
5. Apresentação  
6. Follow-up / operacional  
7. Web explícita (respeita «não pesquise»)  
8. RAG documental  
9. Autoajuda / identidade / utilitário  
10. LLM geral (+ fallback sugerido em `build_fallback_prompt`)

---

## 4. Metadata (resposta)

```json
{
  "intentRouting": {
    "intent": "operational_query",
    "subIntent": "stock_lookup",
    "confidence": 0.94,
    "requiresTool": true,
    "resolvedParams": { "productCode": "10080001" }
  },
  "intentRouterMetrics": { "intent": "operational_query", "decision": "operational_action" },
  "adminDebug": { "intentRoute": { "...": "compat" } }
}
```

Bloco `router` em `intentRoute`: `decision`, `reason`, mensagem normalizada (admin).

---

## 5. Regressão R1–R15

| Caso | Entrada | Intent |
|------|---------|--------|
| R1 | Corrija este texto | `text_task` |
| R2 | Estoque do produto 10080001 | `operational_query` |
| R3 | O que você pode fazer? | `self_help` |
| R4 | Pesquise na web sobre WEG | `web_search` |
| R5 | Coloque isso na lousa | `canvas_task` |
| R6 | Agora fornecedores (+ histórico) | `operational_query` + follow-up |
| R7 | Resuma esse PDF (+ anexo) | `attachment_task` |
| R8 | Monte SQL | `sql_task` |
| R9 | Quem é você? | `identity` |
| R10 | Obrigado | `small_talk` |
| R11 | Mostre em gráfico | `presentation_task` |
| R12 | Sim (+ pending filial) | `clarification` |
| R13 | Corrija: estoque baixo | `text_task` (sem API) |
| R14 | Consulte estoque e e-mail | `mixed_task` |
| R15 | O que diz a norma? | `rag_question` |

---

## 6. Feedback (thumbs down)

Motivos `routing_*` no `personality_playbook.json` e MFE `chatFeedbackReasons.ts`; snapshot via `ChatActivePendingService.routing_snapshot_from_assistant_metadata`.

---

## 7. Roadmap restante

| Fase | Itens |
|------|--------|
| 4+ | Orquestração automática de mixed compound (executar steps em sequência) |
| UI+ | Chips dinâmicos por agente/ações permitidas |

---

## 8. Anti-padrões

Não usar LLM geral para tudo; não chamar API em correção textual; não usar RAG para estoque; não ignorar «não pesquise»; não executar SQL sem permissão quando o pedido é só revisão/explicação.

---

*Especificação detalhada (seções 1–31 do produto): ver histórico do playbook no repositório / conversa de implementação maio/2026.*
