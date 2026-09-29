# ADR — Documentação de processo ≠ Ata

**Status:** DECIDED (2026-09-21). Capability de documentação: **IMPLEMENTED** (pacote V1 local). Runtime prod fica **PROVEN** após deploy/read-back.  
**Escopo:** Transformômetro / Portal Transforma+.

Documentação não prova runtime. Tabela/API abaixo são IMPLEMENTED no código; PROVEN só com evidência de deploy.

## Contexto

Durante o Process Workspace, a tentação foi tratar **Processo ↔ Ata** como relação de domínio a criar (`processo_id` em `tm_meeting_minutes`) para listar atas no workspace.

Isso é inadequado: ata é registro de **reunião**, que pode tratar vários assuntos; não é o artefato canônico da documentação textual do processo.

## Decisão

1. **Ata** = registro de uma reunião (vários assuntos possíveis). Continua bounded context próprio (`tm_meeting_minutes`, rotas `/meeting-minutes`).
2. **Processo ↔ Ata** = **não** é relação direta canônica por padrão. Não criar FK `processo_id` em ata “só para o workspace”. Não inferir vínculo por título/texto.
3. **Process Documentation** = capability do Transformômetro (dona: `transformometro-api` + MFE).
4. Artefato textual canônico: **`ProcessDocument.content_md`** (tabela `transformometro.process_documents`, migration `V049`).
5. **`ProcessDocument` não é**:
   - estado canônico do processo (mestre/instância/revisão);
   - revisão / AS-IS / TO-BE;
   - diagrama (`flowchart_v1`);
   - evidência de revisão ou arquivo do processo;
   - ata / meeting minute.

## Implementação V1 (2026-09-21)

- Cardinalidade: Processo 1→N `ProcessDocument`.
- Soft-delete via `deleted_at` (padrão arquivos/evidências).
- AuthZ: somente `transformometro.access` (manage-only ≠ access).
- API: `/transformometro/processos/{id}/documents` (+ alias EN `/processes/.../documents`).
- Workspace: seção `#documentacao` (+ `#documentacao/{documentId}`).
- Editor: textarea Markdown + preview seguro (`MessageBodyReadonly` / sanitizer do plugin-ui).
- Fora de escopo V1: versionamento, tags, attachments, approval, Mermaid.
- **Surface TÉO (2026-09-22):** exposição via entidade governada `process_document` no catálogo GPT/MCP CRUD — ver [`../integrations/teo-capability-matrix.md`](../integrations/teo-capability-matrix.md) e ADR [`adr-teo-specialist-capability-surfaces.md`](./adr-teo-specialist-capability-surfaces.md). Sem novas operations Action dedicadas.

## Implementação V2 — Markdown experience + realtime (2026-10-27)

- **Renderer documental:** `MarkdownDocumentView` + `buildMarkdownDocumentModel` no `plugin-ui` (`components/markdown/`). GFM via `marked`, sanitização via `stripDangerousRichTextTags` (sem HTML ativo, sem `javascript:`), fenced code com label/copy/scroll interno, anchors determinísticos (`h2+` com ids estáveis + outline derivado — nunca persistido).
- **Mermaid documental:** fenced block ```` ```mermaid ```` renderizado via `DiagramMermaidPreview` (lazy `import("mermaid")`, `securityLevel: "sandbox"`, pós-processamento seguro). **É apenas DOCUMENTAL/ILUSTRATIVO** — nunca sincroniza, sobrescreve ou substitui `flowchart_v1`, que permanece a única autoridade do diagrama do processo.
- **Title dedupe (apresentação):** se o primeiro bloco do `content_md` for `H1` igual ao título do documento (comparação case/whitespace-safe), o H1 não é renderizado no body. O Markdown persistido permanece intacto.
- **Realtime invalidation:** writes de `ProcessDocument` (HTTP Portal + entidade governada GPT/MCP `process_document`) emitem `entity.updated` com `entityType="process_document"`, `sectionKey="documentacao"`, payload mínimo `{processo_id, document_id}` (sem `content_md`, sem claims). Fan-out para a sala existente `processo:{processo_id}` — `process_document` **não** vira entidade de presence/lock (`ALLOWED_ENTITY_TYPES` inalterado).
- **Frontend:** `ProcessDocumentationSection` assina `processo:{processo_id}` e re-lê via API canônica: create/update/delete → refresh de lista; update do doc aberto em view → refresh do detalhe; update do doc em edição → banner de stale-draft (rascunho nunca sobrescrito); delete do doc aberto → fallback/empty state; delete em edição → rascunho preservado + aviso. Anti-eco por `actorClientId` (mesma aba não refaz fetch).
- **Concurrency:** `LOST UPDATE PROTECTION = ABSENT` — `ProcessDocument` não tem version/ETag/expected_version. O banner stale-draft é aviso de UX, **não** proteção de escrita; overwrite concorrente segue possível e é débito conhecido.
- Permanece fora de escopo: versionamento, tags, attachments, approval, autosave, edição colaborativa simultânea, presence/lock de documento, sync Mermaid↔`flowchart_v1`.

## Consequências

- Process Workspace integra **Documentação**, não Atas.
- Markdown é fonte canônica textual do documento; autoridades estruturadas prevalecem se houver contradição.
- `flowchart_v1` permanece a única fonte de verdade do diagrama.

## Histórico

- 2026-09-21: ADR inicial com capability TARGET e relação processo↔ata ABSENT.
- 2026-09-21: V1 implementada (domain/API/MFE); status IMPLEMENTED até aceite runtime.
- 2026-10-27: V2 — renderer documental GFM+Mermaid (ilustrativo), anchors/outline, title dedupe apresentacional e realtime invalidation `process_document`→`processo:{id}` (HTTP + GPT/MCP). `flowchart_v1` segue autoridade única do diagrama.
