# ADR-006 — BPMN nativo do Transformômetro e editor BPMN compartilhado (G7)

- **Status:** Accepted (G7 — LOCAL INTEGRATION RUNTIME)
- **Data:** 2026-10-09
- **Altera:** a premissa anterior "Meu Modelador = autoridade de todo BPMN
  canônico" — SUPERSEDED/REFINADA (evolução aprovada, não bug; DRIFT ledger).

## Contexto

O usuário precisa da mesma experiência profissional de edição BPMN dentro de
um processo do Transformômetro, mas os artefatos criados ali pertencem ao
processo — não à biblioteca do Modelador. Duas fontes de verdade por artefato
continuam proibidas; a novidade é que a **autoridade do artefato passa a ser o
bounded context que o criou**, não um app único.

## Decisão

```text
EDITOR É COMPARTILHADO. ARTEFATO NÃO.

BpmnEditorSurface (plugins/bpmn-editor — package fonte compartilhado)
        │  consome BpmnDocumentHost (port)
        ├─► ModelerDocumentHost          → bpmn-modeler API → bpmn_modeler.*
        └─► TransformometroBpmnDocumentHost → transformometro API → transformometro.*
```

- **Editor compartilhado:** `plugins/bpmn-editor` (`@delpi/bpmn-editor`) —
  mesma superfície source-level consumida pelos dois MFEs (mesmo padrão de
  `@delpi/plugin-ui` e `@delpi/transformometro-meeting-minutes-presentation`:
  package de fonte resolvido por alias vite/tsconfig, bundle por MFE).
  Editor core nunca chama endpoint diretamente — toda persistência passa por
  `BpmnDocumentHost`.
- **Artefato TM-nativo:** `transformometro.processo_bpmn_models` +
  `transformometro.processo_bpmn_revisions` (V053). Ownership = `processo_id`
  (não o criador); `created_by/updated_by` = metadado de auditoria.
- **Representação canônica:** BPMN 2.0 XML + BPMN-DI — única fonte, sem JSON
  visual paralelo. Checksum SHA-256 calculado server-side.
- **Concorrência:** `version` + `ETag "v<n>"` + `If-Match` — mesma semântica
  do Modeler; stale → 409, sem lost update.
- **Validação:** pipeline BPMN extraída para `shared/bpmn_validation`
  (pacote Python canônico já instalado nos dois serviços via
  `pip install -e /shared`) — pure, sem dependência de repo/HTTP/DB.
  TM nunca delega save/validate ao bpmn-modeler-api.
- **AuthZ:** deriva do acesso ao **processo** (`transformometro.access` —
  view e manage compartilham o gate vigente; separação dedicada é follow-up,
  já registrado em ADR-005). `created_by` nunca autoriza. Backend-first;
  capabilities no frontend são UX gating apenas.
- **Dois modos, XOR obrigatório:** um processo tem OU BPMN nativo OU
  referência externa (G5, `processo_bpmn_references`) — nunca ambos ativos.
  Create-native com external ativo → 409; link-external com native ativo →
  409. Sem sync automática; conversões futuras criam artefatos independentes.
- **Visibilidade:** TM-nativo nunca existe em `bpmn_modeler.*`, nunca aparece
  em `/bpmn-modeler/models` nem na biblioteca — não por flag, por ausência.
- **`flowchart_v1`:** LEGACY — intocado, não é fallback nem fonte.

## Invariantes

- `TM save → bpmn-modeler-api` chamadas: 0 (network isolation).
- SQL do repo TM-nativo em `bpmn_modeler.*`: 0. FK cross-schema: 0.
- DUAL ACTIVE BPMN AUTHORITIES per processo: 0.
- `created_by == caller` como autorização: 0.
- Sem proxy genérico: superfície process-scoped estreita
  (`/transformometro/processos/{id}/bpmn*`).
- Autosave só reporta `SAVED` após read-back autoritativo (mesma máquina
  SaveMachine compartilhada).
- Revisões explícitas, imutáveis, append-only; autosave nunca cria revisão;
  restore cria nova revisão com proveniência (`origin="restore"`).

## Estrutura do package compartilhado

```text
plugins/bpmn-editor/src/
  host/BpmnDocumentHost.ts     port + tipos de transporte neutros
  editor/                      adapter, profile, governance, properties,
                               extensionPreservation, i18n, inspector
  layout/                      elk graph + worker + diProposal
  state/                       SaveMachine + AutosaveController + capabilities
  components/                  chrome do editor (PaletteSearch, panels,
                               dialogs, history, export, selectors)
  pages/BpmnDocumentEditorPage.tsx   superfície generalizada
  pages/BpmnRevisionViewPage.tsx     viewer histórico generalizado
  ui/kit.ts + content/ + styles.css
```

MODELER SHELL permanece em `plugins/bpmn-modeler`: biblioteca, lifecycle de
modelo (create/rename/duplicate/archive), routing, `bpmnModelerApi`,
`ModelerDocumentHost`, wrappers finos de página.

## Follow-ups explícitos (não iniciados)

- Separação view/edit dedicada por processo (depende de capability Core);
- cópia Modeler→TM / TM→Modeler (artefatos independentes, UX futura);
- restauração com preview completo de diff;
- TÉO/MCP consumindo o BPMN nativo.
