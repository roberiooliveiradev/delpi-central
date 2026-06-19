# Changelog — Validação de desenhos: payload analyser e roadmap Onda 15

**Data:** 19/06/2026  
**Escopo:** falsos negativos de cadastro em produtos com analyser grande; playbook de evolução da validação normativa.  
**Arquitetura:** [`chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) · Playbook: [`playbook_validacao_desenhos_delpi_roadmap.md`](../roadmap/melhorias/playbook_validacao_desenhos_delpi_roadmap.md)

Princípio: checklist **canônico no chat base** (`ChatDrawingValidationOrchestrationService` + serviços de domínio); textos em `drawing_validation.json` — sem patch no agente ou MFE.

---

## Problema

| Desenho | Sintoma | Causa raiz |
|---------|---------|------------|
| **90263622** | «Cadastro do produto — Não encontrado» com API HTTP 200 | `responsePreview` truncado (~194 KB > limite 100 KB) → `json.loads` falha → payload vazio na validação |
| **90262834** | Roteiro/inspeção/cotas reprovados indevidamente | Estrutura só nível 1; contrato inspeção legado; notas dimensionais sem classificação (ver playbook Fases 15.1–15.5) |

---

## Fase 15.0 — Entregue (código)

| Entrega | Módulo |
|---------|--------|
| `resolve_root_from_data` + prioridade `external_action_data` | `ChatDrawingAnalyserPayloadService` |
| Passagem do payload bruto da tool no turno de desenho | `ChatToolContextAuxiliaryService`, `ChatToolContextResultAssemblyService` |
| `authorizedResult` quando preview `/analyser` truncado | `ChatToolContextExternalActionFormatter` |

**Testes:** `test_chat_drawing_analyser_payload_service.py`, `test_chat_drawing_analysis_enrichment.py`, `test_chat_tool_context_external_action_formatter.py`.

---

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| `playbook_validacao_desenhos_delpi_roadmap.md` | Roadmap Onda 15 (fases 15.0–15.6), casos 90262834/90263622, mapa canônico, gates CI |
| Índices `melhorias/README.md`, `STATUS_ROADMAP_MELHORIAS.md`, `BACKLOG_ROADMAP.md` | Link para Onda 15 |

---

## Próximo (backlog playbook)

1. **15.1** — `ChatDrawingStructureIndexService` (estrutura recursiva).
2. **15.3** — `ChatDrawingInspectionValidationService` (`measurable_tests` / `textual_tests`).
3. **15.4** — `ChatDrawingMultipageCoverageService` (90263622 multipágina).
4. Fixtures `test_chat_drawing_validation_90262834.py` e `_90263622.py`.
