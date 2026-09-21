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
- Fora de escopo V1: versionamento, tags, attachments, approval, Mermaid, GPT Actions, MCP, TÉO.

## Consequências

- Process Workspace integra **Documentação**, não Atas.
- Markdown é fonte canônica textual do documento; autoridades estruturadas prevalecem se houver contradição.
- `flowchart_v1` permanece a única fonte de verdade do diagrama.

## Histórico

- 2026-09-21: ADR inicial com capability TARGET e relação processo↔ata ABSENT.
- 2026-09-21: V1 implementada (domain/API/MFE); status IMPLEMENTED até aceite runtime.
