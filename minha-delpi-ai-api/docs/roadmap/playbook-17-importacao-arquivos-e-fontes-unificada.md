# Playbook 17 — Importação de arquivos e fontes unificada

**Status:** MVP concluído (jun/2026) — kit UI + policy API; orquestração unificada e poll cross-família em backlog  
**Parent:** [`playbook-05-anexos-lousa.md`](./playbook-05-anexos-lousa.md) (comportamento pós-upload: welcome, chips, lousa)  
**Relacionado:** [`../api/04-actions-openapi.md`](../api/04-actions-openapi.md) (não confundir com import OpenAPI — Playbook 16)

---

## 1. Problema observado

O chat expõe **sete superfícies distintas** para enviar ou ingerir arquivos. Cada uma reimplementa dropzone, lista, status e chamada HTTP com CSS e textos diferentes.

| Sintoma | Impacto |
|---------|---------|
| Dropzone agente ≠ dropzone admin ≠ menu «Anexar» | UX inconsistente; usuário não reconhece o mesmo fluxo |
| Status «Aguardando envio» / «Indexado» em TS **e** em `attachments.json` | Risco de divergência (regra `assistant-content-json.mdc`) |
| `accept` e formatos suportados diferentes por tela | Falha silenciosa ou mensagem genérica |
| Polling de indexação só no anexo de sessão | Fontes de agente/projeto/admin sem feedback de processamento |
| Cards de arquivo com layout distinto (chip, row, card, entity-row) | Visualização não padronizada |

**Princípio:** um **pipeline de ingestão** canônico na API; um **kit de UI** canônico no MFE. Playbook 05 continua dono do *o que fazer depois* que o arquivo foi lido (welcome, chips, lousa).

---

## 2. Taxonomia de ingestão (5 famílias)

| Família | ID | Escopo | Persistência | Indexação RAG |
|---------|-----|--------|--------------|---------------|
| **Anexo de sessão** | `session_attachment` | Mensagem / composer | `ai_chat_attachments` | Sim (async) |
| **Fonte de agente** | `agent_source` | Conhecimento do agente | workspace source + knowledge | Sim |
| **Fonte de projeto** | `project_source` | Contexto do projeto | workspace source | Sim |
| **Conhecimento global** | `global_knowledge` | Admin plataforma | `ai_knowledge_documents` | Sim |
| **Contexto efêmero** | `context_paste` | Chip de contexto no composer | Só memória da sessão (texto extraído) | Não |

**Fora do escopo deste playbook:**

| Fluxo | Playbook |
|-------|----------|
| Import OpenAPI / rotas REST | [Playbook 16](./playbook-16-openapi-import-async-e-readiness-operacional.md) |
| Import/export bundle JSON do agente (config) | Builder — contrato `exportChatAgent` / `importChatAgent` |
| Nota de texto em projeto (sem arquivo) | Mesmo endpoint `POST .../sources` com body texto — UI alinhada, sem dropzone |

---

## 3. Inventário de componentes (auditoria jun/2026)

### 3.1 Marcados na revisão UI ✓

| Superfície | Componente MFE | Classe / seletor | API |
|------------|----------------|------------------|-----|
| Composer — menu | `ChatInput.tsx` | `data-tour="composer-attach"` · «Anexar arquivos» | `POST /chat/attachments` ou `.../sessions/{id}/attachments` |
| Composer — preview | `ChatInput.tsx` | `.mdc-chat-input__attachments` · chips + status | — |
| Mensagem — card | `ChatAttachmentCard.tsx` | `.mdc-chat-attachment-card` | `GET /chat/attachments/{id}/download` |
| Agente — dropzone | `AgentKnowledgeSourcesPanel.tsx` | `.mdc-agent-knowledge__dropzone` | `POST /chat/agents/{id}/sources` |
| Agente — cards | `AgentKnowledgeSourcesPanel.tsx` | `.mdc-agent-knowledge__card` | `DELETE /chat/sources/{id}` |
| Projeto — adicionar | `ChatProjectHome.tsx` | `.mdc-chat-project-sources__add` | `POST /chat/projects/{id}/sources` |
| Projeto — lista | `ChatProjectHome.tsx` | `.mdc-chat-project-source-row` | idem |
| Admin — dropzone | `AdminFileDropzone.tsx` + `KnowledgeIngestionPanel.tsx` | `.mdc-admin-file-dropzone` | `uploadKnowledgeDocumentFile` (admin API) |
| Admin — documentos | `KnowledgeDocumentsPanel.tsx` + `KnowledgeDocumentCard.tsx` | `.mdc-knowledge-document-card` | listagem / reindex admin |

### 3.2 Não marcados — incluir no playbook ✗

