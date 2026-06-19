# Changelog — Anexos, desenho DELPI e UX do chat

**Data:** 08/06/2026  
**Escopo:** melhorias no fluxo de anexos (upload, reenvio, status), análise de desenhos e consistência entre `documentVision` e o card na timeline.  
**Arquitetura:** [`docs/architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) · Playbook 07 · Onda 12/13.

Princípio: regras **canônicas na API** (`ChatAttachmentPreviewService`, pipeline de desenho, JSON `attachments.json`); MFE consome `readingStatus` e snapshots — sem duplicar heurística de legibilidade no componente.

---

## 1 — Edição de anexos ao reenviar pergunta

**Commit:** `b8d7c56e`

Ao editar uma mensagem do usuário e reenviar, é possível **remover e adicionar arquivos** antes de confirmar, com pré-visualização em card e modal.

| Camada | Entrega |
|--------|---------|
| MFE | `ChatMessageEditAttachments` — estado de edição no `ChatMessageList` |
| MFE | `ChatAttachmentCard` + `ChatAttachmentPreviewModal` — thumb, metadados e modal de preview |
| MFE | `chatAttachmentPreview.ts` — kind de preview, blob local/servidor, revoke de URL |
| MFE | `fetchChatAttachmentBlob` + `attachmentIds` no resend (`chatApi.ts`, `useChatStreaming.ts`) |
| MFE | Upload de novos arquivos durante edição (`useChatSession.ts`, `ChatPage.tsx`) |

**Testes:** Vitest em `chatAttachmentPreview.test.ts`, `chatNavigation.test.ts` (stub `window`/`PopStateEvent`).

---

## 2 — Relatório DELPI na resposta do assistente

**Commit:** `59bb3791`

**Problema:** turno de desenho concluía com pipeline `drawing:report:ok`, mas a UI mostrava árvore do `product_analyser` e card «Arquivo ilegível» em vez do markdown do relatório DELPI.

**Correção:**

| Camada | Entrega |
|--------|---------|
| API | `chat_tool_context_result_assembly_service` — merge incondicional de `drawingAnalysis` / `drawingAnalysisExport` / `drawingAnalysisMode` |
| API | `chat_turn_llm_assembly_service` — relatório **sempre** substitui `direct_answer` quando há export markdown |
| API | `chat_turn_completion_service` — persiste `answer` = markdown de `drawingAnalysisExport` |
| API | `chat_error_handling_classifier` — não classifica `file_unreadable` se turno de desenho com `/analyser` OK |

**Testes:** `test_chat_turn_llm_assembly_service.py`, `test_error_empty_states.py`.

---

## 3 — Status do card alinhado com `documentVision` legível

**Commit:** `63f3c242`

**Problema:** anexo com `status: index_failed` exibia **«Falha na leitura»** no card, embora `documentVision.legible: true` e o pipeline de desenho tivesse concluído.

**Correção (módulo canônico):**

| Camada | Entrega |
|--------|---------|
| JSON | `attachments.json` → `readingStatusFormats` (`visionReadable`, `visionReadableEngine`, `indexedVisionEngine`, `lowLegibilitySuffix`) |
| API | `ChatAttachmentPreviewService` — `apply_document_vision_to_reading_status`, `enrich_message_attachment_snapshots`, `merge_tool_context_vision_into_attachments` |
| API | `ChatAttachmentResponseService` — `readingStatus` via resolver canônico (upload/listagem) |
| API | `ChatDocumentVisionService.enrich_drawing_extract` — persiste `documentVision` no anexo após OCR do turno de desenho |
| API | Snapshots enriquecidos ao persistir mensagem do usuário (`send` + `stream`) |
| API | `ChatTurnCompletionService` — patch de `metadata.attachments` ao fim do turno (visão do `drawingPdfExtractSummary`) |

**Regras de `readingStatus`:**

| Condição | Label |
|----------|-------|
| `index_failed` + `documentVision.legible: true` | «Legível por visão» ou «Legível por visão ({engine})» |
| `indexed` + visão com engine | «Indexado · visão ({engine})» |
| `legible: false` | sufixo « · OCR com baixa legibilidade» |

**MFE:** `ChatAttachmentCard` prioriza `readingStatus` do snapshot; após `finalizeAssistantTurn`, `loadMessages` sincroniza o card com o patch da API.

**Testes:** `test_chat_attachment_preview_service.py`, `test_chat_attachment_response_service.py`, `test_chat_document_vision_service.py`, `test_chat_document_vision_persist.py` — 20 passed no container.

---

## Commits desta entrega

| Hash | Mensagem |
|------|----------|
| `b8d7c56e` | Permite editar anexos ao reenviar pergunta com pré-visualização em card e modal. |
| `59bb3791` | Garante exibição do relatório DELPI quando análise de desenho conclui com sucesso. |
| `63f3c242` | Alinha status do card de anexo com documentVision legível. |

---

## Validação

```bash
# API — testes de anexo/visão
docker compose -f infra/docker-compose.dev.yml exec -T minha-delpi-ai-api \
  pytest tests/unit/application/services/test_chat_attachment_preview_service.py \
         tests/unit/application/services/test_chat_attachment_response_service.py \
         tests/unit/application/services/test_chat_document_vision_persist.py \
         tests/unit/application/services/test_chat_document_vision_service.py -q

# MFE — preview de anexos (após alterações no plugin)
cd plugins/minha-delpi-chat && npm run test -- chatAttachmentPreview
```

**Cenário manual sugerido:** anexar PDF de desenho com indexação falha → pedir análise DELPI → card deve mostrar «Legível por visão» após o turno; resposta do assistente deve ser o relatório markdown, não árvore de produto nem «Arquivo ilegível».

---

## 4 — `/analyser` com visão completa em turnos de desenho

**Problema:** turnos de análise de desenho chamavam `GET /products/{code}/analyser` com `view=summary` (ex.: `page_size=3`), gerando `meta.sections[].truncated=true`, banner «Parcial • Estrutura parcial» e falsos positivos na validação (BOM/50xx truncados).

**Correção:**

| Camada | Entrega |
|--------|---------|
| Domain | `ChatDrawingAnalyserParameterService` — `requires_full_view` + `apply_to_parameters` / `apply_to_tool_call` |
| Application | `ExternalActionProductRouteCatalogService.build_product_parameters` — threading de `drawing_analysis_mode` |
| Application | `ChatExternalActionOrchestrationService` — `forced_drawing_analysis_mode` + `_apply_drawing_analyser_full_view` |
| Application | `ChatToolContextSelectionService` — pós-patch dos `planned_external_actions` em turno de desenho |

**Testes:** `test_chat_drawing_analyser_parameter_service.py`, `test_build_product_parameters_sets_analyser_view_full_for_drawing_analysis`.

**Cenário manual:** anexar PDF + código no contexto (sem gatilho textual explícito) → análise DELPI → estrutura/roteiro completos, sem banner de cobertura parcial.

---

## 5 — Exportação completa (PDF, CSV, XLSX)

**Problema:** apenas o Markdown trazia o relatório integral; PDF limitava-se a duas tabelas (não conformidades + checklist) e CSV/XLSX exportavam só divergências.

**Correção:**

| Camada | Entrega |
|--------|---------|
| Domain | `ChatDrawingValidationPresentationService.build_export_tables` — PDF/API, estrutura, roteiro, inspeções, divergências, checklist |
| Application | `ChatDrawingReportExportService` — `tables[]`, CSV multi-seção, `xlsxFilename` |
| JSON | `drawing_validation.json` → `export.tableTitles`, `sheetNames`, `columnLabels`, rótulos do PDF |
| MFE | `drawingAnalysisPrint.ts` — HTML no padrão do certificado de inspeções de entrada (logo, faixa azul, selo de status) |
| MFE | `drawingAnalysisExport.ts` — CSV/XLSX com uma aba/seção por tabela |

**Testes:** `test_chat_drawing_report_export_service.py`, `drawingAnalysisExport.test.ts`.

**Cenário manual:** após análise de desenho → exportar PDF (impressão com layout DELPI), CSV e XLSX com todas as tabelas operacionais.
