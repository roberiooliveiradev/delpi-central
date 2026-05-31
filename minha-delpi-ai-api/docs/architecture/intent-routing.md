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
| `ChatIntentRouterMetricsService` | `intentRouting` + `intentRouterMetrics` na resposta |
| `ChatActivePendingService` | Pendências (`clarification`) |
| `ChatReferenceResolutionService` / memória | Follow-up e `resolvedParams` |
| `ChatWebSearchIntentService` | Detecção de `web_search` explícito |

## Prioridade (resumo)

1. Segurança SQL  
2. Clarificação (`activePending`)  
3. Tarefa textual / e-mail  
4. Lousa  
5. Follow-up / apresentação  
6. Consulta operacional  
7. Web explícita  
8. RAG documental  
9. SQL (gerar/revisar/explicar/executar)  
10. Autoajuda / identidade / small talk  
11. LLM geral  

## Metadata

- `metadata.intentRouting` — contrato Playbook 02 (intent, subIntent, flags, resolvedParams, …)  
- `metadata.adminDebug.intentRoute` — compatibilidade admin  
- `metadata.intentRouterMetrics` — snapshot para métricas  

## Testes

- Regressão R1–R15: `tests/fixtures/intent_router_regression_cases.py`, `tests/unit/domain/services/test_intent_router.py`  
- Script: `scripts/run_intent_routing_validation.sh`

## Documentação de produto

Playbook completo: `docs/roadmap/melhorias/playbook_roteamento_intencao_minha_delpi_chat.md`