| Superfície | Componente MFE | Por que importa |
|------------|----------------|-----------------|
| **Contexto do composer** | `ChatAddContextDialog.tsx` · `.mdc-chat-add-context__dropzone` | Ingestão de arquivo → texto em chip (`context_paste`); `accept` mais restrito que anexo |
| **Edição de mensagem** | `ChatMessageEditAttachments.tsx` | «Anexar mais» ao editar mensagem enviada — reusa upload de sessão |
| **Preview** | `ChatAttachmentPreviewModal.tsx` | Visualização pós-upload (PDF/planilha/imagem) — parte da experiência de arquivo |
| **Orquestração sessão** | `useChatSession.ts` · `ChatMessageList.tsx` | Upload + poll pós-envio; duplica lógica com `chatAttachmentIndexPolling.ts` |
| **Primitive admin** | `AdminFileDropzone.tsx` | Único dropzone reutilizável hoje — candidato a generalizar para `WorkspaceFileDropzone` |
| **Status labels MFE** | `chatAttachmentStatus.ts` | Duplica `attachments.json` → `preview.readingStatus` |
| **Dedup local** | `fileContentHash.ts` | Hash SHA-256 em fontes agente; não usado em anexo de sessão |
| **Polling canônico** | `chatAttachmentIndexPolling.ts` | Padrão a estender para outras famílias com job/indexação |

### 3.3 Backend — pontos de entrada HTTP

| Rota | Arquivo | Família |
|------|---------|---------|
| `POST /chat/attachments` | `attachment_routes.py` | `session_attachment` (com session no body) |
| `POST /chat/sessions/{id}/attachments` | `attachment_routes.py` | `session_attachment` |
| `GET /chat/sessions/{id}/attachments` | `attachment_routes.py` | poll lista |
| `POST /chat/agents/{id}/sources` | `project_routes.py` | `agent_source` |
| `POST /chat/projects/{id}/sources` | `project_routes.py` | `project_source` |
| `DELETE /chat/sources/{id}` | `project_routes.py` | agente + projeto |
| `GET /chat/sources/{id}/download` | `project_routes.py` | download fonte |
| Admin knowledge upload | `admin_routes` + `uploadKnowledgeDocumentFile` | `global_knowledge` |

**Serviços canônicos existentes (não unificados):**

- `ChatAttachmentIndexSchedulerService` — indexação async anexo
- `CreateChatAttachmentUseCase` / `IndexChatAttachmentUseCase`
- Workspace sources — upload inline nas rotas de agente/projeto

---

## 4. Arquitetura alvo

### 4.1 API (minha-delpi-ai-api)

| Módulo | Camada | Responsabilidade |
|--------|--------|------------------|
| `WorkspaceFileIngestPolicyService` | domain | ✅ `accept` MIME/ext, tamanho máx, famílias — `GET /chat/ingest/policy` |
| `ChatWorkspaceFileTextExtractionService` | application | ✅ Leitura canônica txt/csv/json/docx/xlsx/**doc**/**xls**/pdf/imagem — anexos, fontes, admin |
| `WorkspaceFileIngestStatusService` | domain | **Backlog** — hoje labels via `workspaceFileIngestContent.ts` + `attachments.json` |
| `WorkspaceFileIngestOrchestratorService` | application | **Backlog** — hoje cada família usa endpoint próprio (anexo, source, knowledge) |
| Ports por família | domain | `ChatAttachmentRepositoryPort`, source repos, knowledge repo |
| **Proibido** | — | Novo texto PT em use case — só `attachments.json` + `error_handling.json` |

**Contrato metadata unificado (resposta poll):**

```json
{
  "ingestId": "uuid",
  "family": "session_attachment",
  "filename": "delpi.manifest.json",
  "sizeBytes": 2662,
  "status": "indexing",
  "statusLabel": "Indexando para consulta",
  "progress": { "done": 1, "total": 3, "unit": "pages" },
  "contentType": "application/json",
  "error": null
}
```

### 4.2 MFE (plugins/minha-delpi-chat)

| Módulo | Responsabilidade |
|--------|------------------|
| `WorkspaceFileDropzone` | Drag/drop + botão + `accept` + busy — substitui 3 dropzones |
| `WorkspaceFileCard` | Card/chip unificado: ícone, nome, tamanho, status, ações (preview, download, remover) |
| `WorkspaceFileIngestList` | Lista horizontal (composer) ou grid (agente) ou rows (projeto) — **mesmo átomo visual** |
| `workspaceFileIngestApi.ts` | Adaptadores finos sobre `chatApi` / `adminApi` |
| `workspaceFileIngestPolling.ts` | Generalizar `chatAttachmentIndexPolling` |
| `workspaceFileIngestContent.ts` | Espelho sync de `attachments.json` (`preview.readingStatus`) |

