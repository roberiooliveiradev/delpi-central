# Jul/2026 — Correções pós-refatoração (chat API)

**Escopo:** `minha-delpi-ai-api` — regressões após migração para conteúdo JSON, runtime de inteligência plugável e desacoplamento de `Settings` direto nos serviços.

---

## Resumo

Correções generalistas no módulo canônico (sem patch por rota/use case), alinhadas a `centralized-rules-first.mdc` e `assistant-content-json.mdc`.

| Área | Problema | Correção |
|------|----------|----------|
| Fine-tuning | `AttributeError: _SECRET_PATTERNS` após mover padrões para `learning_content.json` | `ChatFineTuningAnonymizationService` consome `ChatLearningContentService.compile_pattern_list` |
| Capacidades | `NameError: lines` em `format_action_catalog` | Retorno corrigido para lista `output` (consumida por `lines.extend`) |
| Roteamento | `productCode` do `operationalFocus` vazava em consultas de escopo amplo (ex.: ranking) | `_filtered_working_memory_params` em `ChatIntentRouterEntityResolutionService` |
| Interpretação de dados | Follow-up «resume» falhava quando o presenter só devolvia linhas genéricas de SQL | Fallback substantivo a partir de `responsePreview` + `product_operational_content` (estoque) |
| Testes | Runtime de inteligência/visão batia Postgres fora de app context | Mock autouse em `conftest` + `tests/support/chat_intelligence_runtime.py` |

---

## Arquivos de produção

- `app/domain/services/chat_fine_tuning_anonymization_service.py`
- `app/domain/services/chat_capabilities_catalog_answer_service.py`
- `app/domain/services/chat_intent_router/chat_intent_router_entity_resolution_service.py`
- `app/domain/services/chat_operational_tool_summary_resolution_service.py`

---

## Testes / suporte

- `tests/conftest.py` — mock de `resolve_chat_intelligence_runtime` e `vision_settings`
- `tests/support/chat_intelligence_runtime.py` — `multi_action_enabled=True` por padrão; `patch_platform_runtime_access`
- Ajustes pontuais em testes de semantic ranker, identidade vs capacidades, anexos OCR, admin debug e extensões `.doc`/`.xls`

---

## Validação

```bash
cd minha-delpi-ai-api
.venv/bin/python -m pytest \
  tests/unit/application/services/test_chat_fine_tuning_service.py \
  tests/unit/domain/services/test_chat_fine_tuning_anonymization_service.py \
  tests/unit/application/services/test_chat_admin_debug_persistence.py \
  tests/unit/application/services/test_chat_data_interpretation_answer_service.py \
  tests/unit/application/services/test_chat_active_pending_service.py \
  tests/unit/application/services/test_chat_external_action_orchestration_service.py \
  -q
```

Suíte completa `tests/unit/`: ~4447 pass / ~223 fail (backlog pré-existente em gates, text specialist e stream legados).
