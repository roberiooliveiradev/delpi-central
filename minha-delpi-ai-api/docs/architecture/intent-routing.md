# Roteamento inteligente de intenção (Playbook 02)

## Princípio

**Entenda a intenção antes de escolher ferramenta.** O roteamento roda no chat base (`ChatIntentRouterService`) e é herdado por agentes, projetos e simulação.

## Fluxo

```
Mensagem → normalização → segurança → classificação (classify)
  → resolução de contexto (memória / activePending)
  → execução do pipeline (turn prep)
  → intenção efetiva (resolve_executed) → metadata.intentRouting + adminDebug.intentRoute
```

## Serviços

| Serviço | Papel |
|---------|--------|
| `ChatIntentRouterService` | `classify` (pré-turno), `resolve_executed` (pós-prep) |
| `ChatIntentRouterMetricsService` | `intentRouting` + `intentRouterMetrics`; agregação admin via audit |
| `ChatIntentDisambiguationService` | Resposta direta + chips quando `ambiguous` com código de produto |
| `ChatOperationalSubIntentService` | Sub-intenção operacional (`router.operationalSubIntentPipeline`) |
| `ChatOperationalAmbiguityService` | Escopo ambíguo vs. consulta específica (`operationalAmbiguityExclusionPredicates`) |
| `ChatIntentDisambiguationFollowUpService` | `metadata.routingDisambiguationSuggestions` |
| `ChatActivePendingService` | Pendências (`clarification`) |
| `ChatReferenceResolutionService` / memória | Follow-up e `resolvedParams` |
| `ChatWebSearchIntentService` | Detecção de `web_search` explícito |
| `ChatConversationMessageSearchService` | `session_review` / meta-conversa + evidências da sessão |
| `ChatIntentRouterContentService` | Limites/padrões de `intent_router.json` (ex.: reply curto de filial) |

## Prioridade (resumo)

1. Segurança SQL  
2. Clarificação (`activePending`)  
3. Tarefa textual / e-mail  
4. Lousa  
5. Follow-up / apresentação / **session review (meta-conversa)** / **format refinement** (`follow_up` + `format_refinement`)  
6. Consulta operacional (só com sinal operacional, **sub-intent resolvido** — ex. `schedule_today_lookup` em «programação de produção» — ou reply curto ancorado — **não** só por memória)  
7. Web explícita  
8. RAG documental  
9. SQL (gerar/revisar/explicar/executar)  
10. Autoajuda / identidade / small talk  
11. LLM geral  

## Clarify vs tool (ago/2026)

| Mensagem | Resultado esperado |
|----------|-------------------|
| `programação` (só) | `ChatUnclearRequestService` → `ambiguous_domain` (não schedule) |
| `programação de produção` / `… hoje` | `operational_query` + `schedule_today_lookup` + `requires_tool` |
| Stage `tools` vazio + `no_clear_intent` | `resolve_executed` **não** promove a `operational_query` |

Análise estruturada (`ChatTurnAnalysisService`) só abre no gate (baixa confiança / `llm_fallback`); não substitui heurística de rota clara.

## Metadata

- `metadata.intentRouting` — contrato Playbook 02 (intent, subIntent, flags, resolvedParams, …)  
- `metadata.adminDebug.intentRoute` — compatibilidade admin  
- `metadata.intentRouterMetrics` — snapshot para métricas  
- `metadata.routingDisambiguationSuggestions` — botões Cadastro/Estoque/Fornecedores… (MFE)
- `metadata.selectionPending.kind` — `catalog_route` (slide/TV) vs `score_gap_route` (clarificação de rota; prompt sem «slide»)

## Admin

- `GET /admin/metrics/intent-routing/summary?hours=168` — agregado de `audit_metadata.intentRouting`
- Painel Métricas (MFE): `AdminIntentRoutingMetrics`

## Testes

- Regressão R1–R17: `tests/fixtures/intent_router_regression_cases.py`, `tests/unit/domain/services/test_intent_router.py`  
- Script: `scripts/run_intent_routing_validation.sh`

## Documentação de produto

Playbook completo: `docs/roadmap/melhorias/playbook_roteamento_intencao_minha_delpi_chat.md`