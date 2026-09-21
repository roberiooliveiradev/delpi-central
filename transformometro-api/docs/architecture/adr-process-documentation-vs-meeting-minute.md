# ADR — Documentação de processo ≠ Ata

**Status:** DECIDED (2026-09-21). Capability de documentação: **TARGET** (não implementada).  
**Escopo:** Transformômetro / Portal Transforma+.

Documentação não prova runtime. Nenhuma tabela/API abaixo é PROVEN só por este ADR.

## Contexto

Durante o Process Workspace, a tentação foi tratar **Processo ↔ Ata** como relação de domínio a criar (`processo_id` em `tm_meeting_minutes`) para listar atas no workspace.

Isso é inadequado: ata é registro de **reunião**, que pode tratar vários assuntos; não é o artefato canônico da documentação textual do processo.

## Decisão

1. **Ata** = registro de uma reunião (vários assuntos possíveis). Continua bounded context próprio (`tm_meeting_minutes`, rotas `/meeting-minutes`).
2. **Processo ↔ Ata** = **não** é relação direta canônica por padrão. Não criar FK `processo_id` em ata “só para o workspace”. Não inferir vínculo por título/texto.
3. **Process Documentation** = nova capability **TARGET** do Transformômetro (dona: `transformometro-api` + MFE).
4. Artefato textual canônico alvo: **`ProcessDocument.content_md`** (nome de campo ainda sujeito a pacote/DoR).
5. **`ProcessDocument` não é**:
   - estado canônico do processo (mestre/instância/revisão);
   - revisão / AS-IS / TO-BE;
   - diagrama (`flowchart_v1`);
   - evidência de revisão ou arquivo do processo;
   - ata / meeting minute.

## Consequências

- Process Workspace **não** integra Atas enquanto a relação continuar ABSENT (estado atual confirmado no inventário).
- Qualquer UI futura de “documentação do processo” usa a capability Process Documentation, não o módulo de atas.
- Implementação de `ProcessDocument` exige pacote próprio (Abstraction Gate, AuthZ `transformometro.access`, migration `up` imutável, OpenAPI, Help) — **não autorizada** só por este ADR.

## Não decidido (TO_INVENTORY)

- Schema exacto (`process_documents` vs outro), versionamento, vínculo opcional a revisão.
- Se anexos da documentação reusam `processo_arquivos` ou storage próprio.
- Se a sala/tarefas podem **referenciar** uma ata sem tornar ata filha do processo.
