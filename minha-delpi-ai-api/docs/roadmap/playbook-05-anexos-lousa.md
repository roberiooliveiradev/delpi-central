# Playbook 05 — Anexos e Lousa

Projeto: Minha DELPI Chat IA  
Escopo: arquivos anexados, lousa/canvas, transformação de respostas em documentos.

> **Implementação (jun/2026):** `ChatAttachmentWelcomeService`, `ChatAttachmentFollowUpService`, `ChatAttachmentPreviewService`, `ChatCanvasContentService`, `ChatCanvasAmbiguityService`, `ChatCanvasSessionMetadataService`, `ChatAttachmentLargeFileService`. Legado: [melhorias/playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md](./melhorias/playbooks_melhoria_minha_delpi_chat/07_anexos_e_arquivos.md).

---

## Princípio central

**Anexo é fonte de trabalho. Lousa é área de produção.**

---

## Fluxo de anexo

1. Upload → welcome com nome do arquivo e status de leitura  
2. Chips «Com o anexo» (resumir, corrigir, traduzir, pendências, checklist, ata, lousa)  
3. Processamento por tipo (PDF, planilha, imagem) via indexação / visão  
4. Próximos passos (lousa, exportação, comparar)

---

## Lousa

- Criar / acrescentar / substituir conteúdo (`ChatCanvasContentService`)  
- Ambiguidade em «coloque **isso** na lousa» (`ChatCanvasAmbiguityService`)  
- Metadata `canvas` + `canvasVersion` por abertura (`ChatCanvasSessionMetadataService`)  
- Chips pós-resposta em `personality_playbook.json` (texto, e-mail, web, operacional)

---

## Arquivo grande e ilegível

- Aviso em welcome quando `charCount` ou páginas excedem limiar (`ChatAttachmentLargeFileService`)  
- Mensagem dedicada quando todos os anexos falham na indexação (`attachmentUnreadable`)

---

## Testes de regressão

| Caso | Entrada | Esperado |
|------|---------|----------|
| L1 | upload PDF | welcome + ações |
| L2 | follow-up | chips incluem Resumir e Lousa |
| L5 | coloque na lousa | abre com última resposta |
| L7 | arquivo grande | aviso + chips de seção |
| L11 | index_failed | pede reenvio |
| L12 | isso + múltiplas fontes | pergunta de desambiguação |

Arquivos: `tests/fixtures/attachments_canvas_cases.py`, `tests/unit/application/services/test_attachments_canvas.py`, `scripts/smoke_attachment_index_welcome.py`.

---

## Roadmap

| Fase | Status |
|------|--------|
| 1 — Upload com ações | Concluída |
| 2 — Processamento por tipo | Concluída (indexação + OCR/visão) |
| 3 — Lousa básica | Concluída |
| 4 — Lousa avançada | Parcial (versão em metadata; export no front) |
| 5 — Integração completa | Parcial (chips cruzados; fluxos anexo→lousa) |

---

## Resumo executivo

Arquivo entra como fonte; lousa vira entrega. Toda melhoria em anexo ou canvas deve atualizar welcome, chips, testes L* e `personality_playbook.json`.