**Regra:** `ChatInput`, `AgentKnowledgeSourcesPanel`, `ChatProjectHome`, `KnowledgeIngestionPanel` **só compõem** o kit — sem CSS de dropzone próprio.

### 4.3 Máquina de estados (todas as famílias)

```text
queued → uploading → processing → indexed
                              ↘ unsupported
                              ↘ failed
```

| Estado UI | Chave JSON (`attachments.preview.readingStatus`) |
|-----------|--------------------------------------------------|
| Aguardando envio | `default` |
| Processando leitura | `uploading` / `uploaded` |
| Indexando | `indexing` |
| Indexado | `indexed` |
| Leitura limitada | `unsupported` |
| Falha | `index_failed` |

---

## 5. Mapa de migração por superfície

| Sprint | Superfície | Ação |
|--------|------------|------|
| A | `chatAttachmentStatus.ts` | Consumir só JSON; remover strings PT |
| A | `WorkspaceFileDropzone` + `WorkspaceFileCard` | Extrair de `AdminFileDropzone` + `ChatAttachmentCard` |
| B | `ChatInput` attachments | Trocar chips por `WorkspaceFileCard` |
| B | `ChatAttachmentCard` (mensagem) | Wrapper fino sobre `WorkspaceFileCard` |
| C | `AgentKnowledgeSourcesPanel` | Dropzone + cards → kit |
| C | `ChatProjectHome` sources | Row → `WorkspaceFileCard` variant `row` |
| D | `KnowledgeIngestionPanel` | Usar `WorkspaceFileDropzone` |
| D | `ChatAddContextDialog` | Variante `context_paste` (sem indexação) |
| E | `ChatMessageEditAttachments` | Reusar kit + mesma API sessão | ✅ |
| E | Polling unificado (`session_attachment`) | `workspaceFileIngestPolling` — agente/projeto quando API expuser status | ✅ parcial |

---

## 6. Padronização visual (aceite)

- [x] Copy de dropzone via `workspaceFileIngestContent.ts` (espelho de `attachments.json`)
- [x] Extensões exibidas vêm de `WorkspaceFileIngestPolicyService` (`GET /chat/ingest/policy`)
- [x] Status sempre de `attachments.json` — zero string em TS/Python para usuário (superfícies migradas)
- [x] Card: ícone colorido por tipo, nome truncado, tamanho humanizado, badge de status, preview
- [x] Composer: cards via `WorkspaceFileCard`; agente/projeto/admin: listas com mesmo kit
- [x] Erro de upload: `error_handling.json` por código (`FILE_TOO_LARGE`, `UNSUPPORTED_TYPE`, …) — API + feedback MFE

---

## 7. Testes de regressão

| ID | Caso | Família |
|----|------|---------|
| F1 | Upload PDF no composer → status até `indexed` | `session_attachment` |
| F2 | Duplicata SHA no agente → skip com aviso | `agent_source` |
| F3 | Fonte projeto → aparece na lista com mesmo card | `project_source` |
| F4 | Admin ingest → documento na lista global | `global_knowledge` |
| F5 | Context dialog TXT → chip contexto sem persistir arquivo | `context_paste` |
| F6 | Labels UI = JSON `readingStatus` | transversal |
| F7 | Editar mensagem + anexar mais | `session_attachment` |

Arquivos alvo: `tests/fixtures/workspace_file_ingest_cases.py`, `workspaceFileIngest.test.ts`, smoke `scripts/smoke_workspace_file_ingest.py`.

---

## 8. Relação com Playbook 05

| Playbook 05 | Playbook 17 |
|-------------|-------------|
| Welcome, chips «Com o anexo», lousa | Upload, dropzone, card, status, poll |
| `ChatAttachmentWelcomeService` | `WorkspaceFileIngestOrchestratorService` |
| Casos L1–L12 | Casos F1–F7 |

Implementar 17 **não** altera welcome/chips — só unifica **entrada** e **visualização** do arquivo.

---

## 9. Checklist de aceite (Playbook 17)

- [x] Um `WorkspaceFileDropzone` usado em ≥ 4 superfícies
- [x] Um `WorkspaceFileCard` usado em composer, mensagem, agente, projeto
- [x] Status de leitura/indexação de `attachments.json` no MFE (superfícies migradas)
- [x] `accept` único documentado e enforced na API (+ MFE via `useWorkspaceFileIngestPolicy`)
- [ ] Playbook 05 casos L1–L12 — smoke E2E em homolog (não revalidado em lote pós-17)
- [ ] Poll unificado cross-família (`ingestId` + progresso para agente/projeto/admin)
- [ ] `WorkspaceFileIngestOrchestratorService` (API) — ver §3 módulos canônicos

---

## 10. Referências

