# Playbook 06 — Erros e Resultados Vazios

Projeto: Minha DELPI Chat IA  
Escopo: falhas, respostas sem dados, permissão negada, parâmetros ausentes, API indisponível, busca sem resultado e recuperação de fluxo.

> **Princípio:** erro bom é erro com saída — o que aconteceu, por quê, o que fazer agora e chips de recuperação.

---

## Implementação (jun/2026)

| Componente | Responsabilidade |
|------------|------------------|
| `error_handling.json` | Templates, motivos e chips por tipo (`empty_result`, `permission_denied`, …) |
| `ChatErrorHandlingClassifier` | Classifica a partir de tools, resposta, anexos e trust signals |
| `ChatErrorHandlingService` | Metadata `errorHandling`, `errorRecoveryFollowUpSuggestions`, debug admin |
| `ChatErrorHandlingTelemetryService` | Log estruturado `error_handling` |
| `ChatErrorAutoRecoveryService` | Plano `errorAutoRecovery` + reexecução ao pedir «tente novamente» |
| `ChatErrorHandlingAdminMetricsService` | Auditoria `errorHandlingMetrics` + cliques/tentativas de recuperação |
| `ChatHelpErrorFollowUpService` | Fallback quando não há chips de recuperação tipados |
| MFE `ChatErrorHandlingCard` | Card com título, motivos e chips «Recuperar consulta» (sem chips duplicados quando `interactivity.consolidated`) |

Legado relacionado: `ChatOperationalParameterService` (parâmetro ausente), `ChatSecurityMessagingService` (falhas API), `attachmentUnreadable` (Playbook 05).

---

## Tipos suportados (classificação)

`empty_result`, `missing_parameter`, `invalid_parameter`, `permission_denied`, `api_unavailable`, `timeout`, `partial_result`, `ambiguous_request`, `context_missing`, `rag_no_source`, `web_no_source`, `file_unreadable`, `unsupported_file`, `tool_error`, `action_not_available`.

Metadata exemplo:

```json
{
  "errorHandling": {
    "type": "empty_result",
    "severity": "warning",
    "recoverable": true,
    "userMessage": "Não encontrei registros para esse filtro.",
    "apiFailed": false,
    "affirmsNonExistence": false,
    "suggestions": ["Buscar por descrição", "Ampliar período"]
  }
}
```

---

## Regra crítica

Se a API falhou (`apiFailed: true`), **não** marcar `affirmsNonExistence` — o chat não deve afirmar que o dado não existe.

---

## Testes de regressão

| Caso | Entrada | Esperado |
|------|---------|----------|
| E1 | consulta sem dados | `empty_result` + chips |
| E2 | estoque sem código | `missing_parameter` |
| E4 | HTTP 403 | `permission_denied` |
| E5 | HTTP 503 | `api_unavailable` |
| E8 | anexo `index_failed` | `file_unreadable` |
| E13 | API falhou + «não existe» | `apiFailed`, sem afirmar inexistência |
| E14 | resposta fria curta | `errorHandlingEnrichedAnswer` |

Arquivos: `tests/fixtures/error_empty_states_cases.py`, `tests/unit/application/services/test_error_empty_states.py`, `scripts/smoke_error_empty_states.py`.

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Templates de erro | Concluída |
| 2 — Metadata e debug | Concluída |
| 3 — Chips de recuperação | Concluída |
| 4 — Recuperação automática | Concluída (`errorAutoRecovery`, reexecução em `ChatToolContextService`, estratégias em `error_handling.json`) |
| 5 — Métricas e alertas | Concluída (telemetria, `errorHandlingMetrics`, cliques `recuperar`, `chat.error_recovery.attempted`, painel admin) |

---

## Resumo executivo

Falhou? Explique, sugira e permita recuperar. Toda melhoria neste playbook deve atualizar `error_handling.json`, classificador, testes E* e feedback no MFE.