| Doc / módulo | Conteúdo |
|--------------|----------|
| [playbook-05-anexos-lousa.md](./playbook-05-anexos-lousa.md) | Pós-upload comportamental |
| `app/content/pt-BR/assistant/attachments.json` | Labels e welcome |
| `chatAttachmentIndexPolling.ts` | Padrão poll existente |
| `AdminFileDropzone.tsx` | Primitive visual admin |
| `attachment_routes.py` | Upload sessão |
| `project_routes.py` | Fontes agente/projeto |
| [chat-workspace-file-extraction-limits.md](../architecture/chat-workspace-file-extraction-limits.md) | Limites de leitura (upload, truncamento, env) |

---

## 11. Resumo executivo

A revisão UI cobriu as **superfícies principais**, mas faltaram **cinco áreas** no inventário: contexto do composer (`ChatAddContextDialog`), edição de mensagem (`ChatMessageEditAttachments`), preview (`ChatAttachmentPreviewModal`), camada de status/polling (`chatAttachmentStatus.ts`, `chatAttachmentIndexPolling.ts`) e o primitive `AdminFileDropzone` como base do kit compartilhado.

O Playbook 17 define **famílias de ingestão**, **módulos canônicos** API/MFE e **sprints de migração** sem duplicar o Playbook 05 (inteligência pós-leitura).

**Próximo passo:** smoke E2E F1–F5 em homolog; erros de upload via `error_handling.json`; poll async se fontes indexarem em background.

### Progresso (jun/2026)

| Sprint | Item | Status |
|--------|------|--------|
| A | `chatAttachmentStatus.ts` → JSON | ✅ |
| A | `WorkspaceFileDropzone` + `WorkspaceFileCard` | ✅ |
| B | `ChatInput` attachments | ✅ |
| B | `ChatAttachmentCard` wrapper | ✅ |
| C | `AgentKnowledgeSourcesPanel` | ✅ |
| C | `ChatProjectHome` sources | ✅ |
| D | `ChatAddContextDialog` dropzone | ✅ |
| D | `KnowledgeIngestionPanel` (já usa `AdminFileDropzone`) | ✅ |
| E | `ChatMessageEditAttachments` labels + `ChatAttachmentCard` | ✅ |
| E | `workspaceFileIngestPolling` (sessão) | ✅ |
| E | API `WorkspaceFileIngestPolicyService` + `GET /chat/ingest/policy` | ✅ |
| E | Fixtures F6/F7 + `workspaceFileIngest.test.ts` | ✅ parcial |
| F | `useWorkspaceFileIngestPolicy` nos dropzones + composer | ✅ |
| F | `scripts/smoke_workspace_file_ingest.py` (policy HTTP) | ✅ |
| G | `ChatWorkspaceFileTextExtractionService` + docx/xlsx/doc/xls | ✅ |
| G | OCR Tesseract na indexação de PDF escaneado (`attachmentIndex`) | ✅ |

---

## 12. Matriz formato × leitura (jun/2026)

**Limites completos (upload, truncamento, env, JSON):** [chat-workspace-file-extraction-limits.md](../architecture/chat-workspace-file-extraction-limits.md).

Pipeline canônico: `ChatWorkspaceFileTextExtractionService` → `ChatAttachmentTextExtractor` (fachada).

| Extensão | Extrator | Indexação RAG | Limite principal na leitura |
|----------|----------|---------------|----------------------------|
| `.txt`, `.md` | plain text | Sim | Arquivo inteiro (UTF-8) |
| `.csv` | csv | Sim | **300 linhas** |
| `.json` | json | Sim | Arquivo inteiro |
| `.docx` | python-docx | Sim | Parágrafos + tabelas (sem limite explícito) |
| `.xlsx` | openpyxl | Sim | **10 planilhas** × **300 linhas** |
| `.doc` | antiword | Sim* | *Container com `antiword`; timeout **30 s** |
| `.xls` | xlrd | Sim* | *Mesmos limites de planilha que `.xlsx` |
| `.pdf` | `ChatPdfDocumentExtractionService` | Sim | **20 páginas** (env); scan → Tesseract até **10** páginas OCR se embutido &lt; **120** chars |
| `.png`, `.jpg`, … | metadados + OCR opcional | Sim | OCR até **4000** chars quando habilitado |

| Upload (todas as famílias) | **25 MB** máximo · extensões por família em `WorkspaceFileIngestPolicyService` |
| Aviso «arquivo extenso» (pós-index) | ≥ **120 000** chars ou ≥ **40** páginas no preview — não trunca extração |

**Container:** `antiword` + Tesseract em `Dockerfile.prod` / `Dockerfile.dev`.

**Config:** `attachments.json` → `fileExtraction`; PDF/index OCR → `document_vision.json` → `pdfExtraction.attachmentIndex`.

